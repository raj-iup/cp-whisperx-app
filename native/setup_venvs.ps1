# Creates isolated virtual environments for each pipeline stage
# PowerShell version with consistent logging

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

# Import logging functions
. "$PSScriptRoot\..\scripts\common-logging.ps1"

$VENV_DIR = "native\venvs"
$REQ_DIR = "native\requirements"
$PYTHON_CMD = "python"

Write-LogSection "MPS NATIVE PIPELINE - VIRTUAL ENVIRONMENT SETUP"

# Check Python version
Write-LogInfo "Checking Python version..."
try {
    $pythonVersion = & $PYTHON_CMD --version 2>&1
    Write-LogInfo "Using: $pythonVersion"
} catch {
    Write-LogError "Python 3 not found! Please install Python 3.9+"
    exit 1
}

$stages = @(
    "demux", "tmdb", "pre-ner", "silero-vad", "pyannote-vad", 
    "diarization", "asr", "post-ner", "subtitle-gen", "mux"
)
$total = $stages.Count
$current = 0

foreach ($stageName in $stages) {
    $current++
    Write-LogInfo "[$current/$total] Creating venv for $stageName..."
    
    $venvPath = Join-Path $VENV_DIR $stageName
    $reqFileName = $stageName -replace '-', '_'
    $reqFile = Join-Path $REQ_DIR "$reqFileName.txt"
    
    # Create virtual environment
    if (Test-Path $venvPath) {
        Write-LogInfo "  venv already exists, skipping creation"
    } else {
        & $PYTHON_CMD -m venv $venvPath
        Write-LogSuccess "  venv created"
    }
    
    # Install requirements if file exists
    if (Test-Path $reqFile) {
        $hasContent = Get-Content $reqFile | Where-Object { $_ -match '^\s*[^#]' }
        if ($hasContent) {
            Write-LogInfo "  Installing requirements..."
            $pipExe = Join-Path $venvPath "Scripts\pip.exe"
            & $pipExe install --quiet --upgrade pip setuptools wheel
            & $pipExe install --quiet -r $reqFile
            Write-LogSuccess "  requirements installed"
        } else {
            Write-LogWarn "  [SKIP] no dependencies in requirements file"
        }
    } else {
        Write-LogWarn "  [WARN] no requirements file found: $reqFile"
    }
    Write-Host ""
}

Write-LogSection "VIRTUAL ENVIRONMENT SETUP COMPLETE"
Write-Host ""
Write-LogSuccess "All stage environments created in: $VENV_DIR\"
Write-Host ""
Write-LogInfo "Next steps:"
Write-LogInfo "  1. Configure: config\.env and config\secrets.json"
Write-LogInfo "  2. Run: python native\pipeline.py in\movie.mp4"
Write-Host ""

exit 0
