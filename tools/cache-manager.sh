#!/bin/bash
# Cache Management Utility - Wrapper Script

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Activate virtual environment if it exists
if [ -d "$PROJECT_ROOT/.bollyenv" ]; then
    source "$PROJECT_ROOT/.bollyenv/bin/activate"
fi

# Run cache manager
python3 "$PROJECT_ROOT/scripts/cache_manager.py" "$@"
