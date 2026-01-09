# Quick Start Guide

Get the fraud detection system running in minutes!

## Prerequisites Check

```bash
# Check Docker is installed and running
docker --version
docker ps

# Check Python is installed
python --version

# Check if task runners are available
make --version          # Should be pre-installed on macOS
just --version          # Optional - install with: brew install just
```

## 1. One-Command Setup (Recommended)

```bash
# Using make (pre-installed on macOS)
make setup
```

This will:
- ✅ Start all Docker services (Kafka, MongoDB, Spark, etc.)
- ✅ Install Python ML dependencies in Spark
- ✅ Verify everything is working

## 2. Create Kaggle Config

Create a `.env` file with your Kaggle API token:

```bash
cp .env.example .env
# Edit .env and add your token: KAGGLE_API_TOKEN=KGAT_xxxxx
```

Get token from: https://www.kaggle.com/settings → API → Create New Token

## 3. Run the Complete Workflow

```bash
# Phase 1: Accumulate data (let run for 5-10 minutes)
make run-basic

# In another terminal, check progress
make check

# Phase 2: Train model (stop run-basic with Ctrl+C first)
make train

# Phase 3: Run with ML predictions
make run-ml

# Check ML performance
make check-ml

# View system health
make health
```

## Alternative: Install `just` for Better Experience

```bash
# Install just (optional but recommended)
brew install just

# Then use just instead of make
just setup
just run-basic
just train
just run-ml
just health
```

## Troubleshooting

**Docker not running?**
```bash
# Start Docker Desktop
# Wait for it to be ready, then try again
make status
```

**No data in MongoDB?**
```bash
# Check producer logs
docker logs producer --tail 50

# Check Spark logs
docker logs spark --tail 50

# Verify containers are running
make status
```

**Need to start fresh?**
```bash
# Clean everything and restart
make clean
make setup
```

## Web Interfaces

After starting services:

- **Mongo Express** (Database UI): http://localhost:8081
- **Dozzle** (Log Viewer): http://localhost:8080

```bash
# Quick open commands
make ui-mongo
make ui-logs
```

## Common Commands

```bash
make help           # Show all available commands
make status         # Show container status
make logs           # View all logs
make health         # Complete health check
make check          # Check MongoDB data
make check-ml       # Check ML predictions
make shell-spark    # Enter Spark container
make shell-mongo    # Enter MongoDB shell
make clean-model    # Remove trained model
make reset-producer # Restart data from beginning
```

## Next Steps

- 📖 Read [README.md](readme.md) for detailed documentation
- 🛠️ See [TASK_RUNNERS.md](TASK_RUNNERS.md) for complete task runner guide
- 📝 See [CLAUDE.md](CLAUDE.md) for architecture details
- 📜 See [SCRIPTS.md](SCRIPTS.md) for manual script usage

## Success Metrics

After completing the workflow, you should see:

- ✅ **5000+ transactions** in MongoDB
- ✅ **Model trained** with >95% accuracy
- ✅ **ML predictions** being added in real-time
- ✅ **AUC-ROC** > 0.98
- ✅ **All containers** running healthy

Run `make health` to verify!
