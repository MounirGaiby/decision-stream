#!/bin/bash
# Script to train the ML model
# Usage: ./train-model.sh

echo "========================================"
echo "Training Fraud Detection ML Model"
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
echo "Starting model training..."
echo "This will take 5-10 minutes depending on data size..."
echo ""

# Launch training
docker exec spark /opt/spark/bin/spark-submit --master local[*] --packages org.mongodb.spark:mongo-spark-connector_2.12:10.4.0 /app/train_model.py

if [ $? -eq 0 ]; then
    echo ""
    echo "[SUCCESS] Model trained successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Stop current Spark processor if running (Ctrl+C)"
    echo "2. Start ML-enabled processor: scripts/start-spark-ml.sh"
else
    echo ""
    echo "[ERROR] Model training failed!"
    echo "[TIP] Check logs with: docker logs spark"
fi
