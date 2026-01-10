# Fraud Detection System - Makefile
# Usage: make <target>
# List all targets: make help

.PHONY: help setup start stop restart status install-deps run-basic run-ml train check check-ml logs clean clean-model reset-producer shell-spark shell-mongo check-model health ui-mongo ui-logs

# Default target
.DEFAULT_GOAL := help

# =============================================================================
# Help
# =============================================================================

help: ## Show this help message
	@echo "Fraud Detection System - Available Commands"
	@echo ""
	@echo "Setup & Infrastructure:"
	@echo "  make setup          - Complete first-time setup"
	@echo "  make start          - Start all Docker services"
	@echo "  make stop           - Stop all Docker services"
	@echo "  make restart        - Restart all services"
	@echo "  make status         - Show container status"
	@echo "  make install-deps   - Install Python ML dependencies in Spark"
	@echo ""
	@echo "Data Processing & ML:"
	@echo "  make run-basic      - Run Spark processor without ML"
	@echo "  make run-ml         - Run Spark processor with ML predictions"
	@echo "  make train          - Train the ML model"
	@echo ""
	@echo "Monitoring:"
	@echo "  make check          - Check MongoDB data statistics"
	@echo "  make check-ml       - Check ML predictions performance"
	@echo "  make logs           - View logs for all services"
	@echo "  make health         - Complete system health check"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean          - Clean all data and restart fresh"
	@echo "  make clean-model    - Remove trained model"
	@echo "  make reset-producer - Reset producer state"
	@echo ""
	@echo "Development:"
	@echo "  make shell-spark    - Enter Spark container"
	@echo "  make shell-mongo    - Enter MongoDB shell"
	@echo "  make check-model    - Check if model exists"
	@echo ""
	@echo "UI:"
	@echo "  make ui-mongo       - Open Mongo Express"
	@echo "  make ui-logs        - Open Dozzle log viewer"

# =============================================================================
# Setup & Infrastructure
# =============================================================================

setup: install-deps start check ## Complete first-time setup
	@echo "✅ Setup complete! System is ready."
	@echo ""
	@echo "Next steps:"
	@echo "  1. make run-basic  - Accumulate data"
	@echo "  2. make train      - Train model"
	@echo "  3. make run-ml     - Run with ML"

init-env: ## Create .env file from example
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✅ Created .env file. Please add your KAGGLE_API_TOKEN"; \
	else \
		echo "✅ .env file already exists"; \
	fi

start: ## Start all Docker services
	@echo "🚀 Starting all Docker services..."
	docker-compose up -d
	@echo "✅ Services started"
	@$(MAKE) status

stop: ## Stop all Docker services
	@echo "🛑 Stopping all Docker services..."
	docker-compose down
	@echo "✅ Services stopped"

restart: stop start ## Restart all Docker services

status: ## Show status of all containers
	@echo "📊 Container Status:"
	@docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

install-deps: ## Install Python ML dependencies in Spark container
	@echo "📦 Installing Python dependencies in Spark container..."
	@echo "⏱️  This may take 3-5 minutes..."
	docker exec -u root spark bash -c "apt-get update && apt-get install -y python3-pip && python3 -m pip install --upgrade pip && pip3 install numpy pandas scikit-learn pymongo"
	@echo "✅ Dependencies installed successfully!"

# =============================================================================
# Data Processing & ML
# =============================================================================

run-basic: ## Run Spark processor without ML
	@echo "🔄 Starting Spark processor (without ML)..."
	@echo "💡 Let this run for 5-10 minutes to accumulate ~5000 transactions"
	@echo "💡 Press Ctrl+C to stop"
	docker exec spark /opt/spark/bin/spark-submit \
		--master local[*] \
		--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.mongodb.spark:mongo-spark-connector_2.12:10.4.0 \
		--conf spark.mongodb.write.connection.uri="mongodb://admin:admin123@mongodb:27017/fraud_detection.transactions?authSource=admin" \
		/app/spark-processor.py

run-ml: ## Run Spark processor with ML predictions
	@echo "🤖 Starting Spark processor (with ML predictions)..."
	@echo "💡 Press Ctrl+C to stop"
	docker exec spark /opt/spark/bin/spark-submit \
		--master local[*] \
		--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.mongodb.spark:mongo-spark-connector_2.12:10.4.0 \
		--conf spark.mongodb.write.connection.uri="mongodb://admin:admin123@mongodb:27017/fraud_detection.transactions?authSource=admin" \
		/app/spark-processor-ml.py

train: ## Train the ML model
	@echo "🎓 Training fraud detection model..."
	@echo "⏱️  This will take 5-10 minutes..."
	docker exec spark /opt/spark/bin/spark-submit \
		--master local[*] \
		--packages org.mongodb.spark:mongo-spark-connector_2.12:10.4.0 \
		/app/train_model.py
	@echo ""
	@echo "✅ Model trained! Next: make run-ml"

# =============================================================================
# Monitoring & Verification
# =============================================================================

check: ## Check MongoDB data and statistics
	@bash -c "source venv/bin/activate && python src/check-mongodb.py"

check-ml: ## Check ML predictions and performance
	@bash -c "source venv/bin/activate && python src/check_ml_predictions.py"

logs: ## View logs for all services
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

log-%: ## View logs for specific service (e.g., make log-spark)
	docker logs $* --tail 50 -f

ui-mongo: ## Open Mongo Express in browser
	@echo "🌐 Opening Mongo Express..."
	@open http://localhost:8081 2>/dev/null || xdg-open http://localhost:8081 2>/dev/null || echo "Open: http://localhost:8081"

ui-logs: ## Open Dozzle log viewer in browser
	@echo "🌐 Opening Dozzle..."
	@open http://localhost:8080 2>/dev/null || xdg-open http://localhost:8080 2>/dev/null || echo "Open: http://localhost:8080"

# =============================================================================
# Cleanup & Maintenance
# =============================================================================

clean: ## Clean up all data and restart fresh
	@echo "🧹 Cleaning up..."
	@echo "⚠️  This will delete all data!"
	@read -p "Are you sure? (yes/no) " REPLY; \
	if [ "$$REPLY" = "yes" ]; then \
		docker-compose down -v; \
		rm -rf state/producer_state.db; \
		echo "✅ Cleaned up. Run 'make start' to restart"; \
	else \
		echo "❌ Cancelled"; \
	fi

clean-model: ## Remove trained model
	docker exec spark rm -rf /app/models/random_forest_model /app/models/gradient_boosting_model /app/models/logistic_regression_model /app/models/model_metadata.txt
	@echo "✅ Model removed. Run 'make train' to retrain."

reset-producer: ## Reset producer state
	rm -f state/producer_state.db
	@echo "✅ Producer state reset."

# =============================================================================
# Development & Debugging
# =============================================================================

shell-spark: ## Enter Spark container shell
	docker exec -it spark bash

shell-mongo: ## Enter MongoDB shell
	docker exec -it mongodb mongosh -u admin -p admin123

check-model: ## Check if model exists
	@if docker exec spark test -d /app/models/random_forest_model 2>/dev/null && \
	   docker exec spark test -d /app/models/gradient_boosting_model 2>/dev/null && \
	   docker exec spark test -d /app/models/logistic_regression_model 2>/dev/null; then \
		echo "✅ All 3 models exist"; \
		docker exec spark ls -lh /app/models/; \
	else \
		echo "❌ No model found. Run 'make train' first."; \
	fi

disk-usage: ## Show Docker disk usage
	@echo "💾 Docker disk usage:"
	@docker system df

# =============================================================================
# Health & Status
# =============================================================================

health: ## Complete system health check
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
	@$(MAKE) status
	@echo ""
	@echo "3️⃣  Data Status:"
	@$(MAKE) check
	@echo ""
	@echo "4️⃣  Model Status:"
	@$(MAKE) check-model
	@echo ""
	@echo "5️⃣  Web Interfaces:"
	@echo "   Mongo Express: http://localhost:8081"
	@echo "   Dozzle Logs:   http://localhost:8080"
