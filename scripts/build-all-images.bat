@echo off
REM Build all Docker images for cp-whisperx-app pipeline
REM New Tagging Strategy:
REM - CPU-Only Stages: :cpu tag (built from base:cpu)
REM - GPU Stages: :cuda tag (built from base:cuda)

setlocal enabledelayedexpansion

REM Configuration
if "%DOCKERHUB_USER%"=="" (
    set REGISTRY=rajiup
) else (
    set REGISTRY=%DOCKERHUB_USER%
)
set REPO_NAME=cp-whisperx-app

echo ========================================
echo CP-WhisperX-App Docker Image Builder
echo ========================================
echo.
echo Registry: %REGISTRY%
echo Repository: %REPO_NAME%
echo.
echo Tagging Strategy:
echo   CPU-Only Stages: :cpu (from base:cpu)
echo   GPU Stages: :cuda (from base:cuda)
echo.

REM Track failures
set FAILED_COUNT=0
set FAILED_LIST=

echo === Phase 1: Building Base Images ===
echo.
echo [INFO] Building base images in dependency order:
echo [INFO]   1. base:cpu - CPU-only base
echo [INFO]   2. base:cuda - CUDA base with Python 3.11
echo [INFO]   3. base-ml:cuda - ML base with PyTorch (inherits from base:cuda)
echo [INFO] All other images will reference these base images
echo.

REM Build CPU base
echo Building: %REGISTRY%/%REPO_NAME%-base:cpu
docker build --build-arg REGISTRY=%REGISTRY% -t "%REGISTRY%/%REPO_NAME%-base:cpu" -f "docker\base\Dockerfile" .
if errorlevel 1 (
    echo [FAILED] base:cpu
    echo [ERROR] Cannot proceed without base:cpu image!
    echo [ERROR] All CPU stages require base:cpu
    set /a FAILED_COUNT+=1
    set "FAILED_LIST=!FAILED_LIST! base:cpu"
    goto :error_exit
) else (
    echo [SUCCESS] Built: %REGISTRY%/%REPO_NAME%-base:cpu
)
echo.

REM Build CUDA base
echo Building: %REGISTRY%/%REPO_NAME%-base:cuda
docker build --build-arg REGISTRY=%REGISTRY% -t "%REGISTRY%/%REPO_NAME%-base:cuda" -f "docker\base-cuda\Dockerfile" .
if errorlevel 1 (
    echo [FAILED] base:cuda
    echo [ERROR] Cannot proceed without base:cuda image!
    echo [ERROR] base-ml:cuda requires base:cuda
    set /a FAILED_COUNT+=1
    set "FAILED_LIST=!FAILED_LIST! base:cuda"
    goto :error_exit
) else (
    echo [SUCCESS] Built: %REGISTRY%/%REPO_NAME%-base:cuda
)
echo.

REM Build ML base
echo Building: %REGISTRY%/%REPO_NAME%-base-ml:cuda (ML base with PyTorch)
echo [INFO] This image includes PyTorch 2.1.0 + common ML packages
echo [INFO] Saves 10-15 GB by installing PyTorch once instead of per-stage
docker build --build-arg REGISTRY=%REGISTRY% -t "%REGISTRY%/%REPO_NAME%-base-ml:cuda" -f "docker\base-ml\Dockerfile" .
if errorlevel 1 (
    echo [FAILED] base-ml:cuda
    echo [ERROR] Cannot proceed without base-ml:cuda image!
    echo [ERROR] All GPU stages require base-ml:cuda
    set /a FAILED_COUNT+=1
    set "FAILED_LIST=!FAILED_LIST! base-ml:cuda"
    goto :error_exit
) else (
    echo [SUCCESS] Built: %REGISTRY%/%REPO_NAME%-base-ml:cuda
)
echo.

echo [SUCCESS] All base images built successfully!
echo [INFO] Subsequent GPU stage builds will inherit PyTorch from base-ml
echo.

echo === Phase 2: Building CPU-Only Stages ===
echo (demux, tmdb, pre-ner, post-ner, subtitle-gen, mux)
echo.

REM CPU-only stages - built from base:cpu
for %%s in (demux tmdb pre-ner post-ner subtitle-gen mux) do (
    echo Building: %REGISTRY%/%REPO_NAME%-%%s:cpu
    docker build --build-arg REGISTRY=%REGISTRY% -t "%REGISTRY%/%REPO_NAME%-%%s:cpu" -f "docker\%%s\Dockerfile" .
    if errorlevel 1 (
        echo [FAILED] %%s:cpu
        set /a FAILED_COUNT+=1
        set "FAILED_LIST=!FAILED_LIST! %%s:cpu"
    ) else (
        echo [SUCCESS] Built: %REGISTRY%/%REPO_NAME%-%%s:cpu
    )
    echo.
)

echo === Phase 3: Building GPU Stages (CUDA variants) ===
echo (silero-vad, pyannote-vad, diarization, asr, and optional stages)
echo.

REM GPU stages - built from base:cuda with CUDA PyTorch
for %%s in (silero-vad pyannote-vad diarization asr second-pass-translation lyrics-detection) do (
    if exist "docker\%%s\Dockerfile" (
        echo Building: %REGISTRY%/%REPO_NAME%-%%s:cuda
        docker build --build-arg REGISTRY=%REGISTRY% -t "%REGISTRY%/%REPO_NAME%-%%s:cuda" -f "docker\%%s\Dockerfile" .
        if errorlevel 1 (
            echo [FAILED] %%s:cuda
            set /a FAILED_COUNT+=1
            set "FAILED_LIST=!FAILED_LIST! %%s:cuda"
        ) else (
            echo [SUCCESS] Built: %REGISTRY%/%REPO_NAME%-%%s:cuda
        )
        echo.
    ) else (
        echo [WARNING] Skipping %%s - Dockerfile not found
        echo.
    )
)

echo === Phase 4: Building GPU Stages (CPU fallback variants) ===
echo (Same stages with CPU-only PyTorch for fallback)
echo.

REM GPU stages - CPU fallback variants built from base:cpu
for %%s in (silero-vad pyannote-vad diarization asr second-pass-translation lyrics-detection) do (
    if exist "docker\%%s\Dockerfile.cpu" (
        echo Building: %REGISTRY%/%REPO_NAME%-%%s:cpu
        docker build --build-arg REGISTRY=%REGISTRY% -t "%REGISTRY%/%REPO_NAME%-%%s:cpu" -f "docker\%%s\Dockerfile.cpu" .
        if errorlevel 1 (
            echo [FAILED] %%s:cpu
            set /a FAILED_COUNT+=1
            set "FAILED_LIST=!FAILED_LIST! %%s:cpu"
        ) else (
            echo [SUCCESS] Built: %REGISTRY%/%REPO_NAME%-%%s:cpu
        )
        echo.
    ) else (
        echo [WARNING] Skipping %%s:cpu - Dockerfile.cpu not found
        echo [INFO] Creating CPU variant from main Dockerfile with base:cpu
        
        REM Temporarily modify Dockerfile to use base:cpu
        powershell -Command "(Get-Content 'docker\%%s\Dockerfile') -replace 'base-ml:cuda', 'base:cpu' -replace 'base:cuda', 'base:cpu' | docker build --build-arg REGISTRY=%REGISTRY% -t '%REGISTRY%/%REPO_NAME%-%%s:cpu' -f - ."
        
        if errorlevel 1 (
            echo [FAILED] %%s:cpu
            set /a FAILED_COUNT+=1
            set "FAILED_LIST=!FAILED_LIST! %%s:cpu"
        ) else (
            echo [SUCCESS] Built: %REGISTRY%/%REPO_NAME%-%%s:cpu ^(fallback^)
        )
        echo.
    )
)

REM Summary
echo ========================================
echo Build Summary
echo ========================================
echo.

if %FAILED_COUNT%==0 (
    echo [SUCCESS] All images built successfully!
    echo.
    echo Image Summary:
    echo   Base images: base:cpu, base:cuda
    echo   CPU-only stages ^(6^): demux, tmdb, pre-ner, post-ner, subtitle-gen, mux
    echo   GPU stages with fallback ^(4-6^):
    echo     - silero-vad:cuda + silero-vad:cpu
    echo     - pyannote-vad:cuda + pyannote-vad:cpu
    echo     - diarization:cuda + diarization:cpu
    echo     - asr:cuda + asr:cpu
    echo     - [optional] second-pass-translation:cuda + :cpu
    echo     - [optional] lyrics-detection:cuda + :cpu
    echo.
    for /f %%i in ('docker images ^| findstr /C:"%REGISTRY%/%REPO_NAME%" ^| find /c /v ""') do echo Total images built: %%i
    echo.
    echo Next steps:
    echo   1. Test GPU images: docker compose run --rm --gpus all asr
    echo   2. Test CPU fallback: docker compose run --rm asr
    echo   3. Push to registry: scripts\push-all-images.bat
    echo.
) else (
    echo [FAILED] %FAILED_COUNT% builds failed:
    echo %FAILED_LIST%
    echo.
    exit /b 1
)

goto :eof

:error_exit
echo.
echo [CRITICAL ERROR] Base image build failed!
echo [INFO] Cannot continue without base images.
echo.
echo Base images are required by:
echo   - base:cpu required for: demux, tmdb, pre-ner, post-ner, subtitle-gen, mux
echo   - base:cpu required for: GPU stage CPU fallbacks
echo   - base:cuda required for: GPU stage CUDA variants
echo.
echo Please fix the base image build errors and try again.
echo.
exit /b 1

endlocal
