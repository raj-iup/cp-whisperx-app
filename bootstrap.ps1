# ============================================================================
# CP-WhisperX-App Bootstrap - Multi-Environment Setup (Windows/PowerShell)
# ============================================================================
# Version: 2.0.0
# Date: 2025-12-03
# 
# PowerShell equivalent of bootstrap.sh for Windows environments
# Creates 8 specialized virtual environments for isolated dependency management
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
    if ($LogLevels.ContainsKey($Level)) {
        return $LogLevels[$Level]
    }
    return 1
}

$script:CurrentLogLevel = Get-LogLevelValue $LOG_LEVEL

function ShouldLog {
    param([string]$Level)
    $msgLevel = Get-LogLevelValue $Level
    return $msgLevel -ge $CurrentLogLevel
}

function Write-LogDebug {
    param([string]$Message)
    if (ShouldLog "DEBUG") {
        Write-Host "[DEBUG] $Message" -ForegroundColor Cyan
    }
}

function Write-LogInfo {
    param([string]$Message)
    if (ShouldLog "INFO") {
        Write-Host "[INFO] $Message" -ForegroundColor Blue
    }
}

function Write-LogWarn {
    param([string]$Message)
    if (ShouldLog "WARN") {
        Write-Warning "[WARN] $Message"
    }
}

function Write-LogError {
    param([string]$Message)
    if (ShouldLog "ERROR") {
        Write-Host "[ERROR] $Message" -ForegroundColor Red
    }
}

function Write-LogCritical {
    param([string]$Message)
    Write-Host "[CRITICAL] $Message" -ForegroundColor Red -BackgroundColor Yellow
}

function Write-LogSuccess {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

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

$PROJECT_ROOT = $PSScriptRoot
$VENV_BASE = Join-Path $PROJECT_ROOT "venv"
$REQUIREMENTS_DIR = Join-Path $PROJECT_ROOT "requirements"

# Virtual environment names
$VENV_NAMES = @(
    "common", "whisperx", "mlx", "pyannote", 
    "demucs", "indictrans2", "nllb", "llm"
)

# ═══════════════════════════════════════════════════════════════════════════
# VALIDATION
# ═══════════════════════════════════════════════════════════════════════════

Write-LogSection "CP-WHISPERX-APP BOOTSTRAP - WINDOWS"

# Check Python 3.11+
try {
    $pythonVersion = python --version 2>&1 | Select-String -Pattern "Python (\d+)\.(\d+)"
    if ($pythonVersion) {
        $major = [int]$pythonVersion.Matches.Groups[1].Value
        $minor = [int]$pythonVersion.Matches.Groups[2].Value
        
        if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 11)) {
            Write-LogCritical "Python 3.11+ required (found $major.$minor)"
            exit 1
        }
        
        Write-LogInfo "Python version: $major.$minor"
    }
} catch {
    Write-LogCritical "Python not found. Please install Python 3.11+"
    exit 1
}

# Check pip
try {
    python -m pip --version | Out-Null
    Write-LogInfo "pip is available"
} catch {
    Write-LogCritical "pip not found. Please install pip"
    exit 1
}

# Create venv base directory
if (-not (Test-Path $VENV_BASE)) {
    Write-LogInfo "Creating venv directory: $VENV_BASE"
    New-Item -ItemType Directory -Path $VENV_BASE -Force | Out-Null
}

# ═══════════════════════════════════════════════════════════════════════════
# VIRTUAL ENVIRONMENT CREATION
# ═══════════════════════════════════════════════════════════════════════════

function Create-VirtualEnv {
    param(
        [string]$Name,
        [string]$RequirementsFile
    )
    
    $venvPath = Join-Path $VENV_BASE $Name
    $requirementsPath = Join-Path $REQUIREMENTS_DIR $RequirementsFile
    
    Write-LogSection "Environment: $Name"
    
    # Check if already exists
    if (Test-Path $venvPath) {
        Write-LogWarn "Environment already exists: $venvPath"
        Write-LogInfo "Skipping creation (delete manually to recreate)"
        return
    }
    
    # Create virtual environment
    Write-LogInfo "Creating virtual environment: $venvPath"
    python -m venv $venvPath
    
    if (-not $?) {
        Write-LogError "Failed to create virtual environment: $Name"
        return
    }
    
    # Activate and install dependencies
    $activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
    
    if (Test-Path $requirementsPath) {
        Write-LogInfo "Installing dependencies from: $RequirementsFile"
        
        & $activateScript
        python -m pip install --upgrade pip setuptools wheel
        python -m pip install -r $requirementsPath
        deactivate
        
        if ($?) {
            Write-LogSuccess "Environment created: $Name"
        } else {
            Write-LogError "Failed to install dependencies for: $Name"
        }
    } else {
        Write-LogWarn "No requirements file found: $requirementsPath"
        Write-LogInfo "Virtual environment created but no dependencies installed"
    }
}

# Create all virtual environments
foreach ($venvName in $VENV_NAMES) {
    $reqFile = "requirements-$venvName.txt"
    Create-VirtualEnv -Name $venvName -RequirementsFile $reqFile
}

# ═══════════════════════════════════════════════════════════════════════════
# POST-INSTALLATION TASKS
# ═══════════════════════════════════════════════════════════════════════════

Write-LogSection "Post-Installation"

# Create necessary directories
$directories = @("in", "out", "logs", "config")
foreach ($dir in $directories) {
    $dirPath = Join-Path $PROJECT_ROOT $dir
    if (-not (Test-Path $dirPath)) {
        Write-LogInfo "Creating directory: $dir"
        New-Item -ItemType Directory -Path $dirPath -Force | Out-Null
    }
}

# Check for .env.pipeline
$envFile = Join-Path $PROJECT_ROOT "config\.env.pipeline"
if (-not (Test-Path $envFile)) {
    Write-LogWarn "Configuration file not found: config\.env.pipeline"
    Write-LogInfo "Copy from config\.env.pipeline.example if available"
}

# ═══════════════════════════════════════════════════════════════════════════
# COMPLETION
# ═══════════════════════════════════════════════════════════════════════════

Write-LogSection "Bootstrap Complete"

Write-LogSuccess "All virtual environments created"
Write-LogInfo ""
Write-LogInfo "Next steps:"
Write-LogInfo "  1. Configure: Copy config\.env.pipeline.example to config\.env.pipeline"
Write-LogInfo "  2. Edit configuration: Edit config\.env.pipeline"
Write-LogInfo "  3. Prepare job: .\prepare-job.ps1 -InputFile path\to\video.mp4"
Write-LogInfo "  4. Run pipeline: .\run-pipeline.ps1 -JobId job-YYYYMMDD-user-NNNN"
Write-LogInfo ""
Write-LogInfo "For help: .\prepare-job.ps1 -Help"

exit 0
