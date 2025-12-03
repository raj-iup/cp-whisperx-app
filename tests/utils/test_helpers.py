#!/usr/bin/env python3
"""
Test Helper Utilities

Provides common utilities for test creation, execution, and validation.
Phase 2: Testing Infrastructure - Task 2.3
"""

# Standard library
import hashlib
import json
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any

# Third-party
import pytest


class TestJobBuilder:
    """Builder for creating test job directories with proper structure."""
    
    def __init__(self, base_dir: Optional[Path] = None):
        """
        Initialize test job builder.
        
        Args:
            base_dir: Base directory for test jobs (default: temp directory)
        """
        self.base_dir = base_dir or Path(tempfile.mkdtemp(prefix="test_job_"))
        self.job_counter = 0
    
    def create_job(
        self,
        workflow: str = "transcribe",
        job_name: Optional[str] = None,
        create_input: bool = True
    ) -> Path:
        """
        Create a test job directory with proper structure.
        
        Args:
            workflow: Workflow type (transcribe, translate, subtitle)
            job_name: Job name (default: auto-generated)
            create_input: Whether to create input directory
            
        Returns:
            Path to job directory
        """
        if job_name is None:
            self.job_counter += 1
            job_name = f"test_job_{self.job_counter:04d}"
        
        job_dir = self.base_dir / job_name
        job_dir.mkdir(parents=True, exist_ok=True)
        
        # Create input directory if requested
        if create_input:
            input_dir = job_dir / "in"
            input_dir.mkdir(exist_ok=True)
        
        # Create config file
        config_path = job_dir / "job_config.json"
        config_data = {
            "workflow": workflow,
            "job_name": job_name,
            "created_by": "test_helpers"
        }
        with open(config_path, "w") as f:
            json.dump(config_data, f, indent=2)
        
        return job_dir
    
    def add_sample_audio(
        self,
        job_dir: Path,
        duration: int = 5,
        sample_rate: int = 16000
    ) -> Path:
        """
        Add a sample audio file to job input.
        
        Args:
            job_dir: Job directory
            duration: Audio duration in seconds
            sample_rate: Audio sample rate
            
        Returns:
            Path to created audio file
        """
        try:
            import numpy as np
            import soundfile as sf
        except ImportError:
            pytest.skip("soundfile not available for audio generation")
        
        # Generate simple sine wave
        samples = duration * sample_rate
        t = np.linspace(0, duration, samples)
        audio = np.sin(2 * np.pi * 440 * t)  # 440 Hz tone
        
        # Test inputs go in job_dir/in (not stage output, OK per § 1.1)
        audio_path = job_dir / "in" / "test_audio.wav"
        audio_path.parent.mkdir(exist_ok=True)
        sf.write(audio_path, audio, sample_rate)
        
        return audio_path
    
    def add_sample_video(
        self,
        job_dir: Path,
        duration: int = 5
    ) -> Path:
        """
        Add a sample video file to job input (creates placeholder).
        
        Args:
            job_dir: Job directory
            duration: Video duration in seconds
            
        Returns:
            Path to created video file
        """
        # Test inputs go in job_dir/in (not stage output, OK per § 1.1)
        video_path = job_dir / "in" / "test_video.mp4"
        video_path.parent.mkdir(exist_ok=True)
        video_path.write_text(f"placeholder video {duration}s")
        
        return video_path
    
    def cleanup(self):
        """Clean up all created test jobs."""
        if self.base_dir.exists():
            shutil.rmtree(self.base_dir)


def create_test_job(
    workflow: str = "transcribe",
    audio_file: Optional[Path] = None,
    tmp_path: Optional[Path] = None
) -> Path:
    """
    Quick helper to create a test job with sample audio.
    
    Args:
        workflow: Workflow type
        audio_file: Optional existing audio file to copy
        tmp_path: Temporary directory (pytest fixture)
        
    Returns:
        Path to job directory
    """
    builder = TestJobBuilder(base_dir=tmp_path)
    job_dir = builder.create_job(workflow=workflow)
    
    if audio_file and audio_file.exists():
        dest = job_dir / "in" / audio_file.name
        shutil.copy2(audio_file, dest)
    else:
        builder.add_sample_audio(job_dir)
    
    return job_dir


def cleanup_test_job(job_dir: Path):
    """
    Clean up test job files.
    
    Args:
        job_dir: Job directory to clean up
    """
    if job_dir.exists():
        shutil.rmtree(job_dir)


def assert_stage_completed(job_dir: Path, stage_name: str):
    """
    Assert stage completed successfully.
    
    Args:
        job_dir: Job directory
        stage_name: Stage name to check
        
    Raises:
        AssertionError: If stage did not complete successfully
    """
    stage_dir = job_dir / stage_name
    assert stage_dir.exists(), f"Stage directory not found: {stage_dir}"
    
    manifest_path = stage_dir / "manifest.json"
    assert manifest_path.exists(), f"Manifest not found: {manifest_path}"
    
    with open(manifest_path) as f:
        manifest = json.load(f)
    
    assert manifest.get("exit_code") == 0, \
        f"Stage failed with exit code: {manifest.get('exit_code')}"
    assert manifest.get("stage") == stage_name, \
        f"Manifest stage mismatch: {manifest.get('stage')} != {stage_name}"


def assert_manifest_valid(manifest_path: Path):
    """
    Assert manifest is valid and complete.
    
    Args:
        manifest_path: Path to manifest file
        
    Raises:
        AssertionError: If manifest is invalid
    """
    assert manifest_path.exists(), f"Manifest not found: {manifest_path}"
    
    with open(manifest_path) as f:
        manifest = json.load(f)
    
    # Check required fields
    required_fields = ["stage", "job_name", "start_time", "exit_code"]
    for field in required_fields:
        assert field in manifest, f"Missing required field: {field}"
    
    # If successful, should have outputs
    if manifest["exit_code"] == 0:
        assert "outputs" in manifest, "Successful stage should have outputs"
        assert len(manifest["outputs"]) > 0, "Outputs list is empty"


def assert_logs_exist(job_dir: Path, stage_name: str):
    """
    Assert stage logs exist.
    
    Args:
        job_dir: Job directory
        stage_name: Stage name
        
    Raises:
        AssertionError: If logs not found
    """
    stage_dir = job_dir / stage_name
    log_path = stage_dir / "stage.log"
    
    assert log_path.exists(), f"Stage log not found: {log_path}"
    assert log_path.stat().st_size > 0, f"Stage log is empty: {log_path}"


def compute_file_hash(file_path: Path) -> str:
    """
    Compute SHA-256 hash of a file.
    
    Args:
        file_path: Path to file
        
    Returns:
        Hex digest of file hash
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def create_mock_manifest(
    stage: str,
    job_name: str,
    exit_code: int = 0,
    inputs: Optional[List[Dict[str, Any]]] = None,
    outputs: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Create a mock manifest for testing.
    
    Args:
        stage: Stage name
        job_name: Job name
        exit_code: Exit code
        inputs: List of input file dicts
        outputs: List of output file dicts
        
    Returns:
        Manifest dictionary
    """
    return {
        "stage": stage,
        "job_name": job_name,
        "start_time": "2025-12-03T05:00:00Z",
        "end_time": "2025-12-03T05:01:00Z",
        "exit_code": exit_code,
        "inputs": inputs or [],
        "outputs": outputs or []
    }


# Mock model utilities

class MockWhisperXModel:
    """Mock WhisperX model for testing."""
    
    def __init__(self):
        self.loaded = True
    
    def transcribe(self, audio_path: str, **kwargs) -> Dict[str, Any]:
        """Mock transcription."""
        return {
            "segments": [
                {
                    "start": 0.0,
                    "end": 5.0,
                    "text": "Mock transcription",
                    "words": [
                        {"start": 0.0, "end": 1.0, "word": "Mock"},
                        {"start": 1.0, "end": 2.0, "word": "transcription"}
                    ]
                }
            ],
            "language": "en"
        }


class MockIndicTrans2Model:
    """Mock IndicTrans2 model for testing."""
    
    def __init__(self):
        self.loaded = True
    
    def translate(self, text: str, src_lang: str, tgt_lang: str) -> str:
        """Mock translation."""
        return f"[TRANSLATED:{src_lang}→{tgt_lang}] {text}"


def mock_whisperx_model() -> MockWhisperXModel:
    """
    Create mock WhisperX model for testing.
    
    Returns:
        Mock model instance
    """
    return MockWhisperXModel()


def mock_indictrans2_model() -> MockIndicTrans2Model:
    """
    Create mock IndicTrans2 model for testing.
    
    Returns:
        Mock model instance
    """
    return MockIndicTrans2Model()


# Assertion helpers

def assert_file_exists_with_content(
    file_path: Path,
    min_size: int = 1
):
    """
    Assert file exists and has minimum size.
    
    Args:
        file_path: Path to file
        min_size: Minimum file size in bytes
        
    Raises:
        AssertionError: If file doesn't exist or is too small
    """
    assert file_path.exists(), f"File not found: {file_path}"
    size = file_path.stat().st_size
    assert size >= min_size, f"File too small: {size} < {min_size}"


def assert_json_valid(file_path: Path):
    """
    Assert file contains valid JSON.
    
    Args:
        file_path: Path to JSON file
        
    Raises:
        AssertionError: If JSON is invalid
    """
    assert_file_exists_with_content(file_path)
    
    try:
        with open(file_path) as f:
            json.load(f)
    except json.JSONDecodeError as e:
        pytest.fail(f"Invalid JSON in {file_path}: {e}")


def assert_stage_output_tracked(
    job_dir: Path,
    stage_name: str,
    expected_files: List[str]
):
    """
    Assert all expected files are tracked in stage manifest.
    
    Args:
        job_dir: Job directory
        stage_name: Stage name
        expected_files: List of expected output filenames
        
    Raises:
        AssertionError: If files not tracked
    """
    manifest_path = job_dir / stage_name / "manifest.json"
    assert_json_valid(manifest_path)
    
    with open(manifest_path) as f:
        manifest = json.load(f)
    
    tracked_files = [Path(out["path"]).name for out in manifest.get("outputs", [])]
    
    for expected in expected_files:
        assert expected in tracked_files, \
            f"File {expected} not tracked in manifest. Tracked: {tracked_files}"
