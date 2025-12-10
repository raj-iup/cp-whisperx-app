#!/usr/bin/env python3
"""
Unit tests for Online Media Downloader.

Tests:
- URL detection
- YouTube URL validation
- Video ID extraction
- Filename sanitization
- Format selector logic
- Cache checking

Coverage target: ≥80%
Related: TRD-2025-12-10-02-online-media-integration
"""

# Standard library
import shutil
import tempfile
from pathlib import Path

# Third-party
import pytest

# Local
from shared.online_downloader import OnlineMediaDownloader, is_online_url


class TestURLDetection:
    """Test URL vs local path detection."""
    
    def test_is_online_url_youtube(self):
        """Test YouTube URL detection."""
        assert is_online_url("https://youtube.com/watch?v=VIDEO_ID")
        assert is_online_url("https://www.youtube.com/watch?v=VIDEO_ID")
        assert is_online_url("https://youtu.be/VIDEO_ID")
    
    def test_is_online_url_other_platforms(self):
        """Test other platform URL detection."""
        assert is_online_url("https://vimeo.com/12345")
        assert is_online_url("https://dailymotion.com/video/x12345")
    
    def test_is_online_url_local_paths(self):
        """Test local path detection."""
        assert not is_online_url("in/movie.mp4")
        assert not is_online_url("/absolute/path/to/video.mp4")
        assert not is_online_url("relative/path/video.mp4")
        assert not is_online_url("C:\\Users\\Videos\\movie.mp4")
    
    def test_is_online_url_edge_cases(self):
        """Test edge cases."""
        assert not is_online_url("")
        assert not is_online_url("just_filename.mp4")


class TestYouTubeValidation:
    """Test YouTube-specific validation."""
    
    @pytest.fixture
    def downloader(self):
        """Create downloader instance."""
        temp_dir = Path(tempfile.mkdtemp())
        yield OnlineMediaDownloader(cache_dir=temp_dir)
        shutil.rmtree(temp_dir)
    
    def test_is_youtube_url_standard(self, downloader):
        """Test standard YouTube URLs."""
        assert downloader.is_youtube_url("https://youtube.com/watch?v=VIDEO_ID")
        assert downloader.is_youtube_url("https://www.youtube.com/watch?v=VIDEO_ID")
        assert downloader.is_youtube_url("http://youtube.com/watch?v=VIDEO_ID")
    
    def test_is_youtube_url_short(self, downloader):
        """Test shortened YouTube URLs."""
        assert downloader.is_youtube_url("https://youtu.be/VIDEO_ID")
        assert downloader.is_youtube_url("http://youtu.be/VIDEO_ID")
    
    def test_is_youtube_url_embed(self, downloader):
        """Test embed YouTube URLs."""
        assert downloader.is_youtube_url("https://youtube.com/embed/VIDEO_ID")
        assert downloader.is_youtube_url("https://www.youtube.com/v/VIDEO_ID")
    
    def test_is_youtube_url_not_youtube(self, downloader):
        """Test non-YouTube URLs."""
        assert not downloader.is_youtube_url("https://vimeo.com/12345")
        assert not downloader.is_youtube_url("https://dailymotion.com/video/x12345")
        assert not downloader.is_youtube_url("https://example.com")


class TestVideoIDExtraction:
    """Test video ID extraction."""
    
    @pytest.fixture
    def downloader(self):
        """Create downloader instance."""
        temp_dir = Path(tempfile.mkdtemp())
        yield OnlineMediaDownloader(cache_dir=temp_dir)
        shutil.rmtree(temp_dir)
    
    def test_extract_video_id_standard(self, downloader):
        """Test standard YouTube URL."""
        video_id = downloader.extract_video_id("https://youtube.com/watch?v=dQw4w9WgXcQ")
        assert video_id == "dQw4w9WgXcQ"
    
    def test_extract_video_id_short(self, downloader):
        """Test shortened YouTube URL."""
        video_id = downloader.extract_video_id("https://youtu.be/dQw4w9WgXcQ")
        assert video_id == "dQw4w9WgXcQ"
    
    def test_extract_video_id_embed(self, downloader):
        """Test embed YouTube URL."""
        video_id = downloader.extract_video_id("https://youtube.com/embed/dQw4w9WgXcQ")
        assert video_id == "dQw4w9WgXcQ"
    
    def test_extract_video_id_v_format(self, downloader):
        """Test /v/ format YouTube URL."""
        video_id = downloader.extract_video_id("https://youtube.com/v/dQw4w9WgXcQ")
        assert video_id == "dQw4w9WgXcQ"
    
    def test_extract_video_id_invalid(self, downloader):
        """Test invalid URL."""
        video_id = downloader.extract_video_id("https://example.com")
        assert video_id is None


class TestFilenameSanitization:
    """Test filename sanitization."""
    
    @pytest.fixture
    def downloader(self):
        """Create downloader instance."""
        temp_dir = Path(tempfile.mkdtemp())
        yield OnlineMediaDownloader(cache_dir=temp_dir)
        shutil.rmtree(temp_dir)
    
    def test_sanitize_filename_special_chars(self, downloader):
        """Test removal of special characters."""
        result = downloader.sanitize_filename('Video: Title! (2024)')
        assert '<' not in result
        assert '>' not in result
        assert ':' not in result
        assert '"' not in result
        assert '/' not in result
        assert '\\' not in result
        assert '|' not in result
        assert '?' not in result
        assert '*' not in result
    
    def test_sanitize_filename_spaces(self, downloader):
        """Test space replacement."""
        result = downloader.sanitize_filename('Hello World Test')
        assert ' ' not in result
        assert '_' in result
    
    def test_sanitize_filename_multiple_underscores(self, downloader):
        """Test multiple underscore removal."""
        result = downloader.sanitize_filename('Hello___World___Test')
        # Should not have triple underscores
        assert '___' not in result
    
    def test_sanitize_filename_length_truncation(self, downloader):
        """Test long filename truncation."""
        long_name = 'A' * 300
        result = downloader.sanitize_filename(long_name)
        assert len(result) <= 240


class TestFormatSelector:
    """Test format selector logic."""
    
    @pytest.fixture
    def downloader(self):
        """Create downloader instance."""
        temp_dir = Path(tempfile.mkdtemp())
        yield OnlineMediaDownloader(cache_dir=temp_dir)
        shutil.rmtree(temp_dir)
    
    def test_format_selector_best(self, downloader):
        """Test 'best' quality selector."""
        downloader.format_quality = 'best'
        selector = downloader._get_format_selector()
        assert 'bestvideo+bestaudio' in selector
    
    def test_format_selector_1080p(self, downloader):
        """Test 1080p quality selector."""
        downloader.format_quality = '1080p'
        selector = downloader._get_format_selector()
        assert '1080' in selector
    
    def test_format_selector_720p(self, downloader):
        """Test 720p quality selector."""
        downloader.format_quality = '720p'
        selector = downloader._get_format_selector()
        assert '720' in selector
    
    def test_format_selector_480p(self, downloader):
        """Test 480p quality selector."""
        downloader.format_quality = '480p'
        selector = downloader._get_format_selector()
        assert '480' in selector
    
    def test_format_selector_audio_only(self, downloader):
        """Test audio-only selector."""
        downloader.audio_only = True
        selector = downloader._get_format_selector()
        assert 'bestaudio' in selector
    
    def test_format_selector_audio_quality(self, downloader):
        """Test 'audio' quality selector."""
        downloader.format_quality = 'audio'
        selector = downloader._get_format_selector()
        assert 'bestaudio' in selector


class TestCacheManagement:
    """Test cache management."""
    
    @pytest.fixture
    def temp_cache(self):
        """Create temporary cache directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_get_cached_video_exists(self, temp_cache):
        """Test finding cached video."""
        # Create dummy cached file
        video_id = "dQw4w9WgXcQ"
        cached_file = temp_cache / f"{video_id}.mp4"
        cached_file.touch()
        
        downloader = OnlineMediaDownloader(cache_dir=temp_cache)
        result = downloader.get_cached_video(video_id)
        
        assert result is not None
        assert result == cached_file
    
    def test_get_cached_video_not_exists(self, temp_cache):
        """Test cache miss."""
        downloader = OnlineMediaDownloader(cache_dir=temp_cache)
        result = downloader.get_cached_video("nonexistent_video_id")
        
        assert result is None
    
    def test_get_cached_video_multiple_extensions(self, temp_cache):
        """Test finding cached video with different extensions."""
        # Create dummy cached files with different extensions
        video_id = "dQw4w9WgXcQ"
        (temp_cache / f"{video_id}.mp4").touch()
        (temp_cache / f"{video_id}.mkv").touch()
        
        downloader = OnlineMediaDownloader(cache_dir=temp_cache)
        result = downloader.get_cached_video(video_id)
        
        # Should find at least one
        assert result is not None
        assert str(result).startswith(str(temp_cache / video_id))


class TestDownloadValidation:
    """Test download validation (without actual downloads)."""
    
    @pytest.fixture
    def downloader(self):
        """Create downloader instance."""
        temp_dir = Path(tempfile.mkdtemp())
        yield OnlineMediaDownloader(cache_dir=temp_dir)
        shutil.rmtree(temp_dir)
    
    def test_download_invalid_url(self, downloader):
        """Test download with invalid URL."""
        with pytest.raises(ValueError, match="Not a valid URL"):
            downloader.download("not_a_url.mp4")
    
    def test_download_non_youtube_phase1(self, downloader):
        """Test download with non-YouTube URL (Phase 1)."""
        with pytest.raises(ValueError, match="Only YouTube URLs supported"):
            downloader.download("https://vimeo.com/12345")
    
    def test_download_invalid_youtube_url(self, downloader):
        """Test download with invalid YouTube URL."""
        # youtube.com/invalid doesn't match YouTube URL pattern, so it fails Phase 1 check first
        with pytest.raises(ValueError, match="Only YouTube URLs supported"):
            downloader.download("https://youtube.com/invalid")


class TestIntegration:
    """Integration tests."""
    
    def test_downloader_initialization(self):
        """Test downloader initialization."""
        temp_dir = Path(tempfile.mkdtemp())
        try:
            downloader = OnlineMediaDownloader(
                cache_dir=temp_dir,
                format_quality="720p",
                audio_only=False
            )
            
            assert downloader.cache_dir == temp_dir
            assert downloader.format_quality == "720p"
            assert downloader.audio_only == False
            assert temp_dir.exists()
        finally:
            shutil.rmtree(temp_dir)
    
    def test_downloader_creates_cache_dir(self):
        """Test cache directory creation."""
        temp_dir = Path(tempfile.mkdtemp())
        cache_dir = temp_dir / "online_cache"
        
        try:
            downloader = OnlineMediaDownloader(cache_dir=cache_dir)
            assert cache_dir.exists()
        finally:
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
