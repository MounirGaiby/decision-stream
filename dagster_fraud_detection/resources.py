"""
Dagster Resources for Fraud Detection Pipeline
Provides reusable resources for Docker, MongoDB, and other services
"""

import docker
import subprocess
import time
from pymongo import MongoClient
from dagster import ConfigurableResource
from typing import Optional


class DockerResource(ConfigurableResource):
    """Resource for managing Docker containers"""

    def get_container_status(self, container_name: str) -> str:
        """Get the status of a Docker container"""
        try:
            client = docker.from_env()
            container = client.containers.get(container_name)
            return container.status
        except docker.errors.NotFound:
            return "not_found"
        except Exception as e:
            return f"error: {str(e)}"

    def is_container_running(self, container_name: str) -> bool:
        """Check if a Docker container is running"""
        return self.get_container_status(container_name) == "running"

    def exec_command(self, container_name: str, command: str, timeout: int = 300) -> tuple[int, str]:
        """Execute a command in a Docker container

        Returns:
            tuple: (exit_code, output)
        """
        try:
            result = subprocess.run(
                f"docker exec {container_name} {command}",
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return -1, f"Command timed out after {timeout} seconds"
        except Exception as e:
            return -1, f"Error: {str(e)}"

    def exec_spark_submit(self, script_path: str, packages: Optional[str] = None,
                         config: Optional[dict] = None) -> tuple[int, str]:
        """Execute a Spark submit command

        Args:
            script_path: Path to Python script inside /app
            packages: Maven packages (comma-separated)
            config: Dictionary of Spark configurations

        Returns:
            tuple: (exit_code, output)
        """
        cmd_parts = [
            "/opt/spark/bin/spark-submit",
            "--master local[*]",
        ]

        if packages:
            cmd_parts.append(f"--packages {packages}")

        if config:
            for key, value in config.items():
                cmd_parts.append(f"--conf {key}={value}")

        cmd_parts.append(script_path)
        command = " ".join(cmd_parts)

        return self.exec_command("spark", command, timeout=900)  # 15 min timeout


class MongoDBResource(ConfigurableResource):
    """Resource for MongoDB connections and operations"""

    host: str = "localhost"
    port: int = 27017
    username: str = "admin"
    password: str = "admin123"
    database: str = "fraud_detection"

    def get_client(self) -> MongoClient:
        """Get MongoDB client connection"""
        connection_string = f"mongodb://{self.username}:{self.password}@{self.host}:{self.port}/?authSource=admin"
        return MongoClient(connection_string)

    def get_collection_count(self, collection_name: str) -> int:
        """Get count of documents in a collection"""
        client = self.get_client()
        db = client[self.database]
        count = db[collection_name].count_documents({})
        client.close()
        return count

    def get_fraud_count(self) -> tuple[int, int]:
        """Get counts of normal and fraud transactions

        Returns:
            tuple: (normal_count, fraud_count)
        """
        client = self.get_client()
        db = client[self.database]

        normal_count = db.transactions.count_documents({"Class": 0.0})
        fraud_count = db.transactions.count_documents({"Class": 1.0})

        client.close()
        return normal_count, fraud_count

    def clear_collection(self, collection_name: str) -> int:
        """Clear all documents from a collection

        Returns:
            int: Number of documents deleted
        """
        client = self.get_client()
        db = client[self.database]
        result = db[collection_name].delete_many({})
        client.close()
        return result.deleted_count

    def collection_exists(self, collection_name: str) -> bool:
        """Check if a collection exists and has documents"""
        return self.get_collection_count(collection_name) > 0


# Resource instances
docker_resource = DockerResource()
mongodb_resource = MongoDBResource()
