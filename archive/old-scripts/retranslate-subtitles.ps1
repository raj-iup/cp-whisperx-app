#
# Re-translate Hinglish SRT to English using better translation model
# Fixes WhisperX translation hallucinations and missing segments
#
# Usage:
#   .\retranslate-subtitles.ps1 <job_dir>
#   .\retranslate-subtitles.ps1 out\2025\11\16\1\20251116-0002
#

param(
    [Parameter(Mandatory=$false, Position=0)]
    [string]$JobDir
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Activate virtual environment
$VenvActivate = Join-Path $ScriptDir ".bollyenv\Scripts\Activate.ps1"
if (Test-Path $VenvActivate) {
    & $VenvActivate
} else {
    Write-Error "Virtual environment not found at .bollyenv\"
    exit 1
}

# Check if job directory provided
if (-not $JobDir) {
    Write-Host "Usage: .\retranslate-subtitles.ps1 <job_dir>"
    Write-Host ""
    Write-Host "Example:"
    Write-Host "  .\retranslate-subtitles.ps1 out\2025\11\16\1\20251116-0002"
    Write-Host ""
    Write-Host "This will retranslate the Hinglish SRT file to English using a better"
    Write-Host "translation model, fixing WhisperX hallucinations and missing segments."
    exit 1
}

$AsrDir = Join-Path $JobDir "06_asr"

# Validate directories exist
if (-not (Test-Path $JobDir)) {
    Write-Error "Job directory not found: $JobDir"
    exit 1
}

if (-not (Test-Path $AsrDir)) {
    Write-Error "ASR directory not found: $AsrDir"
    exit 1
}

# Find the Hinglish SRT file
$HinglishSrt = Get-ChildItem -Path $AsrDir -Filter "*.srt" -File | 
    Where-Object { $_.Name -notmatch "English" -and $_.Name -notmatch "test" } | 
    Select-Object -First 1

if (-not $HinglishSrt) {
    Write-Error "No Hinglish SRT file found in $AsrDir"
    exit 1
}

# Determine output filename
$Basename = [System.IO.Path]::GetFileNameWithoutExtension($HinglishSrt.Name)
$OutputSrt = Join-Path $AsrDir "$Basename-English-Retranslated.srt"
$BackupSrt = Join-Path $AsrDir "$Basename-English.srt.backup"

Write-Host "=========================================="
Write-Host "  SRT Re-translation"
Write-Host "=========================================="
Write-Host "Job Directory: $JobDir"
Write-Host "Source SRT:    $($HinglishSrt.FullName)"
Write-Host "Output SRT:    $OutputSrt"
Write-Host ""

# Check if original English translation exists and offer to back it up
$OriginalEnglish = Join-Path $AsrDir "$Basename-English.srt"
if (Test-Path $OriginalEnglish) {
    Write-Host "Note: Original WhisperX translation found: $OriginalEnglish"
    if (-not (Test-Path $BackupSrt)) {
        Write-Host "      Creating backup: $BackupSrt"
        Copy-Item $OriginalEnglish $BackupSrt
    } else {
        Write-Host "      Backup already exists: $BackupSrt"
    }
    Write-Host ""
}

# Check if deep-translator is installed
try {
    python -c "import deep_translator" 2>$null
} catch {
    Write-Host "Installing deep-translator library..."
    pip install deep-translator --quiet
    Write-Host ""
}

# Run the retranslation
Write-Host "Starting translation..."
Write-Host "This may take a few minutes for large files..."
Write-Host ""

python scripts\retranslate_srt.py `
    $HinglishSrt.FullName `
    -o $OutputSrt `
    --method deep-translator `
    --src-lang hi `
    --dest-lang en

Write-Host ""
Write-Host "=========================================="
Write-Host "  Translation Complete!"
Write-Host "=========================================="
Write-Host "Output: $OutputSrt"
Write-Host ""

# Show file size comparison
if (Test-Path $OriginalEnglish) {
    $OrigSize = (Get-Item $OriginalEnglish).Length
    $NewSize = (Get-Item $OutputSrt).Length
    Write-Host "File size comparison:"
    Write-Host "  Original:      $([math]::Round($OrigSize/1KB, 2)) KB"
    Write-Host "  Retranslated:  $([math]::Round($NewSize/1KB, 2)) KB"
    Write-Host ""
}

# Offer to replace original
if (Test-Path $OriginalEnglish) {
    Write-Host "To replace the original English translation with the retranslated version:"
    Write-Host "  Copy-Item `"$OutputSrt`" `"$OriginalEnglish`""
    Write-Host ""
    Write-Host "To restore the original from backup:"
    Write-Host "  Copy-Item `"$BackupSrt`" `"$OriginalEnglish`""
}

Write-Host "=========================================="
