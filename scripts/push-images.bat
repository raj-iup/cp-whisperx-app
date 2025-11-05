@echo off
REM Push all Docker images to registry
setlocal enabledelayedexpansion

REM Load configuration
if exist "config\.env" (
    for /f "usebackq tokens=1,2 delims==" %%a in ("config\.env") do (
        if not "%%a"=="#" set %%a=%%b
    )
)

if "%DOCKER_REGISTRY%"=="" (
    set REGISTRY=rajiup
) else (
    set REGISTRY=%DOCKER_REGISTRY%
)

if "%DOCKER_TAG%"=="" (
    set TAG=latest
) else (
    set TAG=%DOCKER_TAG%
)

echo ======================================================
echo   PUSHING IMAGES TO REGISTRY
echo ======================================================
echo Registry: %REGISTRY%
echo Tag: %TAG%
echo.

REM Login to Docker Hub
echo Logging in to Docker Hub...
docker login
if errorlevel 1 (
    echo ERROR: Docker login failed
    exit /b 1
)
echo.

REM Push all images
set IMAGES=base demux tmdb pre-ner silero-vad pyannote-vad diarization whisperx post-ner subtitle-gen mux
set counter=1
set total=0
for %%i in (%IMAGES%) do set /a total+=1

for %%i in (%IMAGES%) do (
    echo [!counter!/%total%] Pushing %%i...
    docker push %REGISTRY%/cp-whisperx-app-%%i:%TAG%
    if errorlevel 1 (
        echo ERROR: Failed to push %%i
    ) else (
        echo [OK] %%i pushed
    )
    echo.
    set /a counter+=1
)

echo ======================================================
echo   ALL IMAGES PUSHED SUCCESSFULLY
echo ======================================================
echo.
echo Images available at:
for %%i in (%IMAGES%) do (
    echo   %REGISTRY%/cp-whisperx-app-%%i:%TAG%
)

endlocal
