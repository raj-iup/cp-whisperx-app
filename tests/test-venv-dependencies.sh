#!/bin/bash
# Test all virtual environment dependencies
# Verifies that all shared module imports work correctly

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     Testing Virtual Environment Dependencies                ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

errors=0

# Test Demucs venv
echo "Testing .venv-demucs..."
if .venv-demucs/bin/python -c "
import sys
sys.path.insert(0, '.')
from shared.config import Config
from shared.logger import PipelineLogger
print('  ✓ pydantic_settings available')
print('  ✓ shared.config imports successfully')
print('  ✓ shared.logger imports successfully')
" 2>/dev/null; then
    echo "  ✅ Demucs venv: OK"
else
    echo "  ❌ Demucs venv: FAILED"
    errors=$((errors + 1))
fi
echo ""

# Test Common venv
echo "Testing .venv-common..."
if .venv-common/bin/python -c "
import srt
print('  ✓ srt module available')
" 2>/dev/null; then
    echo "  ✅ Common venv: OK"
else
    echo "  ❌ Common venv: FAILED (srt module missing)"
    errors=$((errors + 1))
fi
echo ""

# Test LLM venv
echo "Testing .venv-llm..."
if .venv-llm/bin/python -c "
import sys
sys.path.insert(0, '.')
from pydantic_settings import BaseSettings
from shared.config import load_config
from shared.logger import PipelineLogger
from shared.stage_utils import StageIO
print('  ✓ pydantic_settings available')
print('  ✓ shared.config imports successfully')
print('  ✓ shared.logger imports successfully')
print('  ✓ shared.stage_utils imports successfully')
" 2>/dev/null; then
    echo "  ✅ LLM venv: OK"
else
    echo "  ❌ LLM venv: FAILED"
    errors=$((errors + 1))
fi
echo ""

# Summary
echo "══════════════════════════════════════════════════════════════"
if [ $errors -eq 0 ]; then
    echo "✅ ALL TESTS PASSED"
    echo ""
    echo "All virtual environments have required dependencies installed."
    exit 0
else
    echo "❌ $errors TEST(S) FAILED"
    echo ""
    echo "Some virtual environments are missing dependencies."
    echo "Run the following to fix:"
    echo ""
    echo "  # Fix Demucs venv:"
    echo "  .venv-demucs/bin/pip install pydantic pydantic-settings"
    echo ""
    echo "  # Fix Common venv:"
    echo "  .venv-common/bin/pip install srt"
    echo ""
    echo "  # Fix LLM venv:"
    echo "  .venv-llm/bin/pip install pydantic pydantic-settings"
    echo ""
    exit 1
fi
