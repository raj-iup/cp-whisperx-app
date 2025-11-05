@echo off
REM Test T01: Windows Native Subtitle Generation

setlocal enabledelayedexpansion

echo === Test T01: Windows Native Subtitle Generation ===

REM Check for sample media
if not exist ".\in\sample_movie.mp4" (
    echo [WARNING] .\in\sample_movie.mp4 not found
    echo    Place a sample video file at .\in\sample_movie.mp4
    exit /b 1
)

REM Prepare job with native acceleration
echo Preparing job with native acceleration...
python prepare-job.py ^
  .\in\sample_movie.mp4 ^
  --start-time 00:10:00 ^
  --end-time 00:15:00 ^
  --subtitle-gen ^
  --native

if errorlevel 1 (
    echo [FAILED] Failed to create job
    exit /b 1
)

REM Get job ID from most recent job
for /f "tokens=1-3 delims=/" %%a in ('powershell -Command "Get-Date -Format 'yyyy/MM/dd'"') do (
    set YEAR=%%a
    set MONTH=%%b
    set DAY=%%c
)

for /f %%i in ('dir /b /od "jobs\%YEAR%\%MONTH%\%DAY%" 2^>nul') do set JOB_ID=%%i

if "%JOB_ID%"=="" (
    echo [FAILED] Failed to create job
    exit /b 1
)

echo Job ID: %JOB_ID%

REM Run pipeline
echo Running pipeline...
python pipeline.py --job "%JOB_ID%"

if errorlevel 1 (
    echo [FAILED] Pipeline failed
    exit /b 1
)

REM Verify outputs
echo.
echo Verifying outputs...
set OUTPUT_DIR=out\%YEAR%\%MONTH%\%DAY%\%JOB_ID%

set CHECKS_PASSED=0
set CHECKS_FAILED=0

if exist "%OUTPUT_DIR%\manifest.json" (
    echo [SUCCESS] Manifest created
    set /a CHECKS_PASSED+=1
) else (
    echo [FAILED] Manifest missing
    set /a CHECKS_FAILED+=1
)

if exist "%OUTPUT_DIR%\subtitles\subtitles.srt" (
    echo [SUCCESS] Subtitles created
    set /a CHECKS_PASSED+=1
) else (
    echo [FAILED] Subtitles missing
    set /a CHECKS_FAILED+=1
)

if exist "%OUTPUT_DIR%\final_output.mp4" (
    echo [SUCCESS] Final video created
    set /a CHECKS_PASSED+=1
) else (
    echo [FAILED] Final video missing
    set /a CHECKS_FAILED+=1
)

if exist "%OUTPUT_DIR%\audio\audio.wav" (
    echo [SUCCESS] Audio extracted
    set /a CHECKS_PASSED+=1
) else (
    echo [FAILED] Audio missing
    set /a CHECKS_FAILED+=1
)

REM Check manifest for device
findstr /C:"\"device\": \"cuda\"" "%OUTPUT_DIR%\manifest.json" >nul 2>&1
if not errorlevel 1 (
    echo [SUCCESS] CUDA acceleration confirmed
    set /a CHECKS_PASSED+=1
) else (
    findstr /C:"\"device\": \"cpu\"" "%OUTPUT_DIR%\manifest.json" >nul 2>&1
    if not errorlevel 1 (
        echo [INFO] CPU mode detected
    ) else (
        echo [WARNING] Device acceleration not detected in manifest
    )
)

REM Check pipeline status
findstr /C:"\"status\": \"completed\"" "%OUTPUT_DIR%\manifest.json" >nul 2>&1
if not errorlevel 1 (
    echo [SUCCESS] Pipeline completed successfully
    set /a CHECKS_PASSED+=1
) else (
    echo [FAILED] Pipeline did not complete
    set /a CHECKS_FAILED+=1
)

echo.
echo === Test T01 Summary ===
echo Passed: %CHECKS_PASSED%
echo Failed: %CHECKS_FAILED%

if %CHECKS_FAILED%==0 (
    echo [SUCCESS] Test T01 PASSED
    exit /b 0
) else (
    echo [FAILED] Test T01 FAILED
    exit /b 1
)

endlocal
