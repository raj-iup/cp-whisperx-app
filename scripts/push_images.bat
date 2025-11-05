@echo off
REM Push base + service images to Docker Hub (single-arch)
REM Usage: set DOCKERHUB_USER=youruser && scripts\push_images.bat [--no-push] [--skip-base]
REM Options:
REM   --no-push   : build locally but don't push (useful for testing)
REM   --skip-base : skip building/pushing base images

setlocal enabledelayedexpansion

set NO_PUSH=false
set SKIP_BASE=false

REM Parse arguments
:parse_args
if "%~1"=="" goto :check_user
if "%~1"=="--no-push" (
    set NO_PUSH=true
    shift
    goto :parse_args
)
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
echo Pushing Docker Images
echo ========================================
echo Registry: %REGISTRY%
echo No Push: %NO_PUSH%
echo Skip Base: %SKIP_BASE%
echo.

REM Push base images
if "%SKIP_BASE%"=="false" (
    echo === Pushing Base Images ===
    
    echo Building base:cpu...
    docker build -t "%REGISTRY%/%REPO_NAME%-base:cpu" -f "docker\base\Dockerfile" .
    if errorlevel 1 (
        echo [FAILED] base:cpu build
        exit /b 1
    )
    
    if "%NO_PUSH%"=="false" (
        echo Pushing base:cpu...
        docker push "%REGISTRY%/%REPO_NAME%-base:cpu"
        if errorlevel 1 (
            echo [FAILED] base:cpu push
            exit /b 1
        )
    )
    
    echo Building base:cuda...
    docker build -t "%REGISTRY%/%REPO_NAME%-base:cuda" -f "docker\base-cuda\Dockerfile" .
    if errorlevel 1 (
        echo [FAILED] base:cuda build
        exit /b 1
    )
    
    if "%NO_PUSH%"=="false" (
        echo Pushing base:cuda...
        docker push "%REGISTRY%/%REPO_NAME%-base:cuda"
        if errorlevel 1 (
            echo [FAILED] base:cuda push
            exit /b 1
        )
    )
    
    echo [SUCCESS] Base images processed
    echo.
) else (
    echo Skipping base images...
    echo.
)

REM Push CPU stages
echo === Pushing CPU Stages ===
for %%s in (demux tmdb pre-ner post-ner subtitle-gen mux) do (
    echo Processing %%s:cpu...
    docker build -t "%REGISTRY%/%REPO_NAME%-%%s:cpu" -f "docker\%%s\Dockerfile" .
    if errorlevel 1 (
        echo [FAILED] %%s:cpu build
        exit /b 1
    )
    
    if "%NO_PUSH%"=="false" (
        docker push "%REGISTRY%/%REPO_NAME%-%%s:cpu"
        if errorlevel 1 (
            echo [FAILED] %%s:cpu push
            exit /b 1
        )
    )
)
echo.

REM Push GPU stages (CUDA)
echo === Pushing GPU Stages (CUDA) ===
for %%s in (silero-vad pyannote-vad diarization asr second-pass-translation lyrics-detection) do (
    if exist "docker\%%s\Dockerfile" (
        echo Processing %%s:cuda...
        docker build -t "%REGISTRY%/%REPO_NAME%-%%s:cuda" -f "docker\%%s\Dockerfile" .
        if errorlevel 1 (
            echo [FAILED] %%s:cuda build
            exit /b 1
        )
        
        if "%NO_PUSH%"=="false" (
            docker push "%REGISTRY%/%REPO_NAME%-%%s:cuda"
            if errorlevel 1 (
                echo [FAILED] %%s:cuda push
                exit /b 1
            )
        )
    )
)
echo.

REM Push GPU stages (CPU fallback)
echo === Pushing GPU Stages (CPU Fallback) ===
for %%s in (silero-vad pyannote-vad diarization asr second-pass-translation lyrics-detection) do (
    if exist "docker\%%s\Dockerfile" (
        echo Processing %%s:cpu...
        REM Use modified Dockerfile for CPU variant
        powershell -Command "(Get-Content 'docker\%%s\Dockerfile') -replace 'base:cuda', 'base:cpu' | docker build -t '%REGISTRY%/%REPO_NAME%-%%s:cpu' -f - ."
        
        if "%NO_PUSH%"=="false" (
            docker push "%REGISTRY%/%REPO_NAME%-%%s:cpu"
            if errorlevel 1 (
                echo [FAILED] %%s:cpu push
                exit /b 1
            )
        )
    )
)

echo.
echo ========================================
echo All images processed successfully!
echo ========================================
endlocal
