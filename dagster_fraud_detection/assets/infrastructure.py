from dagster import asset, AssetExecutionContext, Output, MetadataValue
import time
import subprocess
import os
import shutil
from ..resources import DockerResource

@asset(
    description="Start all Docker services (Kafka, MongoDB, Spark, monitoring) with FRESH CLEANUP",
    group_name="infrastructure",
)
def start_docker_services_asset(context: AssetExecutionContext) -> Output[dict]:
    """Start all required Docker services using docker-compose.
    Performs a 'clean' start by removing volumes and local state first.
    """

    context.log.info("🧹 Performing pre-start cleanup (docker-compose down -v)...")
    
    # 1. Docker Cleanup
    subprocess.run(["docker-compose", "down", "-v"], capture_output=True)
    
    # 2. Local File Cleanup
    paths_to_clean = [
        "state/producer_state.db",
        "models",
        "exports",
        ".dagster/storage",
        ".dagster/compute_logs"
    ]
    
    for path in paths_to_clean:
        try:
            if os.path.isfile(path):
                os.remove(path)
                context.log.info(f"Deleted file: {path}")
            elif os.path.isdir(path):
                shutil.rmtree(path)
                context.log.info(f"Deleted directory: {path}")
        except Exception as e:
            context.log.warning(f"Could not clean {path}: {e}")

    # Re-create necessary directories
    os.makedirs("models", exist_ok=True)
    os.makedirs("exports", exist_ok=True)
    os.makedirs("state", exist_ok=True)

    context.log.info("🚀 Starting Docker services with docker-compose...")

    try:
        # Start all services
        result = subprocess.run(
            ["docker-compose", "up", "-d"],
            capture_output=True,
            text=True,
            check=True,
            cwd=os.getcwd()
        )

        context.log.info(f"Docker Compose output: {result.stdout}")

        # Wait for services to be ready (30 seconds)
        context.log.info("Waiting for services to initialize (30 seconds)...")
        time.sleep(30)

        # Check which services started
        check_result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            check=True
        )

        running_services = check_result.stdout.strip().split("\n")
        context.log.info(f"Running services: {', '.join(running_services)}")

        return Output(
            {"status": "started", "services": running_services},
            metadata={
                "service_count": len(running_services),
                "services": MetadataValue.json(running_services),
                "startup_time": "30s"
            }
        )

    except subprocess.CalledProcessError as e:
        context.log.error(f"Failed to start Docker services: {e.stderr}")
        raise Exception(f"Docker compose failed: {e.stderr}")


@asset(
    description="Install Python ML dependencies in Spark container",
    group_name="infrastructure",
    deps=[start_docker_services_asset],
)
def install_dependencies_asset(context: AssetExecutionContext) -> Output[dict]:
    """Install required Python packages in Spark container for ML"""

    context.log.info("Installing Python dependencies in Spark container...")
    context.log.info("This may take 3-5 minutes...")

    try:
        # Install dependencies as root user
        result = subprocess.run(
            [
                "docker", "exec", "-u", "root", "spark", "bash", "-c",
                "apt-get update && apt-get install -y python3-pip && "
                "python3 -m pip install --upgrade pip && "
                "pip3 install numpy pandas scikit-learn pymongo"
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=600  # 10 minutes max
        )

        context.log.info("Dependencies installed successfully!")

        # Verify installations
        verify_result = subprocess.run(
            ["docker", "exec", "spark", "python3", "-c",
             "import numpy, pandas, sklearn, pymongo; print('All imports successful')"],
            capture_output=True,
            text=True,
            check=True
        )

        context.log.info(f"Verification: {verify_result.stdout}")

        return Output(
            {"status": "installed", "packages": ["numpy", "pandas", "scikit-learn", "pymongo"]},
            metadata={
                "packages_installed": 4,
                "installation_time": "3-5 minutes"
            }
        )

    except subprocess.CalledProcessError as e:
        context.log.error(f"Failed to install dependencies: {e.stderr}")
        raise Exception(f"Dependency installation failed: {e.stderr}")
    except subprocess.TimeoutExpired:
        context.log.error("Installation timed out after 10 minutes")
        raise Exception("Dependency installation timed out")


@asset(
    description="Check services and ensure Kafka topic exists",
    group_name="infrastructure",
    deps=[install_dependencies_asset],
)
def check_services_asset(context: AssetExecutionContext, docker: DockerResource) -> Output[dict]:
    """Verify Docker services and create required Kafka topics."""
    # Added producer to the list of required services
    required_services = ["kafka", "mongodb", "spark", "mongo-express", "dozzle", "producer"]
    service_status = {}

    context.log.info("Checking Docker services...")
    for service in required_services:
        status = docker.get_container_status(service)
        service_status[service] = status
        
        # Producer is allowed to be 'exited' (finished job)
        if service == "producer" and status == "exited":
            context.log.info(f"Service {service} has finished (status: exited). This is acceptable.")
            continue

        if status != "running":
            raise Exception(f"Service {service} is not running (status: {status})")

    context.log.info("Ensuring Kafka topic 'fraud-detection-stream' exists...")
    try:
        cmd = [
            "docker", "exec", "kafka",
            "kafka-topics.sh", "--create", "--if-not-exists",
            "--bootstrap-server", "kafka:9092",
            "--topic", "fraud-detection-stream",
            "--partitions", "1",
            "--replication-factor", "1"
        ]
        
        subprocess.run(cmd, capture_output=True, check=False) 
        context.log.info("Kafka topic check/creation attempted.")
    except Exception as e:
        context.log.warning(f"Could not auto-create topic (Spark might fail if topic is missing): {e}")

    return Output(
        service_status,
        metadata={
            "services_checked": len(required_services),
            "all_running": True,
            "details": MetadataValue.json(service_status),
        }
    )
