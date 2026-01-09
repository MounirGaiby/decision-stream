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
    @echo "  2. Train model: just train"
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

# Run Spark processor WITH ML predictions
run-ml:
    @echo "🤖 Starting Spark processor (with ML predictions)..."
    @echo "💡 Press Ctrl+C to stop"
    docker exec spark /opt/spark/bin/spark-submit \
        --master local[*] \
        --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.mongodb.spark:mongo-spark-connector_2.12:10.4.0 \
        --conf spark.mongodb.write.connection.uri="mongodb://admin:admin123@mongodb:27017/fraud_detection.transactions?authSource=admin" \
        /app/src/spark-processor-ml.py

# Train the ML model (Random Forest - single model)
train:
    @echo "🎓 Training fraud detection model..."
    @echo "⏱️  This will take 5-10 minutes..."
    docker exec spark /opt/spark/bin/spark-submit \
        --master local[*] \
        --packages org.mongodb.spark:mongo-spark-connector_2.12:10.4.0 \
        /app/src/train_model.py
    @echo ""
    @echo "✅ Model trained! Next step: just run-ml"

# Train ensemble models (Random Forest + Gradient Boosting + Logistic Regression)
train-ensemble:
    @echo "🎓 Training ensemble models (3 models)..."
    @echo "⏱️  This will take 10-15 minutes..."
    docker exec spark /opt/spark/bin/spark-submit \
        --master local[*] \
        --packages org.mongodb.spark:mongo-spark-connector_2.12:10.4.0 \
        /app/src/train_models_ensemble.py
    @echo ""
    @echo "✅ All 3 models trained! Next step: just run-ensemble"

# Run Spark processor WITH ensemble ML predictions (3 models)
run-ensemble:
    @echo "🤖 Starting Ensemble ML processor (3 models + voting)..."
    @echo "💡 Press Ctrl+C to stop"
    docker exec spark /opt/spark/bin/spark-submit \
        --master local[*] \
        --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.mongodb.spark:mongo-spark-connector_2.12:10.4.0 \
        --conf spark.mongodb.write.connection.uri="mongodb://admin:admin123@mongodb:27017/fraud_detection?authSource=admin" \
        /app/src/spark-processor-ensemble.py

# =============================================================================
# Monitoring & Verification
# =============================================================================

# Check MongoDB data and statistics
check:
    @bash -c "source venv/bin/activate && python src/check-mongodb.py"

# Check ML predictions and model performance
check-ml:
    @bash -c "source venv/bin/activate && python src/check_ml_predictions.py"

# Check ensemble predictions (3 models + flagged transactions)
check-ensemble:
    @bash -c "source venv/bin/activate && python src/check_ensemble.py"

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
    @echo "🧹 Cleaning up..."
    @echo "⚠️  This will delete all data!"
    @read -p "Are you sure? (y/N) " -n 1 -r; \
    echo ""; \
    if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
        docker-compose down -v; \
        rm -rf state/producer_state.db; \
        echo "✅ Cleaned up. Run 'just start' to restart"; \
    else \
        echo "❌ Cancelled"; \
    fi

# Remove trained model
clean-model:
    docker exec spark rm -rf /app/models/fraud_detection_model /app/models/feature_metadata.txt
    @echo "✅ Model removed. Run 'just train' to retrain."

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
    docker exec -it mongodb mongosh -u admin -p admin123

# Run Python script in Spark container
run-script script:
    docker exec spark python /app/{{script}}

# Check if model exists
check-model:
    @if docker exec spark test -d /app/models/fraud_detection_model; then \
        echo "✅ Model exists at /app/models/fraud_detection_model"; \
        docker exec spark ls -lh /app/models/; \
    else \
        echo "❌ No model found. Run 'just train' first."; \
    fi

# Show disk usage for Docker volumes
disk-usage:
    @echo "💾 Docker disk usage:"
    @docker system df

# =============================================================================
# Complete Workflows
# =============================================================================

# Complete workflow: accumulate data, train model, run with ML
workflow:
    @echo "🔄 Starting complete ML workflow..."
    @echo ""
    @echo "Step 1/4: Checking setup..."
    @just status
    @echo ""
    @echo "Step 2/4: You need to run 'just run-basic' and let it accumulate data"
    @echo "         Press Ctrl+C after 5-10 minutes (5000+ transactions)"
    @echo ""
    @echo "Step 3/4: After stopping, run 'just train' to train the model"
    @echo ""
    @echo "Step 4/4: Finally, run 'just run-ml' to use ML predictions"
    @echo ""
    @echo "Or use the interactive workflow: just workflow-interactive"

# Interactive workflow with prompts
workflow-interactive:
    @echo "🎯 Interactive ML Workflow"
    @echo ""
    @just check
    @echo ""
    @read -p "Start basic processor to accumulate data? (y/N) " -n 1 -r; \
    echo ""; \
    if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
        echo "Starting processor... Press Ctrl+C after 5-10 minutes"; \
        just run-basic; \
    fi
    @echo ""
    @just check
    @echo ""
    @read -p "Train model now? (y/N) " -n 1 -r; \
    echo ""; \
    if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
        just train; \
    fi
    @echo ""
    @read -p "Start ML-enabled processor? (y/N) " -n 1 -r; \
    echo ""; \
    if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
        just run-ml; \
    fi

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
