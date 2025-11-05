@echo off
REM Build all Docker images for cp-whisperx-app pipeline

setlocal enabledelayedexpansion

REM Load configuration
if exist "config\.env" (
    for /f "usebackq tokens=1,* delims==" %%a in (`findstr /V /C:"#" config\.env`) do (
        set "%%a=%%b"
    )
)

REM Set defaults
if "%DOCKER_REGISTRY%"=="" set DOCKER_REGISTRY=rajiup
if "%DOCKER_TAG%"=="" set DOCKER_TAG=latest

set REGISTRY=%DOCKER_REGISTRY%
set TAG=%DOCKER_TAG%

echo ======================================================
echo   CP-WHISPERX-APP DOCKER IMAGE BUILD
echo ======================================================
echo Registry: %REGISTRY%
echo Tag: %TAG%
echo.

REM Build base image first
echo [1/11] Building base image...
docker build -t %REGISTRY%/cp-whisperx-app-base:%TAG% -f docker\base\Dockerfile .
if errorlevel 1 exit /b 1
echo [SUCCESS] Base image built
echo.

REM Build all service images
set SERVICES=demux tmdb pre-ner silero-vad pyannote-vad diarization whisperx post-ner subtitle-gen mux
set counter=2

for %%s in (%SERVICES%) do (
    echo [!counter!/11] Building %%s image...
    docker build -t %REGISTRY%/cp-whisperx-app-%%s:%TAG% -f docker\%%s\Dockerfile .
    if errorlevel 1 exit /b 1
    echo [SUCCESS] %%s image built
    echo.
    set /a counter+=1
)

echo ======================================================
echo   BUILD COMPLETE
echo ======================================================
echo.

REM Show image sizes
echo Docker images:
docker images | findstr "cp-whisperx-app" | sort

echo.
echo To push images to registry, run:
echo   scripts\push-images.bat

endlocal
