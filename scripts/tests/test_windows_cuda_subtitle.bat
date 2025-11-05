@echo off
REM Test: Windows CUDA Native Subtitle Generation
REM Windows equivalent of macOS MPS test

setlocal enabledelayedexpansion

echo === Test: Windows CUDA Native Subtitle Generation ===
echo.

REM Check if running on Windows
ver | findstr /i "Windows" >nul
if errorlevel 1 (
    echo X This test requires Windows
    exit /b 1
)

REM Check for sample media
if not exist ".\in\sample_movie.mp4" (
    echo Warning: .\in\sample_movie.mp4 not found
    echo    Place a sample video file at .\in\sample_movie.mp4
    exit /b 1
)

REM Prepare job with native CUDA
echo Preparing job with native CUDA acceleration...
python prepare-job.py ^
  .\in\sample_movie.mp4 ^
  --start-time 00:10:00 ^
  --end-time 00:15:00 ^
  --subtitle-gen ^
  --native

REM Get job ID from most recent job
for /f "tokens=1-3 delims=/" %%a in ('powershell -Command "Get-Date -Format yyyy/MM/dd"') do (
    set YEAR=%%a
    set MONTH=%%b
    set DAY=%%c
)

for /f %%i in ('dir /b /o-d "jobs\%YEAR%\%MONTH%\%DAY%\" 2^>nul ^| findstr /v /c:"Directory of"') do (
    set JOB_ID=%%i
    goto :found_job
)

:found_job
if "%JOB_ID%"=="" (
    echo X Failed to create job
    exit /b 1
)

echo Job ID: %JOB_ID%

REM Run pipeline
echo Running pipeline...
python pipeline.py --job "%JOB_ID%"

REM Verify outputs
echo.
echo Verifying outputs...
set OUTPUT_DIR=out\%YEAR%\%MONTH%\%DAY%\%JOB_ID%

REM Check for expected files
set CHECKS_PASSED=0
set CHECKS_FAILED=0

if exist "%OUTPUT_DIR%\manifest.json" (
    echo [OK] Manifest created
    set /a CHECKS_PASSED+=1
) else (
    echo X Manifest missing
    set /a CHECKS_FAILED+=1
)

if exist "%OUTPUT_DIR%\subtitles\subtitles.srt" (
    echo [OK] Subtitles created
    set /a CHECKS_PASSED+=1
) else (
    echo X Subtitles missing
    set /a CHECKS_FAILED+=1
)

if exist "%OUTPUT_DIR%\final_output.mp4" (
    echo [OK] Final video created
    set /a CHECKS_PASSED+=1
) else (
    echo X Final video missing
    set /a CHECKS_FAILED+=1
)

if exist "%OUTPUT_DIR%\audio\audio.wav" (
    echo [OK] Audio extracted
    set /a CHECKS_PASSED+=1
) else (
    echo X Audio missing
    set /a CHECKS_FAILED+=1
)

REM Check manifest for CUDA device
findstr /c:"\"device\": \"cuda\"" "%OUTPUT_DIR%\manifest.json" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] CUDA acceleration confirmed
    set /a CHECKS_PASSED+=1
) else (
    echo Warning: CUDA acceleration not detected in manifest
)

REM Check pipeline status
findstr /c:"\"status\": \"completed\"" "%OUTPUT_DIR%\manifest.json" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Pipeline completed successfully
    set /a CHECKS_PASSED+=1
) else (
    echo X Pipeline did not complete
    set /a CHECKS_FAILED+=1
)

echo.
echo === Test Summary ===
echo Passed: %CHECKS_PASSED%
echo Failed: %CHECKS_FAILED%
echo.

if %CHECKS_FAILED% equ 0 (
    echo [OK] Test PASSED
    exit /b 0
) else (
    echo X Test FAILED
    exit /b 1
)

endlocal
