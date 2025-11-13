#!/usr/bin/env python3
"""
CP-WhisperX-App Pipeline Orchestrator
Job-based execution with manifest tracking and resume capability
"""
import sys
import os
import platform
import subprocess
import json
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Add paths for imports
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.logger import PipelineLogger, get_stage_log_filename
from shared.config import load_config
from shared.utils import parse_filename
from shared.manifest import ManifestBuilder


# Stage configuration
# (stage_name, next_stage, service_name, timeout_seconds, critical, uses_ml_model)
STAGE_DEFINITIONS = [
    ("demux", "tmdb", "demux", 600, True, False),
    ("tmdb", "pre_ner", "tmdb", 120, False, False),
    ("pre_ner", "silero_vad", "pre-ner", 300, False, False),
    ("silero_vad", "pyannote_vad", "silero-vad", 1800, True, True),  # ML: PyTorch
    ("pyannote_vad", "asr", "pyannote-vad", 3600, True, True),  # ML: PyTorch
    ("asr", "diarization", "asr", 14400, True, True),  # ML: PyTorch (Whisper)
    ("diarization", "glossary_builder", "diarization", 7200, True, True),  # ML: PyTorch
    ("glossary_builder", "second_pass_translation", "glossary-builder", 300, False, False),  # Build glossary after ASR
    ("second_pass_translation", "lyrics_detection", "second-pass-translation", 7200, False, True),  # ML: Translation models
    ("lyrics_detection", "post_ner", "lyrics-detection", 1800, False, True),  # ML: Audio analysis
    ("post_ner", "subtitle_gen", "post-ner", 1200, False, False),
    ("subtitle_gen", "mux", "subtitle-gen", 600, True, False),
    ("mux", "finalize", "mux", 600, True, False),
    ("finalize", None, "finalize", 60, False, False),  # New: organize output
]

# ML stages that can run natively with MPS/CUDA
# Maps stage_name -> script filename in scripts/ directory
ML_STAGES = {
    "silero_vad": "silero_vad.py",
    "pyannote_vad": "pyannote_vad.py",
    "diarization": "diarization.py",
    "asr": "whisperx_asr.py",
    "second_pass_translation": "second_pass_translation.py",
    "lyrics_detection": "lyrics_detection.py"
}

# All stage scripts (for native execution)
# Maps stage_name -> script filename in scripts/ directory
STAGE_SCRIPTS = {
    "demux": "demux.py",
    "tmdb": "tmdb.py",
    "pre_ner": "pre_ner.py",
    "silero_vad": "silero_vad.py",
    "pyannote_vad": "pyannote_vad.py",
    "diarization": "diarization.py",
    "asr": "whisperx_asr.py",
    "glossary_builder": "glossary_builder.py",
    "second_pass_translation": "second_pass_translation.py",
    "lyrics_detection": "lyrics_detection.py",
    "post_ner": "post_ner.py",
    "subtitle_gen": "subtitle_gen.py",
    "mux": "mux.py",
    "finalize": "finalize.py"
}


class JobOrchestrator:
    """Orchestrates pipeline execution for a specific job."""
    
    def __init__(self, job_id: str, stages: Optional[List[str]] = None):
        """Initialize orchestrator for a job.
        
        Args:
            job_id: Job identifier (e.g., "20251101-0001")
            stages: Optional list of specific stages to run
        """
        self.job_id = job_id
        
        # Load job information
        self.job_info = self._load_job_info(job_id)
        if not self.job_info:
            raise ValueError(f"Job not found: {job_id}")
        
        # Load job configuration
        job_env_file = Path(self.job_info["env_file"])
        if not job_env_file.exists():
            raise ValueError(f"Job environment file not found: {job_env_file}")
        
        self.config = load_config(str(job_env_file))
        
        # Filter stages if specified
        if stages:
            self.stages = [s for s in STAGE_DEFINITIONS if s[0] in stages]
            if len(self.stages) != len(stages):
                found = {s[0] for s in self.stages}
                missing = set(stages) - found
                print(f"Warning: Unknown stages skipped: {missing}")
        else:
            # Filter stages based on workflow mode
            workflow_mode = getattr(self.config, 'workflow_mode', 'subtitle-gen')
            if workflow_mode == 'transcribe':
                # Transcribe workflow: demux → silero_vad → asr only
                transcribe_stages = ['demux', 'silero_vad', 'asr']
                self.stages = [s for s in STAGE_DEFINITIONS if s[0] in transcribe_stages]
                # Update stage transitions for transcribe workflow
                self.stages = [
                    ("demux", "silero_vad", "demux", 600, True, False),
                    ("silero_vad", "asr", "silero-vad", 1800, True, True),
                    ("asr", None, "asr", 14400, True, True),
                ]
            else:
                # Full subtitle-gen workflow
                self.stages = STAGE_DEFINITIONS.copy()
                
                # Apply stage control flags from config
                # Check for STEP_VAD_SILERO, STEP_VAD_PYANNOTE, STEP_DIARIZATION flags
                silero_enabled = getattr(self.config, 'step_vad_silero', True)
                pyannote_enabled = getattr(self.config, 'step_vad_pyannote', True)
                diarization_enabled = getattr(self.config, 'step_diarization', True)
                
                # Filter out disabled stages and fix stage transitions
                enabled_stages = []
                for stage in self.stages:
                    stage_name = stage[0]
                    
                    # Skip disabled stages
                    if stage_name == 'silero_vad' and not silero_enabled:
                        continue
                    elif stage_name == 'pyannote_vad' and not pyannote_enabled:
                        continue
                    elif stage_name == 'diarization' and not diarization_enabled:
                        continue
                    
                    enabled_stages.append(stage)
                
                # Fix stage transitions based on what's enabled
                self.stages = self._fix_stage_transitions(enabled_stages, silero_enabled, pyannote_enabled, diarization_enabled)
        
        # Setup output directory (from config or calculate from job)
        if hasattr(self.config, 'output_root') and self.config.output_root and not self.config.output_root.startswith('./'):
            # Use configured output path
            self.output_dir = Path(self.config.output_root)
        else:
            # Calculate from job structure
            self.output_dir = self._get_output_dir()
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        # Setup log directory - logs subdirectory inside output directory
        self.log_dir = self.output_dir / "logs"
        self.log_dir.mkdir(exist_ok=True, parents=True)
        
        # Setup logger (must be done before device detection logging)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_filename = get_stage_log_filename("orchestrator", timestamp)
        log_file = self.log_dir / log_filename
        log_level = self.config.log_level.upper() if hasattr(self.config, 'log_level') else "INFO"
        
        self.logger = PipelineLogger("orchestrator", log_file, log_level=log_level)
        
        # Detect device type from config (after logger is initialized)
        self.device_type = self._detect_device_type()
        
        self.logger.info(f"Job: {job_id}")
        self.logger.info(f"Environment: {job_env_file}")
        self.logger.info(f"Output: {self.output_dir}")
        self.logger.info(f"Logs: {self.log_dir}")
        self.logger.info(f"Platform: {platform.system()}")
        self.logger.info(f"Device mode: {self.device_type.upper()}")
        
        # Platform-aware execution mode info
        system = platform.system()
        all_stage_names = [s[0] for s in self.stages]
        
        if all_stage_names:
            # Check if native mode is available
            native_available = Path(".bollyenv/Scripts/python.exe").exists() if system == 'Windows' else Path(".bollyenv/bin/python").exists()
            
            if system == 'Darwin' and self.device_type == 'mps':
                if native_available:
                    self.logger.info("✓ Execution mode: Native MPS (macOS)")
                    self.logger.info(f"  All stages will run with Apple Silicon GPU acceleration")
                else:
                    self.logger.warning("⚠️  Native mode unavailable - falling back to Docker CPU")
                    self.logger.warning("   Run bootstrap: ./scripts/bootstrap.sh")
            elif system == 'Windows':
                if native_available:
                    if self.device_type == 'cuda':
                        self.logger.info("✓ Execution mode: Native CUDA (Windows)")
                        self.logger.info(f"  All stages will run with NVIDIA GPU acceleration")
                    else:
                        self.logger.info("✓ Execution mode: Native CPU (Windows)")
                        self.logger.info(f"  All stages will run on CPU")
                else:
                    self.logger.warning("⚠️  Native mode unavailable - would fallback to Docker")
                    self.logger.warning("   Run bootstrap: .\\scripts\\bootstrap.ps1")
            elif system == 'Linux':
                if self.device_type == 'cuda':
                    self.logger.info("✓ Execution mode: Docker CUDA (Linux)")
                    self.logger.info(f"  ML stages will run in CUDA containers")
                else:
                    self.logger.info("✓ Execution mode: Docker CPU (Linux)")
                    self.logger.info(f"  All stages will run in CPU containers")
            
            self.logger.info(f"  Stages: {', '.join(all_stage_names)}")
            
            # Performance recommendations
            if self.device_type == 'cpu' and system != 'Linux':
                self.logger.warning("")
                self.logger.warning("⚠️  Performance Notice:")
                if system == 'Darwin':
                    self.logger.warning("   For faster processing: Set DEVICE=mps (Apple Silicon)")
                else:
                    self.logger.warning("   For faster processing: Set DEVICE=cuda (NVIDIA GPU)")
        
        # Log workflow mode
        workflow_mode = getattr(self.config, 'workflow_mode', 'subtitle-gen')
        self.logger.info(f"Workflow: {workflow_mode.upper()}")
        
        if stages:
            self.logger.info(f"Running stages: {', '.join([s[0] for s in self.stages])}")
        elif workflow_mode == 'transcribe':
            self.logger.info("Transcribe workflow: demux → silero_vad → asr → transcript.txt")
        
        self.manifest = None
        self.start_time = datetime.now()
    
    def _load_job_info(self, job_id: str) -> Optional[Dict]:
        """Load job information from job directory."""
        # Parse job ID to get date components
        # Format: YYYYMMDD-NNNN
        if len(job_id) != 13 or job_id[8] != '-':
            raise ValueError(f"Invalid job ID format: {job_id} (expected: YYYYMMDD-NNNN)")
        
        year = job_id[0:4]
        month = job_id[4:6]
        day = job_id[6:8]
        
        # Try to find job in output directory (new structure)
        # Search under out/YYYY/MM/DD/*/job_id/ for job.json
        date_dir = Path("out") / year / month / day
        if date_dir.exists():
            for user_dir in date_dir.iterdir():
                if user_dir.is_dir():
                    job_file = user_dir / job_id / "job.json"
                    if job_file.exists():
                        with open(job_file, 'r', encoding='utf-8', errors='replace') as f:
                            return json.load(f)
        
        # Fallback: Try old jobs/ structure for backwards compatibility
        tracking_file = Path("jobs") / year / month / day / "jobs.json"
        if tracking_file.exists():
            with open(tracking_file, 'r', encoding='utf-8', errors='replace') as f:
                tracking_data = json.load(f)
            for job in tracking_data.get("jobs", []):
                if job["job_id"] == job_id:
                    return job
        
        return None
    
    def _get_output_dir(self) -> Path:
        """Get output directory for job."""
        year = self.job_id[0:4]
        month = self.job_id[4:6]
        day = self.job_id[6:8]
        user_id = self.config.user_id if hasattr(self.config, 'user_id') else 1
        return Path("out") / year / month / day / str(user_id) / self.job_id
    
    def _fix_stage_transitions(self, stages: List, silero_enabled: bool, 
                               pyannote_enabled: bool, diarization_enabled: bool) -> List:
        """Fix stage transitions when stages are disabled.
        
        Args:
            stages: List of enabled stage tuples
            silero_enabled: Whether Silero VAD is enabled
            pyannote_enabled: Whether PyAnnote VAD is enabled
            diarization_enabled: Whether Diarization is enabled
        
        Returns:
            List of stage tuples with corrected transitions
        """
        if not stages:
            return stages
        
        # Build mapping of stage names to indices
        stage_names = [s[0] for s in stages]
        
        # Fix transitions
        fixed_stages = []
        for i, stage in enumerate(stages):
            stage_name, next_stage, service, timeout, critical, uses_ml = stage
            
            # Determine correct next stage
            if next_stage and next_stage not in stage_names:
                # Next stage is disabled, find the next enabled stage
                if stage_name == 'pre_ner':
                    # pre_ner -> silero_vad (if enabled) -> pyannote_vad (if enabled) -> asr
                    if silero_enabled:
                        new_next = 'silero_vad'
                    elif pyannote_enabled:
                        new_next = 'pyannote_vad'
                    else:
                        new_next = 'asr'
                elif stage_name == 'silero_vad':
                    # silero_vad -> pyannote_vad (if enabled) -> asr
                    if pyannote_enabled:
                        new_next = 'pyannote_vad'
                    else:
                        new_next = 'asr'
                elif stage_name == 'pyannote_vad':
                    # pyannote_vad -> asr
                    new_next = 'asr'
                elif stage_name == 'asr':
                    # asr -> diarization (if enabled) -> glossary_builder
                    if diarization_enabled:
                        new_next = 'diarization'
                    else:
                        new_next = 'glossary_builder'
                else:
                    # For other stages, find next available
                    new_next = None
                    for j in range(i + 1, len(stages)):
                        new_next = stages[j][0]
                        break
                
                fixed_stages.append((stage_name, new_next, service, timeout, critical, uses_ml))
            else:
                fixed_stages.append(stage)
        
        return fixed_stages
    
    def _detect_device_type(self) -> str:
        """Detect device type from job configuration.
        
        Returns:
            Device type: 'cpu', 'mps', or 'cuda'
        """
        # Check for global DEVICE setting (new format)
        device = getattr(self.config, 'device', None)
        if device:
            device_lower = str(device).lower()
            if device_lower in ['cpu', 'mps', 'cuda']:
                return device_lower
        
        # Check for DEVICE_WHISPERX (legacy support)
        device_whisperx = getattr(self.config, 'device_whisperx', None)
        if device_whisperx:
            device_lower = str(device_whisperx).lower()
            if device_lower in ['cpu', 'mps', 'cuda']:
                return device_lower
        
        # Default to CPU
        return 'cpu'
    
    def _should_run_native(self, stage_name: str) -> bool:
        """Check if stage should run natively (not in Docker).
        
        Platform-specific native execution strategy:
        - Windows: Native CUDA/CPU with .bollyenv (ALL stages - preferred)
        - macOS: Native MPS with .bollyenv (ALL stages - preferred)
        - Linux: Docker mode (CUDA/CPU containers)
        
        Args:
            stage_name: Stage name
        
        Returns:
            True if stage should run natively,
            False if should run in Docker
        """
        # Check platform
        system = platform.system()
        
        # macOS: Native execution (all stages)
        if system == 'Darwin':
            native_venv_available = self._check_native_venv_available(stage_name)
            if native_venv_available:
                self.logger.debug(f"Native execution available for {stage_name}")
                return True
            else:
                self.logger.debug(f"Native venv not available, falling back to Docker")
                return False
        
        # Windows: Native execution (all stages - preferred)
        # Check if native environment is available
        if system == 'Windows':
            # Check for native venv setup
            native_venv_available = self._check_native_venv_available(stage_name)
            if native_venv_available:
                self.logger.debug(f"Native execution available for {stage_name}")
                return True
            else:
                self.logger.debug(f"Native venv not available, falling back to Docker")
                return False
        
        # Linux: Always use Docker (CUDA or CPU containers)
        return False
    
    def _check_native_venv_available(self, stage_name: str) -> bool:
        """Check if native virtual environment is available for a stage.
        
        Args:
            stage_name: Stage name
            
        Returns:
            True if native venv exists and has Python
        """
        # Check for unified .bollyenv (Windows/macOS unified environment)
        system = platform.system()
        if system == 'Windows':
            # Windows uses .bollyenv/Scripts/python.exe
            python_bin = Path(".bollyenv") / "Scripts" / "python.exe"
        elif system == 'Darwin':
            # macOS uses .bollyenv/bin/python
            python_bin = Path(".bollyenv") / "bin" / "python"
        else:
            # Linux uses per-stage venvs (fallback)
            venv_map = {
                "silero_vad": "vad",
                "pyannote_vad": "vad",
                "diarization": "diarization",
                "asr": "asr",
                "second_pass_translation": "asr",
                "lyrics_detection": "asr"
            }
            venv_name = venv_map.get(stage_name, "base")
            venv_dir = Path("native/venvs") / venv_name
            python_bin = venv_dir / "bin" / "python"
        
        exists = python_bin.exists()
        if exists:
            self.logger.debug(f"Native Python found: {python_bin}")
        else:
            self.logger.debug(f"Native Python not found: {python_bin}")
        
        return exists
    
    def run_native_step(self, stage_name: str, script_name: str, args: List[str] = None, timeout: int = 3600, force_device: str = None) -> bool:
        """Run a pipeline stage natively (outside Docker).
        
        Supports:
        - Windows: .bollyenv/Scripts/python.exe with scripts from scripts/
        - macOS: .bollyenv/bin/python with scripts from scripts/
        - Linux: .bollyenv/bin/python with scripts from scripts/
        
        Args:
            stage_name: Stage name
            script_name: Native script filename
            args: Arguments to pass to script
            timeout: Maximum execution time in seconds
            force_device: Override device (for CPU fallback)
        
        Returns:
            True if successful, False otherwise
        """
        system = platform.system()
        
        # Determine Python binary path and script path
        # All platforms now use unified .bollyenv and scripts/ directory
        if system == 'Windows':
            python_bin = Path(".bollyenv") / "Scripts" / "python.exe"
        else:
            # macOS and Linux use .bollyenv/bin/python
            python_bin = Path(".bollyenv") / "bin" / "python"
        
        # All scripts are now in scripts/ directory
        script_path = Path("scripts") / script_name
        
        if not python_bin.exists():
            self.logger.error(f"Python not found: {python_bin}")
            self.logger.error("Run bootstrap: .\\scripts\\bootstrap.ps1 (Windows) or ./scripts/bootstrap.sh (Unix)")
            return False
        
        if not script_path.exists():
            self.logger.error(f"Script not found: {script_path}")
            return False
        
        # Determine device for this run
        device_for_run = force_device if force_device else self.device_type
        
        # Set up environment
        env = os.environ.copy()
        env['CONFIG_PATH'] = str(Path(self.job_info['env_file']).absolute())
        env['OUTPUT_DIR'] = str(self.output_dir.absolute())
        env['LOG_ROOT'] = str(self.log_dir.absolute())
        env['EXECUTION_MODE'] = 'native'  # Tell script it's running natively
        
        # Add HF_TOKEN for models that require authentication (PyAnnote, etc.)
        if hasattr(self.config, 'hf_token') and self.config.hf_token:
            env['HF_TOKEN'] = self.config.hf_token
        
        # Override device if CPU fallback is requested
        if force_device:
            env['DEVICE_OVERRIDE'] = force_device.upper()
        
        # Add shared directory to PYTHONPATH for imports
        shared_dir = str(Path("shared").absolute())
        if 'PYTHONPATH' in env:
            env['PYTHONPATH'] = f"{shared_dir}{os.pathsep}{env['PYTHONPATH']}"
        else:
            env['PYTHONPATH'] = shared_dir
        
        # Build command
        cmd = [str(python_bin), str(script_path)]
        if args:
            cmd.extend(args)
        
        self.logger.debug(f"Command: {' '.join(cmd)}")
        self.logger.debug(f"Config: {env['CONFIG_PATH']}")
        self.logger.debug(f"Output: {env['OUTPUT_DIR']}")
        self.logger.debug(f"Device: {device_for_run}")
        self.logger.debug(f"Timeout: {timeout}s")
        
        # Warn about CPU for ML stages
        if stage_name in ML_STAGES and device_for_run == "cpu":
            if force_device:
                self.logger.info(f"Running {stage_name} on CPU (fallback from {self.device_type.upper()})")
            else:
                self.logger.warning(f"⚠️  Running {stage_name} on CPU - this will be VERY SLOW")
                self.logger.warning(f"⚠️  Expected time: 2-4 hours for 2-hour movie")
                self.logger.warning(f"⚠️  Recommendation: Enable GPU (CUDA) or skip stage")
                self.logger.warning(f"⚠️  To skip: Set STEP_{stage_name.upper()}=false in config/.env.pipeline")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',  # Replace decode errors with �
                timeout=timeout,
                check=False,
                env=env,
                cwd=str(Path.cwd())
            )
            
            # Log stdout
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        self.logger.debug(f"  {line}")
            
            # Filter and log stderr - ignore progress bars
            if result.stderr:
                for line in result.stderr.strip().split('\n'):
                    line = line.strip()
                    if not line:
                        continue
                    # Skip progress bar lines
                    if any(x in line for x in ['%|', '█', 'MB/s', 'Downloading:', 'model.safetensors']):
                        continue
                    # Log actual errors
                    if any(x in line.lower() for x in ['error', 'exception', 'failed', 'traceback']):
                        self.logger.error(f"  {line}")
                    else:
                        self.logger.warning(f"  {line}")
            
            # Check exit code
            if result.returncode != 0:
                # Handle specific error codes
                if result.returncode == -11:
                    self.logger.error(f"Native script crashed with SIGSEGV (segmentation fault)")
                    if stage_name in ML_STAGES and self.device_type == 'mps':
                        self.logger.error(f"  This is likely a PyTorch MPS memory issue")
                        self.logger.error(f"  The stage will retry on CPU")
                elif result.returncode == -9:
                    self.logger.error(f"Native script was killed (possibly out of memory)")
                elif result.returncode < 0:
                    self.logger.error(f"Native script terminated by signal {-result.returncode}")
                else:
                    self.logger.error(f"Native script exited with code {result.returncode}")
                return False
            
            return True
            
        except subprocess.TimeoutExpired as e:
            self.logger.error(f"Stage timed out after {timeout}s")
            # Log any partial output
            if hasattr(e, 'stdout') and e.stdout:
                self.logger.error("Partial stdout before timeout:")
                for line in e.stdout.strip().split('\n')[-20:]:
                    if line.strip():
                        self.logger.error(f"  {line}")
            return False
        
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    def should_skip_stage(self, stage_name: str) -> bool:
        """Check if stage should be skipped based on manifest."""
        if not self.manifest:
            return False
        completed = self.manifest.data["pipeline"].get("completed_stages", [])
        return stage_name in completed
    
    def run_docker_step(self, service_name: str, args: List[str] = None, timeout: int = 3600, use_cuda: bool = False) -> bool:
        """Run a pipeline stage in Docker container.
        
        Args:
            service_name: Docker Compose service name
            args: Arguments to pass to container
            timeout: Maximum execution time in seconds
            use_cuda: Enable CUDA GPU support (Linux/Windows)
        
        Returns:
            True if successful, False otherwise
        """
        # Set up environment
        env = os.environ.copy()
        env['CONFIG_PATH'] = self._to_container_path(Path(self.job_info['env_file']))
        env['OUTPUT_DIR'] = str(self.output_dir)
        env['LOG_ROOT'] = str(self.log_dir)
        
        # Clean up old containers
        container_prefix = f"cp_whisperx_{service_name.replace('-', '_')}"
        try:
            subprocess.run(
                ["docker", "rm", "-f", container_prefix],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                check=False
            )
        except:
            pass
        
        # Build command
        cmd = [
            "docker", "compose", "-f", "docker-compose.yml",
            "run", "--rm"
        ]
        
        # Add CUDA GPU support for Linux/Windows
        if use_cuda:
            cmd.extend(["--gpus", "all"])
        
        # Add environment variables
        cmd.extend([
            "-e", f"CONFIG_PATH={env['CONFIG_PATH']}",
            "-e", f"OUTPUT_DIR={env['OUTPUT_DIR']}",
            "-e", f"LOG_ROOT={env['LOG_ROOT']}",
        ])
        
        # Add service name
        cmd.append(service_name)
        
        if args:
            cmd.extend(args)
        
        self.logger.debug(f"Command: {' '.join(cmd)}")
        self.logger.debug(f"Config: {env['CONFIG_PATH']}")
        self.logger.debug(f"Output: {env['OUTPUT_DIR']}")
        self.logger.debug(f"Log Dir: {env['LOG_ROOT']}")
        self.logger.debug(f"Timeout: {timeout}s")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=timeout,
                check=False,  # Don't raise on non-zero exit
                env=env
            )
            
            # Log stdout
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        self.logger.debug(f"  {line}")
            
            # Filter and log stderr - ignore progress bars
            if result.stderr:
                for line in result.stderr.strip().split('\n'):
                    line = line.strip()
                    if not line:
                        continue
                    # Skip progress bar lines (contain %, █, or download progress indicators)
                    if any(x in line for x in ['%|', '█', 'MB/s', 'Downloading:', 'model.safetensors']):
                        continue
                    # Log actual errors
                    if any(x in line.lower() for x in ['error', 'exception', 'failed', 'traceback']):
                        self.logger.error(f"  {line}")
                    else:
                        self.logger.warning(f"  {line}")
            
            # Check exit code
            if result.returncode != 0:
                self.logger.error(f"Container exited with code {result.returncode}")
                return False
            
            return True
            
        except subprocess.TimeoutExpired as e:
            self.logger.error(f"Stage timed out after {timeout}s")
            # Log any partial output
            if hasattr(e, 'stdout') and e.stdout:
                self.logger.error("Partial stdout before timeout:")
                for line in e.stdout.strip().split('\n')[-20:]:  # Last 20 lines
                    if line.strip():
                        self.logger.error(f"  {line}")
            return False
        
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    def run_pipeline(self, resume: bool = True) -> bool:
        """Run the pipeline for this job.
        
        Args:
            resume: Whether to resume from previous run
        
        Returns:
            True if successful, False otherwise
        """
        self.logger.info("="*60)
        self.logger.info("CP-WHISPERX-APP PIPELINE STARTED")
        self.logger.info("="*60)
        self.logger.info(f"Job ID: {self.job_id}")
        self.logger.info(f"Media: {self.job_info['source_media']}")
        self.logger.info(f"Resume: {'enabled' if resume else 'disabled'}")
        
        # Get input media path
        input_path = Path(self.job_info["source_media"])
        if not input_path.exists():
            self.logger.error(f"Media file not found: {input_path}")
            return False
        
        # Parse filename for metadata
        file_info = parse_filename(input_path.name)
        title = file_info.get('title', input_path.stem)
        year = file_info.get('year')
        
        self.logger.info(f"Title: {title}")
        if year:
            self.logger.info(f"Year: {year}")
        
        # Initialize manifest
        manifest_file = self.output_dir / "manifest.json"
        
        if not resume and manifest_file.exists():
            self.logger.info("Starting fresh: removing previous manifest")
            manifest_file.unlink()
        
        self.manifest = ManifestBuilder(
            manifest_file,
            job_id=self.job_id,
            user_id=self.config.user_id if hasattr(self.config, 'user_id') else 1,
            job_env_file=Path(self.job_info["env_file"])
        )
        self.manifest.set_input(str(input_path), title, year, self.job_id)
        self.manifest.set_output_dir(str(self.output_dir))
        
        # Check for resume
        if resume and manifest_file.exists():
            completed = self.manifest.data["pipeline"].get("completed_stages", [])
            if completed:
                self.logger.info("")
                self.logger.info("📋 RESUMING FROM PREVIOUS RUN")
                self.logger.info(f"   Completed: {', '.join(completed)}")
                self.logger.info("")
        
        # Execute stages
        total_stages = len(self.stages)
        for idx, (stage_name, next_stage, service, timeout, critical, uses_ml) in enumerate(self.stages, 1):
            self.logger.info("")
            self.logger.info("="*60)
            self.logger.info(f"STAGE {idx}/{total_stages}: {stage_name.upper()}")
            self.logger.info("="*60)
            
            # Check if should skip
            if resume and self.should_skip_stage(stage_name):
                self.logger.info(f"⏭️  Skipping - already completed")
                continue
            
            # Check if stage is conditionally enabled
            if stage_name == "glossary_builder":
                if not getattr(self.config, 'glossary_enable', True):
                    self.logger.info(f"⏭️  Skipping - disabled in config (GLOSSARY_ENABLE=false)")
                    continue
            
            if stage_name == "second_pass_translation":
                if not getattr(self.config, 'second_pass_enabled', False):
                    self.logger.info(f"⏭️  Skipping - disabled in config (SECOND_PASS_ENABLED=false)")
                    continue
            
            if stage_name == "lyrics_detection":
                if not getattr(self.config, 'lyric_detect_enabled', False):
                    self.logger.info(f"⏭️  Skipping - disabled in config (LYRIC_DETECT_ENABLED=false)")
                    continue
            
            # Special handling for finalize stage (output organization)
            if stage_name == "finalize":
                self.logger.info("📁 Organizing final output...")
                try:
                    finalize_script = PROJECT_ROOT / "scripts" / "finalize_output.py"
                    result = subprocess.run(
                        [sys.executable, str(finalize_script), str(self.output_dir)],
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    
                    if result.returncode == 0:
                        self.logger.info("✓ Output organized successfully")
                        # Log output
                        for line in result.stdout.strip().split('\n'):
                            if line:
                                self.logger.info(line)
                    else:
                        self.logger.warning("Output organization failed (non-critical)")
                        if result.stderr:
                            self.logger.warning(result.stderr)
                
                except Exception as e:
                    self.logger.warning(f"Output organization failed (non-critical): {e}")
                
                # Always continue (finalize is non-critical)
                continue
            
            # Determine execution mode
            run_native = self._should_run_native(stage_name)
            system = platform.system()
            use_cuda = False
            
            if run_native:
                # Native execution
                if system == 'Windows':
                    self.logger.info(f"🚀 Running natively on Windows with {self.device_type.upper()}")
                elif system == 'Darwin':
                    self.logger.info(f"🚀 Running natively on macOS with {self.device_type.upper()} acceleration")
                else:
                    self.logger.info(f"🚀 Running natively with {self.device_type.upper()}")
            else:
                # Docker execution
                if stage_name in ML_STAGES:
                    if self.device_type == 'cuda' and system == 'Linux':
                        # CUDA containers on Linux
                        use_cuda = True
                        self.logger.info(f"🐳 Running in Docker with CUDA GPU support")
                    elif self.device_type == 'cpu':
                        self.logger.info(f"🐳 Running in Docker (CPU mode)")
                    else:
                        # MPS but can't run native (fallback to Docker CPU)
                        self.logger.info(f"🐳 Running in Docker (CPU fallback - native mode unavailable)")
                else:
                    self.logger.info(f"🐳 Running in Docker container")
            
            # Run stage
            start_time = time.time()
            max_retries = 2 if stage_name == "asr" else 1  # Allow retries for ASR
            retry_count = 0
            attempted_cpu_fallback = False
            
            # ASR ALWAYS runs on CPU only (no GPU, no fallback)
            force_cpu_only = (stage_name == "asr")
            
            try:
                while retry_count < max_retries:
                    # Prepare arguments (use container paths for Docker, absolute paths for native)
                    use_container_paths = not run_native
                    args = self._get_stage_args(stage_name, input_path, file_info, use_container_paths)
                    
                    # Run stage based on execution mode
                    if retry_count > 0:
                        self.logger.info(f"Retry {retry_count}/{max_retries-1}...")
                    else:
                        self.logger.info(f"Timeout: {timeout}s")
                    
                    # Determine if we should force CPU for this attempt
                    force_cpu = False
                    if force_cpu_only:
                        # ASR always runs on CPU
                        force_cpu = True
                        if retry_count == 0:
                            self.logger.info(f"ℹ️  ASR stage configured for CPU-only execution (no GPU)")
                    elif run_native and stage_name in ML_STAGES and self.device_type in ['mps', 'cuda'] and attempted_cpu_fallback:
                        force_cpu = True
                    
                    if run_native:
                        # Run natively (Windows/macOS)
                        script_name = STAGE_SCRIPTS.get(stage_name)
                        if not script_name:
                            self.logger.error(f"No script mapping for stage: {stage_name}")
                            raise Exception(f"Unknown stage: {stage_name}")
                        
                        if force_cpu:
                            success = self.run_native_step(stage_name, script_name, args, timeout=timeout, force_device='cpu')
                        else:
                            success = self.run_native_step(stage_name, script_name, args, timeout=timeout)
                    else:
                        # Run in Docker (CUDA containers on Linux/Windows, or CPU fallback)
                        success = self.run_docker_step(service, args, timeout=timeout, use_cuda=use_cuda)
                    
                    duration = time.time() - start_time
                    
                    if not success:
                        # Check if this is an ML stage that can fallback to CPU
                        # ASR stage is excluded from CPU fallback since it always runs on CPU
                        if not force_cpu_only and stage_name in ML_STAGES and self.device_type in ['mps', 'cuda'] and not attempted_cpu_fallback:
                            self.logger.warning(f"⚠️  Stage failed on {self.device_type.upper()}")
                            self.logger.warning(f"⚠️  Attempting CPU fallback...")
                            attempted_cpu_fallback = True
                            retry_count += 1
                            if retry_count < max_retries:
                                time.sleep(5)  # Brief pause before retry
                                continue
                            else:
                                raise Exception("Stage execution failed after retries")
                        
                        # Regular retry logic (not CPU fallback)
                        retry_count += 1
                        if retry_count < max_retries:
                            self.logger.warning(f"Stage failed, retrying... ({retry_count}/{max_retries-1})")
                            time.sleep(5)  # Brief pause before retry
                            continue
                        raise Exception("Stage execution failed after retries")
                    
                    # Record success with device info
                    device_used = 'cpu' if force_cpu else self.device_type
                    self.manifest.set_pipeline_step(
                        stage_name,
                        True,
                        completed=True,
                        next_stage=next_stage,
                        status="success",
                        duration=duration,
                        device=device_used.upper() if stage_name in ML_STAGES else 'CPU'
                    )
                    
                    if attempted_cpu_fallback and force_cpu:
                        self.logger.info(f"✓ Stage completed in {duration:.1f}s (on CPU after {self.device_type.upper()} failure)")
                    else:
                        self.logger.info(f"✓ Stage completed in {duration:.1f}s{' on ' + device_used.upper() if stage_name in ML_STAGES else ''}")
                    self.logger.info(f"Progress: {idx}/{total_stages} stages complete")
                    break  # Success, exit retry loop
                
            except Exception as e:
                duration = time.time() - start_time
                error_msg = str(e)
                
                self.logger.error(f"✗ Stage failed: {error_msg}")
                self.logger.error(f"Duration before failure: {duration:.1f}s")
                
                if critical:
                    # Critical failure
                    self.manifest.set_pipeline_step(
                        stage_name,
                        False,
                        completed=True,
                        next_stage=None,
                        status="failed",
                        error=error_msg,
                        duration=duration
                    )
                    self.manifest.finalize(status="failed")
                    
                    self.logger.error("")
                    self.logger.error("="*60)
                    self.logger.error("PIPELINE FAILED - CRITICAL STAGE ERROR")
                    self.logger.error("="*60)
                    return False
                else:
                    # Optional failure - skip and continue
                    self.manifest.set_pipeline_step(
                        stage_name,
                        False,
                        completed=True,
                        next_stage=next_stage,
                        status="skipped",
                        notes=f"Failed: {error_msg}",
                        duration=duration
                    )
                    
                    self.logger.warning(f"⚠️  Optional stage failed - continuing")
        
        # Pipeline completed
        total_duration = time.time() - self.start_time.timestamp()
        
        self.logger.info("")
        self.logger.info("="*60)
        self.logger.info("✓ PIPELINE COMPLETED SUCCESSFULLY")
        self.logger.info("="*60)
        self.logger.info(f"Job ID: {self.job_id}")
        self.logger.info(f"Duration: {total_duration:.1f}s ({total_duration/60:.1f} minutes)")
        self.logger.info(f"Output: {self.output_dir}")
        self.logger.info(f"Logs: {self.log_dir}")
        self.logger.info(f"Manifest: {manifest_file}")
        
        self.manifest.finalize(status="completed")
        
        return True
    
    def _to_container_path(self, path: Path) -> str:
        """Convert a host path to a container path.
        
        Args:
            path: Path on host system
        
        Returns:
            Path inside container (relative to /app)
        """
        # Get project root (parent of scripts directory)
        project_root = PROJECT_ROOT
        
        # Convert to absolute path if needed
        abs_path = path.absolute() if not path.is_absolute() else path
        
        # Make path relative to project root
        try:
            rel_path = abs_path.relative_to(project_root)
            return f"/app/{rel_path}".replace('\\', '/')  # Ensure forward slashes for container
        except ValueError:
            # Path is outside project root, use as-is (shouldn't happen)
            return str(abs_path).replace('\\', '/')
    
    def _get_stage_args(self, stage_name: str, input_path: Path, file_info: dict, use_container_paths: bool = True) -> List[str]:
        """Get arguments for a stage.
        
        Args:
            stage_name: Stage name
            input_path: Input media path
            file_info: Parsed filename info
            use_container_paths: Whether to convert to container paths (True for Docker, False for native)
        
        Returns:
            List of arguments for the stage
        """
        if use_container_paths:
            output_dir_path = self._to_container_path(self.output_dir)
        else:
            output_dir_path = str(self.output_dir.absolute())
        
        if stage_name == "demux":
            if use_container_paths:
                input_container = self._to_container_path(input_path)
            else:
                input_container = str(input_path.absolute())
            return [input_container, output_dir_path]
        elif stage_name == "tmdb":
            args = [output_dir_path, file_info.get('title', input_path.stem)]
            if file_info.get('year'):
                args.append(str(file_info['year']))
            return args
        elif stage_name in ["silero_vad", "pyannote_vad"]:
            # VAD stages expect: audio_file --out-json output.json --device cpu/mps/cuda
            if use_container_paths:
                audio_file = f"{output_dir_path}/audio.wav"
                output_json = f"{output_dir_path}/vad_segments.json"
            else:
                audio_file = str(Path(output_dir_path) / "audio.wav")
                output_json = str(Path(output_dir_path) / "vad_segments.json")
            
            # Get device setting - pass through MPS for PyAnnote VAD
            device = getattr(self.config, 'device', 'cpu').lower()
            
            return [audio_file, "--out-json", output_json, "--device", device]
        elif stage_name == "glossary_builder":
            # Build glossary from ASR and metadata
            args = ["--job-dir", output_dir_path]
            
            title = file_info.get('title', input_path.stem)
            args.extend(["--title", title])
            
            if file_info.get('year'):
                args.extend(["--year", str(file_info['year'])])
            
            # Add TMDB ID if available from tmdb stage
            tmdb_file = self.output_dir / "02_tmdb" / "metadata.json"
            if not tmdb_file.exists():
                tmdb_file = self.output_dir / "tmdb" / "metadata.json"
            
            if tmdb_file.exists():
                try:
                    import json
                    with open(tmdb_file, 'r', encoding='utf-8', errors='replace') as f:
                        tmdb_data = json.load(f)
                    if 'id' in tmdb_data:
                        args.extend(["--tmdb-id", str(tmdb_data['id'])])
                except Exception:
                    pass
            
            # Master glossary and prompts paths
            if use_container_paths:
                args.extend(["--master", "/app/glossary/hinglish_master.tsv"])
                args.extend(["--prompts", "/app/prompts"])
            else:
                args.extend(["--master", "glossary/hinglish_master.tsv"])
                args.extend(["--prompts", "prompts"])
            
            # Add min confidence if configured
            min_conf = getattr(self.config, 'glossary_min_conf', 0.55)
            args.extend(["--min-confidence", str(min_conf)])
            
            return args
        elif stage_name == "mux":
            if use_container_paths:
                input_container = self._to_container_path(input_path)
            else:
                input_container = str(input_path.absolute())
            output_file = f"{output_dir_path}/final_output.mp4"
            
            # Find subtitle file - subtitle-gen creates it at en_merged/{job_id}.merged.srt
            output_dir = Path(output_dir_path)
            job_id = output_dir.name
            subtitle_file = output_dir / "en_merged" / f"{job_id}.merged.srt"
            
            # Fallback to old location if new location doesn't exist
            if not subtitle_file.exists():
                subtitle_file = output_dir / "subtitles" / "subtitles.srt"
            
            subtitle_file = str(subtitle_file)
            return [input_container, subtitle_file, output_file]
        else:
            return [output_dir_path]


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="CP-WhisperX-App Pipeline Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run pipeline for a job
  python pipeline.py --job 20251101-0001
  
  # Run specific stages
  python pipeline.py --job 20251101-0001 --stages asr subtitle_gen
  
  # Start fresh (no resume)
  python pipeline.py --job 20251101-0001 --no-resume
  
  # List available stages
  python pipeline.py --list-stages
        """
    )
    
    parser.add_argument(
        "--job",
        help="Job ID to process (e.g., 20251101-0001)"
    )
    
    parser.add_argument(
        "--stages",
        nargs="+",
        help="Specific stages to run",
        choices=["demux", "tmdb", "pre_ner", "silero_vad", "pyannote_vad",
                 "diarization", "asr", "glossary_builder", "second_pass_translation", 
                 "lyrics_detection", "post_ner", "subtitle_gen", "mux", "finalize"]
    )
    
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Start from scratch (ignore previous progress)"
    )
    
    parser.add_argument(
        "--list-stages",
        action="store_true",
        help="List all available stages and exit"
    )
    
    args = parser.parse_args()
    
    # List stages
    if args.list_stages:
        print("\nAvailable pipeline stages:")
        print("=" * 80)
        for idx, (name, next_stage, service, timeout, critical, uses_ml) in enumerate(STAGE_DEFINITIONS, 1):
            critical_str = "CRITICAL" if critical else "optional"
            ml_str = " [ML]" if uses_ml else ""
            print(f"{idx:2}. {name:15} → {service:15} (timeout: {timeout:4}s) [{critical_str}]{ml_str}")
        print("=" * 80)
        print("\nStage sequence:")
        print(" → ".join([s[0] for s in STAGE_DEFINITIONS]))
        print("\nML stages (can use MPS/CUDA acceleration):")
        print(" → ".join([s[0] for s in STAGE_DEFINITIONS if s[5]]))
        print()
        return 0
    
    # Validate job ID
    if not args.job:
        parser.error("--job is required")
    
    try:
        # Run pipeline
        orchestrator = JobOrchestrator(args.job, stages=args.stages)
        success = orchestrator.run_pipeline(resume=not args.no_resume)
        
        sys.exit(0 if success else 1)
        
    except ValueError as e:
        print(f"\n✗ Error: {e}")
        print("\nMake sure you've prepared the job first:")
        print(f"  python prepare-job.py /path/to/media.mp4")
        print()
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
