#!/usr/bin/env python3
"""
High-Performance Data Accumulator
Reads from Kafka and dumps to MongoDB for training.
- Removes slow Console sinks
- Uses caching for single-pass processing
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, current_timestamp, sum as _sum, lit
from pyspark.sql.types import StructType, StructField, DoubleType, StringType
from pyspark.sql.functions import udf
import uuid

# Define schema for incoming Kafka messages
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

# Generate UUID for consistency with ML pipeline
generate_id_udf = udf(lambda: str(uuid.uuid4()), StringType()).asNondeterministic()

def write_to_mongo(batch_df, batch_id):
    """
    Process batch: Cache -> Write -> Stats -> Unpersist
    """
    if batch_df.rdd.isEmpty():
        return

    # 1. Cache the data (Compute once, use multiple times)
    # We add the UUID here so it's permanently part of the record
    cached_df = batch_df.withColumn("transaction_id", generate_id_udf()) \
                        .withColumn("processed_at", current_timestamp()) \
                        .cache()
    
    # Force materialization to get count and ensure caching happens
    count = cached_df.count()
    
    print(f"Batch {batch_id}: Writing {count} transactions...")

    # 2. Write to MongoDB (Fastest operation first)
    try:
        cached_df.write \
            .format("mongodb") \
            .mode("append") \
            .save()
    except Exception as e:
        print(f"Error writing to Mongo: {e}")

    # 3. Calculate Stats (In-memory, very fast)
    # We use a single aggregation pass instead of multiple .filter().count() calls
    stats = cached_df.select(
        _sum(col("Class")).cast("long").alias("fraud_count")
    ).collect()[0]
    
    fraud_count = stats["fraud_count"] if stats["fraud_count"] else 0
    normal_count = count - fraud_count

    print(f"Saved: {normal_count} Normal | {fraud_count} Fraud")

    # 4. Clear memory
    cached_df.unpersist()

def main():
    print("=" * 80)
    print("FAST DATA ACCUMULATOR")
    print("=" * 80)

    # Initialize Spark Session with tuning for speed
    spark = SparkSession.builder \
        .appName("FraudDetectionAccumulator") \
        .config("spark.sql.shuffle.partitions", "5") \
        .config("spark.mongodb.output.writeConcern.w", "0") \
        .config("spark.jars.packages", 
                "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,"
                "org.mongodb.spark:mongo-spark-connector_2.12:10.4.0") \
        .config("spark.mongodb.write.connection.uri", 
                "mongodb://admin:admin123@mongodb:27017/fraud_detection.accumulated_training_data?authSource=admin") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("ERROR")
    # Silence Kafka consumer logs
    import logging
    logging.getLogger("org.apache.kafka.clients.consumer").setLevel(logging.ERROR)

    # Read Stream from Kafka
    df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "kafka:29092") \
        .option("subscribe", "fraud-detection-stream") \
        .option("startingOffsets", "earliest") \
        .option("maxOffsetsPerTrigger", "10000") \
        .load()

    # Transform
    parsed_df = df.select(
        from_json(col("value").cast("string"), schema).alias("data")
    ).select("data.*")

    print("Connected to Kafka. Accumulating data...")
    print("Press Ctrl+C to stop (or use 'Enter' if running via 'just workflow')\n")

    # Write Stream
    query = parsed_df.writeStream \
        .foreachBatch(write_to_mongo) \
        .option("checkpointLocation", "/tmp/spark-checkpoint") \
        .start()

    query.awaitTermination()

if __name__ == "__main__":
    main()