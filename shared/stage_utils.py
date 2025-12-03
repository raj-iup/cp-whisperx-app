"""
Shared utilities for pipeline stages.
Provides standardized I/O patterns and directory structure.
"""
# Standard library
import os
import json
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# Local
from shared.stage_order import get_stage_number, get_stage_dir, STAGE_NUMBERS
from shared.manifest import StageManifest
from shared.logger import get_logger
logger = get_logger(__name__)


class StageIO:
    """
    Standardized input/output handling for pipeline stages.
    
    Enhanced with:
    - Dual logging (stage.log + main pipeline log)
    - Manifest tracking (inputs, outputs, intermediate files)
    - Automatic resource tracking
    
    Directory structure:
        output_base/
            01_demux/
                stage.log              # NEW: Detailed stage log
                manifest.json          # NEW: I/O tracking
                audio.wav
                metadata.json
            02_tmdb/
                stage.log
                manifest.json
                tmdb_data.json
                metadata.json
            logs/
                99_pipeline_*.log      # Main orchestration log
    """
    
    def __init__(self, stage_name: str, output_base: Optional[Path] = None, 
                 enable_manifest: bool = True):
        """
        Initialize stage I/O handler.
        
        Args:
            stage_name: Name of the current stage
            output_base: Base output directory (defaults to OUTPUT_DIR env var or 'out')
            enable_manifest: Whether to enable manifest tracking (default: True)
        """
        self.stage_name = stage_name
        
        try:
            self.stage_number = get_stage_number(stage_name)
        except ValueError:
            # Fallback for unknown stages
            self.stage_number = 99
        
        # Determine output base directory
        if output_base is None:
            output_base = os.environ.get('OUTPUT_DIR', 'out')
        self.output_base = Path(output_base)
        
        # Create stage-specific directory using centralized naming
        try:
            stage_dir_name = get_stage_dir(stage_name).split('/')[-1]
            self.stage_dir = self.output_base / stage_dir_name
        except ValueError:
            # Fallback for unknown stages
            self.stage_dir = self.output_base / f"{self.stage_number:02d}_{stage_name}"
        
        self.stage_dir.mkdir(parents=True, exist_ok=True)
        
        # Stage log file
        self.stage_log = self.stage_dir / "stage.log"
        
        # Logs directory (for main pipeline log)
        self.logs_dir = self.output_base / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize manifest
        self.enable_manifest = enable_manifest
        self.manifest_path = self.stage_dir / "manifest.json"
        self.manifest = None
        
        if enable_manifest:
            self.manifest = StageManifest(stage_name, self.output_base)
            # Load existing manifest if resuming
            if self.manifest_path.exists():
                self.manifest.load(self.manifest_path)
    
    def get_stage_logger(self, log_level: str = "INFO") -> logging.Logger:
        """
        Get dual logger that writes to both stage.log and main pipeline log.
        
        The logger writes:
        - ALL levels (including DEBUG) to stage.log
        - INFO and above to main pipeline log
        - INFO and above to console
        
        Args:
            log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
        Returns:
            Configured logger instance
        
        Example:
            >>> io = StageIO("asr")
            >>> logger = io.get_stage_logger()
            >>> logger.debug("Detailed step")  # Only in stage.log
            >>> logger.info("Progress update")  # In stage.log + pipeline.log + console
        """
        from shared.logger import setup_dual_logger
        return setup_dual_logger(
            self.stage_name,
            stage_log_file=self.stage_log,
            main_log_dir=self.logs_dir,
            log_level=log_level
        )
    
    def track_input(self, file_path: Path, file_type: str = "file", **metadata: Any) -> None:
        """
        Track input file in manifest.
        
        Args:
            file_path: Path to input file
            file_type: Type of file (e.g., "audio", "transcript", "metadata")
            **metadata: Additional metadata (format, checksum, etc.)
        """
        if self.manifest:
            # StageManifest.add_input expects: key, filepath, description
            # We use file_type as the key and format metadata as description
            description = metadata.get('format', file_type)
            self.manifest.add_input(file_type, file_path, description)
    
    def track_output(self, file_path: Path, file_type: str = "file", **metadata: Any) -> None:
        """
        Track output file in manifest.
        
        Args:
            file_path: Path to output file
            file_type: Type of file (e.g., "audio", "transcript", "metadata")
            **metadata: Additional metadata (format, size, etc.)
        """
        if self.manifest:
            # StageManifest.add_output expects: key, filepath, description
            # We use file_type as the key and format metadata as description
            description = metadata.get('format', file_type)
            self.manifest.add_output(file_type, file_path, description)
    
    def track_intermediate(self, file_path: Path, retained: bool = False, reason: str = "") -> None:
        """
        Track intermediate/cache file in manifest.
        
        Args:
            file_path: Path to intermediate file
            retained: Whether file is kept after stage completion
            reason: Explanation for why file was created/retained
        """
        if self.manifest:
            self.manifest.add_intermediate(file_path, retained, reason)
    
    def add_config(self, key: str, value: Any) -> None:
        """Add configuration parameter to manifest"""
        if self.manifest:
            self.manifest.add_config(key, value)
    
    def set_config(self, config_dict: Dict[str, Any]) -> None:
        """Set multiple configuration parameters in manifest"""
        if self.manifest:
            self.manifest.set_config(config_dict)
    
    def add_warning(self, message: str) -> None:
        """Add warning to manifest"""
        if self.manifest:
            self.manifest.add_warning(message)
    
    def add_error(self, message: str, exception: Optional[Exception] = None) -> None:
        """Add error to manifest"""
        if self.manifest:
            self.manifest.add_error(message, exception)
    
    def set_resources(self, **resources: Any) -> None:
        """Set resource usage in manifest"""
        if self.manifest:
            self.manifest.set_resources(**resources)
    
    def finalize(self, status: str = "success", save_manifest: bool = True, **kwargs: Any) -> None:
        """
        Finalize stage execution.
        
        Args:
            status: Final status (success, failed, skipped)
            save_manifest: Whether to save manifest to disk
            **kwargs: Additional metadata for manifest
        """
        if self.manifest:
            self.manifest.finalize(status, **kwargs)
            if save_manifest:
                self.manifest.save(self.manifest_path)
    
    def get_input_path(self, filename: str, from_stage: Optional[str] = None) -> Path:
        """
        Get path to input file from a previous stage.
        
        Args:
            filename: Name of the input file
            from_stage: Stage to read from (defaults to previous stage)
        
        Returns:
            Path to input file
        """
        if from_stage is None:
            # Default to previous stage
            from_stage_num = self.stage_number - 1
            # Find stage name by number using centralized mapping
            from_stage = next(
                (name for name, num in STAGE_NUMBERS.items() if num == from_stage_num),
                None
            )
        else:
            # Get stage number for specified stage
            try:
                from_stage_num = get_stage_number(from_stage)
            except ValueError:
                from_stage_num = self.stage_number - 1
        
        if from_stage:
            try:
                input_dir_name = get_stage_dir(from_stage).split('/')[-1]
                input_dir = self.output_base / input_dir_name
            except ValueError:
                input_dir = self.output_base / f"{from_stage_num:02d}_{from_stage}"
            input_path = input_dir / filename
        else:
            # Fallback to output_base
            input_path = self.output_base / filename
        
        # If not found in stage dir, check output_base
        if not input_path.exists():
            fallback_path = self.output_base / filename
            if fallback_path.exists():
                return fallback_path
        
        return input_path
    
    def get_output_path(self, filename: str) -> Path:
        """
        Get path for output file in this stage's directory.
        
        Args:
            filename: Name of the output file
        
        Returns:
            Path to output file
        """
        return self.stage_dir / filename
    
    def save_json(self, data: Any, filename: str) -> Path:
        """
        Save JSON data to stage output directory.
        
        Args:
            data: Data to save
            filename: Output filename
        
        Returns:
            Path to saved file
        """
        output_path = self.get_output_path(filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return output_path
    
    def load_json(self, filename: str, from_stage: Optional[str] = None) -> Any:
        """
        Load JSON data from input.
        
        Args:
            filename: Input filename
            from_stage: Stage to load from (defaults to previous stage)
        
        Returns:
            Loaded data
        """
        input_path = self.get_input_path(filename, from_stage)
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        with open(input_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_metadata(self, metadata: Dict[str, Any]) -> Path:
        """
        Save stage metadata including timing and status information.
        
        Args:
            metadata: Metadata dictionary
        
        Returns:
            Path to metadata file
        """
        metadata.update({
            'stage': self.stage_name,
            'stage_number': self.stage_number,
            'timestamp': datetime.now().isoformat()
        })
        return self.save_json(metadata, 'metadata.json')
    
    def load_metadata(self, from_stage: Optional[str] = None) -> Dict[str, Any]:
        """
        Load metadata from a previous stage.
        
        Args:
            from_stage: Stage to load from (defaults to previous stage)
        
        Returns:
            Metadata dictionary
        """
        try:
            return self.load_json('metadata.json', from_stage)
        except FileNotFoundError:
            return {}
    
    def get_log_path(self, timestamp: Optional[str] = None) -> Path:
        """
        Get path for stage log file with sequential numbering.
        
        Args:
            timestamp: Optional timestamp (defaults to current time)
        
        Returns:
            Path to log file
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        log_filename = f"{self.stage_number:02d}_{self.stage_name}_{timestamp}.log"
        return self.logs_dir / log_filename
    
    def copy_to_base(self, filename: str) -> Path:
        """
        Copy a file from stage directory to output base (for backward compatibility).
        
        Args:
            filename: Filename to copy
        
        Returns:
            Path to copied file in base directory
        """
        import shutil
        source = self.get_output_path(filename)
        dest = self.output_base / filename
        
        if source.exists():
            shutil.copy2(source, dest)
        
        return dest
    
    def get_all_inputs(self) -> List[Path]:
        """
        Get all input files from previous stage.
        
        Returns:
            List of paths to input files
        """
        from_stage_num = self.stage_number - 1
        from_stage = next(
            (name for name, num in STAGE_NUMBERS.items() if num == from_stage_num),
            None
        )
        
        if from_stage:
            try:
                input_dir_name = get_stage_dir(from_stage).split('/')[-1]
                input_dir = self.output_base / input_dir_name
            except ValueError:
                input_dir = self.output_base / f"{from_stage_num:02d}_{from_stage}"
            if input_dir.exists():
                return list(input_dir.iterdir())
        
        return []


def get_stage_logger(stage_name: str, log_level: str = "DEBUG", stage_io: Optional['StageIO'] = None) -> logging.Logger:
    """
    Get a logger for a specific stage with proper configuration.
    
    Args:
        stage_name: Name of the stage
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        stage_io: Optional StageIO instance for file logging
    
    Returns:
        Configured logger
    """
    if stage_io is not None:
        # Use dual logger with stage.log + main pipeline log
        from shared.logger import setup_dual_logger
        return setup_dual_logger(
            stage_name,
            stage_log_file=stage_io.stage_log,
            main_log_dir=stage_io.logs_dir,
            log_level=log_level
        )
    else:
        # Fallback to simple console logger
        import logging
        logger = logging.getLogger(stage_name)
        logger.setLevel(getattr(logging, log_level.upper()))
        
        # Remove existing handlers
        logger.handlers = []
        
        # Create console handler with formatting
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        
        formatter = logging.Formatter(
            "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        return logger
