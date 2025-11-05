# CP-WhisperX-App Build All Docker Images
# Complete build script with proper :cpu and :cuda tagging
# 
# Tagging Strategy:
# - CPU-Only Stages: :cpu tag (built from base:cpu)
# - GPU Stages: :cuda tag (built from base:cuda)
#
# BuildKit Optimization: Enabled for faster builds with cache mounts

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

# Enable Docker BuildKit
$env:DOCKER_BUILDKIT = 1
$env:BUILDKIT_PROGRESS = "plain"

# Load common logging
. "$PSScriptRoot\common-logging.ps1"

# Configuration
$registry = if ($env:DOCKERHUB_USER) { $env:DOCKERHUB_USER } else { "rajiup" }
$repoName = "cp-whisperx-app"

# Track failures
$script:failedBuilds = @()

# Build function
function Build-Image {
    param(
        [string]$Stage,
        [string]$Variant,  # "cpu" or "cuda"
        [string]$Dockerfile
    )
    
    $tag = "${registry}/${repoName}-${Stage}:${Variant}"
    
    Write-LogInfo "Building: $tag"
    
    docker build -t $tag -f $Dockerfile .
    
    if ($LASTEXITCODE -eq 0) {
        Write-LogSuccess "Built: $tag"
        return $true
    } else {
        Write-LogError "Failed: $tag"
        $script:failedBuilds += "${Stage}:${Variant}"
        return $false
    }
}

# Start
Write-LogSection "CP-WHISPERX-APP DOCKER IMAGE BUILDER"
Write-LogInfo "BuildKit: ENABLED (cache mounts active)"
Write-LogInfo "Registry: $registry"
Write-LogInfo "Repository: $repoName"
Write-Host ""
Write-Host "Tagging Strategy:" -ForegroundColor Cyan
Write-Host "  CPU-Only Stages: :cpu (from base:cpu)" -ForegroundColor Gray
Write-Host "  GPU Stages: :cuda (from base:cuda)" -ForegroundColor Gray
Write-Host ""

# === Phase 1: Base Images ===
Write-LogSection "Phase 1: Building Base Images"
Write-Host ""
Write-LogInfo "Building base images in dependency order:"
Write-LogInfo "  1. base:cpu - CPU-only base"
Write-LogInfo "  2. base:cuda - CUDA base with Python 3.11"
Write-LogInfo "  3. base-ml:cuda - ML base with PyTorch (inherits from base:cuda)"
Write-LogInfo "All other images will reference these base images"
Write-Host ""

# Build base:cpu
Write-LogInfo "Building base:cpu (required by all CPU-only and fallback stages)"
if (-not (Build-Image "base" "cpu" "docker/base/Dockerfile")) {
    Write-LogCritical "base:cpu build failed!"
    Write-LogCritical "Cannot proceed - all CPU stages require base:cpu"
    Write-LogCritical "Required by: demux, tmdb, pre-ner, post-ner, subtitle-gen, mux"
    Write-LogCritical "Also required for GPU stage CPU fallbacks"
    exit 1
}
Write-Host ""

# Build base:cuda
Write-LogInfo "Building base:cuda (required by base-ml and all GPU CUDA stages)"
if (-not (Build-Image "base" "cuda" "docker/base-cuda/Dockerfile")) {
    Write-LogCritical "base:cuda build failed!"
    Write-LogCritical "Cannot proceed - base-ml:cuda requires base:cuda"
    Write-LogCritical "Required by: base-ml, and all GPU CUDA stages"
    exit 1
}
Write-Host ""

# Build base-ml:cuda
Write-LogInfo "Building base-ml:cuda (ML base with PyTorch - required by all GPU stages)"
Write-LogInfo "This image includes PyTorch 2.1.0 + common ML packages"
Write-LogInfo "Saves 10-15 GB by installing PyTorch once instead of per-stage"
if (-not (Build-Image "base-ml" "cuda" "docker/base-ml/Dockerfile")) {
    Write-LogCritical "base-ml:cuda build failed!"
    Write-LogCritical "Cannot proceed - all GPU stages require base-ml:cuda"
    Write-LogCritical "Required by: silero-vad, pyannote-vad, diarization, asr, etc."
    exit 1
}
Write-Host ""

Write-LogSuccess "All base images built successfully!"
Write-LogInfo "Subsequent GPU stage builds will inherit PyTorch from base-ml"
Write-Host ""

# === Phase 2: CPU-Only Stages ===
Write-LogSection "Phase 2: Building CPU-Only Stages"
Write-Host "(demux, tmdb, pre-ner, post-ner, subtitle-gen, mux)" -ForegroundColor Gray
Write-Host ""

$cpuStages = @(
    "demux",
    "tmdb",
    "pre-ner",
    "post-ner",
    "subtitle-gen",
    "mux"
)

foreach ($stage in $cpuStages) {
    Build-Image $stage "cpu" "docker/$stage/Dockerfile" | Out-Null
    Write-Host ""
}

# === Phase 3: GPU Stages (CUDA variants) ===
Write-LogSection "Phase 3: Building GPU Stages (CUDA variants)"
Write-Host "(silero-vad, pyannote-vad, diarization, asr, and optional stages)" -ForegroundColor Gray
Write-Host ""

$gpuStages = @(
    "silero-vad",
    "pyannote-vad",
    "diarization",
    "asr",
    "second-pass-translation",
    "lyrics-detection"
)

foreach ($stage in $gpuStages) {
    $dockerfile = "docker/$stage/Dockerfile"
    if (Test-Path $dockerfile) {
        Build-Image $stage "cuda" $dockerfile | Out-Null
        Write-Host ""
    } else {
        Write-LogWarn "Skipping $stage - Dockerfile not found"
        Write-Host ""
    }
}

# === Phase 4: GPU Stages (CPU fallback variants) ===
Write-LogSection "Phase 4: Building GPU Stages (CPU fallback variants)"
Write-Host "(Same stages with CPU-only PyTorch for fallback)" -ForegroundColor Gray
Write-Host ""

foreach ($stage in $gpuStages) {
    $dockerfileCpu = "docker/$stage/Dockerfile.cpu"
    $dockerfile = "docker/$stage/Dockerfile"
    
    if (Test-Path $dockerfileCpu) {
        Build-Image $stage "cpu" $dockerfileCpu | Out-Null
        Write-Host ""
    } elseif (Test-Path $dockerfile) {
        Write-LogInfo "Building CPU fallback for $stage"
        
        # Read Dockerfile and modify for CPU
        $content = Get-Content $dockerfile -Raw
        $cpuContent = $content -replace "FROM ${registry}/${repoName}-base-ml:cuda", "FROM ${registry}/${repoName}-base:cpu"
        $cpuContent = $cpuContent -replace "FROM ${registry}/${repoName}-base:cuda", "FROM ${registry}/${repoName}-base:cpu"
        $cpuContent = $cpuContent -replace "--index-url https://download.pytorch.org/whl/cu121", "--index-url https://download.pytorch.org/whl/cpu"
        
        # Build using modified content
        $tempFile = New-TemporaryFile
        Set-Content -Path $tempFile.FullName -Value $cpuContent
        
        $tag = "${registry}/${repoName}-${stage}:cpu"
        Write-LogInfo "Building: $tag"
        docker build -t $tag -f $tempFile.FullName .
        
        Remove-Item $tempFile.FullName
        
        if ($LASTEXITCODE -eq 0) {
            Write-LogSuccess "Built: $tag (fallback)"
        } else {
            Write-LogError "Failed: $tag"
            $script:failedBuilds += "${stage}:cpu"
        }
        Write-Host ""
    } else {
        Write-LogWarn "Skipping ${stage}:cpu - Dockerfile not found"
        Write-Host ""
    }
}

# === Summary ===
Write-LogSection "Build Summary"
Write-Host ""

if ($script:failedBuilds.Count -eq 0) {
    Write-LogSuccess "All images built successfully!"
    Write-Host ""
    Write-Host "Image Summary:" -ForegroundColor Cyan
    Write-Host "  Base images: base:cpu, base:cuda, base-ml:cuda" -ForegroundColor Gray
    Write-Host "  CPU-only stages (6): demux, tmdb, pre-ner, post-ner, subtitle-gen, mux" -ForegroundColor Gray
    Write-Host "  GPU stages with fallback (4-6):" -ForegroundColor Gray
    Write-Host "    - silero-vad:cuda + silero-vad:cpu" -ForegroundColor Gray
    Write-Host "    - pyannote-vad:cuda + pyannote-vad:cpu" -ForegroundColor Gray
    Write-Host "    - diarization:cuda + diarization:cpu" -ForegroundColor Gray
    Write-Host "    - asr:cuda + asr:cpu" -ForegroundColor Gray
    Write-Host "    - [optional] second-pass-translation:cuda + :cpu" -ForegroundColor Gray
    Write-Host "    - [optional] lyrics-detection:cuda + :cpu" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Total images built: ~21" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "  1. Test GPU images: docker compose run --rm --gpus all asr" -ForegroundColor Gray
    Write-Host "  2. Test CPU fallback: docker compose run --rm asr" -ForegroundColor Gray
    Write-Host "  3. Push to registry: .\scripts\push-all-images.ps1" -ForegroundColor Gray
    Write-Host ""
    exit 0
} else {
    Write-LogFailure "Some builds failed ($($script:failedBuilds.Count) failures)"
    Write-Host ""
    Write-Host "Failed builds:" -ForegroundColor Red
    $script:failedBuilds | ForEach-Object {
        Write-Host "  ✗ $_" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "Check build logs above for details" -ForegroundColor Yellow
    exit 1
}
