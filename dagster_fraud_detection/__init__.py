"""
Dagster Fraud Detection Pipeline
Orchestrates the entire fraud detection workflow with visibility and control
"""

from dagster import Definitions

from .assets import (
    start_docker_services_asset,
    install_dependencies_asset,
    check_services_asset,
    accumulate_data_asset,
    train_models_asset,
    run_ml_predictions_asset,
    validate_data_asset,
    export_to_excel_asset,
)
from .jobs import (
    full_pipeline_job,
    data_accumulation_job,
    model_training_job,
    ml_prediction_job,
    data_validation_job,
)
from .resources import docker_resource, mongodb_resource

# Define all assets, jobs, and resources
defs = Definitions(
    assets=[
        start_docker_services_asset,
        install_dependencies_asset,
        check_services_asset,
        accumulate_data_asset,
        train_models_asset,
        run_ml_predictions_asset,
        validate_data_asset,
        export_to_excel_asset,
    ],
    jobs=[
        full_pipeline_job,
        data_accumulation_job,
        model_training_job,
        ml_prediction_job,
        data_validation_job,
    ],
    resources={
        "docker": docker_resource,
        "mongodb": mongodb_resource,
    },
)
