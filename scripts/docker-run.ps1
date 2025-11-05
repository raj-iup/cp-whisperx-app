# CP-WhisperX-App Docker Run Helper
# Builds and starts Docker services

[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [switch]$BuildOnly
)

$ErrorActionPreference = "Stop"

# Logging functions
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [docker-run] [$Level] $Message"
    
    switch ($Level) {
        "ERROR" { Write-Host $logMessage -ForegroundColor Red }
        "WARNING" { Write-Host $logMessage -ForegroundColor Yellow }
        "SUCCESS" { Write-Host $logMessage -ForegroundColor Green }
        default { Write-Host $logMessage }
    }
}

function Write-Header {
    param([string]$Title)
    Write-Host ""
    Write-Host ("=" * 60) -ForegroundColor Cyan
    Write-Host $Title -ForegroundColor Cyan
    Write-Host ("=" * 60) -ForegroundColor Cyan
}

Write-Header "CP-WHISPERX-APP DOCKER RUN"

# Check Docker daemon
Write-Log "Checking Docker daemon..." "INFO"
try {
    docker info | Out-Null
} catch {
    Write-Log "Docker daemon is not running" "ERROR"
    Write-Host ""
    Write-Host "On Windows: Start Docker Desktop and wait until status shows 'Docker is running'" -ForegroundColor Yellow
    Write-Host "Then run 'docker info' to verify before re-running this script" -ForegroundColor Yellow
    exit 1
}

# Build images
Write-Log "Building Docker images..." "INFO"
docker compose build --pull --no-cache --parallel

if ($LASTEXITCODE -ne 0) {
    Write-Log "Build failed" "ERROR"
    exit 1
}

Write-Log "Build completed successfully" "SUCCESS"

if ($BuildOnly) {
    Write-Log "Build-only mode: Exiting" "INFO"
    exit 0
}

# Start ASR service
Write-Log "Starting ASR service (in background)..." "INFO"
docker compose up -d asr

Write-Log "Waiting for ASR to initialize..." "INFO"
Start-Sleep -Seconds 5

# Download spaCy model
Write-Log "Downloading spaCy model in NER container (if needed)..." "INFO"
docker compose run --rm ner python -m spacy download en_core_web_trf

# Start NER service
Write-Log "Starting NER service..." "INFO"
docker compose up -d ner

Write-Header "ALL SERVICES STARTED"
Write-Host ""
Write-Host "View logs:" -ForegroundColor Yellow
Write-Host "  docker compose logs -f asr" -ForegroundColor Gray
Write-Host "  docker compose logs -f ner" -ForegroundColor Gray
Write-Host ""

exit 0
