@echo off
REM Push all Docker images to registry
REM Requires Docker Hub login: docker login

setlocal enabledelayedexpansion

REM Configuration
if "%DOCKERHUB_USER%"=="" (
    set REGISTRY=rajiup
) else (
    set REGISTRY=%DOCKERHUB_USER%
)
set REPO_NAME=cp-whisperx-app

echo ========================================
echo CP-WhisperX-App Docker Image Pusher
echo ========================================
echo.
echo Registry: %REGISTRY%
echo Repository: %REPO_NAME%
echo.

REM Check if logged in
docker info | findstr /C:"Username" >nul 2>&1
if errorlevel 1 (
    echo [FAILED] Not logged in to Docker Hub
    echo Run: docker login
    exit /b 1
)

echo [SUCCESS] Docker Hub login verified
echo.

REM Track failures
set FAILED_COUNT=0
set FAILED_LIST=

echo === Pushing Base Images ===
echo.

REM Push base images
echo Pushing: %REGISTRY%/%REPO_NAME%-base:cpu
docker push "%REGISTRY%/%REPO_NAME%-base:cpu"
if errorlevel 1 (
    echo [FAILED] base:cpu
    set /a FAILED_COUNT+=1
    set "FAILED_LIST=!FAILED_LIST! base:cpu"
) else (
    echo [SUCCESS] Pushed: %REGISTRY%/%REPO_NAME%-base:cpu
)
echo.

echo Pushing: %REGISTRY%/%REPO_NAME%-base:cuda
docker push "%REGISTRY%/%REPO_NAME%-base:cuda"
if errorlevel 1 (
    echo [FAILED] base:cuda
    set /a FAILED_COUNT+=1
    set "FAILED_LIST=!FAILED_LIST! base:cuda"
) else (
    echo [SUCCESS] Pushed: %REGISTRY%/%REPO_NAME%-base:cuda
)
echo.

echo === Pushing Stage Images ===
echo.

REM Get all images and push them
for /f "tokens=1,2 delims=:" %%a in ('docker images --format "{{.Repository}}:{{.Tag}}" ^| findstr /C:"%REGISTRY%/%REPO_NAME%" ^| findstr /V /C:"base:"') do (
    echo Pushing: %%a:%%b
    docker push "%%a:%%b"
    if errorlevel 1 (
        echo [FAILED] %%a:%%b
        set /a FAILED_COUNT+=1
        set "FAILED_LIST=!FAILED_LIST! %%a:%%b"
    ) else (
        echo [SUCCESS] Pushed: %%a:%%b
    )
    echo.
)

REM Summary
echo ========================================
echo Push Summary
echo ========================================
echo.

if %FAILED_COUNT%==0 (
    echo [SUCCESS] All images pushed successfully!
    echo.
    echo Pushed images:
    docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" | findstr /C:"%REGISTRY%/%REPO_NAME%"
    echo.
    echo [SUCCESS] Docker images are now available on Docker Hub
    echo   Registry: https://hub.docker.com/u/%REGISTRY%
    echo.
) else (
    echo [FAILED] %FAILED_COUNT% pushes failed:
    echo %FAILED_LIST%
    echo.
    exit /b 1
)

endlocal
