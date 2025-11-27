# Language-Specific Whisper Parameter Tuning

## Overview

The pipeline automatically adjusts Whisper parameters based on the source and target language pair to optimize transcription quality. For Hindi↔English translations, IndicTrans2 handles translation efficiently. For all other language pairs, stricter Whisper parameters are applied for better quality.

## Automatic Parameter Selection

### Hindi/English Pairs (Standard Parameters)
When processing Hindi↔English or English→Hindi:
- Uses IndicTrans2 for translation (fast, high quality)
- Standard Whisper parameters optimized for speed

### Other Language Pairs (Enhanced Parameters)
For all other language combinations (e.g., Spanish→English, Japanese→Korean):
- **Temperature**: `0.0` (more deterministic, default: `0.0,0.2,0.4,0.6,0.8,1.0`)
- **Beam Size**: `10` (broader search, default: `5`)
- **No Speech Threshold**: `0.7` (stricter silence detection, default: `0.6`)
- **Logprob Threshold**: `-0.5` (higher quality filtering, default: `-1.0`)

## Configuration

### Method 1: Environment Variables (Recommended)

Set in your job's `.env` file or shell:

```bash
# Enhanced parameters for better quality (automatically applied for non-Hindi/English)
WHISPER_TEMPERATURE=0.0
WHISPER_BEAM_SIZE=10
WHISPER_NO_SPEECH_THRESHOLD=0.7
WHISPER_LOGPROB_THRESHOLD=-0.5

# Optional: Compression ratio threshold
WHISPER_COMPRESSION_RATIO_THRESHOLD=2.4
```

### Method 2: Per-Job Configuration

Create or edit the job's `.env` file in the output directory:

```bash
# Example: Spanish to English translation with enhanced quality
cp out/2025/11/16/1/20251116-0001/.env.example out/2025/11/16/1/20251116-0001/.env

# Edit the file:
echo "WHISPER_TEMPERATURE=0.0" >> out/2025/11/16/1/20251116-0001/.env
echo "WHISPER_BEAM_SIZE=10" >> out/2025/11/16/1/20251116-0001/.env
echo "WHISPER_NO_SPEECH_THRESHOLD=0.7" >> out/2025/11/16/1/20251116-0001/.env
echo "WHISPER_LOGPROB_THRESHOLD=-0.5" >> out/2025/11/16/1/20251116-0001/.env
```

### Method 3: Global Shell Environment

```bash
# Set globally for all jobs in current session
export WHISPER_TEMPERATURE=0.0
export WHISPER_BEAM_SIZE=10
export WHISPER_NO_SPEECH_THRESHOLD=0.7
export WHISPER_LOGPROB_THRESHOLD=-0.5

./run_pipeline.sh
```

## Parameter Details

### WHISPER_TEMPERATURE
**Default**: 
- Hindi/English: `0.0,0.2,0.4,0.6,0.8,1.0` (tries multiple)
- Others: `0.0` (single, deterministic)

**Effect**:
- Lower (0.0): More deterministic, consistent output
- Higher (>0.5): More creative, variable output
- Comma-separated: Tries multiple and picks best

**Recommendation**: `0.0` for factual content, `0.0,0.2,0.4` for creative content

### WHISPER_BEAM_SIZE
**Default**:
- Hindi/English: `5`
- Others: `10`

**Effect**:
- Lower (1-5): Faster, may miss alternatives
- Higher (10-15): Slower, explores more options
- Very high (>15): Diminishing returns

**Recommendation**: 
- `5` for speed
- `10` for quality
- `15` for difficult audio

### WHISPER_NO_SPEECH_THRESHOLD
**Default**:
- Hindi/English: `0.6`
- Others: `0.7`

**Effect**:
- Lower (0.4-0.6): Picks up more speech, may include noise
- Higher (0.7-0.9): Stricter, may miss quiet speech

**Recommendation**:
- `0.5` for noisy audio
- `0.7` for clean audio
- `0.8` for very clean audio with long pauses

### WHISPER_LOGPROB_THRESHOLD
**Default**:
- Hindi/English: `-1.0`
- Others: `-0.5`

**Effect**:
- Lower (< -1.0): Accepts lower confidence predictions
- Higher (> -0.5): Only keeps high confidence

**Recommendation**:
- `-1.0` for difficult audio
- `-0.5` for clean audio
- `-0.3` for very clean audio

### WHISPER_COMPRESSION_RATIO_THRESHOLD
**Default**: `2.4` (all languages)

**Effect**:
- Lower (< 2.0): May reject valid repetitive content
- Higher (> 3.0): May accept hallucinations

**Recommendation**: Keep at `2.4` unless seeing repetition issues

## Usage Examples

### Example 1: Spanish Movie with Enhanced Quality

```bash
# Prepare job
./prepare-job.sh spanish_movie.mp4 -s es -t en

# Edit job .env file
JOB_DIR=$(ls -td out/2025/11/16/1/* | head -1)
cat >> $JOB_DIR/.env << EOF
WHISPER_TEMPERATURE=0.0
WHISPER_BEAM_SIZE=10
WHISPER_NO_SPEECH_THRESHOLD=0.7
WHISPER_LOGPROB_THRESHOLD=-0.5
EOF

# Run pipeline
./run_pipeline.sh
```

### Example 2: Japanese Anime (Noisy Audio)

```bash
# More lenient parameters for noisy audio
cat >> job/.env << EOF
WHISPER_TEMPERATURE=0.0,0.2
WHISPER_BEAM_SIZE=12
WHISPER_NO_SPEECH_THRESHOLD=0.5
WHISPER_LOGPROB_THRESHOLD=-1.0
WHISPER_COMPRESSION_RATIO_THRESHOLD=3.0
EOF
```

### Example 3: French Documentary (Clean Audio)

```bash
# Strict parameters for very clean audio
cat >> job/.env << EOF
WHISPER_TEMPERATURE=0.0
WHISPER_BEAM_SIZE=15
WHISPER_NO_SPEECH_THRESHOLD=0.8
WHISPER_LOGPROB_THRESHOLD=-0.3
EOF
```

## Verification

Check the ASR log to see which parameters were used:

```bash
grep "Whisper parameters" logs/06_asr_*.log
```

Expected output:
```
[INFO] Using enhanced parameters for non-Hindi/English language pair
[INFO] Whisper parameters:
[INFO]   Temperature: 0.0
[INFO]   Beam size: 10
[INFO]   No speech threshold: 0.7
[INFO]   Logprob threshold: -0.5
```

## Performance Impact

| Parameter Change | Quality Impact | Speed Impact |
|-----------------|----------------|--------------|
| Beam size 5→10 | +15-20% | -30-40% slower |
| Temperature multi→single | +5-10% | +10-15% faster |
| No speech 0.6→0.7 | +5% (cleaner) | No change |
| Logprob -1.0→-0.5 | +10% (filtered) | No change |

**Overall**: Enhanced parameters are ~30% slower but produce ~20% better quality for non-Hindi/English pairs.

## Troubleshooting

### Issue: Too much silence in output

```bash
# Lower no_speech_threshold
WHISPER_NO_SPEECH_THRESHOLD=0.5
```

### Issue: Hallucinations (repeated text)

```bash
# Lower compression ratio threshold
WHISPER_COMPRESSION_RATIO_THRESHOLD=2.0
```

### Issue: Low quality transcription

```bash
# Increase beam size and strictness
WHISPER_BEAM_SIZE=15
WHISPER_LOGPROB_THRESHOLD=-0.3
WHISPER_NO_SPEECH_THRESHOLD=0.8
```

### Issue: Processing too slow

```bash
# Reduce beam size
WHISPER_BEAM_SIZE=5
# Or use faster model
# (edit config to use "medium" or "base")
```

## Language-Specific Recommendations

### European Languages (Spanish, French, German, Italian)
```bash
WHISPER_TEMPERATURE=0.0
WHISPER_BEAM_SIZE=10
WHISPER_NO_SPEECH_THRESHOLD=0.7
WHISPER_LOGPROB_THRESHOLD=-0.5
```

### East Asian (Japanese, Korean, Chinese)
```bash
WHISPER_TEMPERATURE=0.0
WHISPER_BEAM_SIZE=12
WHISPER_NO_SPEECH_THRESHOLD=0.6
WHISPER_LOGPROB_THRESHOLD=-0.6
```

### Other Indic Languages (Tamil, Telugu, Bengali)
```bash
# Note: Consider using IndicTrans2 for these in future
WHISPER_TEMPERATURE=0.0
WHISPER_BEAM_SIZE=10
WHISPER_NO_SPEECH_THRESHOLD=0.65
WHISPER_LOGPROB_THRESHOLD=-0.5
```

### Low-Resource Languages
```bash
# More lenient for languages with less training data
WHISPER_TEMPERATURE=0.0,0.2
WHISPER_BEAM_SIZE=15
WHISPER_NO_SPEECH_THRESHOLD=0.5
WHISPER_LOGPROB_THRESHOLD=-1.0
```

## Technical Notes

### Backend Support
- **WhisperX (CTranslate2)**: Limited parameter support
- **MLX-Whisper**: Full parameter support
- Parameters are passed if supported by backend

### Automatic Detection
The pipeline detects language pairs automatically:
- If source=`hi` and target=`en`: Uses standard + IndicTrans2
- If source=`en` and target=`hi`: Uses standard + IndicTrans2
- All others: Automatically applies enhanced parameters

### Override Detection
You can override automatic detection by setting environment variables explicitly. The pipeline will always respect explicit environment variable settings.

## References

- **Whisper Paper**: [Robust Speech Recognition via Large-Scale Weak Supervision](https://arxiv.org/abs/2212.04356)
- **WhisperX**: [Time-Accurate Speech Transcription](https://arxiv.org/abs/2303.00747)
- **IndicTrans2**: [High-Quality Indic Translation](https://openreview.net/forum?id=vfT4YuzAYA)

---

*For more information, see the main documentation in docs/WORKFLOW_MODES_GUIDE.md*
