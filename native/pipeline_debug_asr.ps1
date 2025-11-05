# MPS-optimized native pipeline orchestrator with Stage 7 ASR in DEBUG mode
# PowerShell version with consistent logging

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$InputFile
)

$ErrorActionPreference = "Stop"

# Import logging functions
. "$PSScriptRoot\..\scripts\common-logging.ps1"

# Configuration
$OUTPUT_ROOT = ".\out"
$VENV_DIR = "native\venvs"
$SCRIPT_DIR = "native\scripts"

# Validate input
if (-not $InputFile) {
    Write-LogError "Usage: .\native\pipeline_debug_asr.ps1 <input_video.mp4>"
    Write-Host "Example: .\native\pipeline_debug_asr.ps1 in\movie.mp4"
    exit 1
}

if (-not (Test-Path $InputFile)) {
    Write-LogError "Input file not found: $InputFile"
    exit 1
}

# Extract movie directory name
$movieName = [System.IO.Path]::GetFileNameWithoutExtension($InputFile) -replace ' ', '_'
$movieDir = Join-Path $OUTPUT_ROOT $movieName
if (-not (Test-Path $movieDir)) {
    New-Item -ItemType Directory -Path $movieDir -Force | Out-Null
}

Write-LogSection "MPS NATIVE PIPELINE (ASR DEBUG MODE)"
Write-LogInfo "Input: $InputFile"
Write-LogInfo "Output: $movieDir"
Write-LogInfo "Mode: Sequential execution with GPU acceleration"
Write-LogWarn "Stage 7 (ASR) will run in DEBUG mode"
Write-Host ""

# Stage definitions
$stages = @(
    @{Name="demux"; Script="01_demux.py"; Description="Audio extraction"}
    @{Name="tmdb"; Script="02_tmdb.py"; Description="Metadata fetch"}
    @{Name="pre-ner"; Script="03_pre_ner.py"; Description="Entity extraction"}
    @{Name="silero-vad"; Script="04_silero_vad.py"; Description="Coarse VAD"}
    @{Name="pyannote-vad"; Script="05_pyannote_vad.py"; Description="Refined VAD"}
    @{Name="diarization"; Script="06_diarization.py"; Description="Speaker labeling"}
    @{Name="asr"; Script="07_asr.py"; Description="Transcription + translation"}
    @{Name="post-ner"; Script="08_post_ner.py"; Description="Entity correction"}
    @{Name="subtitle-gen"; Script="09_subtitle_gen.py"; Description="Subtitle generation"}
    @{Name="mux"; Script="10_mux.py"; Description="Video muxing"}
)

$total = $stages.Count
$current = 0

# Run stages sequentially
foreach ($stage in $stages) {
    $current++
    
    Write-Host ""
    Write-LogSection "Stage $current/$total`: $($stage.Name)"
    Write-LogInfo $stage.Description
    
    $venvPath = Join-Path $VENV_DIR $stage.Name
    $scriptPath = Join-Path $SCRIPT_DIR $stage.Script
    
    if (-not (Test-Path $venvPath)) {
        Write-LogError "Virtual environment not found: $venvPath"
        Write-LogError "Run native\setup_venvs.ps1 first"
        exit 1
    }
    
    if (-not (Test-Path $scriptPath)) {
        Write-LogError "Script not found: $scriptPath"
        exit 1
    }
    
    # Enable DEBUG mode for Stage 7 (ASR)
    if ($stage.Name -eq "asr") {
        Write-LogWarn "Running Stage 7 (ASR) in DEBUG mode"
        $env:LOG_LEVEL = "DEBUG"
    } else {
        $env:LOG_LEVEL = "INFO"
    }
    
    Write-LogInfo "Running: $($stage.Script)"
    $startTime = Get-Date
    
    # Activate venv and run Python script
    $activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
    & $activateScript
    
    $env:PYTHONPATH = "$PWD;$PWD\shared;$PWD\native\utils;$env:PYTHONPATH"
    $env:PYTORCH_ENABLE_MPS_FALLBACK = "1"
    
    & python -u $scriptPath --input $InputFile --movie-dir $movieDir
    
    if ($LASTEXITCODE -ne 0) {
        Write-LogFailure "Stage $($stage.Name) failed"
        Write-LogError "Pipeline stopped at stage $current/$total"
        exit 1
    }
    
    Write-LogSuccess "Stage $($stage.Name) completed"
}

Write-Host ""
Write-LogSection "PIPELINE COMPLETE"
Write-LogSuccess "All $total stages completed successfully"
Write-LogSuccess "Output directory: $movieDir"
Write-Host ""

exit 0
