# Real-Time Fraud Detection System

A complete Big Data pipeline for detecting credit card fraud using Kafka, Spark Streaming, MongoDB, and Machine Learning.

## Architecture

```
Kaggle Dataset → Producer → Kafka → Spark Streaming → MongoDB
                                            ↓
                                     Random Forest ML
                                            ↓
                                  Real-time Predictions
```

## Tech Stack

- **Streaming**: Apache Kafka
- **Processing**: Apache Spark (Streaming + ML)
- **Storage**: MongoDB
- **ML**: SparkML Random Forest
- **Monitoring**: Dozzle, Mongo Express
- **Orchestration**: Docker Compose

## Quick Start

### Prerequisites

- Docker Desktop (running)
- Python 3.9+
- Kaggle API token
- `just` task runner (recommended): `brew install just`

### 1. Setup Environment

Create `.env` file:
```env
KAGGLE_API_TOKEN=KGAT_your_token_here
KAFKA_BOOTSTRAP_SERVERS=kafka:29092
KAFKA_TOPIC=fraud-detection-stream
STATE_FILE=/app/state/producer_state.db
```

### 2. Start System

```bash
# Complete setup (starts all services + installs dependencies)
just setup

# Or manually
docker-compose up -d
just install-deps
```

### 3. Run the Pipeline

```bash
# Phase 1: Accumulate training data (5-10 min)
just run-basic

# Phase 2: Train ML model (press Ctrl+C first to stop processor)
just train

# Phase 3: Run with ML predictions
just run-ml
```

### 4. Monitor

```bash
# Check data statistics
just check

# Check ML predictions
just check-ml

# System health
just health
```

## Services

| Service | URL | Credentials |
|---------|-----|-------------|
| Kafka | localhost:9092 | - |
| MongoDB | localhost:27017 | admin/admin123 |
| Mongo Express | http://localhost:8081 | admin/admin123 |
| Dozzle Logs | http://localhost:8080 | - |

## Dataset

**Credit Card Fraud Detection** (Kaggle)
- 284,807 transactions
- 492 fraudulent (0.172%)
- 31 features (Time, V1-V28 PCA components, Amount, Class)

## ML Model Performance

- **Accuracy**: 99.9%+
- **AUC-ROC**: 0.9999
- **Precision**: 98.8%
- **Recall**: 95.5%+
- **Algorithm**: Random Forest (100 trees, depth 10)

## Documentation

- **[INSTRUCTIONS.md](INSTRUCTIONS.md)** - Step-by-step presentation guide
- **[COMMANDS.md](COMMANDS.md)** - Complete command reference
- **[CLAUDE.md](CLAUDE.md)** - Developer guide for Claude Code

## Project Structure

```
decision-stream/
├── producer.py                 # Kafka producer
├── spark-processor.py          # Basic processor (no ML)
├── spark-processor-ml.py       # ML-enabled processor
├── train_model.py              # Model training
├── check-mongodb.py            # Data monitoring
├── check_ml_predictions.py     # ML monitoring
├── docker-compose.yml          # Services orchestration
├── justfile                    # Task runner commands
└── requirements.txt            # Python dependencies
```

## Common Commands

```bash
# Setup & Infrastructure
just setup          # Complete first-time setup
just start          # Start all Docker services
just stop           # Stop all services
just status         # Check container status

# Data Processing & ML
just run-basic      # Run without ML (accumulate data)
just train          # Train ML model
just run-ml         # Run with ML predictions

# Monitoring
just check          # Check MongoDB data
just check-ml       # Check ML predictions
just health         # Full system health check
just logs           # View recent logs

# Utilities
just clean          # Clean all data
just clean-model    # Remove trained model
```

See [COMMANDS.md](COMMANDS.md) for complete reference.

## License

MIT

## Author

Mounir Gaiby - Big Data Decision Process Project
