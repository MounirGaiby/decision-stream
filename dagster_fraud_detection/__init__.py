"""
Dagster Fraud Detection Pipeline
Orchestrates the entire fraud detection workflow with visibility and control
"""

from dagster import Definitions

from .assets import (
    start_docker_services_asset,
    install_dependencies_asset,
    check_services_asset,
    spark_streaming_accumulator_asset,
    spark_ml_training_asset,
    spark_ml_training_full_asset,
    spark_streaming_ml_inference_asset,
    spark_streaming_ml_inference_full_asset,
    spark_validation_asset,
    mongo_export_asset,
    reset_environment_asset,
)
from .jobs import (
    setup_infrastructure_job,
    full_pipeline_job,
    data_accumulation_job,
    train_accumulated_job,
    train_full_job,
    main_pipeline_job,
    export_job,
    reset_job,
)
from .resources import docker_resource, mongodb_resource

# Define all assets, jobs, and resources
defs = Definitions(
    assets=[
        start_docker_services_asset,
        install_dependencies_asset,
        check_services_asset,
        spark_streaming_accumulator_asset,
        spark_ml_training_asset,
        spark_ml_training_full_asset,
        spark_streaming_ml_inference_asset,
        spark_streaming_ml_inference_full_asset,
        spark_validation_asset,
        mongo_export_asset,
        reset_environment_asset,
    ],
    jobs=[
        setup_infrastructure_job,
        full_pipeline_job,
        data_accumulation_job,
        train_accumulated_job,
        train_full_job,
        main_pipeline_job,
        export_job,
        reset_job,
    ],
    resources={
        "docker": docker_resource,
        "mongodb": mongodb_resource,
    },
)
