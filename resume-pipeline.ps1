# CP-WhisperX-App Pipeline Resume Script
# Resume pipeline execution with consistent logging

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string]$Job
)

$ErrorActionPreference = "Stop"

# Logging functions
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [resume-pipeline] [$Level] $Message"
    
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
Write-Header "CP-WHISPERX-APP PIPELINE RESUME"
Write-Log "Resuming job: $Job" "INFO"

# Validate Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Log "Python not found. Please install Python 3.9+" "ERROR"
    exit 1
}

# Execute pipeline with resume enabled (default behavior)
Write-Log "Executing: python pipeline.py --job $Job" "INFO"
Write-Host ""

try {
    & python pipeline.py --job $Job
    
    if ($LASTEXITCODE -eq 0) {
        Write-Header "PIPELINE RESUMED SUCCESSFULLY"
        Write-Log "Job $Job completed" "SUCCESS"
        Write-Host ""
        exit 0
    } else {
        Write-Header "PIPELINE RESUME FAILED"
        Write-Log "Pipeline execution failed with exit code $LASTEXITCODE" "ERROR"
        Write-Host ""
        exit $LASTEXITCODE
    }
} catch {
    Write-Log "Unexpected error: $_" "ERROR"
    exit 1
}
