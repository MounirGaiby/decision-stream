# Database Structure Documentation

## Overview

The fraud detection system uses **MongoDB** as the primary data store. All transactions flow from Kafka through Spark Streaming and are persisted in MongoDB for analysis, visualization, and model training.

## Database Configuration

- **Database Name**: `fraud_detection`
- **Collection Name**: `transactions`
- **Connection URI**: `mongodb://admin:admin123@localhost:27017/fraud_detection.transactions?authSource=admin`
- **Interface**: Mongo Express available at `http://localhost:8081`

## Collection Schema

### Collection: `transactions`

The `transactions` collection stores all processed credit card transactions with their features, labels, and ML predictions.

#### Base Schema (Without ML Predictions)

When running the basic processor (`spark-processor.py`), documents contain:

```json
{
  "_id": ObjectId("..."),
  "Time": 0.0,
  "V1": -1.359807,
  "V2": -0.072781,
  "V3": 2.536347,
  "V4": 1.378155,
  "V5": -0.338261,
  "V6": 0.462388,
  "V7": 0.239599,
  "V7": 0.098698,
  "V8": 0.363787,
  "V9": 0.090794,
  "V10": -0.551600,
  "V11": -0.617801,
  "V12": -0.991390,
  "V13": -0.311169,
  "V14": -2.177727,
  "V15": 0.468178,
  "V16": -0.470401,
  "V17": 0.207971,
  "V18": 0.025791,
  "V19": 0.403993,
  "V20": 0.251412,
  "V21": -0.018307,
  "V22": 0.277838,
  "V23": -0.110474,
  "V24": 0.066928,
  "V25": 0.128539,
  "V26": -0.189115,
  "V27": 0.133558,
  "V28": -0.021053,
  "Amount": 149.62,
  "Class": 0.0,
  "processed_at": ISODate("2026-01-09T14:30:45.123Z")
}
```

#### Extended Schema (With ML Predictions)

When running the ML processor (`spark-processor-ml.py`), documents additionally include:

```json
{
  ...all fields above...,
  "fraud_prediction": 0,
  "fraud_probability": 0.0234
}
```

## Column Descriptions

### Transaction Metadata

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `_id` | ObjectId | MongoDB unique document identifier | `ObjectId("65a1b2c3d4e5f6789abcdef0")` |
| `processed_at` | ISODate | Timestamp when Spark processed the transaction | `2026-01-09T14:30:45.123Z` |

### Temporal Features

| Column | Type | Description | Example | Notes |
|--------|------|-------------|---------|-------|
| `Time` | Double | Seconds elapsed between this transaction and the first transaction in the dataset | `0.0`, `172792.0` | Used to detect temporal patterns (e.g., fraud spikes at certain times) |

### Principal Component Analysis (PCA) Features

The dataset uses **PCA transformation** to anonymize sensitive credit card information. The original features (card number, merchant, location, etc.) have been transformed into 28 principal components (V1-V28).

| Column | Type | Description | Example | Notes |
|--------|------|-------------|---------|-------|
| `V1` | Double | First principal component | `-1.359807` | Represents the most significant variance in the original data |
| `V2` | Double | Second principal component | `-0.072781` | Second most significant variance |
| `V3` | Double | Third principal component | `2.536347` | Third most significant variance |
| `V4` through `V27` | Double | Components 4-27 | Various | Additional principal components |
| `V28` | Double | 28th principal component | `-0.021053` | Least significant variance component |

**Why PCA?**
- **Privacy**: Original features (card numbers, merchant names, locations) are sensitive
- **Anonymization**: PCA transforms data into uncorrelated components
- **Dimensionality**: Reduces complexity while preserving important patterns
- **ML Performance**: Helps models learn fraud patterns without exposing PII

**Important Note**: The V1-V28 values are **not directly interpretable** as they represent linear combinations of original features. However, they are highly effective for fraud detection.

### Transaction Amount

| Column | Type | Description | Example | Notes |
|--------|------|-------------|---------|-------|
| `Amount` | Double | Transaction amount in currency units | `149.62`, `0.00` | Critical feature - fraud often involves unusual amounts |

### Ground Truth Label

| Column | Type | Description | Example | Notes |
|--------|------|-------------|---------|-------|
| `Class` | Double | Actual fraud label (ground truth) | `0.0` (normal), `1.0` (fraud) | Used for model training and evaluation. **0 = Normal transaction**, **1 = Fraudulent transaction** |

### Machine Learning Predictions

These fields are added when using the ML processor (`spark-processor-ml.py`):

| Column | Type | Description | Example | Notes |
|--------|------|-------------|---------|-------|
| `fraud_prediction` | Integer | Model's binary prediction | `0` (normal), `1` (fraud) | Final classification from Random Forest model |
| `fraud_probability` | Double | Probability of fraud (0.0 to 1.0) | `0.0234` (2.34%), `0.9876` (98.76%) | Probability that transaction is fraudulent. Higher = more suspicious |

## Example Records

### Example 1: Normal Transaction (No ML)

```json
{
  "_id": ObjectId("65a1b2c3d4e5f6789abcdef1"),
  "Time": 0.0,
  "V1": -1.359807,
  "V2": -0.072781,
  "V3": 2.536347,
  "V4": 1.378155,
  "V5": -0.338261,
  "V6": 0.462388,
  "V7": 0.239599,
  "V8": 0.363787,
  "V9": 0.090794,
  "V10": -0.551600,
  "V11": -0.617801,
  "V12": -0.991390,
  "V13": -0.311169,
  "V14": -2.177727,
  "V15": 0.468178,
  "V16": -0.470401,
  "V17": 0.207971,
  "V18": 0.025791,
  "V19": 0.403993,
  "V20": 0.251412,
  "V21": -0.018307,
  "V22": 0.277838,
  "V23": -0.110474,
  "V24": 0.066928,
  "V25": 0.128539,
  "V26": -0.189115,
  "V27": 0.133558,
  "V28": -0.021053,
  "Amount": 149.62,
  "Class": 0.0,
  "processed_at": ISODate("2026-01-09T14:30:45.123Z")
}
```

### Example 2: Normal Transaction (With ML Predictions)

```json
{
  "_id": ObjectId("65a1b2c3d4e5f6789abcdef2"),
  "Time": 172792.0,
  "V1": 1.191857,
  "V2": 0.266151,
  "V3": 0.166480,
  "V4": 0.448154,
  "V5": 0.060018,
  "V6": -0.082361,
  "V7": -0.078803,
  "V8": 0.085102,
  "V9": -0.255425,
  "V10": -0.166974,
  "V11": 1.612727,
  "V12": 1.065235,
  "V13": 0.489095,
  "V14": -0.143772,
  "V15": 0.635558,
  "V16": 0.463917,
  "V17": -0.114805,
  "V18": -0.183361,
  "V19": -0.145783,
  "V20": -0.069083,
  "V21": -0.225775,
  "V22": -0.638672,
  "V23": 0.101288,
  "V24": -0.339846,
  "V25": 0.167170,
  "V26": 0.125895,
  "V27": -0.008983,
  "V28": 0.014724,
  "Amount": 2.69,
  "Class": 0.0,
  "processed_at": ISODate("2026-01-09T14:35:12.456Z"),
  "fraud_prediction": 0,
  "fraud_probability": 0.0123
}
```

### Example 3: Fraudulent Transaction (With ML Predictions)

```json
{
  "_id": ObjectId("65a1b2c3d4e5f6789abcdef3"),
  "Time": 406.0,
  "V1": -1.359807,
  "V2": -0.072781,
  "V3": 2.536347,
  "V4": 1.378155,
  "V5": -0.338261,
  "V6": 0.462388,
  "V7": 0.239599,
  "V8": 0.363787,
  "V9": 0.090794,
  "V10": -0.551600,
  "V11": -0.617801,
  "V12": -0.991390,
  "V13": -0.311169,
  "V14": -2.177727,
  "V15": 0.468178,
  "V16": -0.470401,
  "V17": 0.207971,
  "V18": 0.025791,
  "V19": 0.403993,
  "V20": 0.251412,
  "V21": -0.018307,
  "V22": 0.277838,
  "V23": -0.110474,
  "V24": 0.066928,
  "V25": 0.128539,
  "V26": -0.189115,
  "V27": 0.133558,
  "V28": -0.021053,
  "Amount": 0.00,
  "Class": 1.0,
  "processed_at": ISODate("2026-01-09T14:30:50.789Z"),
  "fraud_prediction": 1,
  "fraud_probability": 0.9876
}
```

## Data Distribution

### Expected Statistics

Based on the Kaggle Credit Card Fraud Detection dataset:

- **Total Transactions**: 284,807 (full dataset)
- **Normal Transactions**: ~284,315 (99.83%)
- **Fraudulent Transactions**: ~492 (0.17%)
- **Class Imbalance**: Highly imbalanced (fraud is rare)

### Amount Statistics

- **Average Amount**: ~$88.35
- **Maximum Amount**: ~$25,691.16
- **Minimum Amount**: $0.00
- **Fraud Amount Range**: Typically lower amounts, but varies

## Indexes

### Recommended Indexes

For optimal query performance, consider creating indexes:

```javascript
// Index on Class for fraud analysis
db.transactions.createIndex({ "Class": 1 })

// Index on fraud_prediction for ML analysis
db.transactions.createIndex({ "fraud_prediction": 1 })

// Index on fraud_probability for risk analysis
db.transactions.createIndex({ "fraud_probability": -1 })

// Index on processed_at for time-based queries
db.transactions.createIndex({ "processed_at": -1 })

// Compound index for fraud detection queries
db.transactions.createIndex({ "fraud_prediction": 1, "fraud_probability": -1 })

// Index on Amount for amount-based analysis
db.transactions.createIndex({ "Amount": 1 })
```

### Creating Indexes

Connect to MongoDB and run:

```bash
# Using MongoDB shell
docker exec -it mongodb mongosh -u admin -p admin123 --authenticationDatabase admin

# Then in MongoDB shell:
use fraud_detection
db.transactions.createIndex({ "Class": 1 })
db.transactions.createIndex({ "fraud_prediction": 1 })
db.transactions.createIndex({ "fraud_probability": -1 })
db.transactions.createIndex({ "processed_at": -1 })
db.transactions.createIndex({ "fraud_prediction": 1, "fraud_probability": -1 })
db.transactions.createIndex({ "Amount": 1 })
```

## Query Examples

### Count Total Transactions

```javascript
db.transactions.countDocuments({})
```

### Count Fraudulent Transactions

```javascript
db.transactions.countDocuments({ "Class": 1 })
```

### Find High-Risk Transactions (ML)

```javascript
db.transactions.find({
  "fraud_prediction": 1,
  "fraud_probability": { "$gt": 0.8 }
}).sort({ "fraud_probability": -1 }).limit(10)
```

### Find Transactions by Amount Range

```javascript
db.transactions.find({
  "Amount": { "$gte": 1000, "$lte": 5000 }
})
```

### Aggregate Fraud Rate by Hour

```javascript
db.transactions.aggregate([
  {
    "$group": {
      "_id": { "$floor": { "$divide": ["$Time", 3600] } },
      "total": { "$sum": 1 },
      "frauds": { "$sum": { "$cond": [{ "$eq": ["$Class", 1] }, 1, 0] } }
    }
  },
  {
    "$project": {
      "hour": "$_id",
      "fraud_rate": { "$divide": ["$frauds", "$total"] },
      "total": 1,
      "frauds": 1
    }
  },
  { "$sort": { "hour": 1 } }
])
```

## Data Flow

1. **Producer** (`producer.py`) → Reads from Kaggle CSV → Sends to Kafka
2. **Kafka** → Buffers transactions in topic `fraud-detection-stream`
3. **Spark Processor** → Reads from Kafka → Processes → Writes to MongoDB
4. **MongoDB** → Stores all transactions in `fraud_detection.transactions`
5. **Tableau** → Connects to MongoDB → Visualizes data

## Data Retention

By default, MongoDB stores all data indefinitely. For production systems, consider:

- **TTL Index**: Automatically delete old transactions
- **Archival Strategy**: Move old data to cold storage
- **Sampling**: Keep only a sample of normal transactions

Example TTL index (delete transactions older than 1 year):

```javascript
db.transactions.createIndex(
  { "processed_at": 1 },
  { "expireAfterSeconds": 31536000 }  // 1 year in seconds
)
```

## Backup and Recovery

### Export Data

```bash
# Export collection to JSON
docker exec mongodb mongoexport \
  -u admin -p admin123 \
  --authenticationDatabase admin \
  --db fraud_detection \
  --collection transactions \
  --out /data/backup/transactions.json
```

### Import Data

```bash
# Import from JSON
docker exec mongodb mongoimport \
  -u admin -p admin123 \
  --authenticationDatabase admin \
  --db fraud_detection \
  --collection transactions \
  --file /data/backup/transactions.json
```
