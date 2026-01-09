"""
Quick Benchmark Script - Fast performance metrics
Run this for quick statistics without waiting for throughput measurement
"""

from pymongo import MongoClient
from datetime import datetime, timedelta
import time

MONGO_URI = "mongodb://admin:admin123@localhost:27017/"
DATABASE = "fraud_detection"
COLLECTION = "transactions"

def quick_benchmark():
    """Run quick benchmark measurements"""
    client = MongoClient(MONGO_URI)
    db = client[DATABASE]
    collection = db[COLLECTION]
    
    print("=" * 80)
    print("⚡ QUICK BENCHMARK - Fraud Detection Pipeline")
    print("=" * 80)
    
    # Total transactions
    start = time.time()
    total = collection.count_documents({})
    count_time = (time.time() - start) * 1000
    
    print(f"\n📊 Database Statistics:")
    print(f"   Total transactions: {total:,}")
    print(f"   Count query time: {count_time:.2f} ms")
    
    if total == 0:
        print("\n⚠️  No data found. Start the producer and processor first.")
        client.close()
        return
    
    # Class distribution
    normal = collection.count_documents({"Class": 0})
    fraud = collection.count_documents({"Class": 1})
    
    print(f"\n🔍 Fraud Distribution:")
    print(f"   Normal: {normal:,} ({normal/total*100:.2f}%)")
    print(f"   Fraud: {fraud:,} ({fraud/total*100:.2f}%)")
    
    # ML predictions
    ml_count = collection.count_documents({"fraud_prediction": {"$exists": True}})
    if ml_count > 0:
        correct = collection.count_documents({
            "$expr": {"$eq": ["$Class", "$fraud_prediction"]}
        })
        accuracy = (correct / ml_count) * 100
        
        print(f"\n🤖 ML Performance:")
        print(f"   Predictions: {ml_count:,} ({ml_count/total*100:.1f}% coverage)")
        print(f"   Accuracy: {accuracy:.2f}%")
    
    # Recent throughput estimate (last 5 minutes)
    five_min_ago = datetime.now() - timedelta(minutes=5)
    recent_count = collection.count_documents({
        "processed_at": {"$gte": five_min_ago}
    })
    estimated_tps = recent_count / 300  # 5 minutes = 300 seconds
    
    print(f"\n⚡ Recent Throughput (last 5 min):")
    print(f"   Transactions: {recent_count:,}")
    print(f"   Estimated: {estimated_tps:.2f} transactions/second")
    
    # Amount stats
    pipeline = [
        {"$group": {
            "_id": None,
            "avg": {"$avg": "$Amount"},
            "max": {"$max": "$Amount"},
            "min": {"$min": "$Amount"}
        }}
    ]
    stats = list(collection.aggregate(pipeline))
    if stats:
        print(f"\n💰 Amount Statistics:")
        print(f"   Average: ${stats[0]['avg']:.2f}")
        print(f"   Range: ${stats[0]['min']:.2f} - ${stats[0]['max']:.2f}")
    
    print("\n" + "=" * 80)
    client.close()

if __name__ == "__main__":
    quick_benchmark()
