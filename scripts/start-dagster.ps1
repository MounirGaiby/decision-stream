# Start Dagster Web Server (PowerShell)
# Access the UI at http://localhost:3000

Write-Host "========================================" -ForegroundColor Green
Write-Host "Starting Dagster Web Server" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Set Dagster home directory
$env:DAGSTER_HOME = "$PWD\.dagster"

# Create dagster home if it doesn't exist
if (!(Test-Path $env:DAGSTER_HOME)) {
    New-Item -ItemType Directory -Path $env:DAGSTER_HOME | Out-Null
}

Write-Host "[INFO] Dagster Home: $env:DAGSTER_HOME"
Write-Host ""

# Check if services are running
Write-Host "[INFO] Checking Docker services..." -ForegroundColor Cyan
docker ps --format "table {{.Names}}`t{{.Status}}" | Select-String -Pattern "kafka|mongodb|spark"
Write-Host ""

# Activate venv
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "[INFO] Activating virtual environment..." -ForegroundColor Cyan
    & "venv\Scripts\Activate.ps1"
} else {
    Write-Host "[WARNING] Virtual environment not found." -ForegroundColor Yellow
    Write-Host "Run: python -m venv venv" -ForegroundColor Yellow
    Write-Host "Then: venv\Scripts\Activate.ps1" -ForegroundColor Yellow
    Write-Host "Finally: pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "🚀 Starting Dagster UI" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Access the Dagster UI at: http://localhost:3000" -ForegroundColor Cyan
Write-Host ""
Write-Host "Available jobs:" -ForegroundColor Yellow
Write-Host "  - full_pipeline: Complete workflow"
Write-Host "  - accumulate_data: Data accumulation only"
Write-Host "  - train_models: Model training only"
Write-Host "  - run_ml_predictions: ML predictions only"
Write-Host "  - validate_data: Data validation only"
Write-Host ""
Write-Host "Press Ctrl+C to stop" -ForegroundColor Red
Write-Host ""

# Start Dagster webserver
dagster-webserver -h 0.0.0.0 -p 3000 -w workspace.yaml
