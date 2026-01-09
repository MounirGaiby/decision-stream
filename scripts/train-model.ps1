# Script PowerShell pour entrainer le modele ML
# Usage: .\train-model.ps1

Write-Host "========================================" -ForegroundColor Green
Write-Host "Training Fraud Detection ML Model" -ForegroundColor Green
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
Write-Host "Starting model training..." -ForegroundColor Cyan
Write-Host "This will take 5-10 minutes depending on data size..." -ForegroundColor Cyan
Write-Host ""

# Lancer l'entrainement
docker exec spark /opt/spark/bin/spark-submit --master local[*] --packages org.mongodb.spark:mongo-spark-connector_2.12:10.4.0 /app/train_model.py

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "[SUCCESS] Model trained successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Stop current Spark processor if running (Ctrl+C)" -ForegroundColor White
    Write-Host "2. Start ML-enabled processor: scripts\start-spark-ml.ps1" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "[ERROR] Model training failed!" -ForegroundColor Red
    Write-Host "[TIP] Check logs with: docker logs spark" -ForegroundColor Yellow
}