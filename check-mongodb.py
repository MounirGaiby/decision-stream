"""
Script de vérification des données dans MongoDB
Permet de vérifier que les transactions sont bien enregistrées
"""

from pymongo import MongoClient
from datetime import datetime

# Configuration MongoDB
MONGO_URI = "mongodb://admin:admin123@localhost:27017/"
DATABASE = "fraud_detection"
COLLECTION = "transactions"

def check_mongodb():
    """
    Vérifie la connexion et affiche des statistiques sur les données
    """
    try:
        # Connexion à MongoDB
        client = MongoClient(MONGO_URI)
        db = client[DATABASE]
        collection = db[COLLECTION]
        
        print("=" * 80)
        print("📊 FRAUD DETECTION - MongoDB Statistics")
        print("=" * 80)
        
        # Nombre total de transactions
        total_count = collection.count_documents({})
        print(f"\n📈 Total transactions: {total_count}")
        
        if total_count > 0:
            # Statistiques sur les fraudes
            fraud_count = collection.count_documents({"Class": 1})
            normal_count = collection.count_documents({"Class": 0})
            fraud_percentage = (fraud_count / total_count) * 100
            
            print(f"\n🔍 Fraud Analysis:")
            print(f"   ✅ Normal transactions: {normal_count} ({100-fraud_percentage:.2f}%)")
            print(f"   🚨 Fraudulent transactions: {fraud_count} ({fraud_percentage:.2f}%)")
            
            # Dernières transactions
            print(f"\n📝 Latest 5 transactions:")
            print("-" * 80)
            
            latest = collection.find().sort("processed_at", -1).limit(5)
            for i, doc in enumerate(latest, 1):
                fraud_label = "🚨 FRAUD" if doc.get("Class") == 1 else "✅ Normal"
                amount = doc.get("Amount", 0)
                time = doc.get("Time", 0)
                processed = doc.get("processed_at", "N/A")
                
                print(f"{i}. {fraud_label} | Amount: ${amount:.2f} | Time: {time:.0f}s | Processed: {processed}")
            
            # Statistiques sur les montants
            pipeline = [
                {
                    "$group": {
                        "_id": None,
                        "avg_amount": {"$avg": "$Amount"},
                        "max_amount": {"$max": "$Amount"},
                        "min_amount": {"$min": "$Amount"}
                    }
                }
            ]
            
            stats = list(collection.aggregate(pipeline))
            if stats:
                print(f"\n💰 Amount Statistics:")
                print(f"   Average: ${stats[0]['avg_amount']:.2f}")
                print(f"   Maximum: ${stats[0]['max_amount']:.2f}")
                print(f"   Minimum: ${stats[0]['min_amount']:.2f}")
            
            # Statistiques par heure (basé sur Time)
            print(f"\n⏰ Data Collection Status:")
            pipeline_time = [
                {
                    "$group": {
                        "_id": {"$floor": {"$divide": ["$Time", 3600]}},  # Group by hour
                        "count": {"$sum": 1}
                    }
                },
                {"$sort": {"_id": 1}},
                {"$limit": 10}
            ]
            
            hourly_stats = list(collection.aggregate(pipeline_time))
            for stat in hourly_stats:
                hour = int(stat['_id'])
                count = stat['count']
                print(f"   Hour {hour}: {count} transactions")
        
        else:
            print("\n⚠️  No data found in MongoDB!")
            print("💡 Make sure:")
            print("   1. Kafka producer is running")
            print("   2. Spark processor is running")
            print("   3. Check logs with: docker logs spark")
        
        print("\n" + "=" * 80)
        client.close()
        
    except Exception as e:
        print(f"\n❌ Error connecting to MongoDB: {e}")
        print("\n💡 Make sure MongoDB container is running:")
        print("   docker ps | grep mongodb")

if __name__ == "__main__":
    check_mongodb()