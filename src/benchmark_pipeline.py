"""
Benchmark Script for Fraud Detection Pipeline
Measures performance metrics including:
- Transactions per second (throughput)
- Processing latency
- System resource usage
- ML prediction performance
- Database query performance
"""

import time
import psutil
import os
from datetime import datetime, timedelta
from pymongo import MongoClient
from collections import defaultdict
import json

# Configuration
MONGO_URI = "mongodb://admin:admin123@localhost:27017/"
DATABASE = "fraud_detection"
COLLECTION = "transactions"

class PipelineBenchmark:
    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[DATABASE]
        self.collection = self.db[COLLECTION]
        self.results = {}
        
    def print_header(self, title):
        """Print a formatted section header"""
        print("\n" + "=" * 80)
        print(f"📊 {title}")
        print("=" * 80)
    
    def measure_throughput(self, duration_seconds=60):
        """
        Measure transactions per second (TPS) over a time period
        """
        self.print_header("THROUGHPUT MEASUREMENT")
        
        print(f"⏱️  Measuring throughput for {duration_seconds} seconds...")
        print("   (Make sure producer and processor are running)")
        
        # Get initial count
        initial_count = self.collection.count_documents({})
        initial_time = time.time()
        
        print(f"\n📈 Initial state:")
        print(f"   Transactions: {initial_count}")
        print(f"   Timestamp: {datetime.now().isoformat()}")
        
        # Wait for measurement period
        print(f"\n⏳ Waiting {duration_seconds} seconds...")
        time.sleep(duration_seconds)
        
        # Get final count
        final_count = self.collection.count_documents({})
        final_time = time.time()
        elapsed = final_time - initial_time
        
        transactions_processed = final_count - initial_count
        tps = transactions_processed / elapsed if elapsed > 0 else 0
        
        self.results['throughput'] = {
            'transactions_processed': transactions_processed,
            'duration_seconds': elapsed,
            'transactions_per_second': tps,
            'transactions_per_minute': tps * 60,
            'transactions_per_hour': tps * 3600
        }
        
        print(f"\n✅ Results:")
        print(f"   Transactions processed: {transactions_processed:,}")
        print(f"   Duration: {elapsed:.2f} seconds")
        print(f"   Throughput: {tps:.2f} transactions/second")
        print(f"   Throughput: {tps * 60:.2f} transactions/minute")
        print(f"   Throughput: {tps * 3600:.0f} transactions/hour")
        
        return tps
    
    def measure_processing_latency(self, sample_size=100):
        """
        Measure end-to-end processing latency
        Compares processed_at timestamp with transaction Time
        """
        self.print_header("PROCESSING LATENCY MEASUREMENT")
        
        print(f"📊 Sampling {sample_size} recent transactions...")
        
        # Get recent transactions with processing timestamps
        recent = list(self.collection.find(
            {"processed_at": {"$exists": True}}
        ).sort("processed_at", -1).limit(sample_size))
        
        if len(recent) == 0:
            print("⚠️  No transactions with processing timestamps found")
            return
        
        latencies = []
        for doc in recent:
            if "processed_at" in doc:
                processed = doc["processed_at"]
                if isinstance(processed, datetime):
                    # Calculate latency (in seconds)
                    # Note: This is approximate as we compare processing time with transaction Time
                    latency = (datetime.now() - processed).total_seconds()
                    latencies.append(latency)
        
        if not latencies:
            print("⚠️  Could not calculate latencies")
            return
        
        avg_latency = sum(latencies) / len(latencies)
        min_latency = min(latencies)
        max_latency = max(latencies)
        median_latency = sorted(latencies)[len(latencies) // 2]
        
        self.results['latency'] = {
            'sample_size': len(latencies),
            'avg_seconds': avg_latency,
            'min_seconds': min_latency,
            'max_seconds': max_latency,
            'median_seconds': median_latency
        }
        
        print(f"\n✅ Latency Statistics:")
        print(f"   Sample size: {len(latencies)}")
        print(f"   Average: {avg_latency:.3f} seconds")
        print(f"   Minimum: {min_latency:.3f} seconds")
        print(f"   Maximum: {max_latency:.3f} seconds")
        print(f"   Median: {median_latency:.3f} seconds")
    
    def measure_database_performance(self):
        """
        Measure MongoDB query performance
        """
        self.print_header("DATABASE PERFORMANCE")
        
        # Count query
        start = time.time()
        total_count = self.collection.count_documents({})
        count_time = (time.time() - start) * 1000  # ms
        
        # Find query
        start = time.time()
        list(self.collection.find().limit(100))
        find_time = (time.time() - start) * 1000  # ms
        
        # Aggregation query
        start = time.time()
        pipeline = [
            {"$group": {
                "_id": None,
                "avg_amount": {"$avg": "$Amount"},
                "fraud_count": {"$sum": {"$cond": [{"$eq": ["$Class", 1]}, 1, 0]}}
            }}
        ]
        list(self.collection.aggregate(pipeline))
        agg_time = (time.time() - start) * 1000  # ms
        
        # Index check
        indexes = list(self.collection.list_indexes())
        index_count = len(indexes)
        
        self.results['database'] = {
            'total_documents': total_count,
            'count_query_ms': count_time,
            'find_query_ms': find_time,
            'aggregation_query_ms': agg_time,
            'index_count': index_count
        }
        
        print(f"✅ Query Performance:")
        print(f"   Total documents: {total_count:,}")
        print(f"   Count query: {count_time:.2f} ms")
        print(f"   Find query (100 docs): {find_time:.2f} ms")
        print(f"   Aggregation query: {agg_time:.2f} ms")
        print(f"   Indexes: {index_count}")
    
    def measure_ml_performance(self):
        """
        Measure ML prediction performance and accuracy
        """
        self.print_header("ML MODEL PERFORMANCE")
        
        total = self.collection.count_documents({})
        ml_count = self.collection.count_documents({"fraud_prediction": {"$exists": True}})
        
        if ml_count == 0:
            print("⚠️  No ML predictions found")
            print("   Run the ML processor to generate predictions")
            return
        
        # Calculate accuracy
        correct = self.collection.count_documents({
            "$expr": {"$eq": ["$Class", "$fraud_prediction"]}
        })
        accuracy = (correct / ml_count) * 100 if ml_count > 0 else 0
        
        # Confusion matrix
        tp = self.collection.count_documents({"Class": 1, "fraud_prediction": 1})
        fp = self.collection.count_documents({"Class": 0, "fraud_prediction": 1})
        tn = self.collection.count_documents({"Class": 0, "fraud_prediction": 0})
        fn = self.collection.count_documents({"Class": 1, "fraud_prediction": 0})
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        # Probability statistics
        prob_pipeline = [
            {"$match": {"fraud_probability": {"$exists": True}}},
            {"$group": {
                "_id": None,
                "avg_prob": {"$avg": "$fraud_probability"},
                "max_prob": {"$max": "$fraud_probability"},
                "min_prob": {"$min": "$fraud_probability"}
            }}
        ]
        prob_stats = list(self.collection.aggregate(prob_pipeline))
        
        self.results['ml'] = {
            'total_transactions': total,
            'ml_predictions': ml_count,
            'coverage': (ml_count / total * 100) if total > 0 else 0,
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'true_positives': tp,
            'false_positives': fp,
            'true_negatives': tn,
            'false_negatives': fn
        }
        
        if prob_stats:
            self.results['ml']['avg_probability'] = prob_stats[0]['avg_prob']
            self.results['ml']['max_probability'] = prob_stats[0]['max_prob']
            self.results['ml']['min_probability'] = prob_stats[0]['min_prob']
        
        print(f"✅ ML Performance Metrics:")
        print(f"   Total transactions: {total:,}")
        print(f"   ML predictions: {ml_count:,} ({ml_count/total*100:.1f}% coverage)")
        print(f"   Accuracy: {accuracy:.2f}%")
        print(f"   Precision: {precision:.2%}")
        print(f"   Recall: {recall:.2%}")
        print(f"   F1-Score: {f1:.4f}")
        print(f"\n📊 Confusion Matrix:")
        print(f"   True Positives: {tp}")
        print(f"   False Positives: {fp}")
        print(f"   True Negatives: {tn}")
        print(f"   False Negatives: {fn}")
        
        if prob_stats:
            print(f"\n📈 Probability Statistics:")
            print(f"   Average: {prob_stats[0]['avg_prob']*100:.2f}%")
            print(f"   Maximum: {prob_stats[0]['max_prob']*100:.2f}%")
            print(f"   Minimum: {prob_stats[0]['min_prob']*100:.2f}%")
    
    def measure_system_resources(self):
        """
        Measure system resource usage (CPU, Memory, Disk)
        """
        self.print_header("SYSTEM RESOURCES")
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_total_gb = memory.total / (1024**3)
        memory_used_gb = memory.used / (1024**3)
        memory_available_gb = memory.available / (1024**3)
        
        # Disk usage
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        disk_total_gb = disk.total / (1024**3)
        disk_used_gb = disk.used / (1024**3)
        disk_free_gb = disk.free / (1024**3)
        
        self.results['system'] = {
            'cpu_percent': cpu_percent,
            'cpu_count': cpu_count,
            'memory_percent': memory_percent,
            'memory_total_gb': memory_total_gb,
            'memory_used_gb': memory_used_gb,
            'memory_available_gb': memory_available_gb,
            'disk_percent': disk_percent,
            'disk_total_gb': disk_total_gb,
            'disk_used_gb': disk_used_gb,
            'disk_free_gb': disk_free_gb
        }
        
        print(f"✅ System Resources:")
        print(f"   CPU: {cpu_percent:.1f}% (of {cpu_count} cores)")
        print(f"   Memory: {memory_percent:.1f}% ({memory_used_gb:.2f} GB / {memory_total_gb:.2f} GB)")
        print(f"   Disk: {disk_percent:.1f}% ({disk_used_gb:.2f} GB / {disk_total_gb:.2f} GB)")
    
    def measure_data_distribution(self):
        """
        Measure data distribution statistics
        """
        self.print_header("DATA DISTRIBUTION")
        
        total = self.collection.count_documents({})
        
        # Class distribution
        normal = self.collection.count_documents({"Class": 0})
        fraud = self.collection.count_documents({"Class": 1})
        
        # Amount statistics
        amount_pipeline = [
            {"$group": {
                "_id": None,
                "avg": {"$avg": "$Amount"},
                "min": {"$min": "$Amount"},
                "max": {"$max": "$Amount"},
                "std": {"$stdDevPop": "$Amount"}
            }}
        ]
        amount_stats = list(self.collection.aggregate(amount_pipeline))
        
        # Time range
        time_pipeline = [
            {"$group": {
                "_id": None,
                "min_time": {"$min": "$Time"},
                "max_time": {"$max": "$Time"}
            }}
        ]
        time_stats = list(self.collection.aggregate(time_pipeline))
        
        self.results['distribution'] = {
            'total': total,
            'normal': normal,
            'fraud': fraud,
            'fraud_percentage': (fraud / total * 100) if total > 0 else 0
        }
        
        if amount_stats:
            self.results['distribution']['amount_avg'] = amount_stats[0]['avg']
            self.results['distribution']['amount_min'] = amount_stats[0]['min']
            self.results['distribution']['amount_max'] = amount_stats[0]['max']
            self.results['distribution']['amount_std'] = amount_stats[0].get('std', 0)
        
        if time_stats:
            self.results['distribution']['time_min'] = time_stats[0]['min_time']
            self.results['distribution']['time_max'] = time_stats[0]['max_time']
            time_span = time_stats[0]['max_time'] - time_stats[0]['min_time']
            self.results['distribution']['time_span_hours'] = time_span / 3600
        
        print(f"✅ Data Distribution:")
        print(f"   Total transactions: {total:,}")
        print(f"   Normal: {normal:,} ({normal/total*100:.2f}%)")
        print(f"   Fraud: {fraud:,} ({fraud/total*100:.2f}%)")
        
        if amount_stats:
            print(f"\n💰 Amount Statistics:")
            print(f"   Average: ${amount_stats[0]['avg']:.2f}")
            print(f"   Minimum: ${amount_stats[0]['min']:.2f}")
            print(f"   Maximum: ${amount_stats[0]['max']:.2f}")
            if 'std' in amount_stats[0]:
                print(f"   Std Dev: ${amount_stats[0]['std']:.2f}")
        
        if time_stats:
            time_span = time_stats[0]['max_time'] - time_stats[0]['min_time']
            print(f"\n⏰ Time Range:")
            print(f"   Start: {time_stats[0]['min_time']:.0f} seconds")
            print(f"   End: {time_stats[0]['max_time']:.0f} seconds")
            print(f"   Span: {time_span/3600:.2f} hours")
    
    def generate_report(self):
        """
        Generate a comprehensive benchmark report
        """
        self.print_header("COMPREHENSIVE BENCHMARK REPORT")
        
        print(f"\n📅 Generated: {datetime.now().isoformat()}")
        print(f"\n📊 Summary:")
        
        if 'throughput' in self.results:
            tps = self.results['throughput']['transactions_per_second']
            print(f"   Throughput: {tps:.2f} transactions/second")
        
        if 'latency' in self.results:
            avg_lat = self.results['latency']['avg_seconds']
            print(f"   Avg Latency: {avg_lat:.3f} seconds")
        
        if 'ml' in self.results:
            acc = self.results['ml']['accuracy']
            print(f"   ML Accuracy: {acc:.2f}%")
        
        if 'database' in self.results:
            count_time = self.results['database']['count_query_ms']
            print(f"   DB Query Time: {count_time:.2f} ms")
        
        if 'system' in self.results:
            cpu = self.results['system']['cpu_percent']
            mem = self.results['system']['memory_percent']
            print(f"   System: CPU {cpu:.1f}%, Memory {mem:.1f}%")
        
        # Save to file
        report_file = f"benchmark_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n💾 Full report saved to: {report_file}")
        
        return self.results
    
    def run_all(self, throughput_duration=60):
        """
        Run all benchmark measurements
        """
        print("\n" + "=" * 80)
        print("🚀 FRAUD DETECTION PIPELINE BENCHMARK")
        print("=" * 80)
        print(f"\n⏱️  Starting comprehensive benchmark...")
        print(f"   Throughput measurement duration: {throughput_duration} seconds")
        
        try:
            # System resources (quick)
            self.measure_system_resources()
            
            # Data distribution (quick)
            self.measure_data_distribution()
            
            # Database performance (quick)
            self.measure_database_performance()
            
            # ML performance (if available)
            self.measure_ml_performance()
            
            # Processing latency
            self.measure_processing_latency()
            
            # Throughput (takes time)
            self.measure_throughput(throughput_duration)
            
            # Generate final report
            self.generate_report()
            
        except Exception as e:
            print(f"\n❌ Error during benchmark: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.client.close()

def main():
    """
    Main entry point
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Benchmark Fraud Detection Pipeline')
    parser.add_argument('--throughput-duration', type=int, default=60,
                       help='Duration in seconds for throughput measurement (default: 60)')
    parser.add_argument('--throughput-only', action='store_true',
                       help='Only measure throughput')
    parser.add_argument('--ml-only', action='store_true',
                       help='Only measure ML performance')
    parser.add_argument('--system-only', action='store_true',
                       help='Only measure system resources')
    
    args = parser.parse_args()
    
    benchmark = PipelineBenchmark()
    
    if args.throughput_only:
        benchmark.measure_throughput(args.throughput_duration)
    elif args.ml_only:
        benchmark.measure_ml_performance()
    elif args.system_only:
        benchmark.measure_system_resources()
    else:
        benchmark.run_all(args.throughput_duration)

if __name__ == "__main__":
    main()
