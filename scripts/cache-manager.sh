#!/usr/bin/env bash
# ============================================================================
# Cache Manager for CP-WhisperX-App
# ============================================================================
# Manage ML model caches and application caches
#
# Usage:
#   ./scripts/cache-manager.sh status       - Show cache status
#   ./scripts/cache-manager.sh clear-models - Clear ML model caches
#   ./scripts/cache-manager.sh clear-app    - Clear application caches
#   ./scripts/cache-manager.sh clear-all    - Clear all caches
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Source common logging
source "$SCRIPT_DIR/common-logging.sh"

# Function to display size
display_size() {
    local path=$1
    if [ -d "$path" ]; then
        du -sh "$path" 2>/dev/null | awk '{print $1}'
    else
        echo "0B"
    fi
}

# Function to count files
count_files() {
    local path=$1
    if [ -d "$path" ]; then
        find "$path" -type f 2>/dev/null | wc -l | tr -d ' '
    else
        echo "0"
    fi
}

# Status display
show_status() {
    log_section "CACHE STATUS"
    
    log_info "ML Model Caches:"
    echo ""
    log_debug "Checking ML model cache directories"
    
    # Torch cache
    local torch_cache="$PROJECT_ROOT/.cache/torch"
    local torch_size=$(display_size "$torch_cache")
    local torch_files=$(count_files "$torch_cache")
    if [ -d "$torch_cache" ]; then
        log_info "  📦 Torch/Whisper Models"
        log_info "     Location: .cache/torch/"
        log_info "     Size:     $torch_size"
        log_info "     Files:    $torch_files"
        log_debug "Torch cache: $torch_size, $torch_files files"
        echo ""
    fi
    
    # HuggingFace cache
    local hf_cache="$PROJECT_ROOT/.cache/huggingface"
    local hf_size=$(display_size "$hf_cache")
    local hf_files=$(count_files "$hf_cache")
    if [ -d "$hf_cache" ]; then
        log_info "  🤗 HuggingFace Models"
        log_info "     Location: .cache/huggingface/"
        log_info "     Size:     $hf_size"
        log_info "     Files:    $hf_files"
        log_debug "HuggingFace cache: $hf_size, $hf_files files"
        echo ""
    fi
    
    # MLX cache
    local mlx_cache="$PROJECT_ROOT/.cache/mlx"
    local mlx_size=$(display_size "$mlx_cache")
    local mlx_files=$(count_files "$mlx_cache")
    if [ -d "$mlx_cache" ]; then
        log_info "  🍎 MLX Models (Apple Silicon)"
        log_info "     Location: .cache/mlx/"
        log_info "     Size:     $mlx_size"
        log_info "     Files:    $mlx_files"
        log_debug "MLX cache: $mlx_size, $mlx_files files"
        echo ""
    fi
    
    # Total ML cache
    local total_ml_cache="$PROJECT_ROOT/.cache"
    local total_ml_size=$(display_size "$total_ml_cache")
    log_warn "  Total ML Cache: $total_ml_size"
    echo ""
    
    log_info "Application Caches:"
    echo ""
    log_debug "Checking application cache directories"
    
    # TMDB cache
    local tmdb_cache="$PROJECT_ROOT/out/tmdb_cache"
    local tmdb_size=$(display_size "$tmdb_cache")
    local tmdb_files=$(count_files "$tmdb_cache")
    if [ -d "$tmdb_cache" ]; then
        log_info "  🎬 TMDB Metadata"
        log_info "     Location: out/tmdb_cache/"
        log_info "     Size:     $tmdb_size"
        log_info "     Files:    $tmdb_files"
        log_debug "TMDB cache: $tmdb_size, $tmdb_files files"
        echo ""
    fi
    
    # MusicBrainz cache
    local mb_cache="$PROJECT_ROOT/out/musicbrainz_cache"
    local mb_size=$(display_size "$mb_cache")
    local mb_files=$(count_files "$mb_cache")
    if [ -d "$mb_cache" ]; then
        log_info "  🎵 MusicBrainz Metadata"
        log_info "     Location: out/musicbrainz_cache/"
        log_info "     Size:     $mb_size"
        log_info "     Files:    $mb_files"
        log_debug "MusicBrainz cache: $mb_size, $mb_files files"
        echo ""
    fi
    
    # Glossary cache
    local glossary_cache="$PROJECT_ROOT/glossary/cache"
    local glossary_size=$(display_size "$glossary_cache")
    local glossary_files=$(count_files "$glossary_cache")
    if [ -d "$glossary_cache" ]; then
        log_info "  📖 Glossary Cache"
        log_info "     Location: glossary/cache/"
        log_info "     Size:     $glossary_size"
        log_info "     Files:    $glossary_files"
        log_debug "Glossary cache: $glossary_size, $glossary_files files"
        echo ""
    fi
    
    # Legacy cache
    local legacy_cache="$PROJECT_ROOT/shared/model-cache"
    if [ -d "$legacy_cache" ]; then
        local legacy_size=$(display_size "$legacy_cache")
        local legacy_files=$(count_files "$legacy_cache")
        if [ "$legacy_files" != "0" ]; then
            log_warn "  ⚠️  Legacy Model Cache (should be empty)"
            log_warn "     Location: shared/model-cache/"
            log_warn "     Size:     $legacy_size"
            log_warn "     Files:    $legacy_files"
            log_debug "Legacy cache has $legacy_files files - should be migrated"
            echo ""
        fi
    fi
    
    echo ""
    log_info "Tips:"
    log_info "  • ML caches will re-download on next use if cleared"
    log_info "  • Application caches use 90-day expiry"
    log_info "  • To free space: ./scripts/cache-manager.sh clear-models"
    echo ""
}

# Clear ML model caches
clear_models() {
    log_warn "Clearing ML model caches..."
    echo ""
    
    # Confirm
    read -p "This will delete all cached models. Continue? [y/N] " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Cancelled."
        exit 0
    fi
    
    log_debug "Starting ML model cache clearing"
    
    # Clear torch cache
    if [ -d "$PROJECT_ROOT/.cache/torch" ]; then
        log_info "  Clearing Torch/Whisper cache..."
        rm -rf "$PROJECT_ROOT/.cache/torch"
        log_success "  Torch cache cleared"
    fi
    
    # Clear HuggingFace cache
    if [ -d "$PROJECT_ROOT/.cache/huggingface" ]; then
        log_info "  Clearing HuggingFace cache..."
        rm -rf "$PROJECT_ROOT/.cache/huggingface"
        log_success "  HuggingFace cache cleared"
    fi
    
    # Clear MLX cache
    if [ -d "$PROJECT_ROOT/.cache/mlx" ]; then
        log_info "  Clearing MLX cache..."
        rm -rf "$PROJECT_ROOT/.cache/mlx"
        log_success "  MLX cache cleared"
    fi
    
    # Recreate directories
    log_debug "Recreating cache directories"
    mkdir -p "$PROJECT_ROOT/.cache/torch"
    mkdir -p "$PROJECT_ROOT/.cache/huggingface"
    mkdir -p "$PROJECT_ROOT/.cache/mlx"
    
    echo ""
    log_success "Model caches cleared successfully"
    log_warn "Models will re-download on next use"
    echo ""
}

# Clear application caches
clear_app() {
    log_warn "Clearing application caches..."
    echo ""
    
    log_debug "Starting application cache clearing"
    
    # Clear TMDB cache
    if [ -d "$PROJECT_ROOT/out/tmdb_cache" ]; then
        log_info "  Clearing TMDB cache..."
        rm -rf "$PROJECT_ROOT/out/tmdb_cache"
        log_success "  TMDB cache cleared"
    fi
    
    # Clear MusicBrainz cache
    if [ -d "$PROJECT_ROOT/out/musicbrainz_cache" ]; then
        log_info "  Clearing MusicBrainz cache..."
        rm -rf "$PROJECT_ROOT/out/musicbrainz_cache"
        log_success "  MusicBrainz cache cleared"
    fi
    
    # Clear Glossary cache
    if [ -d "$PROJECT_ROOT/glossary/cache" ]; then
        log_info "  Clearing Glossary cache..."
        rm -rf "$PROJECT_ROOT/glossary/cache"
        mkdir -p "$PROJECT_ROOT/glossary/cache"
        log_success "  Glossary cache cleared"
    fi
    
    echo ""
    log_success "Application caches cleared successfully"
    echo ""
}

# Clear all caches
clear_all() {
    log_critical "⚠️  WARNING: This will clear ALL caches"
    echo ""
    
    # Confirm
    read -p "Continue? [y/N] " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Cancelled."
        exit 0
    fi
    
    log_debug "Clearing all caches (models + application)"
    clear_models
    clear_app
    
    log_success "All caches cleared successfully"
    echo ""
}

# Main command dispatcher
case "${1:-}" in
    status)
        show_status
        ;;
    clear-models)
        clear_models
        ;;
    clear-app)
        clear_app
        ;;
    clear-all)
        clear_all
        ;;
    *)
        log_error "Unknown command: ${1:-}"
        echo ""
        log_info "Usage: $0 {status|clear-models|clear-app|clear-all}"
        echo ""
        log_info "Commands:"
        log_info "  status       - Show cache status and sizes"
        log_info "  clear-models - Clear ML model caches (Torch, HuggingFace, MLX)"
        log_info "  clear-app    - Clear application caches (TMDB, MusicBrainz, Glossary)"
        log_info "  clear-all    - Clear all caches"
        echo ""
        exit 1
        ;;
esac
