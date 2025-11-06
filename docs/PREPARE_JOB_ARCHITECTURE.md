# prepare-job.py - Architecture & Workflow

**Job Preparation System for CP-WhisperX-App Pipeline**

---

## 📋 Overview

`prepare-job.py` is the entry point for the CP-WhisperX-App pipeline. It creates job directories, prepares media files, detects hardware capabilities, and generates optimized configuration files for pipeline execution.

### Purpose

- **Job Creation**: Create structured job directories with unique identifiers
- **Media Preparation**: Copy or clip media files for processing
- **Hardware Detection**: Auto-detect GPU/CPU capabilities and optimize settings
- **Configuration Generation**: Create job-specific `.env` files with optimal parameters
- **Workflow Selection**: Configure transcribe-only or full subtitle-generation workflows

---

## 🏗️ Architecture

### Component Overview

```
prepare-job.py
├── Command-line Interface (argparse)
├── Hardware Detection (detect_hardware_capabilities)
├── Device Detection (detect_device_capability)
├── Job Manager (JobManager class)
│   ├── Job Creation
│   ├── Media Preparation (FFmpeg clipping)
│   └── Configuration Generation
└── Logging (PipelineLogger)
```

### Key Classes

#### **JobManager**
Central orchestrator for job preparation.

```python
class JobManager:
    def __init__(self, output_root: Path, logger: PipelineLogger)
    def create_job(...) -> Dict            # Create job directory structure
    def prepare_media(...) -> Path         # Prepare media (copy/clip)
    def finalize_job(...) -> None          # Generate .env configuration
```

**Responsibilities:**
- Generate unique job IDs
- Create hierarchical output directories
- Coordinate media preparation
- Generate optimized configuration

---

## 📂 Job Directory Structure

### Hierarchical Organization

Jobs are organized by date and user for easy management:

```
out/
└── YYYY/                    # Year (e.g., 2024)
    └── MM/                  # Month (e.g., 11)
        └── DD/              # Day (e.g., 06)
            └── USER_ID/     # User ID (default: 1)
                └── JOB_ID/  # Job ID (YYYYMMDD-NNNN)
                    ├── job.json              # Job metadata
                    ├── .YYYYMMDD-NNNN.env   # Job configuration
                    ├── movie.mp4             # Input media
                    └── logs/                 # Stage logs (created during pipeline)
```

### Job ID Format

**Format:** `YYYYMMDD-NNNN`

- `YYYYMMDD`: Date (e.g., 20241106)
- `NNNN`: Sequential job number (0001, 0002, ...)

**Example:** `20241106-0003` = Third job on November 6, 2024

### File Naming Convention

**Full Media:**
```
out/2024/11/06/1/20241106-0001/movie.mp4
```

**Clipped Media:**
```
out/2024/11/06/1/20241106-0002/movie_clip_0002.mp4
```
Format: `{original_name}_clip_{job_number}.{ext}`

---

## 🔄 Workflow Process

### High-Level Flow

```
┌────────────────────────────────────────────────────────────────┐
│ 1. Parse Command-Line Arguments                               │
│    - Input media path                                          │
│    - Workflow mode (transcribe/subtitle-gen)                   │
│    - Native/Docker mode                                        │
│    - Clip times (optional)                                     │
└────────────────────────────────────────────────────────────────┘
                            ↓
┌────────────────────────────────────────────────────────────────┐
│ 2. Detect Hardware Capabilities                               │
│    - CPU cores and threads                                     │
│    - System memory                                             │
│    - GPU detection (CUDA/MPS/none)                             │
│    - GPU memory                                                │
└────────────────────────────────────────────────────────────────┘
                            ↓
┌────────────────────────────────────────────────────────────────┐
│ 3. Calculate Optimal Settings                                 │
│    - Whisper model selection                                   │
│    - Batch size tuning                                         │
│    - Compute type (float16/float32/int8)                       │
│    - Chunk length optimization                                 │
│    - Max speakers configuration                                │
└────────────────────────────────────────────────────────────────┘
                            ↓
┌────────────────────────────────────────────────────────────────┐
│ 4. Create Job Directory Structure                             │
│    - Generate unique job ID                                    │
│    - Create out/YYYY/MM/DD/USER_ID/JOB_ID/                    │
│    - Initialize job.json                                       │
└────────────────────────────────────────────────────────────────┘
                            ↓
┌────────────────────────────────────────────────────────────────┐
│ 5. Prepare Media                                              │
│    ├─ Full Media: Copy to job directory                       │
│    └─ Clipped Media: FFmpeg extract (--start-time/--end-time) │
└────────────────────────────────────────────────────────────────┘
                            ↓
┌────────────────────────────────────────────────────────────────┐
│ 6. Generate Job Configuration                                 │
│    - Load config/.env.pipeline template                        │
│    - Apply hardware optimizations                              │
│    - Set workflow-specific settings                            │
│    - Save as .{JOB_ID}.env                                     │
└────────────────────────────────────────────────────────────────┘
                            ↓
┌────────────────────────────────────────────────────────────────┐
│ 7. Finalize Job                                               │
│    - Update job.json with final metadata                       │
│    - Set status to "ready"                                     │
│    - Log summary and next steps                                │
└────────────────────────────────────────────────────────────────┘
```

### Detailed Step Breakdown

#### Step 1: Argument Parsing

```bash
python prepare-job.py /path/to/movie.mp4 --transcribe --native --start-time 00:10:00 --end-time 00:15:00
```

**Parsed:**
- `input_media`: `/path/to/movie.mp4`
- `workflow_mode`: `transcribe`
- `native_mode`: `True`
- `start_time`: `00:10:00`
- `end_time`: `00:15:00`

#### Step 2: Hardware Detection

```python
hw_info = detect_hardware_capabilities()
```

**Detects:**
- CPU: Cores, threads
- Memory: Total RAM in GB
- GPU: Type (CUDA/MPS/none), name, VRAM

**Example Output:**
```python
{
    'cpu_cores': 8,
    'cpu_threads': 16,
    'memory_gb': 32.0,
    'gpu_available': True,
    'gpu_type': 'cuda',
    'gpu_name': 'NVIDIA GeForce RTX 4090',
    'gpu_memory_gb': 24.0
}
```

**GPU Detection Logic:**
```python
import torch

if torch.cuda.is_available():
    # NVIDIA GPU with CUDA
    gpu_type = 'cuda'
    gpu_name = torch.cuda.get_device_name(0)
    
elif torch.backends.mps.is_available():
    # Apple Silicon with MPS
    gpu_type = 'mps'
    gpu_name = 'Apple Silicon (MPS)'
    
else:
    # CPU fallback
    gpu_type = 'cpu'
```

#### Step 3: Settings Optimization

```python
settings = _calculate_optimal_settings(hw_info)
```

**Decision Matrix:**

| Hardware | Whisper Model | Batch Size | Compute Type | Reason |
|----------|---------------|------------|--------------|--------|
| RTX 4090 (24GB) | large-v3 | 32 | float16 | High VRAM |
| RTX 3060 (12GB) | large-v3 | 16 | float16 | Moderate VRAM |
| RTX 2060 (6GB) | medium | 8 | float16 | Limited VRAM |
| M1 Max (16GB) | large-v3 | 16 | float32 | MPS requires FP32 |
| CPU (32GB RAM) | medium | 16 | int8 | CPU benefits from INT8 |
| CPU (8GB RAM) | base | 4 | int8 | Limited RAM |

**Optimization Logic:**
```python
# Model selection
if gpu_memory_gb >= 10:
    model = 'large-v3'
elif gpu_memory_gb >= 6:
    model = 'medium'
else:
    model = 'base'

# Batch size
if gpu_memory_gb >= 12:
    batch_size = 32
elif gpu_memory_gb >= 8:
    batch_size = 16
else:
    batch_size = 8

# Compute type
if gpu_type == 'cuda':
    compute_type = 'float16'
elif gpu_type == 'mps':
    compute_type = 'float32'
else:
    compute_type = 'int8'
```

#### Step 4: Job Directory Creation

```python
job_info = manager.create_job(
    input_media=Path('/path/to/movie.mp4'),
    workflow_mode='transcribe',
    native_mode=True,
    start_time='00:10:00',
    end_time='00:15:00'
)
```

**Creates:**
```
out/2024/11/06/1/20241106-0001/
├── job.json (initial metadata)
```

**job.json (initial):**
```json
{
  "job_id": "20241106-0001",
  "job_no": 1,
  "user_id": 1,
  "created_at": "2024-11-06T10:30:45.123456",
  "job_dir": "C:/Users/user/cp-whisperx-app/out/2024/11/06/1/20241106-0001",
  "source_media": "C:/Users/user/Movies/movie.mp4",
  "workflow_mode": "transcribe",
  "native_mode": true,
  "is_clip": true,
  "clip_start": "00:10:00",
  "clip_end": "00:15:00",
  "status": "preparing"
}
```

#### Step 5: Media Preparation

**Full Media (no clipping):**
```python
shutil.copy2(input_media, job_dir / input_media.name)
```

**Clipped Media:**
```python
ffmpeg -i input.mp4 -ss 00:10:00 -to 00:15:00 -c copy -y output_clip_0001.mp4
```

#### Step 6: Configuration Generation

**Template Loading:**
```python
config_template = Path('config/.env.pipeline')
with open(config_template) as f:
    config_content = f.read()
```

**Variable Substitution:**
```python
# Job-specific
JOB_ID=20241106-0001
IN_ROOT=/path/to/job/movie.mp4
OUTPUT_ROOT=out/2024/11/06/1/20241106-0001
LOG_ROOT=out/2024/11/06/1/20241106-0001/logs

# Hardware-optimized
WHISPER_MODEL=large-v3        # Based on GPU memory
BATCH_SIZE=32                  # Based on VRAM
COMPUTE_TYPE=float16           # Based on GPU type
CHUNK_LENGTH=30                # Based on memory
MAX_SPEAKERS=10                # Based on resources

# Device configuration (native mode)
DEVICE_WHISPERX=cuda           # Auto-detected
DEVICE_DIARIZATION=cuda
DEVICE_VAD=cuda

# Workflow overrides (transcribe mode)
WORKFLOW_MODE=transcribe
STEP_DIARIZATION=false
STEP_SUBTITLE_GEN=false
STEP_MUX=false
```

**Output File:**
```
out/2024/11/06/1/20241106-0001/.20241106-0001.env
```

#### Step 7: Job Finalization

**Update job.json:**
```json
{
  "job_id": "20241106-0001",
  ...
  "env_file": "C:/Users/user/.../20241106-0001/.20241106-0001.env",
  "status": "ready",
  "hardware": {
    "cpu_cores": 8,
    "memory_gb": 32.0,
    "gpu_type": "cuda",
    "gpu_name": "NVIDIA GeForce RTX 4090",
    "optimized_settings": {
      "whisper_model": "large-v3",
      "batch_size": 32,
      "compute_type": "float16"
    }
  }
}
```

---

## 🎛️ Hardware Detection System

### Detection Functions

#### `detect_hardware_capabilities()`

**Purpose:** Comprehensive hardware detection and settings optimization.

**Returns:**
```python
{
    'cpu_cores': int,           # Physical cores
    'cpu_threads': int,         # Logical threads
    'memory_gb': float,         # Total RAM
    'gpu_available': bool,      # GPU detected
    'gpu_type': str,            # 'cuda', 'mps', or 'cpu'
    'gpu_memory_gb': float,     # GPU VRAM
    'gpu_name': str,            # GPU model name
    'recommended_settings': {   # Optimized settings
        'whisper_model': str,
        'batch_size': int,
        'compute_type': str,
        'device_whisperx': str,
        'chunk_length_s': int,
        'max_speakers': int
    }
}
```

**Detection Flow:**
```python
import psutil
import torch

# CPU detection
cpu_cores = psutil.cpu_count(logical=False)
cpu_threads = psutil.cpu_count(logical=True)
memory_gb = psutil.virtual_memory().total / (1024**3)

# GPU detection
if torch.cuda.is_available():
    gpu_type = 'cuda'
    gpu_name = torch.cuda.get_device_name(0)
    gpu_memory = torch.cuda.get_device_properties(0).total_memory
    
elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
    gpu_type = 'mps'
    gpu_name = 'Apple Silicon (MPS)'
    gpu_memory = estimate_mps_memory()  # Based on system RAM
    
else:
    gpu_type = 'cpu'
```

#### `detect_device_capability()`

**Purpose:** Simplified device detection for native mode.

**Returns:** `'cuda'`, `'mps'`, or `'cpu'`

**Usage:**
```python
device = detect_device_capability()
# Used for DEVICE_WHISPERX, DEVICE_DIARIZATION, etc.
```

### GPU Detection Requirements

**For CUDA Detection:**
1. ✅ NVIDIA GPU installed
2. ✅ NVIDIA drivers installed (`nvidia-smi` works)
3. ❌ PyTorch with CUDA support (CPU-only version won't detect)

**Common Issue:**
```bash
# nvidia-smi works ✓
nvidia-smi

# But PyTorch can't see GPU ✗
python -c "import torch; print(torch.cuda.is_available())"  # False

# Cause: PyTorch CPU-only version installed
python -c "import torch; print(torch.__version__)"  # 2.8.0+cpu
```

**Solution:**
```bash
# Uninstall CPU version
pip uninstall torch torchvision torchaudio

# Install CUDA version
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
```

---

## ⚙️ Configuration Generation

### Template System

**Template Location:** `config/.env.pipeline`

**Template Structure:**
```bash
# Job Configuration
JOB_ID=
IN_ROOT=

# Output
OUTPUT_ROOT=
LOG_ROOT=

# Whisper Model Configuration
WHISPER_MODEL=large-v3

# Devices
DEVICE_WHISPERX=cpu
DEVICE_DIARIZATION=cpu
DEVICE_VAD=cpu

# Workflow
WORKFLOW_MODE=subtitle-gen
STEP_DIARIZATION=true
STEP_SUBTITLE_GEN=true
```

### Configuration Sections

#### **Job Identification**
```bash
JOB_ID=20241106-0001
IN_ROOT=/path/to/job/20241106-0001/movie.mp4
OUTPUT_ROOT=out/2024/11/06/1/20241106-0001
LOG_ROOT=out/2024/11/06/1/20241106-0001/logs
```

#### **Hardware Optimization Comments**
```bash
# ============================================================================
# HARDWARE DETECTION & OPTIMIZATION
# ============================================================================
# CPU: 8 cores (16 threads)
# Memory: 32.0 GB RAM
# GPU: NVIDIA GeForce RTX 4090
# GPU Memory: 24.0 GB
# GPU Type: CUDA
#
# RECOMMENDATION: GPU acceleration available
# Docker: Use cuda images with CPU fallback enabled
# ============================================================================
```

#### **Optimized Settings**
```bash
# Hardware-optimized model selection
# GPU has 24.0GB VRAM - can handle large-v3
WHISPER_MODEL=large-v3

# Batch size optimized for available resources
# High VRAM available
BATCH_SIZE=32

# Compute type optimized for device
# CUDA supports FP16 for faster computation
COMPUTE_TYPE=float16

# Chunk length tuned for memory constraints
# High memory - optimal chunk size
CHUNK_LENGTH=30

# Max speakers based on resource availability
# Sufficient resources for complex scenes
MAX_SPEAKERS=10
```

#### **Device Configuration (Native Mode)**
```bash
# Device set to: CUDA
DEVICE_WHISPERX=cuda
DEVICE_DIARIZATION=cuda
DEVICE_VAD=cuda
DEVICE_NER=cuda
```

#### **Workflow Overrides (Transcribe Mode)**
```bash
# ============================================================================
# TRANSCRIBE WORKFLOW OVERRIDES
# ============================================================================
# Simplified pipeline - only transcription, no diarization or subtitles
WORKFLOW_MODE=transcribe
STEP_DIARIZATION=false
STEP_SUBTITLE_GEN=false
STEP_MUX=false
SECOND_PASS_ENABLED=false
LYRIC_DETECT_ENABLED=false
POST_NER_ENTITY_CORRECTION=false
POST_NER_TMDB_MATCHING=false
```

#### **Resource Monitoring Recommendations**
```bash
# ============================================================================
# RESOURCE MONITORING RECOMMENDATIONS
# ============================================================================
# WARNING: Low memory detected (if < 16GB)
# - Monitor memory usage during processing
# - Consider processing in smaller chunks
# - Use smaller Whisper model if OOM occurs
#
# WARNING: Limited GPU memory (if < 8GB)
# - Reduce batch size if OOM errors occur
# - Monitor GPU memory with: nvidia-smi (CUDA) or Activity Monitor (MPS)
# - CPU fallback will activate automatically if GPU fails
```

---

## 🎯 Workflow Modes

### 1. Transcribe Workflow

**Purpose:** Fast transcription only (no speaker labels).

**Configuration:**
```bash
python prepare-job.py movie.mp4 --transcribe
```

**Pipeline Stages:**
- ✅ Audio extraction
- ✅ VAD (Voice Activity Detection)
- ✅ Transcription (WhisperX)
- ❌ Speaker diarization
- ❌ Named entity recognition
- ❌ Subtitle generation
- ❌ Video muxing

**Use Cases:**
- Quick transcripts
- Testing and development
- When speaker labels not needed

**Output:**
- `transcription.json`: Raw transcript
- Logs only (no subtitles)

### 2. Subtitle Generation Workflow

**Purpose:** Full pipeline with speaker diarization and subtitles.

**Configuration:**
```bash
python prepare-job.py movie.mp4 --subtitle-gen  # or omit (default)
```

**Pipeline Stages:**
- ✅ Audio extraction
- ✅ VAD (Voice Activity Detection)
- ✅ Transcription (WhisperX)
- ✅ Speaker diarization (PyAnnote)
- ✅ Named entity recognition (spaCy + TMDB)
- ✅ Subtitle generation (SRT format)
- ✅ Video muxing (embedded subtitles)

**Optional Enhancements:**
- Second-pass translation (15-20% quality boost for Hinglish)
- Lyrics detection (20-25% improvement for songs)

**Use Cases:**
- Production subtitle generation
- Bollywood movies
- Multi-speaker content

**Output:**
- `movie.srt`: Subtitle file
- `movie_subtitled.mkv`: Video with embedded subtitles
- Complete stage logs

---

## 🚀 Execution Modes

### Native Mode

**Activation:**
```bash
python prepare-job.py movie.mp4 --native
```

**Characteristics:**
- Direct Python execution
- Auto-detects GPU (CUDA/MPS)
- Fastest performance
- Requires local dependencies

**Device Detection:**
```python
device = detect_device_capability()  # 'cuda', 'mps', or 'cpu'
```

**Configuration:**
```bash
DEVICE_WHISPERX=cuda      # Auto-detected
DEVICE_DIARIZATION=cuda
DEVICE_VAD=cuda
```

### Docker Mode (Default)

**Activation:**
```bash
python prepare-job.py movie.mp4  # No --native flag
```

**Characteristics:**
- Containerized execution
- Isolated environment
- CPU/GPU fallback support
- Slower than native

**Configuration:**
```bash
USE_GPU_FALLBACK=true     # Enable CPU fallback if GPU fails
```

---

## 📄 Job Metadata

### job.json Structure

**Location:** `out/YYYY/MM/DD/USER_ID/JOB_ID/job.json`

**Complete Schema:**
```json
{
  "job_id": "20241106-0001",
  "job_no": 1,
  "user_id": 1,
  "created_at": "2024-11-06T10:30:45.123456",
  "job_dir": "/absolute/path/to/out/2024/11/06/1/20241106-0001",
  "source_media": "/absolute/path/to/original/movie.mp4",
  "workflow_mode": "transcribe",
  "native_mode": true,
  "is_clip": true,
  "clip_start": "00:10:00",
  "clip_end": "00:15:00",
  "status": "ready",
  "env_file": "/absolute/path/to/.20241106-0001.env",
  "hardware": {
    "cpu_cores": 8,
    "cpu_threads": 16,
    "memory_gb": 32.0,
    "gpu_type": "cuda",
    "gpu_name": "NVIDIA GeForce RTX 4090",
    "gpu_memory_gb": 24.0,
    "optimized_settings": {
      "whisper_model": "large-v3",
      "whisper_model_reason": "GPU has 24.0GB VRAM - can handle large-v3",
      "batch_size": 32,
      "batch_size_reason": "High VRAM available",
      "compute_type": "float16",
      "compute_type_reason": "CUDA supports FP16 for faster computation",
      "device_whisperx": "cuda",
      "device_diarization": "cuda",
      "device_vad": "cuda",
      "chunk_length_s": 30,
      "chunk_length_reason": "High memory - optimal chunk size",
      "max_speakers": 10,
      "max_speakers_reason": "Sufficient resources for complex scenes"
    }
  }
}
```

**Status Values:**
- `preparing`: Job being created
- `ready`: Ready for pipeline execution
- `running`: Pipeline in progress (set by pipeline.py)
- `completed`: Pipeline finished successfully
- `failed`: Pipeline encountered error

---

## 🛠️ Command-Line Interface

### Basic Usage

```bash
python prepare-job.py <input_media> [OPTIONS]
```

### Options

| Option | Description | Example |
|--------|-------------|---------|
| `input_media` | Path to input video/audio | `movie.mp4` |
| `--transcribe` | Transcribe-only workflow | `--transcribe` |
| `--subtitle-gen` | Full subtitle workflow (default) | `--subtitle-gen` |
| `--native` | Enable native GPU execution | `--native` |
| `--start-time TIME` | Clip start time (HH:MM:SS) | `--start-time 00:10:00` |
| `--end-time TIME` | Clip end time (HH:MM:SS) | `--end-time 00:15:00` |

### Examples

**1. Full subtitle generation (default):**
```bash
python prepare-job.py /path/to/movie.mp4
```

**2. Transcribe only (faster):**
```bash
python prepare-job.py /path/to/movie.mp4 --transcribe
```

**3. Native mode with GPU acceleration:**
```bash
python prepare-job.py /path/to/movie.mp4 --native
```

**4. Process 5-minute clip for testing:**
```bash
python prepare-job.py /path/to/movie.mp4 --start-time 00:10:00 --end-time 00:15:00
```

**5. Transcribe clip with native GPU:**
```bash
python prepare-job.py /path/to/movie.mp4 --transcribe --native --start-time 00:05:00 --end-time 00:10:00
```

### Validation Rules

**Clip Times:**
- Both `--start-time` and `--end-time` required together
- Format: `HH:MM:SS`
- End time must be after start time

**Workflow Flags:**
- Cannot specify both `--transcribe` and `--subtitle-gen`
- Default is `--subtitle-gen` if omitted

**Input Media:**
- Must exist and be accessible
- Supported formats: MP4, MKV, AVI, MOV, WAV, MP3

---

## 📊 Logging

### Log Files

**Location:** `logs/prepare-job/prepare-job_YYYYMMDD_HHMMSS.log`

**Example:**
```
logs/
└── prepare-job/
    ├── prepare-job_20241106_103045.log
    ├── prepare-job_20241106_110532.log
    └── prepare-job_20241106_114821.log
```

### Log Format

```
2024-11-06 10:30:45 [INFO] ============================================================
2024-11-06 10:30:45 [INFO] CP-WHISPERX-APP JOB PREPARATION
2024-11-06 10:30:45 [INFO] ============================================================
2024-11-06 10:30:45 [INFO] Input media: /path/to/movie.mp4
2024-11-06 10:30:45 [INFO] Workflow: TRANSCRIBE
2024-11-06 10:30:45 [INFO] Native mode: ENABLED (detected: CUDA)
2024-11-06 10:30:45 [INFO] Detecting hardware capabilities...
2024-11-06 10:30:46 [INFO] CPU: 8 cores, 16 threads
2024-11-06 10:30:46 [INFO] Memory: 32.0 GB
2024-11-06 10:30:46 [INFO] GPU: NVIDIA GeForce RTX 4090 (CUDA)
2024-11-06 10:30:46 [INFO] GPU Memory: 24.0 GB
2024-11-06 10:30:46 [INFO] Job created: 20241106-0001
2024-11-06 10:30:46 [INFO] Directory: out/2024/11/06/1/20241106-0001
2024-11-06 10:30:46 [INFO] Copying media file...
2024-11-06 10:30:48 [INFO] Media copied: out/.../movie.mp4
2024-11-06 10:30:48 [INFO] Using config template: config/.env.pipeline
2024-11-06 10:30:48 [INFO] Applying hardware-optimized settings...
2024-11-06 10:30:48 [INFO] Configuration saved: .20241106-0001.env
2024-11-06 10:30:48 [INFO] ============================================================
2024-11-06 10:30:48 [INFO] JOB PREPARATION COMPLETE
2024-11-06 10:30:48 [INFO] ============================================================
```

### Log Levels

Controlled by `LOG_LEVEL` environment variable:

- `DEBUG`: Detailed diagnostic information
- `INFO`: General informational messages (default)
- `WARN`: Warning messages
- `ERROR`: Error messages

**Set log level:**
```bash
$env:LOG_LEVEL="DEBUG"
python prepare-job.py movie.mp4
```

---

## 🔧 Integration with Pipeline

### Pipeline Execution

After `prepare-job.py` completes:

```bash
# prepare-job.py output
✓ Job created: 20241106-0001
  Directory: out/2024/11/06/1/20241106-0001
  Workflow: TRANSCRIBE
  
Next step:
  python pipeline.py --job 20241106-0001
```

**Run pipeline:**
```bash
python pipeline.py --job 20241106-0001
```

### Pipeline Job Loading

**pipeline.py loads:**
1. Job metadata: `out/.../20241106-0001/job.json`
2. Configuration: `out/.../20241106-0001/.20241106-0001.env`
3. Input media: `out/.../20241106-0001/movie.mp4`

**Pipeline respects:**
- Workflow mode (transcribe/subtitle-gen)
- Hardware settings (model, batch size, etc.)
- Device configuration (CUDA/MPS/CPU)
- All optimizations from prepare-job.py

---

## 🐛 Troubleshooting

### GPU Not Detected

**Symptom:**
```
[WARNING] No GPU detected - CPU-only execution
```

**Cause:** PyTorch CPU-only version installed

**Check:**
```bash
python -c "import torch; print(torch.__version__)"
# Output: 2.8.0+cpu  (CPU version)
```

**Fix:**
```bash
# Uninstall CPU version
pip uninstall torch torchvision torchaudio

# Install CUDA version
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
```

### FFmpeg Not Found

**Symptom:**
```
[ERROR] FFmpeg failed: FileNotFoundError
```

**Fix:**
```bash
# Windows
winget install FFmpeg

# Linux
sudo apt install ffmpeg

# macOS
brew install ffmpeg
```

### Invalid Clip Times

**Symptom:**
```
✗ Both --start-time and --end-time must be specified together
```

**Fix:**
```bash
# Correct usage
python prepare-job.py movie.mp4 --start-time 00:10:00 --end-time 00:15:00
```

### Template Not Found

**Symptom:**
```
[ERROR] Config template not found: config/.env.pipeline
```

**Fix:**
```bash
# Ensure config/.env.pipeline exists
ls config/.env.pipeline

# If missing, copy from example
cp config/.env.example config/.env.pipeline
```

---

## 📈 Performance Considerations

### Hardware Optimization Impact

| Hardware | Default Settings | Optimized Settings | Performance Gain |
|----------|------------------|-------------------|------------------|
| RTX 4090 | medium, batch=8 | large-v3, batch=32 | 3-4x faster |
| RTX 3060 | base, batch=4 | large-v3, batch=16 | 2-3x faster |
| M1 Max | base, batch=8 | large-v3, batch=16 | 2x faster |
| CPU (32GB) | tiny, batch=2 | medium, batch=16 | 1.5x faster |

### Workflow Performance

**Transcribe vs Subtitle-Gen (2-hour movie):**

| Configuration | Transcribe | Subtitle-Gen | Difference |
|---------------|------------|--------------|------------|
| RTX 4090 | 12 min | 45 min | +33 min |
| RTX 3060 | 25 min | 90 min | +65 min |
| M1 Max | 35 min | 120 min | +85 min |
| CPU | 4 hr | 8 hr | +4 hr |

---

## 🔐 Security Considerations

### File Permissions

- Job directories: `755` (rwxr-xr-x)
- Job files: `644` (rw-r--r--)
- Environment files: `600` (rw-------) - Contains potential secrets

### Path Validation

- Input paths validated before processing
- Symbolic links resolved to prevent directory traversal
- Absolute paths used throughout

### API Keys

Environment files may contain:
- TMDB API keys
- HuggingFace tokens

**Never commit `.env` files to version control!**

---

## 🚀 Future Enhancements

### Planned Features

1. **Multi-user support**: User authentication and isolation
2. **Job queue**: Priority-based job scheduling
3. **Cloud storage**: S3/Azure Blob integration
4. **Web interface**: Job submission via web UI
5. **Advanced clipping**: Multiple clips per job
6. **Batch processing**: Multiple files in one job

### Optimization Opportunities

1. **Model caching**: Pre-download models during setup
2. **GPU memory profiling**: More accurate VRAM detection
3. **Dynamic batch sizing**: Adjust batch size based on actual usage
4. **Multi-GPU support**: Distribute processing across GPUs

---

## 📚 Related Documentation

- **[Workflow Architecture](WORKFLOW_ARCHITECTURE.md)** - Complete pipeline design
- **[Job Orchestration](JOB_ORCHESTRATION.md)** - Pipeline execution details
- **[Hardware Optimization](HARDWARE_OPTIMIZATION.md)** - Hardware tuning guide
- **[Logging Standard](LOGGING_STANDARD.md)** - Logging conventions
- **[CUDA Acceleration Guide](guides/hardware/cuda-acceleration.md)** - NVIDIA GPU setup
- **[MPS Acceleration Guide](guides/hardware/mps-acceleration.md)** - Apple Silicon setup

---

## 📝 Summary

**prepare-job.py** is a sophisticated job preparation system that:

1. ✅ **Auto-detects hardware** (CPU, GPU, memory)
2. ✅ **Optimizes settings** (model, batch size, compute type)
3. ✅ **Creates structured jobs** (hierarchical directories)
4. ✅ **Prepares media** (copy or clip with FFmpeg)
5. ✅ **Generates configuration** (job-specific `.env` files)
6. ✅ **Supports workflows** (transcribe vs subtitle-gen)
7. ✅ **Enables acceleration** (CUDA, MPS, or CPU)

**Next Step:** Execute pipeline with `python pipeline.py --job <JOB_ID>`

---

**Last Updated:** 2024-11-06  
**Version:** 1.0.0
