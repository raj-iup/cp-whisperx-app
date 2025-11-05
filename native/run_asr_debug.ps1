# Run Stage 7: ASR in debug mode with detailed logging
# PowerShell version with consistent logging

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$MovieName,
    
    [Parameter(Mandatory=$false)]
    [string]$Model = "base",
    
    [Parameter(Mandatory=$false)]
    [string]$Language = "",
    
    [Parameter(Mandatory=$false)]
    [int]$BatchSize = 16
)

$ErrorActionPreference = "Stop"

# Import logging functions
. "$PSScriptRoot\..\scripts\common-logging.ps1"

if (-not $MovieName) {
    Write-Host "Usage: .\native\run_asr_debug.ps1 <movie_name> [options]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Arguments:"
    Write-Host "  movie_name    Name of the movie directory in .\out\"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Model        Whisper model size (tiny, base, small, medium, large-v2, large-v3) [default: base]"
    Write-Host "  -Language     Language code (e.g., en, hi, es) [default: auto-detect]"
    Write-Host "  -BatchSize    Batch size for processing [default: 16]"
    Write-Host ""
    Write-Host "Example:"
    Write-Host "  .\native\run_asr_debug.ps1 My_Movie -Model base -Language en"
    exit 1
}

$MOVIE_DIR = Join-Path ".\out" $MovieName
$VENV_PATH = "native\venvs\asr"
$SCRIPT_PATH = "native\scripts\07_asr.py"

# Validate paths
if (-not (Test-Path $MOVIE_DIR)) {
    Write-LogError "Movie directory not found: $MOVIE_DIR"
    exit 1
}

if (-not (Test-Path $VENV_PATH)) {
    Write-LogError "Virtual environment not found: $VENV_PATH"
    Write-LogError "Run native\setup_venvs.ps1 first"
    exit 1
}

if (-not (Test-Path $SCRIPT_PATH)) {
    Write-LogError "Script not found: $SCRIPT_PATH"
    exit 1
}

# Find input video
$INPUT_FILE = $null
foreach ($ext in @("*.mp4", "*.mkv")) {
    $files = Get-ChildItem -Path ".\in" -Filter $ext -ErrorAction SilentlyContinue
    if ($files) {
        $INPUT_FILE = $files[0].FullName
        break
    }
}

if (-not $INPUT_FILE) {
    Write-LogWarn "Could not find input video in .\in\"
    Write-LogWarn "Using placeholder path - adjust if needed"
    $INPUT_FILE = ".\in\video.mp4"
}

Write-LogSection "DEBUG MODE: Stage 7 - ASR (Transcription + Alignment)"
Write-LogInfo "Movie Directory: $MOVIE_DIR"
Write-LogInfo "Virtual Env: $VENV_PATH"
Write-LogInfo "Script: $SCRIPT_PATH"
Write-LogInfo "Input: $INPUT_FILE"
Write-LogInfo "Model: $Model"
if ($Language) {
    Write-LogInfo "Language: $Language"
}
Write-LogInfo "Batch Size: $BatchSize"
Write-Host ""

# Activate venv and set environment
$activateScript = Join-Path $VENV_PATH "Scripts\Activate.ps1"
& $activateScript

$env:PYTHONPATH = "$PWD;$PWD\shared;$PWD\native\utils;$env:PYTHONPATH"
$env:PYTORCH_ENABLE_MPS_FALLBACK = "1"
$env:LOG_LEVEL = "DEBUG"

Write-LogInfo "Starting ASR stage in DEBUG mode..."
Write-LogInfo "Logs will be saved to: logs\asr_${MovieName}_*.log"
Write-Host ""

# Build arguments
$pythonArgs = @($SCRIPT_PATH, "--input", $INPUT_FILE, "--movie-dir", $MOVIE_DIR)
if ($Model) {
    $pythonArgs += "--model", $Model
}
if ($Language) {
    $pythonArgs += "--language", $Language
}
if ($BatchSize) {
    $pythonArgs += "--batch-size", $BatchSize
}

# Run Python with verbose output
& python -u @pythonArgs

$EXIT_CODE = $LASTEXITCODE

Write-Host ""
Write-LogSection "STAGE COMPLETE"
if ($EXIT_CODE -eq 0) {
    Write-LogSuccess "ASR stage completed successfully"
} else {
    Write-LogFailure "ASR stage failed with exit code: $EXIT_CODE"
}
Write-Host ""
Write-LogInfo "Check detailed logs in: logs\"
Write-LogInfo "Output files in: $MOVIE_DIR\transcription\"
Write-Host ""

exit $EXIT_CODE
