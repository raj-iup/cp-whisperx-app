# CP-WhisperX-App Pipeline Status
# Quick reference for pipeline stages and commands

# Logging functions
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [pipeline-status] [$Level] $Message"
    
    switch ($Level) {
        "ERROR" { Write-Host $logMessage -ForegroundColor Red }
        "WARNING" { Write-Host $logMessage -ForegroundColor Yellow }
        "SUCCESS" { Write-Host $logMessage -ForegroundColor Green }
        default { Write-Host $logMessage }
    }
}

Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "CP-WHISPERX PIPELINE - QUICK REFERENCE" -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host ""

Write-Host "PIPELINE STAGES (Sequential)" -ForegroundColor Yellow
Write-Host ("-" * 60) -ForegroundColor Yellow
Write-Host "   1. demux          - Extract 16kHz mono audio" -ForegroundColor Gray
Write-Host "   2. tmdb           - Fetch movie metadata" -ForegroundColor Gray
Write-Host "   3. pre-ner        - Extract entities for prompt" -ForegroundColor Gray
Write-Host "   4. silero-vad     - Coarse speech segmentation" -ForegroundColor Gray
Write-Host "   5. pyannote-vad   - Refined VAD boundaries" -ForegroundColor Gray
Write-Host "   6. diarization    - Speaker labeling" -ForegroundColor Gray
Write-Host "   7. asr            - WhisperX transcription" -ForegroundColor Gray
Write-Host "   8. post-ner       - Entity correction" -ForegroundColor Gray
Write-Host "   9. subtitle-gen   - Generate .srt subtitles" -ForegroundColor Gray
Write-Host "  10. mux            - Embed subtitles in MP4" -ForegroundColor Gray
Write-Host ""

Write-Host "COMMON COMMANDS" -ForegroundColor Yellow
Write-Host ("-" * 60) -ForegroundColor Yellow
Write-Host "  Preflight check:       python preflight.py" -ForegroundColor Gray
Write-Host "  Build all images:      docker compose build" -ForegroundColor Gray
Write-Host "  Run complete pipeline: python pipeline.py in\movie.mp4" -ForegroundColor Gray
Write-Host "  Run single stage:      docker compose run --rm <stage> <args>" -ForegroundColor Gray
Write-Host ""

Write-Host "DOCKER IMAGES STATUS" -ForegroundColor Yellow
Write-Host ("-" * 60) -ForegroundColor Yellow
docker images | Select-String "cp-whisperx-app"
Write-Host ""

Write-Host "OUTPUT STRUCTURE" -ForegroundColor Yellow
Write-Host ("-" * 60) -ForegroundColor Yellow
Write-Host "  out\{Movie_Title}\" -ForegroundColor Gray
Write-Host "  +-- audio\audio.wav" -ForegroundColor Gray
Write-Host "  +-- metadata\tmdb_data.json" -ForegroundColor Gray
Write-Host "  +-- entities\pre_ner.json" -ForegroundColor Gray
Write-Host "  +-- vad\silero_segments.json" -ForegroundColor Gray
Write-Host "  +-- vad\pyannote_segments.json" -ForegroundColor Gray
Write-Host "  +-- diarization\speaker_segments.json" -ForegroundColor Gray
Write-Host "  +-- transcription\transcript.json" -ForegroundColor Gray
Write-Host "  +-- entities\post_ner.json" -ForegroundColor Gray
Write-Host "  +-- subtitles\subtitles.srt" -ForegroundColor Gray
Write-Host "  +-- final_output.mp4" -ForegroundColor Gray
Write-Host "  +-- manifest.json" -ForegroundColor Gray
Write-Host ""

Write-Host "STAGE TIMEOUTS" -ForegroundColor Yellow
Write-Host ("-" * 60) -ForegroundColor Yellow
Write-Host "  demux:        10 min  |  pre-ner:      5 min" -ForegroundColor Gray
Write-Host "  tmdb:          2 min  |  silero-vad:  30 min" -ForegroundColor Gray
Write-Host "  pyannote-vad: 60 min  |  diarization: 30 min" -ForegroundColor Gray
Write-Host "  asr:          60 min  |  post-ner:    10 min" -ForegroundColor Gray
Write-Host "  subtitle-gen:  5 min  |  mux:         10 min" -ForegroundColor Gray
Write-Host ""

Write-Host "INDIVIDUAL STAGE EXAMPLES" -ForegroundColor Yellow
Write-Host ("-" * 60) -ForegroundColor Yellow
Write-Host "  docker compose run --rm demux in\movie.mp4" -ForegroundColor Gray
Write-Host "  docker compose run --rm tmdb `"Movie Title`" 2024" -ForegroundColor Gray
Write-Host "  docker compose run --rm pre-ner out\Movie_Title" -ForegroundColor Gray
Write-Host "  docker compose run --rm asr out\Movie_Title" -ForegroundColor Gray
Write-Host "  docker compose run --rm mux in\movie.mp4 out\Movie_Title\subtitles\subtitles.srt out\Movie_Title\final.mp4" -ForegroundColor Gray
Write-Host ""

Write-Host "DOCUMENTATION" -ForegroundColor Yellow
Write-Host ("-" * 60) -ForegroundColor Yellow
Write-Host "  Full guide:     docs\PIPELINE_REBUILD.md" -ForegroundColor Gray
Write-Host "  Architecture:   arch\workflow-arch.txt" -ForegroundColor Gray
Write-Host "  Logs:           logs\" -ForegroundColor Gray
Write-Host ""

Write-Host "Ready to run pipeline!" -ForegroundColor Green
Write-Host "  Next: python pipeline.py in\your-movie.mp4" -ForegroundColor Yellow
Write-Host ""
