# Beam Search Optimization for Translation Quality

**Version**: 1.0  
**Date**: November 25, 2025  
**Status**: Design Document

## Overview

Implement automatic beam search optimization to find the optimal beam size (4-10) that produces the highest quality translation.

## Current Implementation

### Beam Size Configuration

**File**: `config/.env.pipeline`
```bash
# Single fixed beam size
INDICTRANS2_NUM_BEAMS=4
```

**Usage**: Fixed beam size for all translations

## Proposed Implementation

### Strategy: Beam Size Grid Search

Run translation with multiple beam sizes and select the best result based on quality metrics.

### Beam Size Range
- **Minimum**: 4 beams (current default)
- **Maximum**: 10 beams (quality vs. speed trade-off)
- **Step**: 1 (test each value: 4, 5, 6, 7, 8, 9, 10)

### Quality Metrics

#### 1. **Translation Confidence Score**
- Average confidence from translation model
- Higher is better
- Range: 0.0 - 1.0

#### 2. **Perplexity Score**
- Measure of translation fluency
- Lower is better
- Indicates how "natural" the translation is

#### 3. **BLEU Score (if reference available)**
- Comparison with reference translation
- Higher is better
- Range: 0.0 - 1.0

#### 4. **Character Repetition Rate**
- Detect hallucinations/repetitions
- Lower is better
- Indicates translation quality issues

#### 5. **Word Diversity Score**
- Measure vocabulary richness
- Higher is better
- Indicates natural language usage

### Implementation Options

#### Option A: Sequential Evaluation (Simple)

**Pros**:
- Easy to implement
- Clear quality comparison
- Full control over metrics

**Cons**:
- 7x slower (runs 7 translations)
- High compute cost

**Implementation**:
```python
def optimize_beam_search(segments, source_lang, target_lang):
    """Run translation with multiple beam sizes and select best"""
    
    best_result = None
    best_score = -float('inf')
    
    for num_beams in range(4, 11):
        # Translate with this beam size
        result = translate(segments, num_beams=num_beams)
        
        # Calculate quality score
        score = calculate_quality_score(result)
        
        if score > best_score:
            best_score = score
            best_result = result
    
    return best_result, best_score
```

#### Option B: Adaptive Search (Efficient)

**Pros**:
- Faster than sequential
- Stops when quality plateaus
- More efficient

**Cons**:
- More complex logic
- May miss global optimum

**Implementation**:
```python
def adaptive_beam_search(segments, source_lang, target_lang):
    """Find optimal beam size using adaptive search"""
    
    # Start with middle value
    current_beams = 7
    results = {}
    
    # Test current
    results[current_beams] = translate_and_score(segments, current_beams)
    
    # Test lower and higher
    for direction in [-1, 1]:
        test_beams = current_beams + direction
        if 4 <= test_beams <= 10:
            results[test_beams] = translate_and_score(segments, test_beams)
    
    # Find best in tested range
    best_beams = max(results.keys(), key=lambda k: results[k]['score'])
    
    # Expand search if best is at boundary
    while best_beams in [4, 10]:
        # ... expand search ...
        
    return results[best_beams]
```

#### Option C: Sample-Based Optimization (Balanced)

**Pros**:
- Fast - only translates sample segments
- Good quality estimate
- Practical for production

**Cons**:
- May not reflect full corpus quality
- Needs representative sample

**Implementation**:
```python
def sample_based_optimization(segments, source_lang, target_lang, sample_size=20):
    """Optimize beam size using representative sample"""
    
    # Select representative sample
    sample = select_representative_sample(segments, sample_size)
    
    # Test beam sizes on sample
    best_beams = None
    best_score = -float('inf')
    
    for num_beams in range(4, 11):
        # Fast translation on sample
        result = translate(sample, num_beams=num_beams)
        score = calculate_quality_score(result)
        
        if score > best_score:
            best_score = score
            best_beams = num_beams
    
    # Translate full corpus with optimal beam size
    final_result = translate(segments, num_beams=best_beams)
    
    return final_result, best_beams
```

## Recommended Approach

### Hybrid: Sample + Validation

1. **Phase 1: Sample Optimization (Fast)**
   - Test beams 4-10 on 20 representative segments
   - Find top 3 beam sizes

2. **Phase 2: Validation (Accurate)**
   - Test top 3 beam sizes on 100 segments
   - Select best performer

3. **Phase 3: Full Translation**
   - Use optimal beam size for full corpus

**Total Cost**: ~2x slower than single beam (vs 7x for full grid search)

## Quality Scoring Function

```python
def calculate_quality_score(translation_result):
    """Calculate composite quality score"""
    
    scores = {}
    
    # 1. Translation confidence (0-1, higher better)
    scores['confidence'] = translation_result.avg_confidence
    
    # 2. Perplexity (normalize, lower better)
    scores['perplexity'] = 1.0 / (1.0 + translation_result.perplexity)
    
    # 3. Repetition rate (0-1, lower better)
    scores['repetition'] = 1.0 - translation_result.repetition_rate
    
    # 4. Word diversity (0-1, higher better)
    scores['diversity'] = translation_result.word_diversity
    
    # 5. Length ratio (penalize too short/long)
    length_ratio = len(translation_result.text) / len(translation_result.source_text)
    scores['length'] = 1.0 - abs(length_ratio - 1.0)
    
    # Weighted composite score
    weights = {
        'confidence': 0.3,
        'perplexity': 0.2,
        'repetition': 0.2,
        'diversity': 0.15,
        'length': 0.15
    }
    
    composite_score = sum(scores[k] * weights[k] for k in scores)
    
    return composite_score, scores
```

## Configuration

### New Parameters in `.env.pipeline`

```bash
# ============================================================================
# BEAM SEARCH OPTIMIZATION
# ============================================================================

# Enable automatic beam search optimization
INDICTRANS2_OPTIMIZE_BEAMS=false

# Beam size range for optimization
INDICTRANS2_BEAM_MIN=4
INDICTRANS2_BEAM_MAX=10

# Optimization strategy: sample | full | adaptive
INDICTRANS2_OPTIMIZATION_STRATEGY=sample

# Sample size for sample-based optimization
INDICTRANS2_OPTIMIZATION_SAMPLE_SIZE=20

# Quality metric weights (comma-separated)
INDICTRANS2_QUALITY_WEIGHTS=0.3,0.2,0.2,0.15,0.15
```

## Pipeline Integration

### New Stage: `beam_optimization` (Optional)

**Location**: Between ASR and Translation

**Flow**:
```
05_asr → [06_beam_optimization] → 08_translation
```

**Purpose**: Determine optimal beam size before full translation

### Modified Translation Stage

**If optimization enabled**:
```python
if optimize_beams:
    optimal_beams = run_beam_optimization(sample_segments)
    self.logger.info(f"✓ Optimal beam size: {optimal_beams}")
    num_beams = optimal_beams
else:
    num_beams = config.get("INDICTRANS2_NUM_BEAMS", 4)
```

## Expected Output

### Log Messages

```
[INFO] ▶️  Stage beam_optimization: STARTING
[INFO] Testing beam sizes: 4-10 on 20 sample segments
[INFO]   Beam 4: Quality=0.72 (confidence=0.75, diversity=0.68)
[INFO]   Beam 5: Quality=0.76 (confidence=0.78, diversity=0.71)
[INFO]   Beam 6: Quality=0.79 (confidence=0.82, diversity=0.74) ⭐
[INFO]   Beam 7: Quality=0.78 (confidence=0.81, diversity=0.73)
[INFO]   Beam 8: Quality=0.76 (confidence=0.80, diversity=0.71)
[INFO]   Beam 9: Quality=0.74 (confidence=0.79, diversity=0.69)
[INFO]   Beam 10: Quality=0.73 (confidence=0.78, diversity=0.68)
[INFO] ✓ Optimal beam size: 6 (quality score: 0.79)
[INFO] ✅ Stage beam_optimization: COMPLETED (45s)

[INFO] ▶️  Stage translation: STARTING
[INFO] Using optimized beam size: 6
[INFO] Translating 188 segments...
```

### Quality Report

```json
{
  "beam_optimization": {
    "enabled": true,
    "strategy": "sample",
    "sample_size": 20,
    "tested_beams": [4, 5, 6, 7, 8, 9, 10],
    "results": {
      "4": {"score": 0.72, "confidence": 0.75, "diversity": 0.68},
      "5": {"score": 0.76, "confidence": 0.78, "diversity": 0.71},
      "6": {"score": 0.79, "confidence": 0.82, "diversity": 0.74},
      "7": {"score": 0.78, "confidence": 0.81, "diversity": 0.73},
      "8": {"score": 0.76, "confidence": 0.80, "diversity": 0.71},
      "9": {"score": 0.74, "confidence": 0.79, "diversity": 0.69},
      "10": {"score": 0.73, "confidence": 0.78, "diversity": 0.68}
    },
    "optimal_beam_size": 6,
    "optimal_score": 0.79,
    "optimization_time": 45.2
  }
}
```

## Performance Considerations

### Time Cost

| Strategy | Cost | Time (est) |
|----------|------|------------|
| No optimization (fixed beam) | 1x | 3 min |
| Full grid search (7 beams) | 7x | 21 min |
| Sample-based (20 segments) | ~2x | 6 min |
| Adaptive search | ~3x | 9 min |

### Recommendation

- **Development**: Use sample-based (20 segments)
- **Production**: Cache optimal beam per film/genre
- **One-time**: Run full grid search to determine patterns

## Future Enhancements

1. **Per-Genre Optimization**
   - Cache optimal beams per genre
   - Example: Comedy=5, Drama=7, Action=4

2. **Segment-Level Optimization**
   - Use different beams for dialogue vs songs
   - Dialogue: beam=4 (speed)
   - Songs: beam=8 (quality)

3. **Model-Specific Tuning**
   - Different optimal beams for different model sizes
   - Large model: beam=4-6
   - Small model: beam=6-8

4. **Quality Threshold**
   - Stop when quality exceeds threshold
   - Example: If beam=5 achieves score≥0.8, skip testing 6-10

## Implementation Priority

1. **P0 (Immediate)**:
   - Add configuration parameters
   - Implement quality scoring function
   - Add sample-based optimization

2. **P1 (Next Sprint)**:
   - Integrate into translation stage
   - Add logging and reporting
   - Create quality report JSON

3. **P2 (Future)**:
   - Genre-based caching
   - Adaptive search algorithm
   - Segment-level optimization

---

**Status**: Design Complete  
**Next Step**: Implement sample-based optimization  
**Owner**: Development Team  
**Last Updated**: November 25, 2025
