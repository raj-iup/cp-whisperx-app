# CP-WhisperX-App Quick Start Script
# Full subtitle generation workflow with consistent logging

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$InputVideo
)

$ErrorActionPreference = "Stop"

# Load common logging
. "$PSScriptRoot\scripts\common-logging.ps1"

# Start
Write-LogSection "CP-WHISPERX-APP QUICK START (WINDOWS)"
Write-LogInfo "Input: $InputVideo"
Write-Host ""

# Validate input
if (-not (Test-Path $InputVideo)) {
    Write-LogError "Input video not found: $InputVideo"
    exit 1
}

# Step 1: Preflight checks
Write-Host ""
Write-Host "Step 1/3: Running preflight checks..." -ForegroundColor Yellow
Write-Host ("-" * 60) -ForegroundColor Yellow
Write-LogInfo "Validating system requirements..."

& python scripts\preflight.py
if ($LASTEXITCODE -ne 0) {
    Write-LogError "Preflight checks failed! Please fix errors before continuing."
    exit 1
}
Write-LogSuccess "Preflight checks passed"

# Step 2: Prepare job
Write-Host ""
Write-Host "Step 2/3: Preparing job..." -ForegroundColor Yellow
Write-Host ("-" * 60) -ForegroundColor Yellow
Write-LogInfo "Creating job structure and configuration..."

& python scripts\prepare-job.py $InputVideo --subtitle-gen
if ($LASTEXITCODE -ne 0) {
    Write-LogError "Job preparation failed!"
    exit 1
}

# Extract job ID from the most recent job directory
$year = (Get-Date).Year
$month = (Get-Date).ToString("MM")
$day = (Get-Date).ToString("dd")

$jobDirs = Get-ChildItem -Path "out\$year\$month\$day" -Directory -ErrorAction SilentlyContinue |
    Get-ChildItem -Directory -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending

if (-not $jobDirs) {
    Write-LogError "Could not find created job directory"
    exit 1
}

$jobId = $jobDirs[0].Name
Write-LogSuccess "Job ID: $jobId"

# Step 3: Run pipeline
Write-Host ""
Write-Host "Step 3/3: Running pipeline..." -ForegroundColor Yellow
Write-Host ("-" * 60) -ForegroundColor Yellow
Write-LogInfo "Executing full subtitle generation pipeline..."

& python scripts\pipeline.py --job $jobId
if ($LASTEXITCODE -ne 0) {
    Write-LogError "Pipeline execution failed!"
    exit 1
}

# Success
Write-LogSection "QUICK START COMPLETE"
Write-LogSuccess "Job completed successfully"
Write-Host ""
Write-Host "Check output directory: out\$year\$month\$day\*\$jobId"
Write-Host ""

exit 0
