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

if [ $VALIDATOR_EXIT -eq 0 ]; then
    echo "✅ All files passed compliance checks!"
    echo "✓ Commit allowed"
    exit 0
else
    echo "❌ Compliance violations found!"
    echo ""
    echo "To maintain 100% compliance, please fix the violations before committing."
    echo ""
    echo "Quick fixes:"
    echo "  1. Add missing type hints: def func(param: Type) -> ReturnType:"
    echo "  2. Add missing docstrings: \"\"\"Function description.\"\"\""
    echo "  3. Use logger instead of print()"
    echo "  4. Organize imports: Standard / Third-party / Local"
    echo ""
    echo "To bypass this check (NOT RECOMMENDED):"
    echo "  git commit --no-verify"
    echo ""
    echo "❌ Commit rejected"
    exit 1
fi
