# CP-WhisperX-App Test: Windows CUDA Subtitle Generation
# Test T02: Full pipeline with CUDA acceleration

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

# Load common logging
. "$PSScriptRoot\..\scripts\common-logging.ps1"

Write-LogSection "Test T02: Windows CUDA Subtitle Generation"

# Check for CUDA
Write-LogInfo "Checking CUDA availability..."
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}'); exit(0 if torch.cuda.is_available() else 1)"

if ($LASTEXITCODE -ne 0) {
    Write-LogWarn "CUDA not available - test requires GPU"
    exit 1
}

# Check for sample media
$sampleVideo = ".\in\sample_movie.mp4"
if (-not (Test-Path $sampleVideo)) {
    Write-LogWarn "$sampleVideo not found"
    Write-Host "  Place a sample video file at $sampleVideo" -ForegroundColor Yellow
    exit 1
}

# Prepare job (without --native, will use Docker GPU)
Write-LogInfo "Preparing job for CUDA acceleration..."
python prepare-job.py `
    $sampleVideo `
    --start-time 00:10:00 `
    --end-time 00:15:00 `
    --subtitle-gen

if ($LASTEXITCODE -ne 0) {
    Write-LogFailure "Failed to create job"
    exit 1
}

# Get job ID
$today = Get-Date
$year = $today.ToString("yyyy")
$month = $today.ToString("MM")
$day = $today.ToString("dd")

$jobsPath = "jobs\$year\$month\$day"
$jobId = Get-ChildItem $jobsPath -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 1 -ExpandProperty Name

if (-not $jobId) {
    Write-LogFailure "Failed to find job ID"
    exit 1
}

Write-LogInfo "Job ID: $jobId"

# Run pipeline with GPU
Write-LogInfo "Running pipeline with CUDA..."
python pipeline.py --job $jobId

if ($LASTEXITCODE -ne 0) {
    Write-LogFailure "Pipeline failed"
    exit 1
}

# Verify CUDA usage
$outputDir = "out\$year\$month\$day\$jobId"
$manifest = Get-Content "$outputDir\manifest.json" -Raw

if ($manifest -match '"device":\s*"cuda"') {
    Write-LogSuccess "CUDA acceleration confirmed"
    Write-LogSuccess "Test T02 PASSED"
    exit 0
} else {
    Write-LogFailure "CUDA was not used (fell back to CPU)"
    Write-LogFailure "Test T02 FAILED"
    exit 1
}
