# CP-WhisperX-App Docker Image Pull Script
# Pull all Docker images from registry with consistent logging

[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [string]$Registry = "rajiup"
)

$ErrorActionPreference = "Stop"

# Logging functions
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [pull-images] [$Level] $Message"
    
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

# Start
Write-Header "CP-WHISPERX-APP IMAGE PULL"
Write-Log "Registry: $Registry" "INFO"

# Check if docker scripts exist
if (Test-Path "scripts\pull-all-images.bat") {
    Write-Log "Calling scripts\pull-all-images.bat..." "INFO"
    & cmd /c "scripts\pull-all-images.bat"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Log "All images pulled successfully" "SUCCESS"
        exit 0
    } else {
        Write-Log "Image pull failed with exit code $LASTEXITCODE" "ERROR"
        exit $LASTEXITCODE
    }
} else {
    Write-Log "Image pull script not found: scripts\pull-all-images.bat" "ERROR"
    exit 1
}
