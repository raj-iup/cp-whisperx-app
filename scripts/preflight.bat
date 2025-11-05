@echo off
REM cp-whisperx-app preflight check (Windows)
setlocal enabledelayedexpansion

set ROOT_DIR=%~dp0..
set VENV_DIR=%ROOT_DIR%\.bollyenv
set SECRETS_PATH=%ROOT_DIR%\config\secrets.json
set ENV_PATH=%ROOT_DIR%\config\.env

echo == cp-whisperx-app preflight ==
echo Root: %ROOT_DIR%
echo.

echo -- checking system binaries --
for %%b in (ffmpeg mkvmerge curl python) do (
    where %%b >nul 2>&1
    if !errorlevel! equ 0 (
        for /f "delims=" %%p in ('where %%b') do echo %%b: %%p
    ) else (
        echo %%b: MISSING
    )
)
echo.

echo -- virtualenv --
if exist "%VENV_DIR%" (
    echo Found venv: %VENV_DIR%
    call "%VENV_DIR%\Scripts\activate.bat"
) else (
    echo No virtualenv found at %VENV_DIR% - run scripts\bootstrap.bat first
)
echo.

echo -- python packages (quick import checks) --
for %%p in (whisperx transformers spacy pysubs2 dotenv tmdbsimple huggingface_hub) do (
    python -c "import %%p; print('OK: %%p')" 2>nul || echo MISSING or ERROR: %%p
)
echo.
echo Note: pyannote.audio is intentionally NOT import-checked on the host.
echo It is tested inside the diarization container below.
echo.

echo -- config files --
if exist "%ENV_PATH%" (
    echo Found .env at %ENV_PATH%
) else (
    echo Missing: %ENV_PATH%
)
if exist "%SECRETS_PATH%" (
    echo Found secrets.json at %SECRETS_PATH%
) else (
    echo Missing: %SECRETS_PATH%
)
echo.

echo -- token probes (if present) --
if exist "%SECRETS_PATH%" (
    for /f "delims=" %%t in ('python -c "import json; j=json.load(open('%SECRETS_PATH%')); print(j.get('hf_token',''))" 2^>nul') do set HF_TOKEN=%%t
    for /f "delims=" %%t in ('python -c "import json; j=json.load(open('%SECRETS_PATH%')); print(j.get('tmdb_api_key',''))" 2^>nul') do set TMDB_KEY=%%t
    for /f "delims=" %%t in ('python -c "import json; j=json.load(open('%SECRETS_PATH%')); print(j.get('pyannote_token',''))" 2^>nul') do set PYANNOTE_TOKEN=%%t
    
    if not "!HF_TOKEN!"=="" (
        echo Probing Hugging Face whoami-v2...
        curl -s -o nul -w "HF whoami response code: %%{http_code}" -H "Authorization: Bearer !HF_TOKEN!" https://huggingface.co/api/whoami-v2
        echo.
    ) else (
        echo HF token: missing
    )
    
    if not "!TMDB_KEY!"=="" (
        echo Probing TMDB search...
        curl -s -o nul -w "TMDB response code: %%{http_code}" "https://api.themoviedb.org/3/search/movie?api_key=!TMDB_KEY!&query=Deewar"
        echo.
    ) else (
        echo TMDB key: missing
    )
    
    if not "!PYANNOTE_TOKEN!"=="" (
        echo Probing pyannote token with whoami-v2...
        curl -s -o nul -w "pyannote whoami response code: %%{http_code}" -H "Authorization: Bearer !PYANNOTE_TOKEN!" https://huggingface.co/api/whoami-v2
        echo.
    ) else (
        echo pyannote token: missing
    )
)
echo.

echo -- docker / container quick tests --
where docker >nul 2>&1
if !errorlevel! equ 0 (
    docker --version
    docker compose version >nul 2>&1
    if !errorlevel! equ 0 (
        echo docker compose: OK
        
        echo Running quick python check in 'asr' service...
        docker compose run --rm -T asr python -c "print('ASR container python OK')"
        if !errorlevel! equ 0 (
            echo ASR container python: OK
        ) else (
            echo ASR container python: FAILED
        )
        
        echo Running pyannote.audio import test in 'diarization' service...
        echo import sys; import pyannote.audio as pa; print('pyannote OK', getattr(pa, '__version__', 'unknown')) | docker compose run --rm -T diarization python
        if !errorlevel! equ 0 (
            echo pyannote.audio (in container): OK
        ) else (
            echo pyannote.audio (in container): FAILED
        )
    ) else (
        echo docker compose: NOT FOUND
    )
) else (
    echo docker: MISSING
)
echo.

echo -- quick torch device check --
python -c "import torch; print('Torch:', torch.__version__); print('CUDA available:', torch.cuda.is_available())" 2>nul || echo Torch not available or error
echo.

echo Preflight finished. Review any MISSING/ERROR lines above and fix before running the full pipeline.
exit /b 0
