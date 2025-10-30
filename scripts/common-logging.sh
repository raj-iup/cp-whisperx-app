#!/usr/bin/env bash
# Common logging functions for all shell scripts
# Source this file at the beginning of your shell scripts:
#   source "$(dirname "$0")/common-logging.sh"

# Color codes (optional, can be disabled)
if [ -t 1 ]; then
    # Terminal supports colors
    COLOR_RED='\033[0;31m'
    COLOR_GREEN='\033[0;32m'
    COLOR_YELLOW='\033[1;33m'
    COLOR_BLUE='\033[0;34m'
    COLOR_NC='\033[0m' # No Color
else
    # No color support
    COLOR_RED=''
    COLOR_GREEN=''
    COLOR_YELLOW=''
    COLOR_BLUE=''
    COLOR_NC=''
fi

# Log level (can be overridden by setting LOG_LEVEL environment variable)
LOG_LEVEL=${LOG_LEVEL:-INFO}

# Log file (optional, set LOG_FILE environment variable to enable file logging)
LOG_FILE=${LOG_FILE:-}

# Helper function to write to log file if enabled
_log_to_file() {
    if [ -n "$LOG_FILE" ]; then
        echo "$1" >> "$LOG_FILE"
    fi
}

# Debug logging (only shown if LOG_LEVEL=DEBUG)
log_debug() {
    if [ "$LOG_LEVEL" = "DEBUG" ]; then
        local msg="[$(date '+%Y-%m-%d %H:%M:%S')] [DEBUG] $*"
        echo -e "${COLOR_BLUE}${msg}${COLOR_NC}"
        _log_to_file "$msg"
    fi
}

# Info logging
log_info() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] $*"
    echo -e "${COLOR_GREEN}${msg}${COLOR_NC}"
    _log_to_file "$msg"
}

# Warning logging
log_warn() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] [WARN] $*"
    echo -e "${COLOR_YELLOW}${msg}${COLOR_NC}"
    _log_to_file "$msg"
}

# Error logging (to stderr)
log_error() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] $*"
    echo -e "${COLOR_RED}${msg}${COLOR_NC}" >&2
    _log_to_file "$msg"
}

# Critical error logging (to stderr)
log_critical() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] [CRITICAL] $*"
    echo -e "${COLOR_RED}${msg}${COLOR_NC}" >&2
    _log_to_file "$msg"
}

# Success message (green checkmark)
log_success() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] [SUCCESS] ✓ $*"
    echo -e "${COLOR_GREEN}${msg}${COLOR_NC}"
    _log_to_file "$msg"
}

# Failure message (red X)
log_failure() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] [FAILURE] ✗ $*"
    echo -e "${COLOR_RED}${msg}${COLOR_NC}" >&2
    _log_to_file "$msg"
}

# Section header
log_section() {
    local msg="======================================================================"
    echo -e "${COLOR_BLUE}${msg}${COLOR_NC}"
    echo -e "${COLOR_BLUE}$*${COLOR_NC}"
    echo -e "${COLOR_BLUE}${msg}${COLOR_NC}"
    _log_to_file "$msg"
    _log_to_file "$*"
    _log_to_file "$msg"
}

# Usage example (can be shown with: bash common-logging.sh)
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    echo "Common Logging Functions for Shell Scripts"
    echo ""
    echo "Usage:"
    echo "  source scripts/common-logging.sh"
    echo ""
    echo "Functions:"
    echo "  log_debug <message>    - Debug message (only if LOG_LEVEL=DEBUG)"
    echo "  log_info <message>     - Info message"
    echo "  log_warn <message>     - Warning message"
    echo "  log_error <message>    - Error message (to stderr)"
    echo "  log_critical <message> - Critical error (to stderr)"
    echo "  log_success <message>  - Success message with checkmark"
    echo "  log_failure <message>  - Failure message with X"
    echo "  log_section <message>  - Section header"
    echo ""
    echo "Environment Variables:"
    echo "  LOG_LEVEL    - Set to DEBUG to see debug messages (default: INFO)"
    echo "  LOG_FILE     - Set to file path to enable file logging"
    echo ""
    echo "Examples:"
    echo "  log_info \"Starting build process\""
    echo "  log_error \"Build failed: \$error_msg\""
    echo "  log_success \"Build completed\""
    echo ""
    echo "Demo:"
    log_section "Demo Section"
    log_debug "This is a debug message"
    log_info "This is an info message"
    log_warn "This is a warning message"
    log_error "This is an error message"
    log_success "This is a success message"
    log_failure "This is a failure message"
fi
