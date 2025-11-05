# CP-WhisperX-App Bootstrap Script
# Creates Python virtual environment and installs dependencies

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

# Logging functions
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [bootstrap] [$Level] $Message"
    
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

# Start
Write-Header "CP-WHISPERX-APP BOOTSTRAP"

$venvDir = ".bollyenv"
$reqFile = "requirements.txt"

# Find Python
Write-Log "Searching for Python..." "INFO"
$pythonBin = $null

if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonBin = "python"
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    $pythonBin = "python3"
} else {
    Write-Log "Python not found. Please install Python 3.11+" "ERROR"
    exit 1
}

Write-Log "Using: $pythonBin" "INFO"

# Check Python version
Write-Log "Checking Python version (recommended: 3.11+)" "INFO"
& $pythonBin -c "import sys; v = sys.version_info; print(f'Python {v.major}.{v.minor}.{v.micro}'); print('Warning: Python 3.11+ recommended') if v.major < 3 or (v.major == 3 and v.minor < 11) else None"

# Create or use existing venv
if (Test-Path $venvDir) {
    Write-Log "Found existing virtualenv: $venvDir" "INFO"
} else {
    Write-Log "Creating virtualenv: $venvDir" "INFO"
    & $pythonBin -m venv $venvDir
}

# Activate venv
Write-Log "Activating virtualenv..." "INFO"
$activateScript = Join-Path $venvDir "Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
} else {
    Write-Log "Could not find activation script" "ERROR"
    exit 1
}

# Upgrade pip and wheel
Write-Log "Upgrading pip and wheel..." "INFO"
python -m pip install -U pip wheel | Out-Null

# Create requirements.txt if missing
if (-not (Test-Path $reqFile)) {
    Write-Log "Creating recommended $reqFile" "INFO"
    
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
    Write-Log "Wrote $reqFile" "SUCCESS"
}

# Install dependencies
Write-Log "Installing Python packages from $reqFile (this may take a while)..." "INFO"
python -m pip install -r $reqFile

# Check torch/CUDA
Write-Log "Running quick torch/CUDA check..." "INFO"
python -c "try: import torch, sys; cuda = torch.cuda.is_available(); print('Torch version:', torch.__version__); print('CUDA available:', bool(cuda)); except Exception as e: print('Could not import torch or check devices:', repr(e)); sys.exit(0)"

# Complete
Write-Header "BOOTSTRAP COMPLETE"
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Create .\config\.env and .\config\secrets.json" -ForegroundColor Gray
Write-Host "  2. Run: .\preflight.ps1" -ForegroundColor Gray
Write-Host "  3. Run pipeline: python pipeline.py -h" -ForegroundColor Gray
Write-Host ""

exit 0
