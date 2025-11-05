# CP-WhisperX-App Preflight Checks
# PowerShell wrapper for preflight.py with consistent logging

[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [switch]$Force
)

$ErrorActionPreference = "Stop"

# Load common logging
. "$PSScriptRoot\scripts\common-logging.ps1"

# Start
Write-LogSection "CP-WHISPERX-APP PREFLIGHT CHECKS"
Write-LogInfo "Starting preflight validation..."

# Validate Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-LogError "Python not found. Please install Python 3.9+"
    exit 1
}

# Build arguments
$pythonArgs = @("preflight.py")

if ($Force) {
    $pythonArgs += "--force"
    Write-LogInfo "Force mode: ENABLED"
}

# Execute Python script
Write-LogInfo "Executing: python $($pythonArgs -join ' ')"
Write-Host ""

try {
    & python @pythonArgs
    
    if ($LASTEXITCODE -eq 0) {
        Write-LogSuccess "Preflight checks passed"
        Write-Host ""
        exit 0
    } else {
        Write-LogError "Preflight checks failed with exit code $LASTEXITCODE"
        Write-Host ""
        exit $LASTEXITCODE
    }
} catch {
    Write-LogError "Unexpected error: $_"
    exit 1
}
