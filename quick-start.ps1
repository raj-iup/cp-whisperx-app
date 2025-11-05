# CP-WhisperX-App Quick Start Script
# Full subtitle generation workflow with consistent logging

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$InputVideo
)

$ErrorActionPreference = "Stop"

# Logging functions
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [quick-start] [$Level] $Message"
    
    switch ($Level) {
        "ERROR" { Write-Host $logMessage -ForegroundColor Red }
        "WARNING" { Write-Host $logMessage -ForegroundColor Yellow }
        "SUCCESS" { Write-Host $logMessage -ForegroundColor Green }
        default { Write-Host $logMessage }
    }
}

function Write-Header {
    param([string]$Title)
    Write-Host ""
    Write-Host ("=" * 60) -ForegroundColor Cyan
    Write-Host $Title -ForegroundColor Cyan
    Write-Host ("=" * 60) -ForegroundColor Cyan
}

function Write-Step {
    param([string]$Title)
    Write-Host ""
    Write-Host $Title -ForegroundColor Yellow
    Write-Host ("-" * 60) -ForegroundColor Yellow
}

# Start
Write-Header "CP-WHISPERX-APP QUICK START (WINDOWS)"
Write-Log "Input: $InputVideo" "INFO"
Write-Host ""

# Validate input
if (-not (Test-Path $InputVideo)) {
    Write-Log "Input video not found: $InputVideo" "ERROR"
    exit 1
}

# Step 1: Preflight checks
Write-Step "Step 1/3: Running preflight checks..."
Write-Log "Validating system requirements..." "INFO"

& python preflight.py
if ($LASTEXITCODE -ne 0) {
    Write-Log "Preflight checks failed! Please fix errors before continuing." "ERROR"
    exit 1
}
Write-Log "Preflight checks passed" "SUCCESS"

# Step 2: Prepare job
Write-Step "Step 2/3: Preparing job..."
Write-Log "Creating job structure and configuration..." "INFO"

& python prepare-job.py $InputVideo --subtitle-gen
if ($LASTEXITCODE -ne 0) {
    Write-Log "Job preparation failed!" "ERROR"
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
    Write-Log "Could not find created job directory" "ERROR"
    exit 1
}

$jobId = $jobDirs[0].Name
Write-Log "Job ID: $jobId" "SUCCESS"

# Step 3: Run pipeline
Write-Step "Step 3/3: Running pipeline..."
Write-Log "Executing full subtitle generation pipeline..." "INFO"

& python pipeline.py --job $jobId
if ($LASTEXITCODE -ne 0) {
    Write-Log "Pipeline execution failed!" "ERROR"
    exit 1
}

# Success
Write-Header "QUICK START COMPLETE"
Write-Log "Job completed successfully" "SUCCESS"
Write-Host ""
Write-Host "Check output directory: out\$year\$month\$day\*\$jobId"
Write-Host ""

exit 0
