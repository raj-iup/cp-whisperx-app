#!/usr/bin/env python3
"""
Unit Tests for StageIO and Stage Utilities

Tests the StageIO class and related utilities.
Phase 2: Testing Infrastructure - Task 2.2
"""

# Standard library
import json
import sys
from pathlib import Path

# Third-party
import pytest

# Local
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.stage_utils import StageIO
from tests.utils.test_helpers import TestJobBuilder, compute_file_hash


@pytest.mark.unit
class TestStageIO:
    """Unit tests for StageIO class."""
    
    @pytest.fixture
    def job_builder(self, tmp_path):
        """Create job builder for tests."""
        builder = TestJobBuilder(base_dir=tmp_path)
        yield builder
        builder.cleanup()
    
    def test_stage_io_initialization(self, job_builder):
        """Test StageIO initializes correctly."""
        job_dir = job_builder.create_job()
        
        io = StageIO("test_stage", job_dir, enable_manifest=True)
        
        assert io.stage_name == "test_stage"
        assert io.job_dir == job_dir
        assert io.stage_dir == job_dir / "test_stage"
        assert io.stage_dir.exists()
    
    def test_stage_io_creates_stage_directory(self, job_builder):
        """Test StageIO creates stage directory."""
        job_dir = job_builder.create_job()
        stage_name = "test_stage"
        
        io = StageIO(stage_name, job_dir, enable_manifest=True)
        
        assert (job_dir / stage_name).exists()
        assert (job_dir / stage_name).is_dir()
    
    def test_stage_io_manifest_enabled(self, job_builder):
        """Test StageIO with manifest enabled."""
        job_dir = job_builder.create_job()
        
        io = StageIO("test_stage", job_dir, enable_manifest=True)
        
        assert io.manifest is not None
        assert io.manifest.stage == "test_stage"
    
    def test_stage_io_manifest_disabled(self, job_builder):
        """Test StageIO with manifest disabled."""
        job_dir = job_builder.create_job()
        
        io = StageIO("test_stage", job_dir, enable_manifest=False)
        
        assert io.manifest is None
    
    def test_get_stage_logger(self, job_builder):
        """Test StageIO creates stage logger."""
        job_dir = job_builder.create_job()
        
        io = StageIO("test_stage", job_dir, enable_manifest=True)
        logger = io.get_stage_logger()
        
        assert logger is not None
        assert logger.name == "stage.test_stage"
    
    def test_compute_hash(self, job_builder, tmp_path):
        """Test hash computation."""
        job_dir = job_builder.create_job()
        io = StageIO("test_stage", job_dir, enable_manifest=True)
        
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        hash1 = io.compute_hash(test_file)
        assert len(hash1) == 64  # SHA-256 hex digest
        
        # Same content should produce same hash
        hash2 = io.compute_hash(test_file)
        assert hash1 == hash2
        
        # Different content should produce different hash
        test_file.write_text("different content")
        hash3 = io.compute_hash(test_file)
        assert hash3 != hash1
    
    def test_add_input_tracking(self, job_builder, tmp_path):
        """Test input file tracking."""
        job_dir = job_builder.create_job()
        io = StageIO("test_stage", job_dir, enable_manifest=True)
        
        # Create test input file
        input_file = tmp_path / "input.txt"
        input_file.write_text("input data")
        
        file_hash = io.compute_hash(input_file)
        io.manifest.add_input(input_file, file_hash)
        
        # Verify input tracked
        assert len(io.manifest.inputs) == 1
        assert io.manifest.inputs[0]["path"] == str(input_file)
        assert io.manifest.inputs[0]["hash"] == file_hash
    
    def test_add_output_tracking(self, job_builder):
        """Test output file tracking."""
        job_dir = job_builder.create_job()
        io = StageIO("test_stage", job_dir, enable_manifest=True)
        
        # Create test output file
        output_file = io.stage_dir / "output.txt"
        output_file.write_text("output data")
        
        file_hash = io.compute_hash(output_file)
        io.manifest.add_output(output_file, file_hash)
        
        # Verify output tracked
        assert len(io.manifest.outputs) == 1
        assert io.manifest.outputs[0]["path"] == str(output_file)
        assert io.manifest.outputs[0]["hash"] == file_hash
    
    def test_finalize_manifest(self, job_builder):
        """Test manifest finalization."""
        job_dir = job_builder.create_job()
        io = StageIO("test_stage", job_dir, enable_manifest=True)
        
        # Create and track output
        output_file = io.stage_dir / "output.txt"
        output_file.write_text("output data")
        io.manifest.add_output(output_file, io.compute_hash(output_file))
        
        # Finalize
        io.finalize_stage_manifest(exit_code=0)
        
        # Verify manifest file created
        manifest_path = io.stage_dir / "manifest.json"
        assert manifest_path.exists()
        
        # Verify manifest content
        with open(manifest_path) as f:
            manifest_data = json.load(f)
        
        assert manifest_data["stage"] == "test_stage"
        assert manifest_data["exit_code"] == 0
        assert len(manifest_data["outputs"]) == 1
    
    def test_stage_directory_isolation(self, job_builder):
        """Test that different stages have isolated directories."""
        job_dir = job_builder.create_job()
        
        io1 = StageIO("stage1", job_dir, enable_manifest=True)
        io2 = StageIO("stage2", job_dir, enable_manifest=True)
        
        assert io1.stage_dir != io2.stage_dir
        assert io1.stage_dir == job_dir / "stage1"
        assert io2.stage_dir == job_dir / "stage2"


@pytest.mark.unit
class TestManifestTracking:
    """Unit tests for manifest tracking functionality."""
    
    @pytest.fixture
    def job_builder(self, tmp_path):
        """Create job builder for tests."""
        builder = TestJobBuilder(base_dir=tmp_path)
        yield builder
        builder.cleanup()
    
    def test_manifest_tracks_multiple_inputs(self, job_builder, tmp_path):
        """Test tracking multiple input files."""
        job_dir = job_builder.create_job()
        io = StageIO("test_stage", job_dir, enable_manifest=True)
        
        # Create multiple input files
        for i in range(3):
            input_file = tmp_path / f"input_{i}.txt"
            input_file.write_text(f"input {i}")
            io.manifest.add_input(input_file, io.compute_hash(input_file))
        
        assert len(io.manifest.inputs) == 3
    
    def test_manifest_tracks_multiple_outputs(self, job_builder):
        """Test tracking multiple output files."""
        job_dir = job_builder.create_job()
        io = StageIO("test_stage", job_dir, enable_manifest=True)
        
        # Create multiple output files
        for i in range(3):
            output_file = io.stage_dir / f"output_{i}.txt"
            output_file.write_text(f"output {i}")
            io.manifest.add_output(output_file, io.compute_hash(output_file))
        
        assert len(io.manifest.outputs) == 3
    
    def test_manifest_preserves_file_metadata(self, job_builder):
        """Test manifest preserves file metadata."""
        job_dir = job_builder.create_job()
        io = StageIO("test_stage", job_dir, enable_manifest=True)
        
        # Create output with known content
        output_file = io.stage_dir / "output.txt"
        content = "test content"
        output_file.write_text(content)
        
        file_hash = io.compute_hash(output_file)
        io.manifest.add_output(output_file, file_hash)
        
        # Finalize and reload
        io.finalize_stage_manifest(exit_code=0)
        
        manifest_path = io.stage_dir / "manifest.json"
        with open(manifest_path) as f:
            manifest_data = json.load(f)
        
        output_entry = manifest_data["outputs"][0]
        assert output_entry["path"] == str(output_file)
        assert output_entry["hash"] == file_hash
        assert output_entry["size"] == len(content)


@pytest.mark.unit
class TestStageLogging:
    """Unit tests for stage logging."""
    
    @pytest.fixture
    def job_builder(self, tmp_path):
        """Create job builder for tests."""
        builder = TestJobBuilder(base_dir=tmp_path)
        yield builder
        builder.cleanup()
    
    def test_stage_log_created(self, job_builder):
        """Test stage log file is created."""
        job_dir = job_builder.create_job()
        io = StageIO("test_stage", job_dir, enable_manifest=True)
        logger = io.get_stage_logger()
        
        # Write log message
        logger.info("Test message")
        
        # Verify log file exists
        log_path = io.stage_dir / "stage.log"
        assert log_path.exists()
    
    def test_stage_log_contains_messages(self, job_builder):
        """Test stage log contains logged messages."""
        job_dir = job_builder.create_job()
        io = StageIO("test_stage", job_dir, enable_manifest=True)
        logger = io.get_stage_logger()
        
        # Write log messages
        test_message = "Unique test message 12345"
        logger.info(test_message)
        
        # Verify message in log
        log_path = io.stage_dir / "stage.log"
        log_content = log_path.read_text()
        assert test_message in log_content
    
    def test_stage_logs_isolated(self, job_builder):
        """Test that different stages have isolated logs."""
        job_dir = job_builder.create_job()
        
        io1 = StageIO("stage1", job_dir, enable_manifest=True)
        io2 = StageIO("stage2", job_dir, enable_manifest=True)
        
        logger1 = io1.get_stage_logger()
        logger2 = io2.get_stage_logger()
        
        # Write to different loggers
        logger1.info("Message from stage1")
        logger2.info("Message from stage2")
        
        # Verify messages in correct logs
        log1_content = (io1.stage_dir / "stage.log").read_text()
        log2_content = (io2.stage_dir / "stage.log").read_text()
        
        assert "Message from stage1" in log1_content
        assert "Message from stage2" in log2_content
        assert "Message from stage2" not in log1_content
        assert "Message from stage1" not in log2_content
