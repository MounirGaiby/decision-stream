#!/bin/bash
# Script to start the Spark Processor with ML
# Usage: ./start-spark-ml.sh

echo "========================================"
echo "Starting Spark ML Streaming Processor"
echo "========================================"
echo ""

# Check if Docker is running
if ! docker ps > /dev/null 2>&1; then
    echo "[ERROR] Docker is not running!"
    echo "[TIP] Start Docker Desktop and try again."
    exit 1
fi

echo "[OK] Docker is running"
echo ""
echo "Starting Spark Streaming job with ML predictions..."
echo ""

# Launch Spark Submit with ML processor
docker exec spark /opt/spark/bin/spark-submit \
    --master local[*] \
    --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.mongodb.spark:mongo-spark-connector_2.12:10.4.0 \
    --conf spark.mongodb.write.connection.uri="mongodb://admin:admin123@mongodb:27017/fraud_detection.transactions?authSource=admin" \
    /app/spark-processor-ml.py

if [ $? -eq 0 ]; then
    echo ""
    echo "[SUCCESS] Spark job completed!"
else
    echo ""
    echo "[ERROR] Spark job failed!"
    echo "[TIP] Check logs with: docker logs spark"
fi
