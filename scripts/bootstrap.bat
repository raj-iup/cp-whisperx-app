@echo off
REM Bootstrap script for cp-whisperx-app
REM - creates a Python venv at .bollyenv
REM - ensures pip/wheel are up-to-date
REM - writes a sensible requirements.txt if missing
REM - installs Python dependencies
REM - runs a quick CUDA availability check

setlocal

set VENV_DIR=.bollyenv
set REQ_FILE=requirements.txt

echo == cp-whisperx-app bootstrap ==

REM Find Python
set PYTHON_BIN=
where python 2>nul >nul
if not errorlevel 1 (
    set PYTHON_BIN=python
) else (
    where python3 2>nul >nul
    if not errorlevel 1 (
        set PYTHON_BIN=python3
    ) else (
        echo ERROR: Python not found. Please install Python 3.11+.
        exit /b 1
    )
)

echo Using python: %PYTHON_BIN%

echo Checking Python version (recommended: 3.11+)
%PYTHON_BIN% -c "import sys; v = sys.version_info; print(f'Python {v.major}.{v.minor}.{v.micro}'); print('Warning: Python 3.11+ recommended') if v.major < 3 or (v.major == 3 and v.minor < 11) else None"

if exist "%VENV_DIR%" (
    echo Found existing virtualenv in %VENV_DIR%
) else (
    echo Creating virtualenv in %VENV_DIR%
    %PYTHON_BIN% -m venv "%VENV_DIR%"
)

echo Activating virtualenv
call "%VENV_DIR%\Scripts\activate.bat"

echo Upgrading pip and wheel
python -m pip install -U pip wheel

if not exist "%REQ_FILE%" (
    echo No %REQ_FILE% found - writing recommended requirements.txt
    (
        echo torch^>=2.3,^<3.0
        echo torchaudio^>=2.3,^<3.0
        echo openai-whisper^>=20231117
        echo faster-whisper^>=1.0.0
        echo whisperx^>=3.1.0
        echo whisper-ctranslate2^>=0.4.0
        echo ctranslate2^>=4.2.0
        echo pyannote.audio^>=3.1.0
        echo huggingface_hub^>=0.23.0
        echo librosa^>=0.10.1
        echo soundfile^>=0.12.1
        echo tmdbsimple^>=2.9.1
        echo rich^>=13.7.0
        echo python-dotenv^>=1.0.0
        echo pysubs2^>=1.1.0
        echo spacy^>=3.7.0
        echo transformers^>=4.30.0
    ) > "%REQ_FILE%"
    echo Wrote %REQ_FILE%
)

echo Installing Python packages from %REQ_FILE% (this can take a while)
python -m pip install -r "%REQ_FILE%"

echo Running quick torch/CUDA check
python -c "try: import torch, sys; cuda = torch.cuda.is_available(); print('Torch version:', torch.__version__); print('CUDA available:', bool(cuda)); except Exception as e: print('Could not import torch or check devices:', repr(e)); sys.exit(0)"

echo.
echo Bootstrap complete.
echo Next steps:
echo   - Create .\config\.env and .\config\secrets.json (see README.md for format).
echo   - Run preflight.bat to validate system deps and tokens.
echo   - Run the pipeline via: python run_pipeline.py -h

endlocal
exit /b 0
