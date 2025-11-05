# CP-WhisperX-App Docker Build Verification Test
# Tests critical base images with consistent logging

[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [string]$Registry
)

$ErrorActionPreference = "Stop"

# Load common logging
. "$PSScriptRoot\scripts\common-logging.ps1"

# Determine registry
if (-not $Registry) {
    if ($env:DOCKERHUB_USER) {
        $Registry = $env:DOCKERHUB_USER
    } else {
        $Registry = "rajiup"
    }
}

# Start
Write-LogSection "DOCKER BUILD VERIFICATION TEST"
Write-LogInfo "Registry: $Registry"

# Test Phase 1: base:cpu
Write-Host ""
Write-Host "Testing Phase 1: Building base:cpu..." -ForegroundColor Yellow
Write-Host ("-" * 60) -ForegroundColor Yellow
Write-LogInfo "Building $Registry/cp-whisperx-app-base:cpu"

docker build --build-arg REGISTRY=$Registry -t "$Registry/cp-whisperx-app-base:cpu" -f "docker\base\Dockerfile" .
if ($LASTEXITCODE -ne 0) {
    Write-LogError "[FAILED] base:cpu"
    exit 1
}
Write-LogSuccess "[SUCCESS] base:cpu built"

# Test Phase 2: base:cuda
Write-Host ""
Write-Host "Testing Phase 2: Building base:cuda..." -ForegroundColor Yellow
Write-Host ("-" * 60) -ForegroundColor Yellow
Write-LogInfo "Building $Registry/cp-whisperx-app-base:cuda"

docker build --build-arg REGISTRY=$Registry -t "$Registry/cp-whisperx-app-base:cuda" -f "docker\base-cuda\Dockerfile" .
if ($LASTEXITCODE -ne 0) {
    Write-LogError "[FAILED] base:cuda - This was the previously failing build"
    exit 1
}
Write-LogSuccess "[SUCCESS] base:cuda built (FIXED!)"

# Test Phase 3: base-ml:cuda
Write-Host ""
Write-Host "Testing Phase 3: Building base-ml:cuda..." -ForegroundColor Yellow
Write-Host ("-" * 60) -ForegroundColor Yellow
Write-LogInfo "Building $Registry/cp-whisperx-app-base-ml:cuda"

docker build --build-arg REGISTRY=$Registry -t "$Registry/cp-whisperx-app-base-ml:cuda" -f "docker\base-ml\Dockerfile" .
if ($LASTEXITCODE -ne 0) {
    Write-LogError "[FAILED] base-ml:cuda"
    exit 1
}
Write-LogSuccess "[SUCCESS] base-ml:cuda built"

# Verification Tests
Write-LogSection "VERIFICATION TESTS"

# Test 1: Python in base:cpu
Write-Host ""
Write-Host "Test 1: Verify Python in base:cpu" -ForegroundColor Yellow
Write-Host ("-" * 60) -ForegroundColor Yellow
docker run --rm "$Registry/cp-whisperx-app-base:cpu" python --version
if ($LASTEXITCODE -ne 0) {
    Write-LogError "[FAILED] Python test in base:cpu"
    exit 1
}
Write-LogSuccess "[SUCCESS] Python works in base:cpu"

# Test 2: Python and pip in base:cuda
Write-Host ""
Write-Host "Test 2: Verify Python and pip in base:cuda" -ForegroundColor Yellow
Write-Host ("-" * 60) -ForegroundColor Yellow
docker run --rm "$Registry/cp-whisperx-app-base:cuda" python --version
docker run --rm "$Registry/cp-whisperx-app-base:cuda" pip --version
if ($LASTEXITCODE -ne 0) {
    Write-LogError "[FAILED] Python/pip test in base:cuda"
    exit 1
}
Write-LogSuccess "[SUCCESS] Python and pip work in base:cuda (THIS IS THE FIX!)"

# Test 3: PyTorch in base-ml:cuda
Write-Host ""
Write-Host "Test 3: Verify PyTorch in base-ml:cuda" -ForegroundColor Yellow
Write-Host ("-" * 60) -ForegroundColor Yellow
docker run --rm "$Registry/cp-whisperx-app-base-ml:cuda" python -c "import torch; print(f'PyTorch {torch.__version__}')"
if ($LASTEXITCODE -ne 0) {
    Write-LogError "[FAILED] PyTorch test in base-ml:cuda"
    exit 1
}
Write-LogSuccess "[SUCCESS] PyTorch works in base-ml:cuda"

# Success
Write-LogSection "ALL TESTS PASSED"
Write-LogSuccess "The Docker build issue is FIXED"
Write-Host ""
Write-Host "You can now run: .\scripts\build-all-images.ps1"
Write-Host ""

exit 0
