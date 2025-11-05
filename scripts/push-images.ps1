# CP-WhisperX-App Push Images to Registry
# Consolidated push script with consistent logging

[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [switch]$NoPush,
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipBase
)

$ErrorActionPreference = "Stop"

# Load common logging
. "$PSScriptRoot\common-logging.ps1"

# Load configuration
$envFile = "config\.env"
if (Test-Path $envFile) {
    Get-Content $envFile | Where-Object { $_ -notmatch '^\s*#' -and $_ -match '=' } | ForEach-Object {
        $key, $value = $_ -split '=', 2
        [Environment]::SetEnvironmentVariable($key.Trim(), $value.Trim(), 'Process')
    }
}

$registry = if ($env:DOCKER_REGISTRY) { $env:DOCKER_REGISTRY } else { "rajiup" }
$tag = if ($env:DOCKER_TAG) { $env:DOCKER_TAG } else { "latest" }

Write-LogSection "PUSHING IMAGES TO REGISTRY"
Write-LogInfo "Registry: $registry"
Write-LogInfo "Tag: $tag"
Write-LogInfo "No-Push Mode: $NoPush"
Write-LogInfo "Skip Base: $SkipBase"
Write-Host ""

# Docker login
if (-not $NoPush) {
    Write-LogInfo "Logging in to Docker Hub..."
    docker login
    
    if ($LASTEXITCODE -ne 0) {
        Write-LogError "Docker login failed"
        exit 1
    }
    Write-Host ""
}

# Push all images
$images = @("base", "demux", "tmdb", "pre-ner", "silero-vad", "pyannote-vad", "diarization", "whisperx", "post-ner", "subtitle-gen", "mux")

if ($SkipBase) {
    $images = $images | Where-Object { $_ -ne "base" }
    Write-LogInfo "Skipping base image"
}

$counter = 1
$total = $images.Count

foreach ($image in $images) {
    Write-LogInfo "[$counter/$total] Pushing $image..."
    
    $imageName = "${registry}/cp-whisperx-app-${image}:${tag}"
    
    if ($NoPush) {
        Write-LogInfo "No-push mode: Would push $imageName"
    } else {
        docker push $imageName
        
        if ($LASTEXITCODE -ne 0) {
            Write-LogError "Failed to push $image"
        } else {
            Write-LogSuccess "$image pushed"
        }
    }
    
    Write-Host ""
    $counter++
}

Write-LogSection "ALL IMAGES PUSHED SUCCESSFULLY"
Write-Host ""
Write-LogInfo "Images available at:"
foreach ($image in $images) {
    Write-Host "  ${registry}/cp-whisperx-app-${image}:${tag}" -ForegroundColor Gray
}

exit 0
