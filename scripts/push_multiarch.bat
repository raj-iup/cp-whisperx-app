@echo off
REM Build and push multi-arch images using docker buildx
REM Usage: set DOCKERHUB_USER=youruser && scripts\push_multiarch.bat [--skip-base]

setlocal enabledelayedexpansion

set SKIP_BASE=false

REM Parse arguments
:parse_args
if "%~1"=="" goto :check_user
if "%~1"=="--skip-base" (
    set SKIP_BASE=true
    shift
    goto :parse_args
)
echo Unknown argument: %~1
exit /b 1

:check_user
if "%DOCKERHUB_USER%"=="" (
    echo Please set DOCKERHUB_USER environment variable to your Docker Hub username.
    echo Example: set DOCKERHUB_USER=rajiup ^&^& %~nx0
    exit /b 1
)

set REGISTRY=%DOCKERHUB_USER%
set REPO_NAME=cp-whisperx-app

echo ========================================
echo Building Multi-Arch Docker Images
echo ========================================
echo Registry: %REGISTRY%
echo Skip Base: %SKIP_BASE%
echo.

echo Ensure you have a builder with QEMU enabled. If not, run:
echo   docker buildx create --use --name multiarch-builder --driver docker-container
echo   docker run --rm --privileged multiarch/qemu-user-static --reset -p yes
echo.

REM Build base images
if "%SKIP_BASE%"=="false" (
    echo === Building Multi-Arch Base Images ===
    
    echo Building + pushing multi-arch base:cpu...
    docker buildx build --platform linux/amd64,linux/arm64 ^
        -f "docker\base\Dockerfile" ^
        -t "%REGISTRY%/%REPO_NAME%-base:cpu" ^
        --push .
    if errorlevel 1 (
        echo [FAILED] base:cpu
        exit /b 1
    )
    
    echo Building + pushing multi-arch base:cuda...
    docker buildx build --platform linux/amd64 ^
        -f "docker\base-cuda\Dockerfile" ^
        -t "%REGISTRY%/%REPO_NAME%-base:cuda" ^
        --push .
    if errorlevel 1 (
        echo [FAILED] base:cuda
        exit /b 1
    )
    
    echo [SUCCESS] Base images built and pushed
    echo.
) else (
    echo Skipping base images...
    echo.
)

REM Build CPU stages
echo === Building Multi-Arch CPU Stages ===
for %%s in (demux tmdb pre-ner post-ner subtitle-gen mux) do (
    echo Building + pushing multi-arch %%s:cpu...
    docker buildx build --platform linux/amd64,linux/arm64 ^
        -f "docker\%%s\Dockerfile" ^
        -t "%REGISTRY%/%REPO_NAME%-%%s:cpu" ^
        --push .
    if errorlevel 1 (
        echo [FAILED] %%s:cpu
        exit /b 1
    )
)
echo.

REM Build GPU stages (CUDA only supports amd64)
echo === Building Multi-Arch GPU Stages (CUDA) ===
for %%s in (silero-vad pyannote-vad diarization asr second-pass-translation lyrics-detection) do (
    if exist "docker\%%s\Dockerfile" (
        echo Building + pushing %%s:cuda (amd64 only)...
        docker buildx build --platform linux/amd64 ^
            -f "docker\%%s\Dockerfile" ^
            -t "%REGISTRY%/%REPO_NAME%-%%s:cuda" ^
            --push .
        if errorlevel 1 (
            echo [FAILED] %%s:cuda
            exit /b 1
        )
    )
)

echo.
echo ========================================
echo Multi-arch build/push complete!
echo ========================================
endlocal
