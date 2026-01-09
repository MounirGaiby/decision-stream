# Script pour installer les dependances Python dans le container Spark
# Usage: .\setup-spark-dependencies.ps1

Write-Host "========================================" -ForegroundColor Green
Write-Host "Installing Python dependencies in Spark" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

Write-Host "Installing pip and Python packages..." -ForegroundColor Cyan
Write-Host "This may take 3-5 minutes..." -ForegroundColor Cyan
Write-Host ""

# Installer pip et les dependances
docker exec -u root spark bash -c "apt-get update && apt-get install -y python3-pip && python3 -m pip install --upgrade pip && pip3 install numpy pandas scikit-learn pymongo"

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "[SUCCESS] Dependencies installed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "You can now train the model:" -ForegroundColor Yellow
    Write-Host "  .\train-model.ps1" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "[ERROR] Failed to install dependencies!" -ForegroundColor Red
}