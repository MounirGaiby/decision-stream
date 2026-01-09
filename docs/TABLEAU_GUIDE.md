# Tableau Visualization Guide

## Overview

This guide provides step-by-step instructions for creating visualizations in Tableau to analyze the fraud detection pipeline data. Each chart helps make specific business decisions about fraud detection, system performance, and risk management.

## Prerequisites

1. **Tableau Desktop** or **Tableau Public** installed
2. **MongoDB Connection**: Tableau can connect to MongoDB using the MongoDB connector
3. **Data Access**: Ensure MongoDB is running and accessible

## Connecting to MongoDB

### Step 1: Connect to Data Source

1. Open Tableau Desktop
2. Click **"Connect to Data"**
3. Under **"To a Server"**, select **"MongoDB"**
4. Enter connection details:
   - **Server**: `localhost`
   - **Port**: `27017`
   - **Database**: `fraud_detection`
   - **Authentication**: Username: `admin`, Password: `admin123`
   - **Collection**: `transactions`

### Step 2: Configure Connection

- **Connection Type**: Live Connection (recommended for real-time updates)
- **Initial SQL**: Leave blank
- Click **"Sign In"**

### Step 3: Select Data

- In the data source pane, select the `transactions` collection
- Drag it to the canvas
- Click **"Sheet 1"** to start creating visualizations

## Chart 1: Fraud Detection Overview Dashboard

### Purpose
Provides a high-level overview of fraud detection performance and system health.

### Queries/Calculations Needed

1. **Total Transactions**: `COUNT([_id])`
2. **Fraud Rate**: `SUM(IF [Class] = 1 THEN 1 ELSE 0 END) / COUNT([_id])`
3. **ML Accuracy**: `SUM(IF [Class] = [fraud_prediction] THEN 1 ELSE 0 END) / COUNT([fraud_prediction])`
4. **Average Fraud Probability**: `AVG([fraud_probability])`

### Charts to Create

#### 1.1 Key Metrics Cards
- **Total Transactions**: Number card showing `COUNT([_id])`
- **Fraudulent Transactions**: Number card showing `SUM(IF [Class] = 1 THEN 1 ELSE 0 END)`
- **ML Accuracy**: Number card showing accuracy percentage
- **Average Fraud Probability**: Number card showing average probability

**Decision Support**: 
- **Total Transactions**: Monitor system throughput and data volume
- **Fraud Rate**: Track overall fraud prevalence (should be ~0.17% for this dataset)
- **ML Accuracy**: Assess model performance (target: >99%)
- **Average Probability**: Understand model confidence levels

#### 1.2 Fraud Distribution Pie Chart
- **Rows**: `Class` (grouped: 0 = Normal, 1 = Fraud)
- **Columns**: `COUNT([_id])`
- **Chart Type**: Pie Chart
- **Color**: Use different colors for Normal (green) and Fraud (red)

**Decision Support**: 
- **Visual Balance Check**: Verify the highly imbalanced nature of the dataset
- **Data Quality**: Ensure fraud cases are present in the data
- **Training Data Assessment**: Confirm sufficient fraud examples for model training

#### 1.3 Time Series - Transactions Over Time
- **Rows**: `Time` (convert to hours: `[Time] / 3600`)
- **Columns**: `COUNT([_id])`
- **Chart Type**: Line Chart
- **Color**: Split by `Class` (Normal vs Fraud)

**Decision Support**: 
- **Temporal Patterns**: Identify time periods with higher fraud rates
- **Peak Hours**: Determine when fraud spikes occur
- **System Load**: Understand transaction volume patterns
- **Anomaly Detection**: Spot unusual spikes that may indicate fraud campaigns

## Chart 2: ML Model Performance Analysis

### Purpose
Deep dive into machine learning model accuracy, precision, recall, and prediction quality.

### Queries/Calculations Needed

1. **True Positives**: `SUM(IF [Class] = 1 AND [fraud_prediction] = 1 THEN 1 ELSE 0 END)`
2. **False Positives**: `SUM(IF [Class] = 0 AND [fraud_prediction] = 1 THEN 1 ELSE 0 END)`
3. **True Negatives**: `SUM(IF [Class] = 0 AND [fraud_prediction] = 0 THEN 1 ELSE 0 END)`
4. **False Negatives**: `SUM(IF [Class] = 1 AND [fraud_prediction] = 0 THEN 1 ELSE 0 END)`
5. **Precision**: `[True Positives] / ([True Positives] + [False Positives])`
6. **Recall**: `[True Positives] / ([True Positives] + [False Negatives])`
7. **F1 Score**: `2 * ([Precision] * [Recall]) / ([Precision] + [Recall])`

### Charts to Create

#### 2.1 Confusion Matrix Heatmap
- **Rows**: `Class` (0, 1)
- **Columns**: `fraud_prediction` (0, 1)
- **Color**: `COUNT([_id])`
- **Chart Type**: Heatmap
- **Labels**: Show count and percentage

**Decision Support**: 
- **Model Assessment**: Understand where the model makes mistakes
- **False Positive Rate**: High false positives = too many alerts (costly)
- **False Negative Rate**: High false negatives = missed fraud (risky)
- **Balance Optimization**: Adjust model threshold based on business cost of errors

#### 2.2 Precision-Recall Curve
- **Rows**: `fraud_probability` (binned into 10 bins: 0-0.1, 0.1-0.2, ..., 0.9-1.0)
- **Columns**: Precision and Recall (dual axis)
- **Chart Type**: Line Chart with dual axis

**Decision Support**: 
- **Threshold Selection**: Choose optimal probability threshold for fraud alerts
- **Trade-off Analysis**: Balance between catching fraud (recall) and reducing false alarms (precision)
- **Business Rules**: Set alert thresholds based on acceptable false positive rate

#### 2.3 Fraud Probability Distribution
- **Rows**: `fraud_probability` (binned)
- **Columns**: `COUNT([_id])`
- **Color**: `Class` (Actual fraud vs Normal)
- **Chart Type**: Histogram

**Decision Support**: 
- **Model Confidence**: Understand how confident the model is in its predictions
- **Risk Stratification**: Categorize transactions into risk levels (Low: <0.3, Medium: 0.3-0.7, High: >0.7)
- **Alert Prioritization**: Focus investigation on high-probability cases first

#### 2.4 Prediction Accuracy Over Time
- **Rows**: `processed_at` (grouped by hour/day)
- **Columns**: `SUM(IF [Class] = [fraud_prediction] THEN 1 ELSE 0 END) / COUNT([fraud_prediction])`
- **Chart Type**: Line Chart

**Decision Support**: 
- **Model Stability**: Check if model performance degrades over time
- **Retraining Triggers**: Identify when model accuracy drops (indicates need for retraining)
- **Data Drift Detection**: Spot changes in transaction patterns

## Chart 3: Transaction Amount Analysis

### Purpose
Analyze transaction amounts to identify fraud patterns and unusual spending behaviors.

### Queries/Calculations Needed

1. **Amount Bins**: Create bins: $0-10, $10-50, $50-100, $100-500, $500-1000, $1000+
2. **Average Amount by Class**: `AVG(IF [Class] = 1 THEN [Amount] END)`
3. **Amount Deviation**: `[Amount] - AVG([Amount])`

### Charts to Create

#### 3.1 Amount Distribution by Fraud Status
- **Rows**: `Amount` (binned)
- **Columns**: `COUNT([_id])`
- **Color**: `Class` (Normal vs Fraud)
- **Chart Type**: Stacked Bar Chart

**Decision Support**: 
- **Fraud Patterns**: Identify amount ranges where fraud is more common
- **Risk Thresholds**: Set transaction amount limits for automatic review
- **Business Rules**: Create rules like "Flag transactions >$1000 with high probability"

#### 3.2 Average Amount Comparison
- **Rows**: `Class` (Normal, Fraud)
- **Columns**: `AVG([Amount])`
- **Chart Type**: Bar Chart

**Decision Support**: 
- **Fraud Characteristics**: Understand if fraud typically involves higher or lower amounts
- **Feature Importance**: Confirm that Amount is a useful feature for fraud detection
- **Policy Decisions**: Adjust fraud detection rules based on amount patterns

#### 3.3 High-Value Transaction Risk
- **Rows**: `Amount` (filter: > $1000)
- **Columns**: `fraud_probability`
- **Color**: `Class`
- **Chart Type**: Scatter Plot

**Decision Support**: 
- **High-Value Risk**: Identify high-value transactions with high fraud probability
- **Priority Investigation**: Focus manual review on high-value, high-probability cases
- **Loss Prevention**: Prevent large financial losses by catching high-value fraud early

## Chart 4: Temporal Analysis

### Purpose
Understand fraud patterns over time, identify peak fraud periods, and optimize system resources.

### Queries/Calculations Needed

1. **Hour of Day**: `HOUR([processed_at])`
2. **Day of Week**: `DAYOFWEEK([processed_at])`
3. **Fraud Rate by Time**: `SUM(IF [Class] = 1 THEN 1 ELSE 0 END) / COUNT([_id])`

### Charts to Create

#### 4.1 Fraud Rate by Hour of Day
- **Rows**: `HOUR([processed_at])`
- **Columns**: `SUM(IF [Class] = 1 THEN 1 ELSE 0 END) / COUNT([_id])`
- **Chart Type**: Bar Chart or Line Chart

**Decision Support**: 
- **Peak Fraud Hours**: Identify times when fraud is most common
- **Resource Allocation**: Schedule more fraud analysts during peak hours
- **Real-time Monitoring**: Increase alert sensitivity during high-risk periods
- **Pattern Recognition**: Detect if fraudsters have preferred attack times

#### 4.2 Transaction Volume vs Fraud Rate
- **Rows**: `HOUR([processed_at])`
- **Columns**: Dual axis:
  - `COUNT([_id])` (Transaction Volume)
  - `SUM(IF [Class] = 1 THEN 1 ELSE 0 END) / COUNT([_id])` (Fraud Rate)
- **Chart Type**: Dual-axis Line Chart

**Decision Support**: 
- **Correlation Analysis**: Understand if fraud rate correlates with transaction volume
- **System Load**: Plan system capacity for peak transaction periods
- **Anomaly Detection**: Spot hours where fraud rate is unusually high despite low volume

#### 4.3 Fraud Probability Heatmap by Time
- **Rows**: `HOUR([processed_at])`
- **Columns**: `fraud_probability` (binned: Low, Medium, High)
- **Color**: `COUNT([_id])`
- **Chart Type**: Heatmap

**Decision Support**: 
- **Risk Patterns**: Visualize when high-risk transactions occur
- **Temporal Clustering**: Identify if fraud attempts cluster in specific time windows
- **Proactive Measures**: Implement time-based fraud prevention rules

## Chart 5: Risk Stratification Dashboard

### Purpose
Categorize transactions by risk level and prioritize investigation efforts.

### Queries/Calculations Needed

1. **Risk Level**: 
   ```
   IF [fraud_probability] < 0.3 THEN "Low"
   ELSEIF [fraud_probability] < 0.7 THEN "Medium"
   ELSE "High"
   END
   ```
2. **Risk Score**: `[fraud_probability] * [Amount]` (combines probability and impact)
3. **Alert Priority**: 
   ```
   IF [Risk Score] > 500 THEN "Critical"
   ELSEIF [Risk Score] > 100 THEN "High"
   ELSEIF [fraud_probability] > 0.7 THEN "Medium"
   ELSE "Low"
   END
   ```

### Charts to Create

#### 5.1 Risk Level Distribution
- **Rows**: `Risk Level` (calculated field)
- **Columns**: `COUNT([_id])`
- **Color**: `Risk Level`
- **Chart Type**: Bar Chart or Pie Chart

**Decision Support**: 
- **Workload Planning**: Estimate how many transactions need manual review
- **Resource Requirements**: Determine analyst staffing needs
- **Automation Opportunities**: Identify low-risk transactions that can be auto-approved

#### 5.2 Risk Score Scatter Plot
- **Rows**: `Amount`
- **Columns**: `fraud_probability`
- **Color**: `Risk Level`
- **Size**: `Risk Score`
- **Chart Type**: Scatter Plot

**Decision Support**: 
- **Priority Queue**: Rank transactions for investigation (top-right quadrant = highest priority)
- **Resource Allocation**: Focus limited analyst time on highest-risk cases
- **Loss Prevention**: Prevent large losses by catching high-amount, high-probability fraud

#### 5.3 Alert Priority Queue
- **Rows**: `Alert Priority` (calculated field)
- **Columns**: `COUNT([_id])`
- **Color**: `Alert Priority`
- **Chart Type**: Bar Chart
- **Sort**: By priority (Critical → High → Medium → Low)

**Decision Support**: 
- **Investigation Queue**: Create prioritized list for fraud analysts
- **SLA Management**: Set response time targets by priority level
- **Workflow Design**: Design fraud investigation workflows based on priority

## Chart 6: System Performance Dashboard

### Purpose
Monitor pipeline performance, throughput, and system health.

### Queries/Calculations Needed

1. **Transactions per Minute**: `COUNT([_id]) / (MAX([processed_at]) - MIN([processed_at])) * 60`
2. **Processing Lag**: `NOW() - [processed_at]`
3. **ML Coverage**: `COUNT([fraud_prediction]) / COUNT([_id])`

### Charts to Create

#### 6.1 Throughput Over Time
- **Rows**: `processed_at` (grouped by minute or hour)
- **Columns**: `COUNT([_id])`
- **Chart Type**: Line Chart

**Decision Support**: 
- **System Capacity**: Monitor if system can handle transaction volume
- **Bottleneck Detection**: Identify periods of low throughput (may indicate system issues)
- **Scaling Decisions**: Determine when to scale up infrastructure

#### 6.2 Processing Latency
- **Rows**: `processed_at` (grouped by hour)
- **Columns**: `AVG([Processing Lag])` (in seconds)
- **Chart Type**: Line Chart

**Decision Support**: 
- **Real-time Performance**: Ensure fraud detection happens quickly enough
- **SLA Compliance**: Monitor if processing meets real-time requirements (< 1 second target)
- **System Optimization**: Identify performance degradation periods

#### 6.3 ML Prediction Coverage
- **Rows**: `processed_at` (grouped by hour)
- **Columns**: `COUNT([fraud_prediction]) / COUNT([_id])`
- **Chart Type**: Line Chart

**Decision Support**: 
- **Model Availability**: Ensure ML model is active and making predictions
- **System Health**: Detect if ML processor stops working
- **Coverage Monitoring**: Track percentage of transactions with ML predictions

## Decision-Making Framework

### Individual Chart Decisions

#### From Fraud Detection Overview:
- **If fraud rate > 0.5%**: Investigate data quality or potential fraud campaign
- **If ML accuracy < 95%**: Retrain model or investigate data drift
- **If average probability > 0.5**: Model may be too sensitive, adjust threshold

#### From ML Performance Analysis:
- **If false positives > 5%**: Increase probability threshold to reduce false alarms
- **If false negatives > 1%**: Decrease threshold or retrain model (high risk)
- **If precision drops over time**: Retrain model with recent data

#### From Transaction Amount Analysis:
- **If fraud concentrated in low amounts**: Implement micro-transaction monitoring
- **If high-value fraud detected**: Implement immediate blocking for high-value, high-probability transactions
- **If amount patterns change**: Investigate new fraud techniques

#### From Temporal Analysis:
- **If fraud spikes at specific hours**: Increase monitoring during those periods
- **If fraud rate correlates with volume**: Normal pattern, maintain current detection
- **If fraud rate spikes without volume increase**: Potential coordinated attack

#### From Risk Stratification:
- **If >10% transactions are High Risk**: Investigate model threshold or data quality
- **If Critical alerts > 100/day**: Increase analyst capacity or automate more
- **If Low Risk transactions have fraud**: Model may need retraining

### Collective Decision-Making

#### Combining Multiple Charts:

1. **Fraud Campaign Detection**:
   - **Temporal Analysis** shows fraud spike at specific time
   - **Amount Analysis** shows similar amounts
   - **ML Performance** shows high probability scores
   - **Decision**: Activate enhanced monitoring, block similar transactions, alert security team

2. **Model Retraining Trigger**:
   - **ML Performance** shows accuracy dropping
   - **Temporal Analysis** shows new fraud patterns
   - **Risk Stratification** shows increasing false positives
   - **Decision**: Schedule model retraining, collect recent fraud examples

3. **System Scaling Decision**:
   - **System Performance** shows throughput approaching limits
   - **Temporal Analysis** shows increasing transaction volume
   - **Processing Latency** shows increasing delays
   - **Decision**: Scale up Kafka partitions, add Spark workers, increase MongoDB capacity

4. **Policy Adjustment**:
   - **Risk Stratification** shows too many false positives
   - **ML Performance** shows high precision but low recall
   - **Amount Analysis** shows fraud in specific ranges
   - **Decision**: Adjust probability threshold, create amount-based rules, update business policies

5. **Resource Optimization**:
   - **Risk Stratification** shows 80% transactions are Low Risk
   - **ML Performance** shows high accuracy on Low Risk
   - **System Performance** shows capacity available
   - **Decision**: Automate Low Risk approvals, focus analysts on Medium/High Risk

## Best Practices

1. **Refresh Frequency**: Set dashboards to auto-refresh every 5-15 minutes for real-time monitoring
2. **Alert Thresholds**: Create Tableau alerts for critical metrics (e.g., accuracy < 95%, fraud rate > 1%)
3. **Drill-Down**: Enable drill-down capabilities to investigate anomalies
4. **Export Data**: Use Tableau's export feature to share findings with stakeholders
5. **Mobile Access**: Enable Tableau Mobile for on-the-go monitoring
6. **Scheduled Reports**: Set up daily/weekly reports for management

## Troubleshooting

### Connection Issues
- Verify MongoDB is running: `docker ps | grep mongodb`
- Check connection string and credentials
- Ensure MongoDB port 27017 is accessible

### Missing Data
- Verify producer and processor are running
- Check if ML predictions exist (may need to run ML processor)
- Verify data collection has enough time to accumulate

### Performance Issues
- Use data extracts instead of live connections for large datasets
- Create indexes in MongoDB (see DATABASE_STRUCTURE.md)
- Filter data at the source level in Tableau

## Next Steps

1. Create the dashboards following this guide
2. Customize calculations based on your specific business needs
3. Set up alerts and automated reports
4. Train analysts on interpreting the visualizations
5. Iterate and refine based on feedback and new requirements
