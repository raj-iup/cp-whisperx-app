#!/usr/bin/env python3
"""
Job Preparation Script for CP-WhisperX-App Pipeline

Creates job directory structure and prepares configuration based on parameters.
Copies config/.env.pipeline template and customizes it for the job.

Usage:
    python prepare-job.py <input_media> [OPTIONS]

Options:
    --transcribe          Transcribe-only workflow (faster, 3 stages)
    --transcribe-only     Transcription only (6 stages, includes VAD)
    --translate-only      Translation only (9 stages, reuses existing transcription)
    --subtitle-gen        Full pipeline (default, 15 stages)
    --source-language     Source language code (e.g., hi, es, ja, auto)
    --target-language     Target language code (e.g., en, es, fr, de)
    --native              Enable native GPU acceleration (MPS/CUDA)
    --start-time TIME     Start time for clip (HH:MM:SS)
    --end-time TIME       End time for clip (HH:MM:SS)

Examples:
    # Full subtitle generation (default): Hindi → English
    python prepare-job.py /path/to/movie.mp4
    
    # Spanish to English workflow
    python prepare-job.py /path/to/movie.mp4 --transcribe-only --source-language es
    python prepare-job.py /path/to/movie.mp4 --translate-only --source-language es --target-language en
    
    # Japanese to multiple targets
    python prepare-job.py /path/to/anime.mp4 --transcribe-only --source-language ja
    python prepare-job.py /path/to/anime.mp4 --translate-only --source-language ja --target-language en
    python prepare-job.py /path/to/anime.mp4 --translate-only --source-language ja --target-language es

Job Creation Process:
    1. Create job directory: out/YYYY/MM/DD/<user-id>/<job-id>/
    2. Copy config/.env.pipeline template
    3. Customize configuration based on parameters
    4. Prepare media (clip or copy)
    5. Save job.json definition
    6. Generate final .<job-id>.env file
"""

import sys
import os
import json
import shutil
import argparse
import subprocess
import psutil
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict

# Add paths for imports
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.logger import PipelineLogger, get_stage_log_filename
from scripts.filename_parser import parse_filename


# IndicTrans2 Language Mapping - Indic languages that can use IndicTrans2
INDIC_LANGUAGES = {
    "hi", "as", "bn", "gu", "kn", "ml", "mr", "or", "pa", "ta", "te", "ur",
    "ne", "sd", "si", "sa", "ks", "doi", "mni", "kok", "mai", "sat"
}

def is_indic_language(lang_code: str) -> bool:
    """Check if language code is an Indic language supported by IndicTrans2."""
    return lang_code in INDIC_LANGUAGES


# Supported language codes (90+ languages supported by Whisper)
SUPPORTED_LANGUAGES = {
    # Auto-detect
    'auto': 'Auto-detect',
    
    # South Asian
    'hi': 'Hindi',
    'ur': 'Urdu',
    'ta': 'Tamil',
    'te': 'Telugu',
    'bn': 'Bengali',
    'mr': 'Marathi',
    'gu': 'Gujarati',
    'kn': 'Kannada',
    'ml': 'Malayalam',
    'pa': 'Punjabi',
    'sd': 'Sindhi',
    'ne': 'Nepali',
    'si': 'Sinhala',
    
    # European
    'en': 'English',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'it': 'Italian',
    'pt': 'Portuguese',
    'ru': 'Russian',
    'nl': 'Dutch',
    'pl': 'Polish',
    'uk': 'Ukrainian',
    'cs': 'Czech',
    'ro': 'Romanian',
    'sv': 'Swedish',
    'da': 'Danish',
    'no': 'Norwegian',
    'fi': 'Finnish',
    'el': 'Greek',
    'bg': 'Bulgarian',
    'hr': 'Croatian',
    'sr': 'Serbian',
    'sk': 'Slovak',
    'sl': 'Slovenian',
    'et': 'Estonian',
    'lv': 'Latvian',
    'lt': 'Lithuanian',
    'is': 'Icelandic',
    'ga': 'Irish',
    'cy': 'Welsh',
    'eu': 'Basque',
    'ca': 'Catalan',
    'gl': 'Galician',
    'mt': 'Maltese',
    'sq': 'Albanian',
    'mk': 'Macedonian',
    'be': 'Belarusian',
    
    # East Asian
    'ja': 'Japanese',
    'ko': 'Korean',
    'zh': 'Chinese',
    'yue': 'Cantonese',
    'my': 'Burmese',
    'lo': 'Lao',
    'km': 'Khmer',
    
    # Middle Eastern
    'ar': 'Arabic',
    'tr': 'Turkish',
    'fa': 'Persian',
    'he': 'Hebrew',
    'az': 'Azerbaijani',
    'kk': 'Kazakh',
    'uz': 'Uzbek',
    'ky': 'Kyrgyz',
    'tg': 'Tajik',
    'tk': 'Turkmen',
    
    # Southeast Asian
    'vi': 'Vietnamese',
    'id': 'Indonesian',
    'ms': 'Malay',
    'th': 'Thai',
    'tl': 'Tagalog',
    'jv': 'Javanese',
    
    # African
    'sw': 'Swahili',
    'yo': 'Yoruba',
    'ha': 'Hausa',
    'zu': 'Zulu',
    'af': 'Afrikaans',
    'am': 'Amharic',
    'so': 'Somali',
    
    # Other
    'mn': 'Mongolian',
    'hy': 'Armenian',
    'ka': 'Georgian',
    'bo': 'Tibetan',
    'la': 'Latin',
    'sa': 'Sanskrit',
    'mi': 'Maori',
    'haw': 'Hawaiian',
    'ps': 'Pashto',
    'sn': 'Shona',
    'mg': 'Malagasy',
    'oc': 'Occitan',
    'br': 'Breton',
    'lb': 'Luxembourgish',
    'fo': 'Faroese',
    'yi': 'Yiddish',
    'ht': 'Haitian Creole',
}


def validate_language_code(lang_code: str, arg_name: str = "language") -> str:
    """Validate language code against supported languages.
    
    Args:
        lang_code: Language code to validate
        arg_name: Argument name for error messages
    
    Returns:
        Validated language code (lowercase)
    
    Raises:
        SystemExit: If language code is not supported
    """
    if not lang_code:
        return None
    
    lang_lower = lang_code.lower()
    if lang_lower not in SUPPORTED_LANGUAGES:
        print(f"✗ Unsupported {arg_name}: {lang_code}")
        print(f"\nSupported languages ({len(SUPPORTED_LANGUAGES)}):")
        print("\nPopular languages:")
        popular = ['auto', 'hi', 'en', 'es', 'fr', 'de', 'it', 'ja', 'ko', 'zh', 'ar', 'pt', 'ru']
        for code in popular:
            if code in SUPPORTED_LANGUAGES:
                print(f"  {code:4s} - {SUPPORTED_LANGUAGES[code]}")
        print(f"\nFor complete list, see: https://github.com/openai/whisper#available-models-and-languages")
        sys.exit(1)
    
    return lang_lower


def detect_hardware_capabilities():
    """Detect hardware capabilities and recommend optimal settings.
    
    Returns:
        dict: Hardware capabilities and recommended settings
            {
                'cpu_cores': int,
                'memory_gb': float,
                'gpu_available': bool,
                'gpu_type': str,  # 'cuda', 'mps', or None
                'gpu_memory_gb': float or None,
                'gpu_name': str or None,
                'recommended_settings': dict
            }
    """
    import psutil
    import json
    from pathlib import Path
    
    # First, try to load from hardware_cache.json
    cache_file = Path("out/hardware_cache.json")
    if cache_file.exists():
        try:
            with open(cache_file, 'r') as f:
                cached_info = json.load(f)
            # Return cached hardware info with recommended settings
            return {
                'cpu_cores': cached_info.get('cpu_cores', psutil.cpu_count(logical=False) or 1),
                'cpu_threads': cached_info.get('cpu_threads', psutil.cpu_count(logical=True) or 1),
                'memory_gb': cached_info.get('memory_gb', round(psutil.virtual_memory().total / (1024**3), 2)),
                'gpu_available': cached_info.get('gpu_available', False),
                'gpu_type': cached_info.get('gpu_type', 'cpu'),
                'gpu_memory_gb': cached_info.get('gpu_memory_gb'),
                'gpu_name': cached_info.get('gpu_name'),
                'recommended_settings': cached_info.get('recommended_settings', {})
            }
        except Exception:
            pass  # Fall through to detection
    
    # If cache doesn't exist or failed to load, detect hardware
    hw_info = {
        'cpu_cores': psutil.cpu_count(logical=False) or 1,
        'cpu_threads': psutil.cpu_count(logical=True) or 1,
        'memory_gb': round(psutil.virtual_memory().total / (1024**3), 2),
        'gpu_available': False,
        'gpu_type': None,
        'gpu_memory_gb': None,
        'gpu_name': None,
        'recommended_settings': {}
    }
    
    # Detect GPU
    try:
        import torch
        
        # Check for CUDA
        if torch.cuda.is_available():
            hw_info['gpu_available'] = True
            hw_info['gpu_type'] = 'cuda'
            hw_info['gpu_name'] = torch.cuda.get_device_name(0)
            hw_info['gpu_memory_gb'] = round(
                torch.cuda.get_device_properties(0).total_memory / (1024**3), 2
            )
        # Check for MPS (Apple Silicon)
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            hw_info['gpu_available'] = True
            hw_info['gpu_type'] = 'mps'
            hw_info['gpu_name'] = 'Apple Silicon (MPS)'
            # MPS doesn't report memory, estimate based on system
            if hw_info['memory_gb'] >= 32:
                hw_info['gpu_memory_gb'] = 16  # Estimate for M1/M2 Max
            else:
                hw_info['gpu_memory_gb'] = 8   # Estimate for M1/M2 base
        else:
            hw_info['gpu_type'] = 'cpu'
    except Exception:
        hw_info['gpu_type'] = 'cpu'
    
    # Generate recommended settings
    hw_info['recommended_settings'] = _calculate_optimal_settings(hw_info)
    
    return hw_info


def _calculate_optimal_settings(hw_info: dict) -> dict:
    """Calculate optimal settings based on hardware capabilities.
    
    Args:
        hw_info: Hardware information dictionary
    
    Returns:
        dict: Recommended settings with explanations
    """
    settings = {
        'whisper_model': 'large-v3',
        'whisper_model_reason': '',
        'batch_size': 16,
        'batch_size_reason': '',
        'compute_type': 'float16',
        'compute_type_reason': '',
        'device_whisperx': 'cpu',
        'device_diarization': 'cpu',
        'device_vad': 'cpu',
        'chunk_length_s': 30,
        'chunk_length_reason': '',
        'max_speakers': 10,
        'max_speakers_reason': ''
    }
    
    memory_gb = hw_info['memory_gb']
    gpu_type = hw_info['gpu_type']
    gpu_memory_gb = hw_info.get('gpu_memory_gb', 0) or 0
    cpu_cores = hw_info['cpu_cores']
    
    # Model selection based on available memory
    if gpu_type in ['cuda', 'mps']:
        # GPU available
        if gpu_memory_gb >= 10:
            settings['whisper_model'] = 'large-v3'
            settings['whisper_model_reason'] = f'GPU has {gpu_memory_gb}GB VRAM - can handle large-v3'
        elif gpu_memory_gb >= 6:
            settings['whisper_model'] = 'medium'
            settings['whisper_model_reason'] = f'GPU has {gpu_memory_gb}GB VRAM - medium model recommended'
        else:
            settings['whisper_model'] = 'base'
            settings['whisper_model_reason'] = f'GPU has {gpu_memory_gb}GB VRAM - base model recommended'
        
        settings['device_whisperx'] = gpu_type
        settings['device_diarization'] = gpu_type
        settings['device_vad'] = gpu_type
    else:
        # CPU only
        if memory_gb >= 16:
            settings['whisper_model'] = 'medium'
            settings['whisper_model_reason'] = f'System has {memory_gb}GB RAM - medium model feasible'
        elif memory_gb >= 8:
            settings['whisper_model'] = 'base'
            settings['whisper_model_reason'] = f'System has {memory_gb}GB RAM - base model recommended'
        else:
            settings['whisper_model'] = 'tiny'
            settings['whisper_model_reason'] = f'System has {memory_gb}GB RAM - tiny model required'
        
        settings['device_whisperx'] = 'cpu'
        settings['device_diarization'] = 'cpu'
        settings['device_vad'] = 'cpu'
    
    # Batch size based on available resources
    if gpu_type in ['cuda', 'mps']:
        if gpu_memory_gb >= 12:
            settings['batch_size'] = 32
            settings['batch_size_reason'] = 'High VRAM available'
        elif gpu_memory_gb >= 8:
            settings['batch_size'] = 16
            settings['batch_size_reason'] = 'Moderate VRAM available'
        else:
            settings['batch_size'] = 8
            settings['batch_size_reason'] = 'Limited VRAM - conservative batch size'
    else:
        if memory_gb >= 32:
            settings['batch_size'] = 16
            settings['batch_size_reason'] = 'High RAM available'
        elif memory_gb >= 16:
            settings['batch_size'] = 8
            settings['batch_size_reason'] = 'Moderate RAM available'
        else:
            settings['batch_size'] = 4
            settings['batch_size_reason'] = 'Limited RAM - small batch size'
    
    # Compute type
    if gpu_type == 'cuda':
        settings['compute_type'] = 'float16'
        settings['compute_type_reason'] = 'CUDA supports FP16 for faster computation'
    elif gpu_type == 'mps':
        settings['compute_type'] = 'float32'
        settings['compute_type_reason'] = 'MPS requires FP32 (FP16 support limited)'
    else:
        settings['compute_type'] = 'int8'
        settings['compute_type_reason'] = 'CPU benefits from INT8 quantization'
    
    # Chunk length based on memory
    if memory_gb >= 32:
        settings['chunk_length_s'] = 30
        settings['chunk_length_reason'] = 'High memory - optimal chunk size'
    elif memory_gb >= 16:
        settings['chunk_length_s'] = 20
        settings['chunk_length_reason'] = 'Moderate memory - reduced chunk size'
    else:
        settings['chunk_length_s'] = 10
        settings['chunk_length_reason'] = 'Limited memory - small chunks to avoid OOM'
    
    # Max speakers based on complexity tolerance
    if gpu_type in ['cuda', 'mps'] or memory_gb >= 16:
        settings['max_speakers'] = 10
        settings['max_speakers_reason'] = 'Sufficient resources for complex scenes'
    else:
        settings['max_speakers'] = 5
        settings['max_speakers_reason'] = 'Limited resources - reduce diarization complexity'
    
    return settings


def detect_device_capability():
    """Detect available ML acceleration device (MPS, CUDA, or CPU).
    
    Returns:
        str: Device type - 'mps', 'cuda', or 'cpu'
    """
    try:
        import torch
        
        # Check for CUDA
        if torch.cuda.is_available():
            return 'cuda'
        
        # Check for MPS (Apple Silicon)
        if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            return 'mps'
        
        # Fallback to CPU
        return 'cpu'
    except Exception:
        return 'cpu'


class JobManager:
    """Manages job creation, tracking, and media preparation."""
    
    def __init__(self, output_root: Path = Path("out"), logger: Optional[PipelineLogger] = None):
        """Initialize job manager.
        
        Args:
            output_root: Root directory for all outputs (default: out/)
            logger: Optional logger instance
        """
        self.output_root = output_root
        self.output_root.mkdir(exist_ok=True, parents=True)
        self.logger = logger
    
    def _get_date_components(self) -> tuple:
        """Get current date components (year, month, day)."""
        now = datetime.now()
        return now.year, f"{now.month:02d}", f"{now.day:02d}"
    
    def _get_user_id(self) -> int:
        """Get user ID from environment or config."""
        # Try environment variable first
        user_id = os.environ.get('USER_ID', '1')
        try:
            return int(user_id)
        except ValueError:
            return 1
    
    def _get_next_job_number(self, year: str, month: str, day: str, user_id: int) -> int:
        """Get next job number for the given date and user.
        
        Scans existing job directories to find the highest job number.
        """
        user_dir = self.output_root / str(year) / month / day / str(user_id)
        if not user_dir.exists():
            return 1
        
        # Find all job directories matching YYYYMMDD-NNNN pattern
        import re
        pattern = re.compile(r'(\d{8})-(\d{4})')
        
        max_job_no = 0
        for item in user_dir.iterdir():
            if item.is_dir():
                match = pattern.match(item.name)
                if match:
                    job_no = int(match.group(2))
                    max_job_no = max(max_job_no, job_no)
        
        return max_job_no + 1
    
    def create_job(self, input_media: Path, workflow_mode: str = 'subtitle-gen', 
                   native_mode: bool = False, start_time: Optional[str] = None,
                   end_time: Optional[str] = None, stage_flags: Optional[Dict] = None,
                   source_language: Optional[str] = None, target_language: Optional[str] = None) -> Dict:
        """Create a new job with directory structure and job definition.
        
        Args:
            input_media: Path to input media file
            workflow_mode: Workflow mode - 'transcribe', 'transcribe-only', 'translate-only', or 'subtitle-gen'
            native_mode: Enable native execution with device acceleration
            start_time: Optional start time for clipping (HH:MM:SS)
            end_time: Optional end time for clipping (HH:MM:SS)
            stage_flags: Optional dict with stage enable/disable flags
                {
                    'silero_vad': bool or None,
                    'pyannote_vad': bool or None,
                    'diarization': bool or None
                }
            source_language: Source language code (e.g., hi, es, ja, auto)
            target_language: Target language code (e.g., en, es, fr, de)
        
        Returns:
            Dictionary with job information
        """
        # Get date components and user ID
        year, month, day = self._get_date_components()
        user_id = self._get_user_id()
        
        # Get next job number
        job_no = self._get_next_job_number(year, month, day, user_id)
        job_id = f"{year}{month}{day}-{job_no:04d}"
        
        # Create job directory: out/YYYY/MM/DD/USER_ID/JOB_ID/
        job_dir = self.output_root / str(year) / month / day / str(user_id) / job_id
        job_dir.mkdir(exist_ok=True, parents=True)
        
        # Job definition file
        job_json_file = job_dir / "job.json"
        
        # Validate translate-only mode prerequisites
        if workflow_mode == 'translate-only':
            # Check if segments.json exists from previous transcription
            segments_file = job_dir / "06_asr" / "segments.json"
            if not segments_file.exists():
                if self.logger:
                    self.logger.error(f"translate-only mode requires existing transcription")
                    self.logger.error(f"Missing: {segments_file}")
                    self.logger.error(f"")
                    self.logger.error(f"Please run --transcribe-only first:")
                    self.logger.error(f"  python prepare-job.py {input_media} --transcribe-only --source-language {source_language or 'auto'}")
                print(f"✗ translate-only mode requires existing transcription")
                print(f"  Missing: {segments_file}")
                print(f"")
                print(f"Please run --transcribe-only first:")
                print(f"  python prepare-job.py {input_media} --transcribe-only --source-language {source_language or 'auto'}")
                sys.exit(1)
        
        # Create job info (will be updated after media preparation)
        job_info = {
            "job_id": job_id,
            "job_no": job_no,
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "job_dir": str(job_dir.absolute()),
            "source_media": str(input_media.absolute()),
            "workflow_mode": workflow_mode,
            "native_mode": native_mode,
            "is_clip": bool(start_time and end_time),
            "status": "preparing"
        }
        
        # Add language settings
        if source_language:
            job_info["source_language"] = source_language
        if target_language:
            job_info["target_language"] = target_language
        
        if start_time and end_time:
            job_info["clip_start"] = start_time
            job_info["clip_end"] = end_time
        
        # Add stage control flags if provided
        if stage_flags:
            job_info["stage_flags"] = stage_flags
        
        # Save initial job definition
        with open(job_json_file, 'w') as f:
            json.dump(job_info, f, indent=2)
        
        if self.logger:
            self.logger.info(f"Job created: {job_id}")
            self.logger.info(f"User ID: {user_id}")
            self.logger.info(f"Workflow: {workflow_mode.upper()}")
            if source_language:
                lang_name = SUPPORTED_LANGUAGES.get(source_language, source_language)
                self.logger.info(f"Source language: {source_language} ({lang_name})")
            if target_language:
                lang_name = SUPPORTED_LANGUAGES.get(target_language, target_language)
                self.logger.info(f"Target language: {target_language} ({lang_name})")
            self.logger.info(f"Native mode: {'enabled' if native_mode else 'disabled'}")
            if stage_flags:
                self.logger.info("Stage controls:")
                for stage, enabled in stage_flags.items():
                    if enabled is not None:
                        status = "ENABLED" if enabled else "DISABLED"
                        self.logger.info(f"  {stage}: {status}")
            self.logger.info(f"Directory: {job_dir}")
            self.logger.info(f"Job definition: {job_json_file}")
        
        return job_info
    
    def _create_default_config(self) -> str:
        """Create minimal default configuration."""
        return """# CP-WhisperX-App Job Configuration

# Job Configuration
JOB_ID=
IN_ROOT=

# Output (auto-generated based on job structure)
OUTPUT_ROOT=
LOG_ROOT=

# Logging
LOG_LEVEL=info

# Secrets
SECRETS_PATH=./config/secrets.json

# Whisper Model Configuration
WHISPER_MODEL=large-v3

# Whisper Settings
WHISPER_LANGUAGE=hi
WHISPER_TASK=translate

# Devices
DEVICE=cpu
DEVICE_WHISPERX=cpu
DEVICE_DIARIZATION=cpu
DEVICE_VAD=cpu
DEVICE_NER=cpu
"""
    
    def prepare_media(
        self, 
        job_info: Dict, 
        input_media: Path,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> Path:
        """Prepare media file for job (clip or move).
        
        Args:
            job_info: Job information dictionary
            input_media: Source media file
            start_time: Optional start time for clipping (HH:MM:SS)
            end_time: Optional end time for clipping (HH:MM:SS)
        
        Returns:
            Path to prepared media file in job directory
        """
        job_dir = Path(job_info["job_dir"])
        
        # Generate output filename
        if start_time and end_time:
            # For clips: append "clip" and job number
            # Example: movie.mp4 -> movie_clip_0001.mp4
            stem = input_media.stem
            ext = input_media.suffix
            job_no = job_info["job_no"]
            media_filename = f"{stem}_clip_{job_no:04d}{ext}"
        else:
            # For full media: use original filename
            media_filename = input_media.name
        
        output_media = job_dir / media_filename
        
        if start_time and end_time:
            # Create clip
            if self.logger:
                self.logger.info("Creating media clip...")
                self.logger.info(f"Source: {input_media}")
                self.logger.info(f"Clip: {start_time} → {end_time}")
                self.logger.info(f"Output filename: {media_filename}")
            
            cmd = [
                "ffmpeg", "-i", str(input_media),
                "-ss", start_time,
                "-to", end_time,
                "-c", "copy",
                "-y",
                str(output_media)
            ]
            
            try:
                result = subprocess.run(
                    cmd,
                    check=True,
                    capture_output=True,
                    text=True
                )
                if self.logger:
                    self.logger.info(f"Clip created: {output_media}")
                job_info["is_clip"] = True
                job_info["clip_start"] = start_time
                job_info["clip_end"] = end_time
            except subprocess.CalledProcessError as e:
                if self.logger:
                    self.logger.error(f"FFmpeg failed: {e}")
                    self.logger.error(f"STDERR: {e.stderr}")
                sys.exit(1)
        else:
            # Copy full media
            if self.logger:
                self.logger.info("Copying media file...")
                self.logger.info(f"Source: {input_media}")
            shutil.copy2(input_media, output_media)
            if self.logger:
                self.logger.info(f"Media copied: {output_media}")
            job_info["is_clip"] = False
        
        return output_media
    
    def finalize_job(self, job_info: Dict, media_path: Path):
        """Finalize job by creating environment file from template.
        
        Creates final .env configuration file based on:
        - Template: config/.env.pipeline
        - Hardware detection and optimization
        - Job parameters: workflow_mode, native_mode, device
        - Calculated paths: output_root, log_root
        
        Args:
            job_info: Job information dictionary
            media_path: Path to prepared media file in job directory
        """
        job_dir = Path(job_info["job_dir"])
        job_id = job_info["job_id"]
        
        # Job environment file path
        job_env_file = job_dir / f".{job_id}.env"
        
        # Detect hardware capabilities
        if self.logger:
            self.logger.info("Detecting hardware capabilities...")
        
        hw_info = detect_hardware_capabilities()
        
        if self.logger:
            self.logger.info(f"CPU: {hw_info['cpu_cores']} cores, {hw_info['cpu_threads']} threads")
            self.logger.info(f"Memory: {hw_info['memory_gb']} GB")
            if hw_info['gpu_available']:
                self.logger.info(f"GPU: {hw_info['gpu_name']} ({hw_info['gpu_type'].upper()})")
                self.logger.info(f"GPU Memory: {hw_info['gpu_memory_gb']} GB")
            else:
                self.logger.warning("No GPU detected - CPU-only execution")
        
        # Get recommended settings
        settings = hw_info['recommended_settings']
        
        # Extract GPU type for backend selection
        gpu_type = hw_info.get('gpu_type', 'cpu')
        
        # Load config template from config/.env.pipeline
        config_template = Path("config/.env.pipeline")
        
        if not config_template.exists():
            if self.logger:
                self.logger.error(f"Config template not found: {config_template}")
                self.logger.error("Please ensure config/.env.pipeline exists")
            raise FileNotFoundError(f"Config template not found: {config_template}")
        
        if self.logger:
            self.logger.info(f"Using config template: {config_template}")
            self.logger.info("Applying hardware-optimized settings...")
        
        # Read template
        with open(config_template) as f:
            config_content = f.read()
        
        # Parse title and year from media filename
        parsed_filename = parse_filename(str(media_path))
        movie_title = parsed_filename.title
        movie_year = parsed_filename.year
        
        if self.logger:
            self.logger.info(f"Parsed from filename: {movie_title} ({movie_year if movie_year else 'year unknown'})")
        
        # Calculate paths based on job structure
        year = job_id[0:4]
        month = job_id[4:6]
        day = job_id[6:8]
        user_id = job_info.get("user_id", 1)
        
        output_root = f"out/{year}/{month}/{day}/{user_id}/{job_id}"
        log_root = f"out/{year}/{month}/{day}/{user_id}/{job_id}/logs"
        
        # Get workflow mode and native mode from job_info
        workflow_mode = job_info.get("workflow_mode", "subtitle-gen")
        native_mode = job_info.get("native_mode", False)
        source_language = job_info.get("source_language")
        target_language = job_info.get("target_language")
        
        # Determine device based on performance_profile from hardware_cache
        device = 'cpu'  # Default to CPU (lowercase)
        performance_profile = settings.get('performance_profile', '')
        
        if performance_profile:
            # Map performance profile to device type
            if 'cuda' in performance_profile.lower() or 'gpu' in performance_profile.lower():
                device = 'cuda'
            elif 'mps' in performance_profile.lower():
                device = 'mps'
            elif 'cpu' in performance_profile.lower():
                device = 'cpu'
        
        # Override with detected device if native mode enabled
        if native_mode:
            detected = detect_device_capability()
            device = detected.lower()  # Ensure lowercase for consistency
            if self.logger:
                self.logger.info(f"Native mode enabled - detected device: {device}")
                if device == 'cpu':
                    self.logger.warning("No GPU acceleration available, falling back to CPU")
        else:
            if self.logger:
                self.logger.info(f"Device set from performance profile: {device}")
        
        # Configure workflow-specific settings
        workflow_config = {}
        if workflow_mode == 'transcribe':
            if self.logger:
                self.logger.info("Workflow: TRANSCRIBE (simplified pipeline)")
            workflow_config = {
                'WORKFLOW_MODE': 'transcribe',
                'STEP_DIARIZATION': 'false',
                'STEP_SUBTITLE_GEN': 'false',
                'STEP_MUX': 'false',
                'SECOND_PASS_ENABLED': 'false',
                'LYRIC_DETECT_ENABLED': 'false',
                'POST_NER_ENTITY_CORRECTION': 'false',
                'POST_NER_TMDB_MATCHING': 'false'
            }
        elif workflow_mode == 'transcribe-only':
            if self.logger:
                self.logger.info("Workflow: TRANSCRIBE-ONLY (6 stages, includes VAD)")
            workflow_config = {
                'WORKFLOW_MODE': 'transcribe-only',
                'WHISPER_TASK': 'transcribe',
                'SECOND_PASS_ENABLED': 'false',
                'STEP_SONG_BIAS': 'false',
                'STEP_LYRICS': 'false',
                'STEP_BIAS_CORRECTION': 'false',
                'STEP_DIARIZATION': 'false',
                'STEP_GLOSSARY': 'false',
                'STEP_TRANSLATION': 'false',
                'POST_NER_ENTITY_CORRECTION': 'false',
                'STEP_SUBTITLE_GEN': 'false',
                'STEP_MUX': 'false'
            }
        elif workflow_mode == 'translate-only':
            if self.logger:
                self.logger.info("Workflow: TRANSLATE-ONLY (9 stages, reuses transcription)")
            workflow_config = {
                'WORKFLOW_MODE': 'translate-only',
                'SECOND_PASS_ENABLED': 'true',
                'STEP_DEMUX': 'false',
                'STEP_VAD_SILERO': 'false',
                'STEP_VAD_PYANNOTE': 'false',
                'STEP_ASR': 'false'
            }
        else:
            if self.logger:
                self.logger.info("Workflow: SUBTITLE-GEN (full pipeline)")
            workflow_config = {
                'WORKFLOW_MODE': 'subtitle-gen'
            }
        
        # Add language settings to workflow config
        if source_language:
            workflow_config['SOURCE_LANGUAGE'] = source_language
            workflow_config['WHISPER_LANGUAGE'] = source_language
        if target_language:
            workflow_config['TARGET_LANGUAGE'] = target_language
        
        # Configure IndicTrans2 if source is Indic and target is English/non-Indic
        if source_language and target_language:
            if is_indic_language(source_language) and target_language == 'en':
                workflow_config['INDICTRANS2_ENABLED'] = 'true'
                if self.logger:
                    lang_name = SUPPORTED_LANGUAGES.get(source_language, source_language)
                    self.logger.info(f"✓ IndicTrans2 enabled for {lang_name}→English translation")
                    self.logger.info("  → 90% faster than Whisper for Indic languages")
            else:
                # Disable for non-Indic or non-English target
                workflow_config['INDICTRANS2_ENABLED'] = 'false'
        
        # Apply stage control flags if provided
        stage_flags = job_info.get('stage_flags', {})
        if stage_flags:
            if self.logger:
                self.logger.info("Applying stage control flags...")
            
            if stage_flags.get('silero_vad') is not None:
                workflow_config['STEP_VAD_SILERO'] = 'true' if stage_flags['silero_vad'] else 'false'
                if self.logger:
                    self.logger.info(f"  Silero VAD: {'ENABLED' if stage_flags['silero_vad'] else 'DISABLED'}")
            
            if stage_flags.get('pyannote_vad') is not None:
                workflow_config['STEP_VAD_PYANNOTE'] = 'true' if stage_flags['pyannote_vad'] else 'false'
                if self.logger:
                    self.logger.info(f"  PyAnnote VAD: {'ENABLED' if stage_flags['pyannote_vad'] else 'DISABLED'}")
            
            if stage_flags.get('diarization') is not None:
                workflow_config['STEP_DIARIZATION'] = 'true' if stage_flags['diarization'] else 'false'
                if self.logger:
                    self.logger.info(f"  Diarization: {'ENABLED' if stage_flags['diarization'] else 'DISABLED'}")
        
        # Build configuration with hardware optimization comments
        config_lines = []
        
        # Add hardware detection header
        config_lines.extend([
            "# ============================================================================",
            "# CP-WhisperX-App Job Configuration",
            f"# Generated: {datetime.now().isoformat()}",
            f"# Job ID: {job_id}",
            "# ============================================================================",
            "",
            "# ============================================================================",
            "# HARDWARE DETECTION & OPTIMIZATION",
            "# ============================================================================",
            f"# CPU: {hw_info['cpu_cores']} cores ({hw_info['cpu_threads']} threads)",
            f"# Memory: {hw_info['memory_gb']} GB RAM",
        ])
        
        if hw_info['gpu_available']:
            config_lines.extend([
                f"# GPU: {hw_info['gpu_name']}",
                f"# GPU Memory: {hw_info['gpu_memory_gb']} GB",
                f"# GPU Type: {hw_info['gpu_type'].upper()}",
                "#",
                "# RECOMMENDATION: GPU acceleration available",
            ])
        else:
            config_lines.extend([
                "# GPU: Not available",
                "#",
                "# RECOMMENDATION: CPU-only execution",
                "# WARNING: Processing will be slower without GPU",
            ])
        
        config_lines.extend([
            "# ============================================================================",
            "",
        ])
        
        # Process template lines
        for line in config_content.split('\n'):
            # Skip removed fields
            if line.startswith('INPUT_FILE=') or \
               line.startswith('INPUT_URL=') or \
               line.startswith('CLIP_VIDEO=') or \
               line.startswith('START_CLIP=') or \
               line.startswith('END_CLIP='):
                continue
            
            # Handle job-specific overrides with comments
            if line.startswith('JOB_ID='):
                config_lines.append(f'JOB_ID={job_info["job_id"]}')
            elif line.startswith('TITLE='):
                # Quote title to handle spaces and special characters
                config_lines.append(f'TITLE="{movie_title}"')
            elif line.startswith('YEAR='):
                config_lines.append(f'YEAR={movie_year if movie_year else ""}')
            elif line.startswith('IN_ROOT='):
                config_lines.append(f'IN_ROOT={media_path.absolute()}')
            elif line.startswith('OUTPUT_ROOT='):
                config_lines.append(f'OUTPUT_ROOT={output_root}')
            elif line.startswith('LOG_ROOT='):
                config_lines.append(f'LOG_ROOT={log_root}')
            elif line.startswith('WORKFLOW_MODE='):
                config_lines.append(f'WORKFLOW_MODE={workflow_config.get("WORKFLOW_MODE", "subtitle-gen")}')
            
            # Whisper model optimization
            elif line.startswith('WHISPER_MODEL='):
                config_lines.extend([
                    f"# Hardware-optimized model selection",
                    f"# {settings['whisper_model_reason']}",
                    f"WHISPER_MODEL={settings['whisper_model']}"
                ])
            
            # Batch size optimization
            elif line.startswith('WHISPER_BATCH_SIZE=') or line.startswith('BATCH_SIZE='):
                config_lines.extend([
                    f"# Batch size optimized for available resources",
                    f"# {settings['batch_size_reason']}",
                    f"BATCH_SIZE={settings['batch_size']}"
                ])
            
            # Compute type optimization
            elif line.startswith('WHISPER_COMPUTE_TYPE=') or line.startswith('COMPUTE_TYPE='):
                config_lines.extend([
                    f"# Compute type optimized for device",
                    f"# {settings['compute_type_reason']}",
                    f"WHISPER_COMPUTE_TYPE={settings['compute_type']}"
                ])
            
            # Backend optimization (hardware-aware)
            elif line.startswith('WHISPER_BACKEND='):
                backend = settings.get('whisper_backend', 'whisperx')
                backend_reason = settings.get('whisper_backend_reason', 'Default backend')
                bias_note = settings.get('bias_prompting_note', '')
                config_lines.extend([
                    f"# Backend optimized for {gpu_type.upper() if gpu_type != 'cpu' else 'CPU'}",
                    f"# {backend_reason}",
                    f"# {bias_note}",
                    f"WHISPER_BACKEND={backend}"
                ])
            
            # Chunk length optimization
            elif line.startswith('CHUNK_LENGTH='):
                config_lines.extend([
                    f"# Chunk length tuned for memory constraints",
                    f"# {settings['chunk_length_reason']}",
                    f"CHUNK_LENGTH={settings['chunk_length_s']}"
                ])
            
            # Max speakers optimization
            elif line.startswith('DIARIZATION_MAX_SPEAKERS=') or line.startswith('MAX_SPEAKERS='):
                config_lines.extend([
                    f"# Max speakers based on resource availability",
                    f"# {settings['max_speakers_reason']}",
                    f"DIARIZATION_MAX_SPEAKERS={settings['max_speakers']}"
                ])
            
            # Device configuration (always set based on performance profile or native mode)
            elif line.startswith('DEVICE='):
                config_lines.extend([
                    f"# Global device set to: {device} (from {'native detection' if native_mode else 'performance profile'})",
                    f"DEVICE={device}"
                ])
            elif line.startswith('DEVICE_WHISPERX='):
                config_lines.extend([
                    f"# Device set to: {device} (from {'native detection' if native_mode else 'performance profile'})",
                    f"DEVICE_WHISPERX={device}"
                ])
            elif line.startswith('DEVICE_DIARIZATION='):
                config_lines.append(f'DEVICE_DIARIZATION={device}')
            elif line.startswith('DEVICE_VAD='):
                config_lines.append(f'DEVICE_VAD={device}')
            elif line.startswith('DEVICE_NER='):
                config_lines.append(f'DEVICE_NER={device}')
            
            # Glossary configuration (Advanced strategies)
            elif line.startswith('GLOSSARY_ENABLED='):
                config_lines.extend([
                    f"# Hinglish→English glossary with advanced strategies",
                    f"# Provides context-aware, character-aware, regional term substitution",
                    f"GLOSSARY_ENABLED=true"
                ])
            elif line.startswith('GLOSSARY_PATH='):
                config_lines.append(f'GLOSSARY_PATH=glossary/hinglish_master.tsv')
            elif line.startswith('GLOSSARY_STRATEGY='):
                # Default to adaptive for best quality
                config_lines.extend([
                    f"# Strategy: adaptive (intelligently combines all methods)",
                    f"# Options: first|context|character|regional|frequency|adaptive|ml",
                    f"GLOSSARY_STRATEGY=adaptive"
                ])
            elif line.startswith('FREQUENCY_DATA_PATH='):
                # Path for learned frequency data
                job_freq_path = f"{output_root}/glossary_learned/term_frequency.json"
                config_lines.extend([
                    f"# Frequency learning data (improves over time)",
                    f"FREQUENCY_DATA_PATH={job_freq_path}"
                ])
            elif line.startswith('FILM_PROMPT_PATH='):
                # Try to auto-detect movie-specific prompt based on input filename
                prompt_file = ""
                media_name = media_path.stem.lower().replace(' ', '_').replace('-', '_')
                # Check if a matching prompt exists
                prompts_dir = Path('glossary/prompts')
                if prompts_dir.exists():
                    # Look for prompts matching the media filename
                    # Extract significant words (remove common words and split)
                    media_words = set([w for w in media_name.replace('_', ' ').split() if len(w) > 2])
                    
                    best_match = None
                    best_score = 0
                    
                    for prompt in prompts_dir.glob('*.txt'):
                        prompt_key = prompt.stem.lower().replace(' ', '_').replace('-', '_')
                        prompt_words = set([w for w in prompt_key.replace('_', ' ').split() if len(w) > 2])
                        
                        # Calculate match score (number of common words)
                        common_words = media_words.intersection(prompt_words)
                        score = len(common_words)
                        
                        # If we have at least 2 common words or exact substring match, consider it
                        if score >= 2 or prompt_key in media_name or media_name in prompt_key:
                            if score > best_score:
                                best_score = score
                                best_match = prompt
                    
                    if best_match:
                        prompt_file = f'glossary/prompts/{best_match.name}'
                
                if prompt_file:
                    config_lines.extend([
                        f"# Auto-detected movie-specific prompt (character & regional data)",
                        f"FILM_PROMPT_PATH={prompt_file}"
                    ])
                else:
                    config_lines.extend([
                        f"# Movie-specific prompt not found - using generic glossary",
                        f"# Available prompts in: glossary/prompts/",
                        f"# Create: glossary/prompts/{media_path.stem.lower().replace(' ', '_')}.txt",
                        f"FILM_PROMPT_PATH="
                    ])
            
            else:
                # Keep original line
                config_lines.append(line)
        
        # Add workflow-specific overrides at the end
        if workflow_config:
            config_lines.extend([
                "",
                "# ============================================================================",
                "# WORKFLOW & STAGE OVERRIDES",
                "# ============================================================================",
            ])
            if workflow_mode == 'transcribe':
                config_lines.append("# Simplified pipeline - only transcription, no diarization or subtitles")
            if stage_flags:
                config_lines.append("# Stage control flags applied")
            
            for key, value in workflow_config.items():
                config_lines.append(f"{key}={value}")
        
        # Add resource monitoring recommendations
        config_lines.extend([
            "",
            "# ============================================================================",
            "# RESOURCE MONITORING RECOMMENDATIONS",
            "# ============================================================================",
        ])
        
        if hw_info['memory_gb'] < 16:
            config_lines.extend([
                "# WARNING: Low memory detected",
                "# - Monitor memory usage during processing",
                "# - Consider processing in smaller chunks",
                "# - Use smaller Whisper model if OOM occurs",
            ])
        
        if hw_info['gpu_available'] and hw_info['gpu_memory_gb'] < 8:
            config_lines.extend([
                "# WARNING: Limited GPU memory",
                "# - Reduce batch size if OOM errors occur",
                "# - Monitor GPU memory with: nvidia-smi (CUDA) or Activity Monitor (MPS)",
                "# - CPU fallback will activate automatically if GPU fails",
            ])
        
        if not hw_info['gpu_available']:
            config_lines.extend([
                "# CPU-ONLY EXECUTION:",
                "# - Processing will be significantly slower (10-25x)",
                "# - Consider using GPU-enabled system for large files",
                f"# - Estimated processing time: {settings['whisper_model']} model on CPU",
            ])
        
        config_lines.append("")
        
        # Write final configuration
        with open(job_env_file, 'w') as f:
            f.write('\n'.join(config_lines))
        
        # Update job info with hardware details
        job_info['hardware'] = {
            'cpu_cores': hw_info['cpu_cores'],
            'memory_gb': hw_info['memory_gb'],
            'gpu_type': hw_info['gpu_type'],
            'gpu_name': hw_info['gpu_name'],
            'optimized_settings': settings,
            'device': device  # Store the device value used
        }
        
        # Update job info with env_file and status
        job_info["env_file"] = str(job_env_file.absolute())
        job_info["status"] = "ready"
        
        # Save updated job.json
        job_json_file = job_dir / "job.json"
        with open(job_json_file, 'w') as f:
            json.dump(job_info, f, indent=2)
        
        if self.logger:
            self.logger.info(f"Configuration saved: {job_env_file}")
            self.logger.info(f"Hardware profile saved to: {job_json_file}")
            self.logger.info(f"Recommended model: {settings['whisper_model']}")
            self.logger.info(f"Batch size: {settings['batch_size']}")
            self.logger.info(f"Compute type: {settings['compute_type']}")
            
            # Log glossary configuration
            self.logger.info("")
            self.logger.info("Glossary Configuration:")
            glossary_tsv = Path("glossary/hinglish_master.tsv")
            if glossary_tsv.exists():
                self.logger.info(f"  ✓ Master glossary: {glossary_tsv}")
            else:
                self.logger.info(f"  ✗ Master glossary not found (will use defaults)")
            
            # Check for movie-specific prompt
            prompts_dir = Path('glossary/prompts')
            media_name = media_path.stem.lower()
            prompt_found = False
            if prompts_dir.exists():
                # Extract significant words (remove common words and split)
                media_words = set([w for w in media_name.replace('_', ' ').replace('-', ' ').split() if len(w) > 2])
                
                best_match = None
                best_score = 0
                
                for prompt in prompts_dir.glob('*.txt'):
                    prompt_key = prompt.stem.lower()
                    prompt_words = set([w for w in prompt_key.replace('_', ' ').replace('-', ' ').split() if len(w) > 2])
                    
                    # Calculate match score (number of common words)
                    common_words = media_words.intersection(prompt_words)
                    score = len(common_words)
                    
                    # If we have at least 2 common words or exact substring match, consider it
                    if score >= 2 or prompt_key in media_name or media_name in prompt_key:
                        if score > best_score:
                            best_score = score
                            best_match = prompt
                
                if best_match:
                    self.logger.info(f"  ✓ Movie prompt: {best_match.name}")
                    prompt_found = True
            
            if not prompt_found:
                self.logger.info(f"  • No movie-specific prompt found")
                self.logger.info(f"    Create: glossary/prompts/{media_path.stem.lower().replace(' ', '_')}.txt")



def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Prepare job for CP-WhisperX-App pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full subtitle generation (default): Hindi → English
  python prepare-job.py /path/to/movie.mp4
  
  # Spanish to English workflow
  python prepare-job.py /path/to/movie.mp4 --transcribe-only --source-language es
  python prepare-job.py /path/to/movie.mp4 --translate-only --source-language es --target-language en
  
  # Japanese to multiple targets
  python prepare-job.py /path/to/anime.mp4 --transcribe-only --source-language ja
  python prepare-job.py /path/to/anime.mp4 --translate-only --source-language ja --target-language en
  python prepare-job.py /path/to/anime.mp4 --translate-only --source-language ja --target-language es
  
  # Auto-detect source language
  python prepare-job.py /path/to/movie.mp4 --transcribe-only
  
  # Transcribe only (faster, 3 stages minimal)
  python prepare-job.py /path/to/movie.mp4 --transcribe
  
  # Enable native GPU acceleration (auto-detects MPS/CUDA)
  python prepare-job.py /path/to/movie.mp4 --native
  
  # Process 5-minute clip (for testing)
  python prepare-job.py /path/to/movie.mp4 --start-time 00:10:00 --end-time 00:15:00
        """
    )
    
    parser.add_argument(
        "input_media",
        help="Path to input media file"
    )
    
    parser.add_argument(
        "--start-time",
        help="Start time for clip (HH:MM:SS format)"
    )
    
    parser.add_argument(
        "--end-time",
        help="End time for clip (HH:MM:SS format)"
    )
    
    # Workflow mode arguments
    parser.add_argument(
        "--transcribe",
        action="store_true",
        help="Transcribe-only workflow - minimal (3 stages: demux, ASR, basic output)"
    )
    
    parser.add_argument(
        "--transcribe-only",
        action="store_true",
        help="Transcription-only workflow (6 stages: includes VAD, outputs segments.json)"
    )
    
    parser.add_argument(
        "--translate-only",
        action="store_true",
        help="Translation-only workflow (9 stages: reuses existing segments.json, skips audio processing)"
    )
    
    parser.add_argument(
        "--subtitle-gen",
        action="store_true",
        help="Full subtitle generation workflow - default (15 stages)"
    )
    
    # Language arguments
    parser.add_argument(
        "--source-language", "-s",
        help=f"Source language code (e.g., hi, es, ja, fr, de, auto). Supported: {len(SUPPORTED_LANGUAGES)} languages"
    )
    
    parser.add_argument(
        "--target-language", "-t",
        help="Target language code (e.g., en, es, fr, de). Required for --translate-only"
    )
    
    parser.add_argument(
        "--native",
        action="store_true",
        help="Enable native execution with MPS/CUDA acceleration (auto-detects capability)"
    )
    
    parser.add_argument(
        "--enable-silero-vad",
        action="store_true",
        help="Enable Silero VAD stage (default: enabled)"
    )
    
    parser.add_argument(
        "--disable-silero-vad",
        action="store_true",
        help="Disable Silero VAD stage"
    )
    
    parser.add_argument(
        "--enable-pyannote-vad",
        action="store_true",
        help="Enable PyAnnote VAD stage (default: enabled)"
    )
    
    parser.add_argument(
        "--disable-pyannote-vad",
        action="store_true",
        help="Disable PyAnnote VAD stage"
    )
    
    parser.add_argument(
        "--enable-diarization",
        action="store_true",
        help="Enable Diarization stage (default: enabled)"
    )
    
    parser.add_argument(
        "--disable-diarization",
        action="store_true",
        help="Disable Diarization stage"
    )
    
    args = parser.parse_args()
    
    # Validate input
    input_media = Path(args.input_media)
    if not input_media.exists():
        print(f"✗ Input media not found: {input_media}")
        sys.exit(1)
    
    # Validate clip times
    if bool(args.start_time) != bool(args.end_time):
        print("✗ Both --start-time and --end-time must be specified together")
        sys.exit(1)
    
    # Validate workflow flags (mutually exclusive)
    workflow_flags = [args.transcribe, args.transcribe_only, args.translate_only, args.subtitle_gen]
    if sum(workflow_flags) > 1:
        print("✗ Only one workflow mode can be specified: --transcribe, --transcribe-only, --translate-only, or --subtitle-gen")
        sys.exit(1)
    
    # Validate language codes
    source_language = None
    target_language = None
    
    if args.source_language:
        source_language = validate_language_code(args.source_language, "source language")
    
    if args.target_language:
        target_language = validate_language_code(args.target_language, "target language")
    
    # Validate translate-only requirements
    if args.translate_only:
        if not source_language:
            print("✗ --translate-only requires --source-language")
            print("  Example: --translate-only --source-language es --target-language en")
            sys.exit(1)
        if not target_language:
            print("✗ --translate-only requires --target-language")
            print("  Example: --translate-only --source-language es --target-language en")
            sys.exit(1)
    
    # Set default language for transcribe-only if not specified
    if args.transcribe_only and not source_language:
        source_language = 'auto'  # Default to auto-detect
    
    # Validate stage control flags
    if args.enable_silero_vad and args.disable_silero_vad:
        print("✗ Cannot specify both --enable-silero-vad and --disable-silero-vad")
        sys.exit(1)
    
    if args.enable_pyannote_vad and args.disable_pyannote_vad:
        print("✗ Cannot specify both --enable-pyannote-vad and --disable-pyannote-vad")
        sys.exit(1)
    
    if args.enable_diarization and args.disable_diarization:
        print("✗ Cannot specify both --enable-diarization and --disable-diarization")
        sys.exit(1)
    
    # Determine workflow mode
    if args.transcribe:
        workflow_mode = 'transcribe'
    elif args.transcribe_only:
        workflow_mode = 'transcribe-only'
    elif args.translate_only:
        workflow_mode = 'translate-only'
    else:
        workflow_mode = 'subtitle-gen'  # default
        # Set default languages for subtitle-gen if not specified
        if not source_language:
            source_language = 'hi'  # Default Hindi for backward compatibility
        if not target_language:
            target_language = 'en'  # Default English for backward compatibility
    
    # Setup logging
    logs_dir = Path("logs") / "prepare-job"
    logs_dir.mkdir(exist_ok=True, parents=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_filename = f"prepare-job_{timestamp}.log"  # Not a stage, so no stage number
    log_file = logs_dir / log_filename
    
    # Default log level
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    logger = PipelineLogger("prepare-job", log_file, log_level=log_level)
    
    logger.info("="*60)
    logger.info("CP-WHISPERX-APP JOB PREPARATION")
    logger.info("="*60)
    logger.info(f"Input media: {input_media}")
    logger.info(f"Workflow: {workflow_mode.upper()}")
    if source_language:
        lang_name = SUPPORTED_LANGUAGES.get(source_language, source_language)
        logger.info(f"Source language: {source_language} ({lang_name})")
    if target_language:
        lang_name = SUPPORTED_LANGUAGES.get(target_language, target_language)
        logger.info(f"Target language: {target_language} ({lang_name})")
    if args.native:
        detected_device = detect_device_capability()
        logger.info(f"Native mode: ENABLED (detected: {detected_device.upper()})")
    if args.start_time and args.end_time:
        logger.info(f"Clip mode: {args.start_time} → {args.end_time}")
    
    # Build stage control flags dictionary
    stage_flags = {}
    if args.enable_silero_vad:
        stage_flags['silero_vad'] = True
    elif args.disable_silero_vad:
        stage_flags['silero_vad'] = False
    
    if args.enable_pyannote_vad:
        stage_flags['pyannote_vad'] = True
    elif args.disable_pyannote_vad:
        stage_flags['pyannote_vad'] = False
    
    if args.enable_diarization:
        stage_flags['diarization'] = True
    elif args.disable_diarization:
        stage_flags['diarization'] = False
    
    # Create job
    manager = JobManager(logger=logger)
    
    job_info = manager.create_job(
        input_media,
        workflow_mode=workflow_mode,
        native_mode=args.native,
        start_time=args.start_time,
        end_time=args.end_time,
        stage_flags=stage_flags if stage_flags else None,
        source_language=source_language,
        target_language=target_language
    )
    
    # Prepare media
    media_path = manager.prepare_media(
        job_info,
        input_media,
        args.start_time,
        args.end_time
    )
    
    # Finalize job (creates .env file from template)
    manager.finalize_job(job_info, media_path)
    
    logger.info("")
    logger.info("="*60)
    logger.info("JOB PREPARATION COMPLETE")
    logger.info("="*60)
    logger.info(f"Job ID: {job_info['job_id']}")
    logger.info(f"Job Directory: {job_info['job_dir']}")
    logger.info(f"Environment File: {job_info['env_file']}")
    logger.info(f"Media File: {media_path}")
    logger.info(f"Workflow Mode: {workflow_mode.upper()}")
    if source_language:
        lang_name = SUPPORTED_LANGUAGES.get(source_language, source_language)
        logger.info(f"Source Language: {source_language} ({lang_name})")
    if target_language:
        lang_name = SUPPORTED_LANGUAGES.get(target_language, target_language)
        logger.info(f"Target Language: {target_language} ({lang_name})")
    # Always show device configuration
    device_value = job_info.get('hardware', {}).get('device', 'CPU')
    logger.info(f"Device Configuration: {device_value}")
    
    if job_info.get("is_clip"):
        logger.info(f"Clip Duration: {args.start_time} → {args.end_time}")
    
    logger.info("")
    logger.info("Next step:")
    logger.info(f"  python scripts/pipeline.py --job {job_info['job_id']}")
    
    # Also print to console for user
    print(f"\n✓ Job created: {job_info['job_id']}")
    print(f"  Directory: {job_info['job_dir']}")
    print(f"  Workflow: {workflow_mode.upper()}")
    if source_language:
        lang_name = SUPPORTED_LANGUAGES.get(source_language, source_language)
        print(f"  Source: {source_language} ({lang_name})")
    if target_language:
        lang_name = SUPPORTED_LANGUAGES.get(target_language, target_language)
        print(f"  Target: {target_language} ({lang_name})")
    # Always show device configuration
    device_value = job_info.get('hardware', {}).get('device', 'CPU')
    print(f"  Device: {device_value}")
    print(f"  Log: {log_file}")
    print(f"\nNext step:")
    print(f"  python scripts/pipeline.py --job {job_info['job_id']}")
    print()


if __name__ == "__main__":
    main()
