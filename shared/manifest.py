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

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from contextlib import contextmanager


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
    
    def __init__(self, stage_name: str, movie_dir: Path, logger=None):
        """
        Initialize stage manifest.
        
        Args:
            stage_name: Name of the stage (e.g., "demux", "asr")
            movie_dir: Movie output directory
            logger: Optional logger instance
        """
        self.stage_name = stage_name
        self.movie_dir = Path(movie_dir)
        self.manifest_file = self.movie_dir / "manifest.json"
        self.logger = logger
        self.start_time = datetime.now()
        self.outputs = {}
        self.metadata = {}
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
                "movie_dir": str(self.movie_dir),
                "stages": {},
                "pipeline": {
                    "status": "running",
                    "current_stage": None,
                    "completed_stages": [],
                    "failed_stages": []
                }
            }
        
        # Ensure stages dict exists
        if "stages" not in data:
            data["stages"] = {}
        
        return data
    
    def add_output(self, key: str, filepath: Path, description: str = None):
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
    
    def add_metadata(self, key: str, value: Any):
        """Add stage-specific metadata."""
        self.metadata[key] = value
    
    def set_error(self, error: str):
        """Record an error for this stage."""
        self.error = error
        self.status = "failed"
        if self.logger:
            self.logger.error(f"Stage error recorded: {error}")
    
    def save(self, status: str = None):
        """
        Save manifest to disk.
        
        Args:
            status: Override status (success, failed, skipped)
        """
        if status:
            self.status = status
        
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        # Record stage data
        stage_data = {
            "status": self.status,
            "started_at": self.start_time.isoformat(),
            "completed_at": end_time.isoformat(),
            "duration_seconds": duration,
            "outputs": self.outputs,
            "metadata": self.metadata
        }
        
        if self.error:
            stage_data["error"] = self.error
        
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
            json.dump(self.data, f, indent=2)
        
        if self.logger:
            self.logger.info(f"Manifest updated: {self.manifest_file}")
    
    def __enter__(self):
        """Context manager entry - mark stage as running."""
        self.data["pipeline"]["current_stage"] = self.stage_name
        self.save(status="running")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
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
    
    def __init__(self, manifest_file: Path):
        """Initialize pipeline manifest."""
        self.manifest_file = manifest_file
        self.start_time = datetime.now()
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
    
    def set_input(self, input_file: str, title: str, year: Optional[int]):
        """Set input file information."""
        self.data["input"] = {
            "file": input_file,
            "title": title,
            "year": year
        }
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
    
    def finalize(self, status: str = "completed"):
        """Finalize pipeline execution."""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        self.data["pipeline"]["status"] = status
        self.data["pipeline"]["current_stage"] = None
        self.data["timing"]["completed_at"] = end_time.isoformat()
        self.data["timing"]["total_seconds"] = duration
        
        self.save()
    
    def save(self):
        """Save manifest to disk."""
        self.manifest_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.manifest_file, 'w') as f:
            json.dump(self.data, f, indent=2)


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
