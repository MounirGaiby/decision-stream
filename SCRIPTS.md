# Available Scripts

This project includes automation scripts for both Windows and Unix-based systems.

## Quick Reference

| Action | Windows (PowerShell) | macOS/Linux (Bash) |
|--------|---------------------|-------------------|
| Install Spark dependencies | `.\setup-spark-dependencies.ps1` | `./setup-spark-dependencies.sh` |
| Start processor (no ML) | `.\start-spark-processor.ps1` | `./start-spark-processor.sh` |
| Train ML model | `.\train-model.ps1` | `./train-model.sh` |
| Start processor with ML | `.\start-spark-ml.ps1` | `./start-spark-ml.sh` |

## Python Monitoring Scripts (All Platforms)

```bash
python check-mongodb.py          # Check MongoDB data statistics
python check_ml_predictions.py   # Check ML prediction performance
```

## Docker Commands (All Platforms)

```bash
# Infrastructure
docker-compose up -d             # Start all services
docker-compose down              # Stop all services
docker ps                        # List running containers

# Logs
docker logs producer --tail 50   # View producer logs
docker logs spark --tail 50      # View Spark logs
docker logs kafka --tail 50      # View Kafka logs
docker logs mongodb --tail 50    # View MongoDB logs

# Access containers
docker exec -it spark bash       # Access Spark container
docker exec -it mongodb mongosh  # Access MongoDB shell
```

## Script Features

All scripts include:
- ✅ Docker connectivity check
- ✅ Container status verification
- ✅ Clear success/error messages
- ✅ Helpful tips on failure
- ✅ Colored output for better readability (PowerShell)

## Making Scripts Executable (Unix Only)

If you need to make the shell scripts executable:

```bash
chmod +x *.sh
```

This has already been done, but you may need to repeat it if you clone the repository fresh.
