#!/usr/bin/env python3
"""
IndicTrans2 Job Preparation Script

Simplified job preparation for IndicTrans2 workflows:
- Transcribe: Indian language audio → text transcripts
- Translate: Indian language text → English subtitles

Reuses existing infrastructure:
- config/.env.pipeline configuration
- config/secrets.json for API keys
- shared/logger.py for logging
- shared/manifest.py for job tracking
- out/ directory structure
"""

# Standard library
import sys
import os
import json
import shutil
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict

# Add paths for imports
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import centralized stage ordering
from shared.stage_order import get_all_stage_dirs

from shared.logger import PipelineLogger, get_logger
from shared.environment_manager import EnvironmentManager
from scripts.filename_parser import parse_filename
from scripts.config_loader import Config

# Initialize logger
logger = get_logger(__name__)


def validate_device_backend_compatibility(device: str, backend: str) -> tuple[str, str]:
    """
    Ensure device and backend are compatible
    
    Validates that the selected backend is compatible with the target device
    and makes automatic corrections when incompatibilities are detected.
    
    Args:
        device: Target device (cpu, cuda, mps)
        backend: ASR backend (whisperx, mlx, auto)
        
    Returns:
        Tuple of (validated_device, validated_backend)
        
    Note:
        - MLX backend requires MPS device (Apple Silicon)
        - CPU device is incompatible with MLX backend
        - Auto-corrects incompatible combinations with warnings
    """
    device_lower = device.lower()
    backend_lower = backend.lower()
    
    # MLX backend requires MPS device
    if backend_lower == 'mlx' and device_lower != 'mps':
        logger.warning(f"MLX backend requires MPS device, but {device} specified")
        logger.info(f"Auto-correcting: Setting device to MPS")
        return 'mps', backend_lower
    
    # CPU device with MLX backend is inefficient
    if device_lower == 'cpu' and backend_lower == 'mlx':
        logger.warning(f"MLX backend not optimal for CPU")
        logger.info(f"Auto-correcting: Switching to WhisperX backend")
        return device_lower, 'whisperx'
    
    # MPS device without MLX should warn (suboptimal)
    if device_lower == 'mps' and backend_lower != 'mlx':
        logger.warning(f"WhisperX on MPS is slower than MLX backend")
        logger.info(f"Consider using MLX backend for 2-4x speedup")
    
    return device_lower, backend_lower


# Supported Indian languages for IndicTrans2
INDIAN_LANGUAGES = {
    "hi": "Hindi",
    "as": "Assamese",
    "bn": "Bengali",
    "gu": "Gujarati",
    "kn": "Kannada",
    "ml": "Malayalam",
    "mr": "Marathi",
    "or": "Odia",
    "pa": "Punjabi",
    "ta": "Tamil",
    "te": "Telugu",
    "ur": "Urdu",
    "ne": "Nepali",
    "sd": "Sindhi",
    "si": "Sinhala",
    "sa": "Sanskrit",
    "ks": "Kashmiri",
    "doi": "Dogri",
    "mni": "Manipuri",
    "kok": "Konkani",
    "mai": "Maithili",
    "sat": "Santali",
}


def validate_language(lang_code: str, is_source: bool = True, workflow: str = "translate") -> bool:
    """
    Validate language code based on workflow.
    
    Args:
        lang_code: Language code to validate
        is_source: Whether this is source language
        workflow: Workflow type (transcribe, translate, subtitle)
        
    Returns:
        True if language is valid for the workflow
        
    Note:
        - transcribe: Any language supported by WhisperX (100+ languages)
        - translate: Source must be Indian language (IndicTrans2 constraint)
        - subtitle: Source must be Indian language (IndicTrans2 constraint)
    """
    if workflow == "transcribe":
        # Transcribe supports any language via WhisperX
        return True
    
    if is_source:
        # For translate/subtitle: Source must be Indian language
        return lang_code in INDIAN_LANGUAGES
    else:
        # Target can be any language
        return True


def get_next_job_number(user_id: str, date_str: str) -> int:
    """
    Get next job number for the user on the given date, incrementing a counter file.
    
    Args:
        user_id: User identifier (from job config)
        date_str: Date string in YYYYMMDD format
    
    Returns:
        Next job number (starting from 1)
    """
    counter_file = PROJECT_ROOT / "out" / f".job_counter_{date_str}_{user_id}"
    
    # Read current counter or start at 0
    if counter_file.exists():
        with open(counter_file, 'r') as f:
            current = int(f.read().strip())
    else:
        current = 0
    
    # Increment and save
    next_number = current + 1
    with open(counter_file, 'w') as f:
        f.write(str(next_number))
    
    return next_number


def create_job_directory(input_media: Path, workflow: str, user_id: Optional[str] = None) -> tuple[Path, str]:
    """
    Create job directory structure: out/YYYY/MM/DD/USERID/counter/
    Job ID format: job-YYYYMMDD-USERID-nnnn
    
    Returns:
        Tuple of (job_dir, job_id)
    """
    # Get username (will be used as USER_ID if not provided)
    import getpass
    username = getpass.getuser()
    
    # Use provided user_id or default to username
    if user_id is None:
        user_id = username
    
    # Get current date
    now = datetime.now()
    year = now.strftime("%Y")
    month = now.strftime("%m")
    day = now.strftime("%d")
    date_str = now.strftime("%Y%m%d")
    
    # Get next job number for this user on this date
    job_number = get_next_job_number(user_id, date_str)
    
    # Create job ID: job-YYYYMMDD-USERID-nnnn (4-digit padded)
    job_id = f"job-{date_str}-{user_id}-{job_number:04d}"
    
    # Create directory: out/YYYY/MM/DD/USERID/counter/
    job_dir = PROJECT_ROOT / "out" / year / month / day / user_id / str(job_number)
    job_dir.mkdir(parents=True, exist_ok=True)
    
    # Create main subdirectories
    (job_dir / "logs").mkdir(exist_ok=True)
    (job_dir / "media").mkdir(exist_ok=True)
    (job_dir / "transcripts").mkdir(exist_ok=True)
    (job_dir / "subtitles").mkdir(exist_ok=True)
    
    # Create stage subdirectories using centralized stage order
    for stage_dir in get_all_stage_dirs():
        (job_dir / stage_dir).mkdir(exist_ok=True)
    
    return job_dir, job_id


def prepare_media(input_media: Path, job_dir: Path, 
                  start_time: Optional[str] = None,
                  end_time: Optional[str] = None) -> Path:
    """
    Prepare media file - copy to job directory
    Clipping is now handled by the demux stage based on job config
    
    Returns:
        Path to prepared media file
    """
    media_dir = job_dir / "media"
    output_media = media_dir / input_media.name
    
    # Always copy the full media file
    # Clipping will be done during demux stage based on job.json config
    shutil.copy2(input_media, output_media)
    
    if start_time or end_time:
        logger.info(f"   Note: Clipping configured ({start_time} to {end_time})")
        logger.info(f"   Full media copied - clipping will happen during pipeline execution")
    
    return output_media


def create_job_config(job_dir: Path, job_id: str, workflow: str,
                      input_media: Path, source_lang: str,
                      target_langs: Optional[list] = None,
                      start_time: Optional[str] = None,
                      end_time: Optional[str] = None,
                      debug: bool = False,
                      user_id: Optional[str] = None,
                      log_level: Optional[str] = None,
                      two_step: bool = False) -> None:
    """Create job.json configuration file with environment mappings"""
    
    parsed = parse_filename(input_media.name)
    
    # Extract user_id from job_id if not provided
    if user_id is None:
        # job_id format: job-YYYYMMDD-USERID-nnnn
        user_id = job_id.split('-')[2]
    
    # Store target languages as a list (even if single language)
    if target_langs is None:
        target_langs = []
    
    # Initialize environment manager
    env_manager = EnvironmentManager(PROJECT_ROOT)
    
    # Get required environments for this workflow
    required_envs = env_manager.get_environments_for_workflow(workflow)
    
    # Build environment paths dict
    environments = {}
    for env_name in required_envs:
        env_path = env_manager.get_environment_path(env_name)
        environments[env_name] = str(env_path)
    
    # Build stage-to-environment mapping for this workflow
    stage_environments = {}
    hardware_cache = env_manager.hardware_cache
    stage_mapping = hardware_cache.get("stage_to_environment_mapping", {})
    
    # Include all stages that might be used
    for stage, env in stage_mapping.items():
        if env in required_envs:
            stage_environments[stage] = env
    
    # Load configuration to get source_separation settings
    from shared.config import Config
    config = Config(PROJECT_ROOT)
    sep_enabled = config.get('SOURCE_SEPARATION_ENABLED', 'true').lower() == 'true'
    sep_quality = config.get('SOURCE_SEPARATION_QUALITY', 'balanced')
    
    job_config = {
        "job_id": job_id,
        "user_id": user_id,
        "workflow": workflow,
        "source_language": source_lang,
        "target_languages": target_langs,
        "two_step_transcription": two_step,
        "input_media": str(input_media),
        "title": parsed.title if parsed.title else input_media.stem,
        "year": str(parsed.year) if parsed.year else "",
        "created_at": datetime.now().isoformat(),
        "status": "prepared",
        "debug": debug,
        "media_processing": {
            "mode": "clip" if (start_time or end_time) else "full",
            "start_time": start_time or "",
            "end_time": end_time or ""
        },
        "source_separation": {
            "enabled": sep_enabled,
            "quality": sep_quality
        },
        "tmdb_enrichment": {
            "enabled": workflow == "subtitle",  # Only enable for subtitle workflow (movie/TV content)
            "title": parsed.title if parsed.title else input_media.stem,
            "year": parsed.year if parsed.year else None
        },
        "ner_correction": {
            "enabled": True,
            "apply_to_transcripts": True,
            "apply_to_translations": True
        },
        "log_level": log_level or ("DEBUG" if debug else "INFO"),
        "environments": environments,
        "stage_environments": stage_environments
    }
    
    config_file = job_dir / "job.json"
    with open(config_file, 'w') as f:
        json.dump(job_config, f, indent=2)


def create_env_file(job_dir: Path, job_id: str, workflow: str,
                   input_media: Path, source_lang: str,
                   target_lang: Optional[str] = None,
                   start_time: Optional[str] = None,
                   end_time: Optional[str] = None,
                   debug: bool = False,
                   log_level_arg: Optional[str] = None,
                   user_id: Optional[str] = None) -> None:
    """
    Create job-specific .env file from config/.env.pipeline template
    Injects hardware settings from hardware_cache.json
    Configures media processing mode (full or clip)
    """
    # Read template
    template_file = PROJECT_ROOT / "config" / ".env.pipeline"
    
    if not template_file.exists():
        raise FileNotFoundError(f"Template not found: {template_file}")
    
    with open(template_file, 'r') as f:
        template_content = f.read()
    
    # Load hardware configuration
    hardware_cache = PROJECT_ROOT / "config" / "hardware_cache.json"
    hardware_config = {}
    
    if hardware_cache.exists():
        with open(hardware_cache) as f:
            hardware_config = json.load(f)
    else:
        logger.warning(f" Hardware cache not found: {hardware_cache}")
        logger.info(f"   Run bootstrap script to detect hardware capabilities")
    
    # Extract user_id from job_id if not provided
    if user_id is None:
        # job_id format: job-YYYYMMDD-USERID-nnnn
        user_id = job_id.split('-')[2]
    
    # Parse filename
    parsed = parse_filename(input_media.name)
    title = parsed.title if parsed.title else input_media.stem
    year = str(parsed.year) if parsed.year else ''
    
    # Prepare media path
    media_path = job_dir / "media" / input_media.name
    
    # Load configuration from .env.pipeline
    config = Config(PROJECT_ROOT)
    
    # Extract hardware settings from hardware_cache
    hardware_info = hardware_config.get("hardware", {})
    
    # Determine GPU type from hardware detection
    if hardware_info.get("has_mlx"):
        gpu_type = "mps"  # Apple Silicon with MLX
        whisper_backend = "mlx"
    elif hardware_info.get("has_cuda"):
        gpu_type = "cuda"
        whisper_backend = "whisperx"
    else:
        gpu_type = "cpu"
        whisper_backend = "whisperx"
    
    # Validate device/backend compatibility (auto-corrects if needed)
    gpu_type, whisper_backend = validate_device_backend_compatibility(gpu_type, whisper_backend)
    
    # Get settings from config
    whisper_model = config.whisperx_model
    batch_size = config.batch_size
    
    # Set compute type based on device - CRITICAL for avoiding errors
    if gpu_type == "cpu":
        # CPU MUST use int8 - float16 is not supported efficiently
        compute_type = "int8"
    elif gpu_type == "cuda":
        # CUDA supports float16 for faster inference
        compute_type = "float16"
    elif gpu_type == "mps":
        # MPS with MLX backend can use float16, otherwise float32 for stability
        if whisper_backend == "mlx":
            compute_type = "float16"
        else:
            compute_type = "float32"
    else:
        # Fallback to safe default
        compute_type = "int8"
    
    # Display hardware configuration
    logger.info(f"✓ Hardware detection:")
    logger.info(f"  Device: {gpu_type}")
    logger.info(f"  Backend: {whisper_backend}")
    logger.info(f"  Model: {whisper_model}")
    logger.info(f"  Compute: {compute_type}")
    logger.info(f"  Batch: {batch_size}")
    
    # Create replacements dictionary
    replacements = {
        "JOB_ID=": f"JOB_ID={job_id}",
        "USER_ID=1": f"USER_ID={user_id}",
        "WORKFLOW_MODE=subtitle-gen": f"WORKFLOW_MODE={workflow}",
        "TITLE=": f"TITLE={title}",
        "YEAR=": f"YEAR={year}",
        "IN_ROOT=": f"IN_ROOT={media_path}",
        "OUTPUT_ROOT=": f"OUTPUT_ROOT={job_dir}",
        "LOG_ROOT=": f"LOG_ROOT={job_dir / 'logs'}",
        # Hardware-detected settings
        "WHISPER_MODEL=large-v3": f"WHISPER_MODEL={whisper_model}",
        "WHISPER_COMPUTE_TYPE=float16": f"WHISPER_COMPUTE_TYPE={compute_type}",
        "BATCH_SIZE=2": f"BATCH_SIZE={batch_size}",
        "WHISPERX_DEVICE=mps": f"WHISPERX_DEVICE={gpu_type}",
        "WHISPER_BACKEND=mlx": f"WHISPER_BACKEND={whisper_backend}",
        "SILERO_DEVICE=mps": f"SILERO_DEVICE={gpu_type}",
        "PYANNOTE_DEVICE=mps": f"PYANNOTE_DEVICE={gpu_type}",
        "DIARIZATION_DEVICE=mps": f"DIARIZATION_DEVICE={gpu_type}",
        "INDICTRANS2_DEVICE=auto": f"INDICTRANS2_DEVICE={gpu_type}",
    }
    
    # Add language-specific settings
    if workflow == "transcribe":
        replacements["WHISPER_LANGUAGE=hi"] = f"WHISPER_LANGUAGE={source_lang}"
    elif workflow == "translate" or workflow == "subtitle":
        replacements["WHISPER_LANGUAGE=hi"] = f"WHISPER_LANGUAGE={source_lang}"
        # Add target language setting
    
    # Apply replacements
    env_content = template_content
    for old, new in replacements.items():
        env_content = env_content.replace(old, new)
    
    # Add media processing configuration
    media_mode = "clip" if (start_time or end_time) else "full"
    env_content += f"\n\n# Media Processing Configuration\n"
    env_content += f"MEDIA_PROCESSING_MODE={media_mode}\n"
    env_content += f"MEDIA_START_TIME={start_time or ''}\n"
    env_content += f"MEDIA_END_TIME={end_time or ''}\n"
    
    # Note: Source separation configuration is in config/.env.pipeline
    # It will be loaded from there by the pipeline
    
    # Add debug configuration
    # Use --log-level if provided, otherwise --debug flag, otherwise INFO
    if log_level_arg:
        log_level = log_level_arg
    elif debug:
        log_level = "DEBUG"
    else:
        log_level = "INFO"
    
    env_content += f"\n# Debug Configuration\n"
    env_content += f"LOG_LEVEL={log_level}\n"
    env_content += f"DEBUG_MODE={'true' if debug else 'false'}\n"
    
    # Write to job directory
    env_file = job_dir / f".{job_id}.env"
    with open(env_file, 'w') as f:
        f.write(env_content)


def create_manifest(job_dir: Path, job_id: str, workflow: str) -> None:
    """Create initial manifest.json"""
    
    # Load job config to get target languages and source_separation setting
    job_config_file = job_dir / "job.json"
    target_languages = []
    source_separation_enabled = True  # Default
    
    if job_config_file.exists():
        with open(job_config_file) as f:
            job_data = json.load(f)
            target_languages = job_data.get("target_languages", [])
            sep_config = job_data.get("source_separation", {})
            source_separation_enabled = sep_config.get("enabled", True)
    
    if workflow == "transcribe":
        stages = [
            {"name": "demux", "status": "pending"},
        ]
        # Add TMDB enrichment stage
        stages.append({"name": "tmdb", "status": "pending"})
        # Add source separation if enabled
        if source_separation_enabled:
            stages.append({"name": "source_separation", "status": "pending"})
        stages.extend([
            {"name": "asr", "status": "pending"},
            {"name": "alignment", "status": "pending"},
            {"name": "export_transcript", "status": "pending"},
        ])
    elif workflow == "translate":
        stages = [
            {"name": "load_transcript", "status": "pending"},
            {"name": "indictrans2_translation", "status": "pending"},
            {"name": "subtitle_generation", "status": "pending"},
        ]
    elif workflow == "subtitle":
        stages = [
            {"name": "demux", "status": "pending"},
        ]
        # Add TMDB enrichment stage
        stages.append({"name": "tmdb", "status": "pending"})
        # Add source separation if enabled
        if source_separation_enabled:
            stages.append({"name": "source_separation", "status": "pending"})
        stages.extend([
            {"name": "asr", "status": "pending"},
            {"name": "alignment", "status": "pending"},
            {"name": "export_transcript", "status": "pending"},
            {"name": "load_transcript", "status": "pending"},
        ])
        
        # Add translation and subtitle generation for each target language
        for target_lang in target_languages:
            stages.append({"name": f"indictrans2_translation_{target_lang}", "status": "pending"})
            stages.append({"name": f"subtitle_generation_{target_lang}", "status": "pending"})
        
        # Add source subtitle generation
        stages.append({"name": "subtitle_generation_source", "status": "pending"})
        
        # Add mux stage
        stages.append({"name": "mux", "status": "pending"})
    else:
        stages = []
    
    manifest = {
        "job_id": job_id,
        "workflow": workflow,
        "stages": stages,
        "status": "prepared",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    
    manifest_file = job_dir / "manifest.json"
    with open(manifest_file, 'w') as f:
        json.dump(manifest, f, indent=2)


def main() -> None:
    """Main."""
    parser = argparse.ArgumentParser(
        description="IndicTrans2 Job Preparation Script"
    )
    
    parser.add_argument(
        "input_media",
        type=Path,
        help="Input media file"
    )
    
    parser.add_argument(
        "--workflow",
        required=True,
        choices=["transcribe", "translate", "subtitle"],
        help="Workflow mode"
    )
    
    parser.add_argument(
        "-s", "--source-language",
        help="Source language code (e.g., hi, ta, te). Optional for 'transcribe' workflow (will auto-detect)."
    )
    
    parser.add_argument(
        "-t", "--target-language",
        help="Target language code(s) (e.g., en or en,gu,ta - max 5 languages)"
    )
    
    parser.add_argument(
        "--start-time",
        help="Start time for clip (HH:MM:SS)"
    )
    
    parser.add_argument(
        "--end-time",
        help="End time for clip (HH:MM:SS)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode (verbose logging)"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"],
        help="Set log level (overrides --debug)"
    )
    
    parser.add_argument(
        "--user-id",
        help="User identifier (defaults to system username)"
    )
    
    parser.add_argument(
        "--two-step",
        action="store_true",
        help="Enable two-step transcription (transcribe in source language, then translate)"
    )
    
    args = parser.parse_args()
    
    # Validate input
    if not args.input_media.exists():
        logger.error(f"❌ Error: Input media not found: {args.input_media}")
        sys.exit(1)
    
    # For transcribe workflow, source language is optional (will auto-detect)
    if args.workflow == "transcribe" and not args.source_language:
        logger.info("ℹ️  Source language not specified - will auto-detect during transcription")
        args.source_language = "auto"  # Set to 'auto' for auto-detection
    
    # For other workflows, source language is required
    if args.workflow != "transcribe" and not args.source_language:
        logger.error(f"❌ Error: --source-language is required for '{args.workflow}' workflow")
        logger.info(f"   Supported languages: {', '.join(INDIAN_LANGUAGES.keys())}")
        sys.exit(1)
    
    # Validate languages (skip validation for 'auto')
    if args.source_language != "auto" and not validate_language(args.source_language, is_source=True, workflow=args.workflow):
        logger.error(f"❌ Error: Unsupported source language: {args.source_language}")
        if args.workflow in ["translate", "subtitle"]:
            logger.info(f"   For {args.workflow} workflow, source must be an Indian language")
            logger.info(f"   Supported languages: {', '.join(INDIAN_LANGUAGES.keys())}")
        sys.exit(1)
    
    if args.workflow == "translate" and not args.target_language:
        logger.error("❌ Error: Target language required for translate workflow")
        sys.exit(1)
    
    if args.workflow == "subtitle" and not args.target_language:
        logger.error("❌ Error: Target language required for subtitle workflow")
        sys.exit(1)
    
    # Parse and validate target languages (can be comma-separated)
    target_languages = []
    if args.target_language:
        target_languages = [lang.strip() for lang in args.target_language.split(',')]
        
        # Validate maximum 5 target languages
        if len(target_languages) > 5:
            logger.error(f"❌ Error: Maximum 5 target languages allowed, got {len(target_languages)}")
            sys.exit(1)
        
        # Validate each target language
        for lang in target_languages:
            if not validate_language(lang, is_source=False):
                logger.error(f"❌ Error: Unsupported target language: {lang}")
                logger.info(f"   Supported languages: en, {', '.join(INDIAN_LANGUAGES.keys())}")
                sys.exit(1)
        
        logger.info(f"✓ Target language(s): {', '.join(target_languages)}")
    
    # Validate required environments are installed
    logger.info(f"🔍 Validating environments...")
    try:
        env_manager = EnvironmentManager(PROJECT_ROOT)
        valid, missing = env_manager.validate_environments_for_workflow(args.workflow)
        
        if not valid:
            logger.error(f"❌ Error: Missing required environments: {', '.join(missing)}")
            logger.info(f"   Run: ./bootstrap.sh to install all environments")
            logger.info(f"   Or:  ./bootstrap.sh --env <name> for specific environment")
            sys.exit(1)
        
        logger.info(f"✓ All required environments installed")
    except FileNotFoundError as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        logger.info(f"   Run: ./bootstrap.sh to setup environments")
        sys.exit(1)
    
    # Create job directory
    logger.info(f"📁 Creating job directory...")
    job_dir, job_id = create_job_directory(args.input_media, args.workflow, user_id=args.user_id)
    logger.info(f"   Job ID: {job_id}")
    logger.info(f"   Job directory: {job_dir}")
    
    # Extract user_id from job_id for use in config
    user_id = job_id.split('-')[2]  # job-YYYYMMDD-USERID-nnnn
    
    # Prepare media
    logger.info(f"🎬 Preparing media...")
    prepared_media = prepare_media(
        args.input_media,
        job_dir,
        args.start_time,
        args.end_time
    )
    logger.info(f"   Media: {prepared_media.name}")
    
    # Create job configuration
    logger.info(f"⚙️  Creating job configuration...")
    # Determine log level
    log_level_value = args.log_level if args.log_level else ("DEBUG" if args.debug else "INFO")
    
    create_job_config(
        job_dir,
        job_id,
        args.workflow,
        prepared_media,
        args.source_language,
        target_languages,  # Pass the parsed list
        args.start_time,
        args.end_time,
        args.debug,
        user_id=user_id,  # Pass as keyword argument
        log_level=log_level_value,  # Pass log level
        two_step=args.two_step  # Pass two-step flag
    )
    
    # Create environment file
    logger.info(f"📝 Creating environment file...")
    target_lang_str = ','.join(target_languages) if target_languages else None
    
    # Determine log level
    log_level_for_env = args.log_level if args.log_level else ("DEBUG" if args.debug else None)
    
    create_env_file(
        job_dir,
        job_id,
        args.workflow,
        prepared_media,
        args.source_language,
        target_lang_str,
        args.start_time,
        args.end_time,
        args.debug,
        log_level_arg=log_level_for_env,
        user_id=user_id  # Pass as keyword argument
    )
    
    # Create manifest
    logger.info(f"📋 Creating manifest...")
    create_manifest(job_dir, job_id, args.workflow)
    
    # Success
    logger.info("")
    logger.info(f"✅ Job preparation complete!")
    logger.info("")
    logger.info(f"Job created: {job_id}")
    logger.info(f"Job directory: {job_dir}")
    logger.info("")
    logger.info(f"Next steps:")
    logger.info(f"  1. Run pipeline: ./run-pipeline.sh -j {job_id}")
    logger.info(f"  2. Monitor logs: tail -f {job_dir}/logs/*.log")
    logger.info("")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
