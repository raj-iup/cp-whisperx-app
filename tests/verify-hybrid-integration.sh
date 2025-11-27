#!/bin/bash
# Verify Hybrid Translation Integration

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║    Hybrid Translation Integration Verification                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

errors=0

# Check 1: Bootstrap script
echo "✓ Checking bootstrap.sh..."
if grep -q ".venv-llm" scripts/bootstrap.sh; then
    echo "  ✅ .venv-llm environment added"
else
    echo "  ❌ .venv-llm not found in bootstrap.sh"
    errors=$((errors + 1))
fi

if grep -q "anthropic_api_key" scripts/bootstrap.sh; then
    echo "  ✅ Anthropic API key check added"
else
    echo "  ❌ Anthropic API key check not found"
    errors=$((errors + 1))
fi

# Check 2: Configuration
echo ""
echo "✓ Checking config/.env.pipeline..."
if grep -q "USE_HYBRID_TRANSLATION" config/.env.pipeline; then
    echo "  ✅ USE_HYBRID_TRANSLATION setting added"
else
    echo "  ❌ USE_HYBRID_TRANSLATION not found"
    errors=$((errors + 1))
fi

if grep -q "LLM_PROVIDER" config/.env.pipeline; then
    echo "  ✅ LLM_PROVIDER setting added"
else
    echo "  ❌ LLM_PROVIDER not found"
    errors=$((errors + 1))
fi

# Check 3: Required files
echo ""
echo "✓ Checking required files..."

files=(
    "scripts/hybrid_translator.py"
    "requirements-llm.txt"
    "install-llm.sh"
    "test_hybrid_translator.py"
    "docs/HYBRID_TRANSLATION.md"
    "HYBRID_TRANSLATION_SETUP.md"
    "HYBRID_TRANSLATION_PIPELINE_INTEGRATION.md"
    "config/secrets.example.json"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file missing"
        errors=$((errors + 1))
    fi
done

# Check 4: Glossary locations
echo ""
echo "✓ Checking glossary updates..."
if grep -q "Cuffe Parade" glossary/hinglish_master.tsv; then
    echo "  ✅ Mumbai locations added to glossary"
    count=$(grep -c "location" glossary/hinglish_master.tsv)
    echo "     (Found $count location entries)"
else
    echo "  ❌ Mumbai locations not found in glossary"
    errors=$((errors + 1))
fi

# Check 5: API keys in secrets.example.json
echo ""
echo "✓ Checking secrets.example.json..."
if grep -q "anthropic_api_key" config/secrets.example.json; then
    echo "  ✅ anthropic_api_key field added"
else
    echo "  ❌ anthropic_api_key field missing"
    errors=$((errors + 1))
fi

if grep -q "openai_api_key" config/secrets.example.json; then
    echo "  ✅ openai_api_key field added"
else
    echo "  ❌ openai_api_key field missing"
    errors=$((errors + 1))
fi

# Check 6: Syntax validation
echo ""
echo "✓ Checking shell script syntax..."
if bash -n scripts/bootstrap.sh 2>/dev/null; then
    echo "  ✅ bootstrap.sh syntax valid"
else
    echo "  ❌ bootstrap.sh has syntax errors"
    errors=$((errors + 1))
fi

if bash -n install-llm.sh 2>/dev/null; then
    echo "  ✅ install-llm.sh syntax valid"
else
    echo "  ❌ install-llm.sh has syntax errors"
    errors=$((errors + 1))
fi

# Summary
echo ""
echo "══════════════════════════════════════════════════════════════════"
if [ $errors -eq 0 ]; then
    echo "✅ ALL CHECKS PASSED"
    echo ""
    echo "Hybrid Translation integration is complete and ready to use!"
    echo ""
    echo "Next steps:"
    echo "  1. Run bootstrap: ./bootstrap.sh --force"
    echo "  2. Add API key to config/secrets.json (optional)"
    echo "  3. Test: python test_hybrid_translator.py --use-llm"
else
    echo "❌ $errors CHECKS FAILED"
    echo ""
    echo "Please review the errors above."
fi
echo "══════════════════════════════════════════════════════════════════"
echo ""

exit $errors
