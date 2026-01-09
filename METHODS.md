# All Available Methods to Run This Project

This document shows all three ways to run the fraud detection system.

## 📊 Comparison Table

| Method | Ease of Use | Cross-Platform | Installation Required | Best For |
|--------|-------------|----------------|----------------------|----------|
| **Task Runners** (`just`/`make`) | ⭐⭐⭐⭐⭐ Easiest | ✅ Yes | `just`: Yes, `make`: No (macOS/Linux) | Everyone |
| **Shell Scripts** (`.sh`/`.ps1`) | ⭐⭐⭐ Moderate | ✅ Yes | No | Windows users, manual control |
| **Docker Commands** | ⭐⭐ Complex | ✅ Yes | No | Learning, debugging |

## Method 1: Task Runners (RECOMMENDED)

### Using `just` (Best Experience)

**Install once:**
```bash
brew install just          # macOS
cargo install just         # All platforms
```

**Daily usage:**
```bash
just --list                # Show all commands
just setup                 # First-time setup
just run-basic             # Run without ML
just check                 # Check data
just train                 # Train model
just run-ml                # Run with ML
just check-ml              # Check predictions
just health                # System health
```

### Using `make` (Pre-installed)

**Daily usage:**
```bash
make help                  # Show all commands
make setup                 # First-time setup
make run-basic             # Run without ML
make check                 # Check data
make train                 # Train model
make run-ml                # Run with ML
make check-ml              # Check predictions
make health                # System health
```

**Available on macOS/Linux by default!**

## Method 2: Shell/PowerShell Scripts

### macOS/Linux (Bash)

```bash
# Make executable (first time only)
chmod +x *.sh

# Usage
./setup-spark-dependencies.sh
./start-spark-processor.sh
./train-model.sh
./start-spark-ml.sh

# Monitoring
python check-mongodb.py
python check_ml_predictions.py
```

### Windows (PowerShell)

```powershell
.\setup-spark-dependencies.ps1
.\start-spark-processor.ps1
.\train-model.ps1
.\start-spark-ml.ps1

# Monitoring
python check-mongodb.py
python check_ml_predictions.py
```

## Method 3: Direct Docker Commands

### Infrastructure

```bash
# Start services
docker-compose up -d

# Check status
docker ps

# Stop services
docker-compose down

# View logs
docker logs producer --tail 50
docker logs spark --tail 50
docker logs kafka --tail 50
```

### Install Dependencies

```bash
docker exec -u root spark bash -c "apt-get update && \
    apt-get install -y python3-pip && \
    python3 -m pip install --upgrade pip && \
    pip3 install numpy pandas scikit-learn pymongo"
```

### Run Spark Jobs

**Basic processor (no ML):**
```bash
docker exec spark /opt/spark/bin/spark-submit \
    --master local[*] \
    --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.mongodb.spark:mongo-spark-connector_2.12:10.4.0 \
    --conf spark.mongodb.write.connection.uri="mongodb://admin:admin123@mongodb:27017/fraud_detection.transactions?authSource=admin" \
    /app/spark-processor.py
```

**Train model:**
```bash
docker exec spark /opt/spark/bin/spark-submit \
    --master local[*] \
    --packages org.mongodb.spark:mongo-spark-connector_2.12:10.4.0 \
    /app/train_model.py
```

**ML processor:**
```bash
docker exec spark /opt/spark/bin/spark-submit \
    --master local[*] \
    --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.mongodb.spark:mongo-spark-connector_2.12:10.4.0 \
    --conf spark.mongodb.write.connection.uri="mongodb://admin:admin123@mongodb:27017/fraud_detection.transactions?authSource=admin" \
    /app/spark-processor-ml.py
```

### Monitoring

```bash
# Python scripts
python check-mongodb.py
python check_ml_predictions.py

# Shell access
docker exec -it spark bash
docker exec -it mongodb mongosh -u admin -p admin123
```

## Which Method Should You Use?

### For Development & Daily Use
→ **Use task runners** (`just` or `make`)
- Simplest commands
- Built-in error checking
- Self-documenting
- Reproducible

### For CI/CD & Automation
→ **Use `make`**
- Universally available
- Standard in DevOps
- Works everywhere

### For Learning & Understanding
→ **Use direct Docker commands**
- See exactly what's happening
- Understand the system better
- Easier to debug

### For Windows-Only Teams
→ **Use PowerShell scripts**
- Native Windows experience
- Familiar syntax
- No extra installations

## Complete Workflow Examples

### With `just` (Recommended)
```bash
just setup          # Once
just run-basic      # 5-10 min
just train          # After Ctrl+C
just run-ml         # Run with ML
just health         # Verify
```

### With `make` (Alternative)
```bash
make setup          # Once
make run-basic      # 5-10 min
make train          # After Ctrl+C
make run-ml         # Run with ML
make health         # Verify
```

### With Scripts (macOS/Linux)
```bash
docker-compose up -d
./setup-spark-dependencies.sh
./start-spark-processor.sh    # 5-10 min
./train-model.sh              # After Ctrl+C
./start-spark-ml.sh           # Run with ML
python check_ml_predictions.py
```

### With Scripts (Windows)
```powershell
docker-compose up -d
.\setup-spark-dependencies.ps1
.\start-spark-processor.ps1    # 5-10 min
.\train-model.ps1              # After Ctrl+C
.\start-spark-ml.ps1           # Run with ML
python check_ml_predictions.py
```

## Summary

**Easiest**: `just setup && just run-basic && just train && just run-ml`

**Most Universal**: `make setup && make run-basic && make train && make run-ml`

**Most Explicit**: See "Method 3: Direct Docker Commands" above

**Most Windows-Native**: Use PowerShell scripts from "Method 2"

Choose the method that fits your workflow! They all do the same thing.
