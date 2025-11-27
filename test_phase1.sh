#!/bin/bash
# Phase 1 Testing Script
# Tests ASR optimization changes

set -e

PROJECT_ROOT="/Users/rpatel/Projects/cp-whisperx-app"
cd "$PROJECT_ROOT"

echo "=================================="
echo "PHASE 1: ASR OPTIMIZATION TESTING"
echo "=================================="
echo ""

# Verify configuration
echo "1. Verifying configuration changes..."
echo "   Checking BIAS_STRATEGY..."
if grep -q "^BIAS_STRATEGY=hybrid" config/.env.pipeline; then
    echo "   ✅ BIAS_STRATEGY=hybrid"
else
    echo "   ❌ BIAS_STRATEGY not set"
    exit 1
fi

echo "   Checking WHISPER_TEMPERATURE..."
if grep -q "^WHISPER_TEMPERATURE=0.0,0.1,0.2" config/.env.pipeline; then
    echo "   ✅ WHISPER_TEMPERATURE=0.0,0.1,0.2"
else
    echo "   ❌ WHISPER_TEMPERATURE not optimized"
    exit 1
fi

echo "   Checking WHISPER_BEAM_SIZE..."
if grep -q "^WHISPER_BEAM_SIZE=8" config/.env.pipeline; then
    echo "   ✅ WHISPER_BEAM_SIZE=8"
else
    echo "   ❌ WHISPER_BEAM_SIZE not set"
    exit 1
fi

echo ""
echo "2. Configuration Summary:"
grep "^BIAS_WINDOW_SECONDS\|^BIAS_STRIDE_SECONDS\|^BIAS_TOPK\|^BIAS_STRATEGY" config/.env.pipeline
echo ""
grep "^WHISPER_TEMPERATURE\|^WHISPER_BEAM_SIZE\|^WHISPER_BEST_OF" config/.env.pipeline
echo ""
grep "^WHISPER_NO_SPEECH\|^WHISPER_LOGPROB\|^WHISPER_COMPRESSION" config/.env.pipeline
echo ""

echo "=================================="
echo "Configuration verification complete!"
echo "=================================="
echo ""
echo "Next Steps:"
echo "1. Run test job:"
echo "   ./prepare-job.sh \\"
echo "     --media 'in/Jaane Tu Ya Jaane Na 2008.mp4' \\"
echo "     --workflow translate \\"
echo "     --source-language hi \\"
echo "     --target-language en \\"
echo "     --start-time 00:00:00 \\"
echo "     --end-time 00:05:00"
echo ""
echo "2. Check output:"
echo "   ls -lh out/*/06_asr/"
echo ""
echo "3. Validate results:"
echo "   cat out/*/06_asr/transcript*.txt"
echo ""
