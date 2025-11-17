# Language Parameter Tuning - Quick Reference

## Automatic Behavior

| Language Pair | Parameters | Translation | Speed |
|--------------|------------|-------------|-------|
| Hindi → English | Standard | IndicTrans2 | Fast |
| English → Hindi | Standard | IndicTrans2 | Fast |
| All Others | Enhanced | Whisper | Slower, Better |

## Quick Setup

### Per-Job (Recommended)

```bash
# After prepare-job.sh, edit .env file:
JOB_DIR=$(ls -td out/*/1/* | head -1)
cat >> $JOB_DIR/.env << 'EOF'
WHISPER_TEMPERATURE=0.0
WHISPER_BEAM_SIZE=10
WHISPER_NO_SPEECH_THRESHOLD=0.7
WHISPER_LOGPROB_THRESHOLD=-0.5
EOF
```

### Global (All Jobs)

```bash
export WHISPER_TEMPERATURE=0.0
export WHISPER_BEAM_SIZE=10
export WHISPER_NO_SPEECH_THRESHOLD=0.7
export WHISPER_LOGPROB_THRESHOLD=-0.5
```

## Parameter Quick Guide

| Parameter | Standard | Enhanced | Effect |
|-----------|----------|----------|--------|
| **Temperature** | 0.0,0.2,...1.0 | 0.0 | More deterministic |
| **Beam Size** | 5 | 10 | Better alternatives |
| **No Speech** | 0.6 | 0.7 | Cleaner silence |
| **Logprob** | -1.0 | -0.5 | Higher quality |

## Language Presets

### Clean Audio (Studio, Documentary)
```bash
WHISPER_BEAM_SIZE=15
WHISPER_NO_SPEECH_THRESHOLD=0.8
WHISPER_LOGPROB_THRESHOLD=-0.3
```

### Noisy Audio (Street, Crowd)
```bash
WHISPER_BEAM_SIZE=12
WHISPER_NO_SPEECH_THRESHOLD=0.5
WHISPER_LOGPROB_THRESHOLD=-1.0
```

### Fast Processing
```bash
WHISPER_BEAM_SIZE=5
WHISPER_TEMPERATURE=0.0
```

### Maximum Quality
```bash
WHISPER_BEAM_SIZE=15
WHISPER_TEMPERATURE=0.0
WHISPER_NO_SPEECH_THRESHOLD=0.8
WHISPER_LOGPROB_THRESHOLD=-0.3
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Too much silence | `NO_SPEECH_THRESHOLD=0.5` |
| Repeated text | `COMPRESSION_RATIO_THRESHOLD=2.0` |
| Low quality | `BEAM_SIZE=15`, `LOGPROB_THRESHOLD=-0.3` |
| Too slow | `BEAM_SIZE=5` |

## Verify Settings

```bash
# Check log for applied parameters
grep "Whisper parameters" logs/06_asr_*.log
```

## Examples

```bash
# Spanish→English (auto-enhanced)
./prepare-job.sh movie.mp4 -s es -t en

# Japanese→Korean (custom)
JOB_DIR=$(ls -td out/*/1/* | head -1)
echo "WHISPER_BEAM_SIZE=12" >> $JOB_DIR/.env
./run_pipeline.sh

# Hindi→English (uses IndicTrans2, fast)
./prepare-job.sh movie.mp4 -s hi -t en
```

Full documentation: [LANGUAGE_PARAMETER_TUNING.md](LANGUAGE_PARAMETER_TUNING.md)
