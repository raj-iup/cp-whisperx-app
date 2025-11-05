@echo off
REM MPS-optimized native pipeline orchestrator

setlocal enabledelayedexpansion

set INPUT_FILE=%~1
set OUTPUT_ROOT=.\out
set VENV_DIR=native\venvs
set SCRIPT_DIR=native\scripts

REM Validate input
if "%INPUT_FILE%"=="" (
    echo ERROR: Usage: %~nx0 ^<input_video.mp4^>
    echo Example: %~nx0 in\movie.mp4
    exit /b 1
)

if not exist "%INPUT_FILE%" (
    echo ERROR: Input file not found: %INPUT_FILE%
    exit /b 1
)

REM Extract movie directory name
for %%f in ("%INPUT_FILE%") do set MOVIE_NAME=%%~nf
set MOVIE_NAME=%MOVIE_NAME: =_%
set MOVIE_DIR=%OUTPUT_ROOT%\%MOVIE_NAME%
if not exist "%MOVIE_DIR%" mkdir "%MOVIE_DIR%"

echo ======================================================
echo MPS Native Pipeline
echo ======================================================
echo Input: %INPUT_FILE%
echo Output: %MOVIE_DIR%
echo Mode: Sequential execution with GPU acceleration
echo.

REM Stage definitions
set stages[0]=demux:01_demux.py:Audio extraction
set stages[1]=tmdb:02_tmdb.py:Metadata fetch
set stages[2]=pre-ner:03_pre_ner.py:Entity extraction
set stages[3]=silero-vad:04_silero_vad.py:Coarse VAD
set stages[4]=pyannote-vad:05_pyannote_vad.py:Refined VAD
set stages[5]=diarization:06_diarization.py:Speaker labeling
set stages[6]=asr:07_asr.py:Transcription + translation
set stages[7]=post-ner:08_post_ner.py:Entity correction
set stages[8]=subtitle-gen:09_subtitle_gen.py:Subtitle generation
set stages[9]=mux:10_mux.py:Video muxing

set total=10
set current=0

REM Run stages sequentially
for /l %%i in (0,1,9) do (
    set /a current=%%i+1
    
    REM Parse stage info
    for /f "tokens=1,2,3 delims=:" %%a in ("!stages[%%i]!") do (
        set stage_name=%%a
        set script_name=%%b
        set description=%%c
        
        echo.
        echo ======================================================
        echo Stage !current!/%total%: !stage_name!
        echo ======================================================
        echo !description!
        
        set venv_path=%VENV_DIR%\!stage_name!
        set script_path=%SCRIPT_DIR%\!script_name!
        
        if not exist "!venv_path!" (
            echo [ERROR] Virtual environment not found: !venv_path!
            echo Run native\setup_venvs.bat first
            exit /b 1
        )
        
        if not exist "!script_path!" (
            echo [ERROR] Script not found: !script_path!
            exit /b 1
        )
        
        echo Running: !script_name!
        
        call "!venv_path!\Scripts\activate.bat"
        set PYTHONPATH=%CD%;%CD%\shared;%CD%\native\utils;!PYTHONPATH!
        
        python "!script_path!" --input "%INPUT_FILE%" --movie-dir "%MOVIE_DIR%"
        
        if errorlevel 1 (
            echo [FAILED] Stage !stage_name! failed
            exit /b 1
        )
        
        echo [SUCCESS] Stage !stage_name! completed
    )
)

echo.
echo ======================================================
echo Pipeline Complete
echo ======================================================
echo Output: %MOVIE_DIR%
echo.

endlocal
exit /b 0
