# CP-WhisperX-App Docker Push Monitor
# Monitor Docker push progress with consistent logging

$ErrorActionPreference = "Continue"

# Logging functions
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [push-monitor] [$Level] $Message"
    
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

# Set window title
$host.UI.RawUI.WindowTitle = "Docker Push Monitor"

Write-Header "DOCKER PUSH MONITOR"
Write-Log "Monitoring push_all.log for progress..." "INFO"
Write-Host ""
Write-Host "Press Ctrl+C to exit monitor" -ForegroundColor Yellow
Write-Host ""

# Monitor loop
while ($true) {
    Clear-Host
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "Docker Push Progress - $timestamp" -ForegroundColor Cyan
    Write-Host ("=" * 60) -ForegroundColor Cyan
    Write-Host ""
    
    if (Test-Path "push_all.log") {
        Get-Content "push_all.log" -Tail 30 | ForEach-Object {
            if ($_ -match "ERROR|FAILED") {
                Write-Host $_ -ForegroundColor Red
            } elseif ($_ -match "SUCCESS|Complete") {
                Write-Host $_ -ForegroundColor Green
            } elseif ($_ -match "WARNING") {
                Write-Host $_ -ForegroundColor Yellow
            } else {
                Write-Host $_
            }
        }
    } else {
        Write-Host "Waiting for push to start..." -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host ("=" * 60) -ForegroundColor Cyan
    Write-Host "Press Ctrl+C to exit monitor" -ForegroundColor Yellow
    Write-Host ""
    
    Start-Sleep -Seconds 10
}
