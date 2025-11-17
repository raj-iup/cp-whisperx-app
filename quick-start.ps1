# CP-WhisperX-App Quick Start Script (PowerShell)
# Full subtitle generation workflow with consistent logging
# Windows - CUDA optimized

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$InputVideo,
    
    [Parameter(Mandatory=$false)]
    [switch]$Help
)

$ErrorActionPreference = "Stop"

# Load common logging
. "$PSScriptRoot\scripts\common-logging.ps1"

# Show help
if ($Help) {
    Write-Host @"
Usage: .\quick-start.ps1 <input_video>

Full subtitle generation workflow (Windows - CUDA optimized)

ARGUMENTS:
  <input_video>         Path to input video file (required)

EXAMPLES:
  # Process movie with full subtitle generation
  .\quick-start.ps1 C:\videos\movie.mp4

"@
    exit 0
}

# Validate input
if (-not $InputVideo) {
    Write-LogError "Input video is required"
    Write-Host "Usage: .\quick-start.ps1 <input_video>"
    Write-Host "Example: .\quick-start.ps1 in\movie.mp4"
    exit 1
}

Write-LogSection "CP-WHISPERX-APP QUICK START (CUDA)"
Write-LogInfo "Input: $InputVideo"
Write-Host ""

if (-not (Test-Path $InputVideo)) {
    Write-LogError "Input video not found: $InputVideo"
    exit 1
}

# Step 1: Ensure environment is set up
Write-Host ""
Write-Host "Step 1/3: Checking environment..."
Write-Host "------------------------------------------------------------"
Write-LogInfo "Verifying virtual environment setup..."

if (-not (Test-Path ".bollyenv")) {
    Write-LogWarning "Virtual environment not found. Running bootstrap..."
    & "$PSScriptRoot\scripts\bootstrap.ps1"
    if ($LASTEXITCODE -ne 0) {
        Write-LogError "Bootstrap failed! Please check errors."
        exit 1
    }
} else {
    Write-LogSuccess "Environment ready"
}

# Step 2: Prepare job
Write-Host ""
Write-Host "Step 2/3: Preparing job..."
Write-Host "------------------------------------------------------------"
Write-LogInfo "Creating job structure and configuration..."

& python scripts\prepare-job.py $InputVideo --subtitle-gen
if ($LASTEXITCODE -ne 0) {
    Write-LogError "Job preparation failed!"
    exit 1
}

# Extract job ID from most recent job directory
$year = (Get-Date).Year
$month = (Get-Date).ToString("MM")
$day = (Get-Date).ToString("dd")

$jobDir = Get-ChildItem -Path "out\$year\$month\$day" -Directory -Recurse -Filter "2*-*" -ErrorAction SilentlyContinue |
    Sort-Object Name -Descending |
    Select-Object -First 1

if (-not $jobDir) {
    Write-LogError "Could not find created job directory"
    exit 1
}

$jobId = $jobDir.Name
Write-LogSuccess "Job ID: $jobId"

# Step 3: Run pipeline
Write-Host ""
Write-Host "Step 3/3: Running pipeline..."
Write-Host "------------------------------------------------------------"
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
