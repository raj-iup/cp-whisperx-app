# Silero VAD Stage - Native MPS Pipeline

## Overview

The Silero VAD (Voice Activity Detection) stage is the 4th stage in the native MPS pipeline. It performs coarse-grained speech segmentation using the Silero VAD v4 model, which is optimized for Apple Silicon MPS acceleration.

## Purpose

Silero VAD provides fast, accurate speech detection to:
- Identify speech segments in audio files
- Filter out silence and non-speech regions
- Prepare coarse timestamps for downstream diarization
- Optimize processing by focusing on speech-containing regions

## Location

- **Script**: `native/scripts/04_silero_vad.py`
- **Wrapper**: `native/utils/silero_vad_wrapper.py`
- **Requirements**: `native/requirements/silero_vad.txt`
- **Virtual Environment**: `native/venvs/silero-vad/`

## Dependencies

```txt
torch>=2.0.0
torchaudio>=2.0.0
omegaconf>=2.1.0
```

Plus common dependencies from `native/requirements/common.txt`:
```txt
python-json-logger>=2.0.0
python-dotenv>=1.0.0
```

## Configuration

### Command Line Arguments

```bash
python native/scripts/04_silero_vad.py \
  --input <video_file> \
  --movie-dir <output_directory> \
  --threshold 0.5 \
  --min-speech-ms 250 \
  --merge-gap 0.35
```

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--input` | string | required | Path to input video file |
| `--movie-dir` | string | required | Output directory for movie |
| `--threshold` | float | 0.5 | Speech detection threshold (0-1) |
| `--min-speech-ms` | int | 250 | Minimum speech duration in milliseconds |
| `--merge-gap` | float | 0.35 | Maximum gap to merge segments (seconds) |

### Default Configuration

```python
default_config = {
    'threshold': 0.5,                    # Speech probability threshold
    'min_speech_duration_ms': 250,       # Min speech segment (ms)
    'min_silence_duration_ms': 100,      # Min silence between segments (ms)
    'merge_gap': 0.35,                   # Max gap to merge (seconds)
    'min_segment_duration': 0.3          # Filter segments shorter than this
}
```

## Input Requirements

### Expected Input Files

- **Audio File**: `<movie_dir>/audio/audio.wav`
  - Format: WAV
  - Sample Rate: 16kHz (automatically resampled by Silero)
  - Channels: Mono or Stereo (handled automatically)

### Prerequisites

The following stage must complete successfully:
1. **Stage 1 (Demux)**: Audio extraction from video

## Output

### Directory Structure

```
<movie_dir>/
└── vad/
    └── silero_segments.json
```

### Output Format

**`silero_segments.json`**:
```json
{
  "segments": [
    {
      "start": 0.32,
      "end": 5.47
    },
    {
      "start": 6.12,
      "end": 12.85
    }
  ],
  "statistics": {
    "total_duration": 120.5,
    "num_segments": 45,
    "speech_duration": 98.3,
    "speech_ratio": 0.815,
    "threshold": 0.5,
    "device": "mps"
  },
  "config": {
    "threshold": 0.5,
    "min_speech_duration_ms": 250,
    "merge_gap": 0.35
  }
}
```

### Manifest Updates

The stage updates `<movie_dir>/manifest.json`:

```json
{
  "stages": {
    "silero-vad": {
      "status": "success",
      "started_at": "2024-10-29T18:00:00",
      "completed_at": "2024-10-29T18:00:15",
      "duration_seconds": 15.2,
      "outputs": {
        "segments": {
          "path": "/path/to/out/Movie/vad/silero_segments.json",
          "exists": true,
          "size_bytes": 1024,
          "description": "Silero VAD segments"
        }
      },
      "metadata": {
        "device": "mps",
        "segment_count": 45,
        "speech_ratio": 0.815,
        "total_duration": 120.5,
        "threshold": 0.5
      }
    }
  }
}
```

## Performance

### Device Acceleration

- **MPS (Apple Silicon)**: Automatic detection and usage
- **CPU Fallback**: Automatic fallback if MPS unavailable
- **Model Device**: Note - Silero VAD may use CPU even when MPS is requested for compatibility

### Typical Performance

- **Processing Speed**: ~10-20x real-time on M1/M2
- **Memory Usage**: ~500MB-1GB
- **Example**: 2-hour movie processes in ~6-12 minutes

## Algorithm Details

### Processing Pipeline

1. **Model Loading**
   - Load Silero VAD v4 from torch hub
   - Move to optimal device (MPS/CPU)
   - Cache model for reuse

2. **Audio Processing**
   - Read audio file (auto-resample to 16kHz)
   - Run VAD inference
   - Generate speech timestamps

3. **Segment Refinement**
   - Merge close segments (within `merge_gap`)
   - Filter very short segments (< `min_segment_duration`)
   - Calculate statistics

4. **Output Generation**
   - Save segments to JSON
   - Update manifest
   - Log metrics

### Silero VAD Features

- **Model**: Silero VAD v4
- **Architecture**: LSTM-based neural network
- **Sampling Rate**: 16kHz (required)
- **Frame Size**: 512 samples (~32ms)
- **Languages**: Language-agnostic
- **License**: MIT

## Error Handling

### Common Issues

1. **Audio File Not Found**
   ```
   Error: Audio file not found: <path>
   Solution: Ensure Stage 1 (Demux) completed successfully
   ```

2. **Model Download Failure**
   ```
   Error: Failed to load Silero VAD model
   Solution: Check internet connection, torch hub cache
   ```

3. **Memory Issues**
   ```
   Error: Out of memory
   Solution: Process shorter clips or use CPU device
   ```

### Logging

Logs are written to:
- **Console**: INFO level and above
- **File**: `logs/silero-vad_<movie_name>_<timestamp>.log` (DEBUG level)

## Testing

### Run Test Suite

```bash
cd /path/to/cp-whisperx-app
source native/venvs/silero-vad/bin/activate
python native/scripts/test_silero_vad_mps.py
```

### Manual Testing

```bash
# Process a sample video
./native/pipeline.sh "in/sample_video.mp4"

# Check output
cat out/sample_video/vad/silero_segments.json | jq
```

## Integration with Pipeline

### Stage Order

```
01_demux.py          → Extract audio
02_tmdb.py           → Fetch metadata
03_pre_ner.py        → Extract entities
04_silero_vad.py     → Coarse VAD (THIS STAGE)
05_pyannote_vad.py   → Refined VAD
06_diarization.py    → Speaker diarization
07_asr.py            → Transcription
08_post_ner.py       → Entity correction
09_subtitle_gen.py   → Generate subtitles
10_mux.py            → Mux final video
```

### Data Flow

**Input from Stage 1**:
- `audio/audio.wav`

**Output to Stage 5**:
- `vad/silero_segments.json` (coarse segments)

**Used by Downstream Stages**:
- Stage 5 (Pyannote VAD): Refines these coarse segments
- Stage 6 (Diarization): Uses refined segments for speaker clustering
- Stage 7 (ASR): Transcribes speech segments only

## Configuration Tips

### For Faster Processing (Lower Quality)

```bash
--threshold 0.6 \        # Higher threshold = less sensitive
--min-speech-ms 500 \    # Ignore very short speech
--merge-gap 0.5          # Merge more aggressively
```

### For Better Accuracy (Slower)

```bash
--threshold 0.4 \        # Lower threshold = more sensitive
--min-speech-ms 100 \    # Capture shorter speech
--merge-gap 0.2          # More granular segments
```

### For Noisy Audio

```bash
--threshold 0.6 \        # Higher threshold to avoid false positives
--min-speech-ms 300      # Ignore brief noise spikes
```

## API Reference

### SileroVAD Class

```python
from silero_vad_wrapper import SileroVAD

# Initialize
vad = SileroVAD(device='mps', logger=logger)

# Process audio
segments, stats = vad.process(
    audio_path=Path('audio.wav'),
    threshold=0.5,
    min_speech_duration_ms=250,
    min_silence_duration_ms=100,
    merge_gap=0.35,
    min_segment_duration=0.3
)

# Access results
print(f"Found {len(segments)} speech segments")
print(f"Speech ratio: {stats['speech_ratio']:.1%}")
```

### Key Methods

- `load_model()`: Load Silero VAD from torch hub
- `detect_speech()`: Run VAD on audio file
- `merge_segments()`: Merge close segments
- `filter_short_segments()`: Remove very short segments
- `process()`: Full pipeline (recommended)

## Secrets Configuration

**Note**: This stage does NOT require `config/secrets.json`. However, downstream stages do.

Ensure `config/secrets.json` exists for the full pipeline:

```json
{
  "hf_token": "hf_...",
  "tmdb_api_key": "...",
  "pyannote_token": "hf_..."
}
```

## Troubleshooting

### MPS Not Detected

```bash
# Check MPS availability
python -c "import torch; print(torch.backends.mps.is_available())"

# If False, ensure you're on Apple Silicon Mac with macOS 12.3+
```

### Model Loading Slow

First load downloads from torch hub (~10MB). Subsequent loads use cache:
- Cache location: `~/.cache/torch/hub/snakers4_silero-vad_master`

### Segments Too Granular

Increase `--merge-gap` parameter:
```bash
--merge-gap 0.5  # Merge segments up to 500ms apart
```

### Missing Speech Segments

Lower `--threshold` parameter:
```bash
--threshold 0.3  # More sensitive detection
```

## References

- [Silero VAD GitHub](https://github.com/snakers4/silero-vad)
- [Silero Models](https://github.com/snakers4/silero-models)
- [PyTorch MPS Backend](https://pytorch.org/docs/stable/notes/mps.html)

## Version History

- **v1.0.0**: Initial implementation with MPS support
- Uses Silero VAD v4
- Integrated with native pipeline manifest system
- Full logging and error handling

## License

Part of cp-whisperx-app project. See main project LICENSE.
