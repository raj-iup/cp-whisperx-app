@echo off
REM Windows batch wrapper for prepare-job.py
REM Usage: prepare-job.bat <input_media> [options]

python prepare-job.py %*
if %ERRORLEVEL% NEQ 0 (
    echo Error: Job preparation failed with exit code %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)
