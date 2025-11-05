# CP-WhisperX-App Job Preparation Script
# PowerShell wrapper for prepare-job.py with consistent logging

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$InputMedia,
    
    [Parameter(Mandatory=$false)]
    [string]$StartTime,
    
    [Parameter(Mandatory=$false)]
    [string]$EndTime,
    
    [Parameter(Mandatory=$false)]
    [switch]$Transcribe,
    
    [Parameter(Mandatory=$false)]
    [switch]$SubtitleGen,
    
    [Parameter(Mandatory=$false)]
    [switch]$Native
)

$ErrorActionPreference = "Stop"

# Load common logging
. "$PSScriptRoot\scripts\common-logging.ps1"

# Start
Write-LogSection "CP-WHISPERX-APP JOB PREPARATION"
Write-LogInfo "Starting job preparation..."

# Validate Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-LogError "Python not found. Please install Python 3.9+"
    exit 1
}

# Build arguments
$pythonArgs = @("prepare-job.py", $InputMedia)

if ($StartTime) {
    $pythonArgs += "--start-time", $StartTime
}

if ($EndTime) {
    $pythonArgs += "--end-time", $EndTime
}

if ($Transcribe) {
    $pythonArgs += "--transcribe"
    Write-LogInfo "Workflow: TRANSCRIBE (simplified pipeline)"
} elseif ($SubtitleGen) {
    $pythonArgs += "--subtitle-gen"
    Write-LogInfo "Workflow: SUBTITLE-GEN (full pipeline)"
}

if ($Native) {
    $pythonArgs += "--native"
    Write-LogInfo "Native mode: ENABLED"
}

# Execute Python script
Write-LogInfo "Executing: python $($pythonArgs -join ' ')"

try {
    & python @pythonArgs
    
    if ($LASTEXITCODE -eq 0) {
        Write-LogSuccess "Job preparation completed successfully"
        Write-LogSection "NEXT STEPS"
        Write-Host "Run pipeline with: .\run_pipeline.ps1 -Job <job_id>"
        Write-Host ""
        exit 0
    } else {
        Write-LogError "Job preparation failed with exit code $LASTEXITCODE"
        exit $LASTEXITCODE
    }
} catch {
    Write-LogError "Unexpected error: $_"
    exit 1
}
