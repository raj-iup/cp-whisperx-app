# MLX Alignment & Beam Search Comparison Enhancement

## Overview

This enhancement addresses two key improvements to the CP-WhisperX-App pipeline:

1. **MLX Word-Level Alignment**: Adds actual word-level timestamp alignment for MLX backend transcripts
2. **Beam Search Comparison**: Tool for comparing translation quality across different beam widths (4-10)

## Problem Statement

### 1. Missing Word-Level Alignment for MLX

**Issue**: When using MLX-Whisper backend (Apple Silicon), transcripts lack word-level timestamps because:
- MLX-Whisper by default only provides segment-level timing
- The alignment stage was just a verification step, not performing actual alignment
- This impacts precision features like bias injection windows and karaoke subtitles

**Evidence**:
```bash
$ jq '.segments[0].words' out/2025/11/24/1/1/04_asr/segments.json
[]  # Empty - no word-level timing!
```

### 2. Translation Quality Optimization

**Issue**: Beam search width significantly impacts translation quality, but optimal value varies by content:
- Higher beams (8-10) = better quality but slower
- Lower beams (4-5) = faster but potentially lower quality
- No easy way to compare and determine optimal beam width

## Solution Components

### 1. MLX Alignment Module

**File**: `scripts/mlx_alignment.py`

Performs word-level alignment on MLX transcripts by re-transcribing with `word_timestamps=True`:

```python
import mlx_whisper

result = mlx_whisper.transcribe(
    audio_file,
    path_or_hf_repo="mlx-community/whisper-large-v3-mlx",
    word_timestamps=True,  # Enable word-level timing
    language="hi"
)
```

**Usage**:
```bash
# Standalone usage
python3 scripts/mlx_alignment.py \
    path/to/audio.wav \
    path/to/segments.json \
    path/to/output_aligned.json \
    --language hi \
    --model mlx-community/whisper-large-v3-mlx
```

**Features**:
- ✅ Detects if segments already have word timestamps (skips if present)
- ✅ Uses same anti-hallucination settings as ASR stage
- ✅ Verifies word timestamp quality after alignment
- ✅ Compatible with existing pipeline data format

### 2. Enhanced Alignment Stage

**File**: `scripts/run-pipeline.py` (modified)

The alignment stage now:
1. Checks if word-level timestamps exist
2. If missing and backend is MLX, performs actual alignment
3. Saves aligned segments to `05_alignment/segments_aligned.json`

**Before** (just verification):
```python
def _stage_alignment(self) -> bool:
    """Stage 5: Word-level alignment (already done by WhisperX)"""
    # Just verify segments exist
    self.logger.info(f"✓ Alignment verified: {len(segments)} segments")
    return True
```

**After** (actual alignment):
```python
def _stage_alignment(self) -> bool:
    """Stage 5: Word-level alignment"""
    if not has_word_timestamps:
        if backend == "mlx":
            return self._perform_mlx_alignment(...)
    # Creates 05_alignment/segments_aligned.json
```

**Output Example**:
```bash
05_alignment/
└── segments_aligned.json  # Segments with word-level timing
```

### 3. Beam Search Comparison Tool

**File**: `scripts/beam_search_comparison.py`

Generates multiple translations with different beam widths for quality comparison:

```bash
# Compare beam widths 4-10
./compare-beam-search.sh out/2025/11/24/1/1
```

**What It Does**:
1. Takes ASR output (`04_asr/segments.json`)
2. Translates with each beam width (4, 5, 6, 7, 8, 9, 10)
3. Generates interactive HTML report with side-by-side comparisons
4. Opens in browser for manual inspection

**Output Structure**:
```
{JOB_DIR}/beam_comparison/
├── segments_en_beam4.json   # Translation with beam=4
├── segments_en_beam5.json   # Translation with beam=5
├── segments_en_beam6.json   # Translation with beam=6
├── segments_en_beam7.json   # Translation with beam=7
├── segments_en_beam8.json   # Translation with beam=8
├── segments_en_beam9.json   # Translation with beam=9
├── segments_en_beam10.json  # Translation with beam=10
└── beam_comparison_report.html  # Interactive comparison
```

**HTML Report Features**:
- ✅ Summary statistics (time, segments for each beam width)
- ✅ Side-by-side segment comparison
- ✅ Quick navigation to specific segments
- ✅ Visual highlighting for easy quality inspection
- ✅ Responsive design for mobile/desktop

### 4. Convenience Wrapper Script

**File**: `compare-beam-search.sh`

Easy-to-use wrapper for beam comparison:

```bash
# Basic usage
./compare-beam-search.sh out/2025/11/24/1/1

# Custom beam range
./compare-beam-search.sh out/2025/11/24/1/1 --beam-range 5,8

# Use CPU instead of MPS
./compare-beam-search.sh out/2025/11/24/1/1 --device cpu

# Different languages
./compare-beam-search.sh out/2025/11/24/1/1 \
    --source-lang ta \
    --target-lang en
```

## Usage Examples

### Example 1: Re-align Existing Job

If you have an existing job without word-level timing:

```bash
# Check current state
jq '.segments[0].words | length' out/2025/11/24/1/1/04_asr/segments.json
# Output: 0 (no words)

# Re-run alignment stage only
# (Future: add stage re-run capability to pipeline)

# Or manually align
python3 scripts/mlx_alignment.py \
    out/2025/11/24/1/1/02_source_separation/audio.wav \
    out/2025/11/24/1/1/04_asr/segments.json \
    out/2025/11/24/1/1/05_alignment/segments_aligned.json \
    --language hi

# Verify
jq '.segments[0].words | length' out/2025/11/24/1/1/05_alignment/segments_aligned.json
# Output: 15 (has words!)
```

### Example 2: Find Optimal Beam Width

```bash
# Run comparison for existing job
./compare-beam-search.sh out/2025/11/24/1/1

# Output:
# ════════════════════════════════════════════════════════════════
#   BEAM SEARCH COMPARISON ANALYSIS
# ════════════════════════════════════════════════════════════════
# Job directory:    out/2025/11/24/1/1
# Translation:      hi → en
# Beam range:       4-10 (default)
# 
# ⏱️  Estimated time: ~10 minutes (7 beam widths × ~90s each)
#
# ▶ Beam width 4: Starting translation...
# ✓ Beam width 4: Completed in 87.3s (147 segments)
# ▶ Beam width 5: Starting translation...
# ✓ Beam width 5: Completed in 92.1s (147 segments)
# ...
# ✓ Comparison report generated: beam_comparison_report.html
# Opening report in browser...

# Review translations in browser
# Determine beam=7 gives best quality without excessive time
# Update job config for future runs
```

### Example 3: New Pipeline Run with Alignment

```bash
# Prepare job with MLX backend
./prepare-job.sh \
    --input "Jaane Tu Ya Jaane Na 2008.mp4" \
    --source-lang hi \
    --target-lang en \
    --clip "00:04:00-00:10:00"

# Run pipeline (alignment stage now produces output!)
./run-pipeline.sh out/2025/11/25/1/1

# Verify alignment output
ls -lh out/2025/11/25/1/1/05_alignment/
# total 512K
# -rw-r--r-- 1 user staff 512K Nov 25 10:30 segments_aligned.json

# Check word counts
jq '[.segments[].words | length] | add' \
    out/2025/11/25/1/1/05_alignment/segments_aligned.json
# Output: 1523 (total words with timing!)
```

## Integration with Pipeline

### Stage Flow (Updated)

```
01. demux                    → Extract audio
02. source_separation        → Separate vocals (optional)
03. pyannote_vad            → Voice activity detection
04. asr                      → Transcribe (segment-level)
05. alignment               → Word-level timestamps ✨ NEW
06. hallucination_removal    → Clean transcripts
07. lyrics_detection        → Detect song sections
08. translation             → Translate segments
09. subtitle_generation     → Generate SRT files
10. mux                     → Embed subtitles
```

### Before vs After

**Before** (MLX backend):
```
05_alignment/
└── (empty)  # Just verification, no output
```

**After** (MLX backend):
```
05_alignment/
└── segments_aligned.json  # Full word-level timestamps! ✨
```

## Performance Impact

### MLX Alignment

- **Time**: Adds ~2-3 minutes for 6-minute clip (full re-transcription)
- **Quality**: Same as ASR stage (uses same model/settings)
- **Memory**: ~2-3GB GPU memory (same as ASR)
- **Benefit**: Enables precision features (bias windows, karaoke timing)

### Beam Comparison

- **Time**: ~90s per beam width × 7 beams = ~10 minutes total
- **One-time cost**: Run once to determine optimal beam width
- **Long-term benefit**: Optimize quality vs speed tradeoff

## Configuration

### Enable/Disable Alignment

Alignment runs automatically if:
- Backend is MLX (`WHISPER_BACKEND=mlx`)
- Segments don't have word-level timestamps

To skip alignment (not recommended):
```bash
# In pipeline code, add skip flag
SKIP_ALIGNMENT=true
```

### Beam Width Configuration

Default beam width is set in job config:

```bash
# In .job-*.env
INDICTRANS2_NUM_BEAMS=4  # Default

# After comparison, update to optimal:
INDICTRANS2_NUM_BEAMS=7  # Optimal for your content
```

## Testing

### Test 1: MLX Alignment Module

```bash
# Test alignment on sample job
python3 scripts/mlx_alignment.py \
    out/2025/11/24/1/1/02_source_separation/audio.wav \
    out/2025/11/24/1/1/04_asr/segments.json \
    /tmp/test_aligned.json \
    --language hi \
    --debug

# Verify output
jq '.segments[0] | {text, word_count: (.words | length)}' /tmp/test_aligned.json
```

### Test 2: Beam Comparison

```bash
# Test with small beam range
./compare-beam-search.sh out/2025/11/24/1/1 --beam-range 4,6

# Check outputs
ls -1 out/2025/11/24/1/1/beam_comparison/
# segments_en_beam4.json
# segments_en_beam5.json
# segments_en_beam6.json
# beam_comparison_report.html
```

### Test 3: Pipeline Integration

```bash
# Run full pipeline with new alignment
./prepare-job.sh --input "test.mp4" --source-lang hi --target-lang en
./run-pipeline.sh out/2025/11/25/1/1

# Verify alignment stage output
test -f out/2025/11/25/1/1/05_alignment/segments_aligned.json && \
    echo "✓ Alignment output exists" || \
    echo "✗ Alignment output missing"
```

## Troubleshooting

### Issue: Alignment Stage Still Empty

**Symptoms**:
```bash
$ ls out/2025/11/25/1/1/05_alignment/
# (empty)
```

**Solutions**:
1. Check backend configuration:
   ```bash
   grep WHISPER_BACKEND out/2025/11/25/1/1/.job-*.env
   # Should be: WHISPER_BACKEND=mlx
   ```

2. Check segments have no words:
   ```bash
   jq '.segments[0].words' out/2025/11/25/1/1/04_asr/segments.json
   # Should be: [] (empty)
   ```

3. Check alignment script exists:
   ```bash
   test -f scripts/mlx_alignment.py && echo "✓ Found" || echo "✗ Missing"
   ```

### Issue: Beam Comparison Fails

**Symptoms**:
```bash
✗ Beam width 5: Failed - translation subprocess error
```

**Solutions**:
1. Check IndicTrans2 environment:
   ```bash
   test -d venv/indictrans2 && echo "✓ Exists" || echo "✗ Missing"
   ```

2. Check translator script:
   ```bash
   test -f scripts/indictrans2_translator.py && echo "✓ Found" || echo "✗ Missing"
   ```

3. Test single beam width manually:
   ```bash
   venv/indictrans2/bin/python scripts/indictrans2_translator.py \
       out/2025/11/24/1/1/04_asr/segments.json \
       /tmp/test_beam5.json \
       --src-lang hi \
       --tgt-lang en \
       --num-beams 5
   ```

### Issue: HTML Report Doesn't Open

**Symptoms**:
```bash
✓ Comparison report generated: beam_comparison_report.html
# But browser doesn't open
```

**Solutions**:
```bash
# Manually open report
open out/2025/11/24/1/1/beam_comparison/beam_comparison_report.html

# Or on Linux
xdg-open out/2025/11/24/1/1/beam_comparison/beam_comparison_report.html

# Or copy path and open in browser
echo "file://$(pwd)/out/2025/11/24/1/1/beam_comparison/beam_comparison_report.html"
```

## Future Enhancements

1. **Incremental Alignment**: Only align new segments, not full re-transcription
2. **WhisperX Alignment**: Add word-level alignment for WhisperX backend too
3. **Automatic Beam Selection**: Use quality metrics to auto-select optimal beam width
4. **Real-time Preview**: Stream alignment progress during transcription
5. **Alignment Quality Metrics**: Score and validate word-level timing accuracy

## Files Created/Modified

### New Files
- `scripts/mlx_alignment.py` - MLX word-level alignment module
- `scripts/beam_search_comparison.py` - Beam width comparison tool
- `compare-beam-search.sh` - Convenience wrapper script
- `docs/MLX_ALIGNMENT_BEAM_COMPARISON.md` - This documentation

### Modified Files
- `scripts/run-pipeline.py` - Enhanced `_stage_alignment()` function

### No Changes Required
- `scripts/whisper_backends.py` - Already has MLX alignment stub
- `cache-models.sh` - MLX models already cached
- `bootstrap.sh` - MLX environment already configured

## Summary

This enhancement makes the `05_alignment` directory actually useful by:

1. ✅ **Performing actual alignment** for MLX backend (not just verification)
2. ✅ **Generating word-level timestamps** needed for precision features
3. ✅ **Providing beam comparison tool** for translation quality optimization
4. ✅ **Creating interactive reports** for easy manual inspection
5. ✅ **Maintaining backward compatibility** with existing pipeline

**Impact**: Better subtitle timing, improved bias injection precision, and optimized translation quality through empirical beam width selection.
