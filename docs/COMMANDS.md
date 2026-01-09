# Command Reference

Complete reference for all available commands in the fraud detection system.

## Task Runner Commands (`just`)

### Setup & Infrastructure

```bash
# Complete first-time setup (starts services + installs dependencies)
just setup

# Start all Docker services
just start

# Stop all Docker services
just stop

# Restart all services
just restart

# Show container status
just status

# Install Python ML dependencies in Spark container (takes 3-5 min)
just install-deps
```

### Data Processing & ML

```bash
# Run Spark processor WITHOUT ML (accumulate training data)
just run-basic

# Run Spark processor WITH ML predictions
just run-ml

# Train the ML model (Random Forest)
just train
```

### Monitoring & Verification

```bash
# Check MongoDB data and statistics
just check

# Check ML predictions and model performance
just check-ml

# View recent logs from all services
just logs

# View logs for specific service (follows in real-time)
just log <service>
# Example: just log producer
# Example: just log spark

# Open Mongo Express web interface
just ui-mongo

# Open Dozzle logs viewer
just ui-logs
```

### Cleanup & Maintenance

```bash
# Clean up all data (WARNING: deletes everything)
just clean

# Remove trained model only
just clean-model

# Reset producer state (restart from beginning of dataset)
just reset-producer

# Show disk usage for Docker volumes
just disk-usage
```

### Development & Debugging

```bash
# Enter Spark container shell
just shell-spark

# Enter MongoDB shell
just shell-mongo

# Run Python script in Spark container
just run-script <script>
# Example: just run-script train_model.py

# Check if model exists
just check-model
```

### Complete Workflows

```bash
# Interactive workflow with prompts
just workflow-interactive

# Quick health check of entire system
just health
```

## Direct Docker Commands

### Container Management

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Stop and remove all data volumes
docker-compose down -v

# View all containers
docker ps

# View all containers (including stopped)
docker ps -a

# Restart specific service
docker restart <service>
# Example: docker restart producer
```

### Logs

```bash
# View logs (last 50 lines)
docker logs <container> --tail 50

# Follow logs in real-time
docker logs <container> --tail 50 -f

# Examples
docker logs producer --tail 50
docker logs spark --tail 50
docker logs kafka --tail 50
docker logs mongodb --tail 50
```

### Execute Commands in Containers

```bash
# Execute command in container
docker exec <container> <command>

# Execute interactive bash shell
docker exec -it <container> bash

# Examples
docker exec spark ls -la /app/models/
docker exec -it spark bash
docker exec mongodb mongosh -u admin -p admin123
```

## Spark Submit Commands (Advanced)

### Run Basic Processor

```bash
docker exec spark /opt/spark/bin/spark-submit \
  --master local[*] \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.mongodb.spark:mongo-spark-connector_2.12:10.4.0 \
  --conf spark.mongodb.write.connection.uri="mongodb://admin:admin123@mongodb:27017/fraud_detection.transactions?authSource=admin" \
  /app/spark-processor.py
```

### Run ML Processor

```bash
docker exec spark /opt/spark/bin/spark-submit \
  --master local[*] \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.mongodb.spark:mongo-spark-connector_2.12:10.4.0 \
  --conf spark.mongodb.write.connection.uri="mongodb://admin:admin123@mongodb:27017/fraud_detection.transactions?authSource=admin" \
  /app/spark-processor-ml.py
```

### Train Model

```bash
docker exec spark /opt/spark/bin/spark-submit \
  --master local[*] \
  --packages org.mongodb.spark:mongo-spark-connector_2.12:10.4.0 \
  /app/train_model.py
```

## Python Scripts (Local)

**Note:** All Python scripts must be run from within the virtual environment.

### Setup Virtual Environment

```bash
# Create venv (first time only)
python3 -m venv venv

# Activate venv (required every time)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Deactivate when done
deactivate
```

### Monitoring Scripts

```bash
# Activate venv first
source venv/bin/activate

# Check MongoDB data
python check-mongodb.py

# Check ML predictions
python check_ml_predictions.py
```

## MongoDB Commands

### MongoDB Shell

```bash
# Connect to MongoDB
docker exec -it mongodb mongosh -u admin -p admin123

# Switch to fraud_detection database
use fraud_detection

# Count documents
db.transactions.countDocuments()

# Find documents with ML predictions
db.transactions.find({fraud_prediction: {$exists: true}}).limit(5)

# Count fraud predictions
db.transactions.countDocuments({fraud_prediction: 1})

# Get statistics
db.transactions.aggregate([
  {$group: {
    _id: "$fraud_prediction",
    count: {$sum: 1},
    avgAmount: {$avg: "$Amount"}
  }}
])

# Exit
exit
```

### Mongo Express Web Interface

```
URL: http://localhost:8081
Username: admin
Password: admin123

Navigate to: fraud_detection → transactions
```

## Kafka Commands

### Check Kafka Topics

```bash
# List topics
docker exec kafka kafka-topics --list --bootstrap-server localhost:9092

# Describe topic
docker exec kafka kafka-topics --describe --topic fraud-detection-stream --bootstrap-server localhost:9092

# Check consumer groups
docker exec kafka kafka-consumer-groups --list --bootstrap-server localhost:9092
```

### Consume Messages (for debugging)

```bash
# Consume from beginning
docker exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic fraud-detection-stream \
  --from-beginning \
  --max-messages 10
```

## System Management Commands

### Stop Specific Process

```bash
# Stop basic Spark processor
docker exec spark pkill -f spark-processor.py

# Stop ML Spark processor
docker exec spark pkill -f spark-processor-ml.py

# Stop producer
docker stop producer

# Restart producer
docker restart producer
```

### Resource Monitoring

```bash
# Check Docker resource usage
docker stats

# Check disk usage
docker system df

# Check container details
docker inspect <container>

# Check network
docker network ls
docker network inspect decision-stream_default
```

## Troubleshooting Commands

### Check Service Health

```bash
# Full system health check
just health

# Check individual container status
docker ps | grep <service>

# Check container logs for errors
docker logs <container> 2>&1 | grep -i error

# Check if ports are listening
lsof -i :9092    # Kafka
lsof -i :27017   # MongoDB
lsof -i :8080    # Dozzle
lsof -i :8081    # Mongo Express
```

### Reset Everything

```bash
# Stop all services
just stop

# Remove all data
just clean

# Restart from scratch
just setup
just run-basic
```

### Debug Spark Jobs

```bash
# Access Spark UI (if configured)
open http://localhost:4040

# Check Spark logs
docker logs spark --tail 100

# Check Spark working directory
docker exec spark ls -la /tmp/spark-checkpoint
docker exec spark ls -la /tmp/spark-checkpoint-ml

# Check model directory
docker exec spark ls -la /app/models/
```

## Environment Variables

### Producer (.env file)

```env
KAGGLE_API_TOKEN=KGAT_xxxxx
KAFKA_BOOTSTRAP_SERVERS=kafka:29092
KAFKA_TOPIC=fraud-detection-stream
STATE_FILE=/app/state/producer_state.db
```

### MongoDB Connection String

```
mongodb://admin:admin123@mongodb:27017/fraud_detection.transactions?authSource=admin
```

### Kafka Connection

```
Internal (from containers): kafka:29092
External (from host): localhost:9092
```

## Quick Command Cheatsheet

```bash
# Complete workflow (one-liner)
just setup && just run-basic
# (wait 5-10 min, then Ctrl+C)
just train && just run-ml

# Monitor everything
watch -n 5 'just check'        # Auto-refresh every 5 seconds

# Quick status check
just status && just check && just check-ml

# Clean restart
just stop && just clean && just setup

# Emergency stop
docker-compose down && docker system prune -f
```

## Useful Aliases (Optional)

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
alias j='just'
alias ds-start='just start'
alias ds-stop='just stop'
alias ds-check='just check'
alias ds-health='just health'
alias ds-logs='just logs'
```

Then use:
```bash
j start
ds-check
ds-health
```
