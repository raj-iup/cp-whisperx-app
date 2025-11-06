# CP-WhisperX-App Docker Build Script (Phase 2)
# Consolidated Docker image builder - builds only images needed for execution mode
#
# PHASE 2 FEATURES:
# - Mode-aware building (native, docker-cpu, docker-gpu)
# - Minimal image builds for native mode (default)
# - Full image builds for Docker-based execution
# - BuildKit cache optimization
# - Parallel builds where possible

[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("native", "docker-cpu", "docker-gpu")]
    [string]$Mode = "native",
    
    [Parameter(Mandatory=$false)]
    [string]$Registry = "rajiup",
    
    [Parameter(Mandatory=$false)]
    [switch]$NoPush,
    
    [Parameter(Mandatory=$false)]
    [switch]$Parallel
)

$ErrorActionPreference = "Stop"

# Load common logging
. "$PSScriptRoot\common-logging.ps1"

Write-LogSection "CP-WHISPERX-APP DOCKER BUILD (PHASE 2)"
Write-LogInfo "Mode: $Mode"
Write-LogInfo "Registry: $Registry"
Write-Host ""

# ============================================================================
# Enable Docker BuildKit for better performance
# ============================================================================
$env:DOCKER_BUILDKIT = "1"
$env:COMPOSE_DOCKER_CLI_BUILD = "1"

Write-LogInfo "Docker BuildKit: ENABLED"
Write-Host ""

# ============================================================================
# Build Strategy based on Mode
# ============================================================================

if ($Mode -eq "native") {
    Write-LogSection "NATIVE MODE BUILD"
    Write-LogInfo "Building minimal Docker images for FFmpeg operations only..."
    Write-LogInfo "ML execution will use native .bollyenv environment"
    Write-Host ""
    
    # Native mode only needs:
    # 1. base (CPU-only, minimal)
    # 2. demux (FFmpeg audio extraction)
    # 3. mux (FFmpeg video/subtitle muxing)
    
    $images = @(
        @{name="base"; tag="cpu"; dockerfile="docker/base/Dockerfile"; context="."}
        @{name="demux"; tag="latest"; dockerfile="docker/demux/Dockerfile"; context="."}
        @{name="mux"; tag="latest"; dockerfile="docker/mux/Dockerfile"; context="."}
    )
    
    Write-LogInfo "Images to build: 3 (base, demux, mux)"
    Write-LogInfo "Estimated size: ~2 GB total"
    Write-LogInfo "Estimated time: 2-5 minutes"
    Write-Host ""
    
} elseif ($Mode -eq "docker-cpu") {
    Write-LogSection "DOCKER CPU MODE BUILD"
    Write-LogInfo "Building all images with CPU-only support..."
    Write-Host ""
    
    # CPU mode builds all stages but without CUDA
    $images = @(
        @{name="base"; tag="cpu"; dockerfile="docker/base/Dockerfile"; context="."}
        @{name="base-ml"; tag="cpu"; dockerfile="docker/base-ml/Dockerfile"; context="."; build_args="REGISTRY=$Registry"}
        @{name="demux"; tag="latest"; dockerfile="docker/demux/Dockerfile"; context="."; build_args="REGISTRY=$Registry"}
        @{name="mux"; tag="latest"; dockerfile="docker/mux/Dockerfile"; context="."; build_args="REGISTRY=$Registry"}
        @{name="asr"; tag="cpu"; dockerfile="docker/asr/Dockerfile"; context="."; build_args="REGISTRY=$Registry"}
        @{name="diarization"; tag="cpu"; dockerfile="docker/diarization/Dockerfile"; context="."; build_args="REGISTRY=$Registry"}
        @{name="pyannote-vad"; tag="cpu"; dockerfile="docker/pyannote-vad/Dockerfile"; context="."; build_args="REGISTRY=$Registry"}
        @{name="subtitle-gen"; tag="latest"; dockerfile="docker/subtitle-gen/Dockerfile"; context="."; build_args="REGISTRY=$Registry"}
        @{name="tmdb"; tag="latest"; dockerfile="docker/tmdb/Dockerfile"; context="."; build_args="REGISTRY=$Registry"}
        @{name="pre-ner"; tag="latest"; dockerfile="docker/pre-ner/Dockerfile"; context="."; build_args="REGISTRY=$Registry"}
        @{name="post-ner"; tag="latest"; dockerfile="docker/post-ner/Dockerfile"; context="."; build_args="REGISTRY=$Registry"}
    )
    
    Write-LogInfo "Images to build: 11 (all stages, CPU-only)"
    Write-LogInfo "Estimated size: ~15 GB total"
    Write-LogInfo "Estimated time: 10-20 minutes"
    Write-Host ""
    
} elseif ($Mode -eq "docker-gpu") {
    Write-LogSection "DOCKER GPU MODE BUILD"
    Write-LogInfo "Building all images with CUDA GPU support..."
    Write-Host ""
    
    # GPU mode builds all stages with CUDA support
    # First build base images, then ML stages
    $images = @(
        @{name="base"; tag="cpu"; dockerfile="docker/base/Dockerfile"; context="."}
        @{name="base"; tag="cuda"; dockerfile="docker/base-cuda/Dockerfile"; context="."}
        @{name="base-ml"; tag="cuda"; dockerfile="docker/base-ml/Dockerfile"; context="."; build_args="REGISTRY=$Registry"}
        @{name="demux"; tag="latest"; dockerfile="docker/demux/Dockerfile"; context="."; build_args="REGISTRY=$Registry"}
        @{name="mux"; tag="latest"; dockerfile="docker/mux/Dockerfile"; context="."; build_args="REGISTRY=$Registry"}
        @{name="asr"; tag="cuda"; dockerfile="docker/asr/Dockerfile"; context="."; build_args="REGISTRY=$Registry"}
        @{name="diarization"; tag="cuda"; dockerfile="docker/diarization/Dockerfile"; context="."; build_args="REGISTRY=$Registry"}
        @{name="pyannote-vad"; tag="cuda"; dockerfile="docker/pyannote-vad/Dockerfile"; context="."; build_args="REGISTRY=$Registry"}
        @{name="silero-vad"; tag="cuda"; dockerfile="docker/silero-vad/Dockerfile"; context="."; build_args="REGISTRY=$Registry"}
        @{name="lyrics-detection"; tag="cuda"; dockerfile="docker/lyrics-detection/Dockerfile"; context="."; build_args="REGISTRY=$Registry"}
        @{name="subtitle-gen"; tag="latest"; dockerfile="docker/subtitle-gen/Dockerfile"; context="."; build_args="REGISTRY=$Registry"}
        @{name="tmdb"; tag="latest"; dockerfile="docker/tmdb/Dockerfile"; context="."; build_args="REGISTRY=$Registry"}
        @{name="pre-ner"; tag="latest"; dockerfile="docker/pre-ner/Dockerfile"; context="."; build_args="REGISTRY=$Registry"}
        @{name="post-ner"; tag="latest"; dockerfile="docker/post-ner/Dockerfile"; context="."; build_args="REGISTRY=$Registry"}
        @{name="second-pass-translation"; tag="cuda"; dockerfile="docker/second-pass-translation/Dockerfile"; context="."; build_args="REGISTRY=$Registry"}
    )
    
    Write-LogInfo "Images to build: 15 (all stages, CUDA-enabled)"
    Write-LogInfo "Estimated size: ~20 GB total (slim, no PyTorch in images)"
    Write-LogInfo "Estimated time: 15-30 minutes"
    Write-Host ""
}

# ============================================================================
# Build Images
# ============================================================================
Write-LogSection "BUILDING IMAGES"
Write-Host ""

$builtImages = @()
$failedImages = @()
$startTime = Get-Date

foreach ($img in $images) {
    $imageName = "$Registry/cp-whisperx-app-$($img.name):$($img.tag)"
    Write-LogInfo "Building: $imageName"
    Write-LogInfo "  Dockerfile: $($img.dockerfile)"
    
    # Build docker command
    $dockerArgs = @(
        "build",
        "-t", $imageName,
        "-f", $img.dockerfile
    )
    
    # Add build args if specified
    if ($img.build_args) {
        foreach ($arg in $img.build_args -split " ") {
            $dockerArgs += "--build-arg"
            $dockerArgs += $arg
        }
    }
    
    # Add context
    $dockerArgs += $img.context
    
    Write-Host "  Command: docker $($dockerArgs -join ' ')" -ForegroundColor DarkGray
    Write-Host ""
    
    try {
        & docker @dockerArgs
        
        if ($LASTEXITCODE -eq 0) {
            Write-LogSuccess "Built: $imageName"
            $builtImages += $imageName
        } else {
            Write-LogError "Failed: $imageName (exit code $LASTEXITCODE)"
            $failedImages += $imageName
        }
    } catch {
        Write-LogError "Failed: $imageName (exception: $_)"
        $failedImages += $imageName
    }
    
    Write-Host ""
}

$endTime = Get-Date
$duration = ($endTime - $startTime).TotalSeconds

# ============================================================================
# Summary
# ============================================================================
Write-LogSection "BUILD SUMMARY"
Write-LogInfo "Duration: $([math]::Round($duration, 1)) seconds"
Write-LogInfo "Successfully built: $($builtImages.Count) images"

if ($builtImages.Count -gt 0) {
    Write-Host ""
    Write-Host "Built Images:" -ForegroundColor Green
    foreach ($img in $builtImages) {
        Write-Host "  ✓ $img" -ForegroundColor Green
    }
}

if ($failedImages.Count -gt 0) {
    Write-Host ""
    Write-Host "Failed Images:" -ForegroundColor Red
    foreach ($img in $failedImages) {
        Write-Host "  ✗ $img" -ForegroundColor Red
    }
    Write-Host ""
    Write-LogError "Some images failed to build"
    exit 1
}

# ============================================================================
# Push Images (Optional)
# ============================================================================
if (-not $NoPush) {
    Write-Host ""
    Write-LogSection "PUSHING IMAGES"
    Write-LogInfo "Pushing built images to registry..."
    Write-Host ""
    
    foreach ($img in $builtImages) {
        Write-LogInfo "Pushing: $img"
        
        try {
            docker push $img
            
            if ($LASTEXITCODE -eq 0) {
                Write-LogSuccess "Pushed: $img"
            } else {
                Write-LogWarn "Could not push: $img"
            }
        } catch {
            Write-LogWarn "Could not push: $img ($_)"
        }
        
        Write-Host ""
    }
}

# ============================================================================
# Final Summary
# ============================================================================
Write-Host ""
Write-LogSection "DOCKER BUILD COMPLETE"

if ($Mode -eq "native") {
    Write-LogInfo "Native mode images built successfully"
    Write-LogInfo "ML execution will use native .bollyenv environment"
    Write-LogInfo "Next steps:"
    Write-LogInfo "  1. Run: .\prepare-job.ps1 <input_media>"
    Write-LogInfo "  2. Run: .\run_pipeline.ps1 -Job <job-id>"
} elseif ($Mode -eq "docker-cpu") {
    Write-LogInfo "Docker CPU mode images built successfully"
    Write-LogInfo "All stages will run in Docker containers (CPU-only)"
    Write-LogInfo "Next steps:"
    Write-LogInfo "  1. Run: .\prepare-job.ps1 <input_media>"
    Write-LogInfo "  2. Run: .\run_pipeline.ps1 -Job <job-id> -Mode docker-cpu"
} elseif ($Mode -eq "docker-gpu") {
    Write-LogInfo "Docker GPU mode images built successfully"
    Write-LogInfo "All stages will run in Docker containers (CUDA-enabled)"
    Write-LogInfo "Next steps:"
    Write-LogInfo "  1. Run: .\prepare-job.ps1 <input_media>"
    Write-LogInfo "  2. Run: .\run_pipeline.ps1 -Job <job-id> -Mode docker-gpu"
}

Write-Host ""
Write-LogInfo "Total images: $($builtImages.Count)"
Write-LogInfo "Build time: $([math]::Round($duration, 1)) seconds"
Write-Host ""

exit 0
