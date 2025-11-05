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

# Logging functions
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [prepare-job] [$Level] $Message"
    
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

# Start
Write-Header "CP-WHISPERX-APP JOB PREPARATION"
Write-Log "Starting job preparation..."

# Validate Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Log "Python not found. Please install Python 3.9+" "ERROR"
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
    Write-Log "Workflow: TRANSCRIBE (simplified pipeline)" "INFO"
} elseif ($SubtitleGen) {
    $pythonArgs += "--subtitle-gen"
    Write-Log "Workflow: SUBTITLE-GEN (full pipeline)" "INFO"
}

if ($Native) {
    $pythonArgs += "--native"
    Write-Log "Native mode: ENABLED" "INFO"
}

# Execute Python script
Write-Log "Executing: python $($pythonArgs -join ' ')" "INFO"

try {
    & python @pythonArgs
    
    if ($LASTEXITCODE -eq 0) {
        Write-Log "Job preparation completed successfully" "SUCCESS"
        Write-Header "NEXT STEPS"
        Write-Host "Run pipeline with: .\run_pipeline.ps1 -Job <job_id>"
        Write-Host ""
        exit 0
    } else {
        Write-Log "Job preparation failed with exit code $LASTEXITCODE" "ERROR"
        exit $LASTEXITCODE
    }
} catch {
    Write-Log "Unexpected error: $_" "ERROR"
    exit 1
}
