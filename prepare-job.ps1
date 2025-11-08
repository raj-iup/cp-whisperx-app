# CP-WhisperX-App Job Preparation Script (Simplified)
# Phase 1 Enhancement: Uses existing .bollyenv, hardware cache, no temp venv
#
# IMPROVEMENTS:
# - 80-90% faster (5-30 seconds vs 1-2 minutes)
# - No temporary venv creation
# - No PyTorch installation
# - Uses cached hardware info
# - Direct execution via .bollyenv

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true, Position=0)]
    [Alias("i", "Input")]
    [string]$InputMedia,
    
    [Parameter(Mandatory=$false)]
    [string]$StartTime,
    
    [Parameter(Mandatory=$false)]
    [string]$EndTime,
    
    [Parameter(Mandatory=$false)]
    [switch]$Transcribe,
    
    [Parameter(Mandatory=$false)]
    [Alias("SubtitleGen")]
    [switch]$Subtitle,
    
    [Parameter(Mandatory=$false)]
    [Alias("Workflow")]
    [ValidateSet("subtitle", "transcribe")]
    [string]$Mode
)

$ErrorActionPreference = "Stop"

# Load common logging
. ".\scripts\common-logging.ps1"

Write-LogSection "CP-WHISPERX-APP JOB PREPARATION (OPTIMIZED)"

# ============================================================================
# Step 1: Validate Environment
# ============================================================================
Write-LogInfo "Validating environment..."

# Check if bootstrap has been run
$venvPath = ".bollyenv"
if (-not (Test-Path $venvPath)) {
    Write-LogError "Bootstrap not run - virtual environment not found"
    Write-LogInfo "Please run: .\scripts\bootstrap.ps1"
    exit 1
}

$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
if (-not (Test-Path $activateScript)) {
    Write-LogError "Virtual environment incomplete"
    Write-LogInfo "Please re-run: .\scripts\bootstrap.ps1"
    exit 1
}

Write-LogSuccess "Environment validated"

# ============================================================================
# Step 2: Activate Virtual Environment
# ============================================================================
Write-LogInfo "Activating .bollyenv..."
. $activateScript

# ============================================================================
# Step 3: Validate Input Media
# ============================================================================
Write-LogInfo "Validating input media..."

if (-not (Test-Path $InputMedia)) {
    Write-LogError "Input media not found: $InputMedia"
    exit 1
}

Write-LogSuccess "Input media validated"

# ============================================================================
# Step 4: Build Arguments for prepare-job.py
# ============================================================================
$pythonArgs = @("scripts\prepare-job.py", $InputMedia)

# Add clip times if specified
if ($StartTime) {
    $pythonArgs += "--start-time", $StartTime
}

if ($EndTime) {
    $pythonArgs += "--end-time", $EndTime
}

# Add workflow mode
if ($Mode -eq "transcribe" -or $Transcribe) {
    $pythonArgs += "--transcribe"
    Write-LogInfo "Workflow: TRANSCRIBE (demux → vad → asr only)"
} elseif ($Mode -eq "subtitle" -or $Subtitle) {
    $pythonArgs += "--subtitle-gen"
    Write-LogInfo "Workflow: SUBTITLE-GEN (all 13 stages)"
} else {
    # Default to subtitle-gen
    $pythonArgs += "--subtitle-gen"
    Write-LogInfo "Workflow: SUBTITLE-GEN (all 13 stages, default)"
}

# Always enable native mode (using .bollyenv)
$pythonArgs += "--native"

# Display execution info
Write-LogInfo "Input media: $InputMedia"
if ($StartTime -and $EndTime) {
    Write-LogInfo "Clip: $StartTime → $EndTime"
}

Write-Host ""

# ============================================================================
# Step 5: Execute prepare-job.py
# ============================================================================
Write-LogInfo "Executing: python $($pythonArgs -join ' ')"
Write-Host ""

try {
    $output = & python @pythonArgs 2>&1
    $output | ForEach-Object { Write-Host $_ }
    
    # Extract job ID from output
    $jobId = $null
    foreach ($line in $output) {
        if ($line -match "Job created: (.+)$") {
            $jobId = $matches[1].Trim()
            break
        }
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-LogSuccess "Job preparation completed successfully"
        Write-Host ""
        Write-LogInfo "Pipeline will execute these stages automatically:"
        if ($Mode -eq "transcribe" -or $Transcribe) {
            Write-LogInfo "  1. Demux (audio extraction)"
            Write-LogInfo "  2. Silero VAD (voice detection)"
            Write-LogInfo "  3. ASR (transcription)"
        } else {
            Write-LogInfo "  1. Demux (audio extraction)"
            Write-LogInfo "  2. TMDB (metadata fetch)"
            Write-LogInfo "  3. Pre-NER (entity extraction)"
            Write-LogInfo "  4. Silero VAD (voice detection)"
            Write-LogInfo "  5. PyAnnote VAD (voice refinement)"
            Write-LogInfo "  6. Diarization (speaker identification)"
            Write-LogInfo "  7. ASR (transcription)"
            Write-LogInfo "  8. Second Pass Translation (refinement)"
            Write-LogInfo "  9. Lyrics Detection (song identification)"
            Write-LogInfo "  10. Lyrics Translation (song translation)"
            Write-LogInfo "  11. Post-NER (name correction)"
            Write-LogInfo "  12. Subtitle Generation (SRT creation)"
            Write-LogInfo "  13. Mux (video embedding)"
        }
        Write-Host ""
        Write-LogInfo "Next step: Run the pipeline with the generated job ID"
        if ($jobId) {
            Write-LogInfo "  .\run_pipeline.ps1 -Job $jobId"
        } else {
            Write-LogInfo "  .\run_pipeline.ps1 -Job <job-id>"
        }
        Write-Host ""
    } else {
        Write-LogError "Job preparation failed with exit code $LASTEXITCODE"
        exit 1
    }
} catch {
    Write-LogError "Execution error: $_"
    exit 1
}

exit 0
