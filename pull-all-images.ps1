# CP-WhisperX-App Docker Image Pull Script
# Pull all Docker images from registry with consistent logging

[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [string]$Registry = "rajiup"
)

$ErrorActionPreference = "Stop"

# Load common logging
. "$PSScriptRoot\scripts\common-logging.ps1"

# Start
Write-LogSection "CP-WHISPERX-APP IMAGE PULL"
Write-LogInfo "Registry: $Registry"

# Check if pull script exists in scripts directory
if (Test-Path "scripts\pull-all-images.sh") {
    Write-LogInfo "Calling scripts\pull-all-images.sh..."
    & bash "scripts\pull-all-images.sh"
    
    if ($LASTEXITCODE -eq 0) {
        Write-LogSuccess "All images pulled successfully"
        exit 0
    } else {
        Write-LogError "Image pull failed with exit code $LASTEXITCODE"
        exit $LASTEXITCODE
    }
} else {
    Write-LogError "Image pull script not found: scripts\pull-all-images.sh"
    exit 1
}
