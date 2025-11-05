# CP-WhisperX-App Test: Windows Native Subtitle Generation
# Test T01: Full pipeline with native acceleration

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

# Load common logging
. "$PSScriptRoot\..\scripts\common-logging.ps1"

Write-LogSection "Test T01: Windows Native Subtitle Generation"

# Check for sample media
$sampleVideo = ".\in\sample_movie.mp4"
if (-not (Test-Path $sampleVideo)) {
    Write-LogWarn "$sampleVideo not found"
    Write-Host "  Place a sample video file at $sampleVideo" -ForegroundColor Yellow
    exit 1
}

# Prepare job with native acceleration
Write-LogInfo "Preparing job with native acceleration..."
python prepare-job.py `
    $sampleVideo `
    --start-time 00:10:00 `
    --end-time 00:15:00 `
    --subtitle-gen `
    --native

if ($LASTEXITCODE -ne 0) {
    Write-LogFailure "Failed to create job"
    exit 1
}

# Get job ID from most recent job
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

# Run pipeline
Write-LogInfo "Running pipeline..."
python pipeline.py --job $jobId

if ($LASTEXITCODE -ne 0) {
    Write-LogFailure "Pipeline failed"
    exit 1
}

# Verify outputs
Write-Host ""
Write-LogInfo "Verifying outputs..."
$outputDir = "out\$year\$month\$day\$jobId"

$checksPassed = 0
$checksFailed = 0

# Check manifest
if (Test-Path "$outputDir\manifest.json") {
    Write-LogSuccess "Manifest created"
    $checksPassed++
} else {
    Write-LogFailure "Manifest missing"
    $checksFailed++
}

# Check subtitles
if (Test-Path "$outputDir\subtitles\subtitles.srt") {
    Write-LogSuccess "Subtitles created"
    $checksPassed++
} else {
    Write-LogFailure "Subtitles missing"
    $checksFailed++
}

# Check final video
if (Test-Path "$outputDir\final_output.mp4") {
    Write-LogSuccess "Final video created"
    $checksPassed++
} else {
    Write-LogFailure "Final video missing"
    $checksFailed++
}

# Check audio
if (Test-Path "$outputDir\audio\audio.wav") {
    Write-LogSuccess "Audio extracted"
    $checksPassed++
} else {
    Write-LogFailure "Audio missing"
    $checksFailed++
}

# Check device acceleration
$manifest = Get-Content "$outputDir\manifest.json" -Raw
if ($manifest -match '"device":\s*"cuda"') {
    Write-LogSuccess "CUDA acceleration confirmed"
    $checksPassed++
} elseif ($manifest -match '"device":\s*"cpu"') {
    Write-LogInfo "CPU mode detected"
} else {
    Write-LogWarn "Device acceleration not detected in manifest"
}

# Check pipeline status
if ($manifest -match '"status":\s*"completed"') {
    Write-LogSuccess "Pipeline completed successfully"
    $checksPassed++
} else {
    Write-LogFailure "Pipeline did not complete"
    $checksFailed++
}

Write-Host ""
Write-LogSection "Test T01 Summary"
Write-Host "Passed: $checksPassed" -ForegroundColor Green
Write-Host "Failed: $checksFailed" -ForegroundColor $(if ($checksFailed -eq 0) { "Green" } else { "Red" })

if ($checksFailed -eq 0) {
    Write-LogSuccess "Test T01 PASSED"
    exit 0
} else {
    Write-LogFailure "Test T01 FAILED"
    exit 1
}
