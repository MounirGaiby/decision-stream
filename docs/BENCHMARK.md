# Benchmark Documentation

## Overview

The fraud detection pipeline includes comprehensive benchmarking tools to measure system performance, throughput, latency, and ML model accuracy.

## Quick Start

### Quick Benchmark (Fast Statistics)

Get instant performance metrics without waiting:

```bash
# Using just (recommended)
just benchmark-quick

# Or directly
python3 src/quick_benchmark.py
```

**Output includes:**
- Total transactions
- Fraud distribution
- ML performance (if available)
- Recent throughput estimate
- Amount statistics

### Comprehensive Benchmark

Run full benchmark suite (takes ~60 seconds):

```bash
# Using just (recommended)
just benchmark

# Or directly
python3 src/benchmark_pipeline.py
```

**Measures:**
- Throughput (transactions per second)
- Processing latency
- ML model performance
- Database query performance
- System resource usage (CPU, Memory, Disk)
- Data distribution statistics

### Custom Throughput Measurement

Measure throughput for a specific duration:

```bash
# Measure for 2 minutes (120 seconds)
just benchmark-throughput duration=120

# Or directly
python3 src/benchmark_pipeline.py --throughput-duration 120
```

## Benchmark Scripts

### 1. `quick_benchmark.py`

**Purpose**: Fast performance snapshot without waiting

**Usage**:
```bash
python3 src/quick_benchmark.py
```

**Metrics**:
- Database query performance
- Transaction counts
- Fraud distribution
- ML accuracy (if available)
- Recent throughput estimate (last 5 minutes)
- Amount statistics

**When to use**: 
- Quick health check
- Before/after system changes
- Regular monitoring

### 2. `benchmark_pipeline.py`

**Purpose**: Comprehensive performance analysis

**Usage**:
```bash
# Full benchmark (default 60 seconds)
python3 src/benchmark_pipeline.py

# Custom duration
python3 src/benchmark_pipeline.py --throughput-duration 120

# Only throughput
python3 src/benchmark_pipeline.py --throughput-only

# Only ML performance
python3 src/benchmark_pipeline.py --ml-only

# Only system resources
python3 src/benchmark_pipeline.py --system-only
```

**Metrics**:

#### Throughput
- Transactions processed
- Duration
- Transactions per second
- Transactions per minute
- Transactions per hour

#### Latency
- Average processing latency
- Minimum latency
- Maximum latency
- Median latency

#### ML Performance
- Total transactions
- ML prediction coverage
- Accuracy
- Precision
- Recall
- F1-Score
- Confusion matrix (TP, FP, TN, FN)
- Risk distribution
- Probability statistics

#### Database Performance
- Total documents
- Count query time
- Find query time
- Aggregation query time
- Index count

#### System Resources
- CPU usage (%)
- CPU core count
- Memory usage (%, total, used, available)
- Disk usage (%, total, used, free)

#### Data Distribution
- Total transactions
- Normal vs Fraud counts
- Fraud percentage
- Amount statistics (avg, min, max, std dev)
- Time range and span

**Output**: 
- Console output with formatted results
- JSON report file: `benchmark_report_YYYYMMDD_HHMMSS.json`

## Interpreting Results

### Throughput

**Good**: >10 transactions/second
- System is processing at expected rate
- No bottlenecks detected

**Warning**: 5-10 transactions/second
- System may be under load
- Check resource usage

**Critical**: <5 transactions/second
- Potential bottleneck
- Check Kafka, Spark, or MongoDB logs
- Verify producer is running

### Latency

**Good**: <1 second average
- Real-time processing working well
- Meets SLA requirements

**Warning**: 1-5 seconds
- Some delay in processing
- May need optimization

**Critical**: >5 seconds
- Significant delay
- Check Spark processing time
- Verify MongoDB write performance

### ML Accuracy

**Excellent**: >99%
- Model performing very well
- Low false positive/negative rates

**Good**: 95-99%
- Model performing well
- May need minor threshold adjustments

**Warning**: 90-95%
- Model accuracy declining
- Consider retraining

**Critical**: <90%
- Model needs retraining
- Check for data drift
- Review feature importance

### Database Performance

**Good**: 
- Count query: <100ms
- Find query: <200ms
- Aggregation: <500ms

**Warning**:
- Queries taking longer than above
- May need indexes (see DATABASE_STRUCTURE.md)

**Critical**:
- Queries >1 second
- Create indexes immediately
- Check MongoDB resource usage

### System Resources

**Good**:
- CPU: <70%
- Memory: <80%
- Disk: <80%

**Warning**:
- CPU: 70-90%
- Memory: 80-90%
- Disk: 80-90%

**Critical**:
- CPU: >90%
- Memory: >90%
- Disk: >90%
- Consider scaling up

## Best Practices

1. **Regular Monitoring**: Run `just benchmark-quick` daily
2. **Before Changes**: Benchmark before and after system modifications
3. **Performance Baselines**: Establish baseline metrics for comparison
4. **Trend Analysis**: Track metrics over time to detect degradation
5. **Alert Thresholds**: Set up alerts for critical metrics

## Troubleshooting

### No Data Found

**Error**: "No data found in MongoDB"

**Solution**:
1. Verify producer is running: `docker logs producer`
2. Verify processor is running: `docker logs spark`
3. Check MongoDB: `just check`

### ML Predictions Not Found

**Error**: "No ML predictions found"

**Solution**:
1. Train model: `just train`
2. Run ML processor: `just run-ml`
3. Wait for predictions to accumulate

### High Latency

**Symptoms**: Latency >5 seconds

**Solutions**:
1. Check Spark processing: `docker logs spark`
2. Check MongoDB performance: `just benchmark-quick`
3. Verify system resources: `just benchmark --system-only`
4. Check Kafka lag: `docker logs kafka`

### Low Throughput

**Symptoms**: <5 transactions/second

**Solutions**:
1. Check producer rate: `docker logs producer`
2. Verify Kafka is processing: `docker logs kafka`
3. Check Spark batch processing: `docker logs spark`
4. Verify system resources

## Integration with CI/CD

### Example: Automated Benchmarking

```bash
#!/bin/bash
# Run benchmark and check thresholds

python3 src/benchmark_pipeline.py --throughput-duration 60

# Check if throughput meets minimum
THROUGHPUT=$(python3 -c "import json; f=open('benchmark_report_*.json'); d=json.load(f); print(d['throughput']['transactions_per_second'])")
if (( $(echo "$THROUGHPUT < 10" | bc -l) )); then
    echo "ERROR: Throughput below threshold"
    exit 1
fi

# Check if accuracy meets minimum
ACCURACY=$(python3 -c "import json; f=open('benchmark_report_*.json'); d=json.load(f); print(d['ml']['accuracy'])")
if (( $(echo "$ACCURACY < 95" | bc -l) )); then
    echo "ERROR: ML accuracy below threshold"
    exit 1
fi
```

## Report Analysis

Benchmark reports are saved as JSON files. Example structure:

```json
{
  "throughput": {
    "transactions_processed": 600,
    "duration_seconds": 60.5,
    "transactions_per_second": 9.92,
    "transactions_per_minute": 595.2,
    "transactions_per_hour": 35712
  },
  "latency": {
    "sample_size": 100,
    "avg_seconds": 0.234,
    "min_seconds": 0.123,
    "max_seconds": 0.567,
    "median_seconds": 0.201
  },
  "ml": {
    "total_transactions": 10000,
    "ml_predictions": 5000,
    "coverage": 50.0,
    "accuracy": 99.85,
    "precision": 0.9884,
    "recall": 0.9551,
    "f1_score": 0.9714
  },
  "database": {
    "total_documents": 10000,
    "count_query_ms": 45.2,
    "find_query_ms": 123.5,
    "aggregation_query_ms": 234.7,
    "index_count": 6
  },
  "system": {
    "cpu_percent": 45.2,
    "cpu_count": 8,
    "memory_percent": 62.3,
    "memory_total_gb": 16.0,
    "memory_used_gb": 9.97,
    "memory_available_gb": 6.03
  }
}
```

## Next Steps

1. Run benchmarks regularly to establish baselines
2. Set up automated monitoring
3. Create dashboards from benchmark reports
4. Use results to optimize system performance
5. Integrate with Tableau for visualization (see TABLEAU_GUIDE.md)
