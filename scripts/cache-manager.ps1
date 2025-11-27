# ============================================================================
# Cache Manager for CP-WhisperX-App (PowerShell)
# ============================================================================
# Manage ML model caches and application caches
#
# Usage:
#   .\scripts\cache-manager.ps1 -Action status       - Show cache status
#   .\scripts\cache-manager.ps1 -Action clear-models - Clear ML model caches
#   .\scripts\cache-manager.ps1 -Action clear-app    - Clear application caches
#   .\scripts\cache-manager.ps1 -Action clear-all    - Clear all caches
# ============================================================================

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("status", "clear-models", "clear-app", "clear-all")]
    [string]$Action
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir

# Helper functions
function Get-DirectorySize {
    param([string]$Path)
    
    if (Test-Path $Path) {
        $size = (Get-ChildItem -Path $Path -Recurse -File -ErrorAction SilentlyContinue | 
                Measure-Object -Property Length -Sum).Sum
        
        if ($size -gt 1GB) {
            return "{0:N2} GB" -f ($size / 1GB)
        } elseif ($size -gt 1MB) {
            return "{0:N2} MB" -f ($size / 1MB)
        } elseif ($size -gt 1KB) {
            return "{0:N2} KB" -f ($size / 1KB)
        } else {
            return "$size B"
        }
    }
    return "0 B"
}

function Get-FileCount {
    param([string]$Path)
    
    if (Test-Path $Path) {
        return (Get-ChildItem -Path $Path -Recurse -File -ErrorAction SilentlyContinue).Count
    }
    return 0
}

function Show-Status {
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Blue
    Write-Host "               CACHE STATUS                                " -ForegroundColor Blue
    Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Blue
    Write-Host ""
    
    Write-Host "ML Model Caches:" -ForegroundColor Green
    Write-Host ""
    
    # Torch cache
    $torchCache = Join-Path $projectRoot ".cache\torch"
    if (Test-Path $torchCache) {
        $torchSize = Get-DirectorySize $torchCache
        $torchFiles = Get-FileCount $torchCache
        Write-Host "  📦 Torch/Whisper Models"
        Write-Host "     Location: .cache\torch\"
        Write-Host "     Size:     $torchSize"
        Write-Host "     Files:    $torchFiles"
        Write-Host ""
    }
    
    # HuggingFace cache
    $hfCache = Join-Path $projectRoot ".cache\huggingface"
    if (Test-Path $hfCache) {
        $hfSize = Get-DirectorySize $hfCache
        $hfFiles = Get-FileCount $hfCache
        Write-Host "  🤗 HuggingFace Models"
        Write-Host "     Location: .cache\huggingface\"
        Write-Host "     Size:     $hfSize"
        Write-Host "     Files:    $hfFiles"
        Write-Host ""
    }
    
    # MLX cache
    $mlxCache = Join-Path $projectRoot ".cache\mlx"
    if (Test-Path $mlxCache) {
        $mlxSize = Get-DirectorySize $mlxCache
        $mlxFiles = Get-FileCount $mlxCache
        Write-Host "  🍎 MLX Models (Apple Silicon)"
        Write-Host "     Location: .cache\mlx\"
        Write-Host "     Size:     $mlxSize"
        Write-Host "     Files:    $mlxFiles"
        Write-Host ""
    }
    
    # Total ML cache
    $totalMLCache = Join-Path $projectRoot ".cache"
    $totalMLSize = Get-DirectorySize $totalMLCache
    Write-Host "  Total ML Cache: $totalMLSize" -ForegroundColor Yellow
    Write-Host ""
    
    Write-Host "Application Caches:" -ForegroundColor Green
    Write-Host ""
    
    # TMDB cache
    $tmdbCache = Join-Path $projectRoot "out\tmdb_cache"
    if (Test-Path $tmdbCache) {
        $tmdbSize = Get-DirectorySize $tmdbCache
        $tmdbFiles = Get-FileCount $tmdbCache
        Write-Host "  🎬 TMDB Metadata"
        Write-Host "     Location: out\tmdb_cache\"
        Write-Host "     Size:     $tmdbSize"
        Write-Host "     Files:    $tmdbFiles"
        Write-Host ""
    }
    
    # MusicBrainz cache
    $mbCache = Join-Path $projectRoot "out\musicbrainz_cache"
    if (Test-Path $mbCache) {
        $mbSize = Get-DirectorySize $mbCache
        $mbFiles = Get-FileCount $mbCache
        Write-Host "  🎵 MusicBrainz Metadata"
        Write-Host "     Location: out\musicbrainz_cache\"
        Write-Host "     Size:     $mbSize"
        Write-Host "     Files:    $mbFiles"
        Write-Host ""
    }
    
    # Glossary cache
    $glossaryCache = Join-Path $projectRoot "glossary\cache"
    if (Test-Path $glossaryCache) {
        $glossarySize = Get-DirectorySize $glossaryCache
        $glossaryFiles = Get-FileCount $glossaryCache
        Write-Host "  📖 Glossary Cache"
        Write-Host "     Location: glossary\cache\"
        Write-Host "     Size:     $glossarySize"
        Write-Host "     Files:    $glossaryFiles"
        Write-Host ""
    }
    
    # Legacy cache
    $legacyCache = Join-Path $projectRoot "shared\model-cache"
    if (Test-Path $legacyCache) {
        $legacyFiles = Get-FileCount $legacyCache
        if ($legacyFiles -gt 0) {
            $legacySize = Get-DirectorySize $legacyCache
            Write-Host "  ⚠️  Legacy Model Cache (should be empty)" -ForegroundColor Red
            Write-Host "     Location: shared\model-cache\"
            Write-Host "     Size:     $legacySize"
            Write-Host "     Files:    $legacyFiles"
            Write-Host ""
        }
    }
    
    Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Blue
    Write-Host ""
    Write-Host "Tips:" -ForegroundColor Yellow
    Write-Host "  • ML caches will re-download on next use if cleared"
    Write-Host "  • Application caches use 90-day expiry"
    Write-Host "  • To free space: .\scripts\cache-manager.ps1 -Action clear-models"
    Write-Host ""
}

function Clear-Models {
    Write-Host ""
    Write-Host "Clearing ML model caches..." -ForegroundColor Yellow
    Write-Host ""
    
    # Confirm
    $confirm = Read-Host "This will delete all cached models. Continue? [y/N]"
    if ($confirm -ne "y" -and $confirm -ne "Y") {
        Write-Host "Cancelled."
        exit 0
    }
    
    # Clear torch cache
    $torchCache = Join-Path $projectRoot ".cache\torch"
    if (Test-Path $torchCache) {
        Write-Host "  Clearing Torch/Whisper cache..."
        Remove-Item -Path $torchCache -Recurse -Force
        Write-Host "  ✓ Torch cache cleared" -ForegroundColor Green
    }
    
    # Clear HuggingFace cache
    $hfCache = Join-Path $projectRoot ".cache\huggingface"
    if (Test-Path $hfCache) {
        Write-Host "  Clearing HuggingFace cache..."
        Remove-Item -Path $hfCache -Recurse -Force
        Write-Host "  ✓ HuggingFace cache cleared" -ForegroundColor Green
    }
    
    # Clear MLX cache
    $mlxCache = Join-Path $projectRoot ".cache\mlx"
    if (Test-Path $mlxCache) {
        Write-Host "  Clearing MLX cache..."
        Remove-Item -Path $mlxCache -Recurse -Force
        Write-Host "  ✓ MLX cache cleared" -ForegroundColor Green
    }
    
    # Recreate directories
    New-Item -ItemType Directory -Path (Join-Path $projectRoot ".cache\torch") -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $projectRoot ".cache\huggingface") -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $projectRoot ".cache\mlx") -Force | Out-Null
    
    Write-Host ""
    Write-Host "Model caches cleared successfully" -ForegroundColor Green
    Write-Host "Models will re-download on next use" -ForegroundColor Yellow
    Write-Host ""
}

function Clear-AppCaches {
    Write-Host ""
    Write-Host "Clearing application caches..." -ForegroundColor Yellow
    Write-Host ""
    
    # Clear TMDB cache
    $tmdbCache = Join-Path $projectRoot "out\tmdb_cache"
    if (Test-Path $tmdbCache) {
        Write-Host "  Clearing TMDB cache..."
        Remove-Item -Path $tmdbCache -Recurse -Force
        Write-Host "  ✓ TMDB cache cleared" -ForegroundColor Green
    }
    
    # Clear MusicBrainz cache
    $mbCache = Join-Path $projectRoot "out\musicbrainz_cache"
    if (Test-Path $mbCache) {
        Write-Host "  Clearing MusicBrainz cache..."
        Remove-Item -Path $mbCache -Recurse -Force
        Write-Host "  ✓ MusicBrainz cache cleared" -ForegroundColor Green
    }
    
    # Clear Glossary cache
    $glossaryCache = Join-Path $projectRoot "glossary\cache"
    if (Test-Path $glossaryCache) {
        Write-Host "  Clearing Glossary cache..."
        Remove-Item -Path $glossaryCache -Recurse -Force
        New-Item -ItemType Directory -Path $glossaryCache -Force | Out-Null
        Write-Host "  ✓ Glossary cache cleared" -ForegroundColor Green
    }
    
    Write-Host ""
    Write-Host "Application caches cleared successfully" -ForegroundColor Green
    Write-Host ""
}

function Clear-AllCaches {
    Write-Host ""
    Write-Host "⚠️  WARNING: This will clear ALL caches" -ForegroundColor Red
    Write-Host ""
    
    # Confirm
    $confirm = Read-Host "Continue? [y/N]"
    if ($confirm -ne "y" -and $confirm -ne "Y") {
        Write-Host "Cancelled."
        exit 0
    }
    
    Clear-Models
    Clear-AppCaches
    
    Write-Host "All caches cleared successfully" -ForegroundColor Green
    Write-Host ""
}

# Main dispatcher
switch ($Action) {
    "status" {
        Show-Status
    }
    "clear-models" {
        Clear-Models
    }
    "clear-app" {
        Clear-AppCaches
    }
    "clear-all" {
        Clear-AllCaches
    }
}
