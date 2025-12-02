"""
Stage manifest management for pipeline stages.

Tracks inputs, outputs, intermediate files, and execution metadata
for each pipeline stage.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List


class StageManifest:
    """Manages per-stage execution manifest"""
    
    def __init__(self, stage_name: str, stage_number: int):
        """
        Initialize stage manifest.
        
        Args:
            stage_name: Name of the stage (e.g., "asr", "alignment")
            stage_number: Stage number in pipeline
        """
        self.stage_name = stage_name
        self.stage_number = stage_number
        self.start_time = datetime.now()
        
        self.data: Dict[str, Any] = {
            "stage": stage_name,
            "stage_number": stage_number,
            "timestamp": self.start_time.isoformat(),
            "status": "running",
            "inputs": [],
            "outputs": [],
            "intermediate_files": [],
            "config": {},
            "resources": {},
            "errors": [],
            "warnings": []
        }
    
    def add_input(self, file_path: Path, file_type: str = "file", **metadata):
        """
        Add input file to manifest.
        
        Args:
            file_path: Path to input file
            file_type: Type of file (e.g., "audio", "transcript", "metadata")
            **metadata: Additional metadata (format, size, checksum, etc.)
        """
        entry = {
            "type": file_type,
            "path": str(file_path),
            **metadata
        }
        
        # Add file size if file exists
        if file_path.exists():
            entry["size_bytes"] = file_path.stat().st_size
        
        self.data["inputs"].append(entry)
    
    def add_output(self, file_path: Path, file_type: str = "file", **metadata):
        """
        Add output file to manifest.
        
        Args:
            file_path: Path to output file
            file_type: Type of file (e.g., "audio", "transcript", "metadata")
            **metadata: Additional metadata (format, size, checksum, etc.)
        """
        entry = {
            "type": file_type,
            "path": str(file_path),
            **metadata
        }
        
        # Add file size if file exists
        if file_path.exists():
            entry["size_bytes"] = file_path.stat().st_size
        
        self.data["outputs"].append(entry)
    
    def add_intermediate(self, file_path: Path, retained: bool = False, reason: str = ""):
        """
        Add intermediate/cache file to manifest.
        
        Args:
            file_path: Path to intermediate file
            retained: Whether file is kept after stage completion
            reason: Explanation for why file was created/retained
        """
        entry = {
            "type": "intermediate",
            "path": str(file_path),
            "retained": retained,
            "reason": reason
        }
        
        # Add file size if file exists
        if file_path.exists():
            entry["size_bytes"] = file_path.stat().st_size
        
        self.data["intermediate_files"].append(entry)
    
    def add_config(self, key: str, value: Any):
        """
        Add configuration parameter to manifest.
        
        Args:
            key: Configuration parameter name
            value: Configuration parameter value
        """
        self.data["config"][key] = value
    
    def set_config(self, config_dict: Dict[str, Any]):
        """
        Set multiple configuration parameters at once.
        
        Args:
            config_dict: Dictionary of configuration parameters
        """
        self.data["config"].update(config_dict)
    
    def add_warning(self, message: str):
        """
        Add warning message to manifest.
        
        Args:
            message: Warning message
        """
        self.data["warnings"].append({
            "timestamp": datetime.now().isoformat(),
            "message": message
        })
    
    def add_error(self, message: str, exception: Optional[Exception] = None):
        """
        Add error to manifest.
        
        Args:
            message: Error message
            exception: Optional exception object
        """
        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "message": message
        }
        
        if exception:
            error_entry["exception_type"] = type(exception).__name__
            error_entry["exception_detail"] = str(exception)
        
        self.data["errors"].append(error_entry)
    
    def set_resources(self, **resources):
        """
        Set resource usage information.
        
        Args:
            **resources: Resource usage data (cpu_percent, memory_mb, gpu_used, etc.)
        """
        self.data["resources"].update(resources)
    
    def finalize(self, status: str = "success", **kwargs):
        """
        Finalize manifest with completion status and duration.
        
        Args:
            status: Final status (success, failed, skipped)
            **kwargs: Additional metadata to include in manifest
        """
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        self.data.update({
            "duration_seconds": duration,
            "completed_at": end_time.isoformat(),
            "status": status,
            **kwargs
        })
    
    def save(self, path: Path):
        """
        Save manifest to JSON file.
        
        Args:
            path: Path to save manifest.json
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2)
    
    def load(self, path: Path):
        """
        Load existing manifest from JSON file.
        
        Args:
            path: Path to existing manifest.json
        """
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
                self.data.update(loaded_data)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Get manifest as dictionary.
        
        Returns:
            Dictionary representation of manifest
        """
        return self.data.copy()
    
    def get_inputs(self) -> List[Dict[str, Any]]:
        """Get list of input files"""
        return self.data["inputs"]
    
    def get_outputs(self) -> List[Dict[str, Any]]:
        """Get list of output files"""
        return self.data["outputs"]
    
    def get_intermediate_files(self) -> List[Dict[str, Any]]:
        """Get list of intermediate files"""
        return self.data["intermediate_files"]
    
    def has_errors(self) -> bool:
        """Check if manifest has any errors"""
        return len(self.data["errors"]) > 0
    
    def has_warnings(self) -> bool:
        """Check if manifest has any warnings"""
        return len(self.data["warnings"]) > 0
