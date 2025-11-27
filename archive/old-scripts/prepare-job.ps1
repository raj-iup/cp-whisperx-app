# CP-WhisperX-App Job Preparation Script (PowerShell)
# Phase 1 Enhancement: Uses existing .bollyenv, hardware cache, no temp venv
# Windows Default: CUDA acceleration when available

[CmdletBinding()]
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
    [switch]$TranscribeOnly,
    
    [Parameter(Mandatory=$false)]
    [switch]$TranslateOnly,
    
    [Parameter(Mandatory=$false)]
    [switch]$SubtitleGen,
    
    [Parameter(Mandatory=$false)]
    [string]$SourceLanguage,
    
    [Parameter(Mandatory=$false)]
    [string]$TargetLanguage,
    
    [Parameter(Mandatory=$false)]
    [switch]$Native,
    
    [Parameter(Mandatory=$false)]
    [switch]$EnableSileroVad,
    
    [Parameter(Mandatory=$false)]
    [switch]$DisableSileroVad,
    
    [Parameter(Mandatory=$false)]
    [switch]$EnablePyannoteVad,
    
    [Parameter(Mandatory=$false)]
    [switch]$DisablePyannoteVad,
    
    [Parameter(Mandatory=$false)]
    [switch]$EnableDiarization,
    
    [Parameter(Mandatory=$false)]
    [switch]$DisableDiarization,
    
    [Parameter(Mandatory=$false)]
    [switch]$Help
)

$ErrorActionPreference = "Stop"

# Load common logging
. "$PSScriptRoot\scripts\common-logging.ps1"

# Show usage
if ($Help) {
    Write-Host @"
Usage: .\prepare-job.ps1 <input_media> [OPTIONS]

Prepare a job for the CP-WhisperX-App pipeline (Windows - CUDA optimized)

ARGUMENTS:
  -InputMedia <path>       Path to input media file (MP4, MKV, AVI, etc.)

OPTIONS:
  -Help                    Show this help message
  -StartTime <time>        Start time for clip (HH:MM:SS format)
  -EndTime <time>          End time for clip (HH:MM:SS format)

WORKFLOW MODES:
  -Transcribe              Transcribe-only workflow - minimal (3 stages)
  -TranscribeOnly          Transcription-only workflow (6 stages, includes VAD)
  -TranslateOnly           Translation-only workflow (9 stages, reuses transcription)
  -SubtitleGen             Full subtitle workflow (default, 15 stages)
  -Native                  Enable native GPU acceleration (auto-detects CUDA/CPU)

LANGUAGE OPTIONS:
  -SourceLanguage <code>   Source language (e.g., hi, es, ja, fr, de, auto)
  -TargetLanguage <code>   Target language (e.g., en, es, fr, de)
                           Required for -TranslateOnly
                           
  Supported: 96 languages including:
    auto (Auto-detect), hi (Hindi), en (English), es (Spanish),
    fr (French), de (German), it (Italian), ja (Japanese),
    ko (Korean), zh (Chinese), ar (Arabic), pt (Portuguese), etc.

STAGE CONTROL:
  -EnableSileroVad         Enable Silero VAD stage (default: enabled)
  -DisableSileroVad        Disable Silero VAD stage
  -EnablePyannoteVad       Enable PyAnnote VAD stage (default: enabled)
  -DisablePyannoteVad      Disable PyAnnote VAD stage
  -EnableDiarization       Enable Diarization stage (default: enabled)
  -DisableDiarization      Disable Diarization stage

EXAMPLES:
  # Default: Full Hindi → English subtitle generation (backward compatible)
  .\prepare-job.ps1 C:\videos\movie.mp4

  # Spanish to English (full pipeline)
  .\prepare-job.ps1 C:\videos\movie.mp4 -SourceLanguage es -TargetLanguage en
  .\prepare-job.ps1 C:\videos\movie.mp4 -SubtitleGen -SourceLanguage es -TargetLanguage en

  # Japanese to French (full pipeline)
  .\prepare-job.ps1 C:\videos\anime.mp4 -SourceLanguage ja -TargetLanguage fr

  # Multi-language workflow (transcribe once, translate many times)
  .\prepare-job.ps1 C:\videos\anime.mp4 -TranscribeOnly -SourceLanguage ja
  .\prepare-job.ps1 C:\videos\anime.mp4 -TranslateOnly -SourceLanguage ja -TargetLanguage en
  .\prepare-job.ps1 C:\videos\anime.mp4 -TranslateOnly -SourceLanguage ja -TargetLanguage es
  .\prepare-job.ps1 C:\videos\anime.mp4 -TranslateOnly -SourceLanguage ja -TargetLanguage fr

  # Auto-detect source language
  .\prepare-job.ps1 C:\videos\movie.mp4 -TranscribeOnly

  # Enable native GPU acceleration (CUDA on Windows)
  .\prepare-job.ps1 C:\videos\movie.mp4 -Native

  # Process 5-minute clip for testing
  .\prepare-job.ps1 C:\videos\movie.mp4 -StartTime 00:10:00 -EndTime 00:15:00

WORKFLOW COMPARISON:
  Mode           Languages         Stages  Time  Output
  -SubtitleGen   any → any (hi→en) 15      100%  Subtitled video file
  -TranscribeOnly any              6       40%   Source transcript (JSON)
  -TranslateOnly any → any         9       60%   Target subtitles (SRT)
  -Transcribe    any               3       20%   Raw transcription

PERFORMANCE TIPS:
  - Use -TranscribeOnly for transcription (40% time, outputs segments.json)
  - Use -TranslateOnly to reuse transcription (60% time, no audio processing)
  - Generate 3 subtitle tracks in 160% time vs 300% (transcribe once, translate 3x)
  - Use -Native for GPU acceleration (CUDA on Windows with NVIDIA GPU)

For more information, see: docs\QUICKSTART.md

"@
    exit 0
}
  14. Subtitle Gen       - SRT creation
  15. MUX                - Video embedding
  16. Finalize           - Output organization

For more information, see: docs\QUICKSTART.md

"@
    exit 0
}

Write-LogSection "CP-WHISPERX-APP JOB PREPARATION (OPTIMIZED - CUDA)"

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

if (-not $InputMedia) {
    Write-LogError "No input media specified"
    Write-Host ""
    Write-Host "Usage: .\prepare-job.ps1 <input_media> [options]"
    Write-Host "Run '.\prepare-job.ps1 -Help' for more information"
    exit 1
}

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
    $pythonArgs += "--start-time"
    $pythonArgs += $StartTime
}

if ($EndTime) {
    $pythonArgs += "--end-time"
    $pythonArgs += $EndTime
}

# Add workflow mode
if ($Transcribe) {
    $pythonArgs += "--transcribe"
    $workflow = "transcribe"
    Write-LogInfo "Workflow: TRANSCRIBE (minimal, 3 stages)"
} elseif ($TranscribeOnly) {
    $pythonArgs += "--transcribe-only"
    $workflow = "transcribe-only"
    Write-LogInfo "Workflow: TRANSCRIBE-ONLY (6 stages with VAD)"
} elseif ($TranslateOnly) {
    $pythonArgs += "--translate-only"
    $workflow = "translate-only"
    Write-LogInfo "Workflow: TRANSLATE-ONLY (9 stages, reuses transcription)"
} else {
    $pythonArgs += "--subtitle-gen"
    $workflow = "subtitle-gen"
    Write-LogInfo "Workflow: SUBTITLE-GEN (15 stages, default)"
}

# Add language arguments
if ($SourceLanguage) {
    $pythonArgs += "--source-language"
    $pythonArgs += $SourceLanguage
    Write-LogInfo "Source language: $SourceLanguage"
}

if ($TargetLanguage) {
    $pythonArgs += "--target-language"
    $pythonArgs += $TargetLanguage
    Write-LogInfo "Target language: $TargetLanguage"
}

# Add stage control flags
if ($EnableSileroVad) {
    $pythonArgs += "--enable-silero-vad"
    Write-LogInfo "Stage control: Silero VAD ENABLED"
} elseif ($DisableSileroVad) {
    $pythonArgs += "--disable-silero-vad"
    Write-LogInfo "Stage control: Silero VAD DISABLED"
}

if ($EnablePyannoteVad) {
    $pythonArgs += "--enable-pyannote-vad"
    Write-LogInfo "Stage control: PyAnnote VAD ENABLED"
} elseif ($DisablePyannoteVad) {
    $pythonArgs += "--disable-pyannote-vad"
    Write-LogInfo "Stage control: PyAnnote VAD DISABLED"
}

if ($EnableDiarization) {
    $pythonArgs += "--enable-diarization"
    Write-LogInfo "Stage control: Diarization ENABLED"
} elseif ($DisableDiarization) {
    $pythonArgs += "--disable-diarization"
    Write-LogInfo "Stage control: Diarization DISABLED"
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

# Execute and capture output
$output = & python $pythonArgs 2>&1 | Out-String
$exitCode = $LASTEXITCODE

# Display output
Write-Host $output

if ($exitCode -eq 0) {
    # Extract job ID from output
    $jobId = ""
    if ($output -match "Job created:\s+(.+)") {
        $jobId = $matches[1].Trim()
    }
    
    Write-Host ""
    Write-LogSuccess "Job preparation completed successfully"
    Write-Host ""
    Write-LogInfo "Pipeline will execute these stages automatically:"
    
    $stageNum = 1
    if ($workflow -eq "transcribe") {
        # Minimal transcription: 3 stages
        Write-LogInfo "  ${stageNum}. Demux (audio extraction)"
        $stageNum++
        
        if (-not $DisableSileroVad) {
            Write-LogInfo "  ${stageNum}. Silero VAD (voice detection)"
        } else {
            Write-LogInfo "  ${stageNum}. Silero VAD (voice detection) [SKIPPED]"
        }
        $stageNum++
        
        Write-LogInfo "  ${stageNum}. ASR (transcription)"
        
    } elseif ($workflow -eq "transcribe-only") {
        # Transcription with VAD: 6 stages
        Write-LogInfo "  ${stageNum}. Demux (audio extraction)"
        $stageNum++
        
        Write-LogInfo "  ${stageNum}. TMDB (metadata fetch)"
        $stageNum++
        
        Write-LogInfo "  ${stageNum}. Pre-NER (entity extraction)"
        $stageNum++
        
        if (-not $DisableSileroVad) {
            Write-LogInfo "  ${stageNum}. Silero VAD (voice detection)"
        } else {
            Write-LogInfo "  ${stageNum}. Silero VAD (voice detection) [SKIPPED]"
        }
        $stageNum++
        
        if (-not $DisablePyannoteVad) {
            Write-LogInfo "  ${stageNum}. PyAnnote VAD (voice refinement)"
        } else {
            Write-LogInfo "  ${stageNum}. PyAnnote VAD (voice refinement) [SKIPPED]"
        }
        $stageNum++
        
        Write-LogInfo "  ${stageNum}. ASR (transcription with character bias)"
        
    } elseif ($workflow -eq "translate-only") {
        # Translation only: 9 stages (reuses existing transcription)
        Write-LogInfo "  ${stageNum}. TMDB (metadata fetch)"
        $stageNum++
        
        Write-LogInfo "  ${stageNum}. Song Bias Injection (song/artist corrections)"
        $stageNum++
        
        Write-LogInfo "  ${stageNum}. Lyrics Detection (song identification)"
        $stageNum++
        
        Write-LogInfo "  ${stageNum}. Bias Correction (post-processing)"
        $stageNum++
        
        if (-not $DisableDiarization) {
            Write-LogInfo "  ${stageNum}. Diarization (speaker identification)"
        } else {
            Write-LogInfo "  ${stageNum}. Diarization (speaker identification) [SKIPPED]"
        }
        $stageNum++
        
        Write-LogInfo "  ${stageNum}. Glossary Builder (term management)"
        $stageNum++
        
        Write-LogInfo "  ${stageNum}. Second Pass Translation (refinement)"
        $stageNum++
        
        Write-LogInfo "  ${stageNum}. Post-NER (name correction)"
        $stageNum++
        
        Write-LogInfo "  ${stageNum}. Subtitle Generation (SRT creation)"
        $stageNum++
        
        Write-LogInfo "  ${stageNum}. MUX (video embedding)"
        
    } else {
        # Full subtitle-gen workflow: 15 stages
        Write-LogInfo "  ${stageNum}. Demux (audio extraction)"
        $stageNum++
        
        Write-LogInfo "  ${stageNum}. TMDB (metadata fetch)"
        $stageNum++
        
        Write-LogInfo "  ${stageNum}. Pre-NER (entity extraction)"
        $stageNum++
        
        if (-not $DisableSileroVad) {
            Write-LogInfo "  ${stageNum}. Silero VAD (voice detection)"
        } else {
            Write-LogInfo "  ${stageNum}. Silero VAD (voice detection) [SKIPPED]"
        }
        $stageNum++
        
        if (-not $DisablePyannoteVad) {
            Write-LogInfo "  ${stageNum}. PyAnnote VAD (voice refinement)"
        } else {
            Write-LogInfo "  ${stageNum}. PyAnnote VAD (voice refinement) [SKIPPED]"
        }
        $stageNum++
        
        Write-LogInfo "  ${stageNum}. ASR (transcription with character bias)"
        $stageNum++
        
        Write-LogInfo "  ${stageNum}. Song Bias Injection (song/artist corrections)"
        $stageNum++
        
        Write-LogInfo "  ${stageNum}. Lyrics Detection (song identification)"
        $stageNum++
        
        Write-LogInfo "  ${stageNum}. Bias Correction (post-processing)"
        $stageNum++
        
        if (-not $DisableDiarization) {
            Write-LogInfo "  ${stageNum}. Diarization (speaker identification)"
        } else {
            Write-LogInfo "  ${stageNum}. Diarization (speaker identification) [SKIPPED]"
        }
        $stageNum++
        
        Write-LogInfo "  ${stageNum}. Glossary Builder (term management)"
        $stageNum++
        
        Write-LogInfo "  ${stageNum}. Second Pass Translation (refinement)"
        $stageNum++
        
        Write-LogInfo "  ${stageNum}. Post-NER (name correction)"
        $stageNum++
        
        Write-LogInfo "  ${stageNum}. Subtitle Generation (SRT creation)"
        $stageNum++
        
        Write-LogInfo "  ${stageNum}. MUX (video embedding)"
    }
    
    Write-Host ""
    Write-LogInfo "Next step: Run the pipeline with the generated job ID"
    if ($jobId) {
        Write-LogInfo "  .\run_pipeline.ps1 -Job $jobId"
    } else {
        Write-LogInfo "  .\run_pipeline.ps1 -Job <job-id>"
    }
    Write-Host ""
    exit 0
} else {
    Write-Host ""
    Write-LogError "Job preparation failed with exit code $exitCode"
    exit $exitCode
}
