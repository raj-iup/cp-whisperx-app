# Confidence-Based Hybrid Translation - Implementation Summary

## What Was Implemented

### ✅ Core Features

1. **Enhanced TranslationResult Dataclass**
   - Added `lyric_confidence` field from lyrics detection
   - Added `fallback_reason` to track why fallback was triggered

2. **Confidence Calculation System**
   - Multi-signal confidence scoring:
     - Lyrics detection confidence (audio analysis)
     - Translation quality heuristics (length ratio, repetition, variety)
     - Method-specific confidence scores
   - Weighted scoring algorithm (0.0 to 1.0)

3. **Confidence-Based Fallback**
   - Automatic fallback when confidence < threshold (default: 0.7)
   - Smart routing:
     - Low-confidence IndicTrans2 for songs → Try LLM
     - Failed/low-confidence LLM → Try IndicTrans2
   - Comparison of results, picks better one

4. **Lyrics Detection Integration**
   - Reads `lyric_confidence` from lyrics detection stage
   - Uses confidence to make smarter routing decisions
   - High lyric confidence → Prefer LLM for poetry
   - Low lyric confidence → Use IndicTrans2 (cost-effective)

5. **Enhanced Statistics**
   - `low_confidence_count`: Segments below threshold
   - `fallback_triggered`: Times fallback was used
   - Per-segment confidence tracking

6. **Configuration Support**
   - `CONFIDENCE_THRESHOLD`: Minimum confidence (default: 0.7)
   - `ENABLE_CONFIDENCE_FALLBACK`: Toggle fallback (default: true)
   - Integrates with existing config system

## How Lyrics Detection Helps

### 🎵 Key Benefits

1. **Reduces False Positives**
   - Detects true songs vs dialogue with background music
   - Audio feature analysis (tempo, rhythm, spectral features)
   - Prevents wasting LLM API calls on non-song segments

2. **Quality Signal**
   - High confidence (>0.8) = Strong song indicators
   - Medium confidence (0.5-0.8) = Borderline, use heuristics
   - Low confidence (<0.5) = Likely dialogue, use IndicTrans2

3. **Cost Optimization**
   - Only use expensive LLM for high-confidence songs
   - Example: 200 segments, 20 detected as songs (high confidence)
     - Without confidence: 20 LLM calls
     - With confidence: Maybe 10-15 LLM calls (others use IndicTrans2)
     - Cost savings: 25-50%

4. **Better Routing Decisions**
   ```
   Segment with background music:
   - Lyric confidence: 0.4 (low)
   - Route: IndicTrans2 (accurate for dialogue)
   - Cost: $0 (free)
   
   Actual song segment:
   - Lyric confidence: 0.95 (high)
   - Route: LLM (creative, poetic)
   - Cost: ~$0.01 per segment
   ```

## Files Modified

1. **scripts/hybrid_translator.py**
   - Added confidence calculation logic
   - Added fallback mechanism
   - Enhanced statistics tracking
   - Updated dataclasses

2. **scripts/run-pipeline.py** (previous fix)
   - Added `OUTPUT_DIR` environment variable

3. **docs/CONFIDENCE_HYBRID_TRANSLATION.md** (new)
   - Complete documentation
   - Configuration guide
   - Use cases and examples

## Testing Recommendations

### 1. Test with Different Thresholds
```bash
# High precision (more fallbacks)
CONFIDENCE_THRESHOLD=0.8

# Balanced (default)
CONFIDENCE_THRESHOLD=0.7

# Cost optimized (fewer fallbacks)
CONFIDENCE_THRESHOLD=0.6
```

### 2. Test Lyrics Detection Thresholds
```bash
# Strict (fewer false positives)
LYRICS_DETECTION_THRESHOLD=0.7

# Balanced (default)
LYRICS_DETECTION_THRESHOLD=0.5

# Sensitive (catch more songs)
LYRICS_DETECTION_THRESHOLD=0.3
```

### 3. Monitor Statistics
Check log files for:
- `low_confidence_count` (should be ~10-30% of segments)
- `fallback_triggered` (should be ~5-15% when working well)
- `translation_confidence` values in output JSON

## Next Steps (Optional Enhancements)

1. **Add BLEU Score Evaluation**
   - Compare IndicTrans2 vs LLM translations
   - Use as confidence signal

2. **Segment Length Consideration**
   - Short segments (1-3 words) → IndicTrans2 (fast)
   - Long segments (poetry) → LLM (better context)

3. **Historical Confidence Tracking**
   - Learn which segments types benefit from fallback
   - Adapt threshold per movie/genre

4. **Multi-Model Ensemble**
   - Try both methods in parallel
   - Use confidence voting to select best

## Cost Comparison

### Example: 6-minute clip, 200 segments, 20 songs detected

#### Without Confidence System:
- All 20 songs → LLM: $0.20
- 180 dialogue → IndicTrans2: $0
- **Total: $0.20**

#### With Confidence System:
- 12 high-confidence songs → LLM: $0.12
- 8 low-confidence "songs" → IndicTrans2: $0
- 180 dialogue → IndicTrans2: $0
- **Total: $0.12**
- **Savings: 40%**

Plus:
- Automatic fallback for LLM API failures
- Better quality for edge cases
- No manual intervention needed

