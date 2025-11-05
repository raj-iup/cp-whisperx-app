# CP-WhisperX-App Preflight Checks
# PowerShell wrapper for preflight.py with consistent logging

[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [switch]$Force
)

$ErrorActionPreference = "Stop"

# Logging functions
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [preflight] [$Level] $Message"
    
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
Write-Header "CP-WHISPERX-APP PREFLIGHT CHECKS"
Write-Log "Starting preflight validation..." "INFO"

# Validate Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Log "Python not found. Please install Python 3.9+" "ERROR"
    exit 1
}

# Build arguments
$pythonArgs = @("preflight.py")

if ($Force) {
    $pythonArgs += "--force"
    Write-Log "Force mode: ENABLED" "INFO"
}

# Execute Python script
Write-Log "Executing: python $($pythonArgs -join ' ')" "INFO"
Write-Host ""

try {
    & python @pythonArgs
    
    if ($LASTEXITCODE -eq 0) {
        Write-Log "Preflight checks passed" "SUCCESS"
        Write-Host ""
        exit 0
    } else {
        Write-Log "Preflight checks failed with exit code $LASTEXITCODE" "ERROR"
        Write-Host ""
        exit $LASTEXITCODE
    }
} catch {
    Write-Log "Unexpected error: $_" "ERROR"
    exit 1
}
