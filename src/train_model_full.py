"""
Train "Production" Models Directly from CSV
Bypasses Kafka/MongoDB accumulation. 
Reads the creditcard.csv directly, trains 3 models, and saves them to 'fully_trained'.
"""

import os
import sys
# Try importing kagglehub, install if missing (for Spark container)
try:
    import kagglehub
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "kagglehub"])
    import kagglehub

from pyspark.sql import SparkSession
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.classification import RandomForestClassifier, GBTClassifier, LogisticRegression
from pyspark.ml import Pipeline
from pyspark.sql.functions import col

def main():
    print("\n" + "="*80)
    print("🚀 DIRECT TRAINING (CSV -> MODELS)")
    print("="*80)

    # 1. Get the Dataset (Direct Download)
    print("📥 checking/downloading dataset via KaggleHub...")
    try:
        path = kagglehub.dataset_download("mlg-ulb/creditcardfraud")
        csv_path = os.path.join(path, "creditcard.csv")
        print(f"✅ Dataset found at: {csv_path}")
    except Exception as e:
        print(f"❌ Error downloading dataset: {e}")
        return

    # 2. Initialize Spark
    spark = SparkSession.builder \
        .appName("FraudDetectionDirectTrain") \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("ERROR")

    # 3. Read CSV directly
    print("📊 Reading CSV into Spark DataFrame...")
    df = spark.read.option("header", "true") \
        .option("inferSchema", "true") \
        .csv(csv_path)

    total = df.count()
    print(f"✅ Loaded {total} records from CSV.")

    # 4. Prepare Features (V1-V28 + Amount)
    feature_cols = [f"V{i}" for i in range(1, 29)] + ["Amount"]
    
    # --- FIX WAS HERE: outputCol="features" ---
    assembler = VectorAssembler(inputCols=feature_cols, outputCol="features")

    # 5. Define Models
    rf = RandomForestClassifier(labelCol="Class", featuresCol="features", numTrees=50, maxDepth=10)
    gbt = GBTClassifier(labelCol="Class", featuresCol="features", maxIter=50)
    lr = LogisticRegression(labelCol="Class", featuresCol="features", maxIter=50, regParam=0.01)

    # 6. Train and Save
    output_base = "/app/models/fully_trained"
    
    # Random Forest
    print("\n🌲 Training Random Forest...")
    rf_pipeline = Pipeline(stages=[assembler, rf])
    rf_model = rf_pipeline.fit(df)
    rf_path = f"{output_base}/random_forest_model"
    rf_model.write().overwrite().save(rf_path)
    print(f"   ✅ Saved to: {rf_path}")

    # Gradient Boosting
    print("\n🚀 Training Gradient Boosting...")
    gbt_pipeline = Pipeline(stages=[assembler, gbt])
    gbt_model = gbt_pipeline.fit(df)
    gbt_path = f"{output_base}/gradient_boosting_model"
    gbt_model.write().overwrite().save(gbt_path)
    print(f"   ✅ Saved to: {gbt_path}")

    # Logistic Regression
    print("\n📈 Training Logistic Regression...")
    lr_pipeline = Pipeline(stages=[assembler, lr])
    lr_model = lr_pipeline.fit(df)
    lr_path = f"{output_base}/logistic_regression_model"
    lr_model.write().overwrite().save(lr_path)
    print(f"   ✅ Saved to: {lr_path}")

    print("\n" + "="*80)
    print("🎉 TRAINING COMPLETE!")
    print("   Models are ready in 'models/fully_trained/'")
    print("   Run 'just promote-full' to use them.")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()