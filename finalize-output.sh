#!/usr/bin/env bash
# Finalize Output - Organize final output into title-based directory
# Usage: ./finalize-output.sh <job-id>

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR" && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse arguments
if [ $# -lt 1 ]; then
    echo "Usage: $0 <job-id>"
    echo "Example: $0 20251109-0001"
    exit 1
fi

JOB_ID="$1"

# Find job directory
JOB_DIR=$(find "$PROJECT_ROOT/out" -type d -name "$JOB_ID" 2>/dev/null | head -1)

if [ -z "$JOB_DIR" ]; then
    echo -e "${RED}✗ Job not found: $JOB_ID${NC}"
    exit 1
fi

echo -e "${GREEN}Found job directory: $JOB_DIR${NC}"
echo ""

# Run finalization
python3 "$PROJECT_ROOT/scripts/finalize_output.py" "$JOB_DIR"

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ Finalization completed successfully${NC}"
else
    echo ""
    echo -e "${RED}✗ Finalization failed${NC}"
fi

exit $exit_code
