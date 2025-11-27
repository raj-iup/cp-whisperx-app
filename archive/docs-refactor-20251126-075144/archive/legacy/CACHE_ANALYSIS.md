# Cache Architecture Analysis & Optimization Recommendations

## Executive Summary

This document analyzes how the CP-WhisperX-App caches ML models and artifacts, and provides recommendations for optimal cache utilization.

**Current State**: The application uses **multiple cache locations** with **inconsistent patterns**, leading to potential redundancy and confusion.

**Key Finding**: Cache directories are scattered across:
1. `shared/model-cache/` - Legacy location (partially used)
2. `.cache/` - Project-local cache (TORCH_HOME, HF_HOME)
3. `~/.cache/huggingface/` - User home cache (default fallback)
4. Application-specific caches in `out/` directory

---

## 1. Current Cache Flow

### 1.1 Bootstrap Phase (`bootstrap.sh` → `scripts/bootstrap.sh`)

**What it does:**
- Creates 5 virtual environments (`venv/common`, `venv/whisperx`, `venv/mlx`, `venv/indictrans2`, `venv/nllb`)
- Installs Python packages in each environment
- Creates `config/hardware_cache.json` with environment mappings
- **Does NOT** explicitly set cache directories
- **Does NOT** pre-download models (optional via `model_downloader.py`)

**Cache Configuration:**
```bash
# NO explicit cache path setting in bootstrap.sh
# Environments rely on Python package defaults
```

### 1.2 Model Downloader (`shared/model_downloader.py`)

**When used** (optional during bootstrap):
```python
# Sets cache directories explicitly
cache_dir = project_root / '.cache'
os.environ['TORCH_HOME'] = str(cache_dir / 'torch')
os.environ['HF_HOME'] = str(cache_dir / 'huggingface')
```

**What it downloads:**
- Whisper models (base, large-v3, etc.) → `.cache/torch/`
- Silero VAD → `.cache/torch/hub/`
- spaCy models → system Python site-packages
- PyAnnote models → `.cache/huggingface/hub/`
- MLX Whisper → downloaded on first use

**Current Implementation:**
```python
# shared/model_downloader.py:29-30
os.environ['TORCH_HOME'] = str(cache_dir / 'torch')
os.environ['HF_HOME'] = str(cache_dir / 'huggingface')
```

### 1.3 Prepare-Job Phase (`prepare-job.sh` → `scripts/prepare-job.py`)

**What it does:**
- Validates environment setup
- Creates job directory structure
- Generates job configuration
- **Does NOT** set cache environment variables
- **Does NOT** pre-load models

**Cache Information Passed:**
- ✗ No cache path passed to job config
- ✗ No environment variables set
- ✓ Environment paths via `hardware_cache.json`

### 1.4 Pipeline Execution (`run-pipeline.sh` → `scripts/run-pipeline.py`)

**Environment Manager** (`shared/environment_manager.py`):
```python
# Lines 184-187
env = os.environ.copy()
env["VIRTUAL_ENV"] = str(self.get_environment_path(env_name))
env["PATH"] = f"{self.get_environment_path(env_name) / 'bin'}:{env['PATH']}"
# NO TORCH_HOME or HF_HOME set here!
```

**WhisperX Backend** (`scripts/whisper_backends.py`):
```python
# Line 111 - Falls back to default if not set
cache_dir = os.environ.get('TORCH_HOME', str(Path.home() / '.cache' / 'torch'))
```

**Problem**: Each pipeline stage relies on environment variables that may not be set consistently.

---

## 2. Cache Location Inventory

### 2.1 ML Model Caches

| Cache Type | Current Location | Set By | Consistency |
|-----------|-----------------|--------|-------------|
| Whisper models | `~/.cache/torch/hub/` OR `.cache/torch/` | `TORCH_HOME` env var | ❌ Inconsistent |
| HuggingFace models | `~/.cache/huggingface/` OR `.cache/huggingface/` | `HF_HOME` env var | ❌ Inconsistent |
| MLX Whisper | `~/.cache/mlx_whisper/` | MLX library default | ⚠️ Library-controlled |
| spaCy models | Python site-packages | spaCy default | ✅ Consistent |

### 2.2 Application Caches

| Cache Type | Location | Configuration | Purpose |
|-----------|----------|---------------|---------|
| TMDB metadata | `out/tmdb_cache/` | `config/.env.pipeline` | Movie/TV metadata |
| MusicBrainz | `out/musicbrainz_cache/` | `config/.env.pipeline` | Audio metadata |
| Glossary | `glossary/cache/` | `config/.env.pipeline` | Translation glossaries |
| Legacy model cache | `shared/model-cache/` | Hardcoded | ⚠️ Partially abandoned |

### 2.3 Current Directory Structure

```
cp-whisperx-app/
├── .cache/                    # Project-local ML cache (when set)
│   ├── torch/                 # Whisper, VAD models
│   └── huggingface/           # HF transformers
├── shared/
│   └── model-cache/           # Legacy cache (mostly empty)
│       └── torch/
├── out/
│   ├── tmdb_cache/            # TMDB API cache
│   └── musicbrainz_cache/     # MusicBrainz API cache
├── glossary/cache/            # Translation glossaries
└── config/
    └── hardware_cache.json    # Environment mappings
```

---

## 3. Problems with Current Implementation

### 3.1 Cache Location Inconsistency

**Problem**: Models may be downloaded to different locations depending on whether `TORCH_HOME`/`HF_HOME` are set.

**Scenarios**:
1. **Bootstrap with model_downloader**: Models in `.cache/`
2. **Bootstrap without model_downloader**: Models in `~/.cache/`
3. **Direct pipeline run**: Falls back to `~/.cache/`

**Impact**:
- Wasted disk space (duplicate downloads)
- Slower first-run performance
- Confusion about cache location

### 3.2 Environment Variable Not Propagated

**Problem**: `environment_manager.py` does NOT set `TORCH_HOME` or `HF_HOME` when running pipeline stages.

```python
# shared/environment_manager.py:184-187
env = os.environ.copy()
env["VIRTUAL_ENV"] = str(self.get_environment_path(env_name))
env["PATH"] = f"{self.get_environment_path(env_name) / 'bin'}:{env['PATH']}"
# Missing: env["TORCH_HOME"] = ...
# Missing: env["HF_HOME"] = ...
```

**Impact**: Each stage script must independently set cache directories or fall back to defaults.

### 3.3 No Centralized Cache Configuration

**Problem**: No single source of truth for cache paths.

**Current State**:
- `model_downloader.py` hardcodes `.cache/`
- `whisper_backends.py` falls back to `~/.cache/torch/`
- No configuration file for cache paths

### 3.4 Legacy `shared/model-cache/` Directory

**Problem**: Directory exists but is mostly unused.

```bash
$ ls -la shared/model-cache/
drwxr-xr-x  3 rpatel  staff   96 Nov  8 01:23 .
drwxr-xr-x  3 rpatel  staff   96 Nov  8 01:23 torch
```

**Impact**: Confusing for users and developers.

---

## 4. Recommendations for Optimal Caching

### 4.1 **CRITICAL**: Centralize Cache Path Configuration

**Add to `config/hardware_cache.json`**:

```json
{
  "cache": {
    "base_dir": ".cache",
    "torch_home": ".cache/torch",
    "hf_home": ".cache/huggingface",
    "mlx_home": ".cache/mlx",
    "application_caches": {
      "tmdb": "out/tmdb_cache",
      "musicbrainz": "out/musicbrainz_cache",
      "glossary": "glossary/cache"
    }
  }
}
```

**Rationale**:
- Single source of truth
- Configurable per deployment
- Easy to change for testing or NAS storage

### 4.2 **CRITICAL**: Propagate Cache Paths via Environment Manager

**Update `shared/environment_manager.py:run_in_environment()`**:

```python
def run_in_environment(self, env_name: str, command: List[str], **kwargs):
    python_exe = self.get_python_executable(env_name)
    
    # Set up environment variables
    env = os.environ.copy()
    env["VIRTUAL_ENV"] = str(self.get_environment_path(env_name))
    env["PATH"] = f"{self.get_environment_path(env_name) / 'bin'}:{env['PATH']}"
    
    # ✅ ADD CACHE PATHS
    cache_config = self.hardware_cache.get("cache", {})
    if "torch_home" in cache_config:
        env["TORCH_HOME"] = str(self.project_root / cache_config["torch_home"])
    if "hf_home" in cache_config:
        env["HF_HOME"] = str(self.project_root / cache_config["hf_home"])
        env["TRANSFORMERS_CACHE"] = str(self.project_root / cache_config["hf_home"])
    if "mlx_home" in cache_config:
        env["MLX_CACHE_DIR"] = str(self.project_root / cache_config["mlx_home"])
    
    return subprocess.run(command, env=env, **kwargs)
```

**Rationale**:
- Consistent cache location across all pipeline stages
- Reduces redundant downloads
- Easier troubleshooting

### 4.3 Set Cache Paths During Bootstrap

**Update `scripts/bootstrap.sh`** (after creating hardware_cache.json):

```bash
# After line 259 (hardware_cache.json creation)
log_section "CACHE CONFIGURATION"

# Create cache directories
mkdir -p "$PROJECT_ROOT/.cache/torch"
mkdir -p "$PROJECT_ROOT/.cache/huggingface"
mkdir -p "$PROJECT_ROOT/.cache/mlx"

log_success "Cache directories created: .cache/"

# Set environment variables for current session
export TORCH_HOME="$PROJECT_ROOT/.cache/torch"
export HF_HOME="$PROJECT_ROOT/.cache/huggingface"
export TRANSFORMERS_CACHE="$PROJECT_ROOT/.cache/huggingface"
export MLX_CACHE_DIR="$PROJECT_ROOT/.cache/mlx"

log_info "Cache environment variables set for this session"
log_info "  TORCH_HOME=$TORCH_HOME"
log_info "  HF_HOME=$HF_HOME"
```

**Rationale**:
- Establishes cache location from the start
- Model downloader uses correct paths
- User-facing clarity

### 4.4 Pre-Download Critical Models During Bootstrap

**Update `scripts/bootstrap.sh`** (add before "BOOTSTRAP COMPLETE"):

```bash
# Optional: Pre-download models
log_section "MODEL CACHING (OPTIONAL)"
echo ""
log_info "Pre-downloading critical models..."
log_info "This step is optional but recommended for faster first use"
echo ""

# Check if user wants to skip
if [ "${SKIP_MODEL_DOWNLOAD:-false}" != "true" ]; then
    # Activate common environment for model downloader
    source "$PROJECT_ROOT/venv/common/bin/activate"
    
    # Run model downloader
    python "$PROJECT_ROOT/shared/model_downloader.py" \
        --whisper-models base large-v3 \
        --max-workers 2
    
    deactivate
    
    if [ $? -eq 0 ]; then
        log_success "Models cached successfully"
    else
        log_warn "Model download had issues - models will download on first use"
    fi
else
    log_info "Skipping model download (SKIP_MODEL_DOWNLOAD=true)"
    log_info "Models will download automatically on first use"
fi
echo ""
```

**Rationale**:
- Better first-run experience
- Validates download/connectivity during setup
- Optional for CI/CD environments

### 4.5 Remove/Deprecate Legacy `shared/model-cache/`

**Action**:
```bash
# Add to .gitignore
echo "shared/model-cache/" >> .gitignore

# Remove from repository
rm -rf shared/model-cache/

# Update documentation to reference .cache/ instead
```

**Rationale**:
- Reduces confusion
- Single cache location
- Cleaner directory structure

### 4.6 Add Cache Management Commands

**Create `scripts/cache-manager.sh`**:

```bash
#!/usr/bin/env bash
# Cache management utility

case "$1" in
    status)
        echo "Cache Status:"
        du -sh .cache/* 2>/dev/null
        du -sh out/*_cache 2>/dev/null
        ;;
    clear-models)
        rm -rf .cache/torch .cache/huggingface .cache/mlx
        echo "Model caches cleared"
        ;;
    clear-metadata)
        rm -rf out/tmdb_cache out/musicbrainz_cache
        echo "Metadata caches cleared"
        ;;
    clear-all)
        rm -rf .cache out/tmdb_cache out/musicbrainz_cache glossary/cache
        echo "All caches cleared"
        ;;
    *)
        echo "Usage: $0 {status|clear-models|clear-metadata|clear-all}"
        exit 1
        ;;
esac
```

**Rationale**:
- User-friendly cache management
- Easy troubleshooting
- Disk space reclamation

---

## 5. Implementation Priority

### Phase 1: Critical Fixes (Immediate)
1. ✅ **Add cache config to `hardware_cache.json`** (bootstrap.sh)
2. ✅ **Propagate cache env vars in `environment_manager.py`**
3. ✅ **Set cache paths during bootstrap** (bootstrap.sh)

### Phase 2: Optimization (Next Sprint)
4. ✅ **Pre-download models during bootstrap** (optional flag)
5. ✅ **Add cache management utility**
6. ✅ **Update documentation** (docs/BOOTSTRAP.md, docs/TROUBLESHOOTING.md)

### Phase 3: Cleanup (Future)
7. ✅ **Remove `shared/model-cache/`**
8. ✅ **Add cache size monitoring/alerts**
9. ✅ **Support NAS/network cache locations**

---

## 6. Testing Plan

### 6.1 Cache Consistency Test

```bash
# Clean slate
rm -rf .cache ~/.cache/torch ~/.cache/huggingface

# Bootstrap
./bootstrap.sh

# Verify cache location
ls -la .cache/torch/
ls -la .cache/huggingface/

# Run pipeline
./prepare-job.sh in/test.mp4 --transcribe
./run-pipeline.sh -j <job-id>

# Verify no duplicate downloads
ls -la ~/.cache/torch/  # Should be empty or minimal
ls -la ~/.cache/huggingface/  # Should be empty or minimal
```

### 6.2 Environment Variable Propagation Test

```bash
# Add debug logging to environment_manager.py
import os
print(f"TORCH_HOME={os.environ.get('TORCH_HOME', 'NOT SET')}")
print(f"HF_HOME={os.environ.get('HF_HOME', 'NOT SET')}")

# Run pipeline and check logs
./run-pipeline.sh -j <job-id> 2>&1 | grep "TORCH_HOME\|HF_HOME"
```

### 6.3 Multi-Environment Cache Sharing Test

```bash
# Ensure whisperx and mlx environments share cache
# Both should use .cache/torch/ for Whisper models

# Run with whisperx
./prepare-job.sh in/test.mp4 --transcribe
# Check cache size
du -sh .cache/

# Run with mlx (Apple Silicon)
# Should NOT re-download models
./prepare-job.sh in/test2.mp4 --transcribe
# Cache size should be similar
du -sh .cache/
```

---

## 7. Documentation Updates Required

### 7.1 docs/BOOTSTRAP.md

**Add section: "Understanding the Cache"**

```markdown
## Cache Directory Structure

After bootstrap, CP-WhisperX-App uses the following cache locations:

### ML Model Cache (`.cache/`)
- **Location**: `<project-root>/.cache/`
- **Contents**:
  - `torch/` - Whisper models, VAD models (1-5 GB per model)
  - `huggingface/` - Transformer models for translation (2-10 GB)
  - `mlx/` - MLX-specific models (Apple Silicon only)
- **Shared across**: All virtual environments
- **Persistence**: Kept between runs, safe to delete to free space

### Application Cache (`out/`, `glossary/`)
- **TMDB Cache**: `out/tmdb_cache/` - Movie/TV metadata (< 100 MB)
- **MusicBrainz Cache**: `out/musicbrainz_cache/` - Music metadata (< 50 MB)
- **Glossary Cache**: `glossary/cache/` - Translation glossaries (< 10 MB)
- **Persistence**: Managed by application logic (90-day expiry)

### Cache Management

```bash
# View cache size
du -sh .cache/*

# Clear model cache (will re-download on next use)
rm -rf .cache/

# Clear metadata cache
rm -rf out/tmdb_cache out/musicbrainz_cache
```
```

### 7.2 docs/TROUBLESHOOTING.md

**Add section: "Cache Issues"**

```markdown
## Cache Issues

### Models Downloading Multiple Times

**Symptom**: Whisper or HuggingFace models download every pipeline run.

**Cause**: Cache environment variables not set.

**Fix**:
```bash
# Re-run bootstrap to regenerate cache config
./bootstrap.sh --force

# Verify cache paths in config
cat config/hardware_cache.json | grep cache
```

### Disk Space Issues

**Symptom**: Running out of disk space.

**Diagnosis**:
```bash
# Check cache sizes
du -sh .cache/*
du -sh out/*_cache
```

**Solutions**:
1. **Clear old model versions**:
   ```bash
   rm -rf .cache/torch/hub/  # Re-downloads on next use
   ```

2. **Use smaller Whisper model**:
   ```bash
   # Edit job config to use 'base' or 'medium' instead of 'large-v3'
   ```

3. **Mount cache on external drive**:
   ```bash
   # Symlink cache directory
   mv .cache /Volumes/External/cp-whisperx-cache
   ln -s /Volumes/External/cp-whisperx-cache .cache
   ```
```

---

## 8. Summary of Best Practices

### ✅ DO

1. **Set cache paths in `hardware_cache.json`** - Single source of truth
2. **Propagate via `environment_manager.py`** - Consistent across stages
3. **Use project-local `.cache/`** - Avoids user home clutter
4. **Pre-download during bootstrap** - Better first-run experience
5. **Document cache locations** - User transparency
6. **Provide cache management tools** - Easy cleanup

### ❌ DON'T

1. **DON'T use multiple cache locations** - Causes duplicates
2. **DON'T hardcode cache paths in scripts** - Use config/env vars
3. **DON'T assume cache is set** - Always provide fallback
4. **DON'T ignore cache size** - Monitor and alert
5. **DON'T commit cached models** - Add to `.gitignore`

---

## 9. Quick Reference

### Current Cache Locations (After Recommendations)

```
PROJECT_ROOT/
├── .cache/                          # ML model cache
│   ├── torch/                       # 5-15 GB (Whisper models)
│   ├── huggingface/                 # 2-10 GB (transformers)
│   └── mlx/                         # 1-5 GB (MLX models)
├── out/
│   ├── tmdb_cache/                  # < 100 MB (metadata)
│   └── musicbrainz_cache/           # < 50 MB (metadata)
├── glossary/cache/                  # < 10 MB (glossaries)
└── config/
    └── hardware_cache.json          # Contains cache paths
```

### Environment Variables Set by System

| Variable | Value | Purpose |
|----------|-------|---------|
| `TORCH_HOME` | `.cache/torch` | PyTorch model cache |
| `HF_HOME` | `.cache/huggingface` | HuggingFace cache |
| `TRANSFORMERS_CACHE` | `.cache/huggingface` | Transformers-specific |
| `MLX_CACHE_DIR` | `.cache/mlx` | MLX framework cache |

### Configuration References

| File | Purpose | Cache Info |
|------|---------|-----------|
| `config/hardware_cache.json` | Environment mappings + cache paths | ✅ Primary |
| `config/.env.pipeline` | Application settings | TMDB, MusicBrainz paths |
| `.gitignore` | Exclude from git | `.cache/`, `out/*_cache/` |

---

## 10. Conclusion

**Current State**: The caching system works but is **fragmented and inconsistent**.

**Recommended State**: **Centralized, explicit, and well-documented** cache management.

**Implementation Effort**: 
- **Phase 1** (Critical): 2-3 hours
- **Phase 2** (Optimization): 4-6 hours
- **Phase 3** (Cleanup): 2-3 hours
- **Total**: ~8-12 hours

**Benefits**:
- 🚀 Faster pipeline execution (no redundant downloads)
- 💾 Reduced disk usage (single cache location)
- 🐛 Easier troubleshooting (predictable cache paths)
- 📚 Better user experience (documented and manageable)

**Risk**: Low - Changes are additive and backward-compatible.

---

**Next Steps**:
1. Review recommendations with team
2. Implement Phase 1 (critical fixes)
3. Test with real workflows
4. Document in user-facing docs
5. Deploy Phase 2 & 3 in next sprint
