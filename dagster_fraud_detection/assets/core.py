from dagster import asset, AssetExecutionContext, Output, MetadataValue
import time
import subprocess
from ..resources import DockerResource, MongoDBResource
from .infrastructure import check_services_asset

@asset(
    description="Accumulate training data by running Spark processor (Short Batch)",
    group_name="data_pipeline",
    deps=[check_services_asset],
)
def spark_streaming_accumulator_asset(
    context: AssetExecutionContext,
    docker: DockerResource,
    mongodb: MongoDBResource
) -> Output[dict]:
    """Run Spark processor to accumulate training data."""

    # 1. Network Connectivity Check
    context.log.info("Verifying connectivity from Spark to Kafka...")
    try:
        check_cmd = [
            "docker", "exec", "spark",
            "python3", "-c",
            "import socket; s = socket.socket(); s.settimeout(5); s.connect(('kafka', 9092)); print('Connected'); s.close()"
        ]
        subprocess.run(check_cmd, check=True, capture_output=True)
        context.log.info("Spark container can reach Kafka:9092")
    except subprocess.CalledProcessError:
        raise Exception("Network Error: Spark container cannot reach 'kafka:9092'. Check docker network configuration.")

    # 2. Snapshot initial state
    initial_count = mongodb.get_collection_count("accumulated_training_data")
    context.log.info(f"Initial transaction count: {initial_count}")

    # 2.5 Clean Spark Checkpoint (Critical for re-runs on fresh topics)
    context.log.info("Cleaning Spark checkpoints...")
    subprocess.run(["docker", "exec", "spark", "rm", "-rf", "/tmp/spark-checkpoint"], check=False)

    # 3. Launch Spark Job
    cmd = [
        "docker", "exec", "spark",
        "/opt/spark/bin/spark-submit",
        "--master", "local[*]",
        "--driver-java-options", "-Dlog4j.rootCategory=WARN,console", 
        "--packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.mongodb.spark:mongo-spark-connector_2.12:10.4.0",
        "--conf", "spark.mongodb.write.connection.uri=mongodb://admin:admin123@mongodb:27017/fraud_detection.accumulated_training_data?authSource=admin",
        "/app/src/spark-processor.py"
    ]

    context.log.info("Launching Spark processor...")
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # 4. Monitor Loop
    start_time = time.time()
    target_duration = 120 
    
    try:
        while time.time() - start_time < target_duration:
            if process.poll() is not None:
                _, stderr = process.communicate()
                relevant_errors = [line for line in stderr.split('\n') 
                                   if 'Exception' in line or 'ERROR' in line or 'Caused by' in line]
                error_msg = "\n".join(relevant_errors[-10:]) if relevant_errors else stderr[-1000:]
                raise Exception(f"Spark job crashed. \nRelevant errors:\n{error_msg}")

            time.sleep(10)
            current_count = mongodb.get_collection_count("accumulated_training_data")
            elapsed = int(time.time() - start_time)
            delta = current_count - initial_count
            context.log.info(f"[{elapsed}s] Total: {current_count} (+{delta})")

    finally:
        context.log.info("Stopping Spark processor...")
        subprocess.run(["docker", "exec", "spark", "pkill", "-f", "spark-processor.py"], capture_output=True)
        
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

    # 5. Final Stats
    final_count = mongodb.get_collection_count("accumulated_training_data")
    accumulated = final_count - initial_count
    normal_count, fraud_count = mongodb.get_fraud_count()

    return Output(
        {
            "accumulated": accumulated,
            "total": final_count,
            "fraud_cases": fraud_count
        },
        metadata={
            "accumulated": accumulated,
            "total_transactions": final_count,
            "fraud_stats": f"{fraud_count}/{final_count}"
        }
    )