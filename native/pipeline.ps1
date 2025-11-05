# MPS-optimized native pipeline orchestrator
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
    Write-LogError "Usage: .\native\pipeline.ps1 <input_video.mp4>"
    Write-Host "Example: .\native\pipeline.ps1 in\movie.mp4"
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

Write-LogSection "MPS NATIVE PIPELINE"
Write-LogInfo "Input: $InputFile"
Write-LogInfo "Output: $movieDir"
Write-LogInfo "Mode: Sequential execution with GPU acceleration"
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
    
    Write-LogInfo "Running: $($stage.Script)"
    
    # Activate venv and run Python script
    $activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
    & $activateScript
    
    $env:PYTHONPATH = "$PWD;$PWD\shared;$PWD\native\utils;$env:PYTHONPATH"
    
    & python $scriptPath --input $InputFile --movie-dir $movieDir
    
    if ($LASTEXITCODE -ne 0) {
        Write-LogFailure "Stage $($stage.Name) failed"
        exit 1
    }
    
    Write-LogSuccess "Stage $($stage.Name) completed"
}

Write-Host ""
Write-LogSection "PIPELINE COMPLETE"
Write-LogSuccess "Output: $movieDir"
Write-Host ""

exit 0
