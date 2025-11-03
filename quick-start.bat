@echo off
REM Quick start for Windows - Full subtitle generation workflow
REM Usage: quick-start.bat <input_video>

setlocal enabledelayedexpansion

if "%~1"=="" (
    echo Usage: quick-start.bat ^<input_video^>
    echo Example: quick-start.bat "C:\Videos\movie.mp4"
    exit /b 1
)

set INPUT_VIDEO=%~1

echo ========================================
echo CP-WhisperX-App Quick Start (Windows)
echo ========================================
echo.
echo Input: %INPUT_VIDEO%
echo.

REM Step 1: Run preflight checks
echo Step 1/3: Running preflight checks...
python preflight.py
if %ERRORLEVEL% NEQ 0 (
    echo Preflight checks failed! Please fix errors before continuing.
    exit /b 1
)
echo.

REM Step 2: Prepare job
echo Step 2/3: Preparing job...
python prepare-job.py "%INPUT_VIDEO%" --subtitle-gen
if %ERRORLEVEL% NEQ 0 (
    echo Job preparation failed!
    exit /b 1
)

REM Get the job ID from the last line of output (assuming prepare-job prints it)
REM For now, we'll need to get it from jobs directory
for /f "tokens=*" %%a in ('dir /b /od /ad "jobs\%date:~-4%\*" 2^>nul ^| findstr /r "[0-9][0-9]" ^| sort /r ^| findstr /n "^" ^| findstr "^1:"') do set LAST_MONTH=%%a
set LAST_MONTH=%LAST_MONTH:~2%

for /f "tokens=*" %%a in ('dir /b /od /ad "jobs\%date:~-4%\%LAST_MONTH%\*" 2^>nul ^| sort /r ^| findstr /n "^" ^| findstr "^1:"') do set LAST_DAY=%%a
set LAST_DAY=%LAST_DAY:~2%

for /f "tokens=*" %%a in ('dir /b /od /ad "jobs\%date:~-4%\%LAST_MONTH%\%LAST_DAY%\*" 2^>nul ^| sort /r ^| findstr /n "^" ^| findstr "^1:"') do set JOB_ID=%%a
set JOB_ID=%JOB_ID:~2%

echo Job ID: %JOB_ID%
echo.

REM Step 3: Run pipeline
echo Step 3/3: Running pipeline...
python pipeline.py --job %JOB_ID%
if %ERRORLEVEL% NEQ 0 (
    echo Pipeline execution failed!
    exit /b 1
)

echo.
echo ========================================
echo Quick Start Complete!
echo ========================================
echo Check output directory: out\%date:~-4%\%LAST_MONTH%\%LAST_DAY%\%JOB_ID%
echo.

endlocal
