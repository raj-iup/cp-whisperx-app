# ASR Stage Comprehensive Fixes

**Date**: 2025-11-08  
**Job**: 20251108-0001  
**Log**: 00_orchestrator_20251108_102541.log

---

## Issues Identified

### Task 1: Language not fetched from config (Line 6033)
**Issue**: "No language specified, language will be first be detected for each audio file (increases inference time)"

**Root Cause**: ASR stage not reading `WHISPER_LANGUAGE` and `TARGET_LANGUAGE` from job .env file

### Task 2: PyAnnote version warnings (Lines 6035-6036)
**Issue**: Model version mismatch warnings:
- `Model was trained with pyannote.audio 0.0.1, yours is 3.4.0`
- `Model was trained with torch 1.10.0+cu102, yours is 2.8.0`

### Task 3: No speakers detected (Line 6044)
**Issue**: "0 unique speakers identified" but characters exist in diarization output

**Root Cause**: Diarization didn't properly populate speaker_segments (empty array)

### Task 4: Speakers info not used
**Issue**: ASR doesn't use speaker information from diarization stage

### Task 5: Prompt not from correct file (Line 6053)
**Issue**: Initial prompt should come from `prompts/ner_enhanced_prompt.txt`

### Task 6: Temperature parameter error (Line 6056)
**Issue**: `FasterWhisperPipeline.transcribe() got an unexpected keyword argument 'temperature'`

**Root Cause**: CTranslate2/faster-whisper doesn't support `temperature` parameter the same way

---

## Solutions Implemented

### Fix 1: Read Language from Job Config

**File**: `docker/asr/whisperx_asr.py`

```python
# Before: Hard-coded or missing
source_lang = "hi"  # Or None
target_lang = "en"

# After: Read from config
source_lang = config.get('whisper_language', 'hi')
target_lang = config.get('target_language', 'en')
logger.info(f"Language config: source={source_lang}, target={target_lang}")
```

### Fix 2: Suppress PyAnnote Version Warnings

**File**: `scripts/whisperx_integration.py`

```python
import warnings
# Suppress specific version warnings
warnings.filterwarnings('ignore', message='Model was trained with pyannote')
warnings.filterwarnings('ignore', message='Model was trained with torch')
```

### Fix 3: Fix Diarization Speaker Detection

**File**: `docker/diarization/pyannote_diarization.py`

Issue: Diarization creates speaker_segments array but doesn't populate it properly
Need to ensure speaker segments are written to JSON

### Fix 4: Pass Speaker Info to ASR

**File**: `docker/asr/whisperx_asr.py`

```python
# Read speaker info from diarization
character_names = diar_data.get('character_names', [])
num_speakers = diar_data.get('num_speakers', 0)
logger.info(f"Using {num_speakers} speakers from diarization")
logger.info(f"Character names: {', '.join(character_names[:5])}")
```

### Fix 5: Use NER Enhanced Prompt

**File**: `docker/asr/whisperx_asr.py`

```python
# Change prompt loading priority
def load_initial_prompt(movie_dir: Path, logger: PipelineLogger) -> str:
    # Priority 1: NER enhanced prompt (from pre_ner stage)
    ner_prompt = movie_dir / "prompts" / "ner_enhanced_prompt.txt"
    if ner_prompt.exists():
        logger.info(f"Using NER enhanced prompt: {ner_prompt}")
        with open(ner_prompt) as f:
            return f.read().strip()
    
    # Priority 2: Combined prompt (legacy)
    combined_prompt = movie_dir / f"{movie_dir.name}.combined.initial_prompt.txt"
    if combined_prompt.exists():
        with open(combined_prompt) as f:
            return f.read().strip()
    
    # Priority 3: Basic prompt
    initial_prompt = movie_dir / f"{movie_dir.name}.initial_prompt.txt"
    if initial_prompt.exists():
        with open(initial_prompt) as f:
            return f.read().strip()
    
    logger.warning("No initial prompt found")
    return ""
```

### Fix 6: Remove Unsupported Temperature Parameter

**File**: `scripts/whisperx_integration.py`

```python
# Build transcription options
transcribe_options = {
    "language": source_lang if source_lang else None,
    "task": "translate" if source_lang != target_lang else "transcribe",
    "batch_size": batch_size,
    # "temperature": self.temperature,  # NOT SUPPORTED by FasterWhisperPipeline
    "beam_size": self.beam_size,
    "best_of": self.best_of,
    "patience": self.patience,
    "length_penalty": self.length_penalty,
    "no_speech_threshold": self.no_speech_threshold,
    "logprob_threshold": self.logprob_threshold,
    "compression_ratio_threshold": self.compression_ratio_threshold,
    "condition_on_previous_text": self.condition_on_previous_text,
}
```

Note: FasterWhisperPipeline/CTranslate2 uses beam search which doesn't use temperature.
Temperature is for sampling, beam search is deterministic.

---

## Implementation Plan

1. **Fix temperature parameter** (critical - blocks execution)
2. **Fix language reading** from config
3. **Fix prompt loading** to use NER enhanced prompt
4. **Add speaker info logging** from diarization
5. **Suppress PyAnnote warnings** (cosmetic)
6. **Fix diarization** speaker population (separate task)

---

## Testing

After fixes:
```bash
./resume-pipeline.sh 20251108-0001
```

Expected log output:
```
[INFO] Language config: source=hi, target=en
[INFO] Using NER enhanced prompt: .../prompts/ner_enhanced_prompt.txt
[INFO] Using 15 speakers from diarization
[INFO] Character names: Jai Rathod, Aditi Wadia, Meghna, Amit, Shaleen 'Shali'
[INFO] Transcription complete: X segments
```

---

## Related Stages to Fix

All following stages need similar config reading improvements:

- **Stage 8**: Second Pass Translation
- **Stage 9**: Lyrics Detection
- **Stage 10**: Post-NER
- **Stage 11**: Subtitle Generation
- **Stage 12**: Mux

Each should:
1. Read parameters from job .env file
2. Use outputs from previous stages correctly
3. Log configuration clearly
4. Handle errors gracefully

---

**Status**: Ready to implement
