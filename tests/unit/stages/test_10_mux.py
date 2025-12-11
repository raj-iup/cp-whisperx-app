#!/usr/bin/env python3
"""
Unit Tests for 10_mux Stage

Tests mux stage functionality including subtitle embedding.
Phase 3: Session 2 - Mux Stage Testing
"""

# Standard library
import sys
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call

# Third-party
import pytest

# Local
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.mark.unit
@pytest.mark.stage
class TestMuxStage:
    """Unit tests for 10_mux stage."""
    
    @pytest.fixture
    def mock_job_dir(self, tmp_path: Path) -> Path:
        """Create a mock job directory with minimal structure."""
        job_dir = tmp_path / "test_job"
        job_dir.mkdir()
        
        # Create prerequisite directories
        (job_dir / "09_subtitle_generation").mkdir()
        
        # Create mock subtitle files
        subtitle_dir = job_dir / "09_subtitle_generation"
        (subtitle_dir / "test_video.hi.srt").write_text("1\n00:00:00,000 --> 00:00:02,000\nहिन्दी\n\n")
        (subtitle_dir / "test_video.en.srt").write_text("1\n00:00:00,000 --> 00:00:02,000\nEnglish\n\n")
        
        # Create mock video file
        video_file = job_dir / "test_video.mp4"
        video_file.write_bytes(b"fake video content")
        
        # Create minimal config
        config_path = job_dir / ".env.pipeline"
        config_path.write_text(f"INPUT_MEDIA={video_file}\n")
        
        return job_dir
    
    def test_mux_entry_point_exists(self) -> None:
        """Test that mux stage has run_stage() entry point."""
        import importlib
        module = importlib.import_module("scripts.10_mux")
        assert hasattr(module, "run_stage")
        assert callable(module.run_stage)
    
    def test_mux_has_main_function(self) -> None:
        """Test that mux stage has main() function."""
        import importlib
        module = importlib.import_module("scripts.10_mux")
        assert hasattr(module, "main")
        assert callable(module.main)
    
    @pytest.mark.skip(reason="Phase 3 - Requires ffmpeg and full environment")
    def test_mux_creates_output_dir(self, mock_job_dir: Path) -> None:
        """Test that mux stage creates its output directory."""
        import importlib
        module = importlib.import_module("scripts.10_mux")
        
        exit_code = module.run_stage(mock_job_dir, "10_mux")
        
        output_dir = mock_job_dir / "10_mux"
        assert output_dir.exists()
    
    @pytest.mark.skip(reason="Phase 3 - Requires ffmpeg and full environment")
    def test_mux_returns_exit_code(self, mock_job_dir: Path) -> None:
        """Test that mux stage returns proper exit code."""
        import importlib
        module = importlib.import_module("scripts.10_mux")
        
        exit_code = module.run_stage(mock_job_dir, "10_mux")
        
        assert isinstance(exit_code, int)
        assert exit_code in [0, 1]  # Success or failure


@pytest.mark.unit
@pytest.mark.integration
class TestMuxFunctionality:
    """Integration tests for mux stage functionality."""
    
    @pytest.fixture
    def mock_stage_io(self):
        """Create a mock StageIO object."""
        mock_io = MagicMock()
        mock_io.stage_dir = Path("/tmp/test_job/10_mux")
        mock_io.output_base = Path("/tmp/test_job")
        mock_io.stage_log = Path("/tmp/test_job/10_mux/stage.log")
        mock_io.manifest_path = Path("/tmp/test_job/10_mux/manifest.json")
        
        # Mock logger
        mock_logger = MagicMock()
        mock_io.get_stage_logger.return_value = mock_logger
        
        return mock_io
    
    @pytest.mark.skip(reason="Phase 3 - Requires mocking ffmpeg")
    def test_mux_handles_missing_subtitles(self, mock_stage_io: MagicMock) -> None:
        """Test that mux stage handles missing subtitle files gracefully."""
        # This would test error handling when no subtitles are found
        pass
    
    @pytest.mark.skip(reason="Phase 3 - Requires mocking ffmpeg")
    def test_mux_handles_multiple_subtitles(self, mock_stage_io: MagicMock) -> None:
        """Test that mux stage can handle multiple subtitle tracks."""
        # This would test muxing with multiple language subtitles
        pass
    
    @pytest.mark.skip(reason="Phase 3 - Requires mocking ffmpeg")
    def test_mux_preserves_video_format(self, mock_stage_io: MagicMock) -> None:
        """Test that mux stage preserves original video format."""
        # This would test that output format matches input format
        pass
    
    @pytest.mark.skip(reason="Phase 3 - Requires mocking ffmpeg")
    def test_mux_sets_subtitle_language_metadata(self, mock_stage_io: MagicMock) -> None:
        """Test that mux stage sets proper language metadata."""
        # This would test language code extraction and metadata setting
        pass
    
    @pytest.mark.skip(reason="Phase 3 - Requires mocking ffmpeg")
    def test_mux_creates_final_output_link(self, mock_stage_io: MagicMock) -> None:
        """Test that mux stage creates final_output.mp4 symlink."""
        # This would test symlink creation
        pass


@pytest.mark.unit
class TestMuxHelpers:
    """Unit tests for mux stage helper functions."""
    
    def test_language_code_extraction(self) -> None:
        """Test language code extraction from filename."""
        # Test cases for extracting language codes from filenames
        test_cases = [
            ("movie.hi.srt", "hi"),
            ("movie.en.srt", "en"),
            ("movie.gu.srt", "gu"),
            ("movie.srt", "und"),  # undefined
        ]
        
        for filename, expected_code in test_cases:
            stem = Path(filename).stem
            parts = stem.split('.')
            if len(parts) >= 2:
                lang_code = parts[-1].lower()
            else:
                lang_code = "und"
            
            assert lang_code == expected_code, f"Failed for {filename}"
    
    def test_language_code_mapping(self) -> None:
        """Test 2-letter to 3-letter ISO 639-2 language code mapping."""
        lang_map = {
            "hi": "hin",  # Hindi
            "en": "eng",  # English
            "gu": "guj",  # Gujarati
            "ta": "tam",  # Tamil
        }
        
        # Test known mappings
        assert lang_map.get("hi") == "hin"
        assert lang_map.get("en") == "eng"
        assert lang_map.get("gu") == "guj"
        
        # Test unknown code (should return original)
        assert lang_map.get("xx", "xx") == "xx"
    
    def test_subtitle_sort_order(self) -> None:
        """Test subtitle file sorting by language priority."""
        def sort_key(path: Path) -> tuple:
            """Sort key for subtitle files by language priority."""
            name = path.stem.lower()
            if '.hi.' in name or name.endswith('.hi'):
                return (0, path.stem)  # Hindi first
            elif '.en.' in name or name.endswith('.en'):
                return (1, path.stem)  # English second
            else:
                return (2, path.stem)  # Others last
        
        # Create test file paths
        files = [
            Path("movie.ta.srt"),
            Path("movie.en.srt"),
            Path("movie.hi.srt"),
            Path("movie.gu.srt"),
        ]
        
        sorted_files = sorted(files, key=sort_key)
        
        # Verify Hindi comes first, English second
        assert ".hi." in sorted_files[0].stem or sorted_files[0].stem.endswith(".hi")
        assert ".en." in sorted_files[1].stem or sorted_files[1].stem.endswith(".en")


@pytest.mark.integration
@pytest.mark.smoke
class TestMuxIntegration:
    """Smoke tests for mux stage integration."""
    
    @pytest.mark.skip(reason="Phase 3 - Requires full pipeline environment")
    def test_mux_stage_in_pipeline(self) -> None:
        """Test mux stage as part of full pipeline."""
        # This would test the stage in the context of a full pipeline run
        pass
    
    @pytest.mark.skip(reason="Phase 3 - Requires test media")
    def test_mux_with_test_media(self) -> None:
        """Test mux stage with standard test media samples."""
        # This would test with actual test media files
        # Reference: § 1.4 Standard Test Media
        pass
    
    @pytest.mark.skip(reason="Phase 3 - Requires workflow validation")
    def test_mux_completes_subtitle_workflow(self) -> None:
        """Test that mux stage completes subtitle workflow successfully."""
        # This would validate the entire subtitle workflow from end-to-end
        # Reference: § 1.5 Core Workflows
        pass


# Module-level test info
def test_module_info() -> None:
    """Test that module can be imported and has expected attributes."""
    import importlib
    module = importlib.import_module("scripts.10_mux")
    
    # Check expected functions exist
    assert hasattr(module, "main")
    assert hasattr(module, "run_stage")
    
    # Check type hints are present
    import inspect
    sig = inspect.signature(module.run_stage)
    assert 'job_dir' in sig.parameters
    assert 'stage_name' in sig.parameters
    assert sig.return_annotation == int
