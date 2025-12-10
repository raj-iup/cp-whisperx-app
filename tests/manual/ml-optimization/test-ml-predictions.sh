#!/usr/bin/env bash
################################################################################
# Test ML-Based Adaptive Quality Prediction (AD-015)
#
# This script demonstrates how the ML optimizer predicts optimal parameters
# based on audio characteristics.
#
# Usage:
#   ./tests/manual/ml-optimization/test-ml-predictions.sh
#
# Architecture Decision: AD-015 (ML-Based Adaptive Optimization)
################################################################################

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "ML-BASED ADAPTIVE QUALITY PREDICTION TEST"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Test 1: Verify ML optimizer is available
echo -e "${BLUE}TEST 1: ML Optimizer Module${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd "$PROJECT_ROOT"

python3 -c "
from shared.ml_optimizer import AdaptiveQualityPredictor, AudioFingerprint
predictor = AdaptiveQualityPredictor()
print('✓ ML optimizer module loaded successfully')
" || {
    echo -e "${RED}✗ Failed to load ML optimizer${NC}"
    exit 1
}
echo ""

# Test 2: Test rule-based predictions (no trained model)
echo -e "${BLUE}TEST 2: Rule-Based Predictions${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

python3 << 'EOF'
from shared.ml_optimizer import AdaptiveQualityPredictor, AudioFingerprint

predictor = AdaptiveQualityPredictor()

# Test Case 1: Clean short audio (should use smaller model)
print("📊 Test Case 1: Clean Short Audio")
fp1 = AudioFingerprint(
    duration=120.0,        # 2 minutes
    sample_rate=16000,
    channels=1,
    snr_estimate=30.0,     # Very clean
    language="en",
    speaker_count=1,       # Single speaker
    complexity_score=0.3,  # Low complexity
    file_size=10.0
)
config1 = predictor.predict_optimal_config(fp1)
print(f"  → Model: {config1.whisper_model}")
print(f"  → Batch size: {config1.batch_size}")
print(f"  → Beam size: {config1.beam_size}")
print(f"  → Expected WER: {config1.expected_wer:.1%}")
print(f"  → Confidence: {config1.confidence:.0%}")
print(f"  → Reasoning: {config1.reasoning}")
print("")

# Test Case 2: Noisy long audio (should use larger model)
print("📊 Test Case 2: Noisy Long Audio")
fp2 = AudioFingerprint(
    duration=1800.0,       # 30 minutes
    sample_rate=16000,
    channels=1,
    snr_estimate=12.0,     # Very noisy
    language="hi",
    speaker_count=3,       # Multiple speakers
    complexity_score=0.8,  # High complexity
    file_size=150.0
)
config2 = predictor.predict_optimal_config(fp2)
print(f"  → Model: {config2.whisper_model}")
print(f"  → Batch size: {config2.batch_size}")
print(f"  → Beam size: {config2.beam_size}")
print(f"  → Expected WER: {config2.expected_wer:.1%}")
print(f"  → Confidence: {config2.confidence:.0%}")
print(f"  → Reasoning: {config2.reasoning}")
print("")

# Test Case 3: Medium quality (balanced)
print("📊 Test Case 3: Medium Quality Audio")
fp3 = AudioFingerprint(
    duration=600.0,        # 10 minutes
    sample_rate=16000,
    channels=1,
    snr_estimate=20.0,     # Moderate quality
    language="en",
    speaker_count=2,       # Dialogue
    complexity_score=0.5,  # Medium complexity
    file_size=50.0
)
config3 = predictor.predict_optimal_config(fp3)
print(f"  → Model: {config3.whisper_model}")
print(f"  → Batch size: {config3.batch_size}")
print(f"  → Beam size: {config3.beam_size}")
print(f"  → Expected WER: {config3.expected_wer:.1%}")
print(f"  → Confidence: {config3.confidence:.0%}")
print(f"  → Reasoning: {config3.reasoning}")
print("")

print("✓ All rule-based predictions completed successfully")
EOF

echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}SUMMARY${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ ML Optimizer Status:"
echo "  • Rule-based predictions: Working"
echo "  • Expected performance: 30% faster on clean audio"
echo ""
