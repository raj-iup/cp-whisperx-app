#!/usr/bin/env python3
"""
Job Preparation Script for CP-WhisperX-App Pipeline

Creates job directory structure and prepares configuration based on parameters.
Copies config/.env.pipeline template and customizes it for the job.

Usage:
    python prepare-job.py <input_media> [OPTIONS]

Options:
    --transcribe          Transcribe-only workflow (faster)
    --native              Enable native GPU acceleration (MPS/CUDA)
    --start-time TIME     Start time for clip (HH:MM:SS)
    --end-time TIME       End time for clip (HH:MM:SS)

Example:
    # Full subtitle generation (default)
    python prepare-job.py /path/to/movie.mp4
    
    # Transcribe only with GPU acceleration
    python prepare-job.py /path/to/movie.mp4 --transcribe --native
    
    # Process clip for testing
    python prepare-job.py /path/to/movie.mp4 --start-time 00:10:00 --end-time 00:15:00

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
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict

# Add paths for imports
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR / 'shared'))

from shared.logger import PipelineLogger, get_stage_log_filename


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
                   end_time: Optional[str] = None) -> Dict:
        """Create a new job with directory structure and job definition.
        
        Args:
            input_media: Path to input media file
            workflow_mode: Workflow mode - 'transcribe' or 'subtitle-gen'
            native_mode: Enable native execution with device acceleration
            start_time: Optional start time for clipping (HH:MM:SS)
            end_time: Optional end time for clipping (HH:MM:SS)
        
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
        
        if start_time and end_time:
            job_info["clip_start"] = start_time
            job_info["clip_end"] = end_time
        
        # Save initial job definition
        with open(job_json_file, 'w') as f:
            json.dump(job_info, f, indent=2)
        
        if self.logger:
            self.logger.info(f"Job created: {job_id}")
            self.logger.info(f"User ID: {user_id}")
            self.logger.info(f"Workflow: {workflow_mode.upper()}")
            self.logger.info(f"Native mode: {'enabled' if native_mode else 'disabled'}")
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
        
        # Load config template from config/.env.pipeline
        config_template = Path("config/.env.pipeline")
        
        if not config_template.exists():
            if self.logger:
                self.logger.error(f"Config template not found: {config_template}")
                self.logger.error("Please ensure config/.env.pipeline exists")
            raise FileNotFoundError(f"Config template not found: {config_template}")
        
        if self.logger:
            self.logger.info(f"Using config template: {config_template}")
        
        # Read template
        with open(config_template) as f:
            config_content = f.read()
        
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
        
        # Detect device if native mode enabled
        device = 'cpu'
        if native_mode:
            device = detect_device_capability()
            if self.logger:
                self.logger.info(f"Native mode enabled - detected device: {device.upper()}")
                if device == 'cpu':
                    self.logger.warning("No GPU acceleration available, falling back to CPU")
        
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
        else:
            if self.logger:
                self.logger.info("Workflow: SUBTITLE-GEN (full pipeline)")
            workflow_config = {
                'WORKFLOW_MODE': 'subtitle-gen'
            }
        
        # Update config values
        config_lines = []
        job_id_set = False
        in_root_set = False
        output_root_set = False
        log_root_set = False
        workflow_mode_set = False
        
        for line in config_content.split('\n'):
            # Skip removed fields
            if line.startswith('INPUT_FILE=') or \
               line.startswith('INPUT_URL=') or \
               line.startswith('CLIP_VIDEO=') or \
               line.startswith('START_CLIP=') or \
               line.startswith('END_CLIP='):
                continue
                
            if line.startswith('JOB_ID='):
                config_lines.append(f'JOB_ID={job_info["job_id"]}')
                job_id_set = True
            elif line.startswith('IN_ROOT='):
                config_lines.append(f'IN_ROOT={media_path.absolute()}')
                in_root_set = True
            elif line.startswith('OUTPUT_ROOT='):
                config_lines.append(f'OUTPUT_ROOT={output_root}')
                output_root_set = True
            elif line.startswith('LOG_ROOT='):
                config_lines.append(f'LOG_ROOT={log_root}')
                log_root_set = True
            elif line.startswith('WORKFLOW_MODE='):
                config_lines.append(f'WORKFLOW_MODE={workflow_config.get("WORKFLOW_MODE", "subtitle-gen")}')
                workflow_mode_set = True
            elif native_mode and line.startswith('WHISPERX_DEVICE='):
                config_lines.append(f'WHISPERX_DEVICE={device.upper()}')
            elif native_mode and line.startswith('DIARIZATION_DEVICE='):
                config_lines.append(f'DIARIZATION_DEVICE={device.upper()}')
            elif native_mode and line.startswith('PYANNOTE_DEVICE='):
                config_lines.append(f'PYANNOTE_DEVICE={device.upper()}')
            elif workflow_mode == 'transcribe' and line.split('=')[0] in workflow_config:
                # Override workflow-specific settings
                key = line.split('=')[0]
                config_lines.append(f'{key}={workflow_config[key]}')
            elif line.startswith('WHISPER_MODEL='):
                if line == 'WHISPER_MODEL=' or not line.split('=', 1)[1].strip():
                    config_lines.append('WHISPER_MODEL=large-v3')
                else:
                    config_lines.append(line)
            else:
                config_lines.append(line)
        
        # Add if not present (find insertion point after comments)
        insert_idx = 0
        for i, line in enumerate(config_lines):
            if line.strip() and not line.strip().startswith('#'):
                insert_idx = i
                break
        
        if not job_id_set:
            config_lines.insert(insert_idx, f'JOB_ID={job_info["job_id"]}')
            insert_idx += 1
            
        if not in_root_set:
            config_lines.insert(insert_idx, f'IN_ROOT={media_path.absolute()}')
            insert_idx += 1
            
        if not output_root_set:
            config_lines.insert(insert_idx, f'OUTPUT_ROOT={output_root}')
            insert_idx += 1
            
        if not log_root_set:
            config_lines.insert(insert_idx, f'LOG_ROOT={log_root}')
            insert_idx += 1
        
        if not workflow_mode_set:
            config_lines.insert(insert_idx, f'WORKFLOW_MODE={workflow_config.get("WORKFLOW_MODE", "subtitle-gen")}')
            insert_idx += 1
        
        # Add workflow-specific overrides at the end
        if workflow_mode == 'transcribe':
            config_lines.append('')
            config_lines.append('# Transcribe workflow overrides')
            for key, value in workflow_config.items():
                if key != 'WORKFLOW_MODE':
                    config_lines.append(f'{key}={value}')
        
        # Add device settings if native mode
        if native_mode:
            config_lines.append('')
            config_lines.append(f'# Native execution with {device.upper()} acceleration')
        
        # Write job environment file
        with open(job_env_file, 'w') as f:
            f.write('\n'.join(config_lines))
        
        # Update job info
        job_info["media_path"] = str(media_path.absolute())
        job_info["output_root"] = output_root
        job_info["log_root"] = log_root
        # Update job info with final paths
        job_info["job_env_file"] = str(job_env_file.absolute())
        job_info["media_path"] = str(media_path.absolute())
        job_info["output_root"] = output_root
        job_info["log_root"] = log_root
        job_info["workflow_mode"] = workflow_mode
        job_info["native_mode"] = native_mode
        if native_mode:
            job_info["device"] = device
        job_info["status"] = "ready"
        
        # Update job.json file
        job_dir = Path(job_info["job_dir"])
        job_json_file = job_dir / "job.json"
        with open(job_json_file, 'w') as f:
            json.dump(job_info, f, indent=2)
        
        if self.logger:
            self.logger.info(f"Job environment file created: {job_env_file}")
            self.logger.info(f"Job definition updated: {job_json_file}")
            self.logger.info("✓ Job ready for pipeline processing")
            self.logger.info(f"  Run: python pipeline.py --job {job_info['job_id']}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Prepare job for CP-WhisperX-App pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process full movie with subtitle generation (default)
  python prepare-job.py /path/to/movie.mp4
  
  # Transcribe only (faster, no subtitles)
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
    
    parser.add_argument(
        "--transcribe",
        action="store_true",
        help="Transcribe-only workflow (skip diarization, NER, subtitle gen, mux)"
    )
    
    parser.add_argument(
        "--subtitle-gen",
        action="store_true",
        help="Full subtitle generation workflow (default)"
    )
    
    parser.add_argument(
        "--native",
        action="store_true",
        help="Enable native execution with MPS/CUDA acceleration (auto-detects capability)"
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
    
    # Validate workflow flags
    if args.transcribe and args.subtitle_gen:
        print("✗ Cannot specify both --transcribe and --subtitle-gen")
        sys.exit(1)
    
    # Determine workflow mode
    if args.transcribe:
        workflow_mode = 'transcribe'
    else:
        workflow_mode = 'subtitle-gen'  # default
    
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
    if args.native:
        detected_device = detect_device_capability()
        logger.info(f"Native mode: ENABLED (detected: {detected_device.upper()})")
    if args.start_time and args.end_time:
        logger.info(f"Clip mode: {args.start_time} → {args.end_time}")
    
    # Create job
    manager = JobManager(logger=logger)
    
    job_info = manager.create_job(
        input_media,
        workflow_mode=workflow_mode,
        native_mode=args.native,
        start_time=args.start_time,
        end_time=args.end_time
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
    logger.info(f"Environment File: {job_info['job_env_file']}")
    logger.info(f"Media File: {job_info['media_path']}")
    logger.info(f"Workflow Mode: {workflow_mode.upper()}")
    if args.native:
        logger.info(f"Native Execution: {job_info.get('device', 'cpu').upper()}")
    
    if job_info.get("is_clip"):
        logger.info(f"Clip Duration: {args.start_time} → {args.end_time}")
    
    logger.info("")
    logger.info("Next step:")
    logger.info(f"  python pipeline.py --job {job_info['job_id']}")
    
    # Also print to console for user
    print(f"\n✓ Job created: {job_info['job_id']}")
    print(f"  Directory: {job_info['job_dir']}")
    print(f"  Workflow: {workflow_mode.upper()}")
    if args.native:
        print(f"  Native mode: {job_info.get('device', 'cpu').upper()}")
    print(f"  Log: {log_file}")
    print(f"\nNext step:")
    print(f"  python pipeline.py --job {job_info['job_id']}")
    print()


if __name__ == "__main__":
    main()
