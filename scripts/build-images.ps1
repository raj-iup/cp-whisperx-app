# CP-WhisperX-App Build Images Script
# Builds all Docker images for the pipeline

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

# Load common logging
. "$PSScriptRoot\common-logging.ps1"

# Load configuration
$envFile = "config\.env"
if (Test-Path $envFile) {
    Get-Content $envFile | Where-Object { $_ -notmatch '^\s*#' -and $_ -match '=' } | ForEach-Object {
        $key, $value = $_ -split '=', 2
        Set-Variable -Name $key.Trim() -Value $value.Trim() -Scope Script
    }
}

# Set defaults
$registry = if ($env:DOCKER_REGISTRY) { $env:DOCKER_REGISTRY } elseif ($DOCKER_REGISTRY) { $DOCKER_REGISTRY } else { "rajiup" }
$tag = if ($env:DOCKER_TAG) { $env:DOCKER_TAG } elseif ($DOCKER_TAG) { $DOCKER_TAG } else { "latest" }

Write-LogSection "CP-WHISPERX-APP DOCKER IMAGE BUILD"
Write-LogInfo "Registry: $registry"
Write-LogInfo "Tag: $tag"
Write-Host ""

# Build base image first
Write-LogInfo "[1/11] Building base image..."
docker build -t "${registry}/cp-whisperx-app-base:${tag}" -f docker\base\Dockerfile .

if ($LASTEXITCODE -ne 0) {
    Write-LogError "Base image build failed"
    exit 1
}
Write-LogSuccess "Base image built"
Write-Host ""

# Build all service images
$services = @("demux", "tmdb", "pre-ner", "silero-vad", "pyannote-vad", "diarization", "whisperx", "post-ner", "subtitle-gen", "mux")
$counter = 2

foreach ($service in $services) {
    Write-LogInfo "[$counter/11] Building $service image..."
    docker build -t "${registry}/cp-whisperx-app-${service}:${tag}" -f "docker\${service}\Dockerfile" .
    
    if ($LASTEXITCODE -ne 0) {
        Write-LogError "$service image build failed"
        exit 1
    }
    Write-LogSuccess "$service image built"
    Write-Host ""
    $counter++
}

Write-LogSection "BUILD COMPLETE"
Write-Host ""

# Show image sizes
Write-LogInfo "Docker images:"
docker images | Select-String "cp-whisperx-app" | Sort-Object

Write-Host ""
Write-Host "To push images to registry, run:" -ForegroundColor Yellow
Write-Host "  .\scripts\push-images.ps1" -ForegroundColor Gray

exit 0
