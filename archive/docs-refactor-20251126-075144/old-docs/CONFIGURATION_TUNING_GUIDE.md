# Configuration Tuning Guide - Confidence-Based Hybrid Translation

## Overview
This guide explains how to tune the confidence-based hybrid translation system for optimal cost/quality balance.

## Key Parameters

### 1. `CONFIDENCE_THRESHOLD` (Translation Quality)
**Location**: `config/.env.pipeline` line 471  
**Range**: 0.0 - 1.0  
**Default**: 0.7

Controls when to trigger fallback to alternative translation method.

#### Values:
- **0.6** - Cost optimized (fewer fallbacks, faster)
- **0.7** - Balanced (recommended)
- **0.8** - Quality optimized (more fallbacks, slower)

#### Impact:
```
Threshold 0.6:
  - 5-10% fallback rate
  - Faster processing
  - Lower API costs
  - May miss some poor translations

Threshold 0.7 (default):
  - 10-20% fallback rate
  - Good balance
  - Automatic quality improvement

Threshold 0.8:
  - 20-30% fallback rate
  - Slower processing
  - Highest quality
  - Catches most issues
```

### 2. `ENABLE_CONFIDENCE_FALLBACK` (Fallback System)
**Location**: `config/.env.pipeline` line 472  
**Values**: true | false  
**Default**: true

Enable/disable the entire confidence-based fallback system.

#### When to Disable:
- Testing single translation methods
- Debugging translation issues
- Maximum speed priority (at cost of quality)

### 3. `LYRICS_DETECTION_THRESHOLD` (Song Detection)
**Location**: `config/.env.pipeline` line 485  
**Range**: 0.0 - 1.0  
**Default**: 0.5

Controls sensitivity of song/lyrics detection from audio analysis.

#### Values:
- **0.3** - Sensitive (catches more songs, more false positives)
- **0.5** - Balanced (recommended)
- **0.7** - Strict (only obvious songs, fewer false positives)

#### Impact on Cost:
```
Threshold 0.3 (sensitive):
  - Detects: 30-40 segments as songs
  - LLM attempts: 30-40
  - Cost: Higher
  - Best for: Music videos, musicals

Threshold 0.5 (balanced):
  - Detects: 15-25 segments as songs
  - LLM attempts: 15-25
  - Cost: Moderate
  - Best for: Bollywood movies (standard)

Threshold 0.7 (strict):
  - Detects: 5-15 segments as songs
  - LLM attempts: 5-15
  - Cost: Lower
  - Best for: Dialogue-heavy content
```

## How Parameters Work Together

### Scenario 1: Standard Bollywood Movie
**Goal**: Balanced quality and cost

```bash
LYRICS_DETECTION_THRESHOLD=0.5      # Detect typical songs
CONFIDENCE_THRESHOLD=0.7            # Standard quality bar
ENABLE_CONFIDENCE_FALLBACK=true     # Enable smart fallback
USE_LLM_FOR_SONGS=true              # LLM for songs
```

**Expected Flow**:
```
200 segments total
├─ 20 segments: High lyric confidence (>0.7)
│  ├─ Primary: LLM (creative translation)
│  ├─ Cost: 20 × $0.01 = $0.20
│  └─ Fallback: 2-3 low confidence → IndicTrans2 ($0)
└─ 180 segments: Dialogue
   ├─ Primary: IndicTrans2 (fast, free)
   ├─ Cost: $0
   └─ Fallback: 10-15 low confidence → (no LLM fallback for dialogue)

Total Cost: ~$0.18
Fallback Rate: ~10%
```

### Scenario 2: Cost-Optimized (API Budget Constraints)
**Goal**: Minimize LLM usage

```bash
LYRICS_DETECTION_THRESHOLD=0.7      # Only obvious songs
CONFIDENCE_THRESHOLD=0.6            # Lower quality bar (fewer fallbacks)
ENABLE_CONFIDENCE_FALLBACK=true     # Keep safety net
USE_LLM_FOR_SONGS=true              # Still use LLM for clear songs
```

**Expected Flow**:
```
200 segments total
├─ 10 segments: High lyric confidence (>0.7, strict)
│  ├─ Primary: LLM
│  ├─ Cost: 10 × $0.01 = $0.10
│  └─ Fallback: 1-2 → IndicTrans2 ($0)
└─ 190 segments: Dialogue or low-confidence music
   ├─ Primary: IndicTrans2 (free)
   └─ Fallback: 5-8 → (no LLM for dialogue)

Total Cost: ~$0.09
Savings: 50% vs standard
```

### Scenario 3: Quality-Optimized (Professional Subtitles)
**Goal**: Best possible translation quality

```bash
LYRICS_DETECTION_THRESHOLD=0.4      # Catch more songs
CONFIDENCE_THRESHOLD=0.8            # High quality bar
ENABLE_CONFIDENCE_FALLBACK=true     # Maximum fallback
USE_LLM_FOR_SONGS=true              # LLM for all songs
```

**Expected Flow**:
```
200 segments total
├─ 30 segments: Lyric confidence >0.4 (sensitive)
│  ├─ Primary: LLM
│  ├─ Cost: 30 × $0.01 = $0.30
│  └─ Fallback: 5-7 low confidence → Try IndicTrans2
└─ 170 segments: Dialogue
   ├─ Primary: IndicTrans2
   └─ Fallback: 25-35 low confidence → Re-evaluated

Total Cost: ~$0.30
Fallback Rate: 20-30%
Quality: Highest
```

### Scenario 4: No LLM (Anthropic Credits Exhausted)
**Goal**: Free fallback, no API dependency

```bash
LYRICS_DETECTION_THRESHOLD=0.5      # Still detect songs
CONFIDENCE_THRESHOLD=0.7            # Standard bar
ENABLE_CONFIDENCE_FALLBACK=true     # Enable fallback
USE_LLM_FOR_SONGS=false             # Disable LLM (no credits)
```

**Expected Flow**:
```
200 segments total
├─ All segments: IndicTrans2 (no LLM)
│  ├─ Cost: $0 (completely free)
│  └─ Fallback: None (single method)
└─ Lyrics info still tracked for future use

Total Cost: $0
Note: Lyric detection still runs, confidence tracked
      Ready for LLM when credits available
```

## Troubleshooting

### Issue: Too Many LLM API Calls (High Cost)
**Symptoms**: More than 30-40% segments using LLM
**Cause**: `LYRICS_DETECTION_THRESHOLD` too low (too sensitive)

**Solution**:
```bash
# Increase threshold to be more strict
LYRICS_DETECTION_THRESHOLD=0.7  # Was 0.5
```

### Issue: Missing Song Segments
**Symptoms**: Songs translated poorly, obvious lyrics using IndicTrans2
**Cause**: `LYRICS_DETECTION_THRESHOLD` too high (not sensitive enough)

**Solution**:
```bash
# Lower threshold to catch more songs
LYRICS_DETECTION_THRESHOLD=0.4  # Was 0.5
```

### Issue: Frequent Fallbacks (Slow Processing)
**Symptoms**: >30% fallback rate, slow pipeline
**Cause**: `CONFIDENCE_THRESHOLD` too high

**Solution**:
```bash
# Lower threshold (accept more translations)
CONFIDENCE_THRESHOLD=0.6  # Was 0.7 or 0.8
```

### Issue: Poor Translation Quality
**Symptoms**: Repetitions, truncated text, gibberish
**Cause**: `CONFIDENCE_THRESHOLD` too low (not catching issues)

**Solution**:
```bash
# Raise threshold (trigger more fallbacks)
CONFIDENCE_THRESHOLD=0.8  # Was 0.6 or 0.7
```

## Testing Recommendations

### Step 1: Baseline Test
```bash
CONFIDENCE_THRESHOLD=0.7
LYRICS_DETECTION_THRESHOLD=0.5
ENABLE_CONFIDENCE_FALLBACK=true
```
Run on a 5-10 minute clip, check logs for:
- `low_confidence_count`
- `fallback_triggered`
- Total API costs

### Step 2: Tune Lyrics Detection
Adjust `LYRICS_DETECTION_THRESHOLD` based on content:
- Adjust up (0.6-0.7) if too many dialogue segments marked as songs
- Adjust down (0.4) if missing obvious song segments

### Step 3: Tune Quality Threshold
Adjust `CONFIDENCE_THRESHOLD` based on results:
- Increase (0.8) if seeing poor translations slip through
- Decrease (0.6) if costs too high and quality acceptable

## Monitoring

Check these values in the log file:
```
Translation statistics:
  Total segments: 200
  Dialogue segments: 180
  Song segments: 20
  IndicTrans2 used: 185
  LLM used: 15
  Low confidence count: 25      ← Should be 10-30%
  Fallback triggered: 12        ← Should be 5-20%
  Errors: 0
```

Good indicators:
- ✅ Fallback triggered ≈ 50% of low confidence count
- ✅ Low confidence count: 10-30% of total
- ✅ LLM used ≈ song segments (when API available)
- ✅ Errors = 0

Bad indicators:
- ❌ Fallback triggered > 40% of total (threshold too high)
- ❌ Low confidence count < 5% (threshold too low, not catching issues)
- ❌ LLM used = 0 when song segments > 0 (API issues)

