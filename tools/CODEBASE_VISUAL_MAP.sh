#!/bin/bash
# Generate Visual Dependency Map

cat << 'EOF'

╔══════════════════════════════════════════════════════════════════════════════╗
║                    CP-WHISPERX-APP DEPENDENCY MAP                             ║
║                         Visual Architecture                                   ║
╚══════════════════════════════════════════════════════════════════════════════╝


┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 1. BOOTSTRAP PHASE - Environment Setup                                      ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

    ./bootstrap.sh
          │
          ├──► exec scripts/bootstrap.sh
          │           │
          │           ├─── source scripts/common-logging.sh
          │           │
          │           ├─── read config/secrets.json (optional)
          │           │
          │           ├─── create .venv-common       ◄── requirements-common.txt
          │           ├─── create .venv-whisperx     ◄── requirements-whisperx.txt
          │           ├─── create .venv-mlx          ◄── requirements-mlx.txt
          │           ├─── create .venv-pyannote     ◄── requirements-pyannote.txt
          │           ├─── create .venv-demucs       ◄── requirements-demucs.txt
          │           ├─── create .venv-indictrans2  ◄── requirements-indictrans2.txt
          │           ├─── create .venv-nllb         ◄── requirements-nllb.txt
          │           ├─── create .venv-llm          ◄── requirements-llm.txt
          │           │
          │           ├─── write config/hardware_cache.json
          │           │
          │           └─── (optional) ./cache-models.sh


┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 2. PREPARE-JOB PHASE - Job Creation                                         ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

    ./prepare-job.sh
          │
          ├──► source scripts/common-logging.sh
          │
          └──► python3 scripts/prepare-job.py
                        │
                        ├─── import shared/logger.py
                        ├─── import shared/environment_manager.py
                        ├─── import scripts/config_loader.py
                        ├─── import scripts/filename_parser.py
                        │
                        ├─── read config/hardware_cache.json
                        ├─── read config/secrets.json (optional)
                        │
                        └─── create out/YYYY/MM/DD/<user>/<job>/
                                    ├── job.json
                                    ├── manifest.json
                                    ├── .job-*.env
                                    ├── media/<file>
                                    └── logs/


┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 3. RUN-PIPELINE PHASE - Pipeline Execution                                  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

    ./run-pipeline.sh
          │
          ├──► source scripts/common-logging.sh
          │
          └──► python3 scripts/run-pipeline.py
                        │
                        ├─── import shared/logger.py
                        ├─── import shared/environment_manager.py
                        ├─── import scripts/config_loader.py
                        │
                        ├─── read out/<path>/job.json
                        ├─── read out/<path>/manifest.json
                        ├─── read out/<path>/.job-*.env
                        │
                        └─── Execute Stages:
                                │
                                ├─► Stage 1: demux
                                │   └── .venv-common/bin/python scripts/demux.py
                                │
                                ├─► Stage 2: source_separation
                                │   └── .venv-demucs/bin/python scripts/source_separation.py
                                │
                                ├─► Stage 3: pyannote_vad
                                │   └── .venv-pyannote/bin/python scripts/pyannote_vad.py
                                │
                                ├─► Stage 4: asr
                                │   ├── Backend: WhisperX (.venv-whisperx)
                                │   └── Backend: MLX (.venv-mlx)
                                │        └── uses scripts/whisper_backends.py
                                │
                                ├─► Stage 5: alignment
                                │   └── .venv-mlx/bin/python scripts/mlx_alignment.py
                                │
                                ├─► Stage 5b: hallucination_removal
                                │   └── python scripts/hallucination_removal.py
                                │
                                ├─► Stage 6: lyrics_detection
                                │   └── .venv-demucs/bin/python scripts/lyrics_detection.py
                                │
                                ├─► Stage 7: translation
                                │   ├── .venv-indictrans2/bin/python scripts/indictrans2_translator.py
                                │   └── .venv-nllb/bin/python scripts/nllb_translator.py
                                │
                                ├─► Stage 8: subtitle_generation
                                │   └── python scripts/subtitle_gen.py
                                │
                                └─► Stage 9: mux
                                    └── .venv-common/bin/python scripts/mux.py


┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ SHARED INFRASTRUCTURE                                                        ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

    shared/
      ├── logger.py
      │   └── class PipelineLogger
      │       └── Used by: prepare-job.py, run-pipeline.py, all stage scripts
      │
      ├── environment_manager.py
      │   └── class EnvironmentManager
      │       └── Used by: prepare-job.py, run-pipeline.py
      │
      └── manifest.py
          └── Job tracking and status
              └── Used by: run-pipeline.py

    scripts/
      ├── config_loader.py
      │   └── class Config
      │       └── Used by: prepare-job.py, run-pipeline.py
      │
      ├── filename_parser.py
      │   └── def parse_filename()
      │       └── Used by: prepare-job.py
      │
      └── common-logging.sh
          └── Bash logging functions
              └── Used by: bootstrap.sh, prepare-job.sh, run-pipeline.sh


┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ VIRTUAL ENVIRONMENT → STAGE MAPPING                                         ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

    .venv-common
      └─► demux, mux, subtitle_gen, logging

    .venv-whisperx
      └─► ASR (CTranslate2 backend), alignment

    .venv-mlx
      └─► ASR (MLX backend - Apple Silicon), alignment

    .venv-pyannote
      └─► Voice activity detection, diarization

    .venv-demucs
      └─► Source separation, lyrics detection

    .venv-indictrans2
      └─► IndicTrans2 translation (Indic languages)

    .venv-nllb
      └─► NLLB translation (200+ languages)

    .venv-llm
      └─► LLM translation (Claude, GPT)


┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ CONFIG FILES FLOW                                                            ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

    config/secrets.json (optional, user-created)
      └─► Used by: bootstrap.sh, prepare-job.py
          └─► Contains: HF_TOKEN, TMDB_API_KEY, API keys

    config/hardware_cache.json (generated)
      └─► Created by: bootstrap.sh
          └─► Used by: prepare-job.py, run-pipeline.py
              └─► Contains: device (cpu/cuda/mps), GPU info

    out/<path>/job.json (generated per job)
      └─► Created by: prepare-job.py
          └─► Used by: run-pipeline.py
              └─► Contains: job config, languages, workflow

    out/<path>/.job-*.env (generated per job)
      └─► Created by: prepare-job.py
          └─► Used by: run-pipeline.py stages
              └─► Contains: environment variables for stages

    out/<path>/manifest.json (generated & updated)
      └─► Created by: prepare-job.py
          └─► Updated by: run-pipeline.py
              └─► Contains: stage status, timing, errors


┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ REQUIREMENTS → VENV → PACKAGES                                              ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

    requirements-common.txt
      └─► .venv-common
          └─► ffmpeg-python, pydub, python-json-logger

    requirements-whisperx.txt
      └─► .venv-whisperx
          └─► whisperx, faster-whisper, torch

    requirements-mlx.txt
      └─► .venv-mlx
          └─► mlx-whisper, mlx

    requirements-pyannote.txt
      └─► .venv-pyannote
          └─► pyannote.audio, torch

    requirements-demucs.txt
      └─► .venv-demucs
          └─► demucs, torch

    requirements-indictrans2.txt
      └─► .venv-indictrans2
          └─► transformers, IndicTransToolkit, torch

    requirements-nllb.txt
      └─► .venv-nllb
          └─► transformers, torch

    requirements-llm.txt
      └─► .venv-llm
          └─► anthropic, openai


┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ SCRIPT CALL CHAIN                                                            ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

    USER WORKFLOW:
    
    1. ./bootstrap.sh
          ↓
       [Creates 8 virtual environments]
          ↓
    2. ./prepare-job.sh --input "movie.mp4"
          ↓
       [Creates job directory & config]
          ↓
    3. ./run-pipeline.sh -j <job-id>
          ↓
       [Executes 9 stages sequentially]
          ↓
       [Generates subtitles & final output]


    SCRIPT DEPENDENCIES:
    
    bootstrap.sh
      └── scripts/bootstrap.sh
          └── scripts/common-logging.sh

    prepare-job.sh
      ├── scripts/common-logging.sh
      └── scripts/prepare-job.py
          ├── shared/logger.py
          ├── shared/environment_manager.py
          ├── scripts/config_loader.py
          └── scripts/filename_parser.py

    run-pipeline.sh
      ├── scripts/common-logging.sh
      └── scripts/run-pipeline.py
          ├── shared/logger.py
          ├── shared/environment_manager.py
          ├── scripts/config_loader.py
          └── scripts/whisper_backends.py
              ├── whisperx
              └── mlx_whisper


┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ FILE COUNT SUMMARY                                                           ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

    Root Scripts:              6  (bootstrap, prepare, run × 2 each)
    Virtual Environments:      8  (.venv-*)
    Requirements Files:        8  (requirements-*.txt)
    Config Files:             4  (config/*.json)
    Shared Modules:           3  (shared/*.py)
    Stage Scripts:           12+ (scripts/*stage*.py)
    Helper Scripts:          15+ (scripts/*.py)
    
    Total Files Involved:    50+


╔══════════════════════════════════════════════════════════════════════════════╗
║                            END OF MAP                                         ║
╚══════════════════════════════════════════════════════════════════════════════╝

EOF
