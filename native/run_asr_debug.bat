@echo off
REM Run Stage 7: ASR in debug mode with detailed logging

setlocal

if "%~1"=="" (
    echo Usage: %~nx0 ^<movie_name^> [options]
    echo.
    echo Arguments:
    echo   movie_name    Name of the movie directory in .\out\
    echo.
    echo Options:
    echo   --model       Whisper model size (tiny, base, small, medium, large-v2, large-v3^) [default: base]
    echo   --language    Language code (e.g., en, hi, es^) [default: auto-detect]
    echo   --batch-size  Batch size for processing [default: 16]
    echo.
    echo Example:
    echo   %~nx0 My_Movie --model base --language en
    exit /b 1
)

set MOVIE_NAME=%~1
shift

set MOVIE_DIR=.\out\%MOVIE_NAME%
set VENV_PATH=native\venvs\asr
set SCRIPT_PATH=native\scripts\07_asr.py

REM Validate paths
if not exist "%MOVIE_DIR%" (
    echo [ERROR] Movie directory not found: %MOVIE_DIR%
    exit /b 1
)

if not exist "%VENV_PATH%" (
    echo [ERROR] Virtual environment not found: %VENV_PATH%
    echo Run native\setup_venvs.bat first
    exit /b 1
)

if not exist "%SCRIPT_PATH%" (
    echo [ERROR] Script not found: %SCRIPT_PATH%
    exit /b 1
)

REM Find input video
set INPUT_FILE=
for %%f in (.\in\*.mp4 .\in\*.mkv) do (
    set INPUT_FILE=%%f
    goto found_input
)
:found_input

if "%INPUT_FILE%"=="" (
    echo [WARNING] Could not find input video in .\in\
    echo Using placeholder path - adjust if needed
    set INPUT_FILE=.\in\video.mp4
)

echo ======================================================
echo DEBUG MODE: Stage 7 - ASR (Transcription + Alignment^)
echo ======================================================
echo Movie Directory: %MOVIE_DIR%
echo Virtual Env: %VENV_PATH%
echo Script: %SCRIPT_PATH%
echo Input: %INPUT_FILE%
echo Arguments: %*
echo ======================================================
echo.

REM Activate venv and set environment
call "%VENV_PATH%\Scripts\activate.bat"

set PYTHONPATH=%CD%;%CD%\shared;%CD%\native\utils;%PYTHONPATH%
set PYTORCH_ENABLE_MPS_FALLBACK=1
set LOG_LEVEL=DEBUG

echo Starting ASR stage in DEBUG mode...
echo Logs will be saved to: logs\asr_%MOVIE_NAME%_*.log
echo.

REM Run Python with verbose output
python -u "%SCRIPT_PATH%" --input "%INPUT_FILE%" --movie-dir "%MOVIE_DIR%" %*

set EXIT_CODE=%ERRORLEVEL%

echo.
echo ======================================================
if %EXIT_CODE%==0 (
    echo [SUCCESS] ASR stage completed successfully
) else (
    echo [FAILED] ASR stage failed with exit code: %EXIT_CODE%
)
echo ======================================================
echo.
echo Check detailed logs in: logs\
echo Output files in: %MOVIE_DIR%\transcription\
echo.

endlocal
exit /b %EXIT_CODE%
