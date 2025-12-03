# Stage 02: TMDB Integration

**Status:** ✅ Integrated (Phase 4, Task 4.1)  
**Date:** 2025-12-03  
**Effort:** 8 hours

## Overview

The TMDB enrichment stage fetches movie metadata from The Movie Database (TMDB) and generates glossaries for ASR biasing and translation preservation.

## Integration Details

### File Structure

```
scripts/
  tmdb_enrichment_stage.py    # Main stage implementation
  tmdb.py                     # Wrapper for backward compatibility

shared/
  tmdb_client.py              # TMDB API client
  tmdb_loader.py              # Data loader utilities
  tmdb_cache.py               # Caching layer

tests/stages/
  test_tmdb_integration.py    # Integration tests
  test_tmdb_stage.py          # Unit tests (existing)
```

### Stage Interface

The stage implements the standard `run_stage()` interface:

```python
def run_stage(job_dir: Path, stage_name: str = "02_tmdb") -> int:
    """
    Run TMDB enrichment stage
    
    Args:
        job_dir: Job output directory
        stage_name: Stage name (default: "02_tmdb")
    
    Returns:
        Exit code: 0 for success, 1 for failure
    """
```

### Input/Output

**Input:**
- Movie title from config (`FILM_TITLE`)
- Release year from config (`FILM_YEAR`, optional)
- Or auto-detect from job config or filename

**Output (in `job_dir/02_tmdb/`):**
- `enrichment.json` - Full TMDB metadata
- `glossary_asr.json` - Terms for ASR biasing
- `glossary_translation.json` - Terms for translation preservation
- `glossary.json` - Human-readable full glossary
- `stage.log` - Stage execution log
- `manifest.json` - I/O tracking manifest

### Configuration

Add to `config/.env.pipeline`:

```bash
# TMDB Configuration
TMDB_API_KEY=your_api_key_here
FILM_TITLE=Movie Title
FILM_YEAR=2020  # optional
```

### Usage

**Pipeline Mode:**
```python
from scripts.tmdb_enrichment_stage import run_stage
from pathlib import Path

exit_code = run_stage(Path("out/job_20250103_0001"), "02_tmdb")
if exit_code != 0:
    print("TMDB enrichment failed")
```

**CLI Mode:**
```bash
# With config
python scripts/tmdb_enrichment_stage.py \
  --job-dir out/job_20250103_0001 \
  --title "3 Idiots" \
  --year 2009

# Auto-detect title
python scripts/tmdb_enrichment_stage.py \
  --job-dir out/job_20250103_0001
```

## Compliance

✅ **100% Compliant** with DEVELOPER_STANDARDS.md:

- ✅ Uses `logger` instead of `print()` (except CLI error messages)
- ✅ Imports organized (Standard/Third-party/Local)
- ✅ StageIO pattern with `enable_manifest=True`
- ✅ Tracks all inputs/outputs
- ✅ Writes to `io.stage_dir` only
- ✅ Uses `load_config()` not `os.getenv()`
- ✅ Type hints on all functions
- ✅ Comprehensive docstrings
- ✅ Error handling with `exc_info=True`

## Features

### 1. Automatic Title Detection

If no title is provided, the stage attempts to detect it from:
1. `job_config.json` (`movie_title` or `title` field)
2. Audio filename in `01_demux/` directory

### 2. Graceful Degradation

The stage can be skipped without failing the pipeline:
- If no TMDB API key is configured
- If no movie title is available
- If movie is not found on TMDB

Empty output files are created to maintain pipeline consistency.

### 3. Glossary Generation

Generates three types of glossaries from TMDB metadata:

**ASR Glossary** (`glossary_asr.json`):
- Cast member names
- Character names
- Crew names (director, writer, etc.)
- Movie title and original title
- Used for ASR biasing to improve name recognition

**Translation Glossary** (`glossary_translation.json`):
- Name preservation mappings (name → name)
- Prevents translation of proper nouns
- Used in translation stage

**Full Glossary** (`glossary.json`):
- Complete metadata with cast, crew, genres
- Human-readable format
- For reference and debugging

### 4. Manifest Tracking

Tracks all I/O operations:
- Input: None (fetches from API)
- Outputs: enrichment.json, glossary files
- Configuration: title, year, API status
- Metadata: TMDB ID, cast/crew counts

### 5. Stage Logging

Separate stage log (`02_tmdb/stage.log`) contains:
- API search queries
- Movie matches
- Metadata fetch operations
- Glossary generation details
- Error messages with full context

## Testing

Run integration tests:

```bash
# All TMDB tests
pytest tests/stages/test_tmdb_integration.py -v

# Specific test
pytest tests/stages/test_tmdb_integration.py::TestTMDBStageIntegration::test_run_stage_creates_stage_io -v

# With coverage
pytest tests/stages/test_tmdb_integration.py --cov=scripts.tmdb_enrichment_stage
```

## Pipeline Integration

### Add to Pipeline Orchestrator

Add to `scripts/run-pipeline.py`:

```python
def run_tmdb_enrichment(self):
    """Run TMDB enrichment stage"""
    if not self.config.get("TMDB_ENABLED", "true").lower() == "true":
        self.logger.info("TMDB stage disabled, skipping")
        return
    
    from scripts.tmdb_enrichment_stage import run_stage
    
    self.logger.info("Running TMDB enrichment...")
    exit_code = run_stage(self.job_dir, "02_tmdb")
    
    if exit_code != 0:
        raise StageExecutionError("TMDB enrichment failed")
    
    self.logger.info("✓ TMDB enrichment complete")
```

### Workflow Integration

Update workflow (if `transcribe`, `translate`, or `subtitle`):

```python
# After demux, before ASR
if workflow in ["translate", "subtitle"]:
    self.run_tmdb_enrichment()
```

### Enable/Disable

Control via config:

```bash
# Enable (default)
TMDB_ENABLED=true

# Disable
TMDB_ENABLED=false
```

## Known Issues

1. **Dependency:** Requires `tmdbv3api` package (in requirements/base.txt)
2. **API Key:** Requires valid TMDB API key
3. **Rate Limits:** TMDB has rate limits (40 requests per 10 seconds)
4. **Cache:** Caching implemented in `shared/tmdb_cache.py` (24-hour TTL)

## Future Enhancements

1. **Soundtrack Integration:** Fetch soundtrack data for music detection
2. **Multi-language Support:** Fetch metadata in target language
3. **Persistent Cache:** Save cache across pipeline runs
4. **Fuzzy Matching:** Better title matching for difficult names
5. **Batch Mode:** Process multiple films efficiently

## References

- [TMDB API Documentation](https://developers.themoviedb.org/3)
- [Task 4.1 Specification](../ARCHITECTURE_IMPLEMENTATION_ROADMAP.md#41-integrate-tmdb-enrichment-stage-8-hours)
- [DEVELOPER_STANDARDS.md](../developer/DEVELOPER_STANDARDS.md)
- [StageIO Pattern](../developer/DEVELOPER_STANDARDS.md#26-stage-io-pattern)

## Deliverables

- [x] Script follows StageIO pattern
- [x] `run_stage()` wrapper function added
- [x] Configuration via `load_config()`
- [x] Integration tests created
- [x] Documentation complete
- [x] 100% compliance verified
- [ ] Add to pipeline orchestrator (next step)
- [ ] Add to workflows (next step)
- [ ] End-to-end testing (next step)

---

**Status:** Ready for pipeline integration  
**Next Steps:** Add stage call to run-pipeline.py orchestrator
