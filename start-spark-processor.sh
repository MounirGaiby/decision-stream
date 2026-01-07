#!/bin/bash
# Script to start the Spark Processor
# Usage: ./start-spark-processor.sh

echo "========================================"
echo "Starting Spark Streaming Processor"
echo "========================================"
echo ""

# Check if Docker is running
if ! docker ps > /dev/null 2>&1; then
    echo "[ERROR] Docker is not running!"
    echo "[TIP] Start Docker Desktop and try again."
    exit 1
fi

# Check if Spark container exists
if ! docker ps --filter "name=spark" --format "{{.Names}}" | grep -q spark; then
    echo "[ERROR] Spark container not found!"
    echo "[TIP] Run first: docker-compose up -d"
    exit 1
fi

echo "[OK] Docker and Spark are ready"
echo ""
echo "Starting Spark Streaming job..."
echo ""

# Launch Spark Submit in the container
docker exec spark /opt/spark/bin/spark-submit \
    --master local[*] \
    --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.mongodb.spark:mongo-spark-connector_2.12:10.4.0 \
    --conf spark.mongodb.write.connection.uri="mongodb://admin:admin123@mongodb:27017/fraud_detection.transactions?authSource=admin" \
    /app/spark-processor.py

if [ $? -eq 0 ]; then
    echo ""
    echo "[SUCCESS] Spark job completed!"
else
    echo ""
    echo "[ERROR] Spark job failed with code: $?"
    echo "[TIP] Check logs with: docker logs spark"
fi
