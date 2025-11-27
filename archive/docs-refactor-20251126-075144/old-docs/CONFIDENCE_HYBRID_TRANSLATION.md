# Confidence-Based Hybrid Translation

## Overview
Enhanced hybrid translation system that uses multiple confidence signals to automatically select the best translation method for each segment.

## How It Works

### 1. **Primary Translation**
- **Songs/Poetry** → LLM (Claude/GPT) for creative, context-aware translation
- **Dialogue** → IndicTrans2 for fast, accurate translation

### 2. **Confidence Evaluation**
Multiple signals are combined to calculate overall confidence:

#### A. Lyrics Detection Confidence
- **High confidence (>0.7)**: Strong audio indicators of music/singing
  - LLM is preferred for better poetic translation
- **Low confidence (<0.5)**: Likely dialogue with background music
  - IndicTrans2 is sufficient

#### B. Translation Quality Heuristics
- **Length ratio**: Translated text should be 30-300% of original
- **Repetition detection**: Flags hallucinations (same word repeated)
- **Character variety**: Detects garbage output
- **Empty translations**: Obvious failures

### 3. **Confidence-Based Fallback**
If primary translation has low confidence (< 0.7):
- **IndicTrans2 → LLM**: Song with poor machine translation → try LLM
- **LLM → IndicTrans2**: LLM failed/unavailable → use reliable IndicTrans2

## Configuration

Add to your `.env` file or job config:

```bash
# Enable confidence-based fallback (default: true)
ENABLE_CONFIDENCE_FALLBACK=true

# Minimum confidence threshold (0.0 to 1.0, default: 0.7)
CONFIDENCE_THRESHOLD=0.7

# Use LLM for high-confidence songs (default: true)
USE_LLM_FOR_SONGS=true

# LLM provider (anthropic or openai)
LLM_PROVIDER=anthropic

# Lyrics detection threshold (affects confidence)
LYRICS_DETECTION_THRESHOLD=0.5
```

## Benefits

### 1. **Cost Optimization**
- LLM only used when needed (high-confidence songs)
- Automatic fallback to free IndicTrans2 if LLM fails

### 2. **Quality Improvement**
- Detects and re-translates poor quality segments
- Catches hallucinations and repetitions
- Validates translation completeness

### 3. **Lyrics Detection Integration**
- Uses audio analysis to identify true song segments
- Reduces false positives (dialogue with music)
- Better routing decisions

## Statistics

The system tracks:
- `low_confidence_count`: Segments below threshold
- `fallback_triggered`: Times fallback was used
- `translation_confidence`: Per-segment confidence scores

## Example Output

```json
{
  "text": "तुम्हें मैं प्यार करता हूं",
  "translation": "I love you",
  "translation_method": "hybrid_indictrans2_fallback",
  "translation_confidence": 0.85,
  "lyric_confidence": 0.92,
  "fallback_reason": "low_confidence_indictrans2_for_song"
}
```

## Use Cases

### Scenario 1: High-Confidence Song
```
Lyric confidence: 0.95
Primary: LLM → High quality poetic translation
Confidence: 0.90 ✓
Result: Use LLM translation
```

### Scenario 2: Low-Confidence Song (Dialogue with Music)
```
Lyric confidence: 0.45
Primary: IndicTrans2 → Accurate dialogue translation
Confidence: 0.85 ✓
Result: Use IndicTrans2 (cost-effective)
```

### Scenario 3: Failed Translation
```
Lyric confidence: 0.88
Primary: LLM → API Error/Empty translation
Confidence: 0.20 ✗
Fallback: IndicTrans2 → Good translation
Confidence: 0.75 ✓
Result: Use IndicTrans2 fallback
```

## Tuning Tips

- **High precision**: Set `CONFIDENCE_THRESHOLD=0.8` (more fallbacks, higher quality)
- **Cost sensitive**: Set `CONFIDENCE_THRESHOLD=0.6` (fewer fallbacks, lower cost)
- **Lyrics only**: Set `LYRICS_DETECTION_THRESHOLD=0.7` (stricter song detection)
