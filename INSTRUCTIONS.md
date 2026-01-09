# Presentation Instructions

Step-by-step guide for running the Real-Time Fraud Detection System during class presentation.

## Pre-Presentation Setup (Do This Before Class)

### 1. Verify Prerequisites

```bash
# Check Docker is running
docker --version
docker ps

# Check Python
python3 --version

# Check just is installed
just --version

# If not installed: brew install just
```

### 2. Setup Kaggle Token

1. Login to https://kaggle.com
2. Go to Settings → API → Create New API Token
3. Copy your token (format: `KGAT_xxxxx...`)
4. Create `.env` file:

```bash
cat > .env << EOF
KAGGLE_API_TOKEN=KGAT_your_actual_token_here
KAFKA_BOOTSTRAP_SERVERS=kafka:29092
KAFKA_TOPIC=fraud-detection-stream
STATE_FILE=/app/state/producer_state.db
EOF
```

### 3. Initial System Setup

```bash
# Complete setup (takes 5-10 minutes)
just setup

# This will:
# - Start all 6 Docker containers
# - Install ML dependencies in Spark
# - Verify system health
```

### 4. Pre-train the Model (Saves Time in Presentation)

```bash
# Run basic processor to accumulate data
just run-basic

# Wait 5-10 minutes (or let it run overnight)
# Press Ctrl+C when you have 5000+ transactions

# Check you have enough data
just check
# Should show: "Total transactions: 5000+"

# Train the model (takes 5-10 minutes)
just train

# Verify model exists
just check-model
# Should show: "✅ Model exists"
```

### 5. Stop Everything Before Presentation

```bash
# Stop all containers
just stop

# This ensures clean start during presentation
```

---

## During Presentation

### Part 1: Introduction (2 minutes)

**Talking Points:**
- Real-time fraud detection system using Big Data technologies
- Processes credit card transactions in real-time
- Uses Machine Learning to detect fraudulent transactions
- Architecture: Kafka → Spark → MongoDB with ML predictions

**What to Show:**
```bash
# Show the architecture
cat README.md | grep -A 5 "Architecture"

# Show tech stack
ls -la *.py
ls docker-compose.yml justfile
```

### Part 2: System Startup (3 minutes)

**Step 1: Start Infrastructure**

```bash
# Start all services
just start

# Show containers starting
docker ps
# Point out: Kafka, MongoDB, Spark, Producer, Mongo Express, Dozzle
```

**Step 2: Verify Services**

```bash
# Check system health
just health

# Explain each service
```

### Part 3: Data Ingestion (3 minutes)

**Show Producer in Action:**

```bash
# Check producer logs
docker logs producer --tail 20

# Explain:
# - Reading from Kaggle dataset (284K transactions)
# - Streaming to Kafka topic
# - Rate: ~10 transactions/second
# - Shows: [23715/284807] Sent: Time=32879.0, Class=0.0
```

**Show Data in MongoDB:**

```bash
# Check data accumulation
just check

# Explain output:
# - Total transactions processed
# - Normal vs Fraud distribution (99.66% vs 0.34%)
# - Latest transactions
# - Amount statistics
```

### Part 4: Spark Processing (3 minutes)

**Start Basic Processor (Without ML):**

```bash
# Run basic processor
just run-basic

# Let it run for 30 seconds to show activity
# Then press Ctrl+C

# Explain:
# - Reading from Kafka
# - Processing batches
# - Writing to MongoDB
# - Shows batch statistics
```

**Show Real-time Updates:**

```bash
# While processor runs, check MongoDB in another terminal
just check

# Run this 2-3 times to show increasing transaction count
```

### Part 5: Machine Learning (5 minutes)

**Step 1: Explain Pre-trained Model**

```bash
# Show model exists
just check-model

# Explain:
# - Random Forest with 100 trees
# - Trained on accumulated data
# - Features: V1-V28 (PCA) + Amount
# - Already trained to save time
```

**Step 2: Run ML-Enabled Processor**

```bash
# Start ML processor
just run-ml

# Let it run for 1-2 minutes
# Show real-time processing with predictions
```

**Step 3: Show ML Predictions**

```bash
# In another terminal, check ML predictions
just check-ml

# Explain output:
# - Model accuracy: 99.98%
# - Confusion matrix (TP, FP, TN, FN)
# - Precision: 98.84%
# - Recall: 95.51%
# - Top 5 suspicious transactions
# - Risk distribution
```

### Part 6: Monitoring & Visualization (2 minutes)

**Show Web Interfaces:**

```bash
# Open Mongo Express
open http://localhost:8081
# Or manually open in browser

# Login: admin/admin123
# Navigate to: fraud_detection → transactions
# Show documents with predictions
```

**Show Logs:**

```bash
# Recent logs from all services
just logs

# Or individual service
docker logs spark --tail 30
```

### Part 7: Results Summary (2 minutes)

**Show Final Statistics:**

```bash
# Complete health check
just health

# Highlight:
# - Total transactions processed
# - ML predictions generated
# - Model performance metrics
# - System uptime
```

**Key Achievements:**
- ✅ 50,000+ transactions processed
- ✅ 99.98% ML accuracy
- ✅ Real-time fraud detection
- ✅ Scalable architecture
- ✅ Complete monitoring

---

## Post-Presentation Cleanup

```bash
# Stop all services
just stop

# (Optional) Clean all data
just clean
```

---

## Troubleshooting During Presentation

### If Services Don't Start

```bash
# Restart Docker Desktop
# Then run:
just start
```

### If No Data in MongoDB

```bash
# Check producer is running
docker logs producer --tail 20

# Restart producer if needed
docker restart producer
```

### If ML Processor Fails

```bash
# Verify model exists
just check-model

# If missing, train it (takes 5-10 min)
just train
```

### If Commands Don't Work

```bash
# Check just is installed
just --version

# Alternative: use docker directly
docker exec spark /opt/spark/bin/spark-submit ...
```

---

## Time Allocation (Total: ~20 minutes)

1. Introduction - 2 min
2. System Startup - 3 min
3. Data Ingestion - 3 min
4. Spark Processing - 3 min
5. Machine Learning - 5 min
6. Monitoring - 2 min
7. Results Summary - 2 min

**Buffer**: Keep 2-3 minutes for questions

---

## Key Talking Points

**Technical Highlights:**
- Real-time streaming with Kafka
- Distributed processing with Spark
- NoSQL storage with MongoDB
- Machine Learning with SparkML
- Containerized with Docker

**Business Value:**
- Detects fraud in real-time
- Prevents financial losses
- Scalable to millions of transactions
- High accuracy (99.98%)
- Low false positive rate

**Challenges Overcome:**
- Imbalanced dataset (0.17% fraud)
- Real-time processing requirements
- Model training on streaming data
- System integration and orchestration

---

## Q&A Preparation

**Common Questions:**

**Q: How fast can it process transactions?**
A: Currently ~10 transactions/second, but Kafka+Spark can scale to millions/second with more resources.

**Q: What if the model makes a mistake?**
A: We track False Positives (1 in 26,000) and False Negatives (4 in 26,000). System provides probability scores for manual review.

**Q: How often is the model retrained?**
A: Can be retrained periodically (daily/weekly) as new data accumulates. Takes 5-10 minutes.

**Q: Can it handle real-world scale?**
A: Yes - architecture is horizontally scalable. Add more Kafka partitions, Spark workers, and MongoDB replicas.

**Q: What about data privacy?**
A: Dataset uses PCA transformation (V1-V28) - original features are anonymized. Only metadata (time, amount) is identifiable.
