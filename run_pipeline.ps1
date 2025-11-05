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

# Logging functions
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [orchestrator] [$Level] $Message"
    
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

# Handle --list-stages
if ($ListStages) {
    Write-Log "Listing available pipeline stages..." "INFO"
    & python pipeline.py --list-stages
    exit $LASTEXITCODE
}

# Validate job parameter
if (-not $Job) {
    Write-Log "Job ID is required" "ERROR"
    Write-Host "Usage: .\run_pipeline.ps1 -Job <job_id> [-Stages <stage1>,<stage2>] [-NoResume]"
    Write-Host "       .\run_pipeline.ps1 -ListStages"
    exit 1
}

# Start
Write-Header "CP-WHISPERX-APP PIPELINE ORCHESTRATOR"
Write-Log "Job ID: $Job" "INFO"

# Validate Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Log "Python not found. Please install Python 3.9+" "ERROR"
    exit 1
}

# Build arguments
$pythonArgs = @("pipeline.py", "--job", $Job)

if ($Stages) {
    $pythonArgs += "--stages"
    $pythonArgs += $Stages
    Write-Log "Running specific stages: $($Stages -join ', ')" "INFO"
}

if ($NoResume) {
    $pythonArgs += "--no-resume"
    Write-Log "Resume: DISABLED (starting fresh)" "INFO"
} else {
    Write-Log "Resume: ENABLED (will continue from last checkpoint)" "INFO"
}

# Execute Python script
Write-Log "Executing: python $($pythonArgs -join ' ')" "INFO"
Write-Host ""

try {
    & python @pythonArgs
    
    if ($LASTEXITCODE -eq 0) {
        Write-Header "PIPELINE COMPLETED SUCCESSFULLY"
        Write-Log "Job $Job completed" "SUCCESS"
        Write-Host ""
        exit 0
    } else {
        Write-Header "PIPELINE FAILED"
        Write-Log "Pipeline execution failed with exit code $LASTEXITCODE" "ERROR"
        Write-Host ""
        exit $LASTEXITCODE
    }
} catch {
    Write-Log "Unexpected error: $_" "ERROR"
    exit 1
}
