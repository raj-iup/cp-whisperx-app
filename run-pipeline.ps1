# ============================================================================
# CP-WhisperX-App Pipeline Execution (Windows/PowerShell)
# ============================================================================
# Version: 2.0.0
# Date: 2025-12-03
#
# Executes the complete pipeline for a prepared job.
# PowerShell equivalent of run-pipeline.sh for Windows environments
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
$PIPELINE_SCRIPT = Join-Path $SCRIPTS_DIR "run-pipeline.py"

# ═══════════════════════════════════════════════════════════════════════════
# HELP
# ═══════════════════════════════════════════════════════════════════════════

function Show-Usage {
    @"
Usage: .\run-pipeline.ps1 [OPTIONS]

Execute the pipeline for a prepared job

REQUIRED OPTIONS:
  -JobId <job-id>              Job ID to execute (e.g., job-20251203-user-0001)

OPTIONAL OPTIONS:
  -Resume                      Resume from last completed stage
  -LogLevel <level>            Log level: DEBUG|INFO|WARN|ERROR|CRITICAL
  -Debug                       Enable debug mode (same as -LogLevel DEBUG)
  -Help                        Show this help message

PIPELINE STAGES:
  01. Demux                    Audio extraction from video
  02. TMDB                     Movie metadata enrichment (optional)
  03. Glossary Load            Load glossary files (optional)
  04. ASR                      Speech recognition (WhisperX/MLX)
  05. NER                      Named entity recognition (optional)
  06. Lyrics Detection         Detect lyrics sections (optional)
  07. Hallucination Removal    Remove ASR hallucinations (optional)
  08. Translation              IndicTrans2/NLLB translation
  09. Subtitle Generation      SRT/VTT subtitle creation
  10. Mux                      Embed subtitles in video

EXAMPLES:
  # Run complete pipeline
  .\run-pipeline.ps1 -JobId job-20251203-user-0001

  # Resume from failure
  .\run-pipeline.ps1 -JobId job-20251203-user-0001 -Resume

  # Debug mode
  .\run-pipeline.ps1 -JobId job-20251203-user-0001 -Debug

  # Monitor logs in real-time (separate window)
  .\run-pipeline.ps1 -JobId job-20251203-user-0001
  Get-Content out\2025\12\03\user\1\logs\pipeline.log -Wait

OUTPUT LOCATIONS:
  Job directory:    out\YYYY\MM\DD\user\N\
  Subtitles:        out\...\subtitles\*.srt
  Transcripts:      out\...\transcripts\*.txt
  Logs:             out\...\logs\*.log

ENVIRONMENT REQUIREMENTS:
  Must run .\bootstrap.ps1 first to create virtual environments

"@
}

# ═══════════════════════════════════════════════════════════════════════════
# PARAMETER PARSING
# ═══════════════════════════════════════════════════════════════════════════

param(
    [Parameter(Mandatory=$false)]
    [string]$JobId,
    
    [Parameter(Mandatory=$false)]
    [switch]$Resume,
    
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

Write-LogSection "CP-WHISPERX-APP PIPELINE EXECUTION"

# Validate job ID
if (-not $JobId) {
    Write-LogCritical "Job ID required. Use: -JobId <job-id>"
    Show-Usage
    exit 1
}

# Check if common venv exists
if (-not (Test-Path $COMMON_VENV)) {
    Write-LogCritical "Environment not found: $COMMON_VENV"
    Write-LogError "Run bootstrap first: .\bootstrap.ps1"
    exit 1
}

# Check if pipeline script exists
if (-not (Test-Path $PIPELINE_SCRIPT)) {
    Write-LogCritical "Pipeline script not found: $PIPELINE_SCRIPT"
    exit 1
}

# ═══════════════════════════════════════════════════════════════════════════
# JOB DIRECTORY RESOLUTION
# ═══════════════════════════════════════════════════════════════════════════

# Parse job ID: job-YYYYMMDD-user-NNNN
if ($JobId -match '^job-(\d{8})-([^-]+)-(\d+)$') {
    $dateStr = $Matches[1]
    $user = $Matches[2]
    $numStr = $Matches[3]
    
    $year = $dateStr.Substring(0, 4)
    $month = $dateStr.Substring(4, 2)
    $day = $dateStr.Substring(6, 2)
    
    # Remove leading zeros from number
    $num = [int]$numStr
    
    $jobDir = Join-Path $PROJECT_ROOT "out\$year\$month\$day\$user\$num"
} else {
    Write-LogCritical "Invalid job ID format: $JobId"
    Write-LogError "Expected format: job-YYYYMMDD-user-NNNN"
    exit 1
}

# Validate job directory exists
if (-not (Test-Path $jobDir)) {
    Write-LogCritical "Job directory not found: $jobDir"
    Write-LogError "Run prepare-job.ps1 first"
    exit 1
}

Write-LogDebug "Job directory: $jobDir"

# Check for job.json
$jobConfigFile = Join-Path $jobDir "job.json"
if (-not (Test-Path $jobConfigFile)) {
    Write-LogCritical "Job configuration not found: $jobConfigFile"
    exit 1
}

# Read log level from job.json if not specified
if (-not $LogLevel -and -not $Debug) {
    try {
        $jobConfig = Get-Content $jobConfigFile | ConvertFrom-Json
        if ($jobConfig.log_level) {
            $script:LOG_LEVEL = $jobConfig.log_level
            $script:CurrentLogLevel = Get-LogLevelValue $LOG_LEVEL
            Write-LogDebug "Using log level from job.json: $($jobConfig.log_level)"
        }
    } catch {
        Write-LogWarn "Failed to read log level from job.json"
    }
}

# ═══════════════════════════════════════════════════════════════════════════
# EXECUTION
# ═══════════════════════════════════════════════════════════════════════════

Write-LogInfo "Job ID: $JobId"
Write-LogInfo "Job directory: $jobDir"
Write-LogInfo "Log level: $LOG_LEVEL"

# Build Python arguments
$pythonArgs = @("--job-dir", $jobDir)

if ($Resume) {
    $pythonArgs += "--resume"
}

Write-LogDebug "Python script: $PIPELINE_SCRIPT"
Write-LogDebug "Arguments: $($pythonArgs -join ' ')"

# Set environment variables
$env:VIRTUAL_ENV = $COMMON_VENV
$env:PATH = "$COMMON_VENV\Scripts;$env:PATH"
$env:PYTHONPATH = if ($env:PYTHONPATH) { "$PROJECT_ROOT;$env:PYTHONPATH" } else { $PROJECT_ROOT }

Write-LogInfo "Starting pipeline execution..."
Write-Host ""

# Run pipeline script
$pythonExe = Join-Path $COMMON_VENV "Scripts\python.exe"

try {
    & $pythonExe $PIPELINE_SCRIPT @pythonArgs
    
    if ($LASTEXITCODE -eq 0) {
        Write-LogSuccess "Pipeline execution completed successfully"
        exit 0
    } else {
        Write-LogError "Pipeline execution failed with exit code: $LASTEXITCODE"
        exit $LASTEXITCODE
    }
} catch {
    Write-LogCritical "Failed to run pipeline: $_"
    exit 1
}
