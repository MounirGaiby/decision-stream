# Quick Start Instructions

## Setup (First Time Only)

```bash
just setup
```
Starts all Docker containers and installs dependencies.

## Basic Workflow

### 1. Accumulate Training Data
```bash
just run-basic
```
Runs Spark processor without ML to collect transactions. Let it run for 5-10 minutes to get ~5000 transactions, then press Ctrl+C.

### 2. Train Models
```bash
just train
```
Trains 3 ML models (Random Forest, Gradient Boosting, Logistic Regression). Takes 10-15 minutes.

### 3. Run with ML Predictions
```bash
just run-ml
```
Runs Spark processor with ML predictions. Processes transactions in real-time and saves predictions to MongoDB.

### 4. Export to Excel for Tableau
```bash
just export-excel
```
Exports all MongoDB collections to Excel files in `data/` folder for Tableau analysis.

## Useful Commands

```bash
just check          # Check MongoDB data and statistics
just check-model    # Check if models exist
just check-ml       # Check ML predictions and performance
just status         # Show container status
just stop           # Stop all containers
just clean          # Clean all data and models (fresh start)
```

## Additional Documentation

- **Database Structure**: See [DATABASE_STRUCTURE.md](DATABASE_STRUCTURE.md)
- **Tableau Guide**: See [TABLEAU_GUIDE.md](TABLEAU_GUIDE.md)
- **Benchmarking**: Run `just benchmark` to measure performance
