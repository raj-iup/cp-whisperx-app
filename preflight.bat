@echo off
REM Windows batch wrapper for preflight.py
REM Usage: preflight.bat [--force]

python preflight.py %*
if %ERRORLEVEL% NEQ 0 (
    echo Error: Preflight check failed with exit code %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)
