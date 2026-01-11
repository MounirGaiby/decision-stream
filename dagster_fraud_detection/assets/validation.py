from dagster import asset, AssetExecutionContext, Output, MetadataValue
from ..resources import MongoDBResource
# Removed dependency import
# from .inference import run_ml_predictions_asset

@asset(
    description="Validate data quality and ML prediction accuracy",
    group_name="validation",
    # deps=[run_ml_predictions_asset], # REMOVED: Manual execution only
)
def spark_validation_asset(
    context: AssetExecutionContext,
    mongodb: MongoDBResource
) -> Output[dict]:
    """Validate the data and ML predictions"""

    context.log.info("Running data validation...")

    # Get counts
    transactions = mongodb.get_collection_count("accumulated_training_data")
    predictions = mongodb.get_collection_count("fraud_predictions")
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
        status = "Passed" if passed else "Failed"
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
