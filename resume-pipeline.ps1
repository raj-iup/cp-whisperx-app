# CP-WhisperX-App Pipeline Resume Script
# Resume pipeline execution with consistent logging

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string]$Job
)

$ErrorActionPreference = "Stop"

# Load common logging
. "$PSScriptRoot\scripts\common-logging.ps1"

# Start
Write-LogSection "CP-WHISPERX-APP PIPELINE RESUME"
Write-LogInfo "Resuming job: $Job"

# Validate Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-LogError "Python not found. Please install Python 3.9+"
    exit 1
}

# Execute pipeline with resume enabled (default behavior)
Write-LogInfo "Executing: python pipeline.py --job $Job"
Write-Host ""

try {
    & python pipeline.py --job $Job
    
    if ($LASTEXITCODE -eq 0) {
        Write-LogSection "PIPELINE RESUMED SUCCESSFULLY"
        Write-LogSuccess "Job $Job completed"
        Write-Host ""
        exit 0
    } else {
        Write-LogSection "PIPELINE RESUME FAILED"
        Write-LogError "Pipeline execution failed with exit code $LASTEXITCODE"
        Write-Host ""
        exit $LASTEXITCODE
    }
} catch {
    Write-LogError "Unexpected error: $_"
    exit 1
}
