"""
Unit tests for cache manager (AD-014).
"""
import pytest
from pathlib import Path
import tempfile
import shutil
import json
from datetime import datetime
from shared.cache_manager import (
    MediaCacheManager,
    BaselineArtifacts,
    GlossaryResults
)


class TestMediaCacheManager:
    """Test cache manager functionality."""
    
    @pytest.fixture
    def temp_cache(self):
        """Create temporary cache directory."""
        tmpdir = tempfile.mkdtemp()
        yield Path(tmpdir)
        shutil.rmtree(tmpdir)
    
    @pytest.fixture
    def cache_mgr(self, temp_cache):
        """Create cache manager with temp directory."""
        return MediaCacheManager(cache_root=temp_cache)
    
    @pytest.fixture
    def sample_baseline(self, temp_cache):
        """Create sample baseline artifacts."""
        audio_file = temp_cache / "test_audio.wav"
        audio_file.touch()
        
        return BaselineArtifacts(
            media_id="test123",
            audio_file=audio_file,
            segments=[{"text": "Hello"}],
            aligned_segments=[{"text": "Hello", "start": 0, "end": 1}],
            vad_segments=[{"start": 0, "end": 1}],
            diarization={"speaker1": [0, 1]},
            metadata={"duration": 1.0},
            created_at=datetime.now().isoformat()
        )
    
    def test_cache_manager_creates_directory(self, temp_cache):
        """Verify cache directory creation."""
        cache_mgr = MediaCacheManager(cache_root=temp_cache / "cache")
        assert cache_mgr.cache_root.exists()
    
    def test_has_baseline_returns_false_initially(self, cache_mgr):
        """Verify no baseline initially."""
        assert not cache_mgr.has_baseline("test123")
    
    def test_store_and_retrieve_baseline(self, cache_mgr, sample_baseline):
        """Test storing and retrieving baseline."""
        media_id = "test123"
        
        # Store baseline
        success = cache_mgr.store_baseline(media_id, sample_baseline)
        assert success
        
        # Should now exist
        assert cache_mgr.has_baseline(media_id)
        
        # Retrieve baseline
        retrieved = cache_mgr.get_baseline(media_id)
        assert retrieved is not None
        assert retrieved.media_id == media_id
        assert retrieved.segments == sample_baseline.segments
        assert retrieved.aligned_segments == sample_baseline.aligned_segments
    
    def test_clear_baseline(self, cache_mgr, sample_baseline):
        """Test clearing baseline cache."""
        media_id = "test123"
        
        # Store baseline
        cache_mgr.store_baseline(media_id, sample_baseline)
        assert cache_mgr.has_baseline(media_id)
        
        # Clear baseline
        success = cache_mgr.clear_baseline(media_id)
        assert success
        
        # Should no longer exist
        assert not cache_mgr.has_baseline(media_id)
    
    def test_get_baseline_returns_none_if_not_exist(self, cache_mgr):
        """Verify None for non-existent baseline."""
        result = cache_mgr.get_baseline("nonexistent")
        assert result is None


class TestGlossaryCache:
    """Test glossary result caching."""
    
    @pytest.fixture
    def temp_cache(self):
        """Create temporary cache directory."""
        tmpdir = tempfile.mkdtemp()
        yield Path(tmpdir)
        shutil.rmtree(tmpdir)
    
    @pytest.fixture
    def cache_mgr(self, temp_cache):
        """Create cache manager with temp directory."""
        return MediaCacheManager(cache_root=temp_cache)
    
    @pytest.fixture
    def sample_glossary_results(self):
        """Create sample glossary results."""
        return GlossaryResults(
            media_id="test123",
            glossary_hash="abc123",
            applied_segments=[{"text": "Character Name"}],
            quality_metrics={"accuracy": 0.95},
            created_at=datetime.now().isoformat()
        )
    
    def test_has_glossary_results_returns_false_initially(self, cache_mgr):
        """Verify no glossary results initially."""
        assert not cache_mgr.has_glossary_results("test123", "abc123")
    
    def test_store_and_retrieve_glossary_results(
        self,
        cache_mgr,
        sample_glossary_results
    ):
        """Test storing and retrieving glossary results."""
        media_id = "test123"
        glossary_hash = "abc123"
        
        # Store results
        success = cache_mgr.store_glossary_results(
            media_id,
            glossary_hash,
            sample_glossary_results
        )
        assert success
        
        # Should now exist
        assert cache_mgr.has_glossary_results(media_id, glossary_hash)
        
        # Retrieve results
        retrieved = cache_mgr.get_glossary_results(media_id, glossary_hash)
        assert retrieved is not None
        assert retrieved.media_id == media_id
        assert retrieved.glossary_hash == glossary_hash
        assert retrieved.applied_segments == sample_glossary_results.applied_segments
    
    def test_different_glossary_hash_separate_cache(self, cache_mgr, sample_glossary_results):
        """Verify different glossary hashes create separate caches."""
        media_id = "test123"
        
        # Store with hash1
        results1 = sample_glossary_results
        results1.glossary_hash = "hash1"
        cache_mgr.store_glossary_results(media_id, "hash1", results1)
        
        # Store with hash2
        results2 = GlossaryResults(
            media_id=media_id,
            glossary_hash="hash2",
            applied_segments=[{"text": "Different"}],
            quality_metrics={"accuracy": 0.90},
            created_at=datetime.now().isoformat()
        )
        cache_mgr.store_glossary_results(media_id, "hash2", results2)
        
        # Both should exist independently
        assert cache_mgr.has_glossary_results(media_id, "hash1")
        assert cache_mgr.has_glossary_results(media_id, "hash2")
        
        # Retrieve both
        retrieved1 = cache_mgr.get_glossary_results(media_id, "hash1")
        retrieved2 = cache_mgr.get_glossary_results(media_id, "hash2")
        
        assert retrieved1.applied_segments != retrieved2.applied_segments


class TestCacheManagement:
    """Test cache management functions."""
    
    @pytest.fixture
    def temp_cache(self):
        """Create temporary cache directory."""
        tmpdir = tempfile.mkdtemp()
        yield Path(tmpdir)
        shutil.rmtree(tmpdir)
    
    @pytest.fixture
    def cache_mgr(self, temp_cache):
        """Create cache manager with temp directory."""
        return MediaCacheManager(cache_root=temp_cache)
    
    def test_get_cache_size(self, cache_mgr, temp_cache):
        """Test cache size calculation."""
        # Initially empty
        assert cache_mgr.get_cache_size() == 0
        
        # Create some cached files
        media_dir = temp_cache / "media" / "test123" / "baseline"
        media_dir.mkdir(parents=True)
        
        test_file = media_dir / "test.json"
        test_file.write_text('{"test": "data"}')
        
        # Should report size
        size = cache_mgr.get_cache_size()
        assert size > 0
    
    def test_list_cached_media(self, cache_mgr, temp_cache):
        """Test listing cached media."""
        # Initially empty
        assert cache_mgr.list_cached_media() == []
        
        # Create cache for two media
        (temp_cache / "media" / "media1" / "baseline").mkdir(parents=True)
        (temp_cache / "media" / "media2" / "baseline").mkdir(parents=True)
        
        # Should list both
        cached = cache_mgr.list_cached_media()
        assert len(cached) == 2
        assert "media1" in cached
        assert "media2" in cached
    
    def test_clear_all_cache(self, cache_mgr, temp_cache):
        """Test clearing entire cache."""
        # Create some cached data
        media_dir = temp_cache / "media" / "test123" / "baseline"
        media_dir.mkdir(parents=True)
        (media_dir / "test.json").write_text('{"test": "data"}')
        
        # Clear cache
        success = cache_mgr.clear_all_cache()
        assert success
        
        # Should be empty
        assert cache_mgr.list_cached_media() == []


class TestBaselineArtifacts:
    """Test BaselineArtifacts dataclass."""
    
    def test_to_dict_converts_path_to_string(self):
        """Verify Path objects converted to strings."""
        artifacts = BaselineArtifacts(
            media_id="test",
            audio_file=Path("/tmp/audio.wav"),
            segments=[],
            aligned_segments=[],
            vad_segments=[],
            diarization=None,
            metadata={},
            created_at=""
        )
        
        data = artifacts.to_dict()
        assert isinstance(data['audio_file'], str)
    
    def test_from_dict_converts_string_to_path(self):
        """Verify strings converted back to Path objects."""
        data = {
            'media_id': 'test',
            'audio_file': '/tmp/audio.wav',
            'segments': [],
            'aligned_segments': [],
            'vad_segments': [],
            'diarization': None,
            'metadata': {},
            'created_at': ''
        }
        
        artifacts = BaselineArtifacts.from_dict(data)
        assert isinstance(artifacts.audio_file, Path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
