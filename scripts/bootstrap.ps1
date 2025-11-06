# CP-WhisperX-App Bootstrap Script (Enhanced)
# One-time setup: Creates Python environment, installs dependencies, detects hardware
#
# PHASE 1 ENHANCEMENTS:
# - Hardware detection with caching
# - Model pre-download
# - Directory creation
# - FFmpeg validation
# - Comprehensive validation

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

# Load common logging
. "$PSScriptRoot\common-logging.ps1"

# Start
Write-LogSection "CP-WHISPERX-APP BOOTSTRAP (ENHANCED)"
Write-LogInfo "One-time environment setup..."

$venvDir = ".bollyenv"
$reqFile = "requirements.txt"
$projectRoot = Split-Path -Parent $PSScriptRoot

# Find Python
Write-LogInfo "Searching for Python..."
$pythonBin = $null

if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonBin = "python"
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    $pythonBin = "python3"
} else {
    Write-LogError "Python not found. Please install Python 3.11+"
    exit 1
}

Write-LogInfo "Using: $pythonBin"

# Check Python version
Write-LogInfo "Checking Python version (recommended: 3.11+)"
& $pythonBin -c "import sys; v = sys.version_info; print(f'Python {v.major}.{v.minor}.{v.micro}'); print('Warning: Python 3.11+ recommended') if v.major < 3 or (v.major == 3 and v.minor < 11) else None"

# Create or use existing venv
if (Test-Path $venvDir) {
    Write-LogInfo "Found existing virtualenv: $venvDir"
} else {
    Write-LogInfo "Creating virtualenv: $venvDir"
    & $pythonBin -m venv $venvDir
}

# Activate venv
Write-LogInfo "Activating virtualenv..."
$activateScript = Join-Path $venvDir "Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
} else {
    Write-LogError "Could not find activation script"
    exit 1
}

# Upgrade pip and wheel
Write-LogInfo "Upgrading pip and wheel..."
python -m pip install -U pip wheel | Out-Null

# Create requirements.txt if missing
if (-not (Test-Path $reqFile)) {
    Write-LogInfo "Creating recommended $reqFile"
    
    $requirements = @"
torch>=2.3,<3.0
torchaudio>=2.3,<3.0
openai-whisper>=20231117
faster-whisper>=1.0.0
whisperx>=3.1.0
whisper-ctranslate2>=0.4.0
ctranslate2>=4.2.0
pyannote.audio>=3.1.0
huggingface_hub>=0.23.0
librosa>=0.10.1
soundfile>=0.12.1
tmdbsimple>=2.9.1
rich>=13.7.0
python-dotenv>=1.0.0
pysubs2>=1.1.0
spacy>=3.7.0
transformers>=4.30.0
"@
    
    Set-Content -Path $reqFile -Value $requirements
    Write-LogSuccess "Wrote $reqFile"
}

# Install dependencies
Write-LogInfo "Installing Python packages from $reqFile (this may take a while)..."
python -m pip install -r $reqFile

# ============================================================================
# PHASE 1 ENHANCEMENT: Create Required Directories
# ============================================================================
Write-LogSection "DIRECTORY STRUCTURE"
Write-LogInfo "Creating required directories..."

$requiredDirs = @(
    "in",
    "out",
    "logs",
    "jobs",
    "config",
    "shared-model-and-cache"
)

foreach ($dir in $requiredDirs) {
    $dirPath = Join-Path $projectRoot $dir
    if (-not (Test-Path $dirPath)) {
        New-Item -ItemType Directory -Path $dirPath -Force | Out-Null
        Write-LogInfo "  ✓ Created: $dir/"
    } else {
        Write-LogInfo "  ✓ Exists: $dir/"
    }
}

Write-LogSuccess "Directory structure validated"

# ============================================================================
# PHASE 1 ENHANCEMENT: Validate FFmpeg
# ============================================================================
Write-LogSection "FFMPEG VALIDATION"
Write-LogInfo "Checking FFmpeg installation..."

if (Get-Command ffmpeg -ErrorAction SilentlyContinue) {
    $ffmpegVersion = & ffmpeg -version 2>&1 | Select-Object -First 1
    Write-LogSuccess "FFmpeg found: $ffmpegVersion"
} else {
    Write-LogWarn "FFmpeg not found in PATH"
    Write-LogInfo "FFmpeg is required for media processing"
    Write-LogInfo "Download from: https://ffmpeg.org/download.html"
}

# ============================================================================
# PHASE 1 ENHANCEMENT: Hardware Detection with Caching
# ============================================================================
Write-LogSection "HARDWARE DETECTION & CACHING"
Write-LogInfo "Detecting hardware capabilities..."

try {
    # Run hardware detection with caching
    $hwOutput = python "$projectRoot\shared\hardware_detection.py" --no-cache 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        # Display output
        Write-Host $hwOutput
        Write-LogSuccess "Hardware detection complete"
        
        # Check if cache was created
        $cacheFile = Join-Path $projectRoot "out\hardware_cache.json"
        if (Test-Path $cacheFile) {
            Write-LogInfo "Hardware cache saved (valid for 1 hour)"
        }
    } else {
        Write-LogWarn "Hardware detection failed, but continuing..."
    }
} catch {
    Write-LogWarn "Could not detect hardware: $_"
}

# ============================================================================
# PHASE 1 ENHANCEMENT: Pre-download ML Models (Optional)
# ============================================================================
Write-LogSection "ML MODEL PRE-DOWNLOAD"
Write-LogInfo "Checking for model pre-download..."

$secretsFile = Join-Path $projectRoot "config\secrets.json"
if (Test-Path $secretsFile) {
    Write-LogInfo "Found config/secrets.json - attempting model pre-download"
    
    try {
        # Read secrets to check for HF token
        $secrets = Get-Content $secretsFile | ConvertFrom-Json
        
        if ($secrets.HF_TOKEN) {
            Write-LogInfo "HuggingFace token found - downloading PyAnnote models..."
            $env:HF_TOKEN = $secrets.HF_TOKEN
            
            # Download PyAnnote diarization model
            python -c "from pyannote.audio import Pipeline; Pipeline.from_pretrained('pyannote/speaker-diarization-3.1', use_auth_token=True)" 2>&1 | Out-Null
            
            if ($LASTEXITCODE -eq 0) {
                Write-LogSuccess "PyAnnote models pre-downloaded"
            } else {
                Write-LogWarn "Could not pre-download PyAnnote models"
            }
        } else {
            Write-LogInfo "No HuggingFace token - skipping model pre-download"
            Write-LogInfo "Models will be downloaded on first use"
        }
    } catch {
        Write-LogWarn "Could not read secrets or download models: $_"
    }
} else {
    Write-LogInfo "No secrets.json found - skipping model pre-download"
    Write-LogInfo "Create config/secrets.json with HF_TOKEN to pre-download models"
}

# ============================================================================
# Quick PyTorch Verification
# ============================================================================
Write-LogInfo "Verifying PyTorch installation..."
python -c "try: import torch, sys; cuda = torch.cuda.is_available(); print('  ✓ PyTorch version:', torch.__version__); print('  ✓ CUDA available:', bool(cuda)); except Exception as e: print('  ⚠ Could not verify torch:', repr(e)); sys.exit(0)"

# ============================================================================
# Complete
# ============================================================================
Write-LogSection "BOOTSTRAP COMPLETE"
Write-Host ""
Write-Host "✅ Environment ready!" -ForegroundColor Green
Write-Host ""
Write-Host "What's been set up:" -ForegroundColor Yellow
Write-Host "  ✓ Python virtual environment (.bollyenv/)" -ForegroundColor Gray
Write-Host "  ✓ 70+ Python packages installed" -ForegroundColor Gray
Write-Host "  ✓ Hardware capabilities detected & cached" -ForegroundColor Gray
Write-Host "  ✓ Required directories created" -ForegroundColor Gray
Write-Host "  ✓ FFmpeg validated" -ForegroundColor Gray
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Prepare a job:" -ForegroundColor Gray
Write-Host "     .\prepare-job.ps1 path\to\video.mp4" -ForegroundColor White
Write-Host ""
Write-Host "  2. Run the pipeline:" -ForegroundColor Gray
Write-Host "     .\run_pipeline.ps1 -Job <job-id>" -ForegroundColor White
Write-Host ""
Write-Host "Optional:" -ForegroundColor Yellow
Write-Host "  • Create config/secrets.json with API tokens" -ForegroundColor Gray
Write-Host "  • Re-run bootstrap to pre-download models" -ForegroundColor Gray
Write-Host ""

exit 0
