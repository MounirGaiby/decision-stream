# Script PowerShell pour lancer le Spark Processor avec ML
# Usage: .\start-spark-ml.ps1

Write-Host "========================================" -ForegroundColor Green
Write-Host "Starting Spark ML Streaming Processor" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Verifier que Docker fonctionne
$dockerRunning = docker ps 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Docker is not running!" -ForegroundColor Red
    Write-Host "[TIP] Start Docker Desktop and try again." -ForegroundColor Yellow
    exit 1
}

Write-Host "[OK] Docker is running" -ForegroundColor Green
Write-Host ""
Write-Host "Starting Spark Streaming job with ML predictions..." -ForegroundColor Cyan
Write-Host ""

# Lancer Spark Submit avec le processeur ML
docker exec spark /opt/spark/bin/spark-submit `
    --master local[*] `
    --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.mongodb.spark:mongo-spark-connector_2.12:10.4.0 `
    --conf spark.mongodb.write.connection.uri="mongodb://admin:admin123@mongodb:27017/fraud_detection.transactions?authSource=admin" `
    /app/spark-processor-ml.py

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "[SUCCESS] Spark job completed!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "[ERROR] Spark job failed!" -ForegroundColor Red
    Write-Host "[TIP] Check logs with: docker logs spark" -ForegroundColor Yellow
}