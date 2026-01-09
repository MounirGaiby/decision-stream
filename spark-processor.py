from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, current_timestamp
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType

# Initialize Spark Session with Kafka and MongoDB packages
spark = SparkSession.builder \
    .appName("FraudDetectionSystem") \
    .config("spark.jars.packages", 
            "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,"
            "org.mongodb.spark:mongo-spark-connector_2.12:10.4.0") \
    .config("spark.mongodb.write.connection.uri", 
            "mongodb://admin:admin123@mongodb:27017/fraud_detection.transactions?authSource=admin") \
    .getOrCreate()

# Reduce logging to see our output clearly
spark.sparkContext.setLogLevel("WARN")

# Define the COMPLETE schema matching the Credit Card Fraud dataset
# Dataset has 31 columns: Time, V1-V28, Amount, Class
schema = StructType([
    StructField("Time", DoubleType(), True),
    # Principal Components V1-V28 (résultat de PCA pour anonymiser les données)
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
    # Amount: Montant de la transaction
    StructField("Amount", DoubleType(), True),
    # Class: 0 = Normal, 1 = Fraud
    StructField("Class", DoubleType(), True)
])

print("=" * 80)
print("🚀 FRAUD DETECTION SYSTEM - SPARK STREAMING PROCESSOR")
print("=" * 80)
print("📊 Reading from Kafka topic: fraud-detection-stream")
print("💾 Writing to MongoDB: fraud_detection.transactions")
print("=" * 80)

# 1. Read Stream from Kafka
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:29092") \
    .option("subscribe", "fraud-detection-stream") \
    .option("startingOffsets", "earliest") \
    .load()

# 2. Transform the Data (Parse JSON)
# Kafka sends data as bytes in a "value" column. We must cast to String -> Parse JSON.
parsed_df = df.select(
    from_json(col("value").cast("string"), schema).alias("data")
).select("data.*")

# 3. Add processing timestamp
enriched_df = parsed_df.withColumn("processed_at", current_timestamp())

# 4. Write Stream to MongoDB
# Using foreachBatch for more control and reliability
def write_to_mongo(batch_df, batch_id):
    """
    Fonction appelée pour chaque micro-batch
    """
    if batch_df.count() > 0:
        print(f"📦 Processing batch {batch_id} with {batch_df.count()} transactions...")
        
        # Show some stats about the batch
        fraud_count = batch_df.filter(col("Class") == 1).count()
        normal_count = batch_df.filter(col("Class") == 0).count()
        
        print(f"   ✅ Normal transactions: {normal_count}")
        print(f"   🚨 Fraudulent transactions: {fraud_count}")
        
        # Write to MongoDB
        batch_df.write \
            .format("mongodb") \
            .mode("append") \
            .save()
        
        print(f"   💾 Batch {batch_id} saved to MongoDB successfully!")
    else:
        print(f"📦 Batch {batch_id} is empty, skipping...")

# Start the streaming query with MongoDB sink
query = enriched_df.writeStream \
    .foreachBatch(write_to_mongo) \
    .outputMode("append") \
    .option("checkpointLocation", "/tmp/spark-checkpoint") \
    .start()

print("\n✅ Streaming query started! Waiting for data...")
print("💡 Press Ctrl+C to stop\n")

# Also write to console for monitoring (optional - you can remove this in production)
console_query = enriched_df.writeStream \
    .outputMode("append") \
    .format("console") \
    .option("truncate", "false") \
    .option("numRows", "5") \
    .start()

# Wait for termination
query.awaitTermination()