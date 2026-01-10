#!/bin/bash
# Start Dagster Web Server
# Access the UI at http://localhost:3000

echo "========================================"
echo "Starting Dagster Web Server"
echo "========================================
"

# Set Dagster home directory
export DAGSTER_HOME=$(pwd)/.dagster

# Create dagster home if it doesn't exist
mkdir -p $DAGSTER_HOME

echo "[INFO] Dagster Home: $DAGSTER_HOME"
echo ""

# Check if services are running
echo "[INFO] Checking Docker services..."
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "kafka|mongodb|spark"
echo ""

# Activate venv
if [ -d "venv" ]; then
    echo "[INFO] Activating virtual environment..."
    source venv/bin/activate
else
    echo "[WARNING] Virtual environment not found. Run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

echo ""
echo "========================================"
echo "🚀 Starting Dagster UI"
echo "========================================"
echo ""
echo "Access the Dagster UI at: http://localhost:3000"
echo ""
echo "Available jobs:"
echo "  - full_pipeline: Complete workflow"
echo "  - accumulate_data: Data accumulation only"
echo "  - train_models: Model training only"
echo "  - run_ml_predictions: ML predictions only"
echo "  - validate_data: Data validation only"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Start Dagster webserver
dagster-webserver -h 0.0.0.0 -p 3000 -w workspace.yaml
