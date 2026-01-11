#!/usr/bin/env python3
"""
Full ML Model Training for Fraud Detection
Trains models using the COMPLETE CSV dataset directly (bypassing accumulation).
"""

from pyspark.sql import SparkSession
from pyspark.ml.feature import VectorAssembler, StandardScaler
from pyspark.ml.classification import RandomForestClassifier, GBTClassifier, LogisticRegression
from pyspark.ml import Pipeline
from pyspark.ml.evaluation import BinaryClassificationEvaluator, MulticlassClassificationEvaluator
from pyspark.sql.functions import col
import sys
import os
import glob

def print_section(title):
    print("=" * 80)
    print(f"🤖 {title}")
    print("=" * 80)
    print()

def find_dataset():
    """Find creditcard.csv in /data/kagglehub"""
    search_path = "/data/kagglehub/**/creditcard.csv"
    files = glob.glob(search_path, recursive=True)
    if not files:
        return None
    return files[0]

def main():
    print_section("FULL ML MODEL TRAINING (DIRECT CSV)")

    # Initialize Spark
    spark = SparkSession.builder \
        .appName("FullModelTraining") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")

    # Step 1: Load data from CSV
    print("📊 Step 1: Loading data from CSV...")
    
    csv_path = find_dataset()
    if not csv_path:
        print("❌ ERROR: Could not find 'creditcard.csv' in /data/kagglehub")
        print("   Make sure the producer has run at least once to download the dataset.")
        spark.stop()
        sys.exit(1)

    print(f"   📂 Found dataset: {csv_path}")

    df = spark.read \
        .option("header", "true") \
        .option("inferSchema", "true") \
        .csv(csv_path)

    total_count = df.count()
    print(f"   ✅ Loaded {total_count} transactions from CSV")

    # Step 2: Feature engineering (Same as standard training)
    print()
    print("🔧 Step 2: Feature Engineering...")

    feature_columns = [f"V{i}" for i in range(1, 29)] + ["Amount"]
    
    # Ensure columns exist
    missing_cols = [c for c in feature_columns if c not in df.columns]
    if missing_cols:
        print(f"❌ ERROR: Missing columns: {missing_cols}")
        spark.stop()
        sys.exit(1)

    df_clean = df.select(["Time", "Class"] + feature_columns)

    # Step 3: Train/Test Split
    print()
    print("🎯 Step 3: Preparing Train/Test Split...")
    train_data, test_data = df_clean.randomSplit([0.8, 0.2], seed=42)

    # Create feature pipeline
    assembler = VectorAssembler(inputCols=feature_columns, outputCol="features_raw")
    scaler = StandardScaler(inputCol="features_raw", outputCol="features", withStd=True, withMean=False)

    # Step 4: Train Multiple Models
    print()
    print("🌲 Step 4: Training Multiple ML Models (FULL POWER)...")

    models_to_train = [
        ("random_forest_full", RandomForestClassifier(
            featuresCol="features", labelCol="Class", predictionCol="prediction", 
            probabilityCol="probability", numTrees=100, maxDepth=10, seed=42
        )),
        ("gradient_boosting_full", GBTClassifier(
            featuresCol="features", labelCol="Class", predictionCol="prediction", 
            maxIter=50, maxDepth=5, seed=42
        )),
        ("logistic_regression_full", LogisticRegression(
            featuresCol="features", labelCol="Class", predictionCol="prediction", 
            probabilityCol="probability", maxIter=100, regParam=0.01
        ))
    ]

    trained_models = {}
    evaluator_auc = BinaryClassificationEvaluator(labelCol="Class", metricName="areaUnderROC")

    for model_name, classifier in models_to_train:
        print(f"🔄 Training {model_name}...")

        pipeline = Pipeline(stages=[assembler, scaler, classifier])
        model = pipeline.fit(train_data)
        
        # Evaluate
        predictions = model.transform(test_data)
        auc = evaluator_auc.evaluate(predictions)
        print(f"   ✅ {model_name} AUC-ROC: {auc:.4f}")

        # Save model (staged as _full)
        model_path = f"/app/models/{model_name}"
        model.write().overwrite().save(model_path)
        print(f"   💾 Saved to: {model_path}")
        print()

    print("✅ Full training complete.")
    spark.stop()

if __name__ == "__main__":
    main()