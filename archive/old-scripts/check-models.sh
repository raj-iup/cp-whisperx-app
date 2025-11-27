#!/usr/bin/env bash
# Check ML model status and cache
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/scripts/common-logging.sh"

VENV_PATH=".bollyenv"

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    log_error "Virtual environment not found. Please run ./scripts/bootstrap.sh first"
    exit 1
fi

# Activate virtual environment
log_info "Activating virtual environment..."
# shellcheck source=/dev/null
source "$VENV_PATH/bin/activate"

# Run model checker
log_section "ML MODEL STATUS CHECK"
python shared/model_checker.py "$@"

exit $?
