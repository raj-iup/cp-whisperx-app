"""
manifest.py - Create manifest.json for pipeline runs

Summarizes inputs, devices, outputs, TMDB hits, and durations.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


class ManifestBuilder:
    """Builder for manifest.json"""

    def __init__(self, manifest_file: Optional[Path] = None):
        self.manifest_file = manifest_file
        self.data: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "version": "0.1.0",
            "input": {},
            "output": {},
            "pipeline": {
                "current_stage": None,
                "next_stage": None,
                "completed_stages": [],
                "skipped_stages": [],
                "status": "running"
            },
            "devices": {},
            "timing": {}
        }
        self.start_time = datetime.now()
        
        # Load existing manifest if provided
        if manifest_file and manifest_file.exists():
            self.load(manifest_file)

    def set_input(self, input_file: str, title: str, year: Optional[int], duration: Optional[float]):
        """Set input file information"""
        self.data["input"] = {
            "file": input_file,
            "title": title,
            "year": year,
            "duration_seconds": duration
        }

    def set_output_dir(self, output_dir: str):
        """Set output directory"""
        self.data["output"]["directory"] = output_dir

    def add_output_file(self, key: str, filepath: str):
        """Add an output file to manifest"""
        if "files" not in self.data["output"]:
            self.data["output"]["files"] = {}
        self.data["output"]["files"][key] = filepath

    def set_tmdb_status(self, found: bool, tmdb_id: Optional[int], cast_count: int, crew_count: int):
        """Set TMDB enrichment status"""
        self.data["pipeline"]["tmdb"] = {
            "found": found,
            "tmdb_id": tmdb_id,
            "cast_count": cast_count,
            "crew_count": crew_count
        }

    def set_era(self, era_name: Optional[str]):
        """Set era lexicon used"""
        self.data["pipeline"]["era"] = era_name

    def set_bias_windows(self, num_windows: int, window_seconds: int, stride_seconds: int):
        """Set bias window configuration"""
        self.data["pipeline"]["bias_windows"] = {
            "count": num_windows,
            "window_seconds": window_seconds,
            "stride_seconds": stride_seconds
        }

    def set_device(self, component: str, requested: str, actual: str):
        """
        Set device used for a component

        Args:
            component: Component name (e.g., 'whisperx', 'diarization')
            requested: Requested device (e.g., 'mps')
            actual: Actual device used (e.g., 'cpu' if fallback)
        """
        self.data["devices"][component] = {
            "requested": requested,
            "actual": actual,
            "fallback": requested != actual
        }

    def set_pipeline_step(self, step_name: str, enabled: bool, **kwargs):
        """
        Record pipeline step status

        Args:
            step_name: Name of pipeline step
            enabled: Whether step was enabled
            **kwargs: Additional step-specific info (completed, status, next_stage, etc.)
        """
        if "steps" not in self.data["pipeline"]:
            self.data["pipeline"]["steps"] = {}

        step_data = {
            "enabled": enabled,
            **kwargs
        }
        
        # Add timestamp for when step was recorded
        if "completed" in kwargs and kwargs["completed"]:
            step_data["completed_at"] = datetime.now().isoformat()
        
        self.data["pipeline"]["steps"][step_name] = step_data
        
        # Update current stage tracking
        if "completed" in kwargs and kwargs["completed"]:
            # Get status to determine if stage should be in completed_stages
            status = kwargs.get("status", "success")
            
            # Only add to completed_stages if it was successful
            # Skipped/failed stages should not block resume
            if status == "success" and step_name not in self.data["pipeline"]["completed_stages"]:
                self.data["pipeline"]["completed_stages"].append(step_name)
            elif status in ["skipped", "failed"]:
                # Track skipped/failed stages separately
                if "skipped_stages" not in self.data["pipeline"]:
                    self.data["pipeline"]["skipped_stages"] = []
                if step_name not in self.data["pipeline"]["skipped_stages"]:
                    self.data["pipeline"]["skipped_stages"].append(step_name)
            
            # Set next stage if provided
            if "next_stage" in kwargs:
                self.data["pipeline"]["next_stage"] = kwargs["next_stage"]
                self.data["pipeline"]["current_stage"] = None
            else:
                self.data["pipeline"]["next_stage"] = None
        else:
            self.data["pipeline"]["current_stage"] = step_name
        
        # Auto-save manifest if file path is set
        if self.manifest_file:
            self.save(self.manifest_file)

    def set_duration(self, step_name: str, duration_seconds: float):
        """Record duration for a pipeline step"""
        if "durations" not in self.data["timing"]:
            self.data["timing"]["durations"] = {}

        self.data["timing"]["durations"][step_name] = duration_seconds

    def finalize(self, status: str = "completed"):
        """Finalize manifest with total duration and final status"""
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        self.data["timing"]["total_seconds"] = total_duration
        self.data["timing"]["completed_at"] = end_time.isoformat()
        self.data["pipeline"]["status"] = status
        self.data["pipeline"]["current_stage"] = None
        self.data["pipeline"]["next_stage"] = None
        
        # Auto-save if manifest file is set
        if self.manifest_file:
            self.save(self.manifest_file)

    def save(self, filepath: Path):
        """Save manifest to JSON file"""
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w", encoding='utf-8') as f:
            json.dump(self.data, f, indent=2)

    def to_dict(self) -> Dict[str, Any]:
        """Get manifest as dictionary"""
        return self.data
    
    def load(self, filepath: Path):
        """Load existing manifest from JSON file"""
        if filepath.exists():
            with open(filepath, "r", encoding='utf-8', errors='replace') as f:
                loaded_data = json.load(f)
                # Merge loaded data, preserving structure
                self.data.update(loaded_data)
                # Update timestamp for resume
                self.data["resumed_at"] = datetime.now().isoformat()
    
    def get_last_completed_stage(self) -> Optional[str]:
        """Get the name of the last successfully completed stage"""
        completed = self.data["pipeline"].get("completed_stages", [])
        return completed[-1] if completed else None
    
    def get_next_stage(self) -> Optional[str]:
        """Get the next stage to run"""
        return self.data["pipeline"].get("next_stage")
