# Fraud Detection System - Task Runner
# Install just: https://github.com/casey/just#installation
# Usage: just <recipe>
# List all recipes: just --list

# Set shell for all commands
set shell := ["bash", "-c"]

# Default recipe (shows help)
default:
    @just --list

# =============================================================================
# Setup & Infrastructure
# =============================================================================

# Setup everything from scratch (first time setup)
setup: start install-deps check
    @echo "✅ Setup complete! System is ready to use."
    @echo ""
    @echo "Next steps:"
    @echo "  1. Accumulate data: just run-basic"
    @echo "  2. Train models: just train"
    @echo "  3. Run with ML: just run-ml"

# Install just command runner
install-just:
    @echo "Installing just..."
    @if command -v brew &> /dev/null; then \
        brew install just; \
    elif command -v cargo &> /dev/null; then \
        cargo install just; \
    else \
        echo "❌ Please install just manually: https://github.com/casey/just#installation"; \
        exit 1; \
    fi

# Create .env file if it doesn't exist
init-env:
    @if [ ! -f .env ]; then \
        cp .env.example .env; \
        echo "✅ Created .env file. Please add your KAGGLE_API_TOKEN"; \
        echo "⚠️  Edit .env and add: KAGGLE_API_TOKEN=KGAT_xxxxx"; \
    else \
        echo "✅ .env file already exists"; \
    fi

# Start all Docker services
start:
    @echo "🚀 Starting all Docker services..."
    docker-compose up -d
    @echo "✅ Services started"
    @just status

# Stop all Docker services
stop:
    @echo "🛑 Stopping all Docker services..."
    docker-compose down
    @echo "✅ Services stopped"

# Restart all Docker services
restart: stop start

# Show status of all containers
status:
    @echo "📊 Container Status:"
    @docker ps

# Install Python ML dependencies in Spark container
install-deps:
    @echo "📦 Installing Python dependencies in Spark container..."
    @echo "⏱️  This may take 3-5 minutes..."
    docker exec -u root spark bash -c "apt-get update && apt-get install -y python3-pip && python3 -m pip install --upgrade pip && pip3 install numpy pandas scikit-learn pymongo"
    @echo "✅ Dependencies installed successfully!"

# =============================================================================
# Benchmarking & Performance
# =============================================================================

# Run comprehensive benchmark (takes ~60 seconds)
benchmark:
    @echo "📊 Running comprehensive benchmark..."
    python3 src/benchmark_pipeline.py

# Run quick benchmark (fast statistics)
benchmark-quick:
    @echo "⚡ Running quick benchmark..."
    python3 src/quick_benchmark.py

# Run throughput measurement only (custom duration)
benchmark-throughput duration='60':
    @echo "📈 Measuring throughput for {{duration}} seconds..."
    python3 src/benchmark_pipeline.py --throughput-duration {{duration}}

# =============================================================================
# Data Processing & ML
# =============================================================================

# Run Spark processor WITHOUT ML (accumulate training data)
run-basic:
    @echo "🔄 Starting Spark processor (without ML)..."
    @echo "💡 Let this run for 5-10 minutes to accumulate ~5000 transactions"
    @echo "💡 Press Ctrl+C to stop"
    docker exec spark /opt/spark/bin/spark-submit \
        --master local[*] \
        --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.mongodb.spark:mongo-spark-connector_2.12:10.4.0 \
        --conf spark.mongodb.write.connection.uri="mongodb://admin:admin123@mongodb:27017/fraud_detection.transactions?authSource=admin" \
        /app/src/spark-processor.py

# Run Spark processor WITH ML predictions (3 models: Random Forest, Gradient Boosting, Logistic Regression)
run-ml:
    @echo "🤖 Starting Spark processor (with ML predictions - 3 models)..."
    @echo "💡 Press Ctrl+C to stop"
    docker exec spark /opt/spark/bin/spark-submit \
        --master local[*] \
        --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.mongodb.spark:mongo-spark-connector_2.12:10.4.0 \
        --conf spark.mongodb.write.connection.uri="mongodb://admin:admin123@mongodb:27017/fraud_detection?authSource=admin" \
        /app/src/spark-processor-ml.py

# Train ML models (Random Forest + Gradient Boosting + Logistic Regression)
train:
    @echo "🎓 Training fraud detection models (3 models)..."
    @echo "⏱️  This will take 10-15 minutes..."
    docker exec spark /opt/spark/bin/spark-submit \
        --master local[*] \
        --packages org.mongodb.spark:mongo-spark-connector_2.12:10.4.0 \
        /app/src/train_model.py
    @echo ""
    @echo "✅ All 3 models trained! Next step: just run-ml"

# =============================================================================
# Monitoring & Verification
# =============================================================================

# Check MongoDB data and statistics
check:
    @bash -c "source venv/bin/activate && python src/check-mongodb.py"

# Check ML predictions and model performance
check-ml:
    @bash -c "source venv/bin/activate && python src/check_ml_predictions.py"

# View logs for all services
logs:
    @echo "📋 Recent logs from all services:"
    @echo ""
    @echo "=== Producer Logs ==="
    @docker logs producer --tail 20
    @echo ""
    @echo "=== Spark Logs ==="
    @docker logs spark --tail 20
    @echo ""
    @echo "=== Kafka Logs ==="
    @docker logs kafka --tail 20

# View logs for specific service
log service:
    docker logs {{service}} --tail 50 -f

# Open web interfaces
ui-mongo:
    @echo "🌐 Opening Mongo Express..."
    @open http://localhost:8081 || xdg-open http://localhost:8081 || echo "Open: http://localhost:8081"

ui-logs:
    @echo "🌐 Opening Dozzle (log viewer)..."
    @open http://localhost:8080 || xdg-open http://localhost:8080 || echo "Open: http://localhost:8080"

# =============================================================================
# Cleanup & Maintenance
# =============================================================================

# Clean up all data and restart fresh
clean:
    @echo "🧹 Cleaning up all data..."
    docker exec spark rm -rf /app/models/random_forest_model \
        /app/models/gradient_boosting_model \
        /app/models/logistic_regression_model \
        /app/models/model_metadata.txt 2>/dev/null || true
    docker exec spark rm -rf /tmp/spark-checkpoint /tmp/spark-checkpoint-ml 2>/dev/null || true
    docker-compose down -v
    rm -rf state/producer_state.db
    rm -rf models/
    @echo "✅ Cleaned up. Run 'just start' to restart"

# Remove trained models (all 3 models)
clean-model:
    docker exec spark rm -rf /app/models/random_forest_model \
        /app/models/gradient_boosting_model \
        /app/models/logistic_regression_model \
        /app/models/model_metadata.txt
    @echo "✅ All models removed. Run 'just train' to retrain."

# Clear Spark checkpoints (fixes concurrent stream errors)
clean-checkpoint:
    @echo "🧹 Clearing Spark checkpoints..."
    docker exec spark rm -rf /tmp/spark-checkpoint /tmp/spark-checkpoint-ml
    @echo "✅ Checkpoints cleared. You can now restart the processor."

# Reset producer state (restart from beginning of dataset)
reset-producer:
    rm -f state/producer_state.db
    @echo "✅ Producer state reset. It will restart from the beginning."

# =============================================================================
# Development & Debugging
# =============================================================================

# Enter Spark container shell
shell-spark:
    docker exec -it spark bash

# Enter MongoDB shell
shell-mongo:
    docker exec -it mongodb mongosh -u admin -p admin123 --authenticationDatabase admin fraud_detection

# Run Python script in Spark container
run-script script:
    docker exec spark python /app/{{script}}

# Check if models exist (all 3 models)
check-model:
    @echo "🔍 Checking for trained models..."
    @if docker exec spark test -d /app/models/random_forest_model && \
       docker exec spark test -d /app/models/gradient_boosting_model && \
       docker exec spark test -d /app/models/logistic_regression_model; then \
        echo "✅ All 3 models found:"; \
        echo "   - Random Forest"; \
        echo "   - Gradient Boosting"; \
        echo "   - Logistic Regression"; \
        docker exec spark ls -lh /app/models/ | grep "_model"; \
    else \
        echo "❌ Not all models found. Run 'just train' first."; \
        echo "   Missing:"; \
        docker exec spark test -d /app/models/random_forest_model || echo "     - Random Forest"; \
        docker exec spark test -d /app/models/gradient_boosting_model || echo "     - Gradient Boosting"; \
        docker exec spark test -d /app/models/logistic_regression_model || echo "     - Logistic Regression"; \
    fi

# Export MongoDB data to Excel files for Tableau analysis
export-excel:
    @echo "📤 Exporting MongoDB data to Excel files..."
    python src/export_to_excel.py

# Show disk usage for Docker volumes
disk-usage:
    @echo "💾 Docker disk usage:"
    @docker system df

# =============================================================================
# Complete Workflows
# =============================================================================

# Interactive workflow: guides you through each step without breaking on stop
workflow:
    @echo "🎯 Interactive ML Workflow"
    @echo "=================================================================================="
    @echo ""
    @echo "This workflow will guide you through:"
    @echo "  1. Accumulate training data"
    @echo "  2. Train ML models"
    @echo "  3. Run with ML predictions"
    @echo "  4. Export to Excel for Tableau"
    @echo ""
    @bash -c 'read -p "Press Enter to start Step 1 (Accumulate Data)..." </dev/tty'
    
    @echo ""
    @echo "📊 Step 1/4: Accumulating Training Data"
    @echo "   Starting Spark processor..."
    @echo "   💡 Logs will show below. Let it run for 5-10 minutes."
    @echo "   ⚠️  PRESS ENTER TO STOP AND PROCEED (Do NOT use Ctrl+C)"
    @echo "   -------------------------------------------------------"
    @# Logic: Start Spark in background -> Tail logs -> Wait for Enter -> Kill Spark
    @( \
        docker exec spark /opt/spark/bin/spark-submit \
            --master local[*] \
            --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.mongodb.spark:mongo-spark-connector_2.12:10.4.0 \
            --conf spark.mongodb.write.connection.uri="mongodb://admin:admin123@mongodb:27017/fraud_detection.transactions?authSource=admin" \
            /app/src/spark-processor.py > accumulation.log 2>&1 & \
        SPARK_PID=$$!; \
        tail -f accumulation.log & \
        TAIL_PID=$$!; \
        read -p "   [Running...] Press ENTER to stop accumulation..." ; \
        kill $$TAIL_PID 2>/dev/null; \
        kill $$SPARK_PID 2>/dev/null; \
        docker exec spark pkill -f spark-processor.py 2>/dev/null || true; \
        rm -f accumulation.log; \
        echo "   ✅ Stopped accumulation." \
    )
    
    @echo ""
    @echo "✅ Step 1 complete!"
    @just check
    @echo ""
    @bash -c 'read -p "Press Enter to continue to Step 2 (Train Models)..." </dev/tty'
    
    @echo ""
    @echo "🎓 Step 2/4: Training ML Models"
    @just train
    
    @echo ""
    @bash -c 'read -p "Press Enter to continue to Step 3 (Run ML Predictions)..." </dev/tty'
    
    @echo ""
    @echo "🤖 Step 3/4: Running ML Predictions"
    @echo "   Starting Spark processor with ML..."
    @echo "   ⚠️  PRESS ENTER TO STOP AND PROCEED (Do NOT use Ctrl+C)"
    @echo "   -------------------------------------------------------"
    @( \
        docker exec spark /opt/spark/bin/spark-submit \
            --master local[*] \
            --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.mongodb.spark:mongo-spark-connector_2.12:10.4.0 \
            --conf spark.mongodb.write.connection.uri="mongodb://admin:admin123@mongodb:27017/fraud_detection?authSource=admin" \
            /app/src/spark-processor-ml.py > prediction.log 2>&1 & \
        SPARK_PID=$$!; \
        tail -f prediction.log & \
        TAIL_PID=$$!; \
        read -p "   [Running...] Press ENTER to stop predictions..." ; \
        kill $$TAIL_PID 2>/dev/null; \
        kill $$SPARK_PID 2>/dev/null; \
        docker exec spark pkill -f spark-processor-ml.py 2>/dev/null || true; \
        rm -f prediction.log; \
        echo "   ✅ Stopped predictions." \
    )
    
    @echo ""
    @echo "✅ Step 3 complete!"
    @just check-ml
    @echo ""
    @bash -c 'read -p "Press Enter to continue to Step 4 (Export to Excel)..." </dev/tty'
    
    @echo ""
    @echo "📤 Step 4/4: Exporting to Excel"
    @just export-excel
    @echo ""
    @echo "✅ Workflow Complete!"

# Quick health check of the entire system
health:
    @echo "🏥 System Health Check"
    @echo ""
    @echo "1️⃣  Docker Status:"
    @if docker ps > /dev/null 2>&1; then \
        echo "   ✅ Docker is running"; \
    else \
        echo "   ❌ Docker is not running"; \
    fi
    @echo ""
    @echo "2️⃣  Container Status:"
    @just status
    @echo ""
    @echo "3️⃣  Data Status:"
    @just check
    @echo ""
    @echo "4️⃣  Model Status:"
    @just check-model
    @echo ""
    @echo "5️⃣  Web Interfaces:"
    @echo "   Mongo Express: http://localhost:8081"
    @echo "   Dozzle Logs:   http://localhost:8080"

# =============================================================================
# Direct Training (Bypasses Kafka)
# =============================================================================

# Train models directly from CSV (Fastest method)
train-full:
    @echo "🎓 Training models directly from CSV (skipping Kafka)..."
    @# Ensure pip is up to date and install kagglehub if missing
    docker exec -u root spark pip install kagglehub > /dev/null 2>&1 || true
    @# Run the script
    docker exec spark /opt/spark/bin/spark-submit \
        --master local[*] \
        /app/src/train_model_full.py

# Promote fully trained models to be the active models
promote-full:
    @echo "🚀 Promoting fully trained models..."
    @# Clear old active models
    docker exec spark rm -rf /app/models/random_forest_model \
                             /app/models/gradient_boosting_model \
                             /app/models/logistic_regression_model
    @# Copy new models
    docker exec spark cp -r /app/models/fully_trained/random_forest_model /app/models/
    docker exec spark cp -r /app/models/fully_trained/gradient_boosting_model /app/models/
    docker exec spark cp -r /app/models/fully_trained/logistic_regression_model /app/models/
    @echo "✅ Models promoted! You can now run 'just run-ml'."

# One-step setup: Train fully and promote immediately
setup-models: train-full promote-full
# =============================================================================
# Dagster Orchestration
# =============================================================================

# Start Dagster UI (orchestration platform)
dagster:
    @echo "🚀 Starting Dagster UI..."
    @echo "   Access at: http://localhost:3000"
    @echo ""
    @./scripts/start-dagster.sh

# Run a specific Dagster job
dagster-job job:
    @echo "🚀 Running Dagster job: {{job}}..."
    @export DAGSTER_HOME=$(pwd)/.dagster && bash -c "source venv/bin/activate && dagster job execute -m dagster_fraud_detection -j {{job}}"

# List all available Dagster jobs
dagster-jobs:
    @echo "📋 Available Dagster Jobs:"
    @echo ""
    @bash -c "source venv/bin/activate && dagster job list -m dagster_fraud_detection"

# Launch full pipeline via Dagster
dagster-full:
    @just dagster-job full_pipeline

# Launch data accumulation via Dagster
dagster-accumulate:
    @just dagster-job accumulate_data

# Launch model training via Dagster
dagster-train:
    @just dagster-job train_models

# Launch ML predictions via Dagster
dagster-predict:
    @just dagster-job run_ml_predictions
