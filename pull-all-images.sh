#!/bin/bash
# CP-WhisperX-App Docker Image Pull Script
# Pull all Docker images from registry with consistent logging

# Colors
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

# Logging functions
log_message() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "[${timestamp}] [pull-images] [${level}] ${message}"
}

log_info() { log_message "INFO" "$@"; }

print_header() {
    echo ""
    echo -e "${CYAN}============================================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}============================================================${NC}"
}

print_header "CP-WHISPERX-APP IMAGE PULL"
log_info "Calling scripts/pull-all-images.sh..."

# Execute the actual pull script
exec scripts/pull-all-images.sh "$@"
