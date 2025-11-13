# ASR Bias Prompts - Complete Data Flow

## Overview
The ASR stage uses **rolling windowed bias prompts** to improve recognition of proper nouns (character names, actor names, locations) from TMDB and pre-NER entity extraction.

## Complete Flow Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                     TMDB ENRICHMENT STAGE                         │
│                    (Stage 2: tmdb.py)                             │
├──────────────────────────────────────────────────────────────────┤
│ • Fetches movie/show metadata from TMDB API                      │
│ • Extracts cast names (top 15)                                   │
│ • Extracts crew names (director, writer, etc. - top 5)           │
│ • Saves to: 02_tmdb/tmdb_data.json                               │
│                                                                   │
│ Output Format:                                                    │
│ {                                                                 │
│   "cast": ["Shah Rukh Khan", "Kajol", "Amrish Puri", ...],      │
│   "crew": ["Yash Chopra", "Aditya Chopra", ...]                 │
│ }                                                                 │
└───────────────────────────┬──────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│                     PRE-NER STAGE (Optional)                      │
│                    (Stage 3: pre_ner.py)                          │
├──────────────────────────────────────────────────────────────────┤
│ • Extracts named entities from subtitles/metadata                │
│ • Identifies persons, locations, organizations                   │
│ • Saves to: 03_pre_ner/entities.json                             │
│                                                                   │
│ Output Format:                                                    │
│ {                                                                 │
│   "entities": [                                                   │
│     {"text": "Simran", "type": "PERSON", "confidence": 0.95},   │
│     {"text": "Punjab", "type": "LOCATION", "confidence": 0.92}   │
│   ]                                                               │
│ }                                                                 │
└───────────────────────────┬──────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│                          ASR STAGE                                │
│              (Stage 7: whisperx_integration.py)                   │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ Step 1: LOAD ENTITY NAMES (main() function, lines 554-608)│  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │ 1.1 Load NER entities from 03_pre_ner/entities.json       │  │
│  │     • Extracts entity.text for each entity                │  │
│  │     • Example: ["Simran", "Punjab", "Raj"]                │  │
│  │                                                            │  │
│  │ 1.2 Load TMDB data from 02_tmdb/tmdb_data.json            │  │
│  │     • Adds cast names (top 15)                            │  │
│  │     • Adds crew names (top 5)                             │  │
│  │     • Example: ["Shah Rukh Khan", "Kajol", ...]           │  │
│  │                                                            │  │
│  │ 1.3 Combine and deduplicate                               │  │
│  │     entity_names = list(set(ner + cast + crew))           │  │
│  │     • Removes duplicates                                  │  │
│  │     • Filters empty strings                               │  │
│  └────────────────────────────────────────────────────────────┘  │
│                            │                                      │
│                            ▼                                      │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ Step 2: CREATE BIAS WINDOWS (lines 609-640)               │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │ 2.1 Get audio duration                                     │  │
│  │     • Reads 01_demux/audio.wav                            │  │
│  │     • Calculates duration in seconds                      │  │
│  │     • Example: 9000s (2.5 hour movie)                     │  │
│  │                                                            │  │
│  │ 2.2 Get bias parameters from config                       │  │
│  │     • window_seconds = 45 (default)                       │  │
│  │     • stride_seconds = 15 (default)                       │  │
│  │     • topk = 10 (top 10 terms per window)                 │  │
│  │                                                            │  │
│  │ 2.3 Call create_bias_windows() from bias_injection.py     │  │
│  │     • Creates sliding windows across audio                │  │
│  │     • Each window: 45s duration, 15s stride               │  │
│  │     • For 9000s audio: ~600 windows created               │  │
│  └────────────────────────────────────────────────────────────┘  │
│                            │                                      │
│                            ▼                                      │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ Step 3: BIAS WINDOW CREATION (bias_injection.py)          │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │ create_bias_windows(duration, window, stride, terms, topk)│  │
│  │                                                            │  │
│  │ For each window (start_time += stride):                   │  │
│  │   window_id = 0, 1, 2, ...                                │  │
│  │   start_time = 0s, 15s, 30s, ...                          │  │
│  │   end_time = 45s, 60s, 75s, ...                           │  │
│  │   bias_terms = base_terms[:topk]  # Top 10 terms          │  │
│  │   bias_prompt = ", ".join(bias_terms)                     │  │
│  │                                                            │  │
│  │ Example BiasWindow object:                                │  │
│  │ {                                                          │  │
│  │   "window_id": 0,                                         │  │
│  │   "start_time": 0.0,                                      │  │
│  │   "end_time": 45.0,                                       │  │
│  │   "bias_terms": [                                         │  │
│  │     "Shah Rukh Khan", "Kajol", "Amrish Puri",            │  │
│  │     "Simran", "Raj", "Punjab", "London",                 │  │
│  │     "Yash Chopra", "Aditya Chopra", "DDLJ"               │  │
│  │   ],                                                       │  │
│  │   "bias_prompt": "Shah Rukh Khan, Kajol, Amrish Puri..." │  │
│  │ }                                                          │  │
│  └────────────────────────────────────────────────────────────┘  │
│                            │                                      │
│                            ▼                                      │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ Step 4: SAVE BIAS WINDOWS (lines 636-641)                 │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │ save_bias_windows(bias_dir, windows, basename)             │  │
│  │                                                            │  │
│  │ Saves to: 07_asr/bias_windows/                            │  │
│  │   • transcript.bias.window.0000.json                      │  │
│  │   • transcript.bias.window.0001.json                      │  │
│  │   • ...                                                    │  │
│  │   • transcript.bias.window.0599.json                      │  │
│  └────────────────────────────────────────────────────────────┘  │
│                            │                                      │
│                            ▼                                      │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ Step 5: TRANSCRIBE WITH BIAS (lines 655-667)              │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │ run_whisperx_pipeline(                                     │  │
│  │   audio_file=...,                                         │  │
│  │   bias_windows=bias_windows,  # Pass to WhisperX          │  │
│  │   ...                                                      │  │
│  │ )                                                          │  │
│  │                                                            │  │
│  │ → Calls processor.transcribe_with_bias(...)               │  │
│  │   (lines 199-256)                                         │  │
│  └────────────────────────────────────────────────────────────┘  │
│                            │                                      │
│                            ▼                                      │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ Step 6: APPLY BIAS TO SEGMENTS (lines 252-284)            │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │ NOTE: Currently, bias is applied as METADATA ONLY          │  │
│  │       Not actually passed to Whisper model                │  │
│  │                                                            │  │
│  │ _apply_bias_context(result, bias_windows):                │  │
│  │   For each segment:                                        │  │
│  │     • Get segment start time                              │  │
│  │     • Find matching bias window for that time             │  │
│  │     • Add bias metadata to segment:                       │  │
│  │       - segment["bias_window_id"] = window.window_id      │  │
│  │       - segment["bias_terms"] = window.bias_terms         │  │
│  │                                                            │  │
│  │ Example annotated segment:                                │  │
│  │ {                                                          │  │
│  │   "start": 12.5,                                          │  │
│  │   "end": 15.8,                                            │  │
│  │   "text": "मैं शाहरुख़ खान हूँ",                          │  │
│  │   "bias_window_id": 0,                                    │  │
│  │   "bias_terms": ["Shah Rukh Khan", "Kajol", ...]         │  │
│  │ }                                                          │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

## Data Sources

### 1. TMDB Data (Primary Source)
**Stage**: 02_tmdb  
**File**: `tmdb_data.json`  
**Content**:
```json
{
  "cast": [
    "Shah Rukh Khan",
    "Kajol",
    "Amrish Puri",
    "Farida Jalal",
    "Anupam Kher",
    ...  // Up to 15 cast members
  ],
  "crew": [
    "Yash Chopra",
    "Aditya Chopra",
    "Jatin-Lalit",
    ...  // Up to 5 crew members
  ]
}
```

**Loaded at**: Line 584-604 in `whisperx_integration.py`

### 2. Pre-NER Entities (Secondary Source)
**Stage**: 03_pre_ner  
**File**: `entities.json`  
**Content**:
```json
{
  "entities": [
    {
      "text": "Simran",
      "type": "PERSON",
      "confidence": 0.95
    },
    {
      "text": "Punjab",
      "type": "LOCATION",
      "confidence": 0.92
    }
  ]
}
```

**Loaded at**: Line 568-580 in `whisperx_integration.py`

## Bias Window Structure

### Window Parameters (Configurable)

```python
# From config/.env.pipeline or defaults
BIAS_WINDOW_SECONDS=45     # Window duration (default: 45s)
BIAS_STRIDE_SECONDS=15     # Stride between windows (default: 15s)
BIAS_TOPK=10              # Top K terms per window (default: 10)
BIAS_ENABLED=true         # Enable/disable bias (default: true)
```

### BiasWindow Object

```python
@dataclass
class BiasWindow:
    window_id: int           # Sequential ID: 0, 1, 2, ...
    start_time: float        # Window start in seconds
    end_time: float          # Window end in seconds
    bias_terms: List[str]    # Top-K entity names
    bias_prompt: str         # Comma-separated terms
```

### Example Window Calculation

**Audio Duration**: 9000 seconds (2.5 hours)  
**Window Size**: 45 seconds  
**Stride**: 15 seconds  

**Result**:
- **Total Windows**: ~600
- **Window Coverage**: Overlapping (45s window, 15s stride = 30s overlap)

```
Window 0:   0s -  45s  (terms: top 10)
Window 1:  15s -  60s  (terms: top 10)
Window 2:  30s -  75s  (terms: top 10)
...
Window 599: 8985s - 9000s (terms: top 10)
```

## Current Limitation: Metadata Only

⚠️ **IMPORTANT**: Currently, bias prompts are **NOT** passed to the Whisper model during transcription. They are only added as metadata to segments.

### What Happens Now

```python
# Line 241-246: Transcription WITHOUT bias
result = self.backend.transcribe(
    audio_file,
    language=source_lang,
    task=task,
    batch_size=batch_size
    # NO initial_prompt or bias_prompt parameter!
)

# Line 253-254: Bias added as metadata AFTER transcription
if bias_windows:
    result = self._apply_bias_context(result, bias_windows)
```

### Why Metadata Only?

1. **WhisperX Backend**: Uses CTranslate2 which has limited parameter support
2. **Initial Prompt**: Not currently passed to the backend
3. **Post-Processing**: Bias terms saved for potential future use

### Future Enhancement

To actually use bias prompts during transcription:

```python
# Option 1: Use initial_prompt parameter (if backend supports)
result = self.backend.transcribe(
    audio_file,
    language=source_lang,
    task=task,
    initial_prompt=bias_window.bias_prompt,  # Add bias here
    batch_size=batch_size
)

# Option 2: Process audio in chunks matching bias windows
for window in bias_windows:
    chunk = extract_audio_chunk(audio_file, window.start_time, window.end_time)
    result = transcribe(chunk, initial_prompt=window.bias_prompt)
```

## File Locations

### Input Files
```
02_tmdb/tmdb_data.json          # TMDB cast/crew
03_pre_ner/entities.json        # NER entities (optional)
01_demux/audio.wav              # Audio for duration calculation
```

### Output Files
```
07_asr/bias_windows/
├── transcript.bias.window.0000.json
├── transcript.bias.window.0001.json
├── transcript.bias.window.0002.json
├── ...
└── transcript.bias.window.0599.json

07_asr/transcript.json          # Segments with bias metadata
07_asr/translation.json         # Translation results
```

## Bias Window File Format

**File**: `07_asr/bias_windows/transcript.bias.window.0000.json`

```json
{
  "window_id": 0,
  "start_time": 0.0,
  "end_time": 45.0,
  "bias_terms": [
    "Shah Rukh Khan",
    "Kajol",
    "Amrish Puri",
    "Simran",
    "Raj",
    "Punjab",
    "London",
    "Yash Chopra",
    "Aditya Chopra",
    "DDLJ"
  ],
  "bias_prompt": "Shah Rukh Khan, Kajol, Amrish Puri, Simran, Raj, Punjab, London, Yash Chopra, Aditya Chopra, DDLJ"
}
```

## Segment with Bias Metadata

**File**: `07_asr/transcript.json`

```json
{
  "segments": [
    {
      "start": 12.5,
      "end": 15.8,
      "text": "मैं शाहरुख़ खान हूँ",
      "words": [...],
      "bias_window_id": 0,
      "bias_terms": [
        "Shah Rukh Khan",
        "Kajol",
        "Amrish Puri",
        ...
      ]
    }
  ]
}
```

## Code References

### Main Flow
- **Line 554-650**: Load entities and create bias windows (main function)
- **Line 655-667**: Run WhisperX pipeline with bias
- **Line 465-469**: Call transcribe_with_bias

### Bias Functions
- **Line 199-256**: `transcribe_with_bias()` - Main transcription with bias
- **Line 258-284**: `_apply_bias_context()` - Add bias metadata to segments

### Bias Creation
- **bias_injection.py**:
  - `create_bias_windows()` - Create rolling windows
  - `save_bias_windows()` - Save windows to files
  - `get_window_for_time()` - Find window for timestamp

## Configuration

### Enable/Disable Bias

```bash
# config/.env.pipeline
BIAS_ENABLED=true           # Enable bias injection
BIAS_WINDOW_SECONDS=45      # Window size
BIAS_STRIDE_SECONDS=15      # Stride
BIAS_TOPK=10               # Top K terms per window
```

### Disable Bias

```bash
BIAS_ENABLED=false
```

When disabled:
- No bias windows created
- No entity loading
- Transcription proceeds without bias metadata

## Performance Impact

### Window Creation
- **Time**: ~1-2 seconds for 600 windows
- **Memory**: Minimal (~1MB for 600 windows)

### Transcription
- **Current**: No impact (metadata only)
- **Future**: If implemented as chunked processing, could increase time

## Summary

| Stage | Role | Output |
|-------|------|--------|
| **TMDB** | Fetch cast/crew names | `tmdb_data.json` |
| **Pre-NER** | Extract entities from metadata | `entities.json` |
| **ASR** | Combine sources → create windows → transcribe | Bias windows + transcript |

**Current State**: Bias terms collected and saved as metadata  
**Future**: Can be used for actual prompt injection during transcription

---

**Documentation Date**: 2025-11-13  
**Related Files**: `whisperx_integration.py`, `bias_injection.py`  
**Status**: Metadata implementation (not active prompting)
