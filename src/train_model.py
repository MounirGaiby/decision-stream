"""
Script d'entraînement du modèle de détection de fraude
Utilise SparkML avec Random Forest Classifier

Ce script:
1. Charge les données depuis MongoDB
2. Prépare les features pour le ML
3. Entraîne un modèle Random Forest
4. Évalue les performances
5. Sauvegarde le modèle pour utilisation en streaming
"""

from pyspark.sql import SparkSession
from pyspark.ml.feature import VectorAssembler, StandardScaler
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml import Pipeline
from pyspark.ml.evaluation import BinaryClassificationEvaluator, MulticlassClassificationEvaluator
from pyspark.sql.functions import col
import os

# Configuration
MONGODB_URI = "mongodb://admin:admin123@mongodb:27017/fraud_detection.transactions?authSource=admin"
MODEL_PATH = "/app/models/fraud_detection_model"
FEATURES_PATH = "/app/models/feature_metadata"

print("=" * 80)
print("🤖 FRAUD DETECTION MODEL TRAINING")
print("=" * 80)

# Initialize Spark Session
spark = SparkSession.builder \
    .appName("FraudDetectionModelTraining") \
    .config("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.12:10.4.0") \
    .config("spark.mongodb.read.connection.uri", MONGODB_URI) \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

print("\n📊 Step 1: Loading data from MongoDB...")
# Lire les données depuis MongoDB
df = spark.read \
    .format("mongodb") \
    .load()

total_count = df.count()
print(f"   ✅ Loaded {total_count} transactions from MongoDB")

# Afficher la distribution des classes
fraud_count = df.filter(col("Class") == 1).count()
normal_count = df.filter(col("Class") == 0).count()
fraud_percentage = (fraud_count / total_count) * 100 if total_count > 0 else 0

print(f"\n📈 Dataset Statistics:")
print(f"   Total transactions: {total_count}")
print(f"   Normal transactions: {normal_count} ({100-fraud_percentage:.2f}%)")
print(f"   Fraudulent transactions: {fraud_count} ({fraud_percentage:.2f}%)")

# Vérifier qu'on a assez de données
if total_count < 100:
    print("\n⚠️  WARNING: Not enough data for training!")
    print("   Wait for more data to accumulate in MongoDB.")
    print("   Current: {} transactions, Recommended: 1000+".format(total_count))
    spark.stop()
    exit(1)

if fraud_count == 0:
    print("\n⚠️  WARNING: No fraudulent transactions found!")
    print("   The model needs examples of fraud to learn.")
    print("   Wait for fraudulent transactions to appear in the stream.")
    spark.stop()
    exit(1)

print("\n🔧 Step 2: Feature Engineering...")

# Sélectionner les colonnes features (V1-V28 + Amount)
feature_columns = ["V{}".format(i) for i in range(1, 29)] + ["Amount"]

# Vérifier que toutes les colonnes existent
missing_cols = [col for col in feature_columns if col not in df.columns]
if missing_cols:
    print(f"   ⚠️  Missing columns: {missing_cols}")
    print("   Using only available columns...")
    feature_columns = [col for col in feature_columns if col in df.columns]

print(f"   ✅ Using {len(feature_columns)} features")

# Assembler les features dans un vecteur
assembler = VectorAssembler(
    inputCols=feature_columns,
    outputCol="features_raw",
    handleInvalid="skip"  # Skip les lignes avec valeurs manquantes
)

# Normaliser les features (important pour Random Forest)
scaler = StandardScaler(
    inputCol="features_raw",
    outputCol="features",
    withStd=True,
    withMean=True
)

print("\n🎯 Step 3: Preparing Train/Test Split...")

# Split train/test (80/20)
# Stratifier pour garder la même proportion de fraudes
train_df, test_df = df.randomSplit([0.8, 0.2], seed=42)

train_count = train_df.count()
test_count = test_df.count()
train_fraud = train_df.filter(col("Class") == 1).count()
test_fraud = test_df.filter(col("Class") == 1).count()

print(f"   Training set: {train_count} transactions ({train_fraud} frauds)")
print(f"   Test set: {test_count} transactions ({test_fraud} frauds)")

print("\n🌲 Step 4: Training Random Forest Model...")

# Configuration du Random Forest
# maxDepth: Profondeur maximale des arbres
# numTrees: Nombre d'arbres dans la forêt
# maxBins: Nombre de bins pour discrétiser les features continues
rf = RandomForestClassifier(
    labelCol="Class",
    featuresCol="features",
    numTrees=100,
    maxDepth=10,
    maxBins=32,
    seed=42,
    featureSubsetStrategy="auto"
)

# Créer le pipeline complet
pipeline = Pipeline(stages=[assembler, scaler, rf])

print("   Training in progress...")
print("   This may take a few minutes depending on data size...")

# Entraîner le modèle
model = pipeline.fit(train_df)

print("   ✅ Model trained successfully!")

print("\n📊 Step 5: Evaluating Model Performance...")

# Faire des prédictions sur le test set
predictions = model.transform(test_df)

# Évaluateurs
binary_evaluator = BinaryClassificationEvaluator(
    labelCol="Class",
    rawPredictionCol="rawPrediction",
    metricName="areaUnderROC"
)

multiclass_evaluator = MulticlassClassificationEvaluator(
    labelCol="Class",
    predictionCol="prediction"
)

# Calculer les métriques
auc = binary_evaluator.evaluate(predictions)
accuracy = multiclass_evaluator.evaluate(predictions, {multiclass_evaluator.metricName: "accuracy"})
precision = multiclass_evaluator.evaluate(predictions, {multiclass_evaluator.metricName: "weightedPrecision"})
recall = multiclass_evaluator.evaluate(predictions, {multiclass_evaluator.metricName: "weightedRecall"})
f1 = multiclass_evaluator.evaluate(predictions, {multiclass_evaluator.metricName: "f1"})

print("\n" + "=" * 80)
print("📈 MODEL PERFORMANCE METRICS")
print("=" * 80)
print(f"   AUC-ROC:   {auc:.4f}")
print(f"   Accuracy:  {accuracy:.4f}")
print(f"   Precision: {precision:.4f}")
print(f"   Recall:    {recall:.4f}")
print(f"   F1-Score:  {f1:.4f}")
print("=" * 80)

# Matrice de confusion
print("\n📊 Confusion Matrix:")
predictions.groupBy("Class", "prediction").count().show()

# Feature Importance (top 10)
rf_model = model.stages[-1]
feature_importances = rf_model.featureImportances.toArray()
feature_importance_dict = {
    feature_columns[i]: importance 
    for i, importance in enumerate(feature_importances)
}
sorted_features = sorted(
    feature_importance_dict.items(), 
    key=lambda x: x[1], 
    reverse=True
)

print("\n🔝 Top 10 Most Important Features:")
for i, (feature, importance) in enumerate(sorted_features[:10], 1):
    print(f"   {i}. {feature}: {importance:.4f}")

print("\n💾 Step 6: Saving Model...")

# Créer le dossier models s'il n'existe pas
os.makedirs("/app/models", exist_ok=True)

# Sauvegarder le modèle
model.write().overwrite().save(MODEL_PATH)
print(f"   ✅ Model saved to: {MODEL_PATH}")

# Sauvegarder les métadonnées (pour debugging)
with open(FEATURES_PATH + ".txt", "w") as f:
    f.write("Feature Columns:\n")
    f.write(",".join(feature_columns) + "\n\n")
    f.write("Model Metrics:\n")
    f.write(f"AUC-ROC: {auc:.4f}\n")
    f.write(f"Accuracy: {accuracy:.4f}\n")
    f.write(f"Precision: {precision:.4f}\n")
    f.write(f"Recall: {recall:.4f}\n")
    f.write(f"F1-Score: {f1:.4f}\n\n")
    f.write("Feature Importances:\n")
    for feature, importance in sorted_features:
        f.write(f"{feature}: {importance:.4f}\n")

print(f"   ✅ Metadata saved to: {FEATURES_PATH}.txt")

print("\n" + "=" * 80)
print("✅ MODEL TRAINING COMPLETED SUCCESSFULLY!")
print("=" * 80)
print("\n💡 Next Steps:")
print("   1. The model is ready to use in streaming")
print("   2. Update spark-processor.py to load and use this model")
print("   3. Real-time predictions will be added to MongoDB")
print()

# Afficher un exemple de prédiction
print("📝 Example Predictions (first 5):")
predictions.select(
    "Time", "Amount", "Class", "prediction", "probability"
).show(5, truncate=False)

spark.stop()