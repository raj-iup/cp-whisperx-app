#!/bin/bash
# quick_cleanup.sh - Safe cleanup of unused artifacts
# Generated from Code Review & Compliance Report
# Date: 2025-12-02

set -e  # Exit on error

echo "========================================================================"
echo "CODEBASE CLEANUP SCRIPT"
echo "========================================================================"
echo ""
echo "This script removes unused artifacts identified in the code review:"
echo "  - shared/backup/ directory (104KB, 0 references)"
echo "  - glossary_unified_deprecated.py (2.4KB, 0 references)"
echo "  - Python bytecode (__pycache__/, *.pyc)"
echo "  - Old logs (>7 days)"
echo "  - Old test results (>7 days)"
echo ""
echo "Estimated space to free: ~1.0-1.5MB"
echo ""
read -p "Continue with cleanup? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cleanup cancelled."
    exit 0
fi

echo ""
echo "Starting cleanup..."
echo ""

# 1. Remove backup directory
if [ -d "shared/backup" ]; then
    echo "✓ Removing shared/backup/ directory..."
    rm -rf shared/backup/
    echo "  Removed: shared/backup/ (104KB)"
else
    echo "  Skip: shared/backup/ already removed"
fi

# 2. Remove deprecated file
if [ -f "shared/glossary_unified_deprecated.py" ]; then
    echo "✓ Removing shared/glossary_unified_deprecated.py..."
    rm -f shared/glossary_unified_deprecated.py
    echo "  Removed: glossary_unified_deprecated.py (2.4KB)"
else
    echo "  Skip: glossary_unified_deprecated.py already removed"
fi

# 3. Clean Python bytecode
echo "✓ Cleaning Python bytecode..."
pycache_count=$(find . -type d -name "__pycache__" | wc -l | tr -d ' ')
pyc_count=$(find . -name "*.pyc" | wc -l | tr -d ' ')

find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

echo "  Removed: $pycache_count __pycache__ directories"
echo "  Removed: $pyc_count .pyc files"

# 4. Clean old logs
if [ -d "logs" ]; then
    echo "✓ Cleaning old logs (>7 days)..."
    old_logs=$(find logs/ -name "*.log" -mtime +7 2>/dev/null | wc -l | tr -d ' ')
    find logs/ -name "*.log" -mtime +7 -delete 2>/dev/null || true
    rm -f logs/.DS_Store 2>/dev/null || true
    echo "  Removed: $old_logs old log files"
fi

# 5. Clean old test results
if [ -d "test-results" ]; then
    echo "✓ Cleaning old test results (>7 days)..."
    old_results=$(find test-results/ -type f -mtime +7 2>/dev/null | wc -l | tr -d ' ')
    find test-results/ -name "*.log" -mtime +7 -delete 2>/dev/null || true
    find test-results/ -name "*.srt" -mtime +7 -delete 2>/dev/null || true
    echo "  Removed: $old_results old test result files"
fi

# 6. Update .gitignore
echo "✓ Updating .gitignore..."
touch .gitignore
if ! grep -q "__pycache__" .gitignore 2>/dev/null; then
    echo "__pycache__/" >> .gitignore
    echo "  Added: __pycache__/"
fi
if ! grep -q "*.pyc" .gitignore 2>/dev/null; then
    echo "*.pyc" >> .gitignore
    echo "  Added: *.pyc"
fi

echo ""
echo "========================================================================"
echo "CLEANUP COMPLETE!"
echo "========================================================================"
echo ""
echo "Summary:"
echo "  ✓ Removed unused backup files"
echo "  ✓ Removed deprecated files"
echo "  ✓ Cleaned Python bytecode"
echo "  ✓ Cleaned old logs"
echo "  ✓ Cleaned old test results"
echo "  ✓ Updated .gitignore"
echo ""
echo "Next steps:"
echo "  1. Run: git status"
echo "  2. Review changes"
echo "  3. Run: ./scripts/validate-compliance.py (to verify no breakage)"
echo "  4. Commit: git commit -m 'Clean up unused artifacts'"
echo ""
echo "For compliance improvement, see:"
echo "  - docs/CODEBASE_REVIEW_COMPLIANCE_REPORT.md"
echo "  - docs/CODE_EXAMPLES.md"
echo "  - .github/copilot-instructions.md"
echo ""
