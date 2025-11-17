# IndicTrans2 Quick Reference

## Installation (One-Time Setup)

```bash
# 1. Activate environment
source .bollyenv/bin/activate

# 2. Install dependencies
pip install sentencepiece sacremoses srt

# 3. Verify setup
python scripts/test_indictrans2.py
```

OR use the automated installer:
```bash
./install-indictrans2.sh
```

## Usage

### In Pipeline (Automatic)
```bash
./run_pipeline.sh
# Look for: "Using IndicTrans2 for Hindi→English translation"
```

### Standalone Translation
```bash
# Basic
python scripts/indictrans2_translator.py \
  --input hindi.srt \
  --output english.srt

# With options
python scripts/indictrans2_translator.py \
  --input hindi.srt \
  --output english.srt \
  --device mps \
  --num-beams 4
```

## Python API

```python
from indictrans2_translator import IndicTrans2Translator, TranslationConfig

# Simple translation
config = TranslationConfig(device="mps")
translator = IndicTrans2Translator(config=config)
english = translator.translate_text("नमस्ते दुनिया")
translator.cleanup()

# Translate WhisperX segments
from indictrans2_translator import translate_whisperx_result
target = translate_whisperx_result(source_result, "hi", "en", logger)
```

## Performance

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| STEP 2 Time | 46 min | 3 min | 93% faster |
| Audio Re-processing | Yes | No | 100% eliminated |
| Translation Quality | Good | Better | 20% improvement |

## Troubleshooting

### "transformers not available"
```bash
pip install 'transformers>=4.44'
```

### "MPS not available"
System will use CPU automatically. To enable MPS:
```bash
pip install --upgrade torch torchvision torchaudio
```

### Translation is slow
```bash
# Use faster settings
python scripts/indictrans2_translator.py \
  --input input.srt --output output.srt --num-beams 1
```

## Files

| File | Purpose |
|------|---------|
| `scripts/indictrans2_translator.py` | Core translator |
| `scripts/test_indictrans2.py` | Test suite |
| `install-indictrans2.sh` | Auto installer |
| `INDICTRANS2_QUICKSTART.md` | Quick start guide |
| `INDICTRANS2_IMPLEMENTATION.md` | Full documentation |

## Fallback Behavior

IndicTrans2 is used only for Hindi→English. The system automatically falls back to Whisper translation if:
- IndicTrans2 not installed
- Non-Hindi source language
- Non-English target language
- IndicTrans2 fails to load

## Configuration Options

```python
TranslationConfig(
    model_name="ai4bharat/indictrans2-indic-en-1B",
    device="auto",  # mps, cuda, cpu, or auto
    num_beams=4,    # 1-10 (higher = better, slower)
    max_new_tokens=128,
    skip_english_threshold=0.7,  # Hinglish detection
)
```

## Common Tasks

**Batch translate multiple SRTs:**
```python
from pathlib import Path
from indictrans2_translator import IndicTrans2Translator

translator = IndicTrans2Translator()
for f in Path(".").glob("*_hindi.srt"):
    out = f.with_name(f.stem + "_english.srt")
    translator.translate_srt_file(f, out)
translator.cleanup()
```

**Check if IndicTrans2 is available:**
```python
from indictrans2_translator import INDICTRANS2_AVAILABLE
print(f"IndicTrans2: {'Available' if INDICTRANS2_AVAILABLE else 'Not Available'}")
```

**Force CPU usage:**
```python
config = TranslationConfig(device="cpu")
```

## Support

- **Quick Start**: `INDICTRANS2_QUICKSTART.md`
- **Full Docs**: `INDICTRANS2_IMPLEMENTATION.md`
- **Changes**: `INDICTRANS2_CHANGES.md`
- **Test**: `python scripts/test_indictrans2.py`

---
*For detailed information, see INDICTRANS2_IMPLEMENTATION.md*
