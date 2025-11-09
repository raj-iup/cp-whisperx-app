# Pipeline Status & Quick Reference (PowerShell)
# Usage: .\scripts\pipeline-status.ps1 [job_id]

param(
    [string]$JobId
)

$ProjectRoot = Split-Path -Parent $PSScriptRoot

Write-Host "======================================================"
Write-Host "   CP-WhisperX Pipeline - Status & Reference"
Write-Host "======================================================"
Write-Host ""

# If job ID provided, show job-specific status
if ($JobId) {
    Write-Host "📋 JOB STATUS: $JobId"
    Write-Host "────────────────────────────────────────────────────"
    
    # Parse job ID to find directory
    $Year = $JobId.Substring(0, 4)
    $Month = $JobId.Substring(4, 2)
    $Day = $JobId.Substring(6, 2)
    
    $JobDir = Join-Path $ProjectRoot "out\$Year\$Month\$Day"
    $JobPath = $null
    
    if (Test-Path $JobDir) {
        Get-ChildItem $JobDir -Directory | ForEach-Object {
            $TestPath = Join-Path $_.FullName $JobId
            if (Test-Path $TestPath) {
                $JobPath = $TestPath
            }
        }
    }
    
    if (-not $JobPath) {
        Write-Host "  ❌ Job not found: $JobId"
        Write-Host ""
        exit 1
    }
    
    Write-Host "  📁 Location: $JobPath"
    
    # Check manifest for stage status
    $ManifestPath = Join-Path $JobPath "manifest.json"
    if (Test-Path $ManifestPath) {
        Write-Host "  �� Stage Progress:"
        Write-Host ""
        
        $Manifest = Get-Content $ManifestPath | ConvertFrom-Json
        
        # Define all stages
        $Stages = @(
            "demux", "tmdb", "pre_ner", "silero_vad", "pyannote_vad", 
            "diarization", "asr", "second_pass_translation", 
            "lyrics_detection", "post_ner", "subtitle_gen", "mux"
        )
        
        foreach ($Stage in $Stages) {
            $StageData = $Manifest.stages.$Stage
            $Status = if ($StageData) { $StageData.status } else { "pending" }
            $Completed = if ($StageData) { $StageData.completed } else { $false }
            
            # Check if stage is completed (either status="success" or completed=true)
            if ($Status -eq "success" -or $Completed -eq $true) {
                Write-Host ("    ✓ {0,-25} [COMPLETED]" -f $Stage)
            }
            elseif ($Status -eq "completed") {
                Write-Host ("    ✓ {0,-25} [COMPLETED]" -f $Stage)
            }
            elseif ($Status -eq "failed" -or $Status -eq "error") {
                Write-Host ("    ✗ {0,-25} [FAILED]" -f $Stage)
            }
            elseif ($Status -eq "running" -or $Status -eq "in_progress") {
                Write-Host ("    ⏳ {0,-25} [RUNNING]" -f $Stage)
            }
            else {
                Write-Host ("    ○ {0,-25} [PENDING]" -f $Stage)
            }
        }
    }
    else {
        Write-Host "  ⚠️  Manifest not found (job not initialized)"
    }
    Write-Host ""
    Write-Host "────────────────────────────────────────────────────"
    Write-Host ""
}

Write-Host "📊 PIPELINE STAGES (12 Total - Sequential)"
Write-Host "────────────────────────────────────────────────────"
Write-Host "  1. demux                   → Extract 16kHz mono audio"
Write-Host "  2. tmdb                    → Fetch movie metadata"
Write-Host "  3. pre_ner                 → Extract entities for prompt"
Write-Host "  4. silero_vad              → Coarse speech segmentation (ML)"
Write-Host "  5. pyannote_vad            → Refined VAD boundaries (ML)"
Write-Host "  6. diarization             → Speaker labeling (ML)"
Write-Host "  7. asr                     → WhisperX transcription (ML)"
Write-Host "  8. second_pass_translation → Improve translation quality (ML)"
Write-Host "  9. lyrics_detection        → Detect & mark song sequences (ML)"
Write-Host " 10. post_ner                → Entity correction"
Write-Host " 11. subtitle_gen            → Generate .srt subtitles"
Write-Host " 12. mux                     → Embed subtitles in MP4"
Write-Host ""
Write-Host "  Note: (ML) stages use GPU acceleration when available (MPS/CUDA)"
Write-Host ""

Write-Host "🚀 COMMON COMMANDS"
Write-Host "────────────────────────────────────────────────────"
Write-Host "  Setup environment:     .\scripts\bootstrap.ps1"
Write-Host "  Prepare job:           .\prepare-job.ps1 in\movie.mp4"
Write-Host "  Run pipeline:          .\run_pipeline.ps1 -Job <job_id>"
Write-Host "  Resume pipeline:       .\resume-pipeline.ps1 <job_id>"
Write-Host "  Check job status:      .\scripts\pipeline-status.ps1 <job_id>"
Write-Host ""

Write-Host "🔧 EXECUTION MODES"
Write-Host "────────────────────────────────────────────────────"
Write-Host "  macOS:   Native mode with MPS acceleration (.bollyenv)"
Write-Host "  Windows: Native mode with CUDA/CPU (.bollyenv)"
Write-Host "  Linux:   Docker mode with CUDA/CPU containers"
Write-Host ""

Write-Host "📁 OUTPUT STRUCTURE (Job-Based)"
Write-Host "────────────────────────────────────────────────────"
Write-Host "  out\YYYY\MM\DD\USER_ID\JOB_ID\"
Write-Host "  ├── .JOB_ID.env              # Job configuration"
Write-Host "  ├── job.json                 # Job metadata"
Write-Host "  ├── manifest.json            # Stage tracking"
Write-Host "  ├── audio\                   # Extracted audio"
Write-Host "  │   └── audio.wav"
Write-Host "  ├── metadata\                # TMDB data"
Write-Host "  │   └── tmdb_data.json"
Write-Host "  ├── prompts\                 # NER-enhanced prompts"
Write-Host "  │   └── ner_enhanced_prompt.txt"
Write-Host "  ├── entities\                # Entity extraction"
Write-Host "  │   ├── pre_ner.json"
Write-Host "  │   └── post_ner.json"
Write-Host "  ├── vad\                     # Voice activity detection"
Write-Host "  │   ├── silero_segments.json"
Write-Host "  │   └── pyannote_segments.json"
Write-Host "  ├── diarization\             # Speaker diarization"
Write-Host "  │   └── speaker_segments.json"
Write-Host "  ├── asr\                     # Transcription results"
Write-Host "  │   └── transcript.json"
Write-Host "  ├── translation\             # Second-pass translation"
Write-Host "  │   └── refined_transcript.json"
Write-Host "  ├── lyrics\                  # Lyrics detection"
Write-Host "  │   └── lyrics_segments.json"
Write-Host "  ├── subtitles\               # Generated subtitles"
Write-Host "  │   └── subtitles.srt"
Write-Host "  ├── logs\                    # Stage logs"
Write-Host "  │   └── *.log"
Write-Host "  └── final_output.mp4         # Muxed video (optional)"
Write-Host ""

Write-Host "⏱️  STAGE TIMEOUTS"
Write-Host "────────────────────────────────────────────────────"
Write-Host "  demux:         10 min   |  pre_ner:                  5 min"
Write-Host "  tmdb:           2 min   |  silero_vad:              30 min"
Write-Host "  pyannote_vad:  60 min   |  diarization:            120 min"
Write-Host "  asr:          240 min   |  second_pass_translation:120 min"
Write-Host "  lyrics:        30 min   |  post_ner:                20 min"
Write-Host "  subtitle_gen:  10 min   |  mux:                     10 min"
Write-Host ""

Write-Host "💻 NATIVE EXECUTION EXAMPLES"
Write-Host "────────────────────────────────────────────────────"
Write-Host "  Run complete pipeline:"
Write-Host "    .\run_pipeline.ps1 -Job 20251108-0002"
Write-Host ""
Write-Host "  Resume from checkpoint:"
Write-Host "    .\resume-pipeline.ps1 20251108-0002"
Write-Host ""
Write-Host "  Run specific stages:"
Write-Host "    .\run_pipeline.ps1 -Job 20251108-0002 -Stages 'asr','subtitle_gen','mux'"
Write-Host ""
Write-Host "  Fresh run (ignore resume):"
Write-Host "    .\run_pipeline.ps1 -Job 20251108-0002 -NoResume"
Write-Host ""

Write-Host "📖 DOCUMENTATION"
Write-Host "────────────────────────────────────────────────────"
Write-Host "  Quick Start:          README.md"
Write-Host "  Setup Guide:          docs\BOOTSTRAP.md"
Write-Host "  Architecture:         docs\ARCHITECTURE.md"
Write-Host "  Workflow Details:     docs\WORKFLOW.md"
Write-Host "  Recent Fixes:         DEVICE_AND_CACHE_FIX.md"
Write-Host ""

if ($JobId) {
    Write-Host "✅ Pipeline Ready!"
    Write-Host "   Resume: .\resume-pipeline.ps1 $JobId"
}
