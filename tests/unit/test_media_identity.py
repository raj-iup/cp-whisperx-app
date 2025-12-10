"""
Unit tests for media identity computation (AD-014).
"""
import pytest
from pathlib import Path
import tempfile
import shutil
from shared.media_identity import (
    compute_media_id,
    compute_glossary_hash,
    verify_media_id_stability,
    _get_media_duration
)


class TestComputeMediaId:
    """Test media ID computation."""
    
    def test_requires_existing_file(self):
        """Verify error on missing file."""
        with pytest.raises(FileNotFoundError):
            compute_media_id(Path("nonexistent.mp4"))
    
    def test_requires_file_not_directory(self):
        """Verify error on directory path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(RuntimeError):
                compute_media_id(Path(tmpdir))
    
    def test_returns_64_char_hex_string(self):
        """Verify media ID format."""
        # Use standard test media
        test_media = Path("in/Energy Demand in AI.mp4")
        
        if not test_media.exists():
            pytest.skip("Test media not available")
        
        media_id = compute_media_id(test_media)
        
        # Should be 64-character hex string (SHA256)
        assert len(media_id) == 64
        assert all(c in '0123456789abcdef' for c in media_id)
    
    def test_stability_across_runs(self):
        """Verify same file produces same ID."""
        test_media = Path("in/Energy Demand in AI.mp4")
        
        if not test_media.exists():
            pytest.skip("Test media not available")
        
        # Compute multiple times
        id1 = compute_media_id(test_media)
        id2 = compute_media_id(test_media)
        id3 = compute_media_id(test_media)
        
        # All should match
        assert id1 == id2 == id3
    
    def test_different_files_different_ids(self):
        """Verify different files produce different IDs."""
        test_media1 = Path("in/Energy Demand in AI.mp4")
        test_media2 = Path("in/test_clips/jaane_tu_test_clip.mp4")
        
        if not test_media1.exists() or not test_media2.exists():
            pytest.skip("Test media not available")
        
        id1 = compute_media_id(test_media1)
        id2 = compute_media_id(test_media2)
        
        # Should be different
        assert id1 != id2
    
    def test_verify_media_id_stability_helper(self):
        """Test stability verification helper."""
        test_media = Path("in/Energy Demand in AI.mp4")
        
        if not test_media.exists():
            pytest.skip("Test media not available")
        
        # Should verify as stable
        assert verify_media_id_stability(test_media, iterations=3)


class TestComputeGlossaryHash:
    """Test glossary hash computation."""
    
    def test_empty_glossary_returns_empty_hash(self):
        """Verify hash for non-existent glossary."""
        result = compute_glossary_hash(Path("nonexistent.json"))
        
        # Should return hash of empty content
        assert len(result) == 64
    
    def test_same_glossary_same_hash(self):
        """Verify same content produces same hash."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"test": "value"}')
            temp_path = Path(f.name)
        
        try:
            hash1 = compute_glossary_hash(temp_path)
            hash2 = compute_glossary_hash(temp_path)
            
            assert hash1 == hash2
        finally:
            temp_path.unlink()
    
    def test_different_content_different_hash(self):
        """Verify different content produces different hash."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f1:
            f1.write('{"test": "value1"}')
            temp_path1 = Path(f1.name)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f2:
            f2.write('{"test": "value2"}')
            temp_path2 = Path(f2.name)
        
        try:
            hash1 = compute_glossary_hash(temp_path1)
            hash2 = compute_glossary_hash(temp_path2)
            
            assert hash1 != hash2
        finally:
            temp_path1.unlink()
            temp_path2.unlink()


class TestGetMediaDuration:
    """Test media duration extraction."""
    
    def test_gets_duration_for_valid_media(self):
        """Verify duration extraction works."""
        test_media = Path("in/Energy Demand in AI.mp4")
        
        if not test_media.exists():
            pytest.skip("Test media not available")
        
        duration = _get_media_duration(test_media)
        
        # Should return a positive number
        assert duration is not None
        assert duration > 0
    
    def test_returns_none_for_invalid_file(self):
        """Verify None for invalid media."""
        with tempfile.NamedTemporaryFile(suffix='.mp4') as f:
            # Empty file (invalid media)
            duration = _get_media_duration(Path(f.name))
            
            # Should return None for invalid media
            assert duration is None or duration == 0


class TestMediaIdCaching:
    """Test media ID for caching scenarios."""
    
    def test_same_media_id_enables_caching(self):
        """Verify media ID can be used as cache key."""
        test_media = Path("in/Energy Demand in AI.mp4")
        
        if not test_media.exists():
            pytest.skip("Test media not available")
        
        # Simulate cache lookup
        media_id = compute_media_id(test_media)
        
        # Use as cache key
        cache = {}
        cache[media_id] = {"baseline": "data"}
        
        # Later lookup
        media_id_2 = compute_media_id(test_media)
        
        # Should find cached data
        assert media_id_2 in cache
        assert cache[media_id_2] == {"baseline": "data"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
