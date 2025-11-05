@echo off
REM Helper to build and start Docker services
REM Usage: docker-run.bat [--build-only]

setlocal

set BUILD_ONLY=false

:parse_args
if "%~1"=="" goto args_done
if /i "%~1"=="--build-only" (
    set BUILD_ONLY=true
    shift
    goto parse_args
)
echo Unknown argument: %~1
exit /b 1

:args_done

echo Building Docker images...
docker compose build --pull --no-cache --parallel
if errorlevel 1 (
    echo Build failed
    exit /b 1
)

REM Check Docker daemon health
docker info >nul 2>&1
if errorlevel 1 (
    echo Docker does not appear to be running or the daemon is unreachable.
    echo On Windows, start Docker Desktop and wait until the status says "Docker is running".
    echo Then run 'docker info' to verify the daemon is healthy before re-running this script.
    exit /b 1
)

if "%BUILD_ONLY%"=="true" (
    echo Build completed (build-only).
    exit /b 0
)

echo Starting ASR service (in background)...
docker compose up -d asr

echo Waiting a few seconds for ASR to initialize...
timeout /t 5 /nobreak >nul

echo Downloading spaCy model inside NER container (if needed)...
docker compose run --rm ner python -m spacy download en_core_web_trf

echo Bringing up NER (depends_on: asr)...
docker compose up -d ner

echo All done. Use 'docker compose logs -f asr' and 'docker compose logs -f ner' to follow logs.

endlocal
exit /b 0
