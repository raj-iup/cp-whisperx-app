#!/bin/bash
# Verify Docker infrastructure has been removed

echo "=============================================="
echo "Native-Only Architecture Verification"
echo "=============================================="
echo ""

FAILED=0

# Check Docker directory removed
if [ -d "docker" ]; then
    echo "✗ FAIL: docker/ directory still exists"
    FAILED=1
else
    echo "✓ PASS: docker/ directory removed"
fi

# Check Docker compose files removed
if [ -f "docker-compose.yml" ] || [ -f "docker-compose-fallback.yml" ]; then
    echo "✗ FAIL: docker-compose files still exist"
    FAILED=1
else
    echo "✓ PASS: docker-compose files removed"
fi

# Check PowerShell files removed
PS1_COUNT=$(ls *.ps1 2>/dev/null | wc -l)
if [ $PS1_COUNT -gt 0 ]; then
    echo "✗ FAIL: PowerShell files still exist ($PS1_COUNT files)"
    FAILED=1
else
    echo "✓ PASS: PowerShell files removed"
fi

# Check essential shell scripts preserved
ESSENTIAL=("prepare-job.sh" "run_pipeline.sh" "quick-start.sh")
for script in "${ESSENTIAL[@]}"; do
    if [ ! -f "$script" ]; then
        echo "✗ FAIL: Essential script missing: $script"
        FAILED=1
    else
        echo "✓ PASS: Essential script preserved: $script"
    fi
done

# Check Python scripts preserved
PYTHON_COUNT=$(ls scripts/*.py 2>/dev/null | wc -l)
if [ $PYTHON_COUNT -lt 20 ]; then
    echo "✗ FAIL: Missing Python scripts (found $PYTHON_COUNT, expected 20+)"
    FAILED=1
else
    echo "✓ PASS: Python scripts preserved ($PYTHON_COUNT files)"
fi

# Check shared modules preserved
SHARED_COUNT=$(ls shared/*.py 2>/dev/null | wc -l)
if [ $SHARED_COUNT -lt 5 ]; then
    echo "✗ FAIL: Missing shared modules (found $SHARED_COUNT, expected 5+)"
    FAILED=1
else
    echo "✓ PASS: Shared modules preserved ($SHARED_COUNT files)"
fi

# Check documentation updated
if grep -q "Docker-based pipeline orchestrator" run_pipeline.sh 2>/dev/null; then
    echo "✗ FAIL: run_pipeline.sh still references Docker"
    FAILED=1
else
    echo "✓ PASS: run_pipeline.sh updated (no Docker references)"
fi

echo ""
echo "=============================================="
if [ $FAILED -eq 0 ]; then
    echo "✅ ALL CHECKS PASSED"
    echo "Native-only architecture verified!"
else
    echo "❌ SOME CHECKS FAILED"
    echo "Please review the failures above"
fi
echo "=============================================="

exit $FAILED
