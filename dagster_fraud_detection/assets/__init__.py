"""
Dagster Assets for Fraud Detection Pipeline
Each asset represents a discrete step in the pipeline
"""

from dagster import asset, AssetExecutionContext, Output, MetadataValue
import time
import subprocess
from ..resources import DockerResource, MongoDBResource


@asset(
    description="Check that all required Docker services are running",
    group_name="infrastructure",
)
def check_services_asset(context: AssetExecutionContext, docker: DockerResource) -> Output[dict]:
    """Verify all Docker services are running"""

    required_services = ["kafka", "mongodb", "spark", "mongo-express", "dozzle"]
    service_status = {}

    context.log.info("Checking Docker services...")

    for service in required_services:
        status = docker.get_container_status(service)
        service_status[service] = status
        context.log.info(f"  {service}: {status}")

    all_running = all(status == "running" for status in service_status.values())

    if not all_running:
        failed_services = [svc for svc, status in service_status.items() if status != "running"]
        raise Exception(f"Services not running: {', '.join(failed_services)}")

    return Output(
        service_status,
        metadata={
            "services_checked": len(required_services),
            "all_running": all_running,
            "details": MetadataValue.json(service_status),
        }
    )


@asset(
    description="Accumulate training data by running Spark processor without ML",
    group_name="data_pipeline",
    deps=[check_services_asset],
)
def accumulate_data_asset(
    context: AssetExecutionContext,
    docker: DockerResource,
    mongodb: MongoDBResource
) -> Output[dict]:
    """Run Spark processor to accumulate training data"""

    context.log.info("Starting data accumulation...")

    # Check existing data
    initial_count = mongodb.get_collection_count("transactions")
    context.log.info(f"Initial transaction count: {initial_count}")

    # Start Spark processor in background
    context.log.info("Starting Spark processor (without ML)...")

    # Use subprocess to run in background and monitor
    process = subprocess.Popen(
        [
            "docker", "exec", "spark",
            "/opt/spark/bin/spark-submit",
            "--master", "local[*]",
            "--packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.mongodb.spark:mongo-spark-connector_2.12:10.4.0",
            "--conf", "spark.mongodb.write.connection.uri=mongodb://admin:admin123@mongodb:27017/fraud_detection.transactions?authSource=admin",
            "/app/src/spark-processor.py"
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    context.log.info(f"Spark processor started (PID: {process.pid})")
    context.log.info("Accumulating data for 2 minutes...")

    # Monitor progress
    start_time = time.time()
    target_duration = 120  # 2 minutes

    try:
        while time.time() - start_time < target_duration:
            time.sleep(10)
            current_count = mongodb.get_collection_count("transactions")
            elapsed = int(time.time() - start_time)
            context.log.info(f"  [{elapsed}s] Transactions: {current_count} (+{current_count - initial_count})")

            # Check if process died
            if process.poll() is not None:
                _, stderr = process.communicate()
                raise Exception(f"Spark processor stopped unexpectedly: {stderr}")

    finally:
        # Stop the processor
        context.log.info("Stopping Spark processor...")
        subprocess.run(["docker", "exec", "spark", "pkill", "-f", "spark-processor.py"], capture_output=True)
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()

    final_count = mongodb.get_collection_count("transactions")
    normal_count, fraud_count = mongodb.get_fraud_count()
    accumulated = final_count - initial_count

    context.log.info(f"✅ Data accumulation complete!")
    context.log.info(f"   Accumulated: {accumulated} transactions")
    context.log.info(f"   Total: {final_count} transactions")
    context.log.info(f"   Normal: {normal_count}, Fraud: {fraud_count}")

    if accumulated < 100:
        context.log.warning(f"Only accumulated {accumulated} transactions. Recommend at least 1000 for training.")

    return Output(
        {
            "initial_count": initial_count,
            "final_count": final_count,
            "accumulated": accumulated,
            "normal_count": normal_count,
            "fraud_count": fraud_count,
        },
        metadata={
            "transactions_accumulated": accumulated,
            "total_transactions": final_count,
            "normal_transactions": normal_count,
            "fraud_transactions": fraud_count,
            "fraud_percentage": round(fraud_count / final_count * 100, 2) if final_count > 0 else 0,
        }
    )


@asset(
    description="Train all 3 ML models (Random Forest, Gradient Boosting, Logistic Regression)",
    group_name="machine_learning",
    deps=[accumulate_data_asset],
)
def train_models_asset(
    context: AssetExecutionContext,
    docker: DockerResource,
    mongodb: MongoDBResource
) -> Output[dict]:
    """Train the ensemble ML models"""

    context.log.info("Starting model training...")

    # Check we have enough data
    transaction_count = mongodb.get_collection_count("transactions")
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
    models_check_cmd = "ls -la /app/models/ 2>/dev/null | grep -E 'random_forest|gradient_boosting|logistic_regression' | wc -l"
    exit_code, model_count_output = docker.exec_command("spark", model_count_cmd)

    try:
        models_found = int(model_count_output.strip())
    except:
        models_found = 0

    context.log.info(f"✅ Model training complete!")
    context.log.info(f"   Models found: {models_found}/3")

    if models_found < 3:
        context.log.warning(f"Expected 3 models, found {models_found}")

    return Output(
        {
            "training_samples": transaction_count,
            "normal_samples": normal_count,
            "fraud_samples": fraud_count,
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
    description="Run ML predictions on streaming data using trained models",
    group_name="machine_learning",
    deps=[train_models_asset],
)
def run_ml_predictions_asset(
    context: AssetExecutionContext,
    docker: DockerResource,
    mongodb: MongoDBResource
) -> Output[dict]:
    """Run ML predictions on new data"""

    context.log.info("Starting ML prediction processor...")

    # Check models exist
    exit_code, _ = docker.exec_command("spark", "test -d /app/models/random_forest_model")
    if exit_code != 0:
        raise Exception("Models not found. Run train_models_asset first.")

    # Get initial counts
    initial_transactions = mongodb.get_collection_count("transactions")
    initial_predictions = mongodb.get_collection_count("model_predictions")

    context.log.info(f"Initial state:")
    context.log.info(f"  Transactions: {initial_transactions}")
    context.log.info(f"  Predictions: {initial_predictions}")

    # Start ML processor in background
    context.log.info("Starting ML processor...")

    process = subprocess.Popen(
        [
            "docker", "exec", "spark",
            "/opt/spark/bin/spark-submit",
            "--master", "local[*]",
            "--packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.mongodb.spark:mongo-spark-connector_2.12:10.4.0",
            "--conf", "spark.mongodb.write.connection.uri=mongodb://admin:admin123@mongodb:27017/fraud_detection?authSource=admin",
            "/app/src/spark-processor-ml.py"
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    context.log.info(f"ML processor started (PID: {process.pid})")
    context.log.info("Processing for 2 minutes...")

    # Monitor progress
    start_time = time.time()
    target_duration = 120  # 2 minutes

    try:
        while time.time() - start_time < target_duration:
            time.sleep(15)
            current_predictions = mongodb.get_collection_count("model_predictions")
            elapsed = int(time.time() - start_time)
            context.log.info(f"  [{elapsed}s] Predictions: {current_predictions} (+{current_predictions - initial_predictions})")

            # Check if process died
            if process.poll() is not None:
                _, stderr = process.communicate()
                raise Exception(f"ML processor stopped unexpectedly: {stderr}")

    finally:
        # Stop the processor
        context.log.info("Stopping ML processor...")
        subprocess.run(["docker", "exec", "spark", "pkill", "-f", "spark-processor-ml.py"], capture_output=True)
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()

    final_predictions = mongodb.get_collection_count("model_predictions")
    final_transactions = mongodb.get_collection_count("transactions")
    predictions_made = final_predictions - initial_predictions

    context.log.info(f"✅ ML predictions complete!")
    context.log.info(f"   Predictions made: {predictions_made}")
    context.log.info(f"   Total predictions: {final_predictions}")

    return Output(
        {
            "initial_predictions": initial_predictions,
            "final_predictions": final_predictions,
            "predictions_made": predictions_made,
            "transactions_processed": final_transactions - initial_transactions,
        },
        metadata={
            "predictions_made": predictions_made,
            "total_predictions": final_predictions,
            "coverage": round(final_predictions / final_transactions * 100, 1) if final_transactions > 0 else 0,
        }
    )


@asset(
    description="Validate data quality and ML prediction accuracy",
    group_name="validation",
    deps=[run_ml_predictions_asset],
)
def validate_data_asset(
    context: AssetExecutionContext,
    mongodb: MongoDBResource
) -> Output[dict]:
    """Validate the data and ML predictions"""

    context.log.info("Running data validation...")

    # Get counts
    transactions = mongodb.get_collection_count("transactions")
    predictions = mongodb.get_collection_count("model_predictions")
    normal_count, fraud_count = mongodb.get_fraud_count()

    # Validate data exists
    validation_results = {
        "has_transactions": transactions > 0,
        "has_predictions": predictions > 0,
        "has_fraud_cases": fraud_count > 0,
        "sufficient_data": transactions >= 1000,
    }

    # Calculate coverage
    coverage = (predictions / (transactions * 3)) * 100 if transactions > 0 else 0  # *3 because 3 models

    context.log.info(f"Validation Results:")
    context.log.info(f"  Transactions: {transactions}")
    context.log.info(f"  Predictions: {predictions}")
    context.log.info(f"  Coverage: {coverage:.1f}%")
    context.log.info(f"  Normal/Fraud: {normal_count}/{fraud_count}")

    for check, passed in validation_results.items():
        status = "✅" if passed else "❌"
        context.log.info(f"  {status} {check}: {passed}")

    all_passed = all(validation_results.values())

    return Output(
        {
            **validation_results,
            "transactions": transactions,
            "predictions": predictions,
            "coverage": coverage,
            "all_checks_passed": all_passed,
        },
        metadata={
            "transactions": transactions,
            "predictions": predictions,
            "coverage_percentage": round(coverage, 1),
            "all_checks_passed": all_passed,
        }
    )


@asset(
    description="Export data to Excel files for Tableau analysis",
    group_name="export",
    deps=[validate_data_asset],
)
def export_to_excel_asset(
    context: AssetExecutionContext,
) -> Output[dict]:
    """Export MongoDB data to Excel files"""

    context.log.info("Exporting data to Excel...")

    try:
        # Run the export script
        result = subprocess.run(
            ["python", "src/export_to_excel.py"],
            capture_output=True,
            text=True,
            timeout=120
        )

        context.log.info(result.stdout)

        if result.returncode != 0:
            raise Exception(f"Export failed: {result.stderr}")

        context.log.info("✅ Export complete!")

        return Output(
            {"success": True, "exit_code": result.returncode},
            metadata={"success": True}
        )

    except Exception as e:
        context.log.error(f"Export failed: {e}")
        return Output(
            {"success": False, "error": str(e)},
            metadata={"success": False}
        )
