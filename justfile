# Fraud Detection System - Infrastructure Management
# All pipeline workflows are now managed through Dagster UI
# This file only handles infrastructure setup and maintenance

set shell := ["bash", "-c"]

# Show available commands
default:
    @just --list

# =============================================================================
# Initial Setup
# =============================================================================

# Complete first-time setup
setup: install-deps
    @echo "✅ Setup complete!"
    @echo ""
    @echo "Next steps:"
    @echo "  1. Start Dagster UI: just dagster"
    @echo "  2. Open http://localhost:3000"
    @echo "  3. Run 'full_pipeline' job from Dagster UI"

# Install Python dependencies in Spark container
install-deps:
    @echo "📦 Installing Python dependencies in Spark container..."
    @echo "⏱️  This may take 3-5 minutes..."
    docker exec -u root spark bash -c "apt-get update && apt-get install -y python3-pip && python3 -m pip install --upgrade pip && pip3 install numpy pandas scikit-learn pymongo"
    @echo "✅ Dependencies installed successfully!"

# =============================================================================
# Docker Infrastructure
# =============================================================================

# Start all Docker services (can also be done via Dagster)
start:
    @echo "🚀 Starting all Docker services..."
    docker-compose up -d
    @echo "✅ Services started"
    @echo ""
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

# =============================================================================
# Dagster Orchestration
# =============================================================================

# Start Dagster UI (main interface for all workflows)
dagster:
    @echo "🚀 Starting Dagster UI..."
    @echo "   Access at: http://localhost:3000"
    @echo ""
    @./scripts/start-dagster.sh

# =============================================================================
# Monitoring & Debugging
# =============================================================================

# Quick system health check
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
    @echo "3️⃣  Web Interfaces:"
    @echo "   Dagster UI:    http://localhost:3000"
    @echo "   Mongo Express: http://localhost:8081"
    @echo "   Dozzle Logs:   http://localhost:8080"

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

# Open Mongo Express (data browser)
ui-mongo:
    @echo "🌐 Opening Mongo Express..."
    @open http://localhost:8081 || xdg-open http://localhost:8081 || echo "Open: http://localhost:8081"

# Open Dozzle (log viewer)
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
    rm -rf exports/
    @echo "✅ Cleaned up. Run 'just start' to restart"

# Clear Spark checkpoints (fixes concurrent stream errors)
clean-checkpoint:
    @echo "🧹 Clearing Spark checkpoints..."
    docker exec spark rm -rf /tmp/spark-checkpoint /tmp/spark-checkpoint-ml
    @echo "✅ Checkpoints cleared."

# Reset producer state (restart from beginning of dataset)
reset-producer:
    rm -f state/producer_state.db
    @echo "✅ Producer state reset."

# =============================================================================
# Development Shell Access
# =============================================================================

# Enter Spark container shell
shell-spark:
    docker exec -it spark bash

# Enter MongoDB shell
shell-mongo:
    docker exec -it mongodb mongosh -u admin -p admin123 --authenticationDatabase admin fraud_detection

# Show disk usage for Docker volumes
disk-usage:
    @echo "💾 Docker disk usage:"
    @docker system df
