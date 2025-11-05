@echo off
REM Pull all Docker images from registry
REM This script pulls base images, CPU stages, and CUDA stages

setlocal enabledelayedexpansion

set REGISTRY=rajiup
set IMAGE_PREFIX=cp-whisperx-app

echo ========================================
echo   Docker Image Pull Script
echo ========================================
echo.
echo Registry: %REGISTRY%
echo Image Prefix: %IMAGE_PREFIX%
echo.

set ERROR_COUNT=0
set SUCCESS_COUNT=0

REM Function to pull image
:pull_image
set "IMAGE_TAG=%~1"
echo.
echo [PULLING] %REGISTRY%/%IMAGE_PREFIX%-%IMAGE_TAG%
docker pull %REGISTRY%/%IMAGE_PREFIX%-%IMAGE_TAG%
if %ERRORLEVEL% equ 0 (
    echo [SUCCESS] %IMAGE_TAG%
    set /a SUCCESS_COUNT+=1
) else (
    echo [FAILED] %IMAGE_TAG%
    set /a ERROR_COUNT+=1
)
goto :eof

echo.
echo === Phase 1: Pulling Base Images ===
echo.

call :pull_image "base:cpu"
call :pull_image "base:cuda"
call :pull_image "base-ml:cuda"

echo.
echo === Phase 2: Pulling CPU-Only Stage Images ===
echo.

call :pull_image "demux:cpu"
call :pull_image "tmdb:cpu"
call :pull_image "pre-ner:cpu"
call :pull_image "post-ner:cpu"
call :pull_image "subtitle-gen:cpu"
call :pull_image "mux:cpu"

echo.
echo === Phase 3: Pulling GPU Stage Images (CUDA variants) ===
echo.

call :pull_image "silero-vad:cuda"
call :pull_image "pyannote-vad:cuda"
call :pull_image "diarization:cuda"
call :pull_image "asr:cuda"
call :pull_image "second-pass-translation:cuda"
call :pull_image "lyrics-detection:cuda"

echo.
echo === Phase 4: Pulling GPU Stage Images (CPU fallback variants) ===
echo.

call :pull_image "silero-vad:cpu"
call :pull_image "pyannote-vad:cpu"
call :pull_image "diarization:cpu"
call :pull_image "asr:cpu"
call :pull_image "second-pass-translation:cpu"
call :pull_image "lyrics-detection:cpu"

echo.
echo ========================================
echo   Pull Summary
echo ========================================
echo.
echo Total images pulled successfully: %SUCCESS_COUNT%
echo Total images failed: %ERROR_COUNT%
echo.

if %ERROR_COUNT% gtr 0 (
    echo [WARNING] Some images failed to pull. Check the output above.
    exit /b 1
) else (
    echo [SUCCESS] All images pulled successfully!
    exit /b 0
)
