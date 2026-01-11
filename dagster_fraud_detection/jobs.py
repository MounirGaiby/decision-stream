"""
Dagster Jobs for Fraud Detection Pipeline
Define workflows that combine assets into executable jobs
"""

from dagster import define_asset_job, AssetSelection

# 1. Setup Job (Infrastructure Only)
setup_infrastructure_job = define_asset_job(
    name="setup_infrastructure",
    description="Start Docker services and install dependencies (Run First)",
    selection=AssetSelection.assets(
        "start_docker_services_asset",
        "install_dependencies_asset",
        "check_services_asset"
    ),
)

# 2. Full Pipeline (The Master Job)
# Contains all assets so they can be run individually or in subsets from one view.
full_pipeline_job = define_asset_job(
    name="full_pipeline",
    description="Complete Fraud Detection Platform: Access all tools (Accumulate, Train, Stream, Validate, Export)",
    selection=AssetSelection.assets(
        # Infrastructure
        "start_docker_services_asset",
        "install_dependencies_asset",
        "check_services_asset",
        
        # Data Accumulation
        "spark_streaming_accumulator_asset",
        
        # Training
        "spark_ml_training_asset",
        "spark_ml_training_full_asset",
        
        # Inference (Streaming)
        "spark_streaming_ml_inference_asset",
        "spark_streaming_ml_inference_full_asset",
        
        # Validation & Export (Manual/Ad-hoc)
        "spark_validation_asset",
        "mongo_export_asset"
    ),
)

# 3. Accumulation Only
data_accumulation_job = define_asset_job(
    name="accumulation_only",
    description="Accumulate training data from Kafka stream",
    selection=AssetSelection.assets(
        "check_services_asset",
        "spark_streaming_accumulator_asset",
    ),
)

# 4. Train on Accumulated Data
train_accumulated_job = define_asset_job(
    name="train_accumulated",
    description="Train models using data accumulated in MongoDB",
    selection=AssetSelection.assets(
        "check_services_asset",
        "spark_streaming_accumulator_asset",
        "spark_ml_training_asset",
    ),
)

# 5. Train Full Power (CSV)
train_full_job = define_asset_job(
    name="train_full_power",
    description="Train models using the full CSV dataset (Direct)",
    selection=AssetSelection.assets(
        "check_services_asset",
        "spark_ml_training_full_asset",
    ),
)

# 6. Main Pipeline (Real-time Simulation)
# Focuses on the "Production" loop: Streaming -> ML -> Storage
main_pipeline_job = define_asset_job(
    name="main_pipeline",
    description="Main Real-time Pipeline: Continuous Stream Processing & Prediction (Standard & Full)",
    selection=AssetSelection.assets(
        "check_services_asset",
        "spark_streaming_ml_inference_asset", 
        "spark_streaming_ml_inference_full_asset"
    ),
)

# 7. Export Only
export_job = define_asset_job(
    name="export_data",
    description="Export current MongoDB data to Excel",
    selection=AssetSelection.assets(
        "mongo_export_asset",
    ),
)

# 8. Reset Environment
reset_job = define_asset_job(
    name="reset_environment",
    description="Reset All: Clear MongoDB, Spark checkpoints, and Producer state",
    selection=AssetSelection.assets(
        "reset_environment_asset",
    ),
)
