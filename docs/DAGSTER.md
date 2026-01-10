# Dagster Orchestration Guide

## Table of Contents
- [What is Dagster?](#what-is-dagster)
- [Why Use Dagster?](#why-use-dagster)
- [Quick Start](#quick-start)
- [Assets Overview](#assets-overview)
- [Jobs Overview](#jobs-overview)
- [Running Jobs](#running-jobs)
- [Monitoring & Logs](#monitoring--logs)
- [Troubleshooting](#troubleshooting)
- [Comparison: Scripts vs Dagster](#comparison-scripts-vs-dagster)

---

## What is Dagster?

Dagster is a modern data orchestration platform that helps you build, test, and monitor data pipelines. It provides:

- **Visual UI** for managing and monitoring pipelines
- **Asset-based approach** where each step is a materialized asset
- **Dependency management** - automatically runs steps in the correct order
- **Rich logging** with real-time progress tracking
- **Reusability** - run individual steps or complete workflows
- **Version control** - all pipeline logic is in code

---

## Why Use Dagster?

### Before Dagster (Manual Scripts):
- Had to run multiple commands manually: `just run-basic`, `just train`, `just run-ml`
- No visual feedback on pipeline progress
- Hard to debug failures (logs scattered across containers)
- Manual dependency tracking (forgot to accumulate data before training)
- No centralized monitoring

### With Dagster:
- **One-click workflows** - run entire pipeline from UI
- **Visual progress tracking** - see which assets are running/complete
- **Automatic dependencies** - can't train without data, can't predict without models
- **Centralized logging** - all logs in one place with timestamps
- **Selective execution** - run only what you need (e.g., just retrain models)

---

## Quick Start

### 1. Start Dagster UI

```bash
# Using just command
just dagster

# Or manually
./scripts/start-dagster.sh
```

This will start the Dagster web UI at: **http://localhost:3000**

### 2. Access the UI

Open your browser and navigate to `http://localhost:3000`

You'll see:
- **Assets tab**: View all 6 assets and their dependencies
- **Jobs tab**: List of 5 available jobs
- **Runs tab**: History of all job executions
- **Overview**: System status and recent activity

### 3. Run Your First Job

1. Click **"Jobs"** in the left sidebar
2. Select **"full_pipeline"**
3. Click **"Launchpad"** in the top right
4. Click **"Launch Run"**

The complete pipeline will execute: accumulate → train → predict → validate → export

---

## Assets Overview

Assets are the building blocks of your pipeline. Each asset represents a materialized output.

### Asset Dependency Graph

```
check_services_asset
        ↓
accumulate_data_asset
        ↓
train_models_asset
        ↓
run_ml_predictions_asset
        ↓
validate_data_asset
        ↓
export_to_excel_asset
```

### 1. **check_services_asset**

**Purpose**: Verify all Docker services are running before starting pipeline

**Checks**:
- Kafka (message broker)
- MongoDB (database)
- Spark (processing engine)
- Mongo Express (DB UI)
- Dozzle (log viewer)

**Output**: Dictionary with status of each service

**Why it matters**: Prevents pipeline failures due to missing services

---

### 2. **accumulate_data_asset**

**Purpose**: Collect training data from Kafka stream

**Process**:
1. Starts producer (generates fraud transactions)
2. Launches Spark processor (consumes from Kafka → writes to MongoDB)
3. Monitors for 2 minutes (120 seconds)
4. Logs progress every 10 seconds
5. Stops gracefully

**Output**:
- Count of accumulated transactions
- Fraud vs normal transaction breakdown
- Time taken

**MongoDB Collection**: `fraud_detection.transactions`

**Why it matters**: ML models need diverse training data (fraud + normal transactions)

---

### 3. **train_models_asset**

**Purpose**: Train all 3 ML models using accumulated data

**Models Trained**:
1. **Random Forest** (100 trees, max depth 10)
2. **Gradient Boosting** (50 iterations, max depth 5)
3. **Logistic Regression** (100 iterations)

**Process**:
1. Checks sufficient data (>100 transactions, must have fraud cases)
2. Extracts features from MongoDB
3. Trains all 3 models in parallel
4. Saves models to `/app/models/` (inside Spark container)
5. Generates performance metrics

**Output**:
- Training time for each model
- Accuracy, precision, recall for each model
- Model file locations

**MongoDB Source**: `fraud_detection.transactions`

**Why it matters**: Ensemble approach - multiple models = better fraud detection

---

### 4. **run_ml_predictions_asset**

**Purpose**: Apply trained models to live streaming data

**Process**:
1. Checks all 3 models exist
2. Starts Spark ML processor (loads models)
3. Consumes transactions from Kafka
4. Applies all 3 models to each transaction
5. Creates ensemble decision (majority vote)
6. Runs for 2 minutes
7. Logs prediction stats every 10 seconds

**Output**:
- Count of predictions made
- Model agreement statistics
- Flagged transaction count
- Time taken

**MongoDB Collections Written**:
- `fraud_detection.transactions` - raw transaction data
- `fraud_detection.model_predictions` - individual model predictions
- `fraud_detection.ensemble_results` - final ensemble decisions
- `fraud_detection.flagged_transactions` - high-risk cases (auto-flagged)

**Ensemble Logic**:
- **Majority vote**: If 2+ models say fraud → fraud
- **Confidence score**: Average probability from all 3 models
- **Auto-flag**: Transaction flagged if confidence >80% OR all models agree

**Why it matters**: Real-time fraud detection using ensemble approach

---

### 5. **validate_data_asset**

**Purpose**: Check data quality and ML model accuracy

**Validations**:
1. **Data Volume Check**: Ensures sufficient data collected
2. **Fraud Distribution**: Verifies both fraud and normal cases exist
3. **Model Accuracy**: Checks prediction quality (>80% accuracy expected)
4. **Ensemble Agreement**: Measures how often models agree
5. **Flag Quality**: Validates flagging is working correctly

**Output**:
- Data quality metrics
- Model performance summary
- Validation pass/fail status
- Recommendations if issues found

**MongoDB Collections Analyzed**:
- All 4 collections (transactions, model_predictions, ensemble_results, flagged_transactions)

**Why it matters**: Ensures pipeline produces reliable, accurate fraud predictions

---

### 6. **export_to_excel_asset**

**Purpose**: Export all MongoDB data to Excel files for Tableau analysis

**Files Created** (in `exports/` folder):
1. `transactions.xlsx` - All transaction data
2. `model_predictions.xlsx` - Individual model predictions
3. `ensemble_results.xlsx` - Final ensemble decisions
4. `flagged_transactions.xlsx` - High-risk flagged cases

**Process**:
1. Connects to MongoDB
2. Queries each collection
3. Converts to pandas DataFrames
4. Exports to Excel with proper formatting
5. Adds metadata (export timestamp, row counts)

**Output**:
- File paths for all exports
- Row counts for each file
- Export timestamp

**Why it matters**: Enables business intelligence analysis and presentation charts in Tableau

---

## Jobs Overview

Jobs combine one or more assets into executable workflows.

### 1. **full_pipeline** (Complete Workflow)

**Description**: End-to-end fraud detection pipeline

**Assets Executed** (in order):
1. check_services_asset
2. accumulate_data_asset
3. train_models_asset
4. run_ml_predictions_asset
5. validate_data_asset
6. export_to_excel_asset

**Duration**: ~15-20 minutes

**Use Case**: First-time setup, complete system demo, full retraining

**Command Line**:
```bash
just dagster-full
```

---

### 2. **accumulate_data** (Data Collection Only)

**Description**: Collect training data from Kafka stream

**Assets Executed**:
1. check_services_asset
2. accumulate_data_asset

**Duration**: ~2-3 minutes

**Use Case**: Need more training data, testing data collection

**Command Line**:
```bash
just dagster-accumulate
```

---

### 3. **train_models** (Model Training Only)

**Description**: Train all 3 ML models using existing MongoDB data

**Assets Executed**:
1. check_services_asset
2. train_models_asset

**Duration**: ~10-15 minutes (depends on data volume)

**Use Case**: Retrain models with new data, model performance improvement

**Command Line**:
```bash
just dagster-train
```

**Prerequisites**: Must have accumulated data in MongoDB (run `accumulate_data` first)

---

### 4. **run_ml_predictions** (Predictions Only)

**Description**: Apply trained models to live streaming data

**Assets Executed**:
1. check_services_asset
2. run_ml_predictions_asset

**Duration**: ~2-3 minutes

**Use Case**: Generate predictions for analysis, test model performance

**Command Line**:
```bash
just dagster-predict
```

**Prerequisites**:
- Must have trained models (run `train_models` first)
- Docker services must be running

---

### 5. **validate_data** (Validation Only)

**Description**: Check data quality and model accuracy

**Assets Executed**:
1. validate_data_asset

**Duration**: ~30 seconds

**Use Case**: Quick health check, verify system is working correctly

**Command Line**:
```bash
just dagster-job validate_data
```

**Prerequisites**: Must have prediction data in MongoDB

---

## Running Jobs

### From Dagster UI (Recommended)

1. **Navigate to Jobs**
   - Click "Jobs" in left sidebar
   - See list of all 5 jobs

2. **Select a Job**
   - Click on job name (e.g., "full_pipeline")
   - See job description and asset graph

3. **Launch the Job**
   - Click "Launchpad" button (top right)
   - Review configuration (usually no changes needed)
   - Click "Launch Run"

4. **Monitor Progress**
   - Automatic redirect to run details page
   - See real-time logs for each asset
   - Watch progress bar for each step
   - View metadata and outputs as they're generated

5. **View Results**
   - Once complete, see all asset outputs
   - Click on any asset to see detailed logs
   - Check "Metadata" tab for statistics
   - Download logs if needed

### From Command Line

```bash
# Full pipeline
just dagster-full

# Individual jobs
just dagster-accumulate
just dagster-train
just dagster-predict

# Or use generic command
just dagster-job <job_name>
```

### From Python Code

```python
from dagster import execute_job
from dagster_fraud_detection import defs

# Execute a job
result = execute_job(defs.get_job_def("full_pipeline"))

# Check result
if result.success:
    print("Job completed successfully!")
```

---

## Monitoring & Logs

### Real-Time Monitoring

**In Dagster UI**:
- **Runs tab**: See all job executions (running, completed, failed)
- **Run details page**: Live logs for current run
- **Asset materialization**: See when each asset was last updated
- **Progress indicators**: Visual feedback on completion percentage

**Key Metrics to Watch**:
- **Transaction Count**: Should increase during accumulation
- **Model Accuracy**: Should be >80% after training
- **Prediction Rate**: Transactions per second during ML processing
- **Ensemble Agreement**: How often models agree (ideally >80%)

### Log Levels

Dagster captures all output from your assets:
- **INFO**: Normal progress updates (green)
- **WARNING**: Non-critical issues (yellow)
- **ERROR**: Failures that need attention (red)

**Example Log Output**:
```
[INFO] Starting data accumulation...
[INFO] [10s] Accumulated 87 transactions (12 fraud, 75 normal)
[INFO] [20s] Accumulated 183 transactions (25 fraud, 158 normal)
[INFO] ✅ Accumulation complete: 1,247 transactions
```

### Metadata Tracking

Each asset generates metadata visible in the UI:
- **accumulate_data**: Transaction counts, fraud rate, duration
- **train_models**: Model accuracy, precision, recall, training time
- **run_ml_predictions**: Prediction count, flagged count, agreement rate
- **validate_data**: Quality score, validation status, issues found

### Historical Analysis

**Runs Tab**:
- Filter by job, status, date range
- Compare run durations over time
- Identify performance trends
- Debug recurring failures

---

## Troubleshooting

### Common Issues

#### 1. "Docker services not running"

**Error**: `check_services_asset` fails with service status "not found"

**Solution**:
```bash
# Start Docker services
just start

# Verify services are running
just status

# Then retry Dagster job
```

#### 2. "Not enough training data"

**Error**: `train_models_asset` fails with "Insufficient data for training"

**Cause**: Need at least 100 transactions with some fraud cases

**Solution**:
```bash
# Run accumulation first
just dagster-accumulate

# Check data count
just check

# If still not enough, run accumulation again
```

#### 3. "Models not found"

**Error**: `run_ml_predictions_asset` fails with "Model files not found"

**Cause**: Models haven't been trained yet

**Solution**:
```bash
# Train models first
just dagster-train

# Or run full pipeline
just dagster-full
```

#### 4. "Port 3000 already in use"

**Error**: `dagster-webserver` fails to start

**Cause**: Another Dagster instance or application using port 3000

**Solution**:
```bash
# Find process using port 3000
lsof -i :3000

# Kill the process
kill -9 <PID>

# Or use a different port
dagster-webserver -h 0.0.0.0 -p 3001 -w workspace.yaml
```

#### 5. "Spark executor memory error"

**Error**: Spark job fails with "Not enough memory"

**Cause**: Processing large dataset with limited memory

**Solution**:
```bash
# Increase Spark memory in docker-compose.yml
# Change: SPARK_WORKER_MEMORY=2g
# To:     SPARK_WORKER_MEMORY=4g

# Restart services
just restart
```

#### 6. "Connection refused to MongoDB"

**Error**: Assets fail with "Can't connect to MongoDB"

**Cause**: MongoDB container not ready or credentials wrong

**Solution**:
```bash
# Check MongoDB is running
docker ps | grep mongodb

# Check logs
docker logs mongodb

# Test connection
just shell-mongo

# If all else fails, restart
just restart
```

### Debugging Tips

**View Detailed Logs**:
- Click on failed asset in Dagster UI
- Select "Logs" tab
- Look for last ERROR message
- Check full stack trace

**Run Jobs from Terminal**:
- More verbose output than UI
- Easier to copy-paste errors
```bash
just dagster-job <job_name>
```

**Check Docker Logs**:
```bash
# All services
just logs

# Specific service
just log spark
just log mongodb
```

**Validate MongoDB Data**:
```bash
# Check collections
just check

# Check ML predictions
just check-ml

# Access MongoDB shell
just shell-mongo
```

**Clean State and Retry**:
```bash
# Clear checkpoints (fixes stuck streams)
just clean-checkpoint

# Remove models (force retrain)
just clean-model

# Complete reset
just clean
just setup
```

---

## Comparison: Scripts vs Dagster

### Old Workflow (Manual Scripts)

```bash
# Step 1: Start services
just start

# Step 2: Wait for services to be ready...

# Step 3: Accumulate data
just run-basic
# Wait 5-10 minutes... Ctrl+C to stop

# Step 4: Check data
just check

# Step 5: Train models
just train
# Wait 10-15 minutes...

# Step 6: Run ML predictions
just run-ml
# Wait a few minutes... Ctrl+C to stop

# Step 7: Check predictions
just check-ml

# Step 8: Export to Excel
just export-excel
```

**Problems**:
- ❌ 8 manual steps
- ❌ Manual timing (when to stop accumulation?)
- ❌ No automatic dependency checking
- ❌ Easy to forget a step
- ❌ Logs scattered across terminals
- ❌ Hard to reproduce exact workflow
- ❌ No visual feedback
- ❌ Can't see intermediate results until complete

### New Workflow (Dagster)

```bash
# Step 1: Start Dagster UI
just dagster

# Step 2: Click "full_pipeline" → Launch Run

# Done!
# - All steps run automatically
# - Real-time progress tracking
# - Can't skip required steps
# - Logs all in one place
# - See results as they're generated
```

**Advantages**:
- ✅ 2 manual steps total
- ✅ Automatic timing (assets know when to stop)
- ✅ Dependency enforcement (can't train without data)
- ✅ Reproducible (same workflow every time)
- ✅ Centralized logging
- ✅ Visual progress tracking
- ✅ Selective execution (run only what you need)
- ✅ Metadata tracking (performance metrics)
- ✅ Error recovery (restart from failed step)

---

## For Presentations

### Quick Demo Flow (5 minutes)

1. **Show Dagster UI**
   - Navigate to http://localhost:3000
   - Click "Assets" - show dependency graph
   - Explain asset-based approach

2. **Launch Full Pipeline**
   - Go to "Jobs" → "full_pipeline"
   - Click "Launchpad" → "Launch Run"
   - Show real-time logs

3. **Monitor Progress**
   - Watch assets turn green as they complete
   - Click on running asset to see live logs
   - Show metadata (transaction counts, accuracy)

4. **View Results**
   - Once complete, show final outputs
   - Navigate to "validate_data" asset
   - Show quality metrics and model performance

5. **Open Exported Data**
   - Show Excel files in `exports/` folder
   - Explain they're ready for Tableau analysis

### Talking Points

**Why Dagster?**
- "Traditional batch processing uses scripts - hard to monitor, easy to make mistakes"
- "Dagster treats data as assets - you materialize outputs, not just run code"
- "Built-in dependency management - can't train a model without data"
- "Enterprise-grade observability - see exactly what's happening at every step"

**Technical Highlights**:
- "6 assets representing our pipeline stages"
- "5 jobs for different use cases - full pipeline or individual steps"
- "Automatic resource management - Docker containers controlled by Dagster"
- "Rich metadata - every asset tracks performance metrics"

**Business Value**:
- "Faster iterations - launch complete workflow with one click"
- "Reliable - same workflow every time, no human error"
- "Transparent - stakeholders can see pipeline progress in real-time"
- "Maintainable - all pipeline logic version controlled"

---

## Additional Resources

### Dagster Documentation
- Official Docs: https://docs.dagster.io/
- Asset Tutorial: https://docs.dagster.io/concepts/assets
- Best Practices: https://docs.dagster.io/guides/best-practices

### Project Files
- Asset definitions: `dagster_fraud_detection/assets/__init__.py`
- Job definitions: `dagster_fraud_detection/jobs.py`
- Resources: `dagster_fraud_detection/resources.py`
- Configuration: `workspace.yaml`, `dagster.yaml`

### Command Reference
See [COMMANDS.md](COMMANDS.md) for complete list of available commands.

### Troubleshooting
See [CLAUDE.md](CLAUDE.md) for development notes and common issues.

---

**Last Updated**: January 10, 2026
**Version**: 1.0
**Author**: Fraud Detection System Team
