# Subtitle Generation Accuracy Improvement Roadmap

**Project:** cp-whisperx-app
**Created:** 2025-11-28
**Goal:** Improve subtitle accuracy from ~85% to ~95% with 80% reduction in hallucinations

---

## Executive Summary

This roadmap implements 5 major improvements across 5 phases to enhance subtitle generation quality:

- **Phase 1 (Quick Wins):** 2-3 days - Configuration + filtering (30% immediate improvement)
- **Phase 2 (Hallucination Fix):** 3-4 days - Enhanced detection (80% hallucination reduction)
- **Phase 3 (Readability):** 4-5 days - Segment merging (50% fewer segments)
- **Phase 4 (Advanced):** 5-7 days - Pipeline integration (15-20% proper noun improvement)
- **Phase 5 (Validation):** 2-3 days - Testing framework and metrics

**Total Timeline:** 16-22 days
**Expected ROI:** 85% → 95% accuracy, significantly improved user experience

---

## Phase 1: Quick Wins (Days 1-3)

### Objective
Implement configuration changes and basic filtering with minimal code changes for immediate accuracy gains.

### Tasks

#### 1.1 Optimize WhisperX Parameters
**File:** `config/.env.pipeline`
**Effort:** 1 hour
**Impact:** 🟢 High (10-15% accuracy, 20-30% speed)

```bash
# Current issues:
# - Too many temperature values (slower)
# - Threshold too permissive (hallucinations)

# Changes to make:
WHISPERX_MODEL=large-v3
WHISPERX_TEMPERATURE=0.0,0.2,0.4          # Reduce from 6 → 3 values
WHISPERX_BEAM_SIZE=5                      # Keep
WHISPERX_BEST_OF=5                        # Keep
WHISPERX_CONDITION_ON_PREVIOUS=false      # Keep (anti-hallucination)
WHISPERX_NO_SPEECH_THRESHOLD=0.65         # Increase from 0.6
WHISPERX_LOGPROB_THRESHOLD=-0.7           # Increase from -1.0
WHISPERX_COMPRESSION_RATIO=2.2            # Decrease from 2.4
BIAS_PROMPT_STRATEGY=hybrid               # Use hybrid by default
```

**Validation:**
```bash
# Test with sample file
./pipeline.sh --input test-data/sample.mp4 --job-id test-params
# Compare output quality vs baseline
```

---

#### 1.2 Implement Confidence-Based Filtering
**File:** `scripts/whisperx_integration.py`
**Location:** After transcription processing (~line 800)
**Effort:** 2-3 hours
**Impact:** 🟢 High (30-50% hallucination reduction)

**Implementation:**

```python
def filter_low_confidence_segments(segments, min_logprob=-0.7, min_duration=0.1):
    """
    Filter out low-confidence and zero-duration segments.

    Args:
        segments: List of transcription segments
        min_logprob: Minimum average log probability (-0.7 recommended)
        min_duration: Minimum segment duration in seconds (0.1s recommended)

    Returns:
        Filtered segments list
    """
    filtered = []
    removed_count = 0

    for seg in segments:
        # Check confidence (avg_logprob)
        avg_logprob = seg.get('avg_logprob', 0)
        if avg_logprob < min_logprob:
            removed_count += 1
            continue

        # Check duration
        duration = seg.get('end', 0) - seg.get('start', 0)
        if duration < min_duration:
            removed_count += 1
            continue

        # Check for empty text
        if not seg.get('text', '').strip():
            removed_count += 1
            continue

        filtered.append(seg)

    logger.info(f"Confidence filtering: Removed {removed_count}/{len(segments)} segments")
    return filtered


# Add to transcription pipeline (find the main transcription function)
# After: segments = result["segments"]
# Add:
segments = filter_low_confidence_segments(
    segments,
    min_logprob=float(os.getenv('WHISPERX_LOGPROB_THRESHOLD', -0.7)),
    min_duration=0.1
)
```

**Files to modify:**
1. `scripts/whisperx_integration.py` - Add filter function
2. `config/.env.pipeline` - Add `WHISPERX_MIN_DURATION=0.1` setting

**Testing:**
```bash
# Before/after comparison
./test-glossary-quickstart.sh
# Check metrics in manifest.json
cat test-results/glossary/1/06_asr/manifest.json | jq '.metrics'
```

---

#### 1.3 Add Configuration Validation
**File:** `config/config.py`
**Effort:** 1 hour
**Impact:** 🟡 Medium (prevents misconfigurations)

**Implementation:**

```python
def validate_whisperx_config():
    """Validate WhisperX configuration for optimal accuracy"""
    issues = []

    # Check critical anti-hallucination settings
    if os.getenv('WHISPERX_CONDITION_ON_PREVIOUS', 'false').lower() == 'true':
        issues.append("WARNING: condition_on_previous=true may cause hallucinations")

    logprob = float(os.getenv('WHISPERX_LOGPROB_THRESHOLD', -1.0))
    if logprob < -0.8:
        issues.append(f"WARNING: logprob_threshold={logprob} too permissive (recommend -0.7)")

    no_speech = float(os.getenv('WHISPERX_NO_SPEECH_THRESHOLD', 0.6))
    if no_speech < 0.6:
        issues.append(f"WARNING: no_speech_threshold={no_speech} too low (recommend 0.65)")

    if issues:
        logger.warning("Configuration validation issues:")
        for issue in issues:
            logger.warning(f"  - {issue}")

    return len(issues) == 0

# Add to pipeline initialization
```

---

### Phase 1 Deliverables

- ✅ Updated `config/.env.pipeline` with optimized parameters
- ✅ Confidence filtering in `whisperx_integration.py`
- ✅ Configuration validation in `config/config.py`
- ✅ Test results showing improvement metrics
- ✅ Documentation of parameter changes

### Phase 1 Success Criteria

- [ ] 20-30% reduction in total subtitle segments
- [ ] 30-50% reduction in empty/hallucinated segments
- [ ] No regression in dialogue accuracy
- [ ] Processing time reduced by 15-25%

---

## Phase 2: Hallucination Prevention (Days 4-7)

### Objective
Enhance hallucination detection to eliminate repetitive patterns and common false positives.

### Tasks

#### 2.1 Enhance Hallucination Detection Patterns
**File:** `scripts/hallucination_removal.py`
**Effort:** 3-4 hours
**Impact:** 🟢 High (70-80% of remaining hallucinations)

**Implementation:**

```python
class EnhancedHallucinationRemover:
    """Enhanced hallucination detection with multiple strategies"""

    # Common hallucination patterns (case-insensitive)
    COMMON_PATTERNS = [
        r'^thank you\.?$',
        r'^thanks\.?$',
        r"^what did you do\??$",
        r"^i'?m sorry\.?$",
        r'^sorry\.?$',
        r'^(uh|um|ah|eh)\.?$',
        r'^subscribe',
        r'^please subscribe',
        r'^like and subscribe',
        r'^click the bell',
        r'^thank you for watching',
    ]

    # Very short segments (likely noise)
    MIN_TEXT_LENGTH = 3

    # Repetition detection
    MAX_CONSECUTIVE_REPEATS = 2

    def __init__(self, config=None):
        self.config = config or {}
        self.patterns = [re.compile(p, re.IGNORECASE) for p in self.COMMON_PATTERNS]
        self.stats = {
            'total_segments': 0,
            'removed_by_pattern': 0,
            'removed_by_length': 0,
            'removed_by_repetition': 0,
        }

    def is_hallucination_pattern(self, text):
        """Check if text matches known hallucination patterns"""
        text_clean = text.strip().lower()
        for pattern in self.patterns:
            if pattern.match(text_clean):
                return True
        return False

    def is_too_short(self, text):
        """Check if text is suspiciously short"""
        clean_text = re.sub(r'[^\w\s]', '', text).strip()
        return len(clean_text) < self.MIN_TEXT_LENGTH

    def remove_sequential_duplicates(self, segments):
        """Remove segments that repeat more than MAX_CONSECUTIVE_REPEATS times"""
        if not segments:
            return segments

        result = []
        repeat_count = 1
        last_text = None

        for seg in segments:
            text = seg.get('text', '').strip().lower()

            # Empty text - skip
            if not text:
                continue

            # Same as previous
            if text == last_text:
                repeat_count += 1
                if repeat_count <= self.MAX_CONSECUTIVE_REPEATS:
                    result.append(seg)
                else:
                    self.stats['removed_by_repetition'] += 1
            else:
                repeat_count = 1
                result.append(seg)
                last_text = text

        return result

    def remove_hallucinations(self, segments):
        """
        Main removal pipeline - applies all detection strategies.

        Args:
            segments: List of segments with 'text' field

        Returns:
            Filtered segments list + statistics
        """
        if not segments:
            return segments, self.stats

        self.stats['total_segments'] = len(segments)
        filtered = []

        # Step 1: Remove known patterns
        for seg in segments:
            text = seg.get('text', '').strip()

            if self.is_hallucination_pattern(text):
                self.stats['removed_by_pattern'] += 1
                continue

            if self.is_too_short(text):
                self.stats['removed_by_length'] += 1
                continue

            filtered.append(seg)

        # Step 2: Remove sequential duplicates
        filtered = self.remove_sequential_duplicates(filtered)

        # Log statistics
        removed = self.stats['total_segments'] - len(filtered)
        logger.info(f"Hallucination removal: {removed}/{self.stats['total_segments']} segments removed")
        logger.info(f"  - By pattern: {self.stats['removed_by_pattern']}")
        logger.info(f"  - By length: {self.stats['removed_by_length']}")
        logger.info(f"  - By repetition: {self.stats['removed_by_repetition']}")

        return filtered, self.stats
```

**Integration points:**
1. After ASR stage: `scripts/whisperx_integration.py`
2. Before subtitle generation: `scripts/subtitle_gen.py`

---

#### 2.2 Add Compression Ratio Analysis
**File:** `scripts/hallucination_removal.py`
**Effort:** 2 hours
**Impact:** 🟡 Medium (catches repetitive hallucinations)

**Implementation:**

```python
def calculate_compression_ratio(text):
    """
    Calculate compression ratio to detect repetitive text.
    High ratio = likely hallucination/repetition.
    """
    import zlib

    if not text:
        return 0

    # Compress the text
    compressed = zlib.compress(text.encode('utf-8'))
    ratio = len(text) / len(compressed) if len(compressed) > 0 else 0

    return ratio

def filter_by_compression_ratio(segments, max_ratio=2.2):
    """Remove segments with high compression ratio (repetitive)"""
    filtered = []
    removed = 0

    for seg in segments:
        text = seg.get('text', '')
        ratio = calculate_compression_ratio(text)

        if ratio > max_ratio:
            removed += 1
            logger.debug(f"Removed repetitive segment (ratio={ratio:.2f}): {text[:50]}")
            continue

        filtered.append(seg)

    logger.info(f"Compression filtering: Removed {removed}/{len(segments)} segments")
    return filtered

# Add to EnhancedHallucinationRemover.remove_hallucinations()
```

---

#### 2.3 Create Hallucination Test Suite
**File:** `tests/test_hallucination_removal.py`
**Effort:** 2-3 hours
**Impact:** 🟡 Medium (prevents regressions)

**Implementation:**

```python
import unittest
from scripts.hallucination_removal import EnhancedHallucinationRemover

class TestHallucinationRemoval(unittest.TestCase):

    def setUp(self):
        self.remover = EnhancedHallucinationRemover()

    def test_common_patterns(self):
        """Test removal of common hallucination patterns"""
        segments = [
            {'text': 'Thank you.', 'start': 0, 'end': 1},
            {'text': 'Real dialogue here', 'start': 1, 'end': 2},
            {'text': 'Subscribe', 'start': 2, 'end': 3},
            {'text': 'More real content', 'start': 3, 'end': 4},
        ]

        filtered, stats = self.remover.remove_hallucinations(segments)

        self.assertEqual(len(filtered), 2)
        self.assertEqual(stats['removed_by_pattern'], 2)

    def test_sequential_duplicates(self):
        """Test removal of repetitive segments"""
        segments = [
            {'text': 'Hello', 'start': 0, 'end': 1},
            {'text': 'Thank you', 'start': 1, 'end': 2},
            {'text': 'Thank you', 'start': 2, 'end': 3},
            {'text': 'Thank you', 'start': 3, 'end': 4},  # 3rd repeat - should be removed
            {'text': 'Thank you', 'start': 4, 'end': 5},  # 4th repeat - should be removed
            {'text': 'Goodbye', 'start': 5, 'end': 6},
        ]

        filtered, stats = self.remover.remove_hallucinations(segments)

        # Should keep first 2 "Thank you", remove rest
        self.assertLessEqual(len(filtered), 4)
        self.assertGreater(stats['removed_by_repetition'], 0)

    def test_short_segments(self):
        """Test removal of suspiciously short segments"""
        segments = [
            {'text': 'A', 'start': 0, 'end': 1},
            {'text': 'Um', 'start': 1, 'end': 2},
            {'text': 'This is real dialogue', 'start': 2, 'end': 3},
        ]

        filtered, stats = self.remover.remove_hallucinations(segments)

        self.assertEqual(len(filtered), 1)
        self.assertGreater(stats['removed_by_length'], 0)

    def test_no_false_positives(self):
        """Ensure legitimate content is not removed"""
        segments = [
            {'text': 'Character says thank you very much', 'start': 0, 'end': 1},
            {'text': 'Please help me with this', 'start': 1, 'end': 2},
            {'text': 'I need to subscribe to the newsletter', 'start': 2, 'end': 3},
        ]

        filtered, stats = self.remover.remove_hallucinations(segments)

        # These should NOT be removed (pattern is part of longer sentence)
        self.assertEqual(len(filtered), 3)

if __name__ == '__main__':
    unittest.main()
```

**Run tests:**
```bash
python -m pytest tests/test_hallucination_removal.py -v
```

---

### Phase 2 Deliverables

- ✅ Enhanced `hallucination_removal.py` with new detection strategies
- ✅ Integration into ASR and subtitle generation stages
- ✅ Comprehensive test suite with 10+ test cases
- ✅ Performance metrics showing reduction in hallucinations
- ✅ Updated documentation

### Phase 2 Success Criteria

- [ ] 70-80% reduction in hallucinated segments
- [ ] Zero false positives on test dataset
- [ ] No legitimate dialogue removed
- [ ] Test coverage > 90% for hallucination module

---

## Phase 3: Readability Improvements (Days 8-12)

### Objective
Merge short segments and optimize subtitle display timing for better readability.

### Tasks

#### 3.1 Implement Segment Merging
**File:** `scripts/subtitle_gen.py`
**Location:** Before SRT writing (~line 150)
**Effort:** 4-5 hours
**Impact:** 🟢 High (50% fewer segments, better UX)

**Implementation:**

```python
class SubtitleSegmentMerger:
    """
    Merge short subtitle segments for optimal readability.

    Reading speed guidelines:
    - Comfortable: 17-20 characters/second
    - Fast: 21-25 characters/second
    - Too fast: >25 characters/second
    """

    def __init__(self, config=None):
        self.config = config or {}

        # Merging parameters
        self.max_gap = self.config.get('max_gap_seconds', 1.5)
        self.max_chars = self.config.get('max_chars_per_subtitle', 84)  # 2 lines × 42 chars
        self.min_duration = self.config.get('min_display_duration', 1.0)  # seconds
        self.max_duration = self.config.get('max_display_duration', 7.0)  # seconds
        self.chars_per_second = self.config.get('chars_per_second', 20)  # reading speed

    def calculate_optimal_duration(self, text):
        """Calculate optimal display duration based on reading speed"""
        char_count = len(text)
        optimal = char_count / self.chars_per_second
        return max(self.min_duration, min(optimal, self.max_duration))

    def should_merge(self, seg1, seg2):
        """
        Determine if two segments should be merged.

        Criteria:
        1. Gap between segments is small (< max_gap)
        2. Combined text fits within max_chars
        3. Both are dialogue (not lyrics)
        4. Combined duration is reasonable
        """
        # Check gap
        gap = seg2['start'] - seg1['end']
        if gap > self.max_gap:
            return False

        # Check if either is lyrics (don't merge lyrics)
        if seg1.get('is_lyrics') or seg2.get('is_lyrics'):
            return False

        # Check combined length
        combined_text = seg1['text'] + ' ' + seg2['text']
        if len(combined_text) > self.max_chars:
            return False

        # Check combined duration
        duration = seg2['end'] - seg1['start']
        if duration > self.max_duration:
            return False

        return True

    def merge_segments(self, segments):
        """
        Merge segments according to readability rules.

        Args:
            segments: List of segments with start, end, text fields

        Returns:
            Merged segments list + statistics
        """
        if not segments:
            return segments, {}

        merged = []
        buffer = None
        stats = {
            'original_count': len(segments),
            'merged_count': 0,
            'final_count': 0,
        }

        for seg in segments:
            # Initialize buffer
            if buffer is None:
                buffer = seg.copy()
                continue

            # Try to merge
            if self.should_merge(buffer, seg):
                # Merge into buffer
                buffer['end'] = seg['end']
                buffer['text'] = buffer['text'].strip() + ' ' + seg['text'].strip()

                # Update confidence (average)
                if 'avg_logprob' in buffer and 'avg_logprob' in seg:
                    buffer['avg_logprob'] = (buffer['avg_logprob'] + seg['avg_logprob']) / 2

                stats['merged_count'] += 1
            else:
                # Cannot merge - flush buffer
                merged.append(buffer)
                buffer = seg.copy()

        # Flush final buffer
        if buffer:
            merged.append(buffer)

        stats['final_count'] = len(merged)
        reduction = ((stats['original_count'] - stats['final_count']) /
                     stats['original_count'] * 100)

        logger.info(f"Segment merging: {stats['original_count']} → {stats['final_count']} "
                   f"({reduction:.1f}% reduction)")

        return merged, stats

    def adjust_timing(self, segments):
        """
        Adjust segment timing for optimal reading speed.

        Ensures:
        - Minimum display time for readability
        - No overlapping segments
        - Optimal reading pace
        """
        adjusted = []

        for i, seg in enumerate(segments):
            seg_copy = seg.copy()

            # Calculate optimal duration
            optimal_duration = self.calculate_optimal_duration(seg['text'])
            current_duration = seg['end'] - seg['start']

            # If too short, extend end time (if possible)
            if current_duration < optimal_duration:
                # Check if we can extend without overlapping next segment
                if i < len(segments) - 1:
                    next_start = segments[i + 1]['start']
                    max_end = next_start - 0.1  # 100ms gap
                    seg_copy['end'] = min(seg['start'] + optimal_duration, max_end)
                else:
                    # Last segment - can extend freely
                    seg_copy['end'] = seg['start'] + optimal_duration

            adjusted.append(seg_copy)

        return adjusted
```

**Integration:**

```python
# In subtitle_gen.py main function, before writing SRT:

# Load segments
segments = load_segments(...)

# Apply hallucination removal
from hallucination_removal import EnhancedHallucinationRemover
remover = EnhancedHallucinationRemover()
segments, halluc_stats = remover.remove_hallucinations(segments)

# Merge segments for readability
merger = SubtitleSegmentMerger(config={
    'max_gap_seconds': 1.5,
    'max_chars_per_subtitle': 84,
    'min_display_duration': 1.0,
    'max_display_duration': 7.0,
    'chars_per_second': 20,
})

segments, merge_stats = merger.merge_segments(segments)
segments = merger.adjust_timing(segments)

# Continue with SRT writing...
```

---

#### 3.2 Add Subtitle Reading Speed Validation
**File:** `scripts/metrics/quality_analyzer.py`
**Effort:** 2 hours
**Impact:** 🟡 Medium (quality metrics)

**Implementation:**

```python
def analyze_reading_speed(segments):
    """
    Analyze subtitle reading speed and flag issues.

    Returns:
        {
            'avg_chars_per_second': float,
            'too_fast_count': int,  # >25 cps
            'too_slow_count': int,  # <10 cps
            'optimal_count': int,   # 17-20 cps
        }
    """
    stats = {
        'avg_chars_per_second': 0,
        'too_fast_count': 0,
        'too_slow_count': 0,
        'optimal_count': 0,
        'segments_analyzed': len(segments),
    }

    total_cps = 0

    for seg in segments:
        duration = seg['end'] - seg['start']
        if duration <= 0:
            continue

        chars = len(seg['text'])
        cps = chars / duration
        total_cps += cps

        if cps > 25:
            stats['too_fast_count'] += 1
        elif cps < 10:
            stats['too_slow_count'] += 1
        elif 17 <= cps <= 20:
            stats['optimal_count'] += 1

    if len(segments) > 0:
        stats['avg_chars_per_second'] = total_cps / len(segments)

    return stats
```

---

#### 3.3 Implement Line Breaking for Long Subtitles
**File:** `scripts/subtitle_gen.py`
**Effort:** 2-3 hours
**Impact:** 🟡 Medium (visual formatting)

**Implementation:**

```python
def format_subtitle_lines(text, max_line_length=42):
    """
    Break subtitle text into 2 lines for better readability.

    Rules:
    1. Try to break at natural boundaries (punctuation, conjunctions)
    2. Keep lines balanced (similar length)
    3. Max 2 lines per subtitle
    """
    if len(text) <= max_line_length:
        return text

    # Try to find good break point
    break_chars = ['. ', ', ', '; ', ' and ', ' but ', ' or ', ' - ']

    # Find break point closest to middle
    mid = len(text) // 2
    best_break = -1
    best_distance = float('inf')

    for break_char in break_chars:
        idx = text.find(break_char, mid - 20, mid + 20)
        if idx > 0:
            distance = abs(idx - mid)
            if distance < best_distance:
                best_distance = distance
                best_break = idx + len(break_char)

    # If no good break found, break at word boundary
    if best_break < 0:
        words = text.split()
        line1_words = []
        line2_words = []
        current_len = 0

        for word in words:
            if current_len + len(word) <= max_line_length:
                line1_words.append(word)
                current_len += len(word) + 1
            else:
                line2_words.append(word)

        return '\n'.join([
            ' '.join(line1_words),
            ' '.join(line2_words)
        ]) if line2_words else text

    # Break at found position
    line1 = text[:best_break].strip()
    line2 = text[best_break:].strip()

    return f"{line1}\n{line2}"
```

---

### Phase 3 Deliverables

- ✅ `SubtitleSegmentMerger` class in `subtitle_gen.py`
- ✅ Reading speed analysis in `quality_analyzer.py`
- ✅ Line breaking formatter
- ✅ Updated configuration options
- ✅ Before/after comparison metrics

### Phase 3 Success Criteria

- [ ] 40-60% reduction in total subtitle count
- [ ] 90%+ of subtitles at optimal reading speed (17-20 cps)
- [ ] <5% of subtitles too fast (>25 cps)
- [ ] Improved user readability scores

---

## Phase 4: Advanced Features (Days 13-19)

### Objective
Apply glossary earlier in pipeline and add advanced validation features.

### Tasks

#### 4.1 Pre-Translation Glossary Protection
**File:** `scripts/translate.py`
**Effort:** 5-6 hours
**Impact:** 🟢 High (15-20% proper noun accuracy)

**Implementation:**

```python
class GlossaryProtectedTranslator:
    """
    Translator that protects glossary terms during translation.

    Strategy:
    1. Extract proper nouns from glossary
    2. Replace with placeholders before translation
    3. Restore original terms after translation
    """

    def __init__(self, glossary, base_translator):
        self.glossary = glossary
        self.translator = base_translator
        self.placeholder_pattern = "__TERM_{:04d}__"

    def extract_proper_nouns(self):
        """Get list of proper nouns to protect"""
        if hasattr(self.glossary, 'get_proper_nouns'):
            return self.glossary.get_proper_nouns()

        # Fallback: extract from glossary entries
        proper_nouns = []
        for entry in self.glossary.entries:
            if entry.get('type') in ['name', 'place', 'title']:
                proper_nouns.append(entry['source'])

        return proper_nouns

    def protect_terms(self, text):
        """
        Replace glossary terms with placeholders.

        Returns:
            protected_text, term_map
        """
        term_map = {}
        protected = text
        proper_nouns = self.extract_proper_nouns()

        # Sort by length (longest first) to avoid partial matches
        proper_nouns.sort(key=len, reverse=True)

        for i, term in enumerate(proper_nouns):
            if term.lower() in protected.lower():
                placeholder = self.placeholder_pattern.format(i)
                term_map[placeholder] = term

                # Case-insensitive replace
                pattern = re.compile(re.escape(term), re.IGNORECASE)
                protected = pattern.sub(placeholder, protected)

        return protected, term_map

    def restore_terms(self, text, term_map):
        """Restore original terms from placeholders"""
        restored = text

        for placeholder, original_term in term_map.items():
            restored = restored.replace(placeholder, original_term)

        return restored

    def translate(self, text, src_lang, tgt_lang):
        """
        Translate with glossary protection.

        Args:
            text: Source text
            src_lang: Source language code
            tgt_lang: Target language code

        Returns:
            Translated text with glossary terms preserved
        """
        # Step 1: Protect terms
        protected_text, term_map = self.protect_terms(text)

        logger.debug(f"Protected {len(term_map)} terms: {list(term_map.values())}")

        # Step 2: Translate
        translated = self.translator.translate(protected_text, src_lang, tgt_lang)

        # Step 3: Restore terms
        final = self.restore_terms(translated, term_map)

        return final

    def translate_batch(self, texts, src_lang, tgt_lang):
        """Batch translation with glossary protection"""
        results = []

        for text in texts:
            result = self.translate(text, src_lang, tgt_lang)
            results.append(result)

        return results


# Integration in translate.py:

def create_translator(config, glossary=None):
    """Factory function to create appropriate translator"""

    # Create base translator (IndicTrans2, etc.)
    base_translator = IndicTrans2Translator(config)

    # Wrap with glossary protection if available
    if glossary and config.get('use_glossary_protection', True):
        return GlossaryProtectedTranslator(glossary, base_translator)

    return base_translator
```

**Configuration:**
```bash
# In .env.pipeline
TRANSLATION_GLOSSARY_PROTECTION=true
```

---

#### 4.2 Post-Translation Validation
**File:** `scripts/translate.py`
**Effort:** 3-4 hours
**Impact:** 🟡 Medium (catches translation errors)

**Implementation:**

```python
class TranslationValidator:
    """Validate translation quality and glossary compliance"""

    def __init__(self, glossary):
        self.glossary = glossary

    def validate_glossary_compliance(self, source_text, translated_text):
        """
        Check if required glossary terms are preserved.

        Returns:
            {
                'compliant': bool,
                'missing_terms': list,
                'confidence': float
            }
        """
        result = {
            'compliant': True,
            'missing_terms': [],
            'confidence': 1.0
        }

        if not self.glossary:
            return result

        # Get terms that should appear in translation
        required_terms = self.glossary.find_terms_in_text(source_text)

        for term in required_terms:
            # Check if term or its translation appears
            term_lower = term.lower()
            translated_lower = translated_text.lower()

            # Get expected translation from glossary
            expected = self.glossary.get_translation(term)

            if expected:
                if expected.lower() not in translated_lower and term_lower not in translated_lower:
                    result['missing_terms'].append(term)
                    result['compliant'] = False

        # Calculate confidence
        if required_terms:
            result['confidence'] = 1.0 - (len(result['missing_terms']) / len(required_terms))

        return result

    def validate_length_ratio(self, source_text, translated_text, max_ratio=3.0):
        """
        Check if translation length is reasonable.
        Very long translations may indicate errors.
        """
        src_len = len(source_text)
        tgt_len = len(translated_text)

        if src_len == 0:
            return True

        ratio = tgt_len / src_len
        return ratio <= max_ratio

    def validate_batch(self, source_segments, translated_segments):
        """Validate entire batch of translations"""
        stats = {
            'total': len(source_segments),
            'compliant': 0,
            'length_issues': 0,
            'avg_confidence': 0.0
        }

        total_confidence = 0

        for src, tgt in zip(source_segments, translated_segments):
            # Glossary compliance
            compliance = self.validate_glossary_compliance(src['text'], tgt['text'])
            if compliance['compliant']:
                stats['compliant'] += 1
            total_confidence += compliance['confidence']

            # Length check
            if not self.validate_length_ratio(src['text'], tgt['text']):
                stats['length_issues'] += 1
                logger.warning(f"Length ratio issue: '{src['text'][:50]}...'")

        stats['avg_confidence'] = total_confidence / len(source_segments) if source_segments else 0

        logger.info(f"Translation validation: {stats['compliant']}/{stats['total']} compliant "
                   f"(avg confidence: {stats['avg_confidence']:.2%})")

        return stats
```

---

#### 4.3 Add Glossary Learning from High-Confidence Segments
**File:** `scripts/glossary_learner.py` (new)
**Effort:** 4-5 hours
**Impact:** 🟡 Medium (improves glossary over time)

**Implementation:**

```python
class GlossaryLearner:
    """
    Learn new glossary terms from high-confidence transcriptions.

    Strategy:
    1. Identify proper nouns (capitalized words)
    2. Filter by confidence threshold
    3. Track frequency across multiple runs
    4. Suggest additions to glossary
    """

    def __init__(self, min_confidence=0.9, min_frequency=3):
        self.min_confidence = min_confidence
        self.min_frequency = min_frequency
        self.candidates = {}  # term -> count

    def extract_proper_nouns(self, text):
        """Extract capitalized words (likely proper nouns)"""
        # Simple heuristic: words that are consistently capitalized
        words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        return words

    def process_segment(self, segment):
        """Process a segment and extract candidate terms"""
        # Check confidence
        confidence = segment.get('avg_logprob', 0)
        if confidence < self.min_confidence:
            return

        # Extract proper nouns
        text = segment.get('text', '')
        nouns = self.extract_proper_nouns(text)

        for noun in nouns:
            if noun not in self.candidates:
                self.candidates[noun] = {
                    'count': 0,
                    'contexts': [],
                    'avg_confidence': 0
                }

            self.candidates[noun]['count'] += 1
            self.candidates[noun]['contexts'].append(text)
            # Update avg confidence
            old_conf = self.candidates[noun]['avg_confidence']
            old_count = self.candidates[noun]['count'] - 1
            new_conf = (old_conf * old_count + confidence) / self.candidates[noun]['count']
            self.candidates[noun]['avg_confidence'] = new_conf

    def get_suggestions(self):
        """Get suggested terms for glossary"""
        suggestions = []

        for term, data in self.candidates.items():
            if data['count'] >= self.min_frequency:
                suggestions.append({
                    'term': term,
                    'frequency': data['count'],
                    'confidence': data['avg_confidence'],
                    'sample_contexts': data['contexts'][:3]
                })

        # Sort by frequency × confidence
        suggestions.sort(key=lambda x: x['frequency'] * x['confidence'], reverse=True)

        return suggestions

    def export_to_tsv(self, output_path):
        """Export suggestions to TSV format for manual review"""
        suggestions = self.get_suggestions()

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("term\tfrequency\tconfidence\tsample_context\n")
            for s in suggestions:
                context = s['sample_contexts'][0] if s['sample_contexts'] else ''
                f.write(f"{s['term']}\t{s['frequency']}\t{s['confidence']:.3f}\t{context}\n")

        logger.info(f"Exported {len(suggestions)} glossary suggestions to {output_path}")

# Integration in pipeline:
# After ASR stage, run glossary learner and save suggestions
```

---

### Phase 4 Deliverables

- ✅ `GlossaryProtectedTranslator` in `translate.py`
- ✅ `TranslationValidator` for quality checks
- ✅ `GlossaryLearner` for automatic term discovery
- ✅ Integration with existing pipeline
- ✅ Configuration options for all features

### Phase 4 Success Criteria

- [ ] 15-20% improvement in proper noun preservation
- [ ] <5% glossary term loss in translation
- [ ] Automated glossary suggestions from high-confidence runs
- [ ] Validation metrics in manifest.json

---

## Phase 5: Testing & Validation (Days 20-22)

### Objective
Comprehensive testing framework and quality validation.

### Tasks

#### 5.1 Create Comprehensive Test Suite
**File:** `tests/test_subtitle_accuracy.py`
**Effort:** 4-5 hours
**Impact:** 🟢 High (prevents regressions)

**Implementation:**

```python
import unittest
import json
from pathlib import Path

class TestSubtitleAccuracy(unittest.TestCase):
    """Comprehensive subtitle accuracy tests"""

    @classmethod
    def setUpClass(cls):
        """Run pipeline on test dataset"""
        cls.test_data_dir = Path('test-data')
        cls.results_dir = Path('test-results')

        # Run test pipeline (assumes test data exists)
        import subprocess
        subprocess.run([
            './test-glossary-quickstart.sh'
        ], check=True)

    def test_hallucination_reduction(self):
        """Test that hallucinations are significantly reduced"""
        baseline_srt = self.results_dir / 'baseline' / '1' / 'subtitles' / 'test.en.srt'
        improved_srt = self.results_dir / 'glossary' / '1' / 'subtitles' / 'test.en.srt'

        baseline_count = self.count_subtitle_entries(baseline_srt)
        improved_count = self.count_subtitle_entries(improved_srt)

        reduction_pct = (baseline_count - improved_count) / baseline_count * 100

        # Should see 30-50% reduction
        self.assertGreaterEqual(reduction_pct, 30,
                               "Hallucination reduction below 30%")

    def test_no_empty_segments(self):
        """Test that no empty segments exist"""
        srt_file = self.results_dir / 'glossary' / '1' / 'subtitles' / 'test.en.srt'
        segments = self.parse_srt(srt_file)

        empty_count = sum(1 for seg in segments if not seg['text'].strip())

        self.assertEqual(empty_count, 0,
                        f"Found {empty_count} empty subtitle segments")

    def test_no_zero_duration_segments(self):
        """Test that all segments have positive duration"""
        srt_file = self.results_dir / 'glossary' / '1' / 'subtitles' / 'test.en.srt'
        segments = self.parse_srt(srt_file)

        zero_duration = [seg for seg in segments
                        if seg['start'] == seg['end']]

        self.assertEqual(len(zero_duration), 0,
                        f"Found {len(zero_duration)} zero-duration segments")

    def test_reading_speed(self):
        """Test that reading speed is optimal"""
        srt_file = self.results_dir / 'glossary' / '1' / 'subtitles' / 'test.en.srt'
        segments = self.parse_srt(srt_file)

        too_fast = 0
        optimal = 0

        for seg in segments:
            duration = seg['end'] - seg['start']
            if duration <= 0:
                continue

            cps = len(seg['text']) / duration

            if cps > 25:
                too_fast += 1
            elif 17 <= cps <= 20:
                optimal += 1

        # At least 50% should be optimal speed
        optimal_pct = optimal / len(segments) * 100
        too_fast_pct = too_fast / len(segments) * 100

        self.assertGreaterEqual(optimal_pct, 50,
                               f"Only {optimal_pct:.1f}% at optimal speed")
        self.assertLessEqual(too_fast_pct, 5,
                            f"{too_fast_pct:.1f}% too fast")

    def test_glossary_preservation(self):
        """Test that glossary terms are preserved"""
        manifest = self.results_dir / 'glossary' / '1' / '11_subtitle_generation' / 'manifest.json'

        with open(manifest) as f:
            data = json.load(f)

        # Check for glossary application
        self.assertTrue(data.get('config', {}).get('glossary_enabled'),
                       "Glossary should be enabled")

        # Could add more specific term checking here

    # Helper methods

    def count_subtitle_entries(self, srt_file):
        """Count number of subtitle entries in SRT file"""
        segments = self.parse_srt(srt_file)
        return len(segments)

    def parse_srt(self, srt_file):
        """Parse SRT file into segments"""
        segments = []

        with open(srt_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Split by double newline
        entries = content.strip().split('\n\n')

        for entry in entries:
            lines = entry.split('\n')
            if len(lines) < 3:
                continue

            # Parse timestamp
            timestamp_line = lines[1]
            start_str, end_str = timestamp_line.split(' --> ')

            start = self.parse_timestamp(start_str)
            end = self.parse_timestamp(end_str)

            # Text is remaining lines
            text = '\n'.join(lines[2:])

            segments.append({
                'start': start,
                'end': end,
                'text': text
            })

        return segments

    def parse_timestamp(self, ts_str):
        """Parse SRT timestamp to seconds"""
        # Format: HH:MM:SS,mmm
        h, m, s = ts_str.replace(',', '.').split(':')
        return int(h) * 3600 + int(m) * 60 + float(s)

if __name__ == '__main__':
    unittest.main()
```

---

#### 5.2 Create Accuracy Benchmarking Script
**File:** `scripts/benchmark_accuracy.py`
**Effort:** 3-4 hours
**Impact:** 🟡 Medium (quantifiable metrics)

**Implementation:**

```python
#!/usr/bin/env python3
"""
Benchmark subtitle accuracy across different configurations.

Usage:
    python scripts/benchmark_accuracy.py --input test-data/ --output benchmark-results.json
"""

import argparse
import json
import subprocess
from pathlib import Path
import time

class AccuracyBenchmark:
    """Run accuracy benchmarks on subtitle generation"""

    def __init__(self, input_dir, output_file):
        self.input_dir = Path(input_dir)
        self.output_file = output_file
        self.results = []

    def run_configuration(self, config_name, env_overrides):
        """Run pipeline with specific configuration"""
        print(f"\n{'='*60}")
        print(f"Running configuration: {config_name}")
        print(f"{'='*60}\n")

        start_time = time.time()

        # Set environment variables
        env = os.environ.copy()
        env.update(env_overrides)

        # Run pipeline
        result = subprocess.run(
            ['./pipeline.sh', '--input', str(self.input_dir)],
            env=env,
            capture_output=True,
            text=True
        )

        elapsed = time.time() - start_time

        # Collect metrics
        metrics = self.collect_metrics(config_name)
        metrics['processing_time'] = elapsed
        metrics['success'] = result.returncode == 0

        self.results.append({
            'config': config_name,
            'env': env_overrides,
            'metrics': metrics
        })

        return metrics

    def collect_metrics(self, config_name):
        """Collect accuracy metrics from output"""
        # Parse manifest files
        manifest_dir = Path('out') / config_name / '11_subtitle_generation'
        manifest_file = manifest_dir / 'manifest.json'

        if not manifest_file.exists():
            return {}

        with open(manifest_file) as f:
            manifest = json.load(f)

        # Parse SRT file
        srt_file = manifest_dir.parent / 'subtitles' / 'output.en.srt'
        segments = self.parse_srt(srt_file) if srt_file.exists() else []

        # Calculate metrics
        metrics = {
            'total_segments': len(segments),
            'empty_segments': sum(1 for s in segments if not s['text'].strip()),
            'avg_confidence': manifest.get('metrics', {}).get('avg_confidence', 0),
            'hallucination_rate': self.calculate_hallucination_rate(segments),
            'avg_reading_speed': self.calculate_avg_reading_speed(segments),
        }

        return metrics

    def calculate_hallucination_rate(self, segments):
        """Estimate hallucination rate"""
        # Simple heuristic: repetitive "thank you", short segments
        hallucinations = 0

        for seg in segments:
            text = seg['text'].lower().strip()
            if text in ['thank you', 'thank you.', 'thanks']:
                hallucinations += 1

        return hallucinations / len(segments) if segments else 0

    def calculate_avg_reading_speed(self, segments):
        """Calculate average reading speed (chars/second)"""
        total_cps = 0
        count = 0

        for seg in segments:
            duration = seg['end'] - seg['start']
            if duration > 0:
                cps = len(seg['text']) / duration
                total_cps += cps
                count += 1

        return total_cps / count if count > 0 else 0

    def parse_srt(self, srt_file):
        """Parse SRT file (reuse from test suite)"""
        # ... (same as in test suite)
        pass

    def run_all_benchmarks(self):
        """Run all configuration benchmarks"""

        configs = [
            {
                'name': 'baseline',
                'env': {
                    'TMDB_ENRICHMENT_ENABLED': 'false',
                    'GLOSSARY_CACHE_ENABLED': 'false',
                }
            },
            {
                'name': 'glossary-only',
                'env': {
                    'TMDB_ENRICHMENT_ENABLED': 'false',
                    'GLOSSARY_CACHE_ENABLED': 'true',
                }
            },
            {
                'name': 'full-pipeline',
                'env': {
                    'TMDB_ENRICHMENT_ENABLED': 'true',
                    'GLOSSARY_CACHE_ENABLED': 'true',
                }
            },
        ]

        for config in configs:
            self.run_configuration(config['name'], config['env'])

        # Save results
        with open(self.output_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        # Print comparison
        self.print_comparison()

    def print_comparison(self):
        """Print benchmark comparison table"""
        print(f"\n{'='*80}")
        print("BENCHMARK RESULTS")
        print(f"{'='*80}\n")

        print(f"{'Config':<20} {'Segments':<12} {'Empty':<10} {'Halluc%':<12} {'Speed(cps)':<12} {'Time(s)':<10}")
        print(f"{'-'*80}")

        for result in self.results:
            config = result['config']
            m = result['metrics']

            print(f"{config:<20} "
                  f"{m.get('total_segments', 0):<12} "
                  f"{m.get('empty_segments', 0):<10} "
                  f"{m.get('hallucination_rate', 0)*100:>10.1f}% "
                  f"{m.get('avg_reading_speed', 0):>11.1f} "
                  f"{m.get('processing_time', 0):>9.1f}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, help='Input test data directory')
    parser.add_argument('--output', default='benchmark-results.json', help='Output file')

    args = parser.parse_args()

    benchmark = AccuracyBenchmark(args.input, args.output)
    benchmark.run_all_benchmarks()
```

---

#### 5.3 Update Documentation
**File:** `docs/SUBTITLE_ACCURACY.md` (new)
**Effort:** 2-3 hours
**Impact:** 🟡 Medium (knowledge transfer)

Create comprehensive documentation covering:
- All improvements implemented
- Configuration options
- Best practices
- Troubleshooting guide
- Performance tuning

---

### Phase 5 Deliverables

- ✅ Comprehensive test suite (`tests/test_subtitle_accuracy.py`)
- ✅ Benchmarking script (`scripts/benchmark_accuracy.py`)
- ✅ Updated documentation (`docs/SUBTITLE_ACCURACY.md`)
- ✅ CI/CD integration (optional)
- ✅ Performance baseline established

### Phase 5 Success Criteria

- [ ] All tests passing
- [ ] Benchmark shows 10-15% overall improvement
- [ ] Zero critical regressions
- [ ] Documentation complete and reviewed

---

## Implementation Schedule

### Week 1 (Days 1-5)
- **Mon-Tue:** Phase 1 (Quick Wins)
- **Wed-Fri:** Phase 2 (Hallucination Prevention)

### Week 2 (Days 6-10)
- **Mon-Wed:** Phase 3 (Readability)
- **Thu-Fri:** Phase 4 start (Glossary Protection)

### Week 3 (Days 11-15)
- **Mon-Wed:** Phase 4 completion
- **Thu-Fri:** Phase 5 start (Testing)

### Week 4 (Days 16-22)
- **Mon-Tue:** Phase 5 completion
- **Wed:** Buffer for issues
- **Thu-Fri:** Final validation and docs

---

## Success Metrics

### Overall Goals

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| Subtitle Accuracy | 85% | 95% | Manual review of 100 segments |
| Hallucination Rate | 15-20% | <5% | Automated detection |
| Empty Segments | 100+ per hour | 0 | Automated count |
| Reading Speed (Optimal %) | 40-50% | >90% | 17-20 cps |
| Processing Time | Baseline | -20% | Pipeline duration |
| Proper Noun Accuracy | 70-75% | 90-95% | Glossary term preservation |

### Per-Phase Metrics

**Phase 1:**
- ✅ 20-30% reduction in segments
- ✅ 30-50% reduction in hallucinations
- ✅ 15-25% speed improvement

**Phase 2:**
- ✅ 70-80% hallucination reduction
- ✅ Zero false positives

**Phase 3:**
- ✅ 40-60% segment count reduction
- ✅ 90%+ optimal reading speed

**Phase 4:**
- ✅ 15-20% proper noun improvement
- ✅ <5% glossary term loss

**Phase 5:**
- ✅ 100% test coverage
- ✅ Automated benchmarks
- ✅ Complete documentation

---

## Risk Management

### High-Risk Items

1. **MLX Backend Stability**
   - Risk: Float16 may cause instability
   - Mitigation: Keep float32, add extensive error handling
   - Fallback: Graceful degradation to WhisperX/CPU

2. **Glossary Integration Breaking Changes**
   - Risk: Changes to translation stage may break pipeline
   - Mitigation: Extensive testing, feature flags
   - Fallback: Keep original translator as backup

3. **Performance Regression**
   - Risk: Additional processing may slow pipeline
   - Mitigation: Benchmark each phase, optimize hotspots
   - Fallback: Make features optional via config

### Medium-Risk Items

1. **False Positive Hallucination Detection**
   - Risk: Legitimate dialogue removed
   - Mitigation: Comprehensive test suite, conservative thresholds
   - Fallback: Adjustable thresholds via config

2. **Segment Merging Edge Cases**
   - Risk: Merging inappropriate segments
   - Mitigation: Clear merging rules, extensive testing
   - Fallback: Disable merging via config

---

## Dependencies

### External
- WhisperX (stable - no changes needed)
- IndicTrans2 (stable - no changes needed)
- TMDB API (stable - existing integration)

### Internal
- `scripts/whisperx_integration.py` (Phase 1, 2)
- `scripts/hallucination_removal.py` (Phase 2)
- `scripts/subtitle_gen.py` (Phase 3)
- `scripts/translate.py` (Phase 4)
- `shared/glossary_manager.py` (Phase 4)

### Infrastructure
- Python 3.8+ (existing)
- Storage for test data (~5GB)
- CI/CD for automated testing (optional)

---

## Rollout Plan

### Development
1. Create feature branch: `feature/subtitle-accuracy-improvements`
2. Implement phases sequentially
3. Test after each phase
4. Document changes continuously

### Testing
1. Unit tests per phase
2. Integration tests across phases
3. Regression tests with existing content
4. User acceptance testing (manual review)

### Deployment
1. **Soft Launch:** Enable for 10% of jobs
2. **Monitor:** Track metrics for 1 week
3. **Expand:** Increase to 50% if metrics good
4. **Full Rollout:** 100% after 2 weeks of stability

### Rollback Plan
- Feature flags for each improvement
- Can disable individual features without code changes
- Keep old code in `_legacy` functions for emergency rollback

---

## Maintenance

### Ongoing Tasks
- Weekly review of glossary suggestions
- Monthly accuracy audits
- Quarterly parameter tuning
- Continuous test data expansion

### Monitoring
- Track accuracy metrics in manifest.json
- Alert on regression (>5% drop in accuracy)
- Dashboard for key metrics (optional)

---

## Contact & Support

**Project Lead:** [Your Name]
**Repository:** cp-whisperx-app
**Documentation:** `docs/SUBTITLE_ACCURACY.md`
**Issues:** GitHub Issues

---

## Appendix

### A. Configuration Reference

All configuration options for subtitle accuracy improvements:

```bash
# WhisperX Parameters
WHISPERX_MODEL=large-v3
WHISPERX_TEMPERATURE=0.0,0.2,0.4
WHISPERX_BEAM_SIZE=5
WHISPERX_BEST_OF=5
WHISPERX_CONDITION_ON_PREVIOUS=false
WHISPERX_NO_SPEECH_THRESHOLD=0.65
WHISPERX_LOGPROB_THRESHOLD=-0.7
WHISPERX_COMPRESSION_RATIO=2.2
WHISPERX_MIN_DURATION=0.1
BIAS_PROMPT_STRATEGY=hybrid

# Hallucination Detection
HALLUCINATION_REMOVAL_ENABLED=true
HALLUCINATION_MAX_CONSECUTIVE_REPEATS=2
HALLUCINATION_MIN_TEXT_LENGTH=3

# Segment Merging
SUBTITLE_MERGE_ENABLED=true
SUBTITLE_MAX_GAP_SECONDS=1.5
SUBTITLE_MAX_CHARS_PER_SUBTITLE=84
SUBTITLE_MIN_DISPLAY_DURATION=1.0
SUBTITLE_MAX_DISPLAY_DURATION=7.0
SUBTITLE_CHARS_PER_SECOND=20

# Glossary Protection
TRANSLATION_GLOSSARY_PROTECTION=true
TRANSLATION_VALIDATE_OUTPUT=true

# Quality Metrics
QUALITY_ANALYSIS_ENABLED=true
QUALITY_MIN_CONFIDENCE_THRESHOLD=0.7
```

### B. File Modification Summary

| File | Lines Changed | Phase | Priority |
|------|---------------|-------|----------|
| `config/.env.pipeline` | ~20 | 1 | High |
| `scripts/whisperx_integration.py` | ~100 | 1,2 | High |
| `scripts/hallucination_removal.py` | ~300 | 2 | High |
| `scripts/subtitle_gen.py` | ~400 | 3 | High |
| `scripts/translate.py` | ~250 | 4 | Medium |
| `scripts/glossary_learner.py` | ~200 | 4 | Low |
| `tests/test_subtitle_accuracy.py` | ~300 | 5 | High |
| `scripts/benchmark_accuracy.py` | ~250 | 5 | Medium |

**Total Estimated Lines:** ~1,820 lines

### C. Testing Checklist

- [ ] Unit tests for hallucination detection
- [ ] Unit tests for segment merging
- [ ] Unit tests for glossary protection
- [ ] Integration test: baseline vs improved
- [ ] Regression test: existing content
- [ ] Performance test: processing time
- [ ] Edge case tests: empty inputs, very long/short segments
- [ ] Multi-language tests: Hindi, English, Hinglish
- [ ] User acceptance: manual quality review

---

**End of Roadmap**

*Last Updated: 2025-11-28*
*Version: 1.0*
