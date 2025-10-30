SYSTEM / MASTER PROMPT — cp-whisperx-app (Context-Aware Hindi→English Subtitles)

GOAL
Build and maintain “cp-whisperx-app”: a context-aware Hindi/Hinglish → English subtitle pipeline for Bollywood films, optimized for Apple Silicon but portable (Intel/Linux), with clean packaging, rich QA artifacts, and container support.

PRIMARY FEATURES
- Rolling windowed prompt injection ON by default to bias ASR/translation within scene context.
  • Window length: 45s; stride: 15s (tunable).
- Proper-noun stabilization from: filename inference → era lexicon → TMDB cast/crew.
- Diarization with optional speaker-name mapping.
- NER-guided canonicalization (spaCy transformer) + punctuation/case polish pass.
- Two-pass merge (keep WhisperX timings; refine English in second pass).
- Mux QC: prefer MP4 (mov_text), fall back to MKV if needed.
- Consistent logs: “[timestamp] [module] [LEVEL] message”.
- Secrets only from ./config/secrets.json (no env var exporting).
- All tunables in ./config/.env; code reads config, not shell env.
- Everything important is logged and manifest.json is written inside a timestamped directory under ./logs.

DEVICE POLICY (preferred → fallback)
1) WhisperX (ASR/translate/alignment): MPS → CPU
2) Diarization (pyannote): CUDA → CPU
3) Second-pass translator (HF Transformers): MPS → CPU
4) spaCy NER: CUDA → CPU
All other modules run on CPU. On Apple Silicon, WhisperX defaults to CPU int8 for stability (MPS can be flaky; user may override).

SUPPORTED EXECUTION MODES
A) Local venv (macOS/Intel/Linux):
  - Homebrew (macOS): ffmpeg, mkvtoolnix
  - Python 3.11 venv
B) Containers (recommended for dependency isolation):
  - ASR container (NumPy 2.x, WhisperX, pyannote 3.x)
  - NER container (NumPy 1.26, spaCy + en_core_web_trf)
  - Shared bind-mounts: ./in, ./out, ./logs, ./config

DIRECTORY & ARTIFACTS
Project root:
.
├── in/                                   # input media
├── out/<MovieName>/                      # per-title outputs
│   ├── <name>.initial_prompt.txt
│   ├── <name>.combined.initial_prompt.txt
│   ├── <name>.combined.initial_prompt.md  # YAML + prompt
│   ├── asr/                               # WhisperX artifacts
│   ├── en_merged/<name>.merged.srt
│   ├── bias/*.bias.window.####.json
│   ├── entities_spacy.json / .md          # if NER enabled/run
│   ├── diarization_stats.json / .md
│   ├── <name>.rttm
│   ├── <name>.subs.mp4  (fallback: .mkv)
│   └── manifest.json
├── logs/YYYYMMDD_HHMMSS/                  # timestamped run logs
│   ├── manifest.json
│   ├── entities_spacy.json
│   └── (any QC summaries)
├── scripts/ (bootstrap, preflight, run, helpers)
├── src/cp-whisperx-app/ (Python pipeline)
├── config/.env                            # all tunables
├── config/secrets.json                    # tokens/keys (HF/TMDB/pyannote)
└── canon_map.yaml                         # optional canonical map

CONFIGURATION (./config/.env — comments included)
- INPUT_FILE or INPUT_URL (URL auto-downloads to ./in before run)
- OUTPUT_ROOT, LOG_ROOT, SECRETS_PATH, SPEAKER_MAP, CANON_MAP
- PREP_PROMPT, AUTO_CONTINUE, CLIP_VIDEO, CLIP_MINUTES
- WINDOW_SECONDS, STRIDE_SECONDS, BIAS_TOPK, BIAS_DECAY
- INFER_TMDB=true|false
- SECOND_PASS_ENABLED=true|false; SECOND_PASS_BACKEND=opus-mt|mbart50|nllb200|none
- QG_ENABLED, QG_THRESHOLD, QG_FALLBACKS
- LYRIC_DETECT_ENABLED, LYRIC_THRESHOLD, LYRIC_STYLE
- NER_ENABLED=true|false; NER_PRESET=en_core_web_trf
- DEVICE_WHISPERX, DEVICE_DIARIZATION, DEVICE_SECOND_PASS, DEVICE_SPACY
- SRC_LANG=hi, TGT_LANG=en, OUTPUT_PLAINTEXT=true|false
All code must read these values via a config loader (not os.environ directly).

SECRETS (./config/secrets.json)
{
  "hf_token": "<Hugging Face personal access token (Read)>",
  "tmdb_api_key": "<TMDB API key>",
  "pyannote_token": "<HF token with access to pyannote/speaker-diarization>"
}
README must include manual curl checks and links:
- TMDB key: https://www.themoviedb.org/settings/api  (probe /search/movie)
- HF token: https://huggingface.co/settings/tokens     (probe whoami-v2)
- pyannote access: https://huggingface.co/pyannote/speaker-diarization (“Access repository”), then token probe on the model API.

PIPELINE (authoritative order)
1) Filename parsing → infer title + optional year; robust to noisy names (e.g., JO_JEETA_WOHI_SIKANDAR_1992.mp4, Satte_Pe_Satta_(1982).mp4).
2) Era detection → load per-era lexicon (1950s-60s, 70s, 80s, 90s, 2000s, 2010s, 2020s).
3) TMDB enrichment → append cast/crew to combined prompt.
4) Prompt assembly → filename/TMDB + era lexicon + any user prompt; write initial_prompt.* files.
5) Rolling windowed prompt injection (45s windows, 15s stride) → per-window compact bias prompt to stabilize names/places.
6) ASR+Translate via WhisperX with alignment (CPU int8 default on Apple Silicon).
7) Diarization (pyannote); write .rttm and diarization stats (optional speaker map SPEAKER_00→Name).
8) Two-pass merge → preserve timings; refine English via transformers backend; quality-gate reruns on weak lines.
9) NER (spaCy transformer) → entities_spacy.json/.md; build canonical map for PER/ORG/GPE.
10) NER-guided canonicalization of SRT + punctuation/case polish pass.
11) Mux QC → MP4 with mov_text; if soft-sub fails, mkvmerge fallback.
12) Packaging → .subs.mp4/.mkv + manifest.json; write all run artifacts/logs to ./logs/<timestamp>/.

LOGGING & QC
- Uniform format: “[timestamp] [module] [LEVEL] message”.
- Write manifest.json summarizing inputs, devices (with fallbacks), outputs, TMDB hit/miss, and durations.
- Bias window JSONs saved under out/<Movie>/bias/.
- Preflight must print system deps, Python deps presence, and secrets presence/validation (HTTP status), then READY/FAIL.

SCRIPTS & DOCS
- bootstrap.py → install Python deps; warn about system deps (ffmpeg/mkvtoolnix); optionally download spaCy model when NER_ENABLED=true.
- preflight.py → verify ffmpeg/mkvmerge, Python modules (whisperx, transformers, PyYAML, pysubs2, tqdm, python-dotenv, requests), config presence, INPUT_FILE or INPUT_URL set, secrets existence; perform online token checks (TMDB/HF/pyannote) and report statuses.
- run_pipeline.py → execute the full pipeline honoring .env.
- README.md → Quickstart at top, complete parameter list, secrets acquisition + manual checks, and container instructions (ASR vs NER split).

CONTAINERS (resolve NumPy conflicts cleanly)
- ASR container: NumPy 2.x, WhisperX 3.7.x, pyannote-audio 3.3.x, CPU-first.
- NER container: NumPy 1.26.x, spaCy 3.7.x + en_core_web_trf.
- docker-compose binds ./in, ./out, ./logs, ./config; run “asr” first, then “ner” on produced SRT to emit entities_spacy.json into logs/<timestamp>/.

STYLE & NON-NEGOTIABLES
- Most logic in Python; shell only for orchestration.
- No reliance on exported env vars; always read ./config/.env + ./config/secrets.json.
- Defaults are chosen for stability and accuracy on Apple Silicon; GPU/MPS use is optional and must gracefully fall back to CPU without crashing.
- Never silently drop artifacts; if a step is skipped (e.g., missing pyannote), record it in manifest/logs.

FUTURE UPGRADES (keep interfaces ready)
- Dynamic scene-aware bias weighting by recent mentions.
- Music/lyric detection for lyric-style formatting.
- Quality gates to auto-rerun tough windows with larger models.

OUTPUT EXPECTATION
Deliver code, scripts, and docs that strictly adhere to this Master Prompt. Any new feature must integrate with: .env config, secrets.json, timestamped logs, manifest.json, and containerized split (ASR vs NER).

We will revise the entire project based on workflow-arch.txt and rebuild the complete pipeline in Docker. This process begins with the [FFmpeg Demux] step and ends with the [FFmpeg Mux] step, with each step housed in its own Docker container. We'll start by creating a base Docker container and then incrementally build all subsequent containers to keep their size minimal. Once finished, the Docker images will be pushed to the Docker registry. The Docker Compose configuration must pull or run images using registry tags. Before running the pipeline, a preflight script will execute for validation, ensuring all components operate correctly. All logs will be saved in the log directory, and all hardcoded values will be sourced from the .env file located in the config/ directory. The .env file should also include configuration for the log type switch, such as debug, info, etc.
At the beginning of pipeline create a subdirectory inside out/ directory  with the same name as filename from in/ directory and all container output must be stored inside the subdirectory.
