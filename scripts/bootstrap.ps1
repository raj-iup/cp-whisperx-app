# CP-WhisperX-App Bootstrap Script
# Creates Python virtual environment and installs dependencies

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

# Load common logging
. "$PSScriptRoot\common-logging.ps1"

# Start
Write-LogSection "CP-WHISPERX-APP BOOTSTRAP"

$venvDir = ".bollyenv"
$reqFile = "requirements.txt"

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

# Check torch/CUDA
Write-LogInfo "Running quick torch/CUDA check..."
python -c "try: import torch, sys; cuda = torch.cuda.is_available(); print('Torch version:', torch.__version__); print('CUDA available:', bool(cuda)); except Exception as e: print('Could not import torch or check devices:', repr(e)); sys.exit(0)"

# Complete
Write-LogSection "BOOTSTRAP COMPLETE"
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Create .\config\.env and .\config\secrets.json" -ForegroundColor Gray
Write-Host "  2. Run: .\preflight.ps1" -ForegroundColor Gray
Write-Host "  3. Run pipeline: python pipeline.py -h" -ForegroundColor Gray
Write-Host ""

exit 0
