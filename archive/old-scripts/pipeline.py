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
    ("asr", "song_bias_injection", "asr", 14400, True, True),  # ML: PyTorch (Whisper) - Stage 6: Character name bias
    ("song_bias_injection", "lyrics_detection", "song-bias-injection", 600, False, False),  # Stage 7: Song-specific bias
    ("lyrics_detection", "bias_correction", "lyrics-detection", 1800, False, True),  # Stage 8: ML: Audio analysis
    ("bias_correction", "diarization", "bias-correction", 600, False, False),  # Stage 9: Post-processing corrections
    ("diarization", "glossary_builder", "diarization", 7200, True, True),  # ML: PyTorch
    ("glossary_builder", "second_pass_translation", "glossary-builder", 300, False, False),
    ("second_pass_translation", "post_ner", "second-pass-translation", 7200, False, True),  # ML: Translation models
    ("post_ner", "subtitle_gen", "post-ner", 1200, False, False),
    ("subtitle_gen", "mux", "subtitle-gen", 600, True, False),
    ("mux", None, "mux", 600, True, False),
]

# ML stages that can run natively with MPS/CUDA
# Maps stage_name -> script filename in scripts/ directory
ML_STAGES = {
    "silero_vad": "silero_vad.py",
    "pyannote_vad": "pyannote_vad.py",
    "diarization": "diarization.py",
    "asr": "whisperx_asr.py",
    "lyrics_detection": "lyrics_detection.py",
    "second_pass_translation": "second_pass_translation.py"
}

# All stage scripts (for native execution)
# Maps stage_name -> script filename in scripts/ directory
STAGE_SCRIPTS = {
    "demux": "demux.py",
    "tmdb": "tmdb.py",
    "pre_ner": "pre_ner.py",
    "silero_vad": "silero_vad.py",
    "pyannote_vad": "pyannote_vad.py",
    "asr": "whisperx_asr.py",
    "song_bias_injection": "song_bias_injection.py",  # NEW: Stage 7 - Song-specific bias
    "lyrics_detection": "lyrics_detection.py",  # REFACTORED: Stage 8 - Proper lyrics detection
    "bias_correction": "bias_injection.py",  # RENAMED: Stage 9 - Post-processing correction
    "diarization": "diarization.py",
    "glossary_builder": "glossary_builder.py",
    "second_pass_translation": "second_pass_translation.py",
    "post_ner": "post_ner.py",
    "subtitle_gen": "subtitle_gen.py",
    "mux": "mux.py",
    "create_clip": "create_clip.py"  # NEW: Create video clip with embedded subtitles
}


def get_stages_for_workflow(workflow_mode: str, config: 'Config') -> List[tuple]:
    """Get stage definitions for a specific workflow mode.
    
    Args:
        workflow_mode: Workflow mode (transcribe, transcribe-only, translate-only, subtitle-gen)
        config: Configuration object
    
    Returns:
        List of stage tuples (stage_name, next_stage, service_name, timeout, critical, uses_ml_model)
    """
    if workflow_mode == 'transcribe':
        # Minimal transcribe workflow: demux → [silero_vad] → [pyannote_vad] → asr → create_clip (3-5 stages)
        # Check stage flags to determine which VAD stages to include
        silero_enabled = getattr(config, 'step_vad_silero', True)
        pyannote_enabled = getattr(config, 'step_vad_pyannote', False)
        
        stages = []
        
        # Always start with demux
        if silero_enabled and pyannote_enabled:
            # Both VAD stages enabled: demux → silero → pyannote → asr → create_clip
            stages = [
                ("demux", "silero_vad", "demux", 600, True, False),
                ("silero_vad", "pyannote_vad", "silero-vad", 1800, True, True),
                ("pyannote_vad", "asr", "pyannote-vad", 3600, True, True),
                ("asr", "create_clip", "asr", 14400, True, True),
                ("create_clip", None, "create-clip", 1200, False, False),
            ]
        elif silero_enabled:
            # Only Silero VAD: demux → silero → asr → create_clip
            stages = [
                ("demux", "silero_vad", "demux", 600, True, False),
                ("silero_vad", "asr", "silero-vad", 1800, True, True),
                ("asr", "create_clip", "asr", 14400, True, True),
                ("create_clip", None, "create-clip", 1200, False, False),
            ]
        elif pyannote_enabled:
            # Only PyAnnote VAD: demux → pyannote → asr → create_clip
            stages = [
                ("demux", "pyannote_vad", "demux", 600, True, False),
                ("pyannote_vad", "asr", "pyannote-vad", 3600, True, True),
                ("asr", "create_clip", "asr", 14400, True, True),
                ("create_clip", None, "create-clip", 1200, False, False),
            ]
        else:
            # No VAD: demux → asr → create_clip
            stages = [
                ("demux", "asr", "demux", 600, True, False),
                ("asr", "create_clip", "asr", 14400, True, True),
                ("create_clip", None, "create-clip", 1200, False, False),
            ]
        
        return stages
    
    elif workflow_mode == 'transcribe-only':
        # Transcription-only workflow: 6 stages with VAD, outputs segments.json
        # Stages: demux → tmdb → pre_ner → silero_vad → pyannote_vad → asr
        return [
            ("demux", "tmdb", "demux", 600, True, False),
            ("tmdb", "pre_ner", "tmdb", 120, False, False),
            ("pre_ner", "silero_vad", "pre-ner", 300, False, False),
            ("silero_vad", "pyannote_vad", "silero-vad", 1800, True, True),
            ("pyannote_vad", "asr", "pyannote-vad", 3600, True, True),
            ("asr", None, "asr", 14400, True, True),
        ]
    
    elif workflow_mode == 'translate-only':
        # Translation-only workflow: 9 stages, skips audio processing
        # Stages: tmdb → song_bias → lyrics → bias_correction → diarization → glossary → second_pass → post_ner → subtitle_gen → mux
        # Note: Reuses existing segments.json from previous transcription
        return [
            ("tmdb", "song_bias_injection", "tmdb", 120, False, False),
            ("song_bias_injection", "lyrics_detection", "song-bias-injection", 600, False, False),
            ("lyrics_detection", "bias_correction", "lyrics-detection", 1800, False, True),
            ("bias_correction", "diarization", "bias-correction", 600, False, False),
            ("diarization", "glossary_builder", "diarization", 7200, True, True),
            ("glossary_builder", "second_pass_translation", "glossary-builder", 300, False, False),
            ("second_pass_translation", "post_ner", "second-pass-translation", 7200, False, True),
            ("post_ner", "subtitle_gen", "post-ner", 1200, False, False),
            ("subtitle_gen", "mux", "subtitle-gen", 600, True, False),
            ("mux", None, "mux", 600, True, False),
        ]
    
    else:
        # Full subtitle-gen workflow (15 stages, default)
        return STAGE_DEFINITIONS.copy()


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
            # Get stages based on workflow mode
            workflow_mode = getattr(self.config, 'workflow_mode', 'subtitle-gen')
            self.stages = get_stages_for_workflow(workflow_mode, self.config)
            
            # Validate prerequisites for translate-only workflow
            if workflow_mode == 'translate-only':
                # Check if segments.json exists from previous transcription
                output_dir = self._get_output_dir()
                segments_file = output_dir / "06_asr" / "segments.json"
                if not segments_file.exists():
                    raise ValueError(
                        f"translate-only mode requires existing transcription.\n"
                        f"Missing: {segments_file}\n"
                        f"\n"
                        f"Please run --transcribe-only first:\n"
                        f"  python prepare-job.py <input> --transcribe-only --source-language {getattr(self.config, 'source_language', 'auto')}"
                    )
                self.logger.info(f"✓ Found existing transcription: {segments_file}")
                self.logger.info(f"  Reusing segments.json from previous transcription")
            
            # Apply stage control flags for subtitle-gen workflow
            if workflow_mode == 'subtitle-gen':
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
            
            # Store workflow info for logging later (after logger is initialized)
            self.workflow_mode = workflow_mode
            self.source_lang = getattr(self.config, 'source_language', None)
            self.target_lang = getattr(self.config, 'target_language', None)
        
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
        
        # Log workflow information (now that logger is initialized)
        if hasattr(self, 'workflow_mode'):
            self.logger.info(f"Workflow mode: {self.workflow_mode.upper()}")
            if hasattr(self, 'source_lang') and self.source_lang:
                self.logger.info(f"Source language: {self.source_lang}")
            if hasattr(self, 'target_lang') and self.target_lang:
                self.logger.info(f"Target language: {self.target_lang}")
        
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
                    self.logger.error("✗ Native mode unavailable")
                    self.logger.error("  Please run bootstrap: ./scripts/bootstrap.sh")
                    return False
            elif system == 'Windows':
                if native_available:
                    if self.device_type == 'cuda':
                        self.logger.info("✓ Execution mode: Native CUDA (Windows)")
                        self.logger.info(f"  All stages will run with NVIDIA GPU acceleration")
                    else:
                        self.logger.info("✓ Execution mode: Native CPU (Windows)")
                        self.logger.info(f"  All stages will run on CPU")
                else:
                    self.logger.error("✗ Native mode unavailable")
                    self.logger.error("  Please run bootstrap: .\\scripts\\bootstrap.ps1")
                    return False
            elif system == 'Linux':
                if native_available:
                    if self.device_type == 'cuda':
                        self.logger.info("✓ Execution mode: Native CUDA (Linux)")
                        self.logger.info(f"  ML stages will run with CUDA GPU acceleration")
                    else:
                        self.logger.info("✓ Execution mode: Native CPU (Linux)")
                        self.logger.info(f"  All stages will run on CPU")
                else:
                    self.logger.error("✗ Native mode unavailable")
                    self.logger.error("  Please run bootstrap: ./scripts/bootstrap.sh")
                    return False
            
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
            # Log actual stages being run (respects VAD flags)
            stage_names = [s[0] for s in self.stages]
            stage_flow = ' → '.join(stage_names)
            self.logger.info(f"Transcribe workflow: {stage_flow} → transcript.txt")
        
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
        """Check if native execution environment is available.
        
        All stages run natively with the .bollyenv virtual environment.
        Docker mode has been removed.
        
        Args:
            stage_name: Stage name
        
        Returns:
            True if native venv is available, False otherwise
        """
        return self._check_native_venv_available(stage_name)
    
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
        """Run a pipeline stage natively.
        
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
        
        # Log device info for ML stages (no CPU fallback)
        if stage_name in ML_STAGES:
            if force_device:
                self.logger.info(f"Running {stage_name} on {device_for_run.upper()} (forced)")
            else:
                self.logger.info(f"Running {stage_name} on {device_for_run.upper()} with tuned parameters from job environment")
        
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
            if stage_name == "name_correction":
                # Auto-enable for MPS+MLX, optional for others
                name_correction_enabled = getattr(self.config, 'name_correction_enabled', True)
                whisper_backend = getattr(self.config, 'whisper_backend', 'whisperx')
                gpu_type = getattr(self.config, 'device', 'cpu').lower()
                
                # Skip if disabled in config
                if not name_correction_enabled:
                    self.logger.info(f"⏭️  Skipping - disabled in config (NAME_CORRECTION_ENABLED=false)")
                    continue
                
                # Skip if not using MLX (other backends have bias support)
                if whisper_backend != 'mlx':
                    self.logger.info(f"⏭️  Skipping - not needed (backend={whisper_backend} has bias support)")
                    continue
                
                self.logger.info(f"✓ Enabled for {whisper_backend} backend (compensates for lack of bias)")
            
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
            
            # Check if native execution is available
            run_native = self._should_run_native(stage_name)
            
            if not run_native:
                self.logger.error(f"Native environment not available for {stage_name}")
                self.logger.error(f"Please run ./scripts/bootstrap.sh to set up the environment")
                self.manifest.set_pipeline_step(stage_name, False, error="Native environment not available")
                if critical:
                    return False
                continue
            
            # Native execution
            system = platform.system()
            if system == 'Windows':
                self.logger.info(f"🚀 Running natively on Windows with {self.device_type.upper()}")
            elif system == 'Darwin':
                self.logger.info(f"🚀 Running natively on macOS with {self.device_type.upper()} acceleration")
            else:
                self.logger.info(f"🚀 Running natively with {self.device_type.upper()}")
            
            # Run stage
            start_time = time.time()
            max_retries = 2 if stage_name in ML_STAGES else 1  # Allow retries for ML stages
            retry_count = 0
            
            # ML stages run ONLY on configured device (no CPU fallback)
            # Device and parameters are tuned in job environment file
            if stage_name in ML_STAGES and retry_count == 0:
                self.logger.info(f"ℹ️  ML stage configured for {self.device_type.upper()}-only execution with tuned parameters")
                self.logger.info(f"   No CPU fallback - device settings from job environment file")
            
            try:
                while retry_count < max_retries:
                    # Prepare arguments with absolute paths (native execution)
                    args = self._get_stage_args(stage_name, input_path, file_info, use_container_paths=False)
                    
                    # Run stage based on execution mode
                    if retry_count > 0:
                        self.logger.info(f"Retry {retry_count}/{max_retries-1}...")
                    else:
                        self.logger.info(f"Timeout: {timeout}s")
                    
                    # Run natively - always use configured device (no CPU fallback)
                    script_name = STAGE_SCRIPTS.get(stage_name)
                    if not script_name:
                        self.logger.error(f"No script mapping for stage: {stage_name}")
                        raise Exception(f"Unknown stage: {stage_name}")
                    
                    success = self.run_native_step(stage_name, script_name, args, timeout=timeout)
                    
                    duration = time.time() - start_time
                    
                    if not success:
                        # Retry logic for ML stages (same device, no CPU fallback)
                        retry_count += 1
                        if retry_count < max_retries:
                            self.logger.warning(f"Stage failed, retrying on same device... ({retry_count}/{max_retries-1})")
                            time.sleep(5)  # Brief pause before retry
                            continue
                        raise Exception("Stage execution failed after retries")
                    
                    # Record success with device info
                    device_used = self.device_type if stage_name in ML_STAGES else 'cpu'
                    self.manifest.set_pipeline_step(
                        stage_name,
                        True,
                        completed=True,
                        next_stage=next_stage,
                        status="success",
                        duration=duration,
                        device=device_used.upper() if stage_name in ML_STAGES else 'CPU'
                    )
                    
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
            use_container_paths: Whether to convert to container paths (False for native)
        
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
        elif stage_name == "name_correction":
            # Name entity correction (Stage 7B)
            args = ["--job-dir", output_dir_path]
            
            # Add threshold parameters
            fuzzy_threshold = getattr(self.config, 'name_correction_fuzzy_threshold', 0.85)
            phonetic_threshold = getattr(self.config, 'name_correction_phonetic_threshold', 0.90)
            
            args.extend(["--fuzzy-threshold", str(fuzzy_threshold)])
            args.extend(["--phonetic-threshold", str(phonetic_threshold)])
            
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
                 "lyrics_detection", "post_ner", "subtitle_gen", "mux"]
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
