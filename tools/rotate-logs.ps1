# ============================================================================
# Log Rotation Script for CP-WhisperX-App (PowerShell)
# ============================================================================
# Rotates log files to prevent disk space issues
# Can be run manually or via Windows Task Scheduler
#
# Usage: .\tools\rotate-logs.ps1 [OPTIONS]
# ============================================================================

param(
    [Parameter()]
    [int]$KeepDays = 30,
    
    [Parameter()]
    [switch]$NoCompress,
    
    [Parameter()]
    [switch]$DryRun,
    
    [Parameter()]
    [switch]$Help
)

function Show-Usage {
    Write-Host @"
Usage: .\tools\rotate-logs.ps1 [OPTIONS]

Rotate log files to save disk space

OPTIONS:
  -KeepDays N           Keep logs for N days (default: 30)
  -NoCompress           Don't compress archived logs
  -DryRun               Show what would be done without doing it
  -Help                 Show this help message

EXAMPLES:
  # Keep 7 days of logs
  .\tools\rotate-logs.ps1 -KeepDays 7
  
  # Dry run to see what would be deleted
  .\tools\rotate-logs.ps1 -DryRun
  
  # Keep 90 days without compression
  .\tools\rotate-logs.ps1 -KeepDays 90 -NoCompress

TASK SCHEDULER EXAMPLE:
  # Run daily at 2 AM
  Action: PowerShell.exe
  Arguments: -File C:\path\to\cp-whisperx-app\tools\rotate-logs.ps1 -KeepDays 30

"@
    exit 0
}

if ($Help) {
    Show-Usage
}

# Load common logging
$ProjectRoot = Split-Path -Parent $PSScriptRoot
. "$ProjectRoot\scripts\common-logging.ps1"

Write-LogSection "LOG ROTATION"
Write-LogInfo "Logs directory: $ProjectRoot\logs"
Write-LogInfo "Keep days: $KeepDays"
Write-LogInfo "Compress: $(-not $NoCompress)"
Write-LogInfo "Dry run: $DryRun"
Write-Host ""

# Check if logs directory exists
$LogsDir = Join-Path $ProjectRoot "logs"
if (-not (Test-Path $LogsDir)) {
    Write-LogError "Logs directory not found: $LogsDir"
    exit 1
}

# ============================================================================
# Find old log files
# ============================================================================
Write-LogInfo "Finding log files older than $KeepDays days..."

$CutoffDate = (Get-Date).AddDays(-$KeepDays)
$OldLogs = Get-ChildItem -Path $LogsDir -Filter "*.log" -File | Where-Object {
    $_.LastWriteTime -lt $CutoffDate
}

if ($OldLogs.Count -eq 0) {
    Write-LogSuccess "No old log files found"
    exit 0
}

$LogCount = $OldLogs.Count
$TotalSize = ($OldLogs | Measure-Object -Property Length -Sum).Sum
$TotalSizeFormatted = if ($TotalSize -gt 1GB) {
    "{0:N2} GB" -f ($TotalSize / 1GB)
} elseif ($TotalSize -gt 1MB) {
    "{0:N2} MB" -f ($TotalSize / 1MB)
} else {
    "{0:N2} KB" -f ($TotalSize / 1KB)
}

Write-LogInfo "Found $LogCount log files ($TotalSizeFormatted total)"
Write-Host ""

# ============================================================================
# Compress old logs (if enabled)
# ============================================================================
if (-not $NoCompress) {
    Write-LogInfo "Compressing old logs..."
    
    $ArchiveDate = Get-Date -Format "yyyyMMdd-HHmmss"
    $ArchiveName = "logs-archive-$ArchiveDate.zip"
    $ArchivePath = Join-Path $LogsDir $ArchiveName
    
    if ($DryRun) {
        Write-LogInfo "[DRY RUN] Would create archive: $ArchiveName"
        foreach ($log in $OldLogs) {
            Write-LogInfo "[DRY RUN] Would archive: $($log.Name)"
        }
    } else {
        # Create archive using .NET compression
        try {
            Add-Type -AssemblyName System.IO.Compression.FileSystem
            
            $compression = [System.IO.Compression.CompressionLevel]::Optimal
            $archive = [System.IO.Compression.ZipFile]::Open($ArchivePath, 'Create')
            
            foreach ($log in $OldLogs) {
                $entryName = $log.Name
                [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
                    $archive,
                    $log.FullName,
                    $entryName,
                    $compression
                ) | Out-Null
            }
            
            $archive.Dispose()
            
            $ArchiveSize = (Get-Item $ArchivePath).Length
            $ArchiveSizeFormatted = if ($ArchiveSize -gt 1MB) {
                "{0:N2} MB" -f ($ArchiveSize / 1MB)
            } else {
                "{0:N2} KB" -f ($ArchiveSize / 1KB)
            }
            
            Write-LogSuccess "Created archive: $ArchiveName ($ArchiveSizeFormatted)"
        } catch {
            Write-LogError "Failed to create archive: $_"
        }
    }
    
    Write-Host ""
}

# ============================================================================
# Delete old logs
# ============================================================================
Write-LogInfo "Deleting old log files..."

if ($DryRun) {
    foreach ($log in $OldLogs) {
        Write-LogInfo "[DRY RUN] Would delete: $($log.Name)"
    }
    Write-LogInfo "[DRY RUN] No files were actually deleted"
} else {
    foreach ($log in $OldLogs) {
        Remove-Item $log.FullName -Force
        Write-LogDebug "Deleted: $($log.Name)"
    }
    Write-LogSuccess "Deleted $LogCount old log files"
}

Write-Host ""

# ============================================================================
# Summary
# ============================================================================
Write-LogInfo "Log rotation summary:"
Write-LogInfo "  • Processed: $LogCount files ($TotalSizeFormatted)"
if (-not $NoCompress -and -not $DryRun) {
    Write-LogInfo "  • Archived: $ArchiveName"
}
Write-LogInfo "  • Freed space: $TotalSizeFormatted"

if ($DryRun) {
    Write-LogWarn "Dry run mode - no changes were made"
    Write-LogInfo "Run without -DryRun to actually rotate logs"
}

Write-LogSuccess "Log rotation complete"
