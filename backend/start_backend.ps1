# GeoPredict — Start Backend
# Run this from the backend/ directory

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   GeoPredict Backend Startup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Activate virtual environment if it exists
if (Test-Path ".\venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & ".\venv\Scripts\Activate.ps1"
} else {
    Write-Host "No venv found. Using system Python." -ForegroundColor Yellow
    Write-Host "To create one: python -m venv venv" -ForegroundColor DarkYellow
}

Write-Host ""
Write-Host "Starting FastAPI server on http://localhost:8000" -ForegroundColor Green
Write-Host "API Docs available at http://localhost:8000/docs" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop the server." -ForegroundColor DarkGray
Write-Host ""

uvicorn main:app --reload --host 0.0.0.0 --port 8000
