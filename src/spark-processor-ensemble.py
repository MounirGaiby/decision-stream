#!/usr/bin/env python3
"""
Ensemble Spark Streaming Processor with Multiple ML Models
Reads from Kafka, applies 3 ML models, creates ensemble predictions, and writes to MongoDB
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, current_timestamp, struct, lit, array, when
from pyspark.sql.types import StructType, StructField, DoubleType, StringType
from pyspark.ml import PipelineModel
from pyspark.ml.linalg import Vectors, VectorUDT
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

# UDF to generate transaction ID
def generate_transaction_id():
    return str(uuid.uuid4())

generate_id_udf = udf(generate_transaction_id, StringType())

# UDF to extract probability for class 1 (fraud)
def extract_fraud_probability(probability_vector):
    if probability_vector is not None and len(probability_vector) > 1:
        return float(probability_vector[1])
    return 0.0

extract_prob_udf = udf(extract_fraud_probability, DoubleType())

def process_batch(batch_df, batch_id, models, mongo_uri):
    """Process each micro-batch with ensemble predictions"""

    if batch_df.count() == 0:
        return

    print(f"\n{'='*80}")
    print(f"📦 Processing batch {batch_id} with {batch_df.count()} transactions...")
    print(f"{'='*80}\n")

    # Generate unique transaction IDs
    df_with_id = batch_df.withColumn("transaction_id", generate_id_udf())

    # Add processed timestamp
    df_processed = df_with_id.withColumn("processed_at", current_timestamp())

    # STEP 1: Save raw transactions to 'transactions' collection
    print("💾 Step 1: Saving raw transactions...")
    try:
        df_processed.write \
            .format("mongodb") \
            .mode("append") \
            .option("uri", f"{mongo_uri}&collection=transactions") \
            .save()
        print(f"   ✅ Saved {df_processed.count()} transactions to 'transactions' collection")
    except Exception as e:
        print(f"   ❌ Error saving transactions: {e}")

    # STEP 2: Apply all ML models and save predictions
    print("\n🤖 Step 2: Applying ML Models...")

    model_predictions = {}

    for model_name, model in models.items():
        print(f"   🔮 Applying {model_name.replace('_', ' ').title()}...")
        try:
            # Apply model
            predictions = model.transform(df_processed)

            # Extract fraud probability
            predictions_with_prob = predictions.withColumn(
                "fraud_probability",
                extract_prob_udf(col("probability"))
            )

            # Store predictions for this model
            model_predictions[model_name] = predictions_with_prob

            # Save to model_predictions collection
            predictions_to_save = predictions_with_prob.select(
                col("transaction_id"),
                lit(model_name).alias("model_name"),
                col("prediction").cast("int").alias("prediction"),
                col("fraud_probability"),
                current_timestamp().alias("predicted_at")
            )

            predictions_to_save.write \
                .format("mongodb") \
                .mode("append") \
                .option("uri", f"{mongo_uri}&collection=model_predictions") \
                .save()

            print(f"      ✅ Predictions saved to 'model_predictions' collection")

        except Exception as e:
            print(f"      ❌ Error with {model_name}: {e}")
            model_predictions[model_name] = None

    # STEP 3: Create ensemble predictions
    print("\n🎯 Step 3: Creating Ensemble Predictions...")

    # Get predictions from all models
    rf_pred = model_predictions.get("random_forest")
    gbt_pred = model_predictions.get("gradient_boosting")
    lr_pred = model_predictions.get("logistic_regression")

    if rf_pred and gbt_pred and lr_pred:
        # Join all predictions
        ensemble_df = rf_pred.select(
            "transaction_id", "Class",
            col("prediction").alias("rf_prediction"),
            col("fraud_probability").alias("rf_probability")
        )

        ensemble_df = ensemble_df.join(
            gbt_pred.select(
                "transaction_id",
                col("prediction").alias("gbt_prediction"),
                col("fraud_probability").alias("gbt_probability")
            ),
            "transaction_id"
        )

        ensemble_df = ensemble_df.join(
            lr_pred.select(
                "transaction_id",
                col("prediction").alias("lr_prediction"),
                col("fraud_probability").alias("lr_probability")
            ),
            "transaction_id"
        )

        # Calculate ensemble prediction (majority vote)
        ensemble_df = ensemble_df.withColumn(
            "ensemble_prediction",
            when(
                (col("rf_prediction") + col("gbt_prediction") + col("lr_prediction")) >= 2,
                1
            ).otherwise(0)
        )

        # Calculate ensemble probability (average)
        ensemble_df = ensemble_df.withColumn(
            "ensemble_probability",
            (col("rf_probability") + col("gbt_probability") + col("lr_probability")) / 3
        )

        # Calculate confidence score (how many models agree)
        ensemble_df = ensemble_df.withColumn(
            "models_agreed",
            (col("rf_prediction") + col("gbt_prediction") + col("lr_prediction")).cast("int")
        )

        # Flag high-confidence predictions
        ensemble_df = ensemble_df.withColumn(
            "flagged",
            when(
                (col("ensemble_probability") > 0.8) | (col("models_agreed") == 3),
                True
            ).otherwise(False)
        )

        ensemble_df = ensemble_df.withColumn("created_at", current_timestamp())

        # Save ensemble results
        ensemble_to_save = ensemble_df.select(
            "transaction_id",
            "ensemble_prediction",
            "ensemble_probability",
            "models_agreed",
            "flagged",
            "rf_prediction", "rf_probability",
            "gbt_prediction", "gbt_probability",
            "lr_prediction", "lr_probability",
            "created_at"
        )

        ensemble_to_save.write \
            .format("mongodb") \
            .mode("append") \
            .option("uri", f"{mongo_uri}&collection=ensemble_results") \
            .save()

        print(f"   ✅ Ensemble results saved to 'ensemble_results' collection")

        # STEP 4: Save flagged transactions
        flagged_df = ensemble_df.filter(col("flagged") == True)
        flagged_count = flagged_df.count()

        if flagged_count > 0:
            print(f"\n🚨 Step 4: Processing {flagged_count} Flagged Transactions...")

            flagged_to_save = flagged_df.select(
                "transaction_id",
                lit("High confidence fraud detection").alias("reason"),
                col("ensemble_probability").alias("confidence_score"),
                when(col("models_agreed") == 3, True).otherwise(False).alias("all_models_agreed"),
                current_timestamp().alias("created_at")
            )

            flagged_to_save.write \
                .format("mongodb") \
                .mode("append") \
                .option("uri", f"{mongo_uri}&collection=flagged_transactions") \
                .save()

            print(f"   ✅ Flagged transactions saved to 'flagged_transactions' collection")
            print(f"   🔴 HIGH ALERT: {flagged_count} transactions flagged for review!")

        # Print batch statistics
        print(f"\n{'='*80}")
        print("📊 Batch Statistics:")
        print(f"{'='*80}")

        actual_fraud = ensemble_df.filter(col("Class") == 1).count()
        actual_normal = ensemble_df.filter(col("Class") == 0).count()

        predicted_fraud = ensemble_df.filter(col("ensemble_prediction") == 1).count()
        predicted_normal = ensemble_df.filter(col("ensemble_prediction") == 0).count()

        print(f"\n   📊 Actual Labels:")
        print(f"      ✅ Normal: {actual_normal}")
        print(f"      🚨 Fraud: {actual_fraud}")

        print(f"\n   🤖 Ensemble Predictions:")
        print(f"      ✅ Predicted Normal: {predicted_normal}")
        print(f"      🚨 Predicted Fraud: {predicted_fraud}")

        print(f"\n   🎯 Consensus:")
        consensus_3 = ensemble_df.filter(col("models_agreed") == 3).count()
        consensus_2 = ensemble_df.filter(col("models_agreed") == 2).count()
        consensus_1 = ensemble_df.filter(col("models_agreed") == 1).count()
        consensus_0 = ensemble_df.filter(col("models_agreed") == 0).count()

        print(f"      All 3 models agree: {consensus_3}")
        print(f"      2 models agree: {consensus_2}")
        print(f"      1 model predicts fraud: {consensus_1}")
        print(f"      No models predict fraud: {consensus_0}")

        if flagged_count > 0:
            print(f"\n   🚩 Flagged for Review: {flagged_count}")

        # Calculate accuracy if we have actual labels
        if actual_fraud + actual_normal > 0:
            correct = ensemble_df.filter(col("Class") == col("ensemble_prediction")).count()
            accuracy = (correct / ensemble_df.count()) * 100
            print(f"\n   📈 Batch Accuracy: {accuracy:.2f}%")

        print(f"\n{'='*80}\n")

def main():
    print("\n" + "="*80)
    print("🚀 ENSEMBLE ML PROCESSOR - FRAUD DETECTION SYSTEM")
    print("="*80 + "\n")

    # Initialize Spark Session
    spark = SparkSession.builder \
        .appName("EnsembleFraudDetection") \
        .config("spark.jars.packages",
                "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0," +
                "org.mongodb.spark:mongo-spark-connector_2.12:10.4.0") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")

    # MongoDB URI
    mongo_uri = "mongodb://admin:admin123@mongodb:27017/fraud_detection?authSource=admin"

    # Load all trained models
    print("🔄 Loading trained models...")
    models = {}

    try:
        models["random_forest"] = PipelineModel.load("/app/models/random_forest_model")
        print("   ✅ Random Forest loaded")
    except Exception as e:
        print(f"   ❌ Could not load Random Forest: {e}")
        spark.stop()
        return

    try:
        models["gradient_boosting"] = PipelineModel.load("/app/models/gradient_boosting_model")
        print("   ✅ Gradient Boosting loaded")
    except Exception as e:
        print(f"   ❌ Could not load Gradient Boosting: {e}")
        spark.stop()
        return

    try:
        models["logistic_regression"] = PipelineModel.load("/app/models/logistic_regression_model")
        print("   ✅ Logistic Regression loaded")
    except Exception as e:
        print(f"   ❌ Could not load Logistic Regression: {e}")
        spark.stop()
        return

    print(f"\n✅ All 3 models loaded successfully!\n")

    # Read from Kafka
    print("📡 Connecting to Kafka stream...")
    kafka_df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "kafka:29092") \
        .option("subscribe", "fraud-detection-stream") \
        .option("startingOffsets", "earliest") \
        .load()

    # Parse JSON messages
    parsed_df = kafka_df.select(
        from_json(col("value").cast("string"), schema).alias("data")
    ).select("data.*")

    print("✅ Connected to Kafka stream")
    print("\n💡 Processing transactions with 3 ML models...")
    print("💡 Press Ctrl+C to stop\n")

    # Write stream with foreachBatch for complex logic
    query = parsed_df.writeStream \
        .foreachBatch(lambda batch_df, batch_id: process_batch(batch_df, batch_id, models, mongo_uri)) \
        .option("checkpointLocation", "/tmp/spark-checkpoint-ensemble") \
        .start()

    query.awaitTermination()

if __name__ == "__main__":
    main()
