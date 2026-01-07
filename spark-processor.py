from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType

# Initialize Spark Session with the Kafka package
spark = SparkSession.builder \
    .appName("FraudDetectionSystem") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
    .getOrCreate()

# Reduce logging to see our output clearly
spark.sparkContext.setLogLevel("WARN")

# Define the schema of the incoming JSON (matches your CSV columns)
schema = StructType([
    StructField("Time", DoubleType(), True),
    StructField("V1", DoubleType(), True),
    StructField("V2", DoubleType(), True),
    # ... In a real app, you list all V1-V28 columns. 
    # For this test, we just grab a few and the Class.
    StructField("Class", IntegerType(), True)
])

# 1. Read Stream from Kafka
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:29092") \
    .option("subscribe", "fraud-detection-stream") \
    .option("startingOffsets", "earliest") \
    .load()

# 2. Transform the Data (Parse JSON)
# Kafka sends data as bytes in a "value" column. We must cast to String -> Parse JSON.
parsed_df = df.select(from_json(col("value").cast("string"), schema).alias("data")).select("data.*")

# 3. Write Stream to Console (For Testing)
query = parsed_df.writeStream \
    .outputMode("append") \
    .format("console") \
    .start()

query.awaitTermination()