#!/usr/bin/env python3
"""
High-Performance Spark Streaming Processor (ML Inference)
Optimized for low latency:
- Reduces MongoDB writes
- Calculates all statistics in a single pass
- Optimizes shuffle partitions for micro-batches
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, current_timestamp, struct, lit, when, count, sum as _sum
from pyspark.sql.types import StructType, StructField, DoubleType, StringType, IntegerType
from pyspark.ml import PipelineModel
from pyspark.sql.functions import udf
import uuid

# Schema
schema = StructType([
    StructField("Time", DoubleType(), True),
    StructField("V1", DoubleType(), True),
    StructField("V2", DoubleType(), True),
    StructField("V3", DoubleType(), True),
    StructField("V4", DoubleType(), True),
    StructField("V5", DoubleType(), True),
    StructField("V6", DoubleType(), True),
    StructField("V7", DoubleType(), True),
    StructField("V8", DoubleType(), True),
    StructField("V9", DoubleType(), True),
    StructField("V10", DoubleType(), True),
    StructField("V11", DoubleType(), True),
    StructField("V12", DoubleType(), True),
    StructField("V13", DoubleType(), True),
    StructField("V14", DoubleType(), True),
    StructField("V15", DoubleType(), True),
    StructField("V16", DoubleType(), True),
    StructField("V17", DoubleType(), True),
    StructField("V18", DoubleType(), True),
    StructField("V19", DoubleType(), True),
    StructField("V20", DoubleType(), True),
    StructField("V21", DoubleType(), True),
    StructField("V22", DoubleType(), True),
    StructField("V23", DoubleType(), True),
    StructField("V24", DoubleType(), True),
    StructField("V25", DoubleType(), True),
    StructField("V26", DoubleType(), True),
    StructField("V27", DoubleType(), True),
    StructField("V28", DoubleType(), True),
    StructField("Amount", DoubleType(), True),
    StructField("Class", DoubleType(), True)
])

# Optimized UDFs
generate_id_udf = udf(lambda: str(uuid.uuid4()), StringType()).asNondeterministic()

def extract_fraud_prob(v):
    return float(v[1]) if v is not None and len(v) > 1 else 0.0

extract_prob_udf = udf(extract_fraud_prob, DoubleType())

def process_batch(batch_df, batch_id, models, mongo_uri):
    if batch_df.rdd.isEmpty():
        return

    # Cache immediately to prevent re-computation
    df_cached = batch_df.withColumn("transaction_id", generate_id_udf()) \
                        .withColumn("processed_at", current_timestamp()) \
                        .cache()
    
    cnt = df_cached.count()
    print(f"\nBatch {batch_id}: Processing {cnt} records...")

    # --- WRITE 1: Raw Data (Bulk Write) ---
    df_cached.write \
        .format("mongodb") \
        .mode("append") \
        .option("uri", mongo_uri) \
        .option("collection", "live_stream_events") \
        .save()

    # --- TRANSFORM: Apply all models in memory (No writes yet) ---
    preds = {}
    for name, model in models.items():
        # Short alias: random_forest -> random, gradient_boosting -> gradient, logistic_regression -> logistic
        alias = name.split('_')[0] 
        p = model.transform(df_cached)
        preds[name] = p.select(
            col("transaction_id"),
            col("prediction").cast(IntegerType()).alias(f"{alias}_pred"),
            extract_prob_udf(col("probability")).alias(f"{alias}_prob")
        )

    # --- JOIN: Combine everything into one DataFrame ---
    full_df = df_cached.alias("main") \
        .join(preds["random_forest"], "transaction_id") \
        .join(preds["gradient_boosting"], "transaction_id") \
        .join(preds["logistic_regression"], "transaction_id")

    # --- CALCULATE: Ensemble Logic (Vectorized) ---
    # FIXED: Updated column names to match the aliases generated above
    ensemble_df = full_df.withColumn(
        "models_agreed", 
        col("random_pred") + col("gradient_pred") + col("logistic_pred")
    ).withColumn(
        "ensemble_prediction",
        when(col("models_agreed") >= 2, 1).otherwise(0)
    ).withColumn(
        "ensemble_probability",
        (col("random_prob") + col("gradient_prob") + col("logistic_prob")) / 3
    ).withColumn(
        "flagged",
        (col("ensemble_probability") > 0.8) | (col("models_agreed") == 3)
    )

    # --- WRITE 2: Ensemble Results (Contains ALL model data) ---
    # FIXED: Updated source columns here as well
    cols_to_save = [
        "transaction_id", "ensemble_prediction", "ensemble_probability", 
        "models_agreed", "flagged", "Class", "processed_at",
        col("random_pred").alias("rf_prediction"), col("random_prob").alias("rf_probability"),
        col("gradient_pred").alias("gbt_prediction"), col("gradient_prob").alias("gbt_probability"),
        col("logistic_pred").alias("lr_prediction"), col("logistic_prob").alias("lr_probability")
    ]
    
    final_output = ensemble_df.select(cols_to_save)
    
    final_output.write \
        .format("mongodb") \
        .mode("append") \
        .option("uri", mongo_uri) \
        .option("collection", "fraud_predictions") \
        .save()

    # --- WRITE 3: Flagged (Only if needed) ---
    # --- STATS: Single Pass Aggregation ---
    stats = ensemble_df.select(
        _sum(when(col("Class") == 1, 1).otherwise(0)).alias("actual_fraud"),
        _sum(when(col("Class") == 0, 1).otherwise(0)).alias("actual_normal"),
        _sum(when(col("ensemble_prediction") == 1, 1).otherwise(0)).alias("pred_fraud"),
        _sum(when(col("ensemble_prediction") == 0, 1).otherwise(0)).alias("pred_normal"),
        _sum(when(col("models_agreed") == 3, 1).otherwise(0)).alias("agree_3"),
        _sum(when(col("models_agreed") == 0, 1).otherwise(0)).alias("agree_0"),
        _sum(when(col("flagged") == True, 1).otherwise(0)).alias("flagged_count"),
        _sum(when(col("Class") == col("ensemble_prediction"), 1).otherwise(0)).alias("correct_preds")
    ).collect()[0]

    # Handle Flagged Write efficiently
    flagged_count = stats["flagged_count"]
    if flagged_count > 0:
        print(f"   Writing {flagged_count} high-risk transactions...")
        final_output.filter(col("flagged") == True).select(
            "transaction_id", 
            lit("High Confidence Fraud").alias("reason"), 
            col("ensemble_probability").alias("confidence"),
            "processed_at"
        ).write \
        .format("mongodb") \
        .mode("append") \
        .option("uri", mongo_uri) \
        .option("collection", "high_risk_alerts") \
        .save()

    # Print Stats
    accuracy = (stats["correct_preds"] / cnt) * 100 if cnt > 0 else 0
    print(f"   Stats: Accuracy={accuracy:.1f}% | Fraud Found={stats['pred_fraud']} (Actual={stats['actual_fraud']}) | Flagged={flagged_count}")
    print(f"   Consensus: All Agree={stats['agree_3']} | None Agree={stats['agree_0']}")

    df_cached.unpersist()

import argparse

# ... imports ...

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-type", choices=["standard", "full"], default="standard", help="Model type to use: standard or full")
    args = parser.parse_args()

    print(f"Starting Optimized ML Processor (Mode: {args.model_type.upper()})...")
    
    # Tune Spark for Speed
    spark = SparkSession.builder \
        .appName(f"FraudDetectionFast_{args.model_type}") \
        .config("spark.sql.shuffle.partitions", "5") \
        .config("spark.mongodb.output.writeConcern.w", "0") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.mongodb.spark:mongo-spark-connector_2.12:10.4.0") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("ERROR")
    import logging
    logging.getLogger("org.apache.kafka.clients.consumer").setLevel(logging.ERROR)

    mongo_uri = "mongodb://admin:admin123@mongodb:27017/fraud_detection?authSource=admin"

    # Load Models
    models = {}
    
    # Define model paths based on type
    if args.model_type == "full":
        # Full models end in _full
        paths = {
            "random_forest": "/app/models/random_forest_full",
            "gradient_boosting": "/app/models/gradient_boosting_full",
            "logistic_regression": "/app/models/logistic_regression_full"
        }
    else:
        # Standard models end in _model
        paths = {
            "random_forest": "/app/models/random_forest_model",
            "gradient_boosting": "/app/models/gradient_boosting_model",
            "logistic_regression": "/app/models/logistic_regression_model"
        }

    try:
        models["random_forest"] = PipelineModel.load(paths["random_forest"])
        models["gradient_boosting"] = PipelineModel.load(paths["gradient_boosting"])
        models["logistic_regression"] = PipelineModel.load(paths["logistic_regression"])
        print(f"Models loaded successfully from: {[p for p in paths.values()]}")
    except Exception as e:
        print(f"Error loading models: {e}")
        return

    # Stream
    kafka_df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "kafka:29092") \
        .option("subscribe", "fraud-detection-stream") \
        .option("startingOffsets", "earliest") \
        .option("maxOffsetsPerTrigger", "2000") \
        .load()

    parsed_df = kafka_df.select(from_json(col("value").cast("string"), schema).alias("data")).select("data.*")

    query = parsed_df.writeStream \
        .foreachBatch(lambda df, id: process_batch(df, id, models, mongo_uri)) \
        .option("checkpointLocation", "/tmp/spark-checkpoint-fast") \
        .start()

    query.awaitTermination()

if __name__ == "__main__":
    main()
