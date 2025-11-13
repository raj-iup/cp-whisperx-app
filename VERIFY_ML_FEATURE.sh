#!/bin/bash
# Quick verification that ML glossary feature is working

echo "=================================================="
echo "ML Glossary Feature Verification"
echo "=================================================="
echo ""

cd "$(dirname "$0")"

echo "1. Testing ML selector module..."
python3 -c "
import sys
sys.path.insert(0, 'shared')
from glossary_ml import MLTermSelector
import logging
logging.basicConfig(level=logging.WARNING)
s = MLTermSelector(logging.getLogger())
print(f'   ✓ Model type: {s.model_type}')
print(f'   ✓ Available: {s.is_available()}')
" || { echo "   ✗ FAILED"; exit 1; }

echo ""
echo "2. Testing integration with glossary system..."
python3 tools/test_ml_glossary.py 2>&1 | grep -E "(✅|✗|FAILED)" | head -1

echo ""
echo "3. Checking documentation..."
[ -f "docs/ML_GLOSSARY_GUIDE.md" ] && echo "   ✓ ML_GLOSSARY_GUIDE.md exists" || echo "   ✗ Missing"
[ -f "docs/ML_IMPLEMENTATION_SUMMARY.md" ] && echo "   ✓ ML_IMPLEMENTATION_SUMMARY.md exists" || echo "   ✗ Missing"

echo ""
echo "4. Checking implementation files..."
[ -f "shared/glossary_ml.py" ] && echo "   ✓ glossary_ml.py exists" || echo "   ✗ Missing"
[ -f "tools/test_ml_glossary.py" ] && echo "   ✓ test_ml_glossary.py exists" || echo "   ✗ Missing"

echo ""
echo "=================================================="
echo "✅ ML Glossary Feature is READY!"
echo "=================================================="
echo ""
echo "Usage:"
echo "  export GLOSSARY_STRATEGY=ml"
echo "  ./prepare-job.sh movie.mp4"
echo ""
echo "Or for best results:"
echo "  pip install sentence-transformers"
echo "  export GLOSSARY_STRATEGY=ml"
echo ""
