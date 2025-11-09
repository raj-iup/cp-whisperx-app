# Finalize Output - Organize final output into title-based directory
# Usage: .\finalize-output.ps1 <job-id>

param(
    [Parameter(Mandatory=$true)]
    [string]$JobId
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = $ScriptDir

# Colors (for PowerShell 5.1+)
$Red = "Red"
$Green = "Green"
$Yellow = "Yellow"

# Find job directory
Write-Host "Searching for job: $JobId" -ForegroundColor $Yellow

$JobDir = Get-ChildItem -Path "$ProjectRoot\out" -Directory -Recurse -Filter $JobId -ErrorAction SilentlyContinue | Select-Object -First 1

if (-not $JobDir) {
    Write-Host "✗ Job not found: $JobId" -ForegroundColor $Red
    exit 1
}

Write-Host "Found job directory: $($JobDir.FullName)" -ForegroundColor $Green
Write-Host ""

# Run finalization
try {
    & python "$ProjectRoot\scripts\finalize_output.py" $JobDir.FullName
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✓ Finalization completed successfully" -ForegroundColor $Green
    } else {
        Write-Host ""
        Write-Host "✗ Finalization failed" -ForegroundColor $Red
        exit 1
    }
}
catch {
    Write-Host ""
    Write-Host "✗ Error during finalization: $_" -ForegroundColor $Red
    exit 1
}
