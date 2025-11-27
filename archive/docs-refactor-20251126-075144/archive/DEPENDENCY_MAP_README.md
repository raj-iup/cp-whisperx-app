# Codebase Dependency Map - Quick Reference

## 📚 Documentation Files Created

1. **`docs/CODEBASE_DEPENDENCY_MAP.md`** (17KB)
   - Comprehensive text documentation
   - Complete dependency tree
   - Call graphs and flow diagrams
   - Module imports and relationships

2. **`CODEBASE_VISUAL_MAP.sh`** (12KB)
   - ASCII art visual diagram
   - Tree-based dependency visualization
   - Stage-by-stage flow charts
   - Quick reference format

## 🚀 Quick View

```bash
# View comprehensive documentation
cat docs/CODEBASE_DEPENDENCY_MAP.md

# View visual ASCII diagram
./CODEBASE_VISUAL_MAP.sh
```

## 📊 Key Findings

### Main Orchestration Scripts

| Script | Location | Purpose | Key Dependencies |
|--------|----------|---------|------------------|
| **bootstrap.sh** | Root → scripts/bootstrap.sh | Setup 8 venvs | 8 requirements-*.txt, common-logging.sh |
| **prepare-job.sh** | Root → scripts/prepare-job.py | Create job | shared/{logger,environment_manager}.py |
| **run-pipeline.sh** | Root → scripts/run-pipeline.py | Execute pipeline | All stage scripts, whisper_backends.py |

### Virtual Environment Mapping

| Venv | Requirements File | Used By Stages |
|------|-------------------|----------------|
| venv/common | requirements-common.txt | demux, mux, subtitle_gen |
| venv/whisperx | requirements-whisperx.txt | ASR (CTranslate2), alignment |
| venv/mlx | requirements-mlx.txt | ASR (MLX), alignment |
| venv/pyannote | requirements-pyannote.txt | VAD, diarization |
| venv/demucs | requirements-demucs.txt | Source separation, lyrics |
| venv/indictrans2 | requirements-indictrans2.txt | IndicTrans2 translation |
| venv/nllb | requirements-nllb.txt | NLLB translation |
| venv/llm | requirements-llm.txt | LLM translation |

### Config File Flow

```
bootstrap.sh
    ↓ creates
config/hardware_cache.json
    ↓ used by
prepare-job.py
    ↓ creates
out/<path>/job.json + .job-*.env
    ↓ used by
run-pipeline.py
    ↓ executes stages
```

### Shared Infrastructure

| Module | Location | Used By | Purpose |
|--------|----------|---------|---------|
| PipelineLogger | shared/logger.py | All scripts | Structured logging |
| EnvironmentManager | shared/environment_manager.py | prepare-job, run-pipeline | Venv management |
| Config | scripts/config_loader.py | prepare-job, run-pipeline | Config loading |
| common-logging.sh | scripts/common-logging.sh | All bash scripts | Bash logging utils |

### Stage Scripts (12+)

1. **demux.py** - Audio extraction (venv-common)
2. **source_separation.py** - Demucs separation (venv-demucs)
3. **pyannote_vad.py** - Voice activity (venv-pyannote)
4. **whisper_backends.py** - ASR orchestration (venv-whisperx/mlx)
5. **mlx_alignment.py** - Word alignment (venv-mlx)
6. **hallucination_removal.py** - Clean transcripts (common)
7. **lyrics_detection.py** - Song detection (venv-demucs)
8. **indictrans2_translator.py** - Indic translation (venv-indictrans2)
9. **nllb_translator.py** - NLLB translation (venv-nllb)
10. **subtitle_gen.py** - SRT generation (common)
11. **mux.py** - Video muxing (venv-common)
12. **beam_search_comparison.py** - Quality testing (venv-indictrans2)

### Helper Modules (15+)

- **filename_parser.py** - Parse media filenames
- **tmdb_enrichment.py** - Fetch metadata
- **ner_extraction.py** - Extract entities
- **glossary_builder.py** - Build glossaries
- **bias_injection.py** - Name prompting
- **config_loader.py** - Config management
- And more...

## 📈 Statistics

- **Total Scripts**: 50+
- **Virtual Environments**: 8
- **Requirements Files**: 8
- **Config Files**: 4
- **Stage Scripts**: 12+
- **Helper Scripts**: 15+
- **Shared Modules**: 3

## 🔄 Typical Workflow

```
1. Bootstrap (one-time setup)
   ./bootstrap.sh
   ↓ Creates all 8 virtual environments
   ↓ Generates hardware_cache.json

2. Prepare Job (per video)
   ./prepare-job.sh --input "movie.mp4"
   ↓ Creates job directory
   ↓ Generates job.json + .job-*.env

3. Run Pipeline (per job)
   ./run-pipeline.sh -j <job-id>
   ↓ Executes 9 stages sequentially
   ↓ Each stage uses its dedicated venv
   ↓ Updates manifest.json after each stage
   ↓ Generates subtitles and final output
```

## 🎯 Key Insights

1. **Isolation**: Each stage runs in its own virtual environment
2. **Modularity**: Scripts are independent and reusable
3. **Logging**: Centralized logging through shared/logger.py
4. **Config**: Hardware detection flows through all stages
5. **Flexibility**: Can run stages independently or as pipeline
6. **Debugging**: Logs per stage in out/<path>/logs/

## 📖 Further Reading

- **Full Documentation**: `docs/CODEBASE_DEPENDENCY_MAP.md`
- **Visual Diagram**: Run `./CODEBASE_VISUAL_MAP.sh`
- **Stage Details**: See comments in individual stage scripts
- **Config Reference**: Check `config/secrets.example.json`

---

**Generated**: 2025-11-25  
**Version**: 1.0  
**Coverage**: Complete dependency tree for bootstrap, prepare-job, run-pipeline
