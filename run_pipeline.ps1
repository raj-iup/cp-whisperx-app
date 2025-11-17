# CP-WhisperX-App Pipeline Orchestrator (PowerShell)
# Windows wrapper for pipeline.py with CUDA optimization

[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [Alias("j")]
    [string]$Job,
    
    [Parameter(Mandatory=$false)]
    [Alias("s")]
    [string]$Stages,
    
    [Parameter(Mandatory=$false)]
    [switch]$NoResume,
    
    [Parameter(Mandatory=$false)]
    [switch]$ListStages,
    
    [Parameter(Mandatory=$false)]
    [Alias("h")]
    [switch]$Help
)

$ErrorActionPreference = "Stop"

# Logging functions
function Write-LogMessage {
    param(
        [string]$Level,
        [string]$Message
    )
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] [orchestrator] [$Level] $Message"
}

function Write-LogInfo { Write-LogMessage "INFO" $args[0] }
function Write-LogSuccess { Write-Host (Write-LogMessage "SUCCESS" $args[0]) -ForegroundColor Green }
function Write-LogWarning { Write-Host (Write-LogMessage "WARNING" $args[0]) -ForegroundColor Yellow }
function Write-LogError { Write-Host (Write-LogMessage "ERROR" $args[0]) -ForegroundColor Red }

function Write-Header {
    param([string]$Message)
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host $Message -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
}

# Help message
if ($Help) {
    Write-Host @"
Usage: .\run_pipeline.ps1 [OPTIONS] -Job <job_id>

Native Windows pipeline orchestrator for context-aware subtitle generation.
Optimized for CUDA acceleration with NVIDIA GPUs.

OPTIONS:
    -Job <job_id>           Job ID to process (required)
    -Stages <stages>        Run specific stages only (e.g., "demux asr mux")
    -NoResume               Start fresh, ignore previous progress
    -ListStages             List all available stages and exit
    -Help                   Show this help message

EXAMPLES:
    # Run complete pipeline
    .\run_pipeline.ps1 -Job 20251102-0001

    # Run specific stages
    .\run_pipeline.ps1 -Job 20251102-0001 -Stages "demux asr mux"

    # Start fresh (no resume)
    .\run_pipeline.ps1 -Job 20251102-0001 -NoResume

    # List available stages
    .\run_pipeline.ps1 -ListStages

"@
    exit 0
}

# Handle --list-stages
if ($ListStages) {
    Write-LogInfo "Listing available pipeline stages..."
    python scripts\pipeline.py --list-stages
    exit $LASTEXITCODE
}

# Validate job ID
if (-not $Job) {
    Write-LogError "Job ID is required"
    Write-Host ""
    Write-Host "Usage: .\run_pipeline.ps1 -Job <job_id>"
    Write-Host "Run '.\run_pipeline.ps1 -Help' for more information"
    exit 1
}

# Start
Write-Header "CP-WHISPERX-APP PIPELINE ORCHESTRATOR (CUDA)"
Write-LogInfo "Job ID: $Job"

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

# Build arguments
$pythonArgs = @("scripts\pipeline.py", "--job", $Job)

if ($Stages) {
    $pythonArgs += "--stages"
    $pythonArgs += $Stages
    Write-LogInfo "Running specific stages: $Stages"
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

& python $pythonArgs
$exitCode = $LASTEXITCODE

Write-Host ""
if ($exitCode -eq 0) {
    Write-Header "PIPELINE COMPLETED SUCCESSFULLY"
    Write-LogSuccess "Job $Job completed"
    Write-Host ""
    exit 0
} else {
    Write-Header "PIPELINE FAILED"
    Write-LogError "Pipeline execution failed with exit code $exitCode"
    Write-Host ""
    exit $exitCode
}
