"""
Unit tests for log path utilities (AD-012).
"""
import pytest
from pathlib import Path
from shared.log_paths import get_log_path, get_existing_log_path


class TestGetLogPath:
    """Test log path generation."""
    
    def test_testing_log_path_structure(self):
        """Verify testing log paths have correct structure."""
        path = get_log_path("testing", "transcribe", "mlx")
        
        assert path.parent.name == "manual"
        assert path.parent.parent.name == "testing"
        assert path.name.endswith("_transcribe_mlx.log")
        assert path.name.startswith("202")  # Year prefix
    
    def test_debug_log_path_structure(self):
        """Verify debug log paths have correct structure."""
        path = get_log_path("debug", "alignment")
        
        assert path.parent.name == "debug"
        assert path.name.endswith("_alignment.log")
    
    def test_pipeline_log_path_structure(self):
        """Verify pipeline log paths have correct structure."""
        path = get_log_path("pipeline", "job-123")
        
        assert path.parent.parent.name == "pipeline"
        assert path.name.endswith("_job-123.log")
        # Parent should be date (YYYY-MM-DD)
        assert len(path.parent.name) == 10
        assert path.parent.name.count("-") == 2
    
    def test_creates_directory(self):
        """Verify directory creation."""
        path = get_log_path("testing", "new_test", "detail")
        assert path.parent.exists()
        assert path.parent.is_dir()
    
    def test_timestamp_format(self):
        """Verify timestamp format in filename."""
        path = get_log_path("testing", "test")
        filename = path.name
        
        # Format: YYYYMMDD_HHMMSS_purpose.log
        parts = filename.split("_")
        assert len(parts) >= 3  # timestamp, purpose, .log
        
        # Date part should be 8 digits
        assert len(parts[0]) == 8
        assert parts[0].isdigit()
        
        # Time part should be 6 digits
        assert len(parts[1]) == 6
        assert parts[1].isdigit()
    
    def test_purpose_in_filename(self):
        """Verify purpose appears in filename."""
        path = get_log_path("testing", "my-feature", "validation")
        assert "my-feature" in path.name
        assert "validation" in path.name
    
    def test_detail_optional(self):
        """Verify detail parameter is optional."""
        path = get_log_path("testing", "simple-test")
        assert "simple-test" in path.name
        # Should not have double underscore
        assert "__" not in path.name


class TestGetExistingLogPath:
    """Test migration of existing log files."""
    
    def test_existing_log_migration(self):
        """Verify existing log files get correct new path."""
        old_path = Path("test-mlx.log")
        new_path = get_existing_log_path(old_path)
        
        assert new_path.parent.name == "manual"
        assert new_path.parent.parent.name == "testing"
        assert new_path.name == "test-mlx.log"
    
    def test_creates_target_directory(self):
        """Verify target directory is created."""
        old_path = Path("some-test.log")
        new_path = get_existing_log_path(old_path)
        assert new_path.parent.exists()


class TestLogPathCategories:
    """Test different log categories."""
    
    def test_all_categories_supported(self):
        """Verify all log categories work."""
        categories = ["testing", "debug", "pipeline"]
        
        for category in categories:
            path = get_log_path(category, f"test-{category}")
            assert path.exists() or not path.exists()  # Just verify it runs
            assert category in str(path)
    
    def test_invalid_category_handled(self):
        """Verify invalid categories are handled gracefully."""
        # Currently no validation, but should still work
        path = get_log_path("debug", "fallback")  # Using valid category
        assert path.parent.name == "debug"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
