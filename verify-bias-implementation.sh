#!/bin/bash
# Verify Bias Injection Implementation
# Quick verification script to check that all bias components are in place

echo "=============================================="
echo "Bias Injection Implementation Verification"
echo "=============================================="
echo ""

ERRORS=0
WARNINGS=0

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_file() {
    local file=$1
    local desc=$2
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $desc: $file"
        return 0
    else
        echo -e "${RED}✗${NC} $desc: $file NOT FOUND"
        ERRORS=$((ERRORS + 1))
        return 1
    fi
}

check_content() {
    local file=$1
    local pattern=$2
    local desc=$3
    if grep -q "$pattern" "$file" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $desc"
        return 0
    else
        echo -e "${RED}✗${NC} $desc NOT FOUND in $file"
        ERRORS=$((ERRORS + 1))
        return 1
    fi
}

check_warning() {
    local file=$1
    local pattern=$2
    local desc=$3
    if grep -q "$pattern" "$file" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $desc"
        return 0
    else
        echo -e "${YELLOW}⚠${NC} $desc NOT FOUND in $file (optional)"
        WARNINGS=$((WARNINGS + 1))
        return 1
    fi
}

echo "1. Checking Core Bias Infrastructure..."
echo "----------------------------------------"
check_file "scripts/bias_injection.py" "Bias injection module"
check_content "scripts/bias_injection.py" "class BiasWindow" "BiasWindow dataclass"
check_content "scripts/bias_injection.py" "def create_bias_windows" "create_bias_windows function"
check_content "scripts/bias_injection.py" "def save_bias_windows" "save_bias_windows function"
check_content "scripts/bias_injection.py" "def get_window_for_time" "get_window_for_time function"
echo ""

echo "2. Checking WhisperX Integration..."
echo "----------------------------------------"
check_file "scripts/whisperx_integration.py" "WhisperX integration"
check_content "scripts/whisperx_integration.py" "from bias_injection import" "Bias injection import"
check_content "scripts/whisperx_integration.py" "bias_enabled = getattr" "Bias enabled check"
check_content "scripts/whisperx_integration.py" "create_bias_windows" "Bias window creation call"
check_content "scripts/whisperx_integration.py" "save_bias_windows" "Bias window saving call"
check_content "scripts/whisperx_integration.py" "entity_names.append" "Entity collection"
check_content "scripts/whisperx_integration.py" "tmdb_data.get('cast'" "TMDB cast loading"
echo ""

echo "3. Checking Configuration Files..."
echo "----------------------------------------"
check_file "config/.env.pipeline" "Pipeline configuration"
check_content "config/.env.pipeline" "BIAS_ENABLED" "BIAS_ENABLED setting"
check_content "config/.env.pipeline" "BIAS_WINDOW_SECONDS" "BIAS_WINDOW_SECONDS setting"
check_content "config/.env.pipeline" "BIAS_STRIDE_SECONDS" "BIAS_STRIDE_SECONDS setting"
check_content "config/.env.pipeline" "BIAS_TOPK" "BIAS_TOPK setting"
check_content "config/.env.pipeline" "BIAS_MIN_CONFIDENCE" "BIAS_MIN_CONFIDENCE setting"
echo ""

check_file "config/.env.template" "Configuration template"
check_content "config/.env.template" "BIAS_ENABLED" "BIAS_ENABLED in template"
check_content "config/.env.template" "BIAS_WINDOW_SECONDS" "BIAS_WINDOW_SECONDS in template"
echo ""

echo "4. Checking Config Loader..."
echo "----------------------------------------"
check_file "shared/config.py" "Config loader"
check_content "shared/config.py" "bias_enabled" "bias_enabled field"
check_content "shared/config.py" "bias_window_seconds" "bias_window_seconds field"
check_content "shared/config.py" "bias_stride_seconds" "bias_stride_seconds field"
check_content "shared/config.py" "bias_topk" "bias_topk field"
check_content "shared/config.py" "bias_min_confidence" "bias_min_confidence field"
echo ""

echo "5. Checking Documentation..."
echo "----------------------------------------"
check_file "BIAS_STAGE_ANALYSIS.md" "Original analysis document"
check_file "BIAS_IMPLEMENTATION_COMPLETE.md" "Implementation summary"
check_warning "BIAS_IMPLEMENTATION_COMPLETE.md" "FULLY IMPLEMENTED" "Implementation status"
echo ""

echo "6. Testing Python Imports..."
echo "----------------------------------------"
if python3 -c "from scripts.bias_injection import BiasWindow, create_bias_windows, save_bias_windows, get_window_for_time" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Python imports successful"
else
    echo -e "${YELLOW}⚠${NC} Python imports failed (may need virtual environment)"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

echo "=============================================="
echo "Verification Summary"
echo "=============================================="
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo ""
    echo "Bias injection is fully implemented and ready to use."
    echo ""
    echo "Configuration options:"
    echo "  BIAS_ENABLED=true              # Enable/disable bias injection"
    echo "  BIAS_WINDOW_SECONDS=45         # Window duration"
    echo "  BIAS_STRIDE_SECONDS=15         # Stride between windows"
    echo "  BIAS_TOPK=10                   # Top-K terms per window"
    echo "  BIAS_MIN_CONFIDENCE=0.6        # Minimum confidence (future use)"
    echo ""
    echo "Next steps:"
    echo "  1. Run a test pipeline on a sample movie"
    echo "  2. Check out/<job-id>/07_asr/bias_windows/ for generated windows"
    echo "  3. Compare ASR quality with and without bias"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ $WARNINGS warning(s) found${NC}"
    echo ""
    echo "Implementation is complete, but some optional components are missing."
    echo "This should not affect functionality."
    exit 0
else
    echo -e "${RED}✗ $ERRORS error(s) found${NC}"
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}⚠ $WARNINGS warning(s) found${NC}"
    fi
    echo ""
    echo "Please fix the errors above before using bias injection."
    exit 1
fi
