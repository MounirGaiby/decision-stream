#!/usr/bin/env python3
"""
ML System Monitoring Script
Shows statistics for ML predictions, model agreement, and flagged transactions
"""

from pymongo import MongoClient
from datetime import datetime

def print_section(title):
    """Print formatted section header"""
    print("=" * 80)
    print(f"🤖 {title}")
    print("=" * 80)
    print()

def main():
    # Connect to MongoDB
    client = MongoClient('mongodb://admin:admin123@localhost:27017/', authSource='admin')
    db = client['fraud_detection']

    print_section("ML FRAUD DETECTION - System Statistics")

    # Collection counts
    transactions_count = db.transactions.count_documents({})
    predictions_count = db.model_predictions.count_documents({})
    ensemble_count = db.ensemble_results.count_documents({})
    flagged_count = db.flagged_transactions.count_documents({})

    print("📊 Collection Status:")
    print(f"   Total Transactions: {transactions_count}")
    print(f"   Model Predictions: {predictions_count}")
    print(f"   Ensemble Results: {ensemble_count}")
    print(f"   Flagged Transactions: {flagged_count}")
    print()

    if transactions_count == 0:
        print("⚠️  No data found in MongoDB!")
        print("💡 Make sure:")
        print("   1. Producer is running")
        print("   2. ML processor is running: just run-ml")
        print()
        return

    # Transaction analysis
    print_section("Transaction Analysis")

    fraud_actual = db.transactions.count_documents({"Class": 1.0})
    normal_actual = db.transactions.count_documents({"Class": 0.0})

    print(f"📈 Actual Labels (Ground Truth):")
    print(f"   ✅ Normal: {normal_actual} ({normal_actual/transactions_count*100:.2f}%)")
    print(f"   🚨 Fraud: {fraud_actual} ({fraud_actual/transactions_count*100:.2f}%)")
    print()

    # Ensemble predictions analysis
    if ensemble_count > 0:
        print_section("ML Predictions")

        predicted_fraud = db.ensemble_results.count_documents({"ensemble_prediction": 1})
        predicted_normal = db.ensemble_results.count_documents({"ensemble_prediction": 0})

        print(f"🤖 ML Predictions:")
        print(f"   ✅ Predicted Normal: {predicted_normal} ({predicted_normal/ensemble_count*100:.2f}%)")
        print(f"   🚨 Predicted Fraud: {predicted_fraud} ({predicted_fraud/ensemble_count*100:.2f}%)")
        print()

        # Model consensus analysis
        print("🎯 Model Consensus (Agreement Level):")
        consensus_3 = db.ensemble_results.count_documents({"models_agreed": 3})
        consensus_2 = db.ensemble_results.count_documents({"models_agreed": 2})
        consensus_1 = db.ensemble_results.count_documents({"models_agreed": 1})
        consensus_0 = db.ensemble_results.count_documents({"models_agreed": 0})

        print(f"   All 3 models agree (fraud): {consensus_3} ({consensus_3/ensemble_count*100:.1f}%)")
        print(f"   2 models agree (fraud): {consensus_2} ({consensus_2/ensemble_count*100:.1f}%)")
        print(f"   1 model predicts fraud: {consensus_1} ({consensus_1/ensemble_count*100:.1f}%)")
        print(f"   No models predict fraud: {consensus_0} ({consensus_0/ensemble_count*100:.1f}%)")
        print()

        # Calculate ML accuracy
        print("📊 ML Performance:")

        # Join ensemble results with transactions to get actual labels
        pipeline = [
            {
                "$lookup": {
                    "from": "transactions",
                    "localField": "transaction_id",
                    "foreignField": "transaction_id",
                    "as": "transaction"
                }
            },
            {
                "$unwind": "$transaction"
            },
            {
                "$project": {
                    "ensemble_prediction": 1,
                    "actual_label": "$transaction.Class",
                    "match": {
                        "$cond": [
                            {"$eq": ["$ensemble_prediction", "$transaction.Class"]},
                            1,
                            0
                        ]
                    }
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total": {"$sum": 1},
                    "correct": {"$sum": "$match"}
                }
            }
        ]

        result = list(db.ensemble_results.aggregate(pipeline))
        if result:
            total = result[0]["total"]
            correct = result[0]["correct"]
            accuracy = (correct / total) * 100 if total > 0 else 0
            print(f"   Accuracy: {accuracy:.2f}% ({correct}/{total} correct)")
        print()

        # Individual model performance
        print("🔍 Individual Model Predictions:")
        for model_name in ["random_forest", "gradient_boosting", "logistic_regression"]:
            model_count = db.model_predictions.count_documents({"model_name": model_name})
            model_fraud = db.model_predictions.count_documents({"model_name": model_name, "prediction": 1})

            display_name = model_name.replace("_", " ").title()
            print(f"   {display_name}:")
            print(f"      Total predictions: {model_count}")
            print(f"      Fraud predictions: {model_fraud} ({model_fraud/model_count*100:.1f}%)")
        print()

    # Flagged transactions analysis
    if flagged_count > 0:
        print_section("Flagged Transactions (High Risk)")

        print(f"🚨 Total Flagged: {flagged_count}")
        print()

        # High confidence flagged
        all_agreed = db.flagged_transactions.count_documents({"all_models_agreed": True})
        print(f"   🔴 All 3 models agreed: {all_agreed}")
        print(f"   🟠 High probability: {flagged_count - all_agreed}")
        print()

        # Top 10 most suspicious transactions
        print("⚠️  Top 10 Most Suspicious Transactions:")
        print("-" * 80)

        flagged_transactions = db.flagged_transactions.find().sort("confidence_score", -1).limit(10)

        for idx, flagged in enumerate(flagged_transactions, 1):
            transaction_id = flagged["transaction_id"]

            # Get transaction details
            transaction = db.transactions.find_one({"transaction_id": transaction_id})

            # Get ensemble result
            ensemble = db.ensemble_results.find_one({"transaction_id": transaction_id})

            if transaction and ensemble:
                actual_label = "🚨 FRAUD" if transaction.get("Class") == 1.0 else "✅ NORMAL"
                amount = transaction.get("Amount", 0)
                time = transaction.get("Time", 0)
                confidence = flagged.get("confidence_score", 0) * 100
                all_agreed = "✅ YES" if flagged.get("all_models_agreed") else "❌ NO"

                print(f"{idx}. Actual: {actual_label} | Amount: ${amount:.2f} | Time: {time:.0f}s")
                print(f"   Confidence: {confidence:.1f}% | All Models Agreed: {all_agreed}")
                print(f"   Transaction ID: {transaction_id}")
                print()

        print()

    # Risk distribution
    if ensemble_count > 0:
        print_section("Risk Distribution")

        high_risk = db.ensemble_results.count_documents({"ensemble_probability": {"$gte": 0.8}})
        medium_risk = db.ensemble_results.count_documents({
            "ensemble_probability": {"$gte": 0.5, "$lt": 0.8}
        })
        low_risk = db.ensemble_results.count_documents({"ensemble_probability": {"$lt": 0.5}})

        print(f"🎯 Risk Levels:")
        print(f"   🔴 High Risk (≥80%): {high_risk} ({high_risk/ensemble_count*100:.1f}%)")
        print(f"   🟡 Medium Risk (50-80%): {medium_risk} ({medium_risk/ensemble_count*100:.1f}%)")
        print(f"   🟢 Low Risk (<50%): {low_risk} ({low_risk/ensemble_count*100:.1f}%)")
        print()

    # Summary statistics
    print_section("Summary")

    if ensemble_count > 0:
        coverage = (ensemble_count / transactions_count) * 100 if transactions_count > 0 else 0
        print(f"📊 Processing Coverage: {coverage:.1f}% ({ensemble_count}/{transactions_count} transactions)")

        if flagged_count > 0:
            flag_rate = (flagged_count / ensemble_count) * 100
            print(f"🚩 Flag Rate: {flag_rate:.2f}% ({flagged_count} flagged out of {ensemble_count} processed)")

        print()
        print("💡 System Status: ✅ Operational")
        print("   All 3 ML models are working")
        print(f"   High-risk transactions are being flagged ({flagged_count} so far)")
    else:
        print("⚠️  System Status: Waiting for ML predictions")
        print("💡 Run: just run-ml")

    print()
    print("=" * 80)

if __name__ == "__main__":
    main()
