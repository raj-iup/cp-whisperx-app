@echo off
REM Windows batch wrapper for pipeline.py
REM Usage: run_pipeline.bat --job <job_id> [options]

python pipeline.py %*
if %ERRORLEVEL% NEQ 0 (
    echo Error: Pipeline execution failed with exit code %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)
