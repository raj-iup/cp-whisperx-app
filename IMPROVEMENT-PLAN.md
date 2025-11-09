
# IMPROVEMENT-PLAN.MD — Context‑Aware English Subtitles from Hinglish Bollywood (1990s & 2000s)

> **Purpose:** A complete, production‑ready plan (README format) to generate high‑accuracy, context‑aware **English** subtitles from **Hinglish** dialogue in 1990s & 2000s Bollywood films. Includes step‑by‑step workflow, configs, and code fragments.

---

## Table of Contents
- [Intro (not a step)](#intro-not-a-step)
- [Step 1 — Goals & Success Criteria](#step-1--goals--success-criteria)
- [Step 2 — Curation: Film Buckets (1990s & 2000s)](#step-2--curation-film-buckets-1990s--2000s)
- [Step 3 — Data Acquisition & Preparation](#step-3--data-acquisition--preparation)
- [Step 4 — End‑to‑End Pipeline Overview](#step-4--endtoend-pipeline-overview)
- [Step 5 — Implementation Details](#step-5--implementation-details)
- [Step 6 — Recommended Tech Stack](#step-6--recommended-tech-stack)
- [Step 7 — Orchestration & Config (YAML)](#step-7--orchestration--config-yaml)
- [Step 8 — Hinglish → English Glossary](#step-8--hinglish--english-glossary)
- [Step 9 — Example Commands / Code Fragments](#step-9--example-commands--code-fragments)
- [Step 10 — Human‑in‑the-Loop QA](#step-10--humanintheloop-qa)
- [Step 11 — Rollout Plan](#step-11--rollout-plan)
- [Step 12 — Risks & Mitigations](#step-12--risks--mitigations)
- [Step 13 — Deliverables](#step-13--deliverables)
- [Step 14 — Appendix: Quick Reference](#step-14--appendix-quick-reference)

---

## Intro (not a step)
We will build a robust subtitle pipeline tuned for **Hinglish** (Hindi+English) speech. The pipeline combines **Silero VAD** and **pyannote SAD/diarization**, **Whisper/WhisperX (translate mode)**, **word‑level alignment**, and a **terminology‑aware post‑editing layer**. Two curated buckets (1990s and 2000s) provide diverse accents, slang, diaspora contexts, and rapid code‑switching to stress‑test accuracy.

---

## Step 1 — Goals & Success Criteria

**Primary goal:** Faithful, readable English subtitles that preserve Hinglish intent, humor, and cultural nuance.

**Quality targets**:
- Mixed Error Rate (MER) ≤ **12–15%** on conversational scenes.
- Readability: **≤ 42 chars/line**, **≤ 2 lines**, **≤ 17 CPS** (target **≤ 15 CPS**).
- Terminology consistency ≥ **98%** (glossary‑constrained terms).

**Operational targets**:
- Fast path: ≥ **1 feature film / GPU‑hour**.
- Polish path: **1 film / 2–3 GPU‑hours** (with diarization + alignment + QA).

**Metrics config (JSON fragment):**
```json
{
  "readability": { "max_chars_per_line": 42, "max_lines": 2, "cps_target": 15, "cps_cap": 17 },
  "accuracy": { "metrics": ["WER", "MER"], "mer_target": 0.15 },
  "terminology": { "coverage_target": 0.98, "glossary_path": "glossary/hinglish_master.tsv" }
}
```

---

## Step 2 — Curation: Film Buckets (1990s & 2000s)

> **Acquire rights** and source from Blu‑ray/authorized platforms only.

### 1990s (Hinglish‑forward / urban / diaspora)
- **Rangeela (1995)** — Mumbai slang; rapid code‑switch.
- **Andaz Apna Apna (1994)** — Comedic Hinglish punchlines; idioms & wordplay.
- **Kuch Kuch Hota Hai (1998)** — Campus/urban English interjections.
- **Dil To Pagal Hai (1997)** — Modern urban register; English phrases.
- **Pardes (1997)** — Diaspora context; cross‑cultural vocabulary.
- **Hyderabad Blues (1998)** — Indie Hinglish classic; everyday bilingualism.
- **Bombay Boys (1998)** — Alt/indie with strong Hinglish/English mix.

_Optional_: **Kabhi Haan Kabhi Naa (1994)**, **Duplicate (1998)**, **Sarfarosh (1999)**.

### 2000s (youth/urban/diaspora; heavier Hinglish)
- **Dil Chahta Hai (2001)** — Urban youth; natural code‑switching.
- **Kabhi Khushi Kabhie Gham (2001)** — Family+diaspora toggling.
- **Kal Ho Naa Ho (2003)** — NYC diaspora; English quips + Hindi sentiment.
- **Lakshya (2004)** — Youth/professional registers.
- **Salaam Namaste (2005)** — Australia diaspora; frequent Hinglish.
- **Rang De Basanti (2006)** — Youth slang; overlaps & emotion.
- **Namastey London (2007)** — UK diaspora; accent variety.
- **Jab We Met (2007)** — Quick banter; regional accent + Hinglish.
- **Rock On!! (2008)** — Band jargon + Hinglish.
- **Jaane Tu… Ya Jaane Na (2008)** — Friend‑group colloquialisms.
- **3 Idiots (2009)** — Engineering campus; tech terms + Hinglish.
- **Wake Up Sid (2009)** — Mumbai newsroom/city life; code‑switch.

_Optional_: **Hera Pheri (2000)**, **Swades (2004)**.

**Manifest (YAML fragment):**
```yaml
catalog:
  - title: "Rangeela"
    year: 1995
    notes: "Mumbai slang; rapid code-switch"
  - title: "Dil Chahta Hai"
    year: 2001
    notes: "Urban youth; code-switching"
  # ... add the rest
```

---

## Step 3 — Data Acquisition & Preparation

1. **Demux & downmix (ffmpeg):**
   ```bash
   ffmpeg -i input.mkv -map 0:a:0 -ac 1 -ar 16000 -c:a pcm_s16le audio.wav
   ffmpeg -i input.mkv -map 0:v:0 -c copy video.h264
   ```

2. **Loudness normalize** (EBU R128 via `loudnorm` for stable VAD/ASR):
   ```bash
   ffmpeg -i audio.wav -af "loudnorm=I=-23:LRA=7:TP=-2" -ar 16000 -ac 1 audio_norm.wav
   ```

3. **Light denoise/dereverb (optional):**
   ```bash
   ffmpeg -i audio_norm.wav -af "arnndn=m=rnnoise-models/rnnoise-model.bin" audio_clean.wav
   ```

4. **Channel selection**: Prefer **dialogue stem** if available (5.1 → center). Example:
   ```bash
   ffmpeg -i input.mkv -map_channel 0.1.0 audio_center.wav
   ffmpeg -i audio_center.wav -ac 1 -ar 16000 -c:a pcm_s16le audio_clean.wav
   ```

---

## Step 4 — End‑to‑End Pipeline Overview

```
[Ingest] -> [Preprocess] -> [VAD/SAD] -> [Diarization?] -> [ASR (translate)]
           -> [Word Alignment] -> [Post-edit (glossary, rules)]
           -> [Format & QC] -> [Export SRT/VTT + Reports]
```

**Paths:**
- **Fast path (auto):** Silero VAD → Whisper(translate) → basic rules → export.
- **Polish path (recommended):** Silero VAD → pyannote SAD + diarization → WhisperX(translate) → alignment → terminology + CPS fixing → human QA → export.

---

## Step 5 — Implementation Details

### 5.1 Voice Activity Detection (VAD)
- **Silero (set `STEP_VAD_SILERO=true`)** — fast gating for clean audio.
  - Suggested: `threshold=0.5`, `min_silence_dur=0.2s`, `min_speech_dur=0.3s`, `pad=0.2s`.
- **pyannote SAD (set `STEP_VAD_PYANNOTE=true`)** — robust on overlaps/multi‑speaker.
  - Suggested: `onset=0.5`, `offset=0.5`, `min_duration_on/off=0.2–0.3s`, `pad=0.2s`.
- **Escalation rule:** Run Silero first; if `overlap_ratio > 0.1` or `speakers >= 3`, refine with pyannote.

**Python fragment (conceptual):**
```python
from vad_utils import run_silero, run_pyannote, detect_overlap

segments = run_silero("audio_clean.wav", thr=0.5, min_sil=0.2, min_sp=0.3, pad=0.2)
if detect_overlap("audio_clean.wav", segments) or any(s.speaker_count >= 3 for s in segments):
    segments = run_pyannote("audio_clean.wav", base_segments=segments,
                             onset=0.5, offset=0.5, min_on=0.2, min_off=0.2, pad=0.2)
```

### 5.2 Speaker Diarization
- Use **pyannote** on group scenes (party, meeting, classroom).
- Stabilize labels across reels (map `SPEAKER_00 → Aditi`, etc.).

**Label mapping (JSON):**
```json
{ "SPEAKER_00": "Aditi", "SPEAKER_01": "Jai", "SPEAKER_02": "Arjun" }
```

### 5.3 ASR + Translate (code‑switch aware)
- **Whisper/WhisperX** in `task=translate` (Hindi→English; English remains English).
- Use **initial prompts** per film/scene for names, slang, locations.
- For songs/chanting: consider `task=transcribe` then post‑translate if needed.

**CLI (WhisperX example):**
```bash
whisperx audio_clean.wav   --model large-v3 --task translate --language auto   --diarize True --compute_type float16 --align_model wav2vec2   --initial_prompt "$(cat prompts/dch_scene1.txt)"   --output_dir out/
```

### 5.4 Word/Phoneme Alignment
- Run **WhisperX aligner** to refine timestamps.
- Snap subtitle cuts to **word boundaries** and clause edges.

### 5.5 Context‑Aware Post‑Editing
- Apply glossary (Hinglish→English) with context notes.
- Maintain per‑film “memory” for names/catchphrases.
- Prefer natural English tone over literal translation.

**Rule fragment (YAML):**
```yaml
post_edit:
  merge_short_gaps_ms: 250
  min_segment_ms: 1000
  max_segment_ms: 20000
  italics_for_songs: true
  sfx_brackets: true
  casing: "sentence"
  honorifics:
    ji: "sir|ma’am|omit"
  slang_map:
    yaar: ["dude", "man"]
    jugaad: ["makeshift fix", "hacky workaround"]
```

### 5.6 Subtitle Formatting Rules
- **Max lines:** 2 · **Max width:** 42 chars/line · **Target CPS:** ≤ 15 (cap 17)
- Break on clause boundaries; avoid splitting verb phrases.
- *Italics* for songs/VO; `[SFX]` in brackets; speaker labels for off‑screen.

**SRT snippet:**
```srt
23
00:12:18,240 --> 00:12:21,000
Dude, listen—this isn’t a joke.

24
00:12:21,000 --> 00:12:24,200
We’ll hack a makeshift fix tonight.
```

### 5.7 QA Metrics
- **Auto:** WER/MER, CPS & line‑length violations, terminology coverage.
- **Human:** linguist + subtitles editor review; humor/idiom/intent.

**Python (CPS + width checks):**
```python
from srt_utils import parse_srt

subs = parse_srt("out/movie.srt")
violations = []
for s in subs:
    lines = s.content.split("\n")
    for line in lines:
        if len(line) > 42:
            violations.append((s.index, "line_width", len(line)))
    dur = (s.end - s.start).total_seconds()
    cps = len(s.content.replace("\n", " ")) / max(dur, 0.001)
    if cps > 17:
        violations.append((s.index, "cps", cps))
print({"violations": violations[:10], "total": len(violations)})
```

---

## Step 6 — Recommended Tech Stack
- **Audio/Video:** `ffmpeg`, `pydub`, `librosa`.
- **VAD/SAD:** Silero, `pyannote.audio`.
- **ASR:** OpenAI Whisper / WhisperX (+ CTranslate2 for speed).
- **Alignment:** WhisperX aligner.
- **Diarization:** `pyannote.audio` speaker diarization.
- **Post‑edit:** Python rule engine + LLM‑assisted editing with strict style constraints.
- **QA/CI:** Python scripts for metrics; pre‑commit hooks.

**requirements.txt (fragment):**
```
ffmpeg-python
librosa
numpy
pydub
jiwer
pandas
pyyaml
```

_Optional_ **Dockerfile (fragment):**
```dockerfile
FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04
RUN apt-get update && apt-get install -y ffmpeg git python3-pip && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt ./
RUN pip3 install -r requirements.txt
COPY . .
CMD ["bash", "run.sh"]
```

---

## Step 7 — Orchestration & Config (YAML)
Use environment toggles for VAD steps:

```bash
export STEP_VAD_SILERO=true
export STEP_VAD_PYANNOTE=true
```

**`config/pipeline.yaml`:**
```yaml
project:
  name: hinglish_subs_bollywood_90s_00s
  output_dir: ./out

source:
  video: input.mkv
  audio: audio_clean.wav

preprocess:
  sample_rate: 16000
  mono: true
  denoise: light

vad:
  step_silero: ${STEP_VAD_SILERO}
  silero:
    threshold: 0.5
    min_silence_dur: 0.2
    min_speech_dur: 0.3
    pad_sec: 0.2
  step_pyannote: ${STEP_VAD_PYANNOTE}
  pyannote:
    onset: 0.5
    offset: 0.5
    min_duration_on: 0.2
    min_duration_off: 0.2
    pad_sec: 0.2

speaker:
  diarization: selective

asr:
  engine: whisperx
  model: large-v3
  task: translate
  language: auto
  ctranslate2: true
  initial_prompt_file: ./glossary/prompts/dil_chahta_hai.txt

alignment:
  enabled: true

post:
  terminology_file: ./glossary/hinglish_master.tsv
  cps_target: 15
  cps_hard_cap: 17
  max_line_chars: 42
  max_lines: 2
  italicize_songs: true
  render_sfx: bracketed

export:
  formats: [srt, vtt]
  include_qc_report: true
```

---

## Step 8 — Hinglish → English Glossary
Create a **TSV** with columns: `source	preferred_english	notes`.

**`glossary/hinglish_master.tsv` (excerpt):**
```
yaar	dude|man	Use "dude" for young male; "man" neutral
bhai	bro|brother	Use "bro" in casual banter; "brother" formal
jugaad	makeshift fix|hacky workaround	Choose per tone/context
acha	well|okay	Often discourse marker; may omit
arey	hey|hey there	Exclamation; keep if emphatic
ji	sir|ma’am|Ø	Suffix/honorific; map by context
```

**Scene prompt (per film/scene):**
```
Characters: Aakash, Sameer, Sid; Setting: Mumbai café.
Keep Hinglish tone in English: "yaar"→"dude", "jugaad"→"makeshift fix".
Names: Aakash (male), Sameer (male), Sid (male).
```

---

## Step 9 — Example Commands / Code Fragments

**Extract & normalize:**
```bash
ffmpeg -i input.mkv -map 0:a:0 -ac 1 -ar 16000 -c:a pcm_s16le audio.wav
ffmpeg -i audio.wav -af "loudnorm=I=-23:LRA=7:TP=-2" -ar 16000 -ac 1 audio_clean.wav
```

**Silero → pyannote escalation:**
```python
segments = silero_vad("audio_clean.wav", thr=0.5, min_sil=0.2, min_sp=0.3, pad=0.2)
if needs_refine(segments):
    segments = pyannote_refine("audio_clean.wav", segments,
                               onset=0.5, offset=0.5, min_on=0.2, min_off=0.2, pad=0.2)
```

**WhisperX translate + align:**
```bash
whisperx audio_clean.wav   --model large-v3 --task translate --language auto   --diarize True --compute_type float16 --align_model wav2vec2   --initial_prompt "$(cat prompts/scene_prompt.txt)"   --output_dir out/
```

**Post‑process:**
```python
from post_rules import apply_glossary, enforce_readability
subs = load_subs("out/audio_clean.srt")
subs = apply_glossary(subs, "glossary/hinglish_master.tsv")
subs = enforce_readability(subs, max_chars=42, max_lines=2, cps_target=15, cps_cap=17)
save_srt(subs, "out/final.srt")
```

**Terminology linter (fragment):**
```python
import pandas as pd
terms = pd.read_csv("glossary/hinglish_master.tsv", sep='\t')
violations = []
for i, row in enumerate(iter_subs("out/final.srt")):
    for src in terms['source']:
        if src in row.text and not any(pref in row.text for pref in terms[terms['source']==src]['preferred_english'].iloc[0].split('|')):
            violations.append((row.index, src))
print({"term_violations": len(violations)})
```

---

## Step 10 — Human‑in‑the-Loop QA
1. Linguist pass: idioms, humor, honorifics, cultural references.
2. Subtitles editor pass: timing, CPS, line breaks, overlaps, songs/VO formatting.
3. Spot‑check against **dialogue‑heavy** scenes and **overlap** moments.

**Reviewer checklist (Markdown):**
```md
- [ ] Meaning preserved; jokes land
- [ ] Names/places/honorifics consistent
- [ ] CPS ≤ 15 (cap 17); line width ≤ 42; ≤ 2 lines
- [ ] Overlaps handled (dual lines or [overlap] note)
- [ ] Songs italicized; summaries vs. full lyrics chosen appropriately
```

---

## Step 11 — Rollout Plan
1. **Pilot (2 films):** e.g., *Rangeela* (1995) & *Dil Chahta Hai* (2001). Tune VAD/ASR/glossary.
2. **Expand (6–8 films):** Cover comedy, campus, diaspora, group‑banter scenes. Iterate thresholds/prompts.
3. **Full Run:** Lock config; generate SRT/VTT + QC reports for all curated titles.
4. **Maintenance:** Keep per‑film memory (names, catchphrases). Update glossary as you go.

**Makefile (fragment):**
```make
run:
	bash scripts/run_pipeline.sh input.mkv out/

qc:
	python tools/check_cps.py out/final.srt
	python tools/term_lint.py out/final.srt glossary/hinglish_master.tsv
```

---

## Step 12 — Risks & Mitigations
- **Over‑literal translations** → Glossary + NLG rewrite rules + human QA.
- **Name/term drift** → Terminology linter + per‑film memory map.
- **Overlap confusion** → pyannote diarization; avoid merging across speaker turns; allow overlapping lines sparingly.
- **Music under dialogue** → Prefer dialogue stem; gain‑ride or re‑mix when available.
- **Latency** → Use CTranslate2/quantized Whisper; Silero first, pyannote selectively.

---

## Step 13 — Deliverables
```
project/
├─ config/
│  └─ pipeline.yaml
├─ glossary/
│  ├─ hinglish_master.tsv
│  └─ prompts/
│     └─ <film_or_scene>.txt
├─ scripts/
│  ├─ run_pipeline.sh
│  └─ postprocess.py
├─ tools/
│  ├─ srt_utils.py
│  └─ term_lint.py
├─ out/
│  ├─ <film>.srt
│  ├─ <film>.vtt
│  └─ qc.json
└─ README.md (this file)
```

---

## Step 14 — Appendix: Quick Reference
- **CPS target:** 15 (cap 17)
- **Max line width:** 42 chars
- **Max lines:** 2
- **VAD default:** Silero; escalate to pyannote for overlaps/multi‑speaker
- **ASR:** Whisper/WhisperX Large‑V3 in `translate` mode; alignment ON
- **Diarization:** selective; always for group scenes
- **Style:** clear, natural English; preserve tone; avoid stilted literalism

**Environment toggles:**
```bash
export STEP_VAD_SILERO=true
export STEP_VAD_PYANNOTE=true
```

**One‑liner (fast path demo):**
```bash
ffmpeg -i input.mkv -map 0:a:0 -ac 1 -ar 16000 -c:a pcm_s16le audio.wav && whisperx audio.wav --model large-v3 --task translate --language auto --output_dir out/ && python tools/postprocess.py out/audio.srt glossary/hinglish_master.tsv --cps 15 --width 42 --lines 2
```

---

**License/Usage:** Ensure you hold rights for all source media. Adjust profanity/localization to rating guidelines.
