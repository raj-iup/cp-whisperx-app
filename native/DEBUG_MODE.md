# Debug Mode Guide for Native MPS Pipeline

This guide explains how to run any stage of the native MPS pipeline in debug mode for detailed logging and troubleshooting.

## Stage 7: ASR (Transcription + Alignment) Debug Mode

### Quick Start

```bash
# Run ASR stage in debug mode for a specific movie
./native/run_asr_debug.sh <MOVIE_NAME> [options]
```

### Examples

```bash
# Basic usage with default model (base)
./native/run_asr_debug.sh My_Movie_2024

# With custom model and language
./native/run_asr_debug.sh My_Movie_2024 --model small --language en

# With all options
./native/run_asr_debug.sh My_Movie_2024 \
    --model base \
    --language en \
    --batch-size 16 \
    --compute-type float32
```

### Available Options

| Option | Values | Default | Description |
|--------|--------|---------|-------------|
| `--model` | tiny, base, small, medium, large-v2, large-v3 | base | Whisper model size |
| `--language` | en, hi, es, etc. | auto-detect | Language code |
| `--batch-size` | 1-64 | 16 | Batch size for processing |
| `--compute-type` | float16, float32, int8 | float32 | Computation precision |
| `--log-level` | DEBUG, INFO, WARNING, ERROR | DEBUG | Logging verbosity |

### What Debug Mode Provides

1. **Detailed Console Output**: Real-time progress with verbose logging
2. **Comprehensive Log Files**: Saved to `logs/asr_<MOVIE_NAME>_<TIMESTAMP>.log`
3. **Debug-Level Messages**: 
   - Function calls and parameters
   - Internal processing steps
   - Model loading details
   - Memory usage information
   - Timing for each operation

### Debug Log Locations

All logs are saved to the `logs/` directory:

```
logs/
├── asr_My_Movie_20241030_014822.log    # Stage-specific log
└── session_My_Movie_20241030_014800.log # Full pipeline session (if running full pipeline)
```

### Interpreting Debug Output

Debug logs include:
- `[DEBUG]` - Detailed internal operations
- `[INFO]` - General progress information
- `[WARNING]` - Non-fatal issues
- `[ERROR]` - Failures and exceptions
- Function names and line numbers for traceability

Example debug output:
```
[2024-10-30 01:48:22] [native.asr.My_Movie] [DEBUG] [run_asr:53] Configuration: {'model_name': 'base', ...}
[2024-10-30 01:48:23] [native.asr.My_Movie] [INFO] 🔧 Loading model: Faster-Whisper (base) on cpu
[2024-10-30 01:48:30] [native.asr.My_Movie] [DEBUG] [process:145] Processing audio file: /path/to/audio.wav
```

---

## Running Other Stages in Debug Mode

### Method 1: Environment Variable

Set `LOG_LEVEL=DEBUG` before running any stage:

```bash
# For any individual stage
export LOG_LEVEL=DEBUG
source native/venvs/<STAGE>/bin/activate
python native/scripts/<STAGE_SCRIPT>.py --input "in/video.mp4" --movie-dir "out/My_Movie"
```

### Method 2: Modify pipeline.sh

Edit `native/pipeline.sh` and add debug flag to the Python command:

```bash
# Around line 80-85, modify the python command:
python "$script_path" \
    --input "$INPUT_FILE" \
    --movie-dir "$MOVIE_DIR" \
    --log-level DEBUG    # Add this line
```

### Method 3: Add --log-level to Script Call

Most scripts accept `--log-level` argument directly:

```bash
python native/scripts/07_asr.py \
    --input "in/video.mp4" \
    --movie-dir "out/My_Movie" \
    --log-level DEBUG
```

---

## Debug Mode for Specific Stages

### Stage 4: Silero VAD
```bash
export LOG_LEVEL=DEBUG
source native/venvs/silero-vad/bin/activate
python native/scripts/04_silero_vad.py --input "in/video.mp4" --movie-dir "out/My_Movie"
```

### Stage 5: PyAnnote VAD
```bash
export LOG_LEVEL=DEBUG
source native/venvs/pyannote-vad/bin/activate
python native/scripts/05_pyannote_vad.py --input "in/video.mp4" --movie-dir "out/My_Movie"
```

### Stage 6: Diarization
```bash
export LOG_LEVEL=DEBUG
source native/venvs/diarization/bin/activate
python native/scripts/06_diarization.py --input "in/video.mp4" --movie-dir "out/My_Movie"
```

### Stage 7: ASR (Use helper script)
```bash
./native/run_asr_debug.sh My_Movie --model base
```

### Stage 8: Post-NER
```bash
export LOG_LEVEL=DEBUG
source native/venvs/post-ner/bin/activate
python native/scripts/08_post_ner.py --input "in/video.mp4" --movie-dir "out/My_Movie"
```

### Stage 9: Subtitle Generation
```bash
export LOG_LEVEL=DEBUG
source native/venvs/subtitle-gen/bin/activate
python native/scripts/09_subtitle_gen.py --input "in/video.mp4" --movie-dir "out/My_Movie"
```

### Stage 10: Mux
```bash
export LOG_LEVEL=DEBUG
source native/venvs/mux/bin/activate
python native/scripts/10_mux.py --input "in/video.mp4" --movie-dir "out/My_Movie"
```

---

## Troubleshooting

### Debug logs not showing up?

Check that the `logs/` directory exists:
```bash
mkdir -p logs
```

### Too much output?

Use `INFO` level for less verbose output:
```bash
export LOG_LEVEL=INFO
# or
--log-level INFO
```

### Want to debug Python code interactively?

Use Python's debugger:
```bash
source native/venvs/asr/bin/activate
python -m pdb native/scripts/07_asr.py --input "in/video.mp4" --movie-dir "out/My_Movie"
```

### Check device assignment

Debug output will show which device is being used (cpu, mps, cuda):
```
[INFO] 🔧 Loading model: Faster-Whisper (base) on cpu
```

---

## Additional Debugging Tips

1. **Monitor System Resources**: Use `htop` or Activity Monitor to track CPU/GPU/memory usage
2. **Check Output Files**: Verify intermediate files are created in the movie directory
3. **Review Manifest Files**: Each stage creates a `manifest_<STAGE>.json` with metadata
4. **Test with Small Files**: Use short video clips for faster debugging iterations
5. **Compare Logs**: Keep successful run logs to compare against failed runs

---

## Log File Analysis

Useful commands for analyzing log files:

```bash
# Find all errors
grep ERROR logs/asr_*.log

# Find timing information
grep "completed in" logs/asr_*.log

# View last 50 lines
tail -50 logs/asr_*.log

# Follow log in real-time
tail -f logs/asr_*.log

# Search for specific text
grep -i "whisper" logs/asr_*.log
```

---

## Performance Profiling

For advanced performance debugging, add profiling:

```bash
# Profile with cProfile
python -m cProfile -o profile.stats native/scripts/07_asr.py --input "in/video.mp4" --movie-dir "out/My_Movie"

# Analyze profile
python -m pstats profile.stats
```

---

## Support

If you encounter issues:
1. Check the detailed logs in `logs/`
2. Review the stage manifest in `out/<MOVIE>/manifest_<STAGE>.json`
3. Verify all dependencies are installed in the stage's venv
4. Check that required input files exist (audio, previous stage outputs)
