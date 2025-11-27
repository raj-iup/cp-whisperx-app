"""
Shared utilities for pipeline stages.
Provides standardized I/O patterns and directory structure.
"""
import os
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# Import centralized stage ordering
from shared.stage_order import get_stage_number, get_stage_dir, STAGE_NUMBERS


class StageIO:
    """
    Standardized input/output handling for pipeline stages.
    
    Directory structure:
        output_base/
            01_demux/
                audio.wav
                metadata.json
            02_tmdb/
                tmdb_data.json
                metadata.json
            03_glossary_load/
                glossary_snapshot.json
                metadata.json
            ...
    """
    
    def __init__(self, stage_name: str, output_base: Optional[Path] = None):
        """
        Initialize stage I/O handler.
        
        Args:
            stage_name: Name of the current stage
            output_base: Base output directory (defaults to OUTPUT_DIR env var or 'out')
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
        
        # Logs directory
        self.logs_dir = self.output_base / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
    
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


def get_stage_logger(stage_name: str, log_level: str = "DEBUG", stage_io: Optional['StageIO'] = None):
    """
    Get a logger for a specific stage with proper configuration.
    
    Args:
        stage_name: Name of the stage
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        stage_io: Optional StageIO instance for file logging
    
    Returns:
        Configured logger
    """
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
    
    # Add file handler if StageIO is provided
    if stage_io is not None:
        log_file = stage_io.get_log_path()
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.debug(f"Logging to file: {log_file}")
    
    return logger
