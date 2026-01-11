# Fraud Detection System - Minimal Infrastructure Commands
# All workflows are managed through Dagster UI (http://localhost:3000)

set shell := ["bash", "-c"]

# Show available commands
default:
    @just --list

# =============================================================================
# Dagster - Main Interface
# =============================================================================

# Start Dagster UI (main interface for everything)
dagster:
    @echo "Starting Dagster UI..."
    @echo ""
    @echo "   Access at: http://localhost:3000"
    @echo ""
    @echo "Key Jobs:"
    @echo "   • setup_infrastructure: Start Services & Install Deps"
    @echo "   • full_pipeline:      End-to-End Simulation"
    @echo "   • main_pipeline:      Real-time Processing (Stream -> Predict -> Store)"
    @echo "   • train_full_power:   Train using full CSV dataset"
    @echo "   • reset_environment:  Reset DB and Stream State"
    @echo ""
    @./scripts/start-dagster.sh

# =============================================================================
# Model Management
# =============================================================================

# Replace current models with Full Power models (if trained)
replace-models:
    @echo "Swapping to Full Power models..."
    @docker exec spark bash -c " \
        if [ -d /app/models/random_forest_full ]; then \
            rm -rf /app/models/random_forest_model && mv /app/models/random_forest_full /app/models/random_forest_model; \
            echo 'Random Forest updated'; \
        else echo 'Full Random Forest not found'; fi; \
        if [ -d /app/models/gradient_boosting_full ]; then \
            rm -rf /app/models/gradient_boosting_model && mv /app/models/gradient_boosting_full /app/models/gradient_boosting_model; \
            echo 'Gradient Boosting updated'; \
        else echo 'Full Gradient Boosting not found'; fi; \
        if [ -d /app/models/logistic_regression_full ]; then \
            rm -rf /app/models/logistic_regression_model && mv /app/models/logistic_regression_full /app/models/logistic_regression_model; \
            echo 'Logistic Regression updated'; \
        else echo 'Full Logistic Regression not found'; fi; \
    "
    @echo "Done."

# Train full models using Just (Shortcut)
train-full:
    @echo "Launching Full Model Training via Spark..."
    @docker exec spark /opt/spark/bin/spark-submit /app/src/train_model_full.py

# =============================================================================
# Cleanup & Maintenance
# =============================================================================

# Clean up all data (Docker volumes, models, checkpoints, exports)
clean:
    @echo "Cleaning up all data..."
    docker-compose down -v 2>/dev/null || true
    docker exec spark rm -rf /app/models/* /tmp/spark-checkpoint* 2>/dev/null || true
    rm -rf state/producer_state.db models/ exports/ .dagster/storage .dagster/compute_logs
    @echo "Cleaned up. Run 'just dagster' to start fresh."

# Clear Spark checkpoints only (fixes stream errors)
clean-checkpoint:
    @echo "Clearing Spark checkpoints..."
    docker exec spark rm -rf /tmp/spark-checkpoint /tmp/spark-checkpoint-ml 2>/dev/null || true
    @echo "Checkpoints cleared."

# Reset producer to restart from beginning of dataset
reset-producer:
    rm -f state/producer_state.db
    @echo "Producer state reset."

# =============================================================================
# Monitoring & Debugging
# =============================================================================

# View logs for all Docker services
logs:
    @echo "Recent logs from all services:"
    @echo ""
    @echo "=== Producer ==="
    @docker logs producer --tail 20 2>/dev/null || echo "Not running"
    @echo ""
    @echo "=== Spark ==="
    @docker logs spark --tail 20 2>/dev/null || echo "Not running"
    @echo ""
    @echo "=== Kafka ==="
    @docker logs kafka --tail 20 2>/dev/null || echo "Not running"

# View logs for specific service (follow mode)
log service:
    @docker logs {{service}} --tail 50 -f

# Show status of running containers
status:
    @echo "Docker Container Status:"
    @docker ps

# Quick health check
health:
    @echo "System Health Check"
    @echo ""
    @echo "1. Docker:"
    @if docker ps > /dev/null 2>&1; then \
        echo "   Docker is running"; \
    else \
        echo "   Docker is not running"; \
    fi
    @echo ""
    @echo "2. Containers:"
    @docker ps 2>/dev/null | tail -n +2 | awk '{print "   " $NF ": " $(NF-1)}' || echo "   No containers running"
    @echo ""
    @echo "3. Web Interfaces:"
    @echo "   • Dagster UI:    http://localhost:3000"
    @echo "   • Mongo Express: http://localhost:8081"
    @echo "   • Dozzle Logs:   http://localhost:8080"

# Open Mongo Express (data browser)
ui-mongo:
    @open http://localhost:8081 || xdg-open http://localhost:8081 || echo "Open: http://localhost:8081"

# Open Dozzle (log viewer)
ui-logs:
    @open http://localhost:8080 || xdg-open http://localhost:8080 || echo "Open: http://localhost:8080"

# =============================================================================
# Development & Debugging
# =============================================================================

# Enter Spark container shell
shell-spark:
    docker exec -it spark bash

# Enter MongoDB shell
shell-mongo:
    docker exec -it mongodb mongosh -u admin -p admin123 --authenticationDatabase admin fraud_detection

# Show Docker disk usage
disk-usage:
    @echo "Docker disk usage:"
    @docker system df