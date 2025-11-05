# CP-WhisperX-App Docker Build Verification Test
# Tests critical base images with consistent logging

[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [string]$Registry
)

$ErrorActionPreference = "Stop"

# Logging functions
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [docker-test] [$Level] $Message"
    
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

function Write-TestHeader {
    param([string]$Title)
    Write-Host ""
    Write-Host $Title -ForegroundColor Yellow
    Write-Host ("-" * 60) -ForegroundColor Yellow
}

# Determine registry
if (-not $Registry) {
    if ($env:DOCKERHUB_USER) {
        $Registry = $env:DOCKERHUB_USER
    } else {
        $Registry = "rajiup"
    }
}

# Start
Write-Header "DOCKER BUILD VERIFICATION TEST"
Write-Log "Registry: $Registry" "INFO"

# Test Phase 1: base:cpu
Write-TestHeader "Testing Phase 1: Building base:cpu..."
Write-Log "Building $Registry/cp-whisperx-app-base:cpu" "INFO"

docker build --build-arg REGISTRY=$Registry -t "$Registry/cp-whisperx-app-base:cpu" -f "docker\base\Dockerfile" .
if ($LASTEXITCODE -ne 0) {
    Write-Log "[FAILED] base:cpu" "ERROR"
    exit 1
}
Write-Log "[SUCCESS] base:cpu built" "SUCCESS"

# Test Phase 2: base:cuda
Write-TestHeader "Testing Phase 2: Building base:cuda..."
Write-Log "Building $Registry/cp-whisperx-app-base:cuda" "INFO"

docker build --build-arg REGISTRY=$Registry -t "$Registry/cp-whisperx-app-base:cuda" -f "docker\base-cuda\Dockerfile" .
if ($LASTEXITCODE -ne 0) {
    Write-Log "[FAILED] base:cuda - This was the previously failing build" "ERROR"
    exit 1
}
Write-Log "[SUCCESS] base:cuda built (FIXED!)" "SUCCESS"

# Test Phase 3: base-ml:cuda
Write-TestHeader "Testing Phase 3: Building base-ml:cuda..."
Write-Log "Building $Registry/cp-whisperx-app-base-ml:cuda" "INFO"

docker build --build-arg REGISTRY=$Registry -t "$Registry/cp-whisperx-app-base-ml:cuda" -f "docker\base-ml\Dockerfile" .
if ($LASTEXITCODE -ne 0) {
    Write-Log "[FAILED] base-ml:cuda" "ERROR"
    exit 1
}
Write-Log "[SUCCESS] base-ml:cuda built" "SUCCESS"

# Verification Tests
Write-Header "VERIFICATION TESTS"

# Test 1: Python in base:cpu
Write-TestHeader "Test 1: Verify Python in base:cpu"
docker run --rm "$Registry/cp-whisperx-app-base:cpu" python --version
if ($LASTEXITCODE -ne 0) {
    Write-Log "[FAILED] Python test in base:cpu" "ERROR"
    exit 1
}
Write-Log "[SUCCESS] Python works in base:cpu" "SUCCESS"

# Test 2: Python and pip in base:cuda
Write-TestHeader "Test 2: Verify Python and pip in base:cuda"
docker run --rm "$Registry/cp-whisperx-app-base:cuda" python --version
docker run --rm "$Registry/cp-whisperx-app-base:cuda" pip --version
if ($LASTEXITCODE -ne 0) {
    Write-Log "[FAILED] Python/pip test in base:cuda" "ERROR"
    exit 1
}
Write-Log "[SUCCESS] Python and pip work in base:cuda (THIS IS THE FIX!)" "SUCCESS"

# Test 3: PyTorch in base-ml:cuda
Write-TestHeader "Test 3: Verify PyTorch in base-ml:cuda"
docker run --rm "$Registry/cp-whisperx-app-base-ml:cuda" python -c "import torch; print(f'PyTorch {torch.__version__}')"
if ($LASTEXITCODE -ne 0) {
    Write-Log "[FAILED] PyTorch test in base-ml:cuda" "ERROR"
    exit 1
}
Write-Log "[SUCCESS] PyTorch works in base-ml:cuda" "SUCCESS"

# Success
Write-Header "ALL TESTS PASSED"
Write-Log "The Docker build issue is FIXED" "SUCCESS"
Write-Host ""
Write-Host "You can now run: .\scripts\build-all-images.ps1"
Write-Host ""

exit 0
