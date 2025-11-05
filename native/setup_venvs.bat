@echo off
REM Creates isolated virtual environments for each pipeline stage

setlocal enabledelayedexpansion

set VENV_DIR=native\venvs
set REQ_DIR=native\requirements
set PYTHON_CMD=python

echo ======================================================
echo MPS Native Pipeline - Virtual Environment Setup
echo ======================================================

REM Check Python version
echo Checking Python version...
for /f "delims=" %%i in ('%PYTHON_CMD% --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Using: %PYTHON_VERSION%

where %PYTHON_CMD% >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python 3 not found! Please install Python 3.9+
    exit /b 1
)

REM Stages list
set stages=demux tmdb pre-ner silero-vad pyannote-vad diarization asr post-ner subtitle-gen mux
set total=10
set current=0

for %%s in (%stages%) do (
    set /a current+=1
    echo [!current!/%total%] Creating venv for %%s...
    
    set venv_path=%VENV_DIR%\%%s
    set stage_name=%%s
    set req_file=%REQ_DIR%\!stage_name:-=_!.txt
    
    REM Create virtual environment
    if exist "!venv_path!" (
        echo   venv already exists, skipping creation
    ) else (
        %PYTHON_CMD% -m venv "!venv_path!"
        echo   [SUCCESS] venv created
    )
    
    REM Install requirements if file exists
    if exist "!req_file!" (
        findstr /R /C:"^[^#]" "!req_file!" >nul 2>&1
        if not errorlevel 1 (
            echo   Installing requirements...
            "!venv_path!\Scripts\pip.exe" install --quiet --upgrade pip setuptools wheel
            "!venv_path!\Scripts\pip.exe" install --quiet -r "!req_file!"
            echo   [SUCCESS] requirements installed
        ) else (
            echo   [SKIP] no dependencies in requirements file
        )
    ) else (
        echo   [WARN] no requirements file found: !req_file!
    )
    echo.
)

echo ======================================================
echo Virtual Environment Setup Complete
echo ======================================================
echo.
echo All stage environments created in: %VENV_DIR%\
echo.
echo Next steps:
echo   1. Configure: config\.env and config\secrets.json
echo   2. Run: python native\pipeline.py in\movie.mp4
echo.

endlocal
exit /b 0
