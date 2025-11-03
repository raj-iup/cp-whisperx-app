@echo off
REM Windows batch wrapper for resuming pipeline
REM Usage: resume-pipeline.bat --job <job_id>

python pipeline.py --resume %*
if %ERRORLEVEL% NEQ 0 (
    echo Error: Pipeline resume failed with exit code %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)
