"""
manifest.py - Pipeline manifest tracking for all stages

Each stage in the pipeline creates/updates a manifest.json that tracks:
- Stage execution status (success, failure, skipped)
- Output files with full paths
- Timing information
- Error details if any
- Device information

This enables:
- Resume capability after failures
- Audit trail of pipeline execution
- Easy debugging and monitoring
"""

# Standard library
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from contextlib import contextmanager
import logging

# Local
from shared.logger import get_logger
logger = get_logger(__name__)


class PathEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle Path objects."""
    def default(self, obj):
        if isinstance(obj, Path):
            return str(obj)
        return super().default(obj)


class StageManifest:
    """
    Manifest manager for individual pipeline stages.
    
    Each stage should use this to record its execution status,
    output files, and gracefully handle exits.
    
    Example:
        with StageManifest("demux", movie_dir) as manifest:
            # Do stage work
            manifest.add_output("audio", audio_dir / "audio.wav")
            manifest.add_output("metadata", audio_dir / "metadata.json")
            # Automatic success on exit
    """
    
    def __init__(self, stage_name: str, movie_dir: Path, logger: Optional[logging.Logger] = None, job_id: Optional[str] = None, user_id: Optional[int] = None, job_env_file: Optional[Path] = None) -> None:
        """
        Initialize stage manifest.
        
        Args:
            stage_name: Name of the stage (e.g., "demux", "asr")
            movie_dir: Movie output directory
            logger: Optional logger instance
            job_id: Job ID for this pipeline run
            user_id: User ID for this pipeline run
            job_env_file: Path to job-specific environment file
        """
        self.stage_name = stage_name
        self.movie_dir = Path(movie_dir)
        self.manifest_file = self.movie_dir / "manifest.json"
        self.logger = logger
        self.job_id = job_id
        self.user_id = user_id
        self.job_env_file = str(job_env_file) if job_env_file else None
        self.start_time = datetime.now()
        self.outputs = {}
        self.metadata = {}
        self.input_files = []
        self.error = None
        self.status = "running"
        
        # Load existing manifest or create new
        self.data = self._load_or_create()
    
    def _load_or_create(self) -> Dict[str, Any]:
        """Load existing manifest or create new structure."""
        if self.manifest_file.exists():
            with open(self.manifest_file, 'r') as f:
                data = json.load(f)
        else:
            data = {
                "version": "1.0.0",
                "created_at": datetime.now().isoformat(),
                "job_id": self.job_id,
                "user_id": self.user_id,
                "job_env_file": self.job_env_file,
                "movie_dir": str(self.movie_dir),
                "stages": {},
                "pipeline": {
                    "status": "running",
                    "current_stage": None,
                    "completed_stages": [],
                    "failed_stages": []
                }
            }
        
        # Update job info if provided
        if self.job_id:
            data["job_id"] = self.job_id
        if self.user_id:
            data["user_id"] = self.user_id
        if self.job_env_file:
            data["job_env_file"] = self.job_env_file
        
        # Ensure stages dict exists and convert from array if needed
        if "stages" not in data:
            data["stages"] = {}
        elif isinstance(data["stages"], list):
            # Convert array format to dict format for compatibility
            stages_dict = {}
            for stage in data["stages"]:
                if isinstance(stage, dict) and "name" in stage:
                    stages_dict[stage["name"]] = stage
            data["stages"] = stages_dict
        
        # Ensure pipeline structure exists
        if "pipeline" not in data:
            data["pipeline"] = {
                "status": "running",
                "current_stage": None,
                "completed_stages": [],
                "failed_stages": []
            }
        
        return data
    
    def add_output(self, key: str, filepath: Path, description: Optional[str] = None) -> None:
        """
        Add an output file to the manifest.
        
        Args:
            key: Output identifier (e.g., "audio", "transcript", "subtitles")
            filepath: Full path to output file
            description: Optional description of the output
        """
        self.outputs[key] = {
            "path": str(filepath.resolve()),
            "exists": filepath.exists(),
            "size_bytes": filepath.stat().st_size if filepath.exists() else 0,
            "description": description
        }
        
        if self.logger:
            self.logger.debug(f"Recorded output: {key} -> {filepath}")
    
    def add_input(self, key: str, filepath: Path, description: Optional[str] = None) -> None:
        """
        Add an input file to the manifest.
        
        Args:
            key: Input identifier
            filepath: Full path to input file
            description: Optional description of the input
        """
        self.input_files.append({
            "key": key,
            "path": str(filepath.resolve()),
            "exists": filepath.exists(),
            "size_bytes": filepath.stat().st_size if filepath.exists() else 0,
            "description": description
        })
        
        if self.logger:
            self.logger.debug(f"Recorded input: {key} -> {filepath}")
    
    def add_metadata(self, key: str, value: Any) -> None:
        """Add stage-specific metadata."""
        self.metadata[key] = value
    
    def add_intermediate(self, file_path: Path, retained: bool = False, reason: str = "") -> None:
        """
        Track intermediate/cache file in manifest.
        
        Args:
            file_path: Path to intermediate file
            retained: Whether file is kept after stage completion
            reason: Explanation for why file was created/retained
        """
        if not hasattr(self, 'intermediate_files'):
            self.intermediate_files = []
        
        self.intermediate_files.append({
            "path": str(file_path.resolve()),
            "exists": file_path.exists(),
            "size_bytes": file_path.stat().st_size if file_path.exists() else 0,
            "retained": retained,
            "reason": reason
        })
        
        if self.logger:
            status = "retained" if retained else "temporary"
            self.logger.debug(f"Recorded intermediate file ({status}): {file_path}")
    
    def set_config(self, config_dict: Dict[str, Any]) -> None:
        """
        Store stage configuration in metadata.
        
        Args:
            config_dict: Dictionary of configuration key-value pairs
        """
        for key, value in config_dict.items():
            self.add_metadata(f"config_{key}", value)
    
    def set_error(self, error: str) -> None:
        """Record an error for this stage."""
        self.error = error
        self.status = "failed"
        if self.logger:
            self.logger.error(f"Stage error recorded: {error}")
    
    def add_error(self, message: str, exception: Optional[Exception] = None) -> None:
        """
        Add error message to manifest.
        
        Args:
            message: Error message
            exception: Optional exception object
        """
        if exception:
            self.set_error(f"{message}: {str(exception)}")
        else:
            self.set_error(message)
    
    def add_warning(self, message: str) -> None:
        """
        Add warning message to manifest metadata.
        
        Args:
            message: Warning message
        """
        if not hasattr(self, 'warnings'):
            self.warnings = []
        self.warnings.append({
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        if self.logger:
            self.logger.warning(message)
    
    def finalize(self, status: str = "success", **kwargs: Any) -> None:
        """
        Finalize stage and save manifest.
        
        Args:
            status: Final status (success, failed, skipped)
            **kwargs: Additional metadata to store
        """
        # Add any additional metadata
        for key, value in kwargs.items():
            self.add_metadata(key, value)
        
        # Save with final status
        self.save(status)
    
    def save(self, status: Optional[str] = None) -> None:
        """
        Save manifest to disk.
        
        Args:
            status: Override status (success, failed, skipped)
        """
        if status:
            self.status = status
        
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        # Get stage number from stage name mapping
        stage_numbers = {
            "demux": 1, "tmdb": 2, "pre_ner": 3, "silero_vad": 4,
            "pyannote_vad": 5, "diarization": 6, "asr": 7,
            "post_ner": 8, "subtitle_gen": 9, "mux": 10
        }
        
        # Record stage data
        stage_data = {
            "job_id": self.job_id,
            "user_id": self.user_id,
            "stage_number": stage_numbers.get(self.stage_name, 0),
            "stage_name": self.stage_name,
            "job_env_file": self.job_env_file,
            "status": self.status,
            "started_at": self.start_time.isoformat(),
            "completed_at": end_time.isoformat(),
            "duration_seconds": duration,
            "input_files": self.input_files,
            "outputs": self.outputs,
            "metadata": self.metadata
        }
        
        if self.error:
            stage_data["error"] = self.error
        
        if hasattr(self, 'warnings') and self.warnings:
            stage_data["warnings"] = self.warnings
        
        # Update manifest
        self.data["stages"][self.stage_name] = stage_data
        self.data["pipeline"]["current_stage"] = None
        
        # Update pipeline status
        if self.status == "success":
            if self.stage_name not in self.data["pipeline"]["completed_stages"]:
                self.data["pipeline"]["completed_stages"].append(self.stage_name)
        elif self.status == "failed":
            if self.stage_name not in self.data["pipeline"]["failed_stages"]:
                self.data["pipeline"]["failed_stages"].append(self.stage_name)
        
        # Update overall pipeline status
        if self.data["pipeline"]["failed_stages"]:
            self.data["pipeline"]["status"] = "failed"
        elif len(self.data["pipeline"]["completed_stages"]) == 10:  # All stages
            self.data["pipeline"]["status"] = "completed"
        
        self.data["updated_at"] = datetime.now().isoformat()
        
        # Write to disk
        self.manifest_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.manifest_file, 'w') as f:
            json.dump(self.data, f, indent=2, cls=PathEncoder)
        
        if self.logger:
            self.logger.info(f"Manifest updated: {self.manifest_file}")
    
    def __enter__(self) -> 'StageManifest':
        """Context manager entry - mark stage as running."""
        self.data["pipeline"]["current_stage"] = self.stage_name
        self.save(status="running")
        return self
    
    def __exit__(self, exc_type: Optional[type], exc_val: Optional[BaseException], exc_tb: Optional[Any]) -> bool:
        """Context manager exit - save final status."""
        if exc_type is None:
            # No exception - success
            self.save(status="success")
            if self.logger:
                self.logger.info(f"✓ Stage {self.stage_name} completed successfully")
            return True
        else:
            # Exception occurred - failure
            error_msg = f"{exc_type.__name__}: {exc_val}"
            self.set_error(error_msg)
            self.save(status="failed")
            if self.logger:
                self.logger.error(f"✗ Stage {self.stage_name} failed: {error_msg}")
            return False  # Re-raise exception


class PipelineManifest:
    """
    Full pipeline manifest tracking (for orchestrator use).
    
    This is used by pipeline.py to track the overall pipeline execution.
    Individual stages should use StageManifest instead.
    """
    
    def __init__(self, manifest_file: Path, job_id: str = None, user_id: int = None, job_env_file: Path = None):
        """Initialize pipeline manifest."""
        self.manifest_file = manifest_file
        self.start_time = datetime.now()
        self.job_id = job_id
        self.user_id = user_id
        self.job_env_file = str(job_env_file) if job_env_file else None
        self.data = self._load_or_create()
    
    def _load_or_create(self) -> Dict[str, Any]:
        """Load existing manifest or create new."""
        if self.manifest_file.exists():
            with open(self.manifest_file, 'r') as f:
                return json.load(f)
        else:
            return {
                "version": "1.0.0",
                "created_at": self.start_time.isoformat(),
                "job_id": self.job_id,
                "user_id": self.user_id,
                "job_env_file": self.job_env_file,
                "input": {},
                "stages": {},
                "pipeline": {
                    "status": "running",
                    "current_stage": None,
                    "completed_stages": [],
                    "failed_stages": []
                },
                "timing": {
                    "started_at": self.start_time.isoformat()
                }
            }
    
    def set_input(self, input_file: str, title: str, year: Optional[int], job_id: Optional[str] = None) -> None:
        """Set input file information."""
        self.data["input"] = {
            "file": input_file,
            "title": title,
            "year": year
        }
        if job_id:
            self.data["job_id"] = job_id
        self.save()
    
    def set_output_dir(self, output_dir: str) -> None:
        """Set output directory."""
        self.data["output_dir"] = output_dir
        self.save()
    
    def set_pipeline_step(self, stage_name: str, success: bool, **kwargs: Any) -> None:
        """Record a pipeline step."""
        if stage_name not in self.data["stages"]:
            self.data["stages"][stage_name] = {}
        
        self.data["stages"][stage_name].update(kwargs)
        self.data["stages"][stage_name]["success"] = success
        
        if success and kwargs.get("completed", False):
            if stage_name not in self.data["pipeline"]["completed_stages"]:
                self.data["pipeline"]["completed_stages"].append(stage_name)
        elif not success:
            if stage_name not in self.data["pipeline"]["failed_stages"]:
                self.data["pipeline"]["failed_stages"].append(stage_name)
        
        self.save()
    
    def is_stage_completed(self, stage_name: str) -> bool:
        """Check if a stage is already completed."""
        return stage_name in self.data["pipeline"].get("completed_stages", [])
    
    def get_stage_status(self, stage_name: str) -> Optional[str]:
        """Get status of a specific stage."""
        stages = self.data.get("stages", {})
        if stage_name in stages:
            return stages[stage_name].get("status")
        return None
    
    def finalize(self, status: str = "completed") -> None:
        """Finalize pipeline execution."""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        self.data["pipeline"]["status"] = status
        self.data["pipeline"]["current_stage"] = None
        self.data["timing"]["completed_at"] = end_time.isoformat()
        self.data["timing"]["total_seconds"] = duration
        
        self.save()
    
    def save(self) -> None:
        """Save manifest to disk."""
        self.manifest_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.manifest_file, 'w') as f:
            json.dump(self.data, f, indent=2)


# Alias for compatibility with existing code
ManifestBuilder = PipelineManifest


def get_manifest_file(movie_dir: Path) -> Path:
    """Get manifest file path for a movie directory."""
    return Path(movie_dir) / "manifest.json"


def load_manifest(movie_dir: Path) -> Optional[Dict]:
    """Load existing manifest if it exists."""
    manifest_file = get_manifest_file(movie_dir)
    if manifest_file.exists():
        with open(manifest_file, 'r') as f:
            return json.load(f)
    return None


def is_stage_completed(movie_dir: Path, stage_name: str) -> bool:
    """Check if a stage is completed in the manifest."""
    manifest = load_manifest(movie_dir)
    if manifest:
        return stage_name in manifest.get("pipeline", {}).get("completed_stages", [])
    return False
