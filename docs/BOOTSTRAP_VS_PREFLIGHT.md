# Bootstrap vs Preflight Scripts Comparison

**Understanding the difference between setup (bootstrap) and validation (preflight)**

---

## 🎯 Quick Answer

| Script | Purpose | When to Use |
|--------|---------|-------------|
| **`scripts/bootstrap.*`** | **Setup & Install** | First-time setup, install dependencies |
| **`preflight.*`** | **Validation & Check** | Before running pipeline, verify system ready |

---

## 📦 Bootstrap Scripts

### Purpose: **One-Time Setup & Installation**

Bootstrap scripts prepare your development environment by installing all required dependencies.

### What They Do

```
1. Find Python 3.11+
   ↓
2. Create virtual environment (.bollyenv)
   ↓
3. Activate virtual environment
   ↓
4. Upgrade pip and wheel
   ↓
5. Create/use requirements.txt
   ↓
6. Install all Python packages (PyTorch, WhisperX, etc.)
   ↓
7. Quick torch/CUDA check
   ↓
8. Done! Environment ready
```

### Files

| File | Platform | Lines |
|------|----------|-------|
| `scripts/bootstrap.ps1` | Windows PowerShell | ~105 lines |
| `scripts/bootstrap.sh` | Linux/macOS Bash | ~100 lines |

### Key Actions

1. **Creates virtual environment** (`.bollyenv/`)
2. **Installs ALL dependencies** from `requirements.txt`
3. **One-time operation** (unless you want to rebuild)
4. **Modifies your system** (creates files, installs packages)

### Usage

```bash
# Windows
.\scripts\bootstrap.ps1

# Linux/macOS
./scripts/bootstrap.sh
```

### Output Example

```
======================================================================
CP-WHISPERX-APP BOOTSTRAP
======================================================================
[INFO] Searching for Python...
[INFO] Using: python
[INFO] Checking Python version (recommended: 3.11+)
Python 3.11.5
[INFO] Creating virtualenv: .bollyenv
[INFO] Activating virtualenv...
[INFO] Upgrading pip and wheel...
[INFO] Installing Python packages from requirements.txt (this may take a while)...
[INFO] Running quick torch/CUDA check...
Torch version: 2.5.1
CUDA available: False

======================================================================
BOOTSTRAP COMPLETE
======================================================================

Next steps:
  1. Create .\config\.env and .\config\secrets.json
  2. Run: .\preflight.ps1
  3. Run pipeline: python pipeline.py -h
```

### When to Run

- ✅ **First time** setting up the project
- ✅ **After cloning** the repository
- ✅ **Dependency updates** (new requirements.txt)
- ✅ **Environment corruption** (need to rebuild)
- ❌ **Not needed** before every pipeline run

---

## ✅ Preflight Scripts

### Purpose: **Validation & System Check**

Preflight scripts validate that your system is ready to run the pipeline.

### What They Do

```
1. Check Python version (3.9+)
   ↓
2. Validate FFmpeg installed
   ↓
3. Check Docker & Docker Compose
   ↓
4. Verify directories exist (in/, out/, logs/, etc.)
   ↓
5. Validate config/.env file
   ↓
6. Check HuggingFace token
   ↓
7. Verify TMDB API key
   ↓
8. Test GPU/CUDA availability
   ↓
9. Save results (valid for 24 hours)
   ↓
10. Pass/Fail report
```

### Files

| File | Platform | Function |
|------|----------|----------|
| `preflight.ps1` (root) | Windows | Wrapper script |
| `scripts/preflight.sh` (root) | Linux/macOS | Wrapper script |
| `scripts/preflight.py` | All | Core validation logic |

### Key Actions

1. **Validates system** (reads, doesn't write)
2. **Checks configurations** (files, tokens, keys)
3. **Tests hardware** (GPU detection)
4. **Caches results** (24-hour validity)
5. **Non-destructive** (doesn't install anything)

### Usage

```bash
# Windows
.\preflight.ps1

# Force re-check (skip cache)
.\preflight.ps1 -Force

# Linux/macOS
./preflight.sh

# Force re-check
./preflight.sh --force
```

### Output Example

```
======================================================================
CP-WHISPERX-APP PREFLIGHT CHECKS
======================================================================
[INFO] Starting preflight validation...

System Checks:
  ✓ Python 3.11.5
  ✓ FFmpeg found
  ✓ Docker 24.0.6
  ✓ Docker Compose installed

Directory Checks:
  ✓ Directory: in/
  ✓ Directory: out/
  ✓ Directory: logs/
  ✓ Directory: config/
  ✓ Directory: shared/
  ✓ Directory: docker/

Configuration Checks:
  ✓ Config file (config/.env) - 45 settings found
  ⚠ INPUT_FILE not set in config/.env
  ✓ Secrets file (config/secrets.json)
  ✓ HuggingFace token valid
  ✓ TMDB API key valid

Hardware Checks:
  ✓ CUDA available: True
  ✓ GPU: NVIDIA GeForce GTX 750 Ti
  ✓ GPU memory: 2.00 GB

======================================================================
PREFLIGHT SUMMARY
======================================================================
Passed: 15
Failed: 0
Warnings: 1

[SUCCESS] System ready for pipeline execution
```

### Caching Behavior

**Smart caching** to avoid redundant checks:

```bash
# First run - performs all checks
.\preflight.ps1
# Result saved to: out/preflight_results.json

# Within 24 hours - skips checks
.\preflight.ps1
# Output: "Preflight check passed within last 24 hours (use --force to re-run)"

# Force re-run
.\preflight.ps1 -Force
# Always runs all checks
```

### When to Run

- ✅ **Before running pipeline** (recommended)
- ✅ **After system changes** (GPU drivers, Docker updates)
- ✅ **Configuration changes** (new API keys, tokens)
- ✅ **Troubleshooting** (diagnose issues)
- ✅ **Daily** (automatic via caching)
- ❌ **Not for installation** (use bootstrap for that)

---

## 📊 Side-by-Side Comparison

### Purpose

| Aspect | Bootstrap | Preflight |
|--------|-----------|-----------|
| **Goal** | Install dependencies | Validate system |
| **Type** | Setup/Installation | Verification/Check |
| **Frequency** | Once (or rarely) | Before each run |
| **Modifies System** | ✅ Yes (installs packages) | ❌ No (read-only) |
| **Duration** | ~5-15 minutes | ~10-30 seconds |

### Actions

| Action | Bootstrap | Preflight |
|--------|-----------|-----------|
| Create venv | ✅ Yes | ❌ No |
| Install packages | ✅ Yes | ❌ No |
| Check Python | ✅ Yes | ✅ Yes |
| Check FFmpeg | ❌ No | ✅ Yes |
| Check Docker | ❌ No | ✅ Yes |
| Validate config | ❌ No | ✅ Yes |
| Test tokens | ❌ No | ✅ Yes |
| Check GPU | ⚠️ Basic | ✅ Detailed |

### Output

| Output | Bootstrap | Preflight |
|--------|-----------|-----------|
| Creates files | `.bollyenv/` directory | `out/preflight_results.json` |
| Installs packages | All from requirements.txt | None |
| Exit code | 0 = success | 0 = all passed, 1 = failures |
| Caching | None | 24-hour validity |

### Use Cases

| Scenario | Use Bootstrap | Use Preflight |
|----------|---------------|---------------|
| First-time setup | ✅ Yes | After bootstrap |
| Before running pipeline | ❌ No | ✅ Yes |
| Dependency updates | ✅ Yes | ❌ No |
| System validation | ❌ No | ✅ Yes |
| Troubleshooting | ❌ No | ✅ Yes |
| Environment rebuild | ✅ Yes | After rebuild |

---

## 🔄 Typical Workflow

### Initial Setup (One Time)

```bash
# Step 1: Clone repository
git clone https://github.com/user/cp-whisperx-app.git
cd cp-whisperx-app

# Step 2: Run bootstrap (installs everything)
.\scripts\bootstrap.ps1    # Windows
./scripts/bootstrap.sh     # Linux/macOS

# Step 3: Configure
# Create config/.env and config/secrets.json

# Step 4: Validate with preflight
.\preflight.ps1            # Windows
./preflight.sh             # Linux/macOS

# Step 5: Ready to run pipeline!
```

### Daily Use

```bash
# Optional: Run preflight (auto-cached for 24h)
.\preflight.ps1

# Run pipeline
.\prepare-job.ps1 movie.mp4
.\run_pipeline.ps1 -Job 20241106-0001
```

### After System Changes

```bash
# GPU driver update? New Docker version?
.\preflight.ps1 -Force     # Force re-validation
```

### After Dependency Updates

```bash
# requirements.txt updated?
.\scripts\bootstrap.ps1    # Re-install dependencies
.\preflight.ps1 -Force     # Validate new setup
```

---

## 🎓 Detailed Breakdown

### Bootstrap Script Details

**Location:** `scripts/bootstrap.ps1` / `scripts/bootstrap.sh`

**What it installs:**
```
torch>=2.3,<3.0
torchaudio>=2.3,<3.0
openai-whisper>=20231117
faster-whisper>=1.0.0
whisperx>=3.1.0
whisper-ctranslate2>=0.4.0
ctranslate2>=4.2.0
pyannote.audio>=3.1.0
huggingface_hub>=0.23.0
librosa>=0.10.1
soundfile>=0.12.1
tmdbsimple>=2.9.1
rich>=13.7.0
python-dotenv>=1.0.0
pysubs2>=1.1.0
spacy>=3.7.0
transformers>=4.30.0
psutil>=5.9.0
pyyaml>=6.0
requests>=2.31.0
python-json-logger>=2.0.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
```

**Virtual environment:** `.bollyenv/`

**Next steps after bootstrap:**
1. Create `config/.env`
2. Create `config/secrets.json`
3. Run `preflight.ps1`

### Preflight Script Details

**Location:** `preflight.ps1` / `scripts/preflight.sh` (wrappers)  
**Core logic:** `scripts/preflight.py` (Python)

**What it checks:**

1. **System Prerequisites:**
   - Python 3.9+
   - FFmpeg
   - Docker
   - Docker Compose

2. **Directory Structure:**
   - `in/`
   - `out/`
   - `logs/`
   - `temp/`
   - `config/`
   - `shared/`
   - `docker/`

3. **Configuration Files:**
   - `config/.env` (settings)
   - `config/secrets.json` (tokens/keys)

4. **API Tokens:**
   - HuggingFace token (for PyAnnote)
   - TMDB API key (for metadata)

5. **Hardware:**
   - CUDA availability
   - GPU detection
   - GPU memory

**Results saved to:** `out/preflight_results.json`

**Cache duration:** 24 hours

---

## 🚨 Common Mistakes

### Mistake 1: Running preflight before bootstrap

```bash
# ❌ Wrong order
./preflight.sh           # Fails - venv doesn't exist yet

# ✅ Correct order
./scripts/bootstrap.sh   # Install first
./preflight.sh           # Then validate
```

### Mistake 2: Expecting preflight to install

```bash
# ❌ Preflight doesn't install
./preflight.ps1          # Only checks, doesn't fix

# ✅ Use bootstrap for installation
.\scripts\bootstrap.ps1  # Installs dependencies
```

### Mistake 3: Re-running bootstrap unnecessarily

```bash
# ❌ Don't need to run every time
.\scripts\bootstrap.ps1  # Only needed once or after updates

# ✅ Use preflight for validation
.\preflight.ps1          # Run before each pipeline execution
```

### Mistake 4: Ignoring preflight warnings

```bash
# ⚠️ Preflight shows warnings but you ignore them
.\preflight.ps1
# Output: "⚠ HuggingFace token not found"
# You ignore and run pipeline → Fails during diarization

# ✅ Fix issues before running
# Add token to config/secrets.json
.\preflight.ps1 -Force   # Verify fix
```

---

## 🔍 When to Use Which

### Use Bootstrap When:

- [ ] First time cloning the repository
- [ ] After deleting `.bollyenv/` directory
- [ ] Updating to new version with dependency changes
- [ ] Moving to a new machine/environment
- [ ] Python packages corrupted/broken
- [ ] Major system upgrades (Python version change)

### Use Preflight When:

- [ ] Before running the pipeline (recommended)
- [ ] After changing configuration files
- [ ] After updating API tokens/keys
- [ ] After GPU driver updates
- [ ] After Docker updates
- [ ] Troubleshooting pipeline failures
- [ ] Verifying system ready for processing

---

## 📝 Summary

### Bootstrap

**Purpose:** Install dependencies and create Python environment  
**Run frequency:** Once (or after major changes)  
**Duration:** 5-15 minutes  
**Action:** Creates venv, installs packages  
**Output:** `.bollyenv/` directory

### Preflight

**Purpose:** Validate system ready for pipeline  
**Run frequency:** Before each pipeline run (cached 24h)  
**Duration:** 10-30 seconds  
**Action:** Checks system, doesn't install  
**Output:** `out/preflight_results.json`

### Golden Rule

```
Bootstrap first (setup) → Preflight before use (validate) → Run pipeline (execute)
```

---

## 🔗 Related Documentation

- **Bootstrap Scripts:** `scripts/bootstrap.ps1`, `scripts/bootstrap.sh`
- **Preflight Scripts:** `preflight.ps1`, `scripts/preflight.py`
- **Quick Start Guide:** `docs/guides/user/quickstart.md`
- **Developer Guide:** `docs/guides/developer/developer-guide.md`

---

**Last Updated:** 2024-11-06  
**Version:** 1.0.0
