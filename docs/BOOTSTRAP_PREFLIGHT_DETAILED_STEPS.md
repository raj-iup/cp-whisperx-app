# Detailed Execution Steps: Bootstrap & Preflight

**Step-by-step breakdown of what each script does internally**

---

## 📦 Bootstrap Script - Detailed Execution

### Script Location
- **Windows:** `scripts\bootstrap.ps1`
- **Linux/macOS:** `scripts/bootstrap.sh`

### Complete Execution Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 1: INITIALIZATION                                         │
└─────────────────────────────────────────────────────────────────┘
```

#### Step 1: Load Common Logging System
```powershell
# Line 10: Load logging functions
. "$PSScriptRoot\common-logging.ps1"
```
**Action:**
- Loads shared logging functions
- Initializes log file: `logs/YYYYMMDD-HHMMSS-bootstrap.log`
- Sets up colored console output

**Output:**
```
[INFO] Logging initialized
```

---

#### Step 2: Display Bootstrap Header
```powershell
# Line 13: Print section header
Write-LogSection "CP-WHISPERX-APP BOOTSTRAP"
```
**Action:**
- Displays large section header
- Logs to both console and file

**Output:**
```
======================================================================
CP-WHISPERX-APP BOOTSTRAP
======================================================================
```

---

#### Step 3: Initialize Variables
```powershell
# Lines 15-16: Set key paths
$venvDir = ".bollyenv"
$reqFile = "requirements.txt"
```
**Action:**
- Sets virtual environment directory name
- Sets requirements file path

---

```
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 2: PYTHON DISCOVERY                                       │
└─────────────────────────────────────────────────────────────────┘
```

#### Step 4: Search for Python Executable
```powershell
# Lines 18-29: Find Python
Write-LogInfo "Searching for Python..."

if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonBin = "python"
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    $pythonBin = "python3"
} else {
    Write-LogError "Python not found. Please install Python 3.11+"
    exit 1
}
```
**Action:**
1. Tries to find `python` command
2. If not found, tries `python3`
3. If neither found, exits with error

**Output (Success):**
```
[INFO] Searching for Python...
[INFO] Using: python
```

**Output (Failure):**
```
[ERROR] Python not found. Please install Python 3.11+
```

---

#### Step 5: Validate Python Version
```powershell
# Lines 33-35: Check Python version
Write-LogInfo "Checking Python version (recommended: 3.11+)"
& $pythonBin -c "import sys; v = sys.version_info; print(f'Python {v.major}.{v.minor}.{v.micro}'); print('Warning: Python 3.11+ recommended') if v.major < 3 or (v.major == 3 and v.minor < 11) else None"
```
**Action:**
1. Executes Python to check version
2. Prints version number
3. Shows warning if < 3.11

**Output (Good Version):**
```
[INFO] Checking Python version (recommended: 3.11+)
Python 3.11.5
```

**Output (Old Version):**
```
[INFO] Checking Python version (recommended: 3.11+)
Python 3.9.18
Warning: Python 3.11+ recommended
```

---

```
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 3: VIRTUAL ENVIRONMENT SETUP                              │
└─────────────────────────────────────────────────────────────────┘
```

#### Step 6: Check for Existing Virtual Environment
```powershell
# Lines 37-43: Create or use existing venv
if (Test-Path $venvDir) {
    Write-LogInfo "Found existing virtualenv: $venvDir"
} else {
    Write-LogInfo "Creating virtualenv: $venvDir"
    & $pythonBin -m venv $venvDir
}
```
**Action:**
1. Checks if `.bollyenv/` directory exists
2. If exists: Reuses it
3. If not: Creates new virtual environment

**Command Executed (if new):**
```bash
python -m venv .bollyenv
```

**Output (Existing):**
```
[INFO] Found existing virtualenv: .bollyenv
```

**Output (New):**
```
[INFO] Creating virtualenv: .bollyenv
```

**Files Created:**
```
.bollyenv/
├── Scripts/          # Windows
│   ├── Activate.ps1
│   ├── python.exe
│   └── pip.exe
├── bin/              # Linux/macOS
│   ├── activate
│   ├── python
│   └── pip
├── Lib/
│   └── site-packages/
└── pyvenv.cfg
```

---

#### Step 7: Activate Virtual Environment
```powershell
# Lines 45-53: Activate venv
Write-LogInfo "Activating virtualenv..."
$activateScript = Join-Path $venvDir "Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
} else {
    Write-LogError "Could not find activation script"
    exit 1
}
```
**Action:**
1. Builds path to activation script
2. Checks if activation script exists
3. Executes activation script
4. Exits if activation fails

**Script Path:**
- Windows: `.bollyenv\Scripts\Activate.ps1`
- Linux/macOS: `.bollyenv/bin/activate`

**Effect:**
- Modifies `$env:PATH` to prioritize venv Python
- Sets `$env:VIRTUAL_ENV` variable
- Changes prompt to show `(.bollyenv)`

**Output:**
```
[INFO] Activating virtualenv...
```

**Console Prompt Changes:**
```
# Before
PS C:\Projects\cp-whisperx-app>

# After
(.bollyenv) PS C:\Projects\cp-whisperx-app>
```

---

```
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 4: PACKAGE MANAGEMENT TOOLS                               │
└─────────────────────────────────────────────────────────────────┘
```

#### Step 8: Upgrade pip and wheel
```powershell
# Lines 55-57: Upgrade package managers
Write-LogInfo "Upgrading pip and wheel..."
python -m pip install -U pip wheel | Out-Null
```
**Action:**
1. Upgrades `pip` (package installer)
2. Upgrades `wheel` (package format)
3. Uses venv's Python (now in PATH)

**Command Executed:**
```bash
python -m pip install --upgrade pip wheel
```

**Output:**
```
[INFO] Upgrading pip and wheel...
```

**Package Versions (typically):**
- pip: 23.x → Latest (e.g., 24.0)
- wheel: 0.x → Latest (e.g., 0.43.0)

---

```
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 5: REQUIREMENTS FILE PREPARATION                          │
└─────────────────────────────────────────────────────────────────┘
```

#### Step 9: Create requirements.txt (if missing)
```powershell
# Lines 59-85: Create requirements.txt if needed
if (-not (Test-Path $reqFile)) {
    Write-LogInfo "Creating recommended $reqFile"
    
    $requirements = @"
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
"@
    
    Set-Content -Path $reqFile -Value $requirements
    Write-LogSuccess "Wrote $reqFile"
}
```
**Action:**
1. Checks if `requirements.txt` exists in current directory
2. If missing: Creates file with recommended packages
3. If exists: Uses existing file

**Output (Created):**
```
[INFO] Creating recommended requirements.txt
[SUCCESS] Wrote requirements.txt
```

**Output (Existing):**
```
(No output - uses existing file)
```

**File Created:** `requirements.txt` (22 packages)

---

```
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 6: DEPENDENCY INSTALLATION                                │
└─────────────────────────────────────────────────────────────────┘
```

#### Step 10: Install All Python Packages
```powershell
# Lines 87-89: Install from requirements.txt
Write-LogInfo "Installing Python packages from $reqFile (this may take a while)..."
python -m pip install -r $reqFile
```
**Action:**
1. Reads `requirements.txt`
2. Downloads each package from PyPI
3. Installs packages in virtual environment
4. Resolves dependencies recursively

**Command Executed:**
```bash
python -m pip install -r requirements.txt
```

**Output:**
```
[INFO] Installing Python packages from requirements.txt (this may take a while)...
Collecting torch>=2.3,<3.0
  Downloading torch-2.5.1-cp311-cp311-win_amd64.whl (203.8 MB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 203.8/203.8 MB 15.2 MB/s
Collecting torchaudio>=2.3,<3.0
  Downloading torchaudio-2.5.1-cp311-cp311-win_amd64.whl (4.4 MB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 4.4/4.4 MB 20.1 MB/s
... (continues for all 22 packages + dependencies)
Successfully installed torch-2.5.1 torchaudio-2.5.1 ... (70+ packages total)
```

**Packages Installed:**

| Package | Version | Size | Purpose |
|---------|---------|------|---------|
| **torch** | 2.5.1 | ~200 MB | PyTorch deep learning framework |
| **torchaudio** | 2.5.1 | ~4 MB | Audio processing for PyTorch |
| **openai-whisper** | Latest | ~10 MB | OpenAI Whisper ASR |
| **faster-whisper** | 1.0+ | ~5 MB | Optimized Whisper |
| **whisperx** | 3.1+ | ~2 MB | WhisperX ASR with alignment |
| **whisper-ctranslate2** | 0.4+ | ~3 MB | CTranslate2 Whisper backend |
| **ctranslate2** | 4.2+ | ~50 MB | Fast inference library |
| **pyannote.audio** | 3.1+ | ~20 MB | Speaker diarization |
| **huggingface_hub** | 0.23+ | ~5 MB | HuggingFace model hub |
| **librosa** | 0.10+ | ~10 MB | Audio analysis |
| **soundfile** | 0.12+ | ~1 MB | Audio file I/O |
| **tmdbsimple** | 2.9+ | <1 MB | TMDB API client |
| **rich** | 13.7+ | ~5 MB | Rich text formatting |
| **python-dotenv** | 1.0+ | <1 MB | .env file support |
| **pysubs2** | 1.1+ | <1 MB | Subtitle parsing |
| **spacy** | 3.7+ | ~30 MB | NLP library |
| **transformers** | 4.30+ | ~50 MB | Hugging Face transformers |
| **psutil** | 5.9+ | ~1 MB | System utilities |
| **pyyaml** | 6.0+ | <1 MB | YAML parser |
| **requests** | 2.31+ | ~1 MB | HTTP client |
| **python-json-logger** | 2.0+ | <1 MB | JSON logging |
| **pydantic** | 2.0+ | ~5 MB | Data validation |

**Total Download:** ~2-3 GB  
**Installation Time:** 5-15 minutes (depending on network speed)

**Dependencies Installed (automatically):**
- numpy, scipy, scikit-learn
- pandas, matplotlib
- certifi, charset-normalizer, idna, urllib3
- filelock, fsspec, networkx
- typing-extensions, packaging
- joblib, threadpoolctl
- ... (50+ additional dependencies)

---

```
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 7: INSTALLATION VERIFICATION                              │
└─────────────────────────────────────────────────────────────────┘
```

#### Step 11: Verify PyTorch and CUDA
```powershell
# Lines 91-93: Quick torch/CUDA check
Write-LogInfo "Running quick torch/CUDA check..."
python -c "try: import torch, sys; cuda = torch.cuda.is_available(); print('Torch version:', torch.__version__); print('CUDA available:', bool(cuda)); except Exception as e: print('Could not import torch or check devices:', repr(e)); sys.exit(0)"
```
**Action:**
1. Imports PyTorch
2. Checks PyTorch version
3. Tests CUDA availability
4. Prints results

**Output (With GPU):**
```
[INFO] Running quick torch/CUDA check...
Torch version: 2.5.1
CUDA available: True
```

**Output (CPU only):**
```
[INFO] Running quick torch/CUDA check...
Torch version: 2.5.1+cpu
CUDA available: False
```

**Output (Import Error):**
```
[INFO] Running quick torch/CUDA check...
Could not import torch or check devices: ModuleNotFoundError("No module named 'torch'")
```

---

```
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 8: COMPLETION                                             │
└─────────────────────────────────────────────────────────────────┘
```

#### Step 12: Display Completion Message
```powershell
# Lines 95-102: Final message
Write-LogSection "BOOTSTRAP COMPLETE"
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Create .\config\.env and .\config\secrets.json" -ForegroundColor Gray
Write-Host "  2. Run: .\preflight.ps1" -ForegroundColor Gray
Write-Host "  3. Run pipeline: python pipeline.py -h" -ForegroundColor Gray
Write-Host ""

exit 0
```
**Action:**
1. Displays completion banner
2. Shows next steps
3. Exits with success code (0)

**Output:**
```
======================================================================
BOOTSTRAP COMPLETE
======================================================================

Next steps:
  1. Create .\config\.env and .\config\secrets.json
  2. Run: .\preflight.ps1
  3. Run pipeline: python pipeline.py -h
```

---

### Bootstrap Summary

**Total Steps:** 12  
**Total Time:** 5-15 minutes  
**Disk Space Used:** ~3-4 GB  

**Files Created:**
```
.bollyenv/                      # Virtual environment (~3 GB)
├── Scripts/ or bin/           # Python executables
├── Lib/site-packages/         # Installed packages
└── pyvenv.cfg                 # Configuration

requirements.txt                # Package list (if didn't exist)

logs/
└── YYYYMMDD-HHMMSS-bootstrap.log  # Execution log
```

**Exit Codes:**
- `0` = Success
- `1` = Python not found or activation failed

---

## ✅ Preflight Script - Detailed Execution

### Script Location
- **Wrapper (Windows):** `preflight.ps1`
- **Wrapper (Linux/macOS):** `scripts/preflight.sh`
- **Core Logic:** `scripts/preflight.py`

### Complete Execution Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 1: INITIALIZATION                                         │
└─────────────────────────────────────────────────────────────────┘
```

#### Step 1: Parse Command-Line Arguments
```python
# preflight.py main() function
parser = argparse.ArgumentParser(description="Preflight validation checks")
parser.add_argument("--force", action="store_true", help="Force re-run")
args = parser.parse_args()
```
**Action:**
- Parses `--force` flag (skips cache)

---

#### Step 2: Initialize Preflight Checker
```python
# Create checker instance
checker = PreflightCheck(output_dir=Path("out"), force=args.force)
```
**Action:**
1. Sets output directory (`out/`)
2. Initializes counters: passed=0, failed=0, warnings=0
3. Creates results dictionary
4. Records start time

---

#### Step 3: Check Cache (24-hour validity)
```python
def should_run_checks(self) -> bool:
    if self.force:
        return True
    
    if not self.results_file.exists():
        return True
    
    # Load last results
    with open(self.results_file, 'r') as f:
        last_results = json.load(f)
    
    # Check if last run was successful
    if last_results.get("checks_failed", 1) > 0:
        return True
    
    # Check if last run was within 24 hours
    last_run = datetime.fromisoformat(last_results["timestamp"])
    age = datetime.now() - last_run
    
    if age < timedelta(hours=24):
        print("✓ Preflight check passed within last 24 hours")
        return False
    
    return True
```
**Action:**
1. Checks if `out/preflight_results.json` exists
2. Reads last run timestamp
3. Calculates age of last check
4. If < 24 hours and passed: Skips checks
5. If --force flag: Always runs

**Output (Cached):**
```
✓ Preflight check passed within last 24 hours
  Last run: 2024-11-06 14:30:45
  Age: 2h 15m ago
  Passed: 18
  Failed: 0
  Warnings: 1

Skipping preflight checks (use --force to re-run)
```

**Output (Force or Expired):**
```
Preflight check is older than 24 hours - re-running
  Last run: 2024-11-05 10:15:30
```

---

```
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 2: SYSTEM PREREQUISITES                                   │
└─────────────────────────────────────────────────────────────────┘
```

#### Step 4: Check Python Version
```python
import sys
v = sys.version_info
if v.major >= 3 and v.minor >= 9:
    print(f"✓ PASS Python {v.major}.{v.minor}.{v.micro}")
else:
    print(f"✗ FAIL Python version too old")
```
**Action:**
1. Gets Python version from `sys.version_info`
2. Checks if >= 3.9
3. Passes or fails

**Output:**
```
✓ PASS Python 3.11.5
```

---

#### Step 5: Check FFmpeg Installation
```python
def check_ffmpeg(self) -> bool:
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=True
        )
        version = result.stdout.split('\n')[0]
        self.print_check("FFmpeg installed", True, version)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        self.print_check("FFmpeg", False, "Not found")
        return False
```
**Action:**
1. Runs `ffmpeg -version`
2. Captures output
3. Parses version string
4. Times out after 10 seconds

**Output (Success):**
```
✓ PASS FFmpeg installed
       ffmpeg version 6.0 Copyright (c) 2000-2023 the FFmpeg developers
```

**Output (Missing):**
```
✗ FAIL FFmpeg
       Not found
```

---

#### Step 6: Check Docker Installation
```python
def check_docker(self) -> bool:
    # Check docker --version
    result = subprocess.run(
        ["docker", "--version"],
        capture_output=True,
        text=True,
        timeout=10,
        check=True
    )
    version = result.stdout.strip()
    self.print_check("Docker installed", True, version)
    
    # Check if daemon running
    result = subprocess.run(
        ["docker", "ps"],
        capture_output=True,
        text=True,
        timeout=30,
        check=True
    )
    self.print_check("Docker daemon running", True)
    return True
```
**Action:**
1. Tests `docker --version`
2. Tests `docker ps` (requires running daemon)
3. Timeout: 30 seconds

**Output (Running):**
```
✓ PASS Docker installed
       Docker version 24.0.6, build ed223bc
✓ PASS Docker daemon running
```

**Output (Not Running):**
```
✓ PASS Docker installed
       Docker version 24.0.6, build ed223bc
✗ FAIL Docker daemon running
       Docker not responding
```

---

#### Step 7: Check Docker Compose
```python
def check_docker_compose(self) -> bool:
    result = subprocess.run(
        ["docker", "compose", "version"],
        capture_output=True,
        text=True,
        timeout=10,
        check=True
    )
    version = result.stdout.strip()
    self.print_check("Docker Compose installed", True, version)
    return True
```
**Action:**
1. Tests `docker compose version`
2. Parses version

**Output:**
```
✓ PASS Docker Compose installed
       Docker Compose version v2.23.0
```

---

```
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 3: DIRECTORY STRUCTURE                                    │
└─────────────────────────────────────────────────────────────────┘
```

#### Step 8: Validate Required Directories
```python
def check_directories(self) -> bool:
    required_dirs = [
        "in",      # Input media
        "out",     # Outputs
        "logs",    # Log files
        "temp",    # Temporary files
        "config",  # Configuration
        "shared",  # Shared Python code
        "docker"   # Docker images
    ]
    
    all_exist = True
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        exists = dir_path.exists() and dir_path.is_dir()
        self.print_check(f"Directory: {dir_name}/", exists)
        if not exists:
            all_exist = False
    
    return all_exist
```
**Action:**
1. Checks each required directory
2. Verifies it exists and is a directory (not file)

**Output (All Exist):**
```
✓ PASS Directory: in/
✓ PASS Directory: out/
✓ PASS Directory: logs/
✓ PASS Directory: temp/
✓ PASS Directory: config/
✓ PASS Directory: shared/
✓ PASS Directory: docker/
```

**Output (Missing):**
```
✓ PASS Directory: in/
✗ FAIL Directory: out/
✓ PASS Directory: logs/
```

---

```
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 4: CONFIGURATION FILES                                    │
└─────────────────────────────────────────────────────────────────┘
```

#### Step 9: Validate config/.env File
```python
def check_config_file(self) -> Tuple[bool, Dict]:
    config_file = Path("config/.env")
    
    if not config_file.exists():
        self.print_check("Config file (config/.env)", False, "File not found")
        return False, {}
    
    # Parse .env file
    config = {}
    with open(config_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                config[key.strip()] = value.strip()
    
    self.print_check("Config file (config/.env)", True, f"{len(config)} settings found")
    return True, config
```
**Action:**
1. Checks if `config/.env` exists
2. Parses file (KEY=VALUE format)
3. Skips comments and blank lines
4. Counts settings

**Output (Exists):**
```
✓ PASS Config file (config/.env)
       45 settings found
```

**Output (Missing):**
```
✗ FAIL Config file (config/.env)
       File not found
```

---

#### Step 10: Check Input File (Optional)
```python
def check_input_file(self, config: Dict) -> bool:
    input_file = config.get("INPUT_FILE", "")
    
    if not input_file:
        self.print_warning("INPUT_FILE not set in config/.env")
        return True  # Not a hard requirement
    
    input_path = Path(input_file)
    exists = input_path.exists() and input_path.is_file()
    
    if exists:
        size_mb = input_path.stat().st_size / (1024 * 1024)
        self.print_check(f"Input file: {input_file}", True, f"Size: {size_mb:.2f} MB")
    else:
        self.print_check(f"Input file: {input_file}", False, "File not found")
    
    return exists
```
**Action:**
1. Reads `INPUT_FILE` from config
2. Checks if file exists
3. Reports file size if found
4. Warning only (not failure)

**Output (Exists):**
```
✓ PASS Input file: in/movie.mp4
       Size: 1024.50 MB
```

**Output (Not Set):**
```
⚠ WARNING INPUT_FILE not set in config/.env
```

---

```
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 5: DOCKER CONFIGURATION                                   │
└─────────────────────────────────────────────────────────────────┘
```

#### Step 11: Validate docker-compose.yml
```python
def check_docker_compose_config(self) -> bool:
    compose_file = Path("docker-compose.yml")
    
    if not compose_file.exists():
        self.print_check("Docker Compose config", False, "docker-compose.yml not found")
        return False
    
    # Read and check for required services
    with open(compose_file, 'r') as f:
        content = f.read()
    
    required_services = [
        "demux", "pre-ner", "silero-vad", "pyannote-vad",
        "diarization", "asr", "post-ner", "subtitle-gen", "mux"
    ]
    
    services_found = []
    services_missing = []
    
    for service in required_services:
        if f"\n  {service}:" in content:
            services_found.append(service)
        else:
            services_missing.append(service)
    
    if services_missing:
        self.print_check("Docker Compose config", False, f"Missing services: {len(services_missing)}")
        for service in services_missing:
            self.print_warning(f"  Missing: {service}")
        return False
    else:
        self.print_check("Docker Compose config", True, f"All 9 containerized services configured")
        return True
```
**Action:**
1. Checks if `docker-compose.yml` exists
2. Reads file content
3. Searches for 9 required service definitions
4. Lists any missing services

**Output (Complete):**
```
✓ PASS Docker Compose config
       All 9 containerized services configured
       Note: TMDB (Stage 2) handled by orchestrator
```

**Output (Missing Services):**
```
✗ FAIL Docker Compose config
       Missing services: 2
⚠ WARNING   Missing: pyannote-vad
⚠ WARNING   Missing: diarization
```

---

#### Step 12: Check Docker Images
```python
def check_docker_images(self) -> bool:
    # List all images
    result = subprocess.run(
        ["docker", "images", "--format", "{{.Repository}}:{{.Tag}}"],
        capture_output=True,
        text=True,
        timeout=30,
        check=True
    )
    
    images = result.stdout.strip().split('\n')
    
    # Check base image
    base_image = "rajiup/cp-whisperx-app-base:latest"
    has_base = any(base_image in img for img in images)
    
    if has_base:
        self.print_check("Docker base image", True, base_image)
    else:
        self.print_warning(f"Base image not found: {base_image}")
    
    # Check 10 stage images
    stage_images = [
        "rajiup/cp-whisperx-app-demux:latest",
        "rajiup/cp-whisperx-app-tmdb:latest",
        # ... (8 more)
    ]
    
    images_found = 0
    images_missing = 0
    
    for stage_image in stage_images:
        has_stage = any(stage_image in img for img in images)
        if has_stage:
            images_found += 1
        else:
            images_missing += 1
            self.print_warning(f"Image missing: {stage_image}")
    
    if images_missing > 0:
        self.print_warning(f"\n{images_missing} of 10 container images not built")
        self.print_warning("Run: docker compose build")
    else:
        print("       All 10 container images ready!")
    
    return True
```
**Action:**
1. Lists all Docker images on system
2. Checks for base image
3. Checks for 10 stage images
4. Reports missing images

**Output (All Present):**
```
✓ PASS Docker base image
       rajiup/cp-whisperx-app-base:latest
✓ PASS   demux
       Stage 1: FFmpeg audio extraction
✓ PASS   tmdb
       Stage 2: TMDB metadata fetch
... (8 more stages)
       All 10 container images ready!
```

**Output (Missing Images):**
```
⚠ WARNING Base image not found: rajiup/cp-whisperx-app-base:latest
⚠ WARNING Run: docker build -f docker/base/Dockerfile ...
⚠ WARNING Image missing: rajiup/cp-whisperx-app-demux:latest
⚠ WARNING   Stage 1: FFmpeg audio extraction
⚠ WARNING 
⚠ WARNING 5 of 10 container images not built
⚠ WARNING Run: docker compose build
```

---

```
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 6: API TOKENS & SECRETS                                   │
└─────────────────────────────────────────────────────────────────┘
```

#### Step 13: Check Secrets File
```python
def check_secrets(self) -> bool:
    secrets_file = Path("config/secrets.json")
    
    if not secrets_file.exists():
        self.print_warning("Secrets file not found: config/secrets.json")
        self.print_warning("Some features may not work without API keys")
        return True  # Not a hard requirement
    
    # Parse JSON
    with open(secrets_file, 'r') as f:
        secrets = json.load(f)
    
    # Check TMDB API Key
    has_tmdb = secrets.get("TMDB_API_KEY") or secrets.get("tmdb_api_key")
    if has_tmdb:
        self.print_check("TMDB API key", True, "For movie metadata enrichment")
    else:
        self.print_warning("TMDB API key not found in secrets")
        self.print_warning("  Used by: TMDB metadata stage")
        self.print_warning("  Impact: Cannot fetch movie cast, plot, keywords")
    
    # Check HuggingFace Token
    has_hf = secrets.get("HF_TOKEN") or secrets.get("hf_token")
    if has_hf:
        self.print_check("HuggingFace token", True, "For PyAnnote VAD and Diarization")
    else:
        self.print_warning("HuggingFace token not found in secrets")
        self.print_warning("  Used by: PyAnnote VAD and Diarization stages")
        self.print_warning("  Impact: PyAnnote models may fail to load")
        self.print_warning("  Get token: https://huggingface.co/settings/tokens")
    
    return True
```
**Action:**
1. Checks if `config/secrets.json` exists
2. Parses JSON
3. Validates TMDB API key
4. Validates HuggingFace token
5. Warnings only (not failures)

**Output (All Present):**
```
✓ PASS TMDB API key
       For movie metadata enrichment
✓ PASS HuggingFace token
       For PyAnnote VAD and Diarization
```

**Output (Missing):**
```
⚠ WARNING Secrets file not found: config/secrets.json
⚠ WARNING Some features may not work without API keys
⚠ WARNING   Create from: cp config/secrets.example.json config/secrets.json
```

**Output (Partial):**
```
✓ PASS TMDB API key
       For movie metadata enrichment
⚠ WARNING HuggingFace token not found in secrets
⚠ WARNING   Used by: PyAnnote VAD and Diarization stages
⚠ WARNING   Impact: PyAnnote models may fail to load
⚠ WARNING   Get token: https://huggingface.co/settings/tokens
```

---

```
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 7: HARDWARE DETECTION                                     │
└─────────────────────────────────────────────────────────────────┘
```

#### Step 14: Check Disk Space
```python
def check_disk_space(self) -> bool:
    import shutil
    stat = shutil.disk_usage(".")
    
    free_gb = stat.free / (1024 ** 3)
    total_gb = stat.total / (1024 ** 3)
    
    # Warn if less than 10GB free
    if free_gb < 10:
        self.print_check("Disk space", False, f"{free_gb:.1f}GB free (need at least 10GB)")
        return False
    else:
        self.print_check("Disk space", True, f"{free_gb:.1f}GB free / {total_gb:.1f}GB total")
        return True
```
**Action:**
1. Gets disk usage stats
2. Calculates free space in GB
3. Requires at least 10GB free

**Output (Sufficient):**
```
✓ PASS Disk space
       125.3GB free / 500.0GB total
```

**Output (Low):**
```
✗ FAIL Disk space
       7.2GB free (need at least 10GB)
```

---

#### Step 15: Detect Compute Devices (GPU/CPU)
```python
def check_compute_devices(self) -> Dict[str, Any]:
    import platform
    import torch
    
    system = platform.system()
    
    devices = {
        "platform": system,
        "cuda": {"available": False, "device_count": 0, "devices": []},
        "mps": {"available": False},
        "cpu": {"available": True}
    }
    
    # Check CUDA
    if torch.cuda.is_available():
        devices["cuda"]["available"] = True
        devices["cuda"]["device_count"] = torch.cuda.device_count()
        devices["cuda"]["cuda_version"] = torch.version.cuda
        devices["cuda"]["cudnn_version"] = torch.backends.cudnn.version()
        
        for i in range(torch.cuda.device_count()):
            device_info = {
                "id": i,
                "name": torch.cuda.get_device_name(i),
                "compute_capability": f"{torch.cuda.get_device_capability(i)[0]}.{torch.cuda.get_device_capability(i)[1]}",
                "total_memory_gb": torch.cuda.get_device_properties(i).total_memory / (1024**3)
            }
            devices["cuda"]["devices"].append(device_info)
        
        self.print_check("CUDA available", True, f"{devices['cuda']['device_count']} device(s), CUDA {devices['cuda']['cuda_version']}")
        
        for dev in devices["cuda"]["devices"]:
            print(f"       GPU {dev['id']}: {dev['name']} ({dev['total_memory_gb']:.1f}GB VRAM, CC {dev['compute_capability']})")
        
        # Get NVIDIA driver version
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=10,
            check=True
        )
        driver_version = result.stdout.strip()
        print(f"       NVIDIA Driver: {driver_version}")
        devices["cuda"]["driver_version"] = driver_version
    else:
        self.print_check("CUDA available", False, "No NVIDIA GPU detected or CUDA not installed")
        self.print_warning("For GPU acceleration, install:")
        self.print_warning("  1. NVIDIA Driver from nvidia.com")
        self.print_warning("  2. CUDA Toolkit from developer.nvidia.com")
        self.print_warning("  3. PyTorch with CUDA: pip install torch --index-url https://download.pytorch.org/whl/cu121")
    
    # Check MPS (macOS only)
    if system == 'Darwin':
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            devices["mps"]["available"] = True
            self.print_check("MPS available (Apple Silicon)", True, "Metal Performance Shaders acceleration")
        else:
            self.print_check("MPS available", False, "Not available (Intel Mac or macOS < 12.3)")
    
    # CPU always available
    self.print_check("CPU available", True, f"Fallback device on {system}")
    
    # Determine recommended device
    if devices["cuda"]["available"]:
        recommended = "cuda"
        print(f"       Recommended: CUDA (NVIDIA GPU acceleration)")
    elif devices["mps"]["available"]:
        recommended = "mps"
        print(f"       Recommended: MPS (Apple Silicon acceleration)")
    else:
        recommended = "cpu"
        print(f"       Recommended: CPU (no GPU acceleration available)")
    
    devices["recommended"] = recommended
    
    return devices
```
**Action:**
1. Imports PyTorch
2. Detects platform (Windows/Linux/macOS)
3. Checks CUDA availability
4. For CUDA: Gets device count, names, memory, driver
5. Checks MPS (macOS only)
6. CPU always available
7. Recommends best device

**Output (NVIDIA GPU - Windows):**
```
✓ PASS CUDA available (Windows)
       1 device(s), CUDA 12.6
       GPU 0: NVIDIA GeForce GTX 750 Ti (2.0GB VRAM, CC 5.0)
       NVIDIA Driver: 560.94
✓ PASS CPU available
       Fallback device on Windows
       Recommended: CUDA (Windows native with NVIDIA GPU)
```

**Output (Apple Silicon - macOS):**
```
✗ FAIL CUDA available
       No NVIDIA GPU detected
✓ PASS MPS available (Apple Silicon)
       Metal Performance Shaders acceleration
✓ PASS CPU available
       Fallback device on Darwin
       Recommended: MPS (Apple Silicon acceleration)
```

**Output (CPU only):**
```
✗ FAIL CUDA available
       No NVIDIA GPU detected or CUDA not installed
⚠ WARNING For GPU acceleration, install:
⚠ WARNING   1. NVIDIA Driver from nvidia.com
⚠ WARNING   2. CUDA Toolkit from developer.nvidia.com
⚠ WARNING   3. PyTorch with CUDA: pip install torch --index-url ...
✓ PASS CPU available
       Fallback device on Windows
       Recommended: CPU (no GPU acceleration available)
```

---

```
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 8: RESULTS & SAVING                                       │
└─────────────────────────────────────────────────────────────────┘
```

#### Step 16: Calculate Summary
```python
# Count results
duration = time.time() - self.start_time
status = "success" if self.checks_failed == 0 else "failed"
```
**Action:**
1. Calculates execution time
2. Determines pass/fail status
3. Counts passed, failed, warnings

---

#### Step 17: Save Results to JSON
```python
def save_results(self, devices: Dict = None):
    duration = time.time() - self.start_time
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "checks_passed": self.checks_passed,
        "checks_failed": self.checks_failed,
        "warnings": self.warnings,
        "duration_seconds": duration,
        "status": "success" if self.checks_failed == 0 else "failed",
        "details": self.check_details,
        "devices": devices,
        "pipeline_device": devices["recommended"]
    }
    
    # Save to out/preflight_results.json
    with open(self.results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Also save timestamped copy
    log_file = Path("logs") / f"preflight_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(log_file, 'w') as f:
        json.dump(results, f, indent=2)
```
**Action:**
1. Creates results dictionary
2. Saves to `out/preflight_results.json` (cached)
3. Saves to `logs/preflight_YYYYMMDD_HHMMSS.json` (archive)

**Files Created:**
```
out/
└── preflight_results.json        # Cached results (24h)

logs/
└── preflight_20241106_152530.json  # Timestamped archive
```

**JSON Structure:**
```json
{
  "timestamp": "2024-11-06T15:25:30.123456",
  "version": "1.0.0",
  "checks_passed": 18,
  "checks_failed": 0,
  "warnings": 2,
  "duration_seconds": 12.5,
  "status": "success",
  "details": {
    "Python version": {
      "status": "pass",
      "details": "Python 3.11.5"
    },
    "FFmpeg installed": {
      "status": "pass",
      "details": "ffmpeg version 6.0"
    },
    ...
  },
  "devices": {
    "platform": "Windows",
    "cuda": {
      "available": true,
      "device_count": 1,
      "cuda_version": "12.6",
      "devices": [
        {
          "id": 0,
          "name": "NVIDIA GeForce GTX 750 Ti",
          "compute_capability": "5.0",
          "total_memory_gb": 2.0
        }
      ]
    },
    "mps": {
      "available": false
    },
    "cpu": {
      "available": true
    },
    "recommended": "cuda"
  },
  "pipeline_device": "cuda"
}
```

---

#### Step 18: Display Summary
```python
print("\n" + "="*60)
print("PREFLIGHT SUMMARY")
print("="*60)
print(f"Passed: {self.checks_passed}")
print(f"Failed: {self.checks_failed}")
print(f"Warnings: {self.warnings}")
print(f"Duration: {duration:.1f}s")
print()

if self.checks_failed == 0:
    print("✓ System ready for pipeline execution")
    exit(0)
else:
    print("✗ System not ready - fix failures above")
    exit(1)
```
**Action:**
1. Displays summary box
2. Shows counts
3. Shows duration
4. Exits with appropriate code

**Output (Success):**
```
======================================================================
PREFLIGHT SUMMARY
======================================================================
Passed: 18
Failed: 0
Warnings: 2
Duration: 12.5s

✓ System ready for pipeline execution
```

**Output (Failures):**
```
======================================================================
PREFLIGHT SUMMARY
======================================================================
Passed: 12
Failed: 3
Warnings: 5
Duration: 10.2s

✗ System not ready - fix failures above
```

---

### Preflight Summary

**Total Steps:** 18  
**Total Time:** 10-30 seconds  
**Disk Space Used:** <1 MB (results files)  

**Checks Performed:**

| Category | Checks | Critical? |
|----------|--------|-----------|
| **System** | Python, FFmpeg, Docker, Docker Compose | Yes |
| **Directories** | 7 directories | Yes |
| **Configuration** | config/.env, INPUT_FILE | Partial |
| **Docker** | docker-compose.yml, images | No |
| **Secrets** | TMDB key, HF token | No |
| **Hardware** | Disk space, CUDA/MPS/CPU | Partial |

**Files Created:**
```
out/
└── preflight_results.json           # Cached (24h validity)

logs/
└── preflight_20241106_152530.json   # Timestamped archive
```

**Exit Codes:**
- `0` = All critical checks passed
- `1` = One or more critical checks failed

---

## 🔄 Complete Workflow Example

### First-Time Setup

```bash
# Step 1: Clone repository
git clone repo
cd cp-whisperx-app

# Step 2: Bootstrap (5-15 min)
.\scripts\bootstrap.ps1
# → Creates .bollyenv/
# → Installs 70+ packages
# → ~3 GB download

# Step 3: Configure (manual)
# Create config/.env
# Create config/secrets.json

# Step 4: Preflight (30 sec)
.\preflight.ps1
# → Validates 18 checks
# → Saves results

# Step 5: Ready!
```

### Daily Use

```bash
# Step 1: Preflight (cached, instant)
.\preflight.ps1
# → Reads cache: "✓ Passed 2h ago"
# → Skips checks

# Step 2: Run pipeline
.\prepare-job.ps1 movie.mp4
.\run_pipeline.ps1 -Job 20241106-0001
```

---

**Created:** 2024-11-06  
**Version:** 1.0.0  
**Purpose:** Detailed execution documentation
