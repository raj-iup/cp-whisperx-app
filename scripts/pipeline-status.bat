@echo off
REM Pipeline Quick Reference - shows status and available commands

echo ======================================================
echo    CP-WhisperX Pipeline - Quick Reference
echo ======================================================
echo.

echo PIPELINE STAGES (Sequential)
echo ------------------------------------------------------
echo   1. demux          - Extract 16kHz mono audio
echo   2. tmdb           - Fetch movie metadata
echo   3. pre-ner        - Extract entities for prompt
echo   4. silero-vad     - Coarse speech segmentation
echo   5. pyannote-vad   - Refined VAD boundaries
echo   6. diarization    - Speaker labeling
echo   7. asr            - WhisperX transcription
echo   8. post-ner       - Entity correction
echo   9. subtitle-gen   - Generate .srt subtitles
echo  10. mux            - Embed subtitles in MP4
echo.

echo COMMON COMMANDS
echo ------------------------------------------------------
echo   Preflight check:       python preflight.py
echo   Build all images:      docker compose build
echo   Run complete pipeline: python pipeline.py in\movie.mp4
echo   Run single stage:      docker compose run --rm ^<stage^> ^<args^>
echo.

echo DOCKER IMAGES STATUS
echo ------------------------------------------------------
docker images | findstr "cp-whisperx-app"
echo.

echo OUTPUT STRUCTURE
echo ------------------------------------------------------
echo   out\{Movie_Title}\
echo   +-- audio\audio.wav
echo   +-- metadata\tmdb_data.json
echo   +-- entities\pre_ner.json
echo   +-- vad\silero_segments.json
echo   +-- vad\pyannote_segments.json
echo   +-- diarization\speaker_segments.json
echo   +-- transcription\transcript.json
echo   +-- entities\post_ner.json
echo   +-- subtitles\subtitles.srt
echo   +-- final_output.mp4
echo   +-- manifest.json
echo.

echo STAGE TIMEOUTS
echo ------------------------------------------------------
echo   demux:        10 min   ^|  pre-ner:      5 min
echo   tmdb:          2 min   ^|  silero-vad:  30 min
echo   pyannote-vad: 60 min   ^|  diarization: 30 min
echo   asr:          60 min   ^|  post-ner:    10 min
echo   subtitle-gen:  5 min   ^|  mux:         10 min
echo.

echo INDIVIDUAL STAGE EXAMPLES
echo ------------------------------------------------------
echo   docker compose run --rm demux in\movie.mp4
echo   docker compose run --rm tmdb "Movie Title" 2024
echo   docker compose run --rm pre-ner out\Movie_Title
echo   docker compose run --rm asr out\Movie_Title
echo   docker compose run --rm mux in\movie.mp4 out\Movie_Title\subtitles\subtitles.srt out\Movie_Title\final.mp4
echo.

echo DOCUMENTATION
echo ------------------------------------------------------
echo   Full guide:     docs\PIPELINE_REBUILD.md
echo   Architecture:   arch\workflow-arch.txt
echo   Logs:           logs\
echo.

echo Ready to run pipeline!
echo    Next: python pipeline.py in\your-movie.mp4
echo.
