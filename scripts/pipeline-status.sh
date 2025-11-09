#!/bin/bash
# Pipeline Status & Quick Reference
# Usage: ./scripts/pipeline-status.sh [job_id]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Check if job ID provided
JOB_ID="$1"

echo "======================================================"
echo "   CP-WhisperX Pipeline - Status & Reference"
echo "======================================================"
echo ""

# If job ID provided, show job-specific status
if [ -n "$JOB_ID" ]; then
    echo "📋 JOB STATUS: $JOB_ID"
    echo "────────────────────────────────────────────────────"
    
    # Find job directory
    YEAR="${JOB_ID:0:4}"
    MONTH="${JOB_ID:4:2}"
    DAY="${JOB_ID:6:2}"
    
    JOB_DIR="$PROJECT_ROOT/out/$YEAR/$MONTH/$DAY"
    JOB_PATH=""
    
    if [ -d "$JOB_DIR" ]; then
        for user_dir in "$JOB_DIR"/*; do
            if [ -d "$user_dir/$JOB_ID" ]; then
                JOB_PATH="$user_dir/$JOB_ID"
                break
            fi
        done
    fi
    
    if [ -z "$JOB_PATH" ]; then
        echo "  ❌ Job not found: $JOB_ID"
        echo ""
        exit 1
    fi
    
    echo "  📁 Location: $JOB_PATH"
    
    # Check manifest for stage status
    MANIFEST="$JOB_PATH/manifest.json"
    if [ -f "$MANIFEST" ]; then
        echo "  📊 Stage Progress:"
        echo ""
        
        # Define all stages
        STAGES=("demux" "tmdb" "pre_ner" "silero_vad" "pyannote_vad" "diarization" "asr" "second_pass_translation" "lyrics_detection" "post_ner" "subtitle_gen" "mux")
        
        for stage in "${STAGES[@]}"; do
            if command -v jq >/dev/null 2>&1; then
                STATUS=$(jq -r ".stages.\"$stage\".status // \"pending\"" "$MANIFEST" 2>/dev/null)
                COMPLETED=$(jq -r ".stages.\"$stage\".completed // false" "$MANIFEST" 2>/dev/null)
                
                # Check if stage is completed (either status="success" or completed=true)
                if [ "$STATUS" = "success" ] || [ "$COMPLETED" = "true" ]; then
                    printf "    ✓ %-25s [COMPLETED]\n" "$stage"
                elif [ "$STATUS" = "completed" ]; then
                    printf "    ✓ %-25s [COMPLETED]\n" "$stage"
                elif [ "$STATUS" = "failed" ] || [ "$STATUS" = "error" ]; then
                    printf "    ✗ %-25s [FAILED]\n" "$stage"
                elif [ "$STATUS" = "running" ] || [ "$STATUS" = "in_progress" ]; then
                    printf "    ⏳ %-25s [RUNNING]\n" "$stage"
                else
                    printf "    ○ %-25s [PENDING]\n" "$stage"
                fi
            else
                printf "    ? %-25s [UNKNOWN - jq not installed]\n" "$stage"
            fi
        done
    else
        echo "  ⚠️  Manifest not found (job not initialized)"
    fi
    echo ""
    echo "────────────────────────────────────────────────────"
    echo ""
fi

echo "📊 PIPELINE STAGES (12 Total - Sequential)"
echo "────────────────────────────────────────────────────"
echo "  1. demux                   → Extract 16kHz mono audio"
echo "  2. tmdb                    → Fetch movie metadata"
echo "  3. pre_ner                 → Extract entities for prompt"
echo "  4. silero_vad              → Coarse speech segmentation (ML)"
echo "  5. pyannote_vad            → Refined VAD boundaries (ML)"
echo "  6. diarization             → Speaker labeling (ML)"
echo "  7. asr                     → WhisperX transcription (ML)"
echo "  8. second_pass_translation → Improve translation quality (ML)"
echo "  9. lyrics_detection        → Detect & mark song sequences (ML)"
echo " 10. post_ner                → Entity correction"
echo " 11. subtitle_gen            → Generate .srt subtitles"
echo " 12. mux                     → Embed subtitles in MP4"
echo ""
echo "  Note: (ML) stages use GPU acceleration when available (MPS/CUDA)"
echo ""

echo "🚀 COMMON COMMANDS"
echo "────────────────────────────────────────────────────"
echo "  Setup environment:     ./scripts/bootstrap.sh"
echo "  Prepare job:           ./prepare-job.sh in/movie.mp4"
echo "  Run pipeline:          ./run_pipeline.sh --job <job_id>"
echo "  Resume pipeline:       ./resume-pipeline.sh <job_id>"
echo "  Check job status:      ./scripts/pipeline-status.sh <job_id>"
echo ""

echo "🔧 EXECUTION MODES"
echo "────────────────────────────────────────────────────"
echo "  macOS:   Native mode with MPS acceleration (.bollyenv)"
echo "  Windows: Native mode with CUDA/CPU (.bollyenv)"
echo "  Linux:   Docker mode with CUDA/CPU containers"
echo ""

echo "📁 OUTPUT STRUCTURE (Job-Based)"
echo "────────────────────────────────────────────────────"
echo "  out/YYYY/MM/DD/USER_ID/JOB_ID/"
echo "  ├── .JOB_ID.env              # Job configuration"
echo "  ├── job.json                 # Job metadata"
echo "  ├── manifest.json            # Stage tracking"
echo "  ├── audio/                   # Extracted audio"
echo "  │   └── audio.wav"
echo "  ├── metadata/                # TMDB data"
echo "  │   └── tmdb_data.json"
echo "  ├── prompts/                 # NER-enhanced prompts"
echo "  │   └── ner_enhanced_prompt.txt"
echo "  ├── entities/                # Entity extraction"
echo "  │   ├── pre_ner.json"
echo "  │   └── post_ner.json"
echo "  ├── vad/                     # Voice activity detection"
echo "  │   ├── silero_segments.json"
echo "  │   └── pyannote_segments.json"
echo "  ├── diarization/             # Speaker diarization"
echo "  │   └── speaker_segments.json"
echo "  ├── asr/                     # Transcription results"
echo "  │   └── transcript.json"
echo "  ├── translation/             # Second-pass translation"
echo "  │   └── refined_transcript.json"
echo "  ├── lyrics/                  # Lyrics detection"
echo "  │   └── lyrics_segments.json"
echo "  ├── subtitles/               # Generated subtitles"
echo "  │   └── subtitles.srt"
echo "  ├── logs/                    # Stage logs"
echo "  │   └── *.log"
echo "  └── final_output.mp4         # Muxed video (optional)"
echo ""

echo "⏱️  STAGE TIMEOUTS"
echo "────────────────────────────────────────────────────"
echo "  demux:         10 min   |  pre_ner:                  5 min"
echo "  tmdb:           2 min   |  silero_vad:              30 min"
echo "  pyannote_vad:  60 min   |  diarization:            120 min"
echo "  asr:          240 min   |  second_pass_translation:120 min"
echo "  lyrics:        30 min   |  post_ner:                20 min"
echo "  subtitle_gen:  10 min   |  mux:                     10 min"
echo ""

echo "💻 NATIVE EXECUTION EXAMPLES"
echo "────────────────────────────────────────────────────"
echo "  Run complete pipeline:"
echo "    ./run_pipeline.sh --job 20251108-0002"
echo ""
echo "  Resume from checkpoint:"
echo "    ./resume-pipeline.sh 20251108-0002"
echo ""
echo "  Run specific stages:"
echo "    ./run_pipeline.sh --job 20251108-0002 --stages \"asr subtitle_gen mux\""
echo ""
echo "  Fresh run (ignore resume):"
echo "    ./run_pipeline.sh --job 20251108-0002 --no-resume"
echo ""

echo "📖 DOCUMENTATION"
echo "────────────────────────────────────────────────────"
echo "  Quick Start:          README.md"
echo "  Setup Guide:          docs/BOOTSTRAP.md"
echo "  Architecture:         docs/ARCHITECTURE.md"
echo "  Workflow Details:     docs/WORKFLOW.md"
echo "  Recent Fixes:         DEVICE_AND_CACHE_FIX.md"
echo ""

echo "✅ Pipeline Ready!"
if [ -n "$JOB_ID" ]; then
    echo "   Resume: ./resume-pipeline.sh $JOB_ID"
else
    echo "   Next: ./prepare-job.sh in/your-movie.mp4"
fi
echo ""
