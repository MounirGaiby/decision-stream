# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## IMPORTANT: Virtual Environment Usage

**ALWAYS use the virtual environment for Python commands:**
- Before running ANY Python scripts or pip commands, activate the venv: `source venv/bin/activate`
- Never install packages globally - always use `pip install` within the activated venv
- All monitoring scripts (check-mongodb.py, check_ml_predictions.py) MUST be run from within the venv
- If new Python dependencies are needed, add them to `requirements.txt` first, then install via `pip install -r requirements.txt`

**Quick setup:**
```bash
# Create venv (if doesn't exist)
python3 -m venv venv

# Activate venv (required before any Python work)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## IMPORTANT: Git Commit Policy

**NEVER add Claude co-authored attribution to commits:**
- Do NOT add `Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>` to commit messages
- Keep commits clean and professional for class presentations
- Use simple, descriptive commit messages without co-author tags

## Project Overview

This is a real-time fraud detection system built for Big Data processing. It ingests credit card transaction data from Kaggle, processes it through a streaming pipeline (Kafka → Spark → MongoDB), and uses Machine Learning (Random Forest) to detect fraudulent transactions in real-time.

**Key Components:**
- **Data Ingestion**: Python producer streams transactions from Kaggle dataset to Kafka
- **Stream Processing**: Spark Streaming reads from Kafka, processes data, and writes to MongoDB
- **Machine Learning**: SparkML Random Forest classifier trained on accumulated data for fraud prediction
- **Storage**: MongoDB stores all transactions with optional ML predictions
- **Monitoring**: Dozzle (logs), Mongo Express (data browser)

## Architecture Flow

```
Kaggle Dataset → Producer (Python) → Kafka → Spark Streaming → MongoDB
                                              ↓
                                       SparkML (Random Forest)
                                              ↓
                                    Real-time Predictions
```

**Two Processing Modes:**
1. **Data Accumulation Mode** (`spark-processor.py`): No ML predictions, just stores transactions
2. **ML Mode** (`spark-processor-ml.py`): Loads trained model and adds fraud predictions to each transaction

## Development Commands

### Recommended: Task Runner (just)

This project uses **`just`** for simplified, reproducible commands:

- Install: `brew install just` (macOS) or `cargo install just`
- Usage: `just --list` to see all commands
- Example: `just setup`, `just run-basic`, `just train`, `just run-ml`

See [COMMANDS.md](COMMANDS.md) for complete reference.

### Infrastructure Setup

**With just (Recommended):**
```bash
# Complete first-time setup (starts services, installs dependencies)
just setup

# Start services only
just start

# Check status
just status

# Install Python ML dependencies in Spark container
just install-deps
```

**Manual Method (Docker + Scripts):**
```bash
# Start all Docker services (Kafka, MongoDB, Spark, Producer, etc.)
docker-compose up -d

# Verify all 6 containers are running
docker ps

# Install Python ML dependencies in Spark container (required once)
scripts/setup-spark-dependencies.sh  # macOS/Linux
```

**Services:**
- Kafka: `localhost:9092` (Internal: `kafka:29092`)
- MongoDB: `localhost:27017` (admin/admin123)
- Mongo Express: `http://localhost:8081`
- Dozzle (logs): `http://localhost:8080`

## Typical Development Workflow

**Quick Start with just:**
```bash
just setup              # First-time setup
just run-basic          # Accumulate data (5-10 min)
just check              # Monitor progress
just train              # Train model (after Ctrl+C)
just run-ml             # Run with ML
just check-ml           # Verify predictions
just health             # System health check
```

**Detailed Workflow:**

**Phase 1: Accumulate Training Data**
```bash
# Start basic processor (no ML)
just run-basic

# Monitor progress in another terminal
just check

# Let it run for 5-10 minutes to accumulate ~5000+ transactions
# Press Ctrl+C to stop when ready
```

**Phase 2: Train ML Model**
```bash
# Train the model on accumulated data
just train

# This runs: docker exec spark python /app/train_model.py
# Output: /app/models/fraud_detection_model
```

**Phase 3: Run with ML Predictions**
```bash
# Start ML-enabled processor
just run-ml

# Verify predictions in another terminal
just check-ml
```

## Code Architecture

### Producer (`producer.py`)
- Downloads Kaggle credit card fraud dataset (284K transactions)
- Uses SQLite (`state/producer_state.db`) to track progress - supports pause/resume
- Streams transactions to Kafka at ~0.1s intervals
- Automatically creates Kafka topic if missing

**State Management**: Producer tracks last sent index in SQLite, allowing it to resume after restarts without re-sending data.

### Spark Processors

**`spark-processor.py`** (Basic mode):
- Reads from Kafka topic `fraud-detection-stream`
- Parses JSON using predefined schema (31 fields: Time, V1-V28, Amount, Class)
- Adds `processed_at` timestamp
- Writes to MongoDB using `foreachBatch` for reliability
- Prints batch statistics (normal vs fraud counts)

**`spark-processor-ml.py`** (ML mode):
- Everything from basic mode, PLUS:
- Loads trained model from `/app/models/fraud_detection_model`
- Applies model to each micro-batch
- Adds two fields: `fraud_prediction` (0/1), `fraud_probability` (0.0-1.0)
- Prints per-batch accuracy and high-risk alerts

**Key Implementation Details:**
- Both processors use checkpoint locations (`/tmp/spark-checkpoint` vs `/tmp/spark-checkpoint-ml`) to track Kafka offsets
- Schema matches Kaggle dataset: 28 PCA components (V1-V28), Amount, Class (label)
- MongoDB writes use `append` mode with `foreachBatch` for exactly-once semantics

### Model Training (`train_model.py`)

**Pipeline:**
1. Load data from MongoDB (requires 100+ transactions, at least 1 fraud)
2. Feature engineering: Assemble V1-V28 + Amount into vector
3. Normalization: StandardScaler (mean=0, std=1)
4. Train: Random Forest (100 trees, max depth 10)
5. Evaluate: AUC-ROC, Accuracy, Precision, Recall, F1
6. Save: Model + feature metadata

**SparkML Pipeline:**
- `VectorAssembler`: Combines 29 features into single vector
- `StandardScaler`: Normalizes features (critical for RF performance)
- `RandomForestClassifier`: 100 trees, depth 10, seed 42

**Output:**
- Model saved to `/app/models/fraud_detection_model` (PipelineModel)
- Metadata saved to `/app/models/feature_metadata.txt`

### Data Schema

**Kafka/MongoDB Base Schema:**
```json
{
  "Time": 0.0,
  "V1": -1.359807,
  "V2": -0.072781,
  ...
  "V28": -0.021053,
  "Amount": 149.62,
  "Class": 0.0,
  "processed_at": "2026-01-09T14:30:45.123Z"
}
```

**With ML Predictions:**
```json
{
  ...all fields above...,
  "fraud_prediction": 0,
  "fraud_probability": 0.02
}
```

### Monitoring Scripts

**`check-mongodb.py`**: Shows total transactions, fraud/normal distribution, latest 5 transactions, amount statistics

**`check_ml_predictions.py`**: Shows ML prediction statistics, confusion matrix, accuracy, precision/recall, top 5 suspicious transactions, risk distribution

## Important Patterns

### Modifying Spark Processors
- Always read the existing processor file before making changes
- Schema changes require updating all three files: both processors + training script
- When adding new features, update `feature_columns` in `train_model.py`
- Test without ML first (`spark-processor.py`) before adding ML features

### Working with Models
- Model must exist at `/app/models/fraud_detection_model` before running ML processor
- Model is a PipelineModel including VectorAssembler + StandardScaler + RandomForestModel
- If schema changes, retrain model - don't try to adapt old model
- Check model exists: `docker exec spark ls -la /app/models/`

### Kafka Configuration
- Producer connects to: `kafka:29092` (internal Docker network)
- External connections use: `localhost:9092`
- Topic: `fraud-detection-stream` (auto-created by producer)
- Processor uses `startingOffsets: earliest` to read from beginning on first run

### MongoDB Connection
- URI: `mongodb://admin:admin123@mongodb:27017/fraud_detection.transactions?authSource=admin`
- Database: `fraud_detection`
- Collection: `transactions`
- Spark uses `mongo-spark-connector_2.12:10.4.0`
- Python scripts use `pymongo`

### Environment Variables
Producer uses `.env` file:
```
KAGGLE_API_TOKEN=KGAT_xxxxx
KAFKA_BOOTSTRAP_SERVERS=kafka:29092
KAFKA_TOPIC=fraud-detection-stream
STATE_FILE=/app/state/producer_state.db
```

## Troubleshooting Common Issues

**"No data in MongoDB"**: Check producer is running (`docker ps`), check Kafka has data (`docker logs producer`), verify Spark is consuming (`docker logs spark`)

**"Could not load ML model"**: Train model first with `just train`, verify `/app/models/fraud_detection_model` exists in Spark container

**"Not enough data for training"**: Accumulate at least 100 transactions (preferably 1000+) with at least 1 fraud case before training

**Spark job fails to start**: Ensure all jars are specified in `--packages`, check MongoDB connection URI, verify Kafka is accessible from Spark container

**Producer restarts from beginning**: SQLite state file corrupted or missing - check `./state/producer_state.db` exists and is mounted correctly

## Testing

This project doesn't have unit tests. To verify functionality:

1. **Producer Test**: Check `docker logs producer` for "Sent: Time=X, Class=Y" messages
2. **Kafka Test**: Verify topic exists with producer logs showing successful sends
3. **Spark Test**: Run `just check` - should show increasing transaction counts
4. **ML Test**: Run `just check-ml` - should show >95% accuracy if model trained properly

## Dependencies

**Python Requirements** (`requirements.txt`):
- kafka-python: Kafka producer client
- pandas: DataFrame operations in producer
- kagglehub: Download dataset from Kaggle
- pyspark: Spark processing (installed in Docker image)
- pymongo: MongoDB client for monitoring scripts

**Spark Dependencies** (via `--packages`):
- `org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0`: Kafka integration
- `org.mongodb.spark:mongo-spark-connector_2.12:10.4.0`: MongoDB writes

**Spark Container ML Libraries** (installed via setup script):
- numpy, pandas, scikit-learn: Used by SparkML internally
- pymongo: For training script to read from MongoDB

## Files Organization

**Essential Files:**
- `README.md`: Project overview and quick start
- `INSTRUCTIONS.md`: Step-by-step presentation guide
- `COMMANDS.md`: Command reference
- `CLAUDE.md`: This file - comprehensive guide for Claude Code

**Source Code** (`src/` folder):
- `producer.py`: Kafka producer
- `spark-processor.py`: Basic Spark processor
- `spark-processor-ml.py`: ML-enabled processor
- `train_model.py`: Model training script
- `check-mongodb.py`: MongoDB monitoring
- `check_ml_predictions.py`: ML prediction monitoring

**Configuration** (root directory):
- `docker-compose.yml`: Service definitions
- `justfile`: Task runner commands
- `Makefile`: Alternative task runner
- `requirements.txt`: Python dependencies
- `.env`: Environment variables (not in git)

**Scripts** (`scripts/` folder):
- `setup-spark-dependencies.sh`: Install ML libs in Spark container
- `start-spark-processor.sh`: Start basic processor
- `start-spark-ml.sh`: Start ML processor
- `train-model.sh`: Train model
- PowerShell versions (`.ps1`) for Windows

**Documentation** (`docs/` folder):
- `INSTRUCTIONS.md`: Step-by-step presentation guide
- `COMMANDS.md`: Command reference
- `CLAUDE.md`: This file - developer guide
