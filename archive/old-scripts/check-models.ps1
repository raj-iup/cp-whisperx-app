# Check ML model status and cache
param(
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Arguments
)

$ErrorActionPreference = "Stop"

$VenvPath = ".bollyenv"

# Check if virtual environment exists
if (-not (Test-Path $VenvPath)) {
    Write-Host "ERROR: Virtual environment not found. Please run .\scripts\bootstrap.ps1 first" -ForegroundColor Red
    exit 1
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Cyan
& "$VenvPath\Scripts\Activate.ps1"

# Run model checker
Write-Host ""
Write-Host "======================================================================" -ForegroundColor Yellow
Write-Host "  ML MODEL STATUS CHECK" -ForegroundColor Yellow
Write-Host "======================================================================" -ForegroundColor Yellow
Write-Host ""

python shared/model_checker.py @Arguments

exit $LASTEXITCODE
