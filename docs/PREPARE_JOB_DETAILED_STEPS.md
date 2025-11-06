# Detailed Execution Steps: prepare-job-venv & prepare-job.py

**Complete step-by-step breakdown of job preparation workflow**

---

## 🎯 Overview

Two-part execution:
1. **`prepare-job-venv.ps1`/`.sh`** - Wrapper script that creates venv, installs PyTorch, runs prepare-job.py
2. **`scripts/prepare-job.py`** - Core Python script that creates job structure

---

## 📦 Part 1: prepare-job-venv Script (Wrapper)

### Script Locations
- **Windows:** `prepare-job-venv.ps1`
- **Linux/macOS:** `prepare-job-venv.sh`

### Complete Execution Flow (19 Steps)

```
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 1: INITIALIZATION & VALIDATION                            │
└─────────────────────────────────────────────────────────────────┘
```

#### Step 1: Parse Command-Line Arguments
```powershell
# Lines 5-24: Parameter declaration
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
```
**Action:**
- Parses required input media path
- Parses optional clip times (start/end)
- Parses workflow mode flags
- Parses --keep-venv flag for debugging

**Arguments:**
| Argument | Type | Required | Purpose |
|----------|------|----------|---------|
| `InputMedia` | String | Yes | Path to video/audio file |
| `StartTime` | String | No | Clip start (HH:MM:SS) |
| `EndTime` | String | No | Clip end (HH:MM:SS) |
| `Transcribe` | Switch | No | Transcribe-only workflow |
| `SubtitleGen` | Switch | No | Full subtitle workflow |
| `KeepVenv` | Switch | No | Keep venv after execution |

---

#### Step 2: Load Common Logging System
```powershell
# Line 29: Load logging
. "$PSScriptRoot\scripts\common-logging.ps1"
```
**Action:**
- Loads shared logging functions
- Creates log file: `logs/YYYYMMDD-HHMMSS-prepare-job-venv.log`
- Sets up colored console output

---

#### Step 3: Display Header
```powershell
# Lines 32-34: Display header
Write-LogSection "CP-WHISPERX-APP JOB PREPARATION (VENV MODE)"
Write-LogInfo "Creating isolated Python environment for job preparation..."
```
**Output:**
```
======================================================================
CP-WHISPERX-APP JOB PREPARATION (VENV MODE)
======================================================================
[INFO] Creating isolated Python environment for job preparation...
```

---

#### Step 4: Validate Input Media File
```powershell
# Lines 36-40: Check input file exists
if (-not (Test-Path $InputMedia)) {
    Write-LogError "Input media not found: $InputMedia"
    exit 1
}
```
**Action:**
1. Checks if input file exists
2. Exits with error if not found

**Output (Success):**
```
(No output - continues)
```

**Output (Failure):**
```
[ERROR] Input media not found: movie.mp4
```

---

```
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 2: PYTHON DISCOVERY & VERSION CHECK                       │
└─────────────────────────────────────────────────────────────────┘
```

#### Step 5: Search for Python Executable
```powershell
# Lines 43-55: Find Python
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
```
**Action:**
1. Tries `python` command first
2. Falls back to `python3`
3. Falls back to `py` (Windows Python launcher)
4. Exits if none found

**Output:**
```
[INFO] Validating Python installation...
```

---

#### Step 6: Validate Python Version
```powershell
# Lines 57-69: Check version
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
```
**Action:**
1. Runs `python --version`
2. Parses version string with regex
3. Validates >= Python 3.9
4. Exits if too old

**Output (Good):**
```
[INFO] Found: Python 3.11.5
[SUCCESS] Python version check passed
```

**Output (Too Old):**
```
[INFO] Found: Python 3.8.10
[ERROR] Python 3.9+ required. Found: Python 3.8
```

---

```
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 3: VIRTUAL ENVIRONMENT CREATION                           │
└─────────────────────────────────────────────────────────────────┘
```

#### Step 7: Create Temporary Virtual Environment
```powershell
# Lines 74-92: Create venv
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
```
**Action:**
1. Sets venv path: `.venv-prepare-job-temp/`
2. Removes existing venv if present
3. Creates new venv with `python -m venv`
4. Checks for errors

**Command Executed:**
```bash
python -m venv .venv-prepare-job-temp
```

**Output:**
```
======================================================================
CREATING VIRTUAL ENVIRONMENT
======================================================================
[INFO] Location: C:\...\cp-whisperx-app\.venv-prepare-job-temp
[INFO] Creating new venv...
[SUCCESS] Virtual environment created
```

**Directory Created:**
```
.venv-prepare-job-temp/
├── Scripts/         # Windows
│   ├── Activate.ps1
│   ├── python.exe
│   └── pip.exe
└── pyvenv.cfg
```

---

#### Step 8: Activate Virtual Environment
```powershell
# Lines 95-112: Activate venv
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
```
**Action:**
1. Builds path to Activate.ps1 script
2. Checks if script exists
3. Executes activation script (dot-source)
4. Verifies Python executable exists in venv

**Output:**
```
[INFO] Activating virtual environment...
[SUCCESS] Virtual environment activated
```

**Effect:**
- `$env:PATH` modified to use venv Python
- `$env:VIRTUAL_ENV` set
- Prompt changes to show `(.venv-prepare-job-temp)`

---

```
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 4: HARDWARE DETECTION                                     │
└─────────────────────────────────────────────────────────────────┘
```

#### Step 9: Detect NVIDIA GPU via nvidia-smi
```powershell
# Lines 115-153: Hardware detection
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
```
**Action:**
1. Checks if `nvidia-smi` command exists
2. Runs `nvidia-smi` and captures output
3. Parses CUDA version with regex
4. Sets device mode to "cuda" if found

**Output (NVIDIA GPU Found):**
```
======================================================================
HARDWARE DETECTION
======================================================================
[INFO] Detecting available acceleration hardware...
[INFO] NVIDIA GPU detected (nvidia-smi available)
[INFO] CUDA Version: 12.6
```

**Output (No GPU):**
```
======================================================================
HARDWARE DETECTION
======================================================================
[INFO] Detecting available acceleration hardware...
[INFO] No NVIDIA GPU detected (nvidia-smi not found)
```

---

#### Step 10: Detect Apple Silicon (MPS)
```powershell
# Lines 143-150: Check for Apple Silicon
if ($IsWindows -eq $false -and $IsMacOS) {
    $systemInfo = & sysctl -n machdep.cpu.brand_string 2>&1
    if ($systemInfo -match "Apple") {
        Write-LogInfo "Apple Silicon detected"
        $deviceMode = "mps"
    }
}

Write-LogSuccess "Device mode: $($deviceMode.ToUpper())"
```
**Action:**
1. Checks if running on macOS
2. Runs `sysctl` to get CPU info
3. Checks for "Apple" in brand string
4. Sets device mode to "mps" if Apple Silicon

**Output (Apple Silicon):**
```
[INFO] Apple Silicon detected
[SUCCESS] Device mode: MPS
```

**Output (Final - CPU):**
```
[SUCCESS] Device mode: CPU
```

---

```
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 5: PYTORCH INSTALLATION                                   │
└─────────────────────────────────────────────────────────────────┘
```

#### Step 11: Install PyTorch with Matching CUDA Version
```powershell
# Lines 156-222: Install PyTorch
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
```
**Action:**
1. Determines PyTorch index URL based on CUDA version
2. Installs torch, torchvision, torchaudio
3. Falls back to CPU version if CUDA/MPS install fails
4. Cleans up venv on error

**CUDA Version Mapping:**
| CUDA Version | PyTorch Index URL |
|--------------|-------------------|
| 12.6+ | `https://download.pytorch.org/whl/cu126` |
| 12.4-12.5 | `https://download.pytorch.org/whl/cu124` |
| 12.1-12.3 | `https://download.pytorch.org/whl/cu121` |
| 11.x | `https://download.pytorch.org/whl/cu118` |

**Commands Executed:**
```bash
# For CUDA 12.6
python -m pip install --quiet torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126

# For MPS/CPU
python -m pip install --quiet torch torchvision torchaudio
```

**Output:**
```
======================================================================
INSTALLING PYTORCH
======================================================================
[INFO] Installing PyTorch with CUDA 12.6 support...
[INFO] PyTorch index: https://download.pytorch.org/whl/cu126
[SUCCESS] PyTorch installed successfully
```

**Packages Installed:**
- `torch` (~200 MB with CUDA, ~120 MB CPU)
- `torchvision` (~4 MB)
- `torchaudio` (~4 MB)

---

```
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 6: PYTORCH VERIFICATION                                   │
└─────────────────────────────────────────────────────────────────┘
```

#### Step 12: Verify PyTorch GPU Detection
```powershell
# Lines 226-265: Verify installation
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
```
**Action:**
1. Runs inline Python script to test PyTorch
2. Checks `torch.cuda.is_available()`
3. Checks `torch.backends.mps.is_available()`
4. Prints GPU details if available
5. Falls back to CPU if detection fails

**Output (CUDA Success):**
```
======================================================================
VERIFYING PYTORCH INSTALLATION
======================================================================
[INFO] Testing PyTorch GPU detection...
PyTorch version: 2.5.1+cu126
CUDA available: True
CUDA version: 12.6
GPU: NVIDIA GeForce GTX 750 Ti
GPU memory: 2.00 GB

[SUCCESS] PyTorch verification passed
```

**Output (MPS Success):**
```
PyTorch version: 2.5.1
MPS available: True
Device: Apple Silicon

[SUCCESS] PyTorch verification passed
```

**Output (CPU Mode):**
```
PyTorch version: 2.5.1+cpu
GPU: Not available (CPU mode)

[SUCCESS] PyTorch verification passed
```

---

#### Step 13: Install Additional Dependencies
```powershell
# Lines 269-281: Install psutil
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
```
**Action:**
1. Installs `psutil` package
2. Used by prepare-job.py for hardware detection
3. Cleans up venv on failure

**Command:**
```bash
python -m pip install --quiet psutil
```

**Output:**
```
[INFO] Installing psutil for hardware detection...
[SUCCESS] Dependencies installed
```

---

```
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 7: JOB PREPARATION EXECUTION                              │
└─────────────────────────────────────────────────────────────────┘
```

#### Step 14: Build Arguments for prepare-job.py
```powershell
# Lines 284-316: Build arguments
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
```
**Action:**
1. Builds argument list for prepare-job.py
2. Adds input media path
3. Adds optional clip times
4. Adds workflow mode flag
5. Always adds --native flag (venv execution)
6. Displays execution info

**Output:**
```
======================================================================
RUNNING JOB PREPARATION
======================================================================
[INFO] Workflow: SUBTITLE-GEN
[INFO] Native mode: ENABLED (using venv Python with CUDA)
[INFO] Input media: movie.mp4

[INFO] Executing: python scripts\prepare-job.py movie.mp4 --subtitle-gen --native
```

---

#### Step 15: Execute prepare-job.py
```powershell
# Lines 318-341: Execute Python script
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
```
**Action:**
1. Executes prepare-job.py with venv Python
2. Passes all arguments
3. Checks exit code
4. Cleans up venv on failure (unless --keep-venv)

**Output:**
```
(prepare-job.py output - see Part 2 below)

[SUCCESS] Job preparation completed successfully
```

---

```
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 8: CLEANUP                                                │
└─────────────────────────────────────────────────────────────────┘
```

#### Step 16: Cleanup Virtual Environment (Optional)
```powershell
# Lines 345-371: Cleanup or preserve venv
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
```
**Action:**
1. If `--keep-venv`: Displays preservation message
2. If not: Deactivates and removes venv
3. Reports success or manual cleanup needed

**Output (Default - Removed):**
```
======================================================================
CLEANING UP
======================================================================
[INFO] Removing virtual environment...
[SUCCESS] Virtual environment removed
```

**Output (--keep-venv):**
```
======================================================================
VIRTUAL ENVIRONMENT PRESERVED
======================================================================
[INFO] Virtual environment kept at: .venv-prepare-job-temp
[INFO] To activate: . .venv-prepare-job-temp\Scripts\Activate.ps1
[INFO] To remove: Remove-Item -Path '.venv-prepare-job-temp' -Recurse -Force
```

---

#### Step 17: Display Completion Summary
```powershell
# Lines 373-379: Final summary
Write-Host ""
Write-LogSection "JOB PREPARATION COMPLETE"
Write-LogInfo "Device mode used: $($deviceMode.ToUpper())"
Write-LogSuccess "Ready to run pipeline"
Write-Host ""

exit 0
```
**Action:**
1. Displays completion banner
2. Shows device mode used
3. Exits with success code

**Output:**
```
======================================================================
JOB PREPARATION COMPLETE
======================================================================
[INFO] Device mode used: CUDA
[SUCCESS] Ready to run pipeline
```

---

### prepare-job-venv Summary

**Total Steps:** 17  
**Duration:** 1-2 minutes (first run), 30-60 seconds (cached PyTorch)  
**Disk Space:** ~3 GB (temporary)

**Stages:**
1. Initialization & Validation (4 steps)
2. Python Discovery (2 steps)
3. Virtual Environment (2 steps)
4. Hardware Detection (2 steps)
5. PyTorch Installation (1 step)
6. PyTorch Verification (1 step)
7. Dependencies (1 step)
8. Job Preparation (2 steps)
9. Cleanup (2 steps)

**Files Created (Temporary):**
```
.venv-prepare-job-temp/          # Virtual environment (~3 GB)
├── Scripts/                     # Python, pip, activate
├── Lib/site-packages/           # PyTorch + dependencies
└── pyvenv.cfg

logs/
└── YYYYMMDD-HHMMSS-prepare-job-venv.log
```

**Exit Codes:**
- `0` = Success
- `1` = Failure (Python not found, venv creation failed, PyTorch install failed, etc.)

---

## 🎯 Part 2: scripts/prepare-job.py (Core Script)

### Script Location
- **Path:** `scripts/prepare-job.py`
- **Execution:** Called by wrapper or directly

### Complete Execution Flow (12 Steps)

```
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 1: INITIALIZATION                                         │
└─────────────────────────────────────────────────────────────────┘
```

#### Step 1: Parse Command-Line Arguments
```python
# main() function
parser = argparse.ArgumentParser(
    description="Prepare job for CP-WhisperX-App pipeline"
)
parser.add_argument("input_media", help="Path to input media file")
parser.add_argument("--transcribe", action="store_true", help="Transcribe-only workflow")
parser.add_argument("--subtitle-gen", action="store_true", help="Full subtitle workflow (default)")
parser.add_argument("--native", action="store_true", help="Enable native GPU acceleration")
parser.add_argument("--start-time", help="Start time for clip (HH:MM:SS)")
parser.add_argument("--end-time", help="End time for clip (HH:MM:SS)")
args = parser.parse_args()
```
**Action:**
- Parses all command-line arguments
- Validates required arguments

---

#### Step 2: Initialize Logger
```python
# Create logger
log_file = get_stage_log_filename("prepare-job")
logger = PipelineLogger("prepare-job", log_file)
logger.info("=" * 70)
logger.info("PREPARE JOB - Job Preparation")
logger.info("=" * 70)
```
**Action:**
- Creates logger instance
- Sets up log file: `logs/prepare-job_YYYYMMDD_HHMMSS.log`
- Logs header

**Output:**
```
======================================================================
PREPARE JOB - Job Preparation
======================================================================
```

---

```
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 2: HARDWARE DETECTION                                     │
└─────────────────────────────────────────────────────────────────┘
```

#### Step 3: Detect Hardware Capabilities
```python
def detect_hardware_capabilities():
    """Detect hardware and recommend optimal settings."""
    import psutil
    
    hw_info = {
        'cpu_cores': psutil.cpu_count(logical=False) or 1,
        'cpu_threads': psutil.cpu_count(logical=True) or 1,
        'memory_gb': round(psutil.virtual_memory().total / (1024**3), 2),
        'gpu_available': False,
        'gpu_type': None,
        'gpu_memory_gb': None,
        'gpu_name': None,
        'recommended_settings': {}
    }
    
    # Detect GPU
    try:
        import torch
        
        # Check for CUDA
        if torch.cuda.is_available():
            hw_info['gpu_available'] = True
            hw_info['gpu_type'] = 'cuda'
            hw_info['gpu_name'] = torch.cuda.get_device_name(0)
            hw_info['gpu_memory_gb'] = round(
                torch.cuda.get_device_properties(0).total_memory / (1024**3), 2
            )
        # Check for MPS (Apple Silicon)
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            hw_info['gpu_available'] = True
            hw_info['gpu_type'] = 'mps'
            hw_info['gpu_name'] = 'Apple Silicon (MPS)'
            # Estimate MPS memory
            if hw_info['memory_gb'] >= 32:
                hw_info['gpu_memory_gb'] = 16
            else:
                hw_info['gpu_memory_gb'] = 8
        else:
            hw_info['gpu_type'] = 'cpu'
    except Exception:
        hw_info['gpu_type'] = 'cpu'
    
    # Calculate optimal settings
    hw_info['recommended_settings'] = _calculate_optimal_settings(hw_info)
    
    return hw_info
```
**Action:**
1. Detects CPU cores and threads
2. Detects system RAM
3. Imports PyTorch
4. Checks CUDA availability
5. Checks MPS availability (macOS)
6. Gets GPU name and memory
7. Calculates optimal settings

**Hardware Info Collected:**
| Field | Example | Description |
|-------|---------|-------------|
| `cpu_cores` | 4 | Physical CPU cores |
| `cpu_threads` | 8 | Logical threads (with hyperthreading) |
| `memory_gb` | 16.0 | System RAM in GB |
| `gpu_available` | `True` | GPU detected |
| `gpu_type` | `"cuda"` | GPU type (cuda/mps/cpu) |
| `gpu_name` | `"NVIDIA GeForce GTX 750 Ti"` | GPU model name |
| `gpu_memory_gb` | 2.0 | GPU VRAM in GB |

---

#### Step 4: Calculate Optimal Settings
```python
def _calculate_optimal_settings(hw_info: dict) -> dict:
    """Calculate optimal settings based on hardware."""
    settings = {
        'whisper_model': 'large-v3',
        'whisper_model_reason': '',
        'batch_size': 16,
        'batch_size_reason': '',
        'compute_type': 'float16',
        'compute_type_reason': '',
        'chunk_length_s': 30,
        'chunk_length_reason': '',
        'max_speakers': 10,
        'max_speakers_reason': '',
        'use_docker_cpu_fallback': True,
        'docker_recommendation': ''
    }
    
    memory_gb = hw_info['memory_gb']
    gpu_type = hw_info['gpu_type']
    gpu_memory_gb = hw_info.get('gpu_memory_gb', 0) or 0
    cpu_cores = hw_info['cpu_cores']
    
    # Model selection based on GPU memory
    if gpu_type in ['cuda', 'mps']:
        if gpu_memory_gb >= 10:
            settings['whisper_model'] = 'large-v3'
            settings['whisper_model_reason'] = f'GPU has {gpu_memory_gb}GB VRAM - can handle large-v3'
        elif gpu_memory_gb >= 6:
            settings['whisper_model'] = 'medium'
            settings['whisper_model_reason'] = f'GPU has {gpu_memory_gb}GB VRAM - medium model recommended'
        else:
            settings['whisper_model'] = 'base'
            settings['whisper_model_reason'] = f'GPU has {gpu_memory_gb}GB VRAM - base model recommended'
    else:
        # CPU mode
        settings['whisper_model'] = 'base'
        settings['whisper_model_reason'] = 'CPU-only - base model for reasonable speed'
    
    # Batch size optimization
    if gpu_type in ['cuda', 'mps']:
        if gpu_memory_gb >= 10:
            settings['batch_size'] = 16
        elif gpu_memory_gb >= 6:
            settings['batch_size'] = 8
        else:
            settings['batch_size'] = 4
    else:
        settings['batch_size'] = 1
    
    # Compute type
    if gpu_type == 'cuda' and gpu_memory_gb >= 6:
        settings['compute_type'] = 'float16'
    elif gpu_type == 'mps':
        settings['compute_type'] = 'float32'  # MPS doesn't support float16 well
    else:
        settings['compute_type'] = 'int8'
    
    return settings
```
**Action:**
1. Analyzes hardware capabilities
2. Recommends Whisper model size
3. Calculates optimal batch size
4. Determines compute type (float16/float32/int8)
5. Sets chunk length
6. Estimates max speakers

**Optimization Logic:**

| Hardware | Whisper Model | Batch Size | Compute Type |
|----------|---------------|------------|--------------|
| GPU 10+ GB | large-v3 | 16 | float16 |
| GPU 6-10 GB | medium | 8 | float16 |
| GPU 2-6 GB | base | 4 | float16 |
| MPS (Apple) | medium-large | 8 | float32 |
| CPU only | base | 1 | int8 |

**Log Output:**
```
[INFO] Hardware Detection:
[INFO]   CPU: 4 cores, 8 threads
[INFO]   Memory: 16.0 GB
[INFO]   GPU: NVIDIA GeForce GTX 750 Ti (CUDA)
[INFO]   GPU Memory: 2.0 GB
[INFO] Recommended Settings:
[INFO]   Whisper Model: base (GPU has 2.0GB VRAM - base model recommended)
[INFO]   Batch Size: 4
[INFO]   Compute Type: float16
```

---

```
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 3: JOB CREATION                                           │
└─────────────────────────────────────────────────────────────────┘
```

#### Step 5: Create Job Directory Structure
```python
class JobManager:
    def create_job(self, input_media: Path, workflow_mode: str = 'subtitle-gen', 
                   native_mode: bool = False, start_time: Optional[str] = None,
                   end_time: Optional[str] = None) -> Dict:
        """Create new job with directory structure."""
        
        # Get date components
        year, month, day = self._get_date_components()  # e.g., 2024, "11", "06"
        user_id = self._get_user_id()  # e.g., 1
        
        # Get next job number
        job_no = self._get_next_job_number(year, month, day, user_id)  # e.g., 1
        job_id = f"{year}{month}{day}-{job_no:04d}"  # e.g., "20241106-0001"
        
        # Create job directory
        job_dir = self.output_root / str(year) / month / day / str(user_id) / job_id
        # Example: out/2024/11/06/1/20241106-0001/
        job_dir.mkdir(exist_ok=True, parents=True)
        
        # Create job info
        job_info = {
            "job_id": job_id,
            "job_no": job_no,
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "job_dir": str(job_dir.absolute()),
            "source_media": str(input_media.absolute()),
            "workflow_mode": workflow_mode,
            "native_mode": native_mode,
            "is_clip": bool(start_time and end_time),
            "status": "preparing"
        }
        
        if start_time and end_time:
            job_info["clip_start"] = start_time
            job_info["clip_end"] = end_time
        
        # Save job definition
        job_json_file = job_dir / "job.json"
        with open(job_json_file, 'w') as f:
            json.dump(job_info, f, indent=2)
        
        logger.info(f"Job created: {job_id}")
        logger.info(f"Directory: {job_dir}")
        
        return job_info
```
**Action:**
1. Gets current date (YYYY/MM/DD)
2. Gets user ID from environment (default: 1)
3. Scans existing jobs to get next job number
4. Generates job ID: `YYYYMMDD-NNNN`
5. Creates directory structure
6. Creates job.json definition file

**Directory Structure Created:**
```
out/
└── 2024/
    └── 11/
        └── 06/
            └── 1/
                └── 20241106-0001/
                    └── job.json
```

**job.json Content:**
```json
{
  "job_id": "20241106-0001",
  "job_no": 1,
  "user_id": 1,
  "created_at": "2024-11-06T15:30:45.123456",
  "job_dir": "C:\\...\\out\\2024\\11\\06\\1\\20241106-0001",
  "source_media": "C:\\...\\movie.mp4",
  "workflow_mode": "subtitle-gen",
  "native_mode": true,
  "is_clip": false,
  "status": "preparing"
}
```

**Log Output:**
```
[INFO] Job created: 20241106-0001
[INFO] User ID: 1
[INFO] Workflow: SUBTITLE-GEN
[INFO] Native mode: enabled
[INFO] Directory: out/2024/11/06/1/20241106-0001
[INFO] Job definition: out/2024/11/06/1/20241106-0001/job.json
```

---

```
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 4: MEDIA PREPARATION                                      │
└─────────────────────────────────────────────────────────────────┘
```

#### Step 6: Prepare Media File (Clip or Copy)
```python
def prepare_media(
    self, 
    job_info: Dict, 
    input_media: Path,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None
) -> Path:
    """Prepare media file for job (clip or copy)."""
    job_dir = Path(job_info["job_dir"])
    
    # Generate output filename
    if start_time and end_time:
        # For clips: movie.mp4 -> movie_clip_0001.mp4
        stem = input_media.stem
        ext = input_media.suffix
        job_no = job_info["job_no"]
        media_filename = f"{stem}_clip_{job_no:04d}{ext}"
    else:
        # For full media: use original filename
        media_filename = input_media.name
    
    output_media = job_dir / media_filename
    
    if start_time and end_time:
        # Create clip with FFmpeg
        logger.info("Creating media clip...")
        logger.info(f"Source: {input_media}")
        logger.info(f"Clip: {start_time} → {end_time}")
        logger.info(f"Output filename: {media_filename}")
        
        cmd = [
            "ffmpeg", "-i", str(input_media),
            "-ss", start_time,
            "-to", end_time,
            "-c", "copy",  # Copy codec (no re-encoding)
            "-y",
            str(output_media)
        ]
        
        try:
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True
            )
            logger.info(f"Clip created: {output_media}")
            job_info["is_clip"] = True
            job_info["clip_start"] = start_time
            job_info["clip_end"] = end_time
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg failed: {e}")
            logger.error(f"STDERR: {e.stderr}")
            sys.exit(1)
    else:
        # Copy full media
        logger.info("Copying media file...")
        logger.info(f"Source: {input_media}")
        shutil.copy2(input_media, output_media)
        logger.info(f"Media copied: {output_media}")
        job_info["is_clip"] = False
    
    return output_media
```
**Action:**
1. Generates output filename
2. If clip requested: Runs FFmpeg to extract clip
3. If full media: Copies file to job directory
4. Updates job_info with clip status

**FFmpeg Command (Clip):**
```bash
ffmpeg -i movie.mp4 -ss 00:10:00 -to 00:15:00 -c copy -y output.mp4
```

**Log Output (Clip):**
```
[INFO] Creating media clip...
[INFO] Source: C:\Videos\movie.mp4
[INFO] Clip: 00:10:00 → 00:15:00
[INFO] Output filename: movie_clip_0001.mp4
[INFO] Clip created: out/2024/11/06/1/20241106-0001/movie_clip_0001.mp4
```

**Log Output (Full Copy):**
```
[INFO] Copying media file...
[INFO] Source: C:\Videos\movie.mp4
[INFO] Media copied: out/2024/11/06/1/20241106-0001/movie.mp4
```

**Files Created:**
```
out/2024/11/06/1/20241106-0001/
├── job.json
└── movie.mp4                    # Or movie_clip_0001.mp4
```

---

```
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 5: CONFIGURATION GENERATION                               │
└─────────────────────────────────────────────────────────────────┘
```

#### Step 7: Load Configuration Template
```python
def finalize_job(self, job_info: Dict, media_path: Path):
    """Finalize job by creating environment file from template."""
    job_dir = Path(job_info["job_dir"])
    job_id = job_info["job_id"]
    
    # Job environment file
    job_env_file = job_dir / f".{job_id}.env"
    
    # Load config template
    config_template = Path("config/.env.pipeline")
    
    if not config_template.exists():
        logger.error(f"Config template not found: {config_template}")
        raise FileNotFoundError(f"Config template not found: {config_template}")
    
    logger.info(f"Using config template: {config_template}")
    logger.info("Applying hardware-optimized settings...")
    
    # Read template
    with open(config_template) as f:
        config_content = f.read()
```
**Action:**
1. Creates job-specific .env filename: `.20241106-0001.env`
2. Loads template from `config/.env.pipeline`
3. Reads template content

---

#### Step 8: Calculate Paths and Apply Settings
```python
    # Calculate paths based on job structure
    year = job_id[0:4]   # "2024"
    month = job_id[4:6]  # "11"
    day = job_id[6:8]    # "06"
    user_id = job_info.get("user_id", 1)
    
    output_root = f"out/{year}/{month}/{day}/{user_id}/{job_id}"
    log_root = f"out/{year}/{month}/{day}/{user_id}/{job_id}/logs"
    
    # Get workflow mode and native mode
    workflow_mode = job_info.get("workflow_mode", "subtitle-gen")
    native_mode = job_info.get("native_mode", False)
    
    # Get hardware-optimized settings
    hw_info = detect_hardware_capabilities()
    settings = hw_info['recommended_settings']
    
    # Determine device based on native mode
    if native_mode and hw_info['gpu_available']:
        device = hw_info['gpu_type']  # 'cuda' or 'mps'
    else:
        device = 'cpu'
```
**Action:**
1. Parses job ID to extract date components
2. Constructs output and log paths
3. Gets workflow mode (transcribe vs subtitle-gen)
4. Gets native mode flag
5. Re-runs hardware detection
6. Determines device (cuda/mps/cpu)

---

#### Step 9: Generate Configuration File
```python
    # Apply substitutions to template
    config_content = config_content.replace("{{JOB_ID}}", job_id)
    config_content = config_content.replace("{{OUTPUT_ROOT}}", output_root)
    config_content = config_content.replace("{{LOG_ROOT}}", log_root)
    config_content = config_content.replace("{{INPUT_MEDIA}}", str(media_path))
    config_content = config_content.replace("{{WORKFLOW_MODE}}", workflow_mode)
    config_content = config_content.replace("{{WHISPER_MODEL}}", settings['whisper_model'])
    config_content = config_content.replace("{{BATCH_SIZE}}", str(settings['batch_size']))
    config_content = config_content.replace("{{COMPUTE_TYPE}}", settings['compute_type'])
    config_content = config_content.replace("{{DEVICE_WHISPERX}}", device)
    config_content = config_content.replace("{{DEVICE_DIARIZATION}}", device)
    config_content = config_content.replace("{{DEVICE_VAD}}", device)
    config_content = config_content.replace("{{DEVICE_NER}}", device)
    config_content = config_content.replace("{{CHUNK_LENGTH_S}}", str(settings['chunk_length_s']))
    config_content = config_content.replace("{{MAX_SPEAKERS}}", str(settings['max_speakers']))
    
    # Write final configuration
    with open(job_env_file, 'w') as f:
        f.write(config_content)
    
    logger.info(f"Job configuration created: {job_env_file}")
    logger.success("Job preparation complete!")
```
**Action:**
1. Performs variable substitution on template
2. Replaces {{PLACEHOLDERS}} with actual values
3. Writes final .env file
4. Logs success

**Template Variables:**
| Variable | Example Value | Source |
|----------|---------------|--------|
| `{{JOB_ID}}` | `20241106-0001` | Job ID |
| `{{OUTPUT_ROOT}}` | `out/2024/11/06/1/20241106-0001` | Calculated |
| `{{LOG_ROOT}}` | `out/2024/11/06/1/20241106-0001/logs` | Calculated |
| `{{INPUT_MEDIA}}` | `movie.mp4` | Media path |
| `{{WORKFLOW_MODE}}` | `subtitle-gen` | User choice |
| `{{WHISPER_MODEL}}` | `base` | Hardware optimized |
| `{{BATCH_SIZE}}` | `4` | Hardware optimized |
| `{{COMPUTE_TYPE}}` | `float16` | Hardware optimized |
| `{{DEVICE_WHISPERX}}` | `cuda` | Native mode + GPU |
| `{{DEVICE_DIARIZATION}}` | `cuda` | Native mode + GPU |
| `{{DEVICE_VAD}}` | `cuda` | Native mode + GPU |
| `{{DEVICE_NER}}` | `cuda` | Native mode + GPU |
| `{{CHUNK_LENGTH_S}}` | `30` | Hardware optimized |
| `{{MAX_SPEAKERS}}` | `10` | Hardware optimized |

**Log Output:**
```
[INFO] Using config template: config/.env.pipeline
[INFO] Applying hardware-optimized settings...
[INFO]   Whisper Model: base
[INFO]   Batch Size: 4
[INFO]   Compute Type: float16
[INFO]   Device: CUDA
[INFO] Job configuration created: out/2024/11/06/1/20241106-0001/.20241106-0001.env
[SUCCESS] Job preparation complete!
```

---

#### Step 10: Update job.json with Final Status
```python
    # Update job.json with final status
    job_info["status"] = "ready"
    job_info["media_path"] = str(media_path)
    job_info["config_file"] = str(job_env_file)
    job_info["prepared_at"] = datetime.now().isoformat()
    job_info["hardware"] = {
        "cpu_cores": hw_info['cpu_cores'],
        "memory_gb": hw_info['memory_gb'],
        "gpu_type": hw_info['gpu_type'],
        "gpu_name": hw_info['gpu_name'],
        "gpu_memory_gb": hw_info['gpu_memory_gb']
    }
    job_info["settings"] = settings
    
    job_json_file = job_dir / "job.json"
    with open(job_json_file, 'w') as f:
        json.dump(job_info, f, indent=2)
```
**Action:**
1. Updates job status to "ready"
2. Adds media path
3. Adds config file path
4. Adds timestamp
5. Saves hardware info
6. Saves optimized settings
7. Overwrites job.json

**Updated job.json:**
```json
{
  "job_id": "20241106-0001",
  "job_no": 1,
  "user_id": 1,
  "created_at": "2024-11-06T15:30:45.123456",
  "prepared_at": "2024-11-06T15:31:02.456789",
  "job_dir": "...",
  "source_media": "...",
  "media_path": "out/2024/11/06/1/20241106-0001/movie.mp4",
  "config_file": "out/2024/11/06/1/20241106-0001/.20241106-0001.env",
  "workflow_mode": "subtitle-gen",
  "native_mode": true,
  "is_clip": false,
  "status": "ready",
  "hardware": {
    "cpu_cores": 4,
    "memory_gb": 16.0,
    "gpu_type": "cuda",
    "gpu_name": "NVIDIA GeForce GTX 750 Ti",
    "gpu_memory_gb": 2.0
  },
  "settings": {
    "whisper_model": "base",
    "batch_size": 4,
    "compute_type": "float16",
    "chunk_length_s": 30,
    "max_speakers": 10,
    "use_docker_cpu_fallback": true
  }
}
```

---

```
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 6: COMPLETION                                             │
└─────────────────────────────────────────────────────────────────┘
```

#### Step 11: Display Summary
```python
    # Display summary
    logger.info("=" * 70)
    logger.info("JOB SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Job ID: {job_id}")
    logger.info(f"Job Directory: {job_dir}")
    logger.info(f"Workflow: {workflow_mode.upper()}")
    logger.info(f"Native Mode: {'ENABLED' if native_mode else 'DISABLED'}")
    logger.info(f"Device: {device.upper()}")
    logger.info(f"Whisper Model: {settings['whisper_model']}")
    logger.info(f"Batch Size: {settings['batch_size']}")
    logger.info(f"Ready for pipeline execution")
    logger.info("=" * 70)
```
**Output:**
```
======================================================================
JOB SUMMARY
======================================================================
[INFO] Job ID: 20241106-0001
[INFO] Job Directory: out/2024/11/06/1/20241106-0001
[INFO] Workflow: SUBTITLE-GEN
[INFO] Native Mode: ENABLED
[INFO] Device: CUDA
[INFO] Whisper Model: base
[INFO] Batch Size: 4
[INFO] Ready for pipeline execution
======================================================================
```

---

#### Step 12: Exit with Success Code
```python
# Exit success
sys.exit(0)
```
**Action:**
- Exits with code 0 (success)

---

### prepare-job.py Summary

**Total Steps:** 12  
**Duration:** 5-30 seconds  
**Disk Space:** Size of media file + ~1 KB (configs)

**Stages:**
1. Initialization (2 steps)
2. Hardware Detection (2 steps)
3. Job Creation (1 step)
4. Media Preparation (1 step)
5. Configuration Generation (3 steps)
6. Finalization (2 steps)
7. Completion (1 step)

**Files Created:**
```
out/2024/11/06/1/20241106-0001/
├── job.json                      # Job metadata
├── .20241106-0001.env           # Job configuration
└── movie.mp4                     # Media file (copied or clipped)

logs/
└── prepare-job_20241106_153045.log  # Execution log
```

**Exit Codes:**
- `0` = Success
- `1` = Failure (media not found, FFmpeg failed, template missing, etc.)

---

## 🔄 Complete Workflow Summary

### End-to-End Execution

```
prepare-job-venv.ps1 movie.mp4 --subtitle-gen
    │
    ├─ Step 1-6: Validate Python, create venv
    ├─ Step 7-10: Detect GPU, install PyTorch
    ├─ Step 11-13: Verify PyTorch, install psutil
    │
    └─ Step 14-15: Execute prepare-job.py
                │
                ├─ Step 1-4: Parse args, detect hardware, calculate settings
                ├─ Step 5-6: Create job directory, prepare media
                └─ Step 7-12: Generate config, finalize job, exit
    │
    └─ Step 16-17: Cleanup venv, display completion
```

### Total Duration
- **First run:** 1-2 minutes (PyTorch download)
- **Subsequent runs:** 30-60 seconds (cached PyTorch)
- **Without venv (direct):** 5-10 seconds

### Files Created
```
.venv-prepare-job-temp/         # Temporary (removed after)
├── Scripts/python.exe
└── Lib/site-packages/torch/

out/2024/11/06/1/20241106-0001/  # Permanent
├── job.json
├── .20241106-0001.env
└── movie.mp4

logs/
├── YYYYMMDD-HHMMSS-prepare-job-venv.log
└── prepare-job_YYYYMMDD_HHMMSS.log
```

### Next Step
```bash
# Run pipeline with prepared job
.\run_pipeline.ps1 -Job 20241106-0001
```

---

**Created:** 2024-11-06  
**Version:** 1.0.0  
**Purpose:** Complete execution documentation for prepare-job workflow
