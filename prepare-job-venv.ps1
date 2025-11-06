# ============================================================================
# ⚠️  DEPRECATION NOTICE ⚠️
# ============================================================================
# This script is DEPRECATED as of Phase 1 consolidation.
# 
# The prepare-job-venv wrapper is no longer needed because:
# - Bootstrap now creates a permanent .bollyenv/ environment
# - No temporary venv creation required
# - Hardware detection is cached
# - 80-90% faster execution
#
# Please use the simplified wrapper instead:
#   .\prepare-job.ps1 <input_media> [options]
#
# This script will be removed in a future version.
# ============================================================================

# CP-WhisperX-App Job Preparation with Virtual Environment (DEPRECATED)
# Creates isolated Python venv, installs PyTorch with GPU support, runs prepare-job.py
# Automatically detects CUDA/MPS and falls back to CPU if needed

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
    [switch]$KeepVenv
)

$ErrorActionPreference = "Stop"

# Display deprecation warning
Write-Host ""
Write-Host "⚠️  DEPRECATION WARNING" -ForegroundColor Yellow
Write-Host "="*70 -ForegroundColor Yellow
Write-Host "This script (prepare-job-venv.ps1) is deprecated." -ForegroundColor Yellow
Write-Host ""
Write-Host "Please use the simplified wrapper instead:" -ForegroundColor White
Write-Host "  .\prepare-job.ps1 <input_media> [options]" -ForegroundColor Cyan
Write-Host ""
Write-Host "Benefits of the new script:" -ForegroundColor White
Write-Host "  • 80-90% faster (5-30 sec vs 1-2 min)" -ForegroundColor Gray
Write-Host "  • Uses existing .bollyenv environment" -ForegroundColor Gray
Write-Host "  • No temporary venv creation" -ForegroundColor Gray
Write-Host "  • Cached hardware detection" -ForegroundColor Gray
Write-Host "="*70 -ForegroundColor Yellow
Write-Host ""
Write-Host "Continuing with old script for backward compatibility..." -ForegroundColor Gray
Write-Host ""
Start-Sleep -Seconds 3

# Load common logging
. "$PSScriptRoot\scripts\common-logging.ps1"

# Start
Write-LogSection "CP-WHISPERX-APP JOB PREPARATION (VENV MODE)"
Write-LogInfo "Creating isolated Python environment for job preparation..."
Write-Host ""

# Validate input media
if (-not (Test-Path $InputMedia)) {
    Write-LogError "Input media not found: $InputMedia"
    exit 1
}

# Validate Python 3.9+
Write-LogInfo "Validating Python installation..."
$pythonCmd = $null
foreach ($cmd in @("python", "python3", "py")) {
    if (Get-Command $cmd -ErrorAction SilentlyContinue) {
        $pythonCmd = $cmd
        break
    }
}

if (-not $pythonCmd) {
    Write-LogError "Python not found. Please install Python 3.9+"
    exit 1
}

$pythonVersion = & $pythonCmd --version 2>&1
Write-LogInfo "Found: $pythonVersion"

# Extract version number
if ($pythonVersion -match "Python (\d+)\.(\d+)") {
    $major = [int]$matches[1]
    $minor = [int]$matches[2]
    
    if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 9)) {
        Write-LogError "Python 3.9+ required. Found: Python $major.$minor"
        exit 1
    }
}

Write-LogSuccess "Python version check passed"
Write-Host ""

# Create temporary virtual environment
$venvPath = Join-Path $PSScriptRoot ".venv-prepare-job-temp"
Write-LogSection "CREATING VIRTUAL ENVIRONMENT"
Write-LogInfo "Location: $venvPath"

if (Test-Path $venvPath) {
    Write-LogInfo "Removing existing venv..."
    Remove-Item -Path $venvPath -Recurse -Force
}

Write-LogInfo "Creating new venv..."
& $pythonCmd -m venv $venvPath

if ($LASTEXITCODE -ne 0) {
    Write-LogError "Failed to create virtual environment"
    exit 1
}

Write-LogSuccess "Virtual environment created"
Write-Host ""

# Activate venv
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
if (-not (Test-Path $activateScript)) {
    Write-LogError "Activate script not found: $activateScript"
    exit 1
}

Write-LogInfo "Activating virtual environment..."
. $activateScript

# Verify activation
$venvPython = Join-Path $venvPath "Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-LogError "Virtual environment Python not found"
    exit 1
}

Write-LogSuccess "Virtual environment activated"
Write-Host ""

# Detect GPU/CUDA
Write-LogSection "HARDWARE DETECTION"
Write-LogInfo "Detecting available acceleration hardware..."

$deviceMode = "cpu"
$cudaVersion = $null

# Check for NVIDIA GPU
if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
    Write-LogInfo "NVIDIA GPU detected (nvidia-smi available)"
    
    # Get CUDA version from nvidia-smi
    try {
        $nvidiaSmiOutput = nvidia-smi 2>&1 | Out-String
        if ($nvidiaSmiOutput -match "CUDA Version: (\d+)\.(\d+)") {
            $cudaMajor = $matches[1]
            $cudaMinor = $matches[2]
            $cudaVersion = "$cudaMajor.$cudaMinor"
            Write-LogInfo "CUDA Version: $cudaVersion"
            $deviceMode = "cuda"
        }
    } catch {
        Write-LogWarn "Failed to detect CUDA version from nvidia-smi"
    }
} else {
    Write-LogInfo "No NVIDIA GPU detected (nvidia-smi not found)"
}

# Check for Apple Silicon (MPS) on macOS
if ($IsWindows -eq $false -and $IsMacOS) {
    $systemInfo = & sysctl -n machdep.cpu.brand_string 2>&1
    if ($systemInfo -match "Apple") {
        Write-LogInfo "Apple Silicon detected"
        $deviceMode = "mps"
    }
}

Write-LogSuccess "Device mode: $($deviceMode.ToUpper())"
Write-Host ""

# Install PyTorch with appropriate backend
Write-LogSection "INSTALLING PYTORCH"

try {
    switch ($deviceMode) {
        "cuda" {
            Write-LogInfo "Installing PyTorch with CUDA $cudaVersion support..."
            
            # Map CUDA version to PyTorch wheel
            $torchIndex = switch ($cudaMajor) {
                "12" { 
                    if ([int]$cudaMinor -ge 6) {
                        "https://download.pytorch.org/whl/cu126"
                    } elseif ([int]$cudaMinor -ge 4) {
                        "https://download.pytorch.org/whl/cu124"
                    } else {
                        "https://download.pytorch.org/whl/cu121"
                    }
                }
                "11" {
                    "https://download.pytorch.org/whl/cu118"
                }
                default {
                    Write-LogWarn "CUDA version $cudaVersion not recognized, using CUDA 12.1"
                    "https://download.pytorch.org/whl/cu121"
                }
            }
            
            Write-LogInfo "PyTorch index: $torchIndex"
            & $venvPython -m pip install --quiet torch torchvision torchaudio --index-url $torchIndex
            
            if ($LASTEXITCODE -ne 0) {
                Write-LogWarn "Failed to install CUDA PyTorch, falling back to CPU"
                $deviceMode = "cpu"
                & $venvPython -m pip install --quiet torch torchvision torchaudio
            }
        }
        
        "mps" {
            Write-LogInfo "Installing PyTorch with MPS support (macOS)..."
            & $venvPython -m pip install --quiet torch torchvision torchaudio
            
            if ($LASTEXITCODE -ne 0) {
                Write-LogWarn "Failed to install MPS PyTorch, falling back to CPU"
                $deviceMode = "cpu"
            }
        }
        
        "cpu" {
            Write-LogInfo "Installing PyTorch (CPU-only mode)..."
            & $venvPython -m pip install --quiet torch torchvision torchaudio
        }
    }
    
    if ($LASTEXITCODE -ne 0) {
        Write-LogError "Failed to install PyTorch"
        throw "PyTorch installation failed"
    }
    
    Write-LogSuccess "PyTorch installed successfully"
} catch {
    Write-LogError "PyTorch installation error: $_"
    Write-LogInfo "Cleaning up virtual environment..."
    if (Test-Path $venvPath) {
        Remove-Item -Path $venvPath -Recurse -Force
    }
    exit 1
}

Write-Host ""

# Verify PyTorch installation and GPU detection
Write-LogSection "VERIFYING PYTORCH INSTALLATION"
Write-LogInfo "Testing PyTorch GPU detection..."

$verifyScript = @"
import torch
import sys

try:
    print(f'PyTorch version: {torch.__version__}')
    
    if torch.cuda.is_available():
        print(f'CUDA available: True')
        print(f'CUDA version: {torch.version.cuda}')
        print(f'GPU: {torch.cuda.get_device_name(0)}')
        print(f'GPU memory: {torch.cuda.get_device_properties(0).total_memory / (1024**3):.2f} GB')
        sys.exit(0)
    elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        print(f'MPS available: True')
        print(f'Device: Apple Silicon')
        sys.exit(0)
    else:
        print(f'GPU: Not available (CPU mode)')
        sys.exit(0)
except Exception as e:
    print(f'Error: {e}', file=sys.stderr)
    sys.exit(1)
"@

$verifyOutput = & $venvPython -c $verifyScript 2>&1

Write-Host $verifyOutput
Write-Host ""

if ($LASTEXITCODE -ne 0) {
    Write-LogWarn "PyTorch GPU detection failed, continuing with CPU mode"
    $deviceMode = "cpu"
} else {
    Write-LogSuccess "PyTorch verification passed"
}

Write-Host ""

# Install other required packages
Write-LogInfo "Installing psutil for hardware detection..."
& $venvPython -m pip install --quiet psutil

if ($LASTEXITCODE -ne 0) {
    Write-LogError "Failed to install psutil"
    if (-not $KeepVenv) {
        Remove-Item -Path $venvPath -Recurse -Force
    }
    exit 1
}

Write-LogSuccess "Dependencies installed"
Write-Host ""

# Build arguments for prepare-job.py
Write-LogSection "RUNNING JOB PREPARATION"

$pythonArgs = @("scripts\prepare-job.py", $InputMedia)

if ($StartTime) {
    $pythonArgs += "--start-time", $StartTime
}

if ($EndTime) {
    $pythonArgs += "--end-time", $EndTime
}

if ($Transcribe) {
    $pythonArgs += "--transcribe"
    Write-LogInfo "Workflow: TRANSCRIBE"
} elseif ($SubtitleGen) {
    $pythonArgs += "--subtitle-gen"
    Write-LogInfo "Workflow: SUBTITLE-GEN"
}

# Always enable native mode since we're using venv
$pythonArgs += "--native"
Write-LogInfo "Native mode: ENABLED (using venv Python with $($deviceMode.ToUpper()))"
Write-LogInfo "Input media: $InputMedia"

if ($StartTime -and $EndTime) {
    Write-LogInfo "Clip: $StartTime → $EndTime"
}

Write-Host ""
Write-LogInfo "Executing: python $($pythonArgs -join ' ')"
Write-Host ""

# Execute prepare-job.py
try {
    & $venvPython @pythonArgs
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-LogSuccess "Job preparation completed successfully"
    } else {
        Write-LogError "Job preparation failed with exit code $LASTEXITCODE"
        throw "prepare-job.py failed"
    }
} catch {
    Write-LogError "Execution error: $_"
    Write-Host ""
    
    # Cleanup venv on failure
    if (-not $KeepVenv) {
        Write-LogInfo "Cleaning up virtual environment..."
        if (Test-Path $venvPath) {
            Remove-Item -Path $venvPath -Recurse -Force
        }
    }
    exit 1
}

Write-Host ""

# Cleanup virtual environment
if ($KeepVenv) {
    Write-LogSection "VIRTUAL ENVIRONMENT PRESERVED"
    Write-LogInfo "Virtual environment kept at: $venvPath"
    Write-LogInfo "To activate: . $activateScript"
    Write-LogInfo "To remove: Remove-Item -Path '$venvPath' -Recurse -Force"
} else {
    Write-LogSection "CLEANING UP"
    Write-LogInfo "Removing virtual environment..."
    
    # Deactivate first
    if (Test-Path Function:\deactivate) {
        deactivate
    }
    
    # Remove venv
    if (Test-Path $venvPath) {
        Remove-Item -Path $venvPath -Recurse -Force -ErrorAction SilentlyContinue
        
        if (Test-Path $venvPath) {
            Write-LogWarn "Could not remove virtual environment (may be in use)"
            Write-LogInfo "Manual cleanup: Remove-Item -Path '$venvPath' -Recurse -Force"
        } else {
            Write-LogSuccess "Virtual environment removed"
        }
    }
}

Write-Host ""
Write-LogSection "JOB PREPARATION COMPLETE"
Write-LogInfo "Device mode used: $($deviceMode.ToUpper())"
Write-LogSuccess "Ready to run pipeline"
Write-Host ""

exit 0
