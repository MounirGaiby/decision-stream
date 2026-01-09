from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, current_timestamp, udf, struct
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType
from pyspark.ml import PipelineModel
import os

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

# Chemins
MODEL_PATH = "/app/models/fraud_detection_model"
USE_ML_MODEL = os.path.exists(MODEL_PATH)

# Define the COMPLETE schema matching the Credit Card Fraud dataset
schema = StructType([
    StructField("Time", DoubleType(), True),
    # Principal Components V1-V28
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
    # Amount
    StructField("Amount", DoubleType(), True),
    # Class: 0 = Normal, 1 = Fraud
    StructField("Class", DoubleType(), True)
])

print("=" * 80)
print("🚀 FRAUD DETECTION SYSTEM - SPARK STREAMING PROCESSOR")
print("=" * 80)
print("📊 Reading from Kafka topic: fraud-detection-stream")
print("💾 Writing to MongoDB: fraud_detection.transactions")

# Charger le modèle ML si disponible
ml_model = None
if USE_ML_MODEL:
    try:
        print(f"🤖 Loading ML model from: {MODEL_PATH}")
        ml_model = PipelineModel.load(MODEL_PATH)
        print("✅ ML Model loaded successfully - Real-time predictions ENABLED")
    except Exception as e:
        print(f"⚠️  Could not load ML model: {e}")
        print("⚠️  Running WITHOUT predictions")
        USE_ML_MODEL = False
else:
    print("⚠️  No ML model found - Running WITHOUT predictions")
    print(f"💡 Train a model first: docker exec spark python /app/train_model.py")

print("=" * 80)

# 1. Read Stream from Kafka
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:29092") \
    .option("subscribe", "fraud-detection-stream") \
    .option("startingOffsets", "earliest") \
    .load()

# 2. Transform the Data (Parse JSON)
parsed_df = df.select(
    from_json(col("value").cast("string"), schema).alias("data")
).select("data.*")

# 3. Add processing timestamp
enriched_df = parsed_df.withColumn("processed_at", current_timestamp())

# 4. Add ML Predictions if model is loaded
if USE_ML_MODEL and ml_model is not None:
    print("🔮 ML Predictions will be added to each transaction")
    
    # Faire les prédictions
    predictions_df = ml_model.transform(enriched_df)
    
    # Extraire la probabilité de fraude (probabilité de la classe 1)
    # probability est un vecteur [prob_class_0, prob_class_1]
    # On extrait prob_class_1
    from pyspark.sql.functions import udf
    from pyspark.sql.types import DoubleType
    
    def extract_fraud_probability(probability_vector):
        """Extrait la probabilité de fraude (classe 1)"""
        if probability_vector is not None and len(probability_vector) > 1:
            return float(probability_vector[1])
        return 0.0
    
    extract_prob_udf = udf(extract_fraud_probability, DoubleType())
    
    # Ajouter les colonnes de prédiction
    final_df = predictions_df \
        .withColumn("fraud_prediction", col("prediction").cast(IntegerType())) \
        .withColumn("fraud_probability", extract_prob_udf(col("probability"))) \
        .drop("features_raw", "features", "rawPrediction", "probability", "prediction")
else:
    final_df = enriched_df

# 5. Write Stream to MongoDB
def write_to_mongo(batch_df, batch_id):
    """
    Fonction appelée pour chaque micro-batch
    """
    if batch_df.count() > 0:
        print(f"\n{'='*80}")
        print(f"📦 Processing batch {batch_id} with {batch_df.count()} transactions...")
        
        # Statistiques de base
        fraud_count_actual = batch_df.filter(col("Class") == 1).count()
        normal_count_actual = batch_df.filter(col("Class") == 0).count()
        
        print(f"   📊 Actual Labels:")
        print(f"      ✅ Normal: {normal_count_actual}")
        print(f"      🚨 Fraud: {fraud_count_actual}")
        
        # Si on a des prédictions ML
        if USE_ML_MODEL and "fraud_prediction" in batch_df.columns:
            predicted_fraud = batch_df.filter(col("fraud_prediction") == 1).count()
            predicted_normal = batch_df.filter(col("fraud_prediction") == 0).count()
            
            print(f"   🤖 ML Predictions:")
            print(f"      ✅ Predicted Normal: {predicted_normal}")
            print(f"      🚨 Predicted Fraud: {predicted_fraud}")
            
            # Calculer l'accuracy sur ce batch (si on a les vraies labels)
            if fraud_count_actual + normal_count_actual > 0:
                correct_predictions = batch_df.filter(
                    col("Class") == col("fraud_prediction")
                ).count()
                batch_accuracy = (correct_predictions / batch_df.count()) * 100
                print(f"   📈 Batch Accuracy: {batch_accuracy:.2f}%")
            
            # Afficher les transactions suspectes (haute probabilité de fraude)
            high_risk = batch_df.filter(col("fraud_probability") > 0.8).count()
            if high_risk > 0:
                print(f"   ⚠️  HIGH RISK: {high_risk} transactions with >80% fraud probability")
        
        # Write to MongoDB
        try:
            batch_df.write \
                .format("mongodb") \
                .mode("append") \
                .save()
            print(f"   ✅ Batch {batch_id} saved to MongoDB successfully!")
        except Exception as e:
            print(f"   ❌ Error saving batch {batch_id}: {e}")
        
        print(f"{'='*80}\n")
    else:
        print(f"📦 Batch {batch_id} is empty, skipping...")

# Start the streaming query with MongoDB sink
query = final_df.writeStream \
    .foreachBatch(write_to_mongo) \
    .outputMode("append") \
    .option("checkpointLocation", "/tmp/spark-checkpoint-ml") \
    .start()

print("\n✅ Streaming query started! Waiting for data...")
if USE_ML_MODEL:
    print("🤖 ML Model is active - Real-time fraud predictions enabled!")
else:
    print("⚠️  Running without ML predictions")
print("💡 Press Ctrl+C to stop\n")

# Wait for termination
query.awaitTermination()