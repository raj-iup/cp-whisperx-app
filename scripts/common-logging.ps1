# Common Logging Module for PowerShell Scripts
# Provides consistent logging functions across all scripts

# Usage:
#   . .\scripts\common-logging.ps1
#   Write-Log "Message" "INFO"
#   Write-LogSection "Section Title"

# Environment variables
$script:LogLevel = if ($env:LOG_LEVEL) { $env:LOG_LEVEL } else { "INFO" }
$script:LogFile = $env:LOG_FILE

function Write-LogMessage {
    param(
        [string]$Message,
        [string]$Level = "INFO",
        [switch]$ToStdErr
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    
    # Console output with colors
    switch ($Level) {
        "DEBUG" {
            if ($script:LogLevel -eq "DEBUG") {
                Write-Host $logMessage -ForegroundColor DarkGray
            }
        }
        "INFO" { Write-Host $logMessage }
        "WARN" { Write-Host $logMessage -ForegroundColor Yellow }
        "ERROR" {
            if ($ToStdErr) {
                [Console]::Error.WriteLine($logMessage)
            } else {
                Write-Host $logMessage -ForegroundColor Red
            }
        }
        "CRITICAL" {
            if ($ToStdErr) {
                [Console]::Error.WriteLine($logMessage)
            } else {
                Write-Host $logMessage -ForegroundColor Red -BackgroundColor Black
            }
        }
        "SUCCESS" { Write-Host $logMessage -ForegroundColor Green }
        "FAILURE" {
            if ($ToStdErr) {
                [Console]::Error.WriteLine($logMessage)
            } else {
                Write-Host $logMessage -ForegroundColor Red
            }
        }
        default { Write-Host $logMessage }
    }
    
    # File output if LOG_FILE is set
    if ($script:LogFile) {
        Add-Content -Path $script:LogFile -Value $logMessage
    }
}

function Write-LogDebug {
    param([string]$Message)
    Write-LogMessage -Message $Message -Level "DEBUG"
}

function Write-LogInfo {
    param([string]$Message)
    Write-LogMessage -Message $Message -Level "INFO"
}

function Write-LogWarn {
    param([string]$Message)
    Write-LogMessage -Message $Message -Level "WARN"
}

function Write-LogError {
    param([string]$Message)
    Write-LogMessage -Message $Message -Level "ERROR" -ToStdErr
}

function Write-LogCritical {
    param([string]$Message)
    Write-LogMessage -Message $Message -Level "CRITICAL" -ToStdErr
}

function Write-LogSuccess {
    param([string]$Message)
    Write-LogMessage -Message $Message -Level "SUCCESS"
}

function Write-LogFailure {
    param([string]$Message)
    Write-LogMessage -Message $Message -Level "FAILURE" -ToStdErr
}

function Write-LogSection {
    param([string]$Title)
    
    $separator = "=" * 70
    Write-Host $separator -ForegroundColor Cyan
    Write-Host $Title -ForegroundColor Cyan
    Write-Host $separator -ForegroundColor Cyan
    
    if ($script:LogFile) {
        Add-Content -Path $script:LogFile -Value $separator
        Add-Content -Path $script:LogFile -Value $Title
        Add-Content -Path $script:LogFile -Value $separator
    }
}

# Export functions for use in other scripts
Export-ModuleMember -Function Write-LogMessage, Write-LogDebug, Write-LogInfo, `
                              Write-LogWarn, Write-LogError, Write-LogCritical, `
                              Write-LogSuccess, Write-LogFailure, Write-LogSection

# Show usage if run directly
if ($MyInvocation.InvocationName -eq "common-logging.ps1") {
    Write-Host ""
    Write-Host "Common Logging Functions for PowerShell Scripts" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Yellow
    Write-Host "  . .\scripts\common-logging.ps1" -ForegroundColor Gray
    Write-Host "  Write-LogInfo 'message'" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Functions:" -ForegroundColor Yellow
    Write-Host "  Write-LogDebug     - Debug message (only if LOG_LEVEL=DEBUG)" -ForegroundColor Gray
    Write-Host "  Write-LogInfo      - Info message" -ForegroundColor Gray
    Write-Host "  Write-LogWarn      - Warning message" -ForegroundColor Gray
    Write-Host "  Write-LogError     - Error message (to stderr)" -ForegroundColor Gray
    Write-Host "  Write-LogCritical  - Critical error (to stderr)" -ForegroundColor Gray
    Write-Host "  Write-LogSuccess   - Success message" -ForegroundColor Gray
    Write-Host "  Write-LogFailure   - Failure message" -ForegroundColor Gray
    Write-Host "  Write-LogSection   - Section header" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Environment Variables:" -ForegroundColor Yellow
    Write-Host "  LOG_LEVEL - Set to DEBUG to see debug messages (default: INFO)" -ForegroundColor Gray
    Write-Host "  LOG_FILE  - Set to file path to enable file logging" -ForegroundColor Gray
    Write-Host ""
}
