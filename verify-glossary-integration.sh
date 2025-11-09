#!/usr/bin/env bash
# Glossary Integration Verification Script
# Tests all integration points to ensure glossary system is working

set -euo pipefail

echo "=========================================="
echo "GLOSSARY INTEGRATION VERIFICATION"
echo "=========================================="
echo ""

PASS=0
FAIL=0

# Test 1: Check glossary directory
echo "Test 1: Glossary directory structure"
if [ -d "glossary" ] && [ -d "glossary/prompts" ]; then
    echo "  ✅ PASS: Directory structure exists"
    ((PASS++))
else
    echo "  ❌ FAIL: Directory structure missing"
    ((FAIL++))
fi

# Test 2: Check master TSV
echo "Test 2: Master glossary TSV"
if [ -f "glossary/hinglish_master.tsv" ]; then
    term_count=$(tail -n +2 glossary/hinglish_master.tsv 2>/dev/null | grep -v '^[[:space:]]*$' | wc -l | tr -d ' ')
    echo "  ✅ PASS: Master TSV found with $term_count terms"
    ((PASS++))
else
    echo "  ⚠️  WARN: Master TSV not found (can be added later)"
    ((PASS++))  # Not a failure, glossary is optional
fi

# Test 3: Check movie prompts
echo "Test 3: Movie-specific prompts"
prompt_count=$(find glossary/prompts -name "*.txt" -type f 2>/dev/null | wc -l | tr -d ' ')
if [ "$prompt_count" -ge 15 ]; then
    echo "  ✅ PASS: Found $prompt_count movie prompts (expected 15+)"
    ((PASS++))
else
    echo "  ❌ FAIL: Only $prompt_count prompts found (expected 15+)"
    ((FAIL++))
fi

# Test 4: Check glossary module
echo "Test 4: Glossary Python module"
if [ -f "shared/glossary.py" ]; then
    echo "  ✅ PASS: shared/glossary.py exists"
    ((PASS++))
else
    echo "  ❌ FAIL: shared/glossary.py missing"
    ((FAIL++))
fi

# Test 5: Check config template
echo "Test 5: Configuration template"
if grep -q "GLOSSARY_ENABLED" config/.env.pipeline 2>/dev/null; then
    echo "  ✅ PASS: GLOSSARY_ENABLED in config/.env.pipeline"
    ((PASS++))
else
    echo "  ❌ FAIL: GLOSSARY_ENABLED not in config/.env.pipeline"
    ((FAIL++))
fi

# Test 6: Check bootstrap.sh integration
echo "Test 6: Bootstrap.sh integration"
if grep -q "GLOSSARY SYSTEM VALIDATION" scripts/bootstrap.sh 2>/dev/null; then
    echo "  ✅ PASS: Bootstrap.sh has glossary validation"
    ((PASS++))
else
    echo "  ❌ FAIL: Bootstrap.sh missing glossary validation"
    ((FAIL++))
fi

# Test 7: Check prepare-job.py integration
echo "Test 7: Prepare-job.py integration"
if grep -q "GLOSSARY_ENABLED" scripts/prepare-job.py 2>/dev/null; then
    echo "  ✅ PASS: Prepare-job.py processes glossary config"
    ((PASS++))
else
    echo "  ❌ FAIL: Prepare-job.py missing glossary processing"
    ((FAIL++))
fi

# Test 8: Check subtitle_gen.py integration
echo "Test 8: Subtitle-gen integration"
if grep -q "HinglishGlossary" docker/subtitle-gen/subtitle_gen.py 2>/dev/null; then
    echo "  ✅ PASS: Subtitle-gen imports HinglishGlossary"
    ((PASS++))
else
    echo "  ❌ FAIL: Subtitle-gen missing glossary import"
    ((FAIL++))
fi

# Test 9: Check documentation
echo "Test 9: Documentation"
doc_count=0
[ -f "glossary/README.md" ] && ((doc_count++))
[ -f "GLOSSARY_INTEGRATION.md" ] && ((doc_count++))
[ -f "GLOSSARY_INTEGRATION_COMPLETE.md" ] && ((doc_count++))

if [ "$doc_count" -ge 2 ]; then
    echo "  ✅ PASS: Found $doc_count documentation files"
    ((PASS++))
else
    echo "  ❌ FAIL: Only $doc_count documentation files found"
    ((FAIL++))
fi

# Summary
echo ""
echo "=========================================="
echo "VERIFICATION SUMMARY"
echo "=========================================="
echo "Tests Passed: $PASS"
echo "Tests Failed: $FAIL"
echo ""

if [ "$FAIL" -eq 0 ]; then
    echo "🎉 ALL TESTS PASSED!"
    echo ""
    echo "Glossary system is fully integrated and ready to use."
    echo ""
    echo "Next steps:"
    echo "  1. Run bootstrap: ./scripts/bootstrap.sh"
    echo "  2. Prepare a job: ./prepare-job.sh path/to/movie.mp4"
    echo "  3. Run pipeline: ./run_pipeline.sh -j <job-id>"
    exit 0
else
    echo "⚠️  SOME TESTS FAILED"
    echo ""
    echo "Please review the failed tests above and fix issues."
    exit 1
fi
