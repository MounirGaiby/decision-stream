"""
Dagster Jobs for Fraud Detection Pipeline
Define workflows that combine assets into executable jobs
"""

from dagster import define_asset_job, AssetSelection

# Full pipeline: Run everything in sequence
full_pipeline_job = define_asset_job(
    name="full_pipeline",
    description="Complete fraud detection pipeline: accumulate → train → predict → validate → export",
    selection=AssetSelection.all(),
)

# Data accumulation only
data_accumulation_job = define_asset_job(
    name="accumulate_data",
    description="Accumulate training data from Kafka stream",
    selection=AssetSelection.assets(
        "check_services_asset",
        "accumulate_data_asset",
    ),
)

# Model training only
model_training_job = define_asset_job(
    name="train_models",
    description="Train all 3 ML models (requires accumulated data)",
    selection=AssetSelection.assets(
        "check_services_asset",
        "train_models_asset",
    ),
)

# ML prediction only
ml_prediction_job = define_asset_job(
    name="run_ml_predictions",
    description="Run ML predictions on streaming data (requires trained models)",
    selection=AssetSelection.assets(
        "check_services_asset",
        "run_ml_predictions_asset",
    ),
)

# Data validation only
data_validation_job = define_asset_job(
    name="validate_data",
    description="Validate data quality and ML prediction accuracy",
    selection=AssetSelection.assets(
        "validate_data_asset",
    ),
)
