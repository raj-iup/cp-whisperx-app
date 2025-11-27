#!/usr/bin/env python3
"""
Source Separation stage: Extract vocals from audio using Demucs
Removes background music, leaving clean speech for transcription

Follows best practices:
- NO hardcoded values
- NO os.environ direct reads
- Configuration via job.json
- Proper logging with module name
"""
import sys
import os
import subprocess
import shutil
import json
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.stage_utils import StageIO, get_stage_logger


def check_demucs_installed():
    """Check if Demucs is installed"""
    try:
        result = subprocess.run(
            ["demucs", "--help"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def install_demucs(logger):
    """Install Demucs using pip"""
    logger.info("Demucs not found. Installing...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "demucs"],
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode == 0:
            logger.info("✓ Demucs installed successfully")
            return True
        else:
            logger.error(f"Failed to install Demucs: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"Failed to install Demucs: {e}")
        return False


def separate_vocals(input_audio, output_dir, quality="balanced", logger=None):
    """
    Separate vocals from background music using Demucs
    
    Args:
        input_audio: Path to input audio file
        output_dir: Directory for output files
        quality: Quality preset (fast/balanced/quality)
        logger: Logger instance
    
    Returns:
        Path to separated vocals file, or None if failed
    """
    if logger:
        logger.info("Starting source separation...")
        logger.info(f"  Input: {input_audio}")
        logger.info(f"  Quality: {quality}")
    
    # Create temp directory for Demucs output
    temp_output = output_dir / "demucs_temp"
    temp_output.mkdir(parents=True, exist_ok=True)
    
    # Build Demucs command
    cmd = ["demucs"]
    
    # Auto-detect best device (MPS on Apple Silicon, CUDA on NVIDIA, CPU fallback)
    # Let demucs choose the best device automatically
    
    # Model selection based on quality
    if quality == "quality":
        # Best quality: htdemucs (Hybrid Transformer model)
        cmd.extend(["-n", "htdemucs"])
    elif quality == "fast":
        # Faster: mdx_extra_q model with MP3 output
        cmd.extend(["-n", "mdx_extra_q", "--mp3"])
    else:  # balanced
        # Balanced: htdemucs (default, best quality)
        cmd.extend(["-n", "htdemucs"])
    
    # Two-stems mode (vocals + accompaniment only)
    cmd.extend([
        "--two-stems=vocals",
        "-o", str(temp_output),
        str(input_audio)
    ])
    
    if logger:
        logger.debug(f"Running: {' '.join(cmd)}")
        logger.info("Processing audio with Demucs...")
        logger.info("Note: Using hardware acceleration (MPS/CUDA) if available")
    
    # Run Demucs
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=900  # 15 minutes max
        )
        
        if result.returncode != 0:
            if logger:
                logger.error(f"Demucs failed with code {result.returncode}")
                logger.error(f"stderr: {result.stderr}")
            return None
        
        # Find the separated vocals file
        # Demucs output structure varies by model
        audio_name = input_audio.stem
        
        # Try both model output directories
        model_dirs = ["htdemucs", "mdx_extra_q"]
        vocals_file = None
        
        for model_dir in model_dirs:
            potential_vocals = temp_output / model_dir / audio_name / "vocals.wav"
            if potential_vocals.exists():
                vocals_file = potential_vocals
                break
        
        if not vocals_file:
            if logger:
                logger.error(f"Expected vocals file not found in {temp_output}")
            return None
        
        # Copy vocals to final output location
        final_vocals = output_dir / "vocals.wav"
        shutil.copy2(vocals_file, final_vocals)
        
        # Also save the accompaniment (music) for reference
        accompaniment_file = vocals_file.parent / "no_vocals.wav"
        if accompaniment_file.exists():
            final_accompaniment = output_dir / "accompaniment.wav"
            shutil.copy2(accompaniment_file, final_accompaniment)
            if logger:
                logger.debug(f"  Accompaniment saved: {final_accompaniment}")
        
        # Clean up temp directory
        shutil.rmtree(temp_output, ignore_errors=True)
        
        if logger:
            logger.info(f"✓ Vocals extracted: {final_vocals}")
            vocals_size = final_vocals.stat().st_size / (1024*1024)
            logger.debug(f"  Vocals file size: {vocals_size:.2f} MB")
        
        return final_vocals
        
    except subprocess.TimeoutExpired:
        if logger:
            logger.error("Demucs timed out after 10 minutes")
        return None
    except Exception as e:
        if logger:
            logger.error(f"Source separation failed: {e}")
        return None


def main():
    """Extract vocals from audio using source separation."""
    # Initialize stage I/O
    stage_io = StageIO("source_separation")
    logger = get_stage_logger("source_separation", log_level="DEBUG", stage_io=stage_io)
    
    logger.info("=" * 60)
    logger.info("SOURCE SEPARATION STAGE: Extract Vocals")
    logger.info("=" * 60)
    
    # Load job configuration (BEST PRACTICE: Read from job.json)
    # job.json is at the job directory root, which is output_base
    job_config_file = stage_io.output_base / "job.json"
    
    if not job_config_file.exists():
        logger.error(f"Job configuration not found: {job_config_file}")
        logger.error("This stage requires job configuration from prepare-job")
        return 1
    
    try:
        with open(job_config_file, 'r') as f:
            job_config = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load job configuration: {e}")
        return 1
    
    # Read source_separation configuration from job config
    sep_config = job_config.get("source_separation", {})
    enabled = sep_config.get("enabled", True)  # Default: enabled
    quality = sep_config.get("quality", "balanced")
    
    # Log configuration
    logger.info("Configuration:")
    logger.info(f"  Enabled: {enabled}")
    logger.info(f"  Quality: {quality}")
    logger.info(f"  Config source: job.json")
    
    if not enabled:
        logger.info("Source separation is disabled (skipping)")
        logger.info("To enable, set source_separation.enabled=true in job.json")
        logger.info("Or use: ./prepare-job.sh --source-separation")
        logger.info("=" * 60)
        return 0
    
    # Validate quality setting
    valid_qualities = ['fast', 'balanced', 'quality']
    if quality not in valid_qualities:
        logger.warning(f"Invalid quality '{quality}', using 'balanced'")
        quality = 'balanced'
    
    # Check if Demucs is installed
    if not check_demucs_installed():
        logger.warning("Demucs is not installed")
        # Try to install it
        if not install_demucs(logger):
            logger.error("Cannot proceed without Demucs")
            logger.error("To install manually: pip install demucs")
            return 1
    
    # Get input audio from demux stage
    input_audio = stage_io.output_base / "01_demux" / "audio.wav"
    
    if not input_audio.exists():
        logger.error(f"Input audio not found: {input_audio}")
        logger.error("Expected audio.wav in 01_demux/ directory from demux stage")
        return 1
    
    # Log input/output
    logger.info(f"📥 Input: {input_audio.relative_to(stage_io.output_base)}")
    logger.info(f"📤 Output: {stage_io.stage_dir.relative_to(stage_io.output_base)}/")
    logger.info(f"Input audio: {input_audio}")
    logger.info(f"Quality preset: {quality}")
    
    # Create output directory
    output_dir = stage_io.stage_dir
    
    # Separate vocals
    vocals_file = separate_vocals(input_audio, output_dir, quality, logger)
    
    if not vocals_file:
        logger.error("Source separation failed")
        return 1
    
    # Save the vocals as the output audio.wav
    # This will be used by downstream stages (VAD, ASR)
    output_audio = stage_io.get_output_path("audio.wav")
    shutil.copy2(vocals_file, output_audio)
    logger.info(f"✓ Output audio (vocals only): {output_audio}")
    
    # Save metadata
    metadata = {
        'status': 'completed',
        'input_audio': str(input_audio),
        'vocals_file': str(vocals_file),
        'output_audio': str(output_audio),
        'quality': quality,
        'method': 'demucs-htdemucs',
        'stems': 'two-stems (vocals + accompaniment)'
    }
    
    # Save original audio info for reference
    if input_audio.exists():
        metadata['original_size_mb'] = input_audio.stat().st_size / (1024*1024)
    if vocals_file.exists():
        metadata['vocals_size_mb'] = vocals_file.stat().st_size / (1024*1024)
    
    metadata_path = stage_io.save_metadata(metadata)
    logger.debug(f"Metadata saved: {metadata_path}")
    
    logger.info("=" * 60)
    logger.info("SOURCE SEPARATION COMPLETED")
    logger.info("Next stages will use vocals-only audio")
    logger.info("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
