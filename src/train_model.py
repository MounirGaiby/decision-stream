#!/usr/bin/env python3
"""
ML Model Training for Fraud Detection
Trains Random Forest, Gradient Boosting, and Logistic Regression (ensemble)
"""

from pyspark.sql import SparkSession
from pyspark.ml.feature import VectorAssembler, StandardScaler
from pyspark.ml.classification import RandomForestClassifier, GBTClassifier, LogisticRegression
from pyspark.ml import Pipeline
from pyspark.ml.evaluation import BinaryClassificationEvaluator, MulticlassClassificationEvaluator
from pyspark.sql.functions import col
import sys

def print_section(title):
    """Print formatted section header"""
    print("=" * 80)
    print(f"{title}")
    print("=" * 80)
    print()

def main():
    print_section("ML MODEL TRAINING - FRAUD DETECTION")

    # Initialize Spark
    # MongoDB connection - include collection in URI like train_model.py
    mongo_uri = "mongodb://admin:admin123@mongodb:27017/fraud_detection.transactions?authSource=admin"
    
    spark = SparkSession.builder \
        .appName("EnsembleModelTraining") \
        .config("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.12:10.4.0") \
        .config("spark.mongodb.read.connection.uri", mongo_uri) \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")

    # Step 1: Load data
    print("Step 1: Loading data from MongoDB...")
    df = spark.read \
        .format("mongodb") \
        .load()

    total_count = df.count()
    print(f"   Loaded {total_count} transactions from MongoDB")

    if total_count < 100:
        print(f"   ERROR: Not enough data! Need at least 100 transactions, got {total_count}")
        spark.stop()
        sys.exit(1)

    # Check fraud distribution
    fraud_count = df.filter(col("Class") == 1.0).count()
    normal_count = df.filter(col("Class") == 0.0).count()

    print()
    print("Dataset Statistics:")
    print(f"   Total transactions: {total_count}")
    print(f"   Normal transactions: {normal_count} ({normal_count/total_count*100:.2f}%)")
    print(f"   Fraudulent transactions: {fraud_count} ({fraud_count/total_count*100:.2f}%)")

    if fraud_count < 1:
        print(f"   ERROR: No fraud cases found! Cannot train models.")
        spark.stop()
        sys.exit(1)

    # Step 2: Feature engineering
    print()
    print("Step 2: Feature Engineering...")

    feature_columns = [f"V{i}" for i in range(1, 29)] + ["Amount"]
    print(f"   Using {len(feature_columns)} features")

    # Select only needed columns
    df_clean = df.select(["Time", "Class"] + feature_columns)

    # Step 3: Train/Test Split
    print()
    print("Step 3: Preparing Train/Test Split...")
    train_data, test_data = df_clean.randomSplit([0.8, 0.2], seed=42)

    train_count = train_data.count()
    test_count = test_data.count()
    train_fraud = train_data.filter(col("Class") == 1.0).count()
    test_fraud = test_data.filter(col("Class") == 1.0).count()

    print(f"   Training set: {train_count} transactions ({train_fraud} frauds)")
    print(f"   Test set: {test_count} transactions ({test_fraud} frauds)")

    # Create feature pipeline (common for all models)
    assembler = VectorAssembler(inputCols=feature_columns, outputCol="features_raw")
    scaler = StandardScaler(inputCol="features_raw", outputCol="features", withStd=True, withMean=False)

    # Step 4: Train Multiple Models
    print()
    print("Step 4: Training Multiple ML Models...")
    print()

    models_to_train = []

    # Model 1: Random Forest
    print("   Training Model 1: Random Forest...")
    rf = RandomForestClassifier(
        featuresCol="features",
        labelCol="Class",
        predictionCol="prediction",
        probabilityCol="probability",
        numTrees=100,
        maxDepth=10,
        seed=42
    )
    models_to_train.append(("random_forest", rf))
    print("   Random Forest configured")

    # Model 2: Gradient Boosting Trees
    print("   Training Model 2: Gradient Boosting Trees...")
    gbt = GBTClassifier(
        featuresCol="features",
        labelCol="Class",
        predictionCol="prediction",
        maxIter=50,
        maxDepth=5,
        seed=42
    )
    models_to_train.append(("gradient_boosting", gbt))
    print("   Gradient Boosting configured")

    # Model 3: Logistic Regression
    print("   Training Model 3: Logistic Regression...")
    lr = LogisticRegression(
        featuresCol="features",
        labelCol="Class",
        predictionCol="prediction",
        probabilityCol="probability",
        maxIter=100,
        regParam=0.01
    )
    models_to_train.append(("logistic_regression", lr))
    print("   Logistic Regression configured")

    # Train all models
    print()
    print("   Training all models... This may take 5-10 minutes...")
    print()

    trained_models = {}
    evaluator_auc = BinaryClassificationEvaluator(labelCol="Class", metricName="areaUnderROC")
    evaluator_acc = MulticlassClassificationEvaluator(labelCol="Class", predictionCol="prediction", metricName="accuracy")
    evaluator_precision = MulticlassClassificationEvaluator(labelCol="Class", predictionCol="prediction", metricName="weightedPrecision")
    evaluator_recall = MulticlassClassificationEvaluator(labelCol="Class", predictionCol="prediction", metricName="weightedRecall")
    evaluator_f1 = MulticlassClassificationEvaluator(labelCol="Class", predictionCol="prediction", metricName="f1")

    # Step 5: Train and evaluate each model
    print("=" * 80)
    print("MODEL PERFORMANCE METRICS")
    print("=" * 80)
    print()

    for model_name, classifier in models_to_train:
        print(f"Training {model_name.replace('_', ' ').title()}...")

        # Create pipeline
        pipeline = Pipeline(stages=[assembler, scaler, classifier])

        # Train
        model = pipeline.fit(train_data)
        trained_models[model_name] = model

        # Evaluate
        predictions = model.transform(test_data)

        auc = evaluator_auc.evaluate(predictions)
        accuracy = evaluator_acc.evaluate(predictions)
        precision = evaluator_precision.evaluate(predictions)
        recall = evaluator_recall.evaluate(predictions)
        f1 = evaluator_f1.evaluate(predictions)

        print(f"   {model_name.replace('_', ' ').title()} Performance:")
        print(f"      AUC-ROC:   {auc:.4f}")
        print(f"      Accuracy:  {accuracy:.4f}")
        print(f"      Precision: {precision:.4f}")
        print(f"      Recall:    {recall:.4f}")
        print(f"      F1-Score:  {f1:.4f}")
        print()

        # Save model
        model_path = f"/app/models/{model_name}_model"
        model.write().overwrite().save(model_path)
        print(f"   Model saved to: {model_path}")
        print()

    # Step 6: Save model metadata
    print("Step 6: Saving Model Metadata...")
    metadata_path = "/app/models/model_metadata.txt"
    with open(metadata_path, "w") as f:
        f.write("Fraud Detection ML Models\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Total training samples: {train_count}\n")
        f.write(f"Total test samples: {test_count}\n")
        f.write(f"Features used: {len(feature_columns)}\n\n")
        f.write("Models:\n")
        f.write("1. Random Forest (100 trees, depth 10)\n")
        f.write("2. Gradient Boosting (50 iterations, depth 5)\n")
        f.write("3. Logistic Regression (100 iterations)\n\n")
        f.write("Feature columns:\n")
        f.write(", ".join(feature_columns))

    print(f"   Metadata saved to: {metadata_path}")

    print()
    print("=" * 80)
    print("ML MODEL TRAINING COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    print()
    print("Next Steps:")
    print("   1. Stop current Spark processor if running (Ctrl+C)")
    print("   2. Start ML processor: just run-ml")
    print("   3. Check ML predictions: just check-ml")
    print()

    spark.stop()

if __name__ == "__main__":
    main()