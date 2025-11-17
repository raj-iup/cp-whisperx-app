# CP-WhisperX-App Pipeline Resume Script (PowerShell)
# Resume pipeline execution with consistent logging
# Windows - CUDA optimized

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$JobId,
    
    [Parameter(Mandatory=$false)]
    [switch]$Help
)

$ErrorActionPreference = "Stop"

# Load common logging
. "$PSScriptRoot\scripts\common-logging.ps1"

# Show help
if ($Help) {
    Write-Host @"
Usage: .\resume-pipeline.ps1 <job_id>

Resume a failed or interrupted pipeline job (Windows - CUDA optimized)

ARGUMENTS:
  <job_id>              Job ID to resume (required)

EXAMPLES:
  # Resume a specific job
  .\resume-pipeline.ps1 20251102-0002

"@
    exit 0
}

# Validate job ID
if (-not $JobId) {
    Write-LogError "Job ID is required"
    Write-Host "Usage: .\resume-pipeline.ps1 <job_id>"
    Write-Host "Example: .\resume-pipeline.ps1 20251102-0002"
    exit 1
}

Write-LogSection "CP-WHISPERX-APP PIPELINE RESUME (CUDA)"
Write-LogInfo "Resuming job: $JobId"

# Set up environment
$projectRoot = $PSScriptRoot

# Activate virtual environment if it exists
$venvActivate = Join-Path $projectRoot ".bollyenv\Scripts\Activate.ps1"
if (Test-Path $venvActivate) {
    . $venvActivate
    Write-LogInfo "Activated virtual environment: .bollyenv"
} else {
    Write-LogWarning "Virtual environment not found. Run .\scripts\bootstrap.ps1 first"
}

# Set cache directories (consistent with bootstrap)
$env:TORCH_HOME = Join-Path $projectRoot ".cache\torch"
$env:HF_HOME = Join-Path $projectRoot ".cache\huggingface"

# Validate Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-LogError "Python not found. Please install Python 3.9+"
    exit 1
}

# Execute pipeline with resume enabled (default behavior)
Write-LogInfo "Executing: python scripts\pipeline.py --job $JobId"
Write-Host ""

& python scripts\pipeline.py --job $JobId
$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-LogSection "PIPELINE RESUMED SUCCESSFULLY"
    Write-LogSuccess "Job $JobId completed"
    Write-Host ""
    exit 0
} else {
    Write-LogSection "PIPELINE RESUME FAILED"
    Write-LogError "Pipeline execution failed with exit code $exitCode"
    Write-Host ""
    exit 1
}
