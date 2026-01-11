# Real-time Fraud Detection System

**Big Data Decision Processing Project**

A complete banking fraud detection system using Machine Learning (Ensemble of 3 models) and Real-time Processing with Dagster orchestration.

---

## Architecture

```
Dataset (284K transactions)
        ↓
Producer → Kafka → Spark Streaming → MongoDB (4 collections)
                             ↓
                    SparkML Ensemble (3 models)
                    - Random Forest
                    - Gradient Boosting
                    - Logistic Regression
                             ↓
                    Majority Vote + Auto-flagging
```

### Technology Stack

| Component                  | Technology             | Usage                                                |
| -------------------------- | ---------------------- | ---------------------------------------------------- |
| **Orchestration**    | **Dagster**      | Workflow management and UI                           |
| **Streaming**        | **Apache Kafka** | Real-time transaction ingestion                      |
| **Processing**       | **Apache Spark** | Distributed stream processing (Structured Streaming) |
| **Machine Learning** | **Spark ML**     | Model training and inference (RandomForest, GBT, LR) |
| **Storage**          | **MongoDB**      | NoSQL storage for transactions and results           |
| **Containerization** | **Docker**       | Service isolation and deployment                     |
| **Languages**        | **Python 3.9+**  | Core logic and scripting                             |

---

## 📊 Data Structure

### 1. The Dataset

We use the [Kaggle Credit Card Fraud Detection Dataset](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud).

- **Rows:** 284,807 transactions
- **Columns:**
  - `Time`: Seconds elapsed between this transaction and the first transaction.
  - `V1` - `V28`: Principal components obtained with PCA (features are anonymized).
  - `Amount`: Transaction amount.
  - `Class`: Target variable (`1` = Fraud, `0` = Normal).

### 2. MongoDB Collections

The system organizes data into 4 distinct collections in the `fraud_detection` database:

| Collection Name                         | Description                                                                                                                            |
| :-------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------- |
| **`accumulated_training_data`** | Raw transactions collected specifically for**training** the models. Populated by the "Accumulator" job.                          |
| **`live_stream_events`**        | A log of all raw transactions processed during the**live inference** phase. Used for audit trails.                               |
| **`fraud_predictions`**         | The main output. Contains every transaction plus the predictions from all 3 models (RF, GBT, LR) and the final Ensemble vote.          |
| **`high_risk_alerts`**          | A filtered subset of `fraud_predictions` containing ONLY high-confidence fraud cases (Ensemble Probability > 80% or Unanimous Vote). |
