from dagster import asset, AssetExecutionContext, Output, MetadataValue
from ..resources import DockerResource, MongoDBResource
from .core import spark_streaming_accumulator_asset
from .infrastructure import check_services_asset

@asset(
    description="Train all 3 ML models (Random Forest, Gradient Boosting, Logistic Regression) using ACCUMULATED MongoDB data",
    group_name="machine_learning",
    deps=[spark_streaming_accumulator_asset],
)
def spark_ml_training_asset(
    context: AssetExecutionContext,
    docker: DockerResource,
    mongodb: MongoDBResource
) -> Output[dict]:
    """Train the ensemble ML models using data in MongoDB"""

    context.log.info("Starting model training (from MongoDB)...")

    # Check we have enough data
    transaction_count = mongodb.get_collection_count("accumulated_training_data")
    normal_count, fraud_count = mongodb.get_fraud_count()

    context.log.info(f"Training data: {transaction_count} transactions")
    context.log.info(f"  Normal: {normal_count}, Fraud: {fraud_count}")

    if transaction_count < 100:
        raise Exception(f"Not enough data for training. Have {transaction_count}, need at least 100.")

    if fraud_count < 1:
        raise Exception("No fraud cases found. Cannot train models.")

    # Train models
    context.log.info("Executing model training (this may take 10-15 minutes)...")

    exit_code, output = docker.exec_spark_submit(
        script_path="/app/src/train_model.py",
        packages="org.mongodb.spark:mongo-spark-connector_2.12:10.4.0"
    )

    # Log training output
    for line in output.split('\n'):
        if any(keyword in line for keyword in ['✅', '📊', '🔄', 'ERROR', 'WARN']):
            context.log.info(line)

    if exit_code != 0:
        raise Exception(f"Model training failed with exit code {exit_code}:\n{output}")

    # Verify models were created
    model_count_cmd = "ls -la /app/models/ 2>/dev/null | grep -E 'random_forest|gradient_boosting|logistic_regression' | wc -l"
    exit_code, model_count_output = docker.exec_command("spark", model_count_cmd)

    try:
        models_found = int(model_count_output.strip())
    except:
        models_found = 0

    context.log.info("✅ Model training complete!")
    context.log.info(f"   Models found: {models_found}/3")

    if models_found < 3:
        context.log.warning(f"Expected 3 models, found {models_found}")

    return Output(
        {
            "training_samples": transaction_count,
            "models_trained": 3,
            "exit_code": exit_code,
        },
        metadata={
            "training_samples": transaction_count,
            "fraud_percentage": round(fraud_count / transaction_count * 100, 2),
            "models_trained": 3,
            "success": exit_code == 0,
        }
    )

@asset(
    description="Train FULL POWER models using the complete Kaggle CSV dataset (High Performance)",
    group_name="machine_learning",
    deps=[check_services_asset],
)
def spark_ml_training_full_asset(
    context: AssetExecutionContext,
    docker: DockerResource
) -> Output[dict]:
    """Train the ensemble ML models using the full CSV dataset"""

    context.log.info("Starting FULL model training (from CSV)...")
    context.log.info("This trains on the entire 284k dataset. Please wait...")

    # Train models
    exit_code, output = docker.exec_spark_submit(
        script_path="/app/src/train_model_full.py",
    )

    # Log training output
    for line in output.split('\n'):
        if any(keyword in line for keyword in ['✅', '📊', '🔄', 'ERROR', 'WARN']):
            context.log.info(line)

    if exit_code != 0:
        raise Exception(f"Full Model training failed with exit code {exit_code}:\n{output}")

    context.log.info("✅ Full Model training complete! Models saved with '_full' suffix.")
    
    return Output(
        {
            "status": "success",
            "mode": "full_dataset"
        },
        metadata={
            "status": "success",
            "source": "creditcard.csv"
        }
    )
