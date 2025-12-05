#!/bin/bash
#
# Pre-commit hook to maintain 100% compliance
# Validates Python files before allowing commit
#
# This hook runs the compliance validator on all staged Python files
# and prevents commits if any violations are found.
#

echo "🔍 Running compliance validation..."
echo ""

# Get the project root
PROJECT_ROOT="$(git rev-parse --show-toplevel)"
cd "$PROJECT_ROOT" || exit 1

# Get list of staged Python files
STAGED_PY_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(py)$' || true)

if [ -z "$STAGED_PY_FILES" ]; then
    echo "✓ No Python files to validate"
    exit 0
fi

echo "Files to validate:"
echo "$STAGED_PY_FILES" | sed 's/^/  - /'
echo ""

# Convert to array for validation
FILES_ARRAY=()
while IFS= read -r file; do
    if [ -f "$file" ]; then
        FILES_ARRAY+=("$file")
    fi
done <<< "$STAGED_PY_FILES"

# Run validator if we have files
if [ ${#FILES_ARRAY[@]} -eq 0 ]; then
    echo "✓ No files to validate"
    exit 0
fi

# Run the compliance validator with --strict flag
python3 scripts/validate-compliance.py --strict "${FILES_ARRAY[@]}"
VALIDATOR_EXIT=$?

echo ""

if [ $VALIDATOR_EXIT -ne 0 ]; then
    echo "❌ Compliance violations found!"
    echo ""
    echo "To maintain 100% compliance, please fix the violations before committing."
    echo ""
    echo "Quick fixes:"
    echo "  1. Add missing type hints: def func(param: Type) -> ReturnType:"
    echo "  2. Add missing docstrings: \"\"\"Function description.\"\"\""
    echo "  3. Use logger instead of print()"
    echo "  4. Organize imports: Standard / Third-party / Local"
    echo "  5. AD-006: Read job.json and override parameters (see ARCHITECTURE_ALIGNMENT_2025-12-04.md)"
    echo "  6. AD-007: Use 'shared.' prefix for all shared/ imports"
    echo ""
    echo "See docs/developer/DEVELOPER_STANDARDS.md for detailed guidance."
    echo ""
    echo "To bypass this check (NOT RECOMMENDED):"
    echo "  git commit --no-verify"
    echo ""
    echo "❌ Commit rejected"
    exit 1
fi

echo "✅ All files passed compliance checks!"
echo ""

# Run file naming standard tests (if pytest available)
if command -v pytest &> /dev/null; then
    echo "🔍 Running file naming standard tests..."
    python3 -m pytest tests/test_file_naming_standard.py -v --tb=short -q 2>&1 | grep -E "(PASSED|FAILED|ERROR|test_)"
    NAMING_EXIT=${PIPESTATUS[0]}
    
    if [ $NAMING_EXIT -ne 0 ]; then
        echo ""
        echo "❌ File naming tests failed!"
        echo "   This indicates the file naming standard (§ 1.3.1) has been violated."
        echo "   Please ensure all output files follow the pattern: {stage}_{descriptor}.{ext}"
        echo ""
        echo "❌ Commit rejected"
        exit 1
    fi
    
    echo "✅ File naming tests passed!"
fi

echo ""
echo "✓ All checks passed - Commit allowed"
exit 0
