#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# Install MLX and MLX-Whisper for Apple Silicon GPU Acceleration
# ============================================================================
# ⚠️  DEPRECATED: This script is no longer needed
# 
# MLX is now automatically installed by bootstrap.sh in the venv/mlx environment
# 
# RECOMMENDED ACTION:
#   Just run: ./bootstrap.sh
# 
# This will:
#   1. Create venv/mlx virtual environment
#   2. Install MLX and MLX-Whisper automatically
#   3. Configure hardware detection for MPS acceleration
# 
# This script is kept for backward compatibility but simply forwards to bootstrap
# ============================================================================

# Load common logging
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/scripts/common-logging.sh"

log_section "MLX INSTALLATION FOR APPLE SILICON"

# Check if we're on Apple Silicon
OS_TYPE=$(uname -s)
ARCH_TYPE=$(uname -m)

if [[ "$OS_TYPE" != "Darwin" ]] || [[ "$ARCH_TYPE" != "arm64" ]]; then
    log_error "MLX is only available on Apple Silicon (M1/M2/M3) Macs"
    log_info "Your system: $OS_TYPE ($ARCH_TYPE)"
    log_info "MLX requires: Darwin (arm64)"
    exit 1
fi

# Check if venv/mlx already exists
if [ -d "$SCRIPT_DIR/venv/mlx" ]; then
    log_success "MLX environment already exists at venv/mlx"
    log_info "To recreate, run: rm -rf venv/mlx && ./bootstrap.sh"
    exit 0
fi

# Check if bootstrap has been run
if [ ! -f "$SCRIPT_DIR/config/hardware_cache.json" ]; then
    log_error "Bootstrap has not been run yet"
    log_info "Please run ./bootstrap.sh first to create all environments"
    exit 1
fi

log_info "MLX environment not found - running bootstrap..."
log_info "This will create the venv/mlx environment with MLX support"
echo ""

# Forward to bootstrap - it will create all missing environments
exec "$SCRIPT_DIR/bootstrap.sh"
