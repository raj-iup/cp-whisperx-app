# Hybrid VAD for Noisy Hinglish Media: Silero + PyAnnote
**Target**: 1970s–80s Bollywood (Hinglish), music-under-dialogue, tape hiss, multi‑speaker scenes.  
**Goal**: High-precision speech segmentation for WhisperX ASR with balanced throughput.

---

## 1) Why Hybrid?
- **Silero VAD**: ultra‑fast rough cuts, trims long silences and non‑speech with minimal compute (CPU‑friendly).
- **PyAnnote VAD**: context‑aware refinement; better under music/noise, integrates cleanly with diarization.

**Strategy**: Run **Silero → PyAnnote**. Feed WhisperX only refined speech regions to reduce WER and alignment drift.

---

## 2) Environment Setup
> Use a CUDA/RTX machine. Adjust torch wheel to your CUDA version.

```bash
# Core
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install pyannote.audio==3.* librosa soundfile

# WhisperX (for ASR + forced alignment)
pip install git+https://github.com/m-bain/whisperx.git
```

Silero is loaded from `torch.hub`:
```python
model, utils = torch.hub.load("snakers4/silero-vad", "silero_vad", trust_repo=True)
```

---

## 3) Archive‑Tuned Preprocessing
- Resample to **16kHz mono**.
- High‑pass @ **80 Hz**, mild **noise reduction** (6–10 dB), light **compression** (~2:1).  
- Normalize loudness to **−23 to −18 LUFS**. Keep denoise conservative to avoid artifacts.

---

## 4) Stage A — Silero (Rough Cuts)
Recommended defaults for music‑heavy tracks:
```python
ts = get_speech_timestamps(
    torch.from_numpy(wav_16k),
    model,
    sampling_rate=16000,
    threshold=0.6,
    min_speech_duration_ms=250,
    min_silence_duration_ms=300
)
# Merge gaps < 350 ms (hysteresis)
```
Output: candidate speech windows.

---

## 5) Stage B — PyAnnote (Refinement)
- Expand each Silero window by **±0.25 s**.
- Run `pyannote/voice-activity-detection` on window audio.
- Merge refined segments with gaps < **0.2 s**.

```python
from pyannote.audio import Pipeline
vad_pipe = Pipeline.from_pretrained("pyannote/voice-activity-detection")
refined = vad_pipe("window.wav")  # itersegments() → (start, end)
```

**Optional**: Add **diarization** (`pyannote/speaker-diarization`) on full file, then intersect with refined segments for speaker labels.

---

## 6) Stage C — WhisperX (ASR + Alignment)
- Use `large-v3` (or `large-v3-turbo` for speed).
- Transcribe **only refined segments**; disable Whisper’s internal VAD.
- Run **forced alignment** per segment; rebase times to original audio.

```python
model = whisperx.load_model("large-v3", device)
result = model.transcribe(seg_path, language=None, task="transcribe")
align_model, meta = whisperx.load_align_model(language_code=result["language"], device=device)
aligned = whisperx.align(result["segments"], align_model, meta, seg_path, device)
```

Exports: SRT/WebVTT/JSON with word‑level timestamps.

---

## 7) Parameter Cheat‑Sheet (Good Defaults)
**Silero**  
- `threshold`: **0.6**  
- `min_speech_duration_ms`: **250**  
- `min_silence_duration_ms`: **300**  
- Merge gaps < **0.35 s**

**PyAnnote**  
- Window pad: **±0.25 s**  
- Merge gaps < **0.2 s**  
- Prefer **GPU** for long files

**WhisperX**  
- Model: `large-v3` / `large-v3-turbo`  
- Segment‑wise transcription + **forced alignment**  
- Temperature fallback: `[0.0, 0.2, 0.4]` for code‑switching

---

## 8) Quality Controls (Vintage Audio)
- Spot‑check scenes with **music under dialogue**.  
- Verify code‑switched lines and ensure **no mid‑word cuts** at joins.  
- Subtitle constraints: ~42 chars/line, ≤2 lines, 100–160 wpm.

---

## 9) Example Orchestrator (Pseudo‑Pipeline)
```python
# 1) preprocess -> 2) silero_windows -> 3) pyannote_refine -> 4) whisperx_transcribe -> 5) align -> 6) diarize -> 7) export
```

For a production repo, add:  
- **Make targets** (`make asr`, `make srt`)  
- **Dockerfile** with CUDA base (≤ host CUDA)  
- **Metrics**: coverage %, avg segment length, RTF (ASR sec / audio sec).

---

## 10) Troubleshooting
| Symptom | Likely Cause | Action |
|---|---|---|
| Music flagged as speech | Silero threshold too low | Raise to 0.6–0.7; add light denoise |
| Lost syllables at cuts | Windows too tight | Increase pad to ±0.3–0.4 s |
| Slow throughput | Running PyAnnote on full audio | Run only on Silero windows; batch WhisperX 20–60 s |
| Misaligned subtitles | Skipped alignment | Ensure WhisperX forced alignment is applied |

---

## 11) Minimal File Tree (suggested)
```
project/
├─ audio/
├─ scripts/
│  ├─ preprocess.py
│  ├─ vad_silero.py
│  ├─ vad_pyannote.py
│  ├─ asr_whisperx.py
│  └─ export_srt.py
├─ README-SILERO-PYANNOTE-VAD.md
└─ requirements.txt
```

---

**Recommendation**: For 70s–80s Bollywood sources, default to **hybrid mode**. Use Silero to prune, PyAnnote to polish, WhisperX to lock timestamps.
