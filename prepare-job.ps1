# ============================================================================
# CP-WhisperX-App Job Preparation (Windows/PowerShell)
# ============================================================================
# Version: 2.0.0
# Date: 2025-12-03
#
# Creates job directory structure and configuration for pipeline execution.
# PowerShell equivalent of prepare-job.sh for Windows environments
# ============================================================================

#Requires -Version 5.1

# Enable strict mode for better error handling
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ═══════════════════════════════════════════════════════════════════════════
# COMMON LOGGING FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

$script:LOG_LEVEL = if ($env:LOG_LEVEL) { $env:LOG_LEVEL } else { "INFO" }

$script:LogLevels = @{
    "DEBUG" = 0; "INFO" = 1; "WARN" = 2; "ERROR" = 3; "CRITICAL" = 4
}

function Get-LogLevelValue {
    param([string]$Level)
    if ($LogLevels.ContainsKey($Level)) { return $LogLevels[$Level] }
    return 1
}

$script:CurrentLogLevel = Get-LogLevelValue $LOG_LEVEL

function ShouldLog {
    param([string]$Level)
    return (Get-LogLevelValue $Level) -ge $CurrentLogLevel
}

function Write-LogDebug { param([string]$Message) if (ShouldLog "DEBUG") { Write-Host "[DEBUG] $Message" -ForegroundColor Cyan } }
function Write-LogInfo { param([string]$Message) if (ShouldLog "INFO") { Write-Host "[INFO] $Message" -ForegroundColor Blue } }
function Write-LogWarn { param([string]$Message) if (ShouldLog "WARN") { Write-Warning "[WARN] $Message" } }
function Write-LogError { param([string]$Message) if (ShouldLog "ERROR") { Write-Host "[ERROR] $Message" -ForegroundColor Red } }
function Write-LogCritical { param([string]$Message) Write-Host "[CRITICAL] $Message" -ForegroundColor Red -BackgroundColor Yellow }
function Write-LogSuccess { param([string]$Message) Write-Host "✓ $Message" -ForegroundColor Green }

function Write-LogSection {
    param([string]$Message)
    Write-Host ""
    Write-Host ("━" * 80) -ForegroundColor Cyan
    Write-Host $Message -ForegroundColor Cyan
    Write-Host ("━" * 80) -ForegroundColor Cyan
}

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

$PROJECT_ROOT = Split-Path -Parent $PSScriptRoot
$SCRIPTS_DIR = Join-Path $PROJECT_ROOT "scripts"
$COMMON_VENV = Join-Path $PROJECT_ROOT "venv\common"
$PREPARE_JOB_SCRIPT = Join-Path $SCRIPTS_DIR "prepare_job.py"

# ═══════════════════════════════════════════════════════════════════════════
# HELP
# ═══════════════════════════════════════════════════════════════════════════

function Show-Usage {
    @"
Usage: .\prepare-job.ps1 [OPTIONS]

Prepare a new job for pipeline execution

REQUIRED OPTIONS:
  -InputFile <path>            Input video/audio file

OPTIONAL OPTIONS:
  -JobName <name>              Custom job name (default: derived from filename)
  -User <username>             User identifier (default: current user)
  -LogLevel <level>            Log level: DEBUG|INFO|WARN|ERROR|CRITICAL
  -Debug                       Enable debug mode (same as -LogLevel DEBUG)
  -Help                        Show this help message

OUTPUT:
  Creates job directory in: out/YYYY/MM/DD/user/N/
  Returns job ID: job-YYYYMMDD-user-NNNN

EXAMPLES:
  # Basic usage
  .\prepare-job.ps1 -InputFile C:\Videos\movie.mp4

  # Custom job name
  .\prepare-job.ps1 -InputFile C:\Videos\movie.mp4 -JobName "movie_subtitle"

  # Custom user
  .\prepare-job.ps1 -InputFile C:\Videos\movie.mp4 -User "john"

  # Debug mode
  .\prepare-job.ps1 -InputFile C:\Videos\movie.mp4 -Debug

NEXT STEPS:
  After preparing job, run pipeline:
  .\run-pipeline.ps1 -JobId <job-id>

"@
}

# ═══════════════════════════════════════════════════════════════════════════
# PARAMETER PARSING
# ═══════════════════════════════════════════════════════════════════════════

param(
    [Parameter(Mandatory=$false)]
    [string]$InputFile,
    
    [Parameter(Mandatory=$false)]
    [string]$JobName,
    
    [Parameter(Mandatory=$false)]
    [string]$User,
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("DEBUG", "INFO", "WARN", "ERROR", "CRITICAL")]
    [string]$LogLevel,
    
    [Parameter(Mandatory=$false)]
    [switch]$Debug,
    
    [Parameter(Mandatory=$false)]
    [switch]$Help
)

if ($Help) {
    Show-Usage
    exit 0
}

# Set log level
if ($Debug) {
    $script:LOG_LEVEL = "DEBUG"
    $script:CurrentLogLevel = Get-LogLevelValue "DEBUG"
} elseif ($LogLevel) {
    $script:LOG_LEVEL = $LogLevel
    $script:CurrentLogLevel = Get-LogLevelValue $LogLevel
}

# ═══════════════════════════════════════════════════════════════════════════
# VALIDATION
# ═══════════════════════════════════════════════════════════════════════════

Write-LogSection "CP-WHISPERX-APP JOB PREPARATION"

# Validate input file
if (-not $InputFile) {
    Write-LogCritical "Input file required. Use: -InputFile <path>"
    Show-Usage
    exit 1
}

if (-not (Test-Path $InputFile)) {
    Write-LogCritical "Input file not found: $InputFile"
    exit 1
}

$InputFile = Resolve-Path $InputFile

Write-LogInfo "Input file: $InputFile"

# Check if common venv exists
if (-not (Test-Path $COMMON_VENV)) {
    Write-LogCritical "Environment not found: $COMMON_VENV"
    Write-LogError "Run bootstrap first: .\bootstrap.ps1"
    exit 1
}

# Check if prepare_job.py exists
if (-not (Test-Path $PREPARE_JOB_SCRIPT)) {
    Write-LogCritical "Prepare job script not found: $PREPARE_JOB_SCRIPT"
    exit 1
}

# ═══════════════════════════════════════════════════════════════════════════
# EXECUTION
# ═══════════════════════════════════════════════════════════════════════════

# Build Python arguments
$pythonArgs = @("--input-file", $InputFile)

if ($JobName) {
    $pythonArgs += @("--job-name", $JobName)
}

if ($User) {
    $pythonArgs += @("--user", $User)
}

if ($LogLevel) {
    $pythonArgs += @("--log-level", $LogLevel)
} elseif ($Debug) {
    $pythonArgs += @("--log-level", "DEBUG")
}

Write-LogDebug "Python script: $PREPARE_JOB_SCRIPT"
Write-LogDebug "Arguments: $($pythonArgs -join ' ')"

# Set environment variables
$env:VIRTUAL_ENV = $COMMON_VENV
$env:PATH = "$COMMON_VENV\Scripts;$env:PATH"
$env:PYTHONPATH = if ($env:PYTHONPATH) { "$PROJECT_ROOT;$env:PYTHONPATH" } else { $PROJECT_ROOT }

Write-LogInfo "Preparing job..."
Write-Host ""

# Run prepare_job.py
$pythonExe = Join-Path $COMMON_VENV "Scripts\python.exe"

try {
    & $pythonExe $PREPARE_JOB_SCRIPT @pythonArgs
    
    if ($LASTEXITCODE -eq 0) {
        Write-LogSuccess "Job prepared successfully"
        exit 0
    } else {
        Write-LogError "Job preparation failed with exit code: $LASTEXITCODE"
        exit $LASTEXITCODE
    }
} catch {
    Write-LogCritical "Failed to run prepare_job.py: $_"
    exit 1
}
