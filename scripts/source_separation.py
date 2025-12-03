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
# Standard library
import sys
import os
import subprocess
import shutil
import json
import logging
from pathlib import Path
from typing import Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.stage_utils import StageIO, get_stage_logger

# Local
from shared.logger import get_logger
logger = get_logger(__name__)


def check_demucs_installed() -> bool:
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


def install_demucs(logger: logging.Logger) -> bool:
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
        logger.error(f"Failed to install Demucs: {e}", exc_info=True)
        return False


def separate_vocals(input_audio: Path, output_dir: Path, quality: str = "balanced", logger: Optional[logging.Logger] = None) -> None:
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
            logger.error("Demucs timed out after 10 minutes", exc_info=True)
        return None
    except Exception as e:
        if logger:
            logger.error(f"Source separation failed: {e}", exc_info=True)
        return None


def main() -> int:
    """Extract vocals from audio using source separation."""
    stage_io = None
    logger = None
    
    try:
        # Initialize stage I/O with manifest tracking
        stage_io = StageIO("source_separation", enable_manifest=True)
        logger = stage_io.get_stage_logger("INFO")
        
        logger.info("=" * 60)
        logger.info("SOURCE SEPARATION STAGE: Extract Vocals")
        logger.info("=" * 60)
        
        # Load job configuration (BEST PRACTICE: Read from job.json)
        # job.json is at the job directory root, which is output_base
        job_config_file = stage_io.output_base / "job.json"
        
        if not job_config_file.exists():
            logger.error(f"Job configuration not found: {job_config_file}")
            logger.error("This stage requires job configuration from prepare-job")
            stage_io.add_error("Job configuration not found")
            stage_io.finalize(status="failed", error="No job.json")
            return 1
        
        try:
            with open(job_config_file, 'r') as f:
                job_config = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in job configuration: {e}", exc_info=True)
            stage_io.add_error(f"Config parse failed: {e}", e)
            stage_io.finalize(status="failed", error=f"Invalid JSON: {e}")
            return 1
        except IOError as e:
            logger.error(f"Failed to read job configuration: {e}", exc_info=True)
            stage_io.add_error(f"Config read failed: {e}", e)
            stage_io.finalize(status="failed", error=f"IO error: {e}")
            return 1
        
        # Read source_separation configuration from job config
        sep_config = job_config.get("source_separation", {})
        enabled = sep_config.get("enabled", True)  # Default: enabled
        quality = sep_config.get("quality", "balanced")
        
        # Track configuration
        stage_io.set_config({
            "enabled": enabled,
            "quality": quality,
            "method": "demucs-htdemucs"
        })
        
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
            stage_io.finalize(status="skipped", reason="Disabled in config")
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
                stage_io.add_error("Demucs not installed and auto-install failed")
                stage_io.finalize(status="failed", error="Missing dependency: demucs")
                return 1
        
        # Get input audio from demux stage
        input_audio = stage_io.output_base / "01_demux" / "audio.wav"
        
        if not input_audio.exists():
            logger.error(f"Input audio not found: {input_audio}")
            logger.error("Expected audio.wav in 01_demux/ directory from demux stage")
            stage_io.add_error(f"Input audio not found: {input_audio}")
            stage_io.finalize(status="failed", error="Input file missing")
            return 1
        
        # Validate input file is readable
        try:
            input_size = input_audio.stat().st_size
            if input_size == 0:
                raise ValueError("Input audio file is empty")
            logger.debug(f"Input audio size: {input_size / (1024*1024):.2f} MB")
        except OSError as e:
            logger.error(f"Cannot access input audio: {e}", exc_info=True)
            stage_io.add_error(f"Input file access error: {e}")
            stage_io.finalize(status="failed", error=f"Cannot read input: {e}")
            return 1
        
        # Track input
        stage_io.track_input(input_audio, "audio", format="wav")
        
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
            stage_io.add_error("Vocal separation failed")
            stage_io.finalize(status="failed", error="Separation process failed")
            return 1
        
        # Validate vocals file was created successfully
        if not vocals_file.exists():
            logger.error(f"Vocals file not created: {vocals_file}")
            stage_io.add_error("Vocals file missing after separation")
            stage_io.finalize(status="failed", error="Output file not created")
            return 1
        
        vocals_size = vocals_file.stat().st_size
        if vocals_size == 0:
            logger.error("Vocals file is empty")
            stage_io.add_error("Empty vocals file produced")
            stage_io.finalize(status="failed", error="Empty output file")
            return 1
        
        # Save the vocals as the output audio.wav
        # This will be used by downstream stages (VAD, ASR)
        output_audio = stage_io.get_output_path("audio.wav")
        
        try:
            shutil.copy2(vocals_file, output_audio)
            logger.info(f"✓ Output audio (vocals only): {output_audio}")
        except IOError as e:
            logger.error(f"Failed to copy vocals to output: {e}", exc_info=True)
            stage_io.add_error(f"Output file copy failed: {e}")
            stage_io.finalize(status="failed", error=f"Cannot write output: {e}")
            return 1
        
        # Track outputs
        vocals_size_mb = vocals_file.stat().st_size / (1024*1024) if vocals_file.exists() else 0
        stage_io.track_output(output_audio, "audio",
                             format="wav",
                             type="vocals",
                             size_mb=round(vocals_size_mb, 2))
        
        # Track intermediate if separate vocals file kept
        if vocals_file != output_audio and vocals_file.exists():
            stage_io.track_intermediate(vocals_file, retained=True,
                                       reason="Original separated vocals")
        
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
        
        try:
            metadata_path = stage_io.save_metadata(metadata)
            logger.debug(f"Metadata saved: {metadata_path}")
            stage_io.track_intermediate(metadata_path, retained=True,
                                       reason="Stage metadata")
        except Exception as e:
            logger.warning(f"Failed to save metadata: {e}")
            # Non-fatal, continue
        
        # Finalize with success
        stage_io.finalize(status="success",
                         quality=quality,
                         vocals_size_mb=round(vocals_size_mb, 2))
        
        logger.info("=" * 60)
        logger.info("SOURCE SEPARATION COMPLETED")
        logger.info("Next stages will use vocals-only audio")
        logger.info("=" * 60)
        logger.info(f"Stage log: {stage_io.stage_log.relative_to(stage_io.output_base)}")
        logger.info(f"Stage manifest: {stage_io.manifest_path.relative_to(stage_io.output_base)}")
        
        return 0
    
    except FileNotFoundError as e:
        if logger:
            logger.error(f"File not found: {e}", exc_info=True, exc_info=True)
        if stage_io:
            stage_io.add_error(f"File not found: {e}")
            stage_io.finalize(status="failed", error=f"Missing file: {e}")
        return 1
    
    except IOError as e:
        if logger:
            logger.error(f"I/O error: {e}", exc_info=True, exc_info=True)
        if stage_io:
            stage_io.add_error(f"I/O error: {e}")
            stage_io.finalize(status="failed", error=f"IO error: {e}")
        return 1
    
    except ValueError as e:
        if logger:
            logger.error(f"Invalid value: {e}", exc_info=True, exc_info=True)
        if stage_io:
            stage_io.add_error(f"Validation error: {e}")
            stage_io.finalize(status="failed", error=f"Invalid input: {e}")
        return 1
    
    except subprocess.TimeoutExpired as e:
        if logger:
            logger.error(f"Processing timeout: {e}", exc_info=True, exc_info=True)
        if stage_io:
            stage_io.add_error(f"Timeout during processing: {e}")
            stage_io.finalize(status="failed", error="Processing timeout")
        return 1
    
    except KeyboardInterrupt:
        if logger:
            logger.warning("Interrupted by user")
        if stage_io:
            stage_io.add_error("User interrupted")
            stage_io.finalize(status="failed", error="User interrupted")
        return 130
    
    except Exception as e:
        if logger:
            logger.error(f"Unexpected error: {e}", exc_info=True, exc_info=True)
        else:
            logger.info(f"ERROR: {e}", file=sys.stderr)
        if stage_io:
            stage_io.add_error(f"Unexpected error: {e}")
            stage_io.finalize(status="failed", error=f"Unexpected: {type(e).__name__}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
