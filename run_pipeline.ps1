# CP-WhisperX-App Pipeline Orchestrator
# PowerShell wrapper for pipeline.py with consistent logging

[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [string]$Job,
    
    [Parameter(Mandatory=$false)]
    [string[]]$Stages,
    
    [Parameter(Mandatory=$false)]
    [switch]$NoResume,
    
    [Parameter(Mandatory=$false)]
    [switch]$ListStages
)

$ErrorActionPreference = "Stop"

# Load common logging
. "$PSScriptRoot\scripts\common-logging.ps1"

# Handle --list-stages
if ($ListStages) {
    Write-LogInfo "Listing available pipeline stages..."
    & python scripts\pipeline.py --list-stages
    exit $LASTEXITCODE
}

# Validate job parameter
if (-not $Job) {
    Write-LogError "Job ID is required"
    Write-Host "Usage: .\run_pipeline.ps1 -Job <job-number> [-Stages <stage1>,<stage2>] [-NoResume]"
    Write-Host "       .\run_pipeline.ps1 -ListStages"
    exit 1
}

# Start
Write-LogSection "CP-WHISPERX-APP PIPELINE ORCHESTRATOR"
Write-LogInfo "Job ID: $Job"

# Validate Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-LogError "Python not found. Please install Python 3.9+"
    exit 1
}

# Build arguments
$pythonArgs = @("scripts\pipeline.py", "--job", $Job)

if ($Stages -and $Stages.Count -gt 0) {
    $pythonArgs += "--stages"
    $pythonArgs += $Stages
    Write-LogInfo "Running specific stages: $($Stages -join ', ')"
} else {
    Write-LogInfo "Running all stages"
}

if ($NoResume) {
    $pythonArgs += "--no-resume"
    Write-LogInfo "Resume: DISABLED (starting fresh)"
} else {
    Write-LogInfo "Resume: ENABLED (will continue from last checkpoint)"
}

# Execute Python script
Write-LogInfo "Executing: python $($pythonArgs -join ' ')"
Write-Host ""

try {
    & python @pythonArgs
    
    if ($LASTEXITCODE -eq 0) {
        Write-LogSection "PIPELINE COMPLETED SUCCESSFULLY"
        Write-LogSuccess "Job $Job completed"
        Write-Host ""
        exit 0
    } else {
        Write-LogSection "PIPELINE FAILED"
        Write-LogError "Pipeline execution failed with exit code $LASTEXITCODE"
        Write-Host ""
        exit $LASTEXITCODE
    }
} catch {
    Write-LogError "Unexpected error: $_"
    exit 1
}
