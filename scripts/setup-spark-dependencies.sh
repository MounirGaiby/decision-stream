#!/bin/bash
# Script to install Python dependencies in Spark container
# Usage: ./setup-spark-dependencies.sh

echo "========================================"
echo "Installing Python dependencies in Spark"
echo "========================================"
echo ""

echo "Installing pip and Python packages..."
echo "This may take 3-5 minutes..."
echo ""

# Install pip and dependencies
docker exec -u root spark bash -c "apt-get update && apt-get install -y python3-pip && python3 -m pip install --upgrade pip && pip3 install numpy pandas scikit-learn pymongo"

if [ $? -eq 0 ]; then
    echo ""
    echo "[SUCCESS] Dependencies installed successfully!"
    echo ""
    echo "You can now train the model:"
    echo "  scripts/train-model.sh"
else
    echo ""
    echo "[ERROR] Failed to install dependencies!"
fi
