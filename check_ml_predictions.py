"""
Script de verification des predictions ML dans MongoDB
Affiche les statistiques sur les predictions et la performance du modele
"""

from pymongo import MongoClient
from datetime import datetime

# Configuration MongoDB
MONGO_URI = "mongodb://admin:admin123@localhost:27017/"
DATABASE = "fraud_detection"
COLLECTION = "transactions"

def check_ml_predictions():
    """
    Verifie les predictions ML et affiche les statistiques
    """
    try:
        # Connexion a MongoDB
        client = MongoClient(MONGO_URI)
        db = client[DATABASE]
        collection = db[COLLECTION]
        
        print("=" * 80)
        print("🤖 ML PREDICTIONS - MongoDB Statistics")
        print("=" * 80)
        
        # Nombre total de transactions
        total_count = collection.count_documents({})
        print(f"\n📈 Total transactions: {total_count}")
        
        if total_count == 0:
            print("\n⚠️  No data found in MongoDB!")
            client.close()
            return
        
        # Verifier si on a des predictions ML
        ml_count = collection.count_documents({"fraud_prediction": {"$exists": True}})
        
        if ml_count == 0:
            print("\n⚠️  No ML predictions found!")
            print("💡 Steps to enable ML predictions:")
            print("   1. Train the model: train-model.bat (or .ps1)")
            print("   2. Stop current processor (Ctrl+C)")
            print("   3. Start ML processor: start-spark-ml.bat (or .ps1)")
            client.close()
            return
        
        print(f"🤖 Transactions with ML predictions: {ml_count} ({ml_count/total_count*100:.1f}%)")
        
        # Statistiques sur les vraies labels
        actual_fraud = collection.count_documents({"Class": 1})
        actual_normal = collection.count_documents({"Class": 0})
        
        print(f"\n📊 Actual Labels (Ground Truth):")
        print(f"   ✅ Normal: {actual_normal} ({actual_normal/total_count*100:.2f}%)")
        print(f"   🚨 Fraud: {actual_fraud} ({actual_fraud/total_count*100:.2f}%)")
        
        # Statistiques sur les predictions
        if ml_count > 0:
            predicted_fraud = collection.count_documents({"fraud_prediction": 1})
            predicted_normal = collection.count_documents({"fraud_prediction": 0})
            
            print(f"\n🤖 ML Predictions:")
            print(f"   ✅ Predicted Normal: {predicted_normal} ({predicted_normal/ml_count*100:.2f}%)")
            print(f"   🚨 Predicted Fraud: {predicted_fraud} ({predicted_fraud/ml_count*100:.2f}%)")
            
            # Calculer l'accuracy
            correct_predictions = collection.count_documents({
                "$expr": {"$eq": ["$Class", "$fraud_prediction"]}
            })
            accuracy = (correct_predictions / ml_count) * 100
            
            print(f"\n📈 Model Performance:")
            print(f"   Accuracy: {accuracy:.2f}%")
            print(f"   Correct: {correct_predictions}/{ml_count}")
            print(f"   Wrong: {ml_count - correct_predictions}/{ml_count}")
            
            # Matrice de confusion
            true_positives = collection.count_documents({
                "Class": 1, 
                "fraud_prediction": 1
            })
            false_positives = collection.count_documents({
                "Class": 0, 
                "fraud_prediction": 1
            })
            true_negatives = collection.count_documents({
                "Class": 0, 
                "fraud_prediction": 0
            })
            false_negatives = collection.count_documents({
                "Class": 1, 
                "fraud_prediction": 0
            })
            
            print(f"\n📊 Confusion Matrix:")
            print(f"   True Positives (Fraud detected):     {true_positives}")
            print(f"   False Positives (False alarm):       {false_positives}")
            print(f"   True Negatives (Normal detected):    {true_negatives}")
            print(f"   False Negatives (Fraud missed):      {false_negatives}")
            
            # Precision et Recall
            if (true_positives + false_positives) > 0:
                precision = true_positives / (true_positives + false_positives)
                print(f"\n   Precision: {precision:.2%}")
            
            if (true_positives + false_negatives) > 0:
                recall = true_positives / (true_positives + false_negatives)
                print(f"   Recall: {recall:.2%}")
            
            # Transactions a haut risque
            high_risk = collection.count_documents({"fraud_probability": {"$gt": 0.8}})
            medium_risk = collection.count_documents({
                "fraud_probability": {"$gt": 0.5, "$lte": 0.8}
            })
            low_risk = collection.count_documents({
                "fraud_probability": {"$lte": 0.5}
            })
            
            print(f"\n🎯 Risk Distribution:")
            print(f"   🔴 High Risk (>80%):    {high_risk}")
            print(f"   🟡 Medium Risk (50-80%): {medium_risk}")
            print(f"   🟢 Low Risk (<50%):      {low_risk}")
            
            # Top 5 transactions suspectes
            print(f"\n⚠️  Top 5 Most Suspicious Transactions:")
            print("-" * 80)
            
            suspicious = collection.find(
                {"fraud_prediction": {"$exists": True}}
            ).sort("fraud_probability", -1).limit(5)
            
            for i, doc in enumerate(suspicious, 1):
                fraud_label = "🚨 FRAUD" if doc.get("Class") == 1 else "✅ Normal"
                prediction = "🚨 FRAUD" if doc.get("fraud_prediction") == 1 else "✅ Normal"
                amount = doc.get("Amount", 0)
                probability = doc.get("fraud_probability", 0) * 100
                time = doc.get("Time", 0)
                
                match = "✅" if doc.get("Class") == doc.get("fraud_prediction") else "❌"
                
                print(f"{i}. {match} Actual: {fraud_label} | Predicted: {prediction}")
                print(f"   Amount: ${amount:.2f} | Fraud Probability: {probability:.1f}% | Time: {time:.0f}s")
            
            # Statistiques de probabilite
            pipeline = [
                {"$match": {"fraud_probability": {"$exists": True}}},
                {
                    "$group": {
                        "_id": None,
                        "avg_probability": {"$avg": "$fraud_probability"},
                        "max_probability": {"$max": "$fraud_probability"},
                        "min_probability": {"$min": "$fraud_probability"}
                    }
                }
            ]
            
            prob_stats = list(collection.aggregate(pipeline))
            if prob_stats:
                print(f"\n📊 Fraud Probability Statistics:")
                print(f"   Average: {prob_stats[0]['avg_probability']*100:.2f}%")
                print(f"   Maximum: {prob_stats[0]['max_probability']*100:.2f}%")
                print(f"   Minimum: {prob_stats[0]['min_probability']*100:.2f}%")
        
        print("\n" + "=" * 80)
        client.close()
        
    except Exception as e:
        print(f"\n❌ Error connecting to MongoDB: {e}")
        print("\n💡 Make sure MongoDB container is running:")
        print("   docker ps | grep mongodb")

if __name__ == "__main__":
    check_ml_predictions()