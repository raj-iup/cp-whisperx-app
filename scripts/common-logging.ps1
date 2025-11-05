# Common Logging Module for PowerShell Scripts
# Provides consistent logging functions across all scripts

# Usage:
#   . .\scripts\common-logging.ps1
#   Write-Log "Message" "INFO"
#   Write-LogSection "Section Title"

# Auto-initialize logging for the calling script
function Initialize-Logging {
    param([string]$CallingScript)
    
    # Extract script name without extension
    $scriptName = [System.IO.Path]::GetFileNameWithoutExtension($CallingScript)
    
    # Create logs directory if it doesn't exist
    $logsDir = Join-Path $PSScriptRoot "..\logs"
    if (-not (Test-Path $logsDir)) {
        New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
    }
    
    # Generate log filename: YYYYMMDD-HHMMSS-scriptname.log
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $logFileName = "$timestamp-$scriptName.log"
    $logFilePath = Join-Path $logsDir $logFileName
    
    return $logFilePath
}

# Environment variables
$script:LogLevel = if ($env:LOG_LEVEL) { $env:LOG_LEVEL } else { "INFO" }

# Auto-create log file if not explicitly set
if (-not $env:LOG_FILE) {
    # Get the calling script path (skip common-logging.ps1 itself)
    $callingScript = Get-PSCallStack | Where-Object { $_.ScriptName -and $_.ScriptName -notmatch 'common-logging\.ps1$' } | Select-Object -First 1 -ExpandProperty ScriptName
    
    if ($callingScript) {
        $script:LogFile = Initialize-Logging -CallingScript $callingScript
    } else {
        $script:LogFile = $null
    }
} else {
    $script:LogFile = $env:LOG_FILE
}

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

# Functions are automatically available when dot-sourced
# No need for Export-ModuleMember in a .ps1 file

# Show usage if run directly (check if script is being run, not dot-sourced)
if ($MyInvocation.InvocationName -ne '.' -and $MyInvocation.InvocationName -notlike '*\*') {
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
    Write-Host "Automatic Logging:" -ForegroundColor Yellow
    Write-Host "  Log files are automatically created in logs/ directory" -ForegroundColor Gray
    Write-Host "  Format: YYYYMMDD-HHMMSS-scriptname.log" -ForegroundColor Gray
    Write-Host "  Example: 20251105-113045-build-all-images.log" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Environment Variables:" -ForegroundColor Yellow
    Write-Host "  LOG_LEVEL - Set to DEBUG to see debug messages (default: INFO)" -ForegroundColor Gray
    Write-Host "  LOG_FILE  - Override automatic log file path (optional)" -ForegroundColor Gray
    Write-Host ""
}
