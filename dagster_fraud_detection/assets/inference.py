from dagster import asset, AssetExecutionContext, Output, MetadataValue
import time
import subprocess
from ..resources import DockerResource, MongoDBResource
from .infrastructure import check_services_asset

def run_inference_logic(context, docker, mongodb, model_type="standard"):
    """Shared logic for running inference with different model types"""
    context.log.info(f"Starting ML prediction processor (Mode: {model_type})...")

    # Check models exist
    # Standard: /app/models/random_forest_model
    # Full: /app/models/random_forest_full
    suffix = "_full" if model_type == "full" else "_model"
    check_path = f"/app/models/random_forest{suffix}"
    
    exit_code, _ = docker.exec_command("spark", f"test -d {check_path}")
    if exit_code != 0:
        raise Exception(f"Models not found at {check_path}. Run {model_type} training first.")

    # Get initial counts (CORRECTED: Monitoring 'fraud_predictions' and 'live_stream_events')
    initial_transactions = mongodb.get_collection_count("live_stream_events")
    initial_predictions = mongodb.get_collection_count("fraud_predictions")

    context.log.info(f"Initial state:")
    context.log.info(f"  Events: {initial_transactions}")
    context.log.info(f"  Predictions: {initial_predictions}")

    # Clean Spark Checkpoint (Critical for re-runs on fresh topics)
    context.log.info("Cleaning Spark ML checkpoints...")
    subprocess.run(["docker", "exec", "spark", "rm", "-rf", "/tmp/spark-checkpoint-fast"], check=False)

    # Start ML processor in background
    context.log.info("Starting ML processor...")

    cmd = [
        "docker", "exec", "spark",
        "/opt/spark/bin/spark-submit",
        "--master", "local[*]",
        "--packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.mongodb.spark:mongo-spark-connector_2.12:10.4.0",
        "--conf", "spark.mongodb.write.connection.uri=mongodb://admin:admin123@mongodb:27017/fraud_detection?authSource=admin",
        "/app/src/spark-processor-ml.py",
        "--model-type", model_type
    ]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    context.log.info(f"ML processor started (PID: {process.pid})")
    context.log.info("Processing indefinitely (Continuous Mode)...")

    # Monitor progress
    start_time = time.time()
    # target_duration = 3600 * 24 # effectively infinite for a demo session (24 hours)
    
    try:
        # Loop forever (or until manually stopped via Dagster UI cancellation)
        while True:
            time.sleep(15)
            current_predictions = mongodb.get_collection_count("fraud_predictions")
            elapsed = int(time.time() - start_time)
            delta = current_predictions - initial_predictions
            
            context.log.info(f"  [{elapsed}s] Predictions: {current_predictions} (+{delta})")

            # Check if process died
            if process.poll() is not None:
                _, stderr = process.communicate()
                raise Exception(f"ML processor stopped unexpectedly: {stderr}")

    except KeyboardInterrupt:
        context.log.info("Received stop signal (KeyboardInterrupt).")
    except Exception as e:
        # Dagster cancellation often raises specific exceptions or interrupts
        context.log.info(f"Stopping due to: {e}")
        raise e
    finally:
        # Stop the processor
        context.log.info("Stopping ML processor...")
        subprocess.run(["docker", "exec", "spark", "pkill", "-f", "spark-processor-ml.py"], capture_output=True)
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()

    # If we ever reach here (unlikely in infinite loop unless crashed or stopped), return stats
    final_predictions = mongodb.get_collection_count("fraud_predictions")
    final_transactions = mongodb.get_collection_count("live_stream_events")
    predictions_made = final_predictions - initial_predictions

    return Output(
        {
            "predictions_made": predictions_made,
            "total_predictions": final_predictions,
            "model_type": model_type
        },
        metadata={
            "predictions_made": predictions_made,
            "total_predictions": final_predictions,
            "coverage": round(final_predictions / final_transactions * 100, 1) if final_transactions > 0 else 0,
            "model_type": model_type
        }
    )

@asset(
    description="Main Pipeline: Stream & Predict using STANDARD trained models",
    group_name="inference",
    deps=[check_services_asset],
)
def spark_streaming_ml_inference_asset(
    context: AssetExecutionContext,
    docker: DockerResource,
    mongodb: MongoDBResource
) -> Output[dict]:
    """Run ML predictions using STANDARD models"""
    return run_inference_logic(context, docker, mongodb, model_type="standard")

@asset(
    description="Main Pipeline: Stream & Predict using FULL POWER trained models",
    group_name="inference",
    deps=[check_services_asset],
)
def spark_streaming_ml_inference_full_asset(
    context: AssetExecutionContext,
    docker: DockerResource,
    mongodb: MongoDBResource
) -> Output[dict]:
    """Run ML predictions using FULL models"""
    return run_inference_logic(context, docker, mongodb, model_type="full")
