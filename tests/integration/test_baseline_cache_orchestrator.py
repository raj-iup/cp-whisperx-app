#!/usr/bin/env python3
"""
Integration tests for BaselineCacheOrchestrator (AD-014).

Tests the complete cache workflow integration.
"""
# Standard library
import sys
from pathlib import Path
import json
import tempfile
import subprocess
from datetime import datetime

# Add project root to path
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pytest

# Local
from shared.baseline_cache_orchestrator import BaselineCacheOrchestrator
from shared.cache_manager import MediaCacheManager
from shared.media_identity import compute_media_id


@pytest.fixture
def job_dir(tmp_path):
    """Create a temporary job directory with stage subdirectories."""
    job = tmp_path / "job-test-001"
    job.mkdir()
    
    # Create stage directories
    for stage in ["01_demux", "05_vad", "06_asr", "07_alignment"]:
        (job / stage).mkdir()
    
    return job


@pytest.fixture
def test_media_file(tmp_path):
    """Create a test media file using FFmpeg."""
    media_file = tmp_path / "test_media.mp4"
    
    # Generate 5 seconds of test video with audio
    cmd = [
        'ffmpeg', '-y',
        '-f', 'lavfi', '-i', 'testsrc=duration=5:size=320x240:rate=1',
        '-f', 'lavfi', '-i', 'sine=frequency=1000:duration=5',
        '-pix_fmt', 'yuv420p',
        str(media_file)
    ]
    
    try:
        subprocess.run(cmd, capture_output=True, check=True, timeout=15)
        return media_file
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        pytest.skip("FFmpeg not available or failed")


@pytest.fixture
def populated_job_dir(job_dir):
    """Create a job directory with baseline artifacts."""
    # Audio file
    audio_file = job_dir / "01_demux" / "audio.wav"
    audio_file.write_text("dummy audio")
    
    # VAD segments
    vad_file = job_dir / "05_vad" / "vad_segments.json"
    vad_segments = [{"start": 0.0, "end": 5.0}]
    with open(vad_file, 'w') as f:
        json.dump(vad_segments, f)
    
    # ASR segments
    segments_file = job_dir / "06_asr" / "segments.json"
    segments = [
        {"start": 0.0, "end": 1.0, "text": "Test segment 1"},
        {"start": 1.0, "end": 2.0, "text": "Test segment 2"}
    ]
    with open(segments_file, 'w') as f:
        json.dump(segments, f)
    
    # Aligned segments
    aligned_file = job_dir / "07_alignment" / "aligned_segments.json"
    aligned_segments = [
        {"start": 0.0, "end": 1.0, "text": "Test segment 1", "words": []},
        {"start": 1.0, "end": 2.0, "text": "Test segment 2", "words": []}
    ]
    with open(aligned_file, 'w') as f:
        json.dump(aligned_segments, f)
    
    return job_dir


class TestBaselineCacheOrchestrator:
    """Test BaselineCacheOrchestrator basic operations."""
    
    def test_init_enabled(self, job_dir, tmp_path):
        """Test initialization with caching enabled."""
        orchestrator = BaselineCacheOrchestrator(job_dir, enabled=True)
        
        assert orchestrator.enabled
        assert orchestrator.job_dir == job_dir
    
    def test_init_disabled(self, job_dir):
        """Test initialization with caching disabled."""
        orchestrator = BaselineCacheOrchestrator(job_dir, enabled=False)
        
        assert not orchestrator.enabled
    
    def test_init_skip_cache(self, job_dir):
        """Test initialization with skip_cache flag."""
        orchestrator = BaselineCacheOrchestrator(
            job_dir, enabled=True, skip_cache=True
        )
        
        assert not orchestrator.enabled  # skip_cache disables caching


class TestCacheRestoration:
    """Test cache restoration workflow."""
    
    def test_try_restore_from_cache_disabled(self, job_dir, test_media_file):
        """Test that restoration is skipped when caching disabled."""
        orchestrator = BaselineCacheOrchestrator(job_dir, enabled=False)
        
        result = orchestrator.try_restore_from_cache(test_media_file)
        
        assert not result  # Should return False when disabled
    
    def test_try_restore_from_cache_no_cache(self, job_dir, test_media_file, tmp_path):
        """Test restoration when no cache exists."""
        # Use temporary cache directory
        orchestrator = BaselineCacheOrchestrator(job_dir, enabled=True)
        orchestrator.cache_integration.cache_mgr = MediaCacheManager(tmp_path / "cache")
        
        result = orchestrator.try_restore_from_cache(test_media_file)
        
        assert not result  # Should return False when no cache
    
    def test_store_baseline_to_cache_disabled(self, populated_job_dir, test_media_file):
        """Test that storage is skipped when caching disabled."""
        orchestrator = BaselineCacheOrchestrator(populated_job_dir, enabled=False)
        
        result = orchestrator.store_baseline_to_cache(test_media_file)
        
        assert not result  # Should return False when disabled
    
    def test_store_baseline_to_cache_success(self, populated_job_dir, test_media_file, tmp_path):
        """Test storing baseline to cache."""
        # Use temporary cache directory
        cache_dir = tmp_path / "cache"
        orchestrator = BaselineCacheOrchestrator(populated_job_dir, enabled=True)
        orchestrator.cache_integration.cache_mgr = MediaCacheManager(cache_dir)
        
        result = orchestrator.store_baseline_to_cache(test_media_file)
        
        assert result  # Should return True on success
        
        # Verify cache was created
        media_id = compute_media_id(test_media_file)
        cache_mgr = MediaCacheManager(cache_dir)
        assert cache_mgr.has_baseline(media_id)


class TestFullCacheWorkflow:
    """Test complete cache workflow (store and restore)."""
    
    def test_full_workflow(self, populated_job_dir, test_media_file, tmp_path):
        """Test storing and then restoring from cache."""
        cache_dir = tmp_path / "cache"
        
        # First run - store in cache
        orchestrator1 = BaselineCacheOrchestrator(populated_job_dir, enabled=True)
        orchestrator1.cache_integration.cache_mgr = MediaCacheManager(cache_dir)
        
        store_result = orchestrator1.store_baseline_to_cache(test_media_file)
        assert store_result
        
        # Create new job directory for second run
        job_dir2 = tmp_path / "job-test-002"
        job_dir2.mkdir()
        for stage in ["01_demux", "05_vad", "06_asr", "07_alignment"]:
            (job_dir2 / stage).mkdir()
        
        # Second run - restore from cache
        orchestrator2 = BaselineCacheOrchestrator(job_dir2, enabled=True)
        orchestrator2.cache_integration.cache_mgr = MediaCacheManager(cache_dir)
        
        restore_result = orchestrator2.try_restore_from_cache(test_media_file)
        assert restore_result
        
        # Verify artifacts were restored
        assert (job_dir2 / "01_demux" / "audio.wav").exists()
        assert (job_dir2 / "05_vad" / "vad_segments.json").exists()
        assert (job_dir2 / "06_asr" / "segments.json").exists()
        assert (job_dir2 / "07_alignment" / "aligned_segments.json").exists()


class TestCacheInvalidation:
    """Test cache invalidation operations."""
    
    def test_invalidate_cache(self, populated_job_dir, test_media_file, tmp_path):
        """Test invalidating cache for specific media."""
        cache_dir = tmp_path / "cache"
        
        # Store baseline in cache
        orchestrator = BaselineCacheOrchestrator(populated_job_dir, enabled=True)
        orchestrator.cache_integration.cache_mgr = MediaCacheManager(cache_dir)
        orchestrator.store_baseline_to_cache(test_media_file)
        
        # Verify cache exists
        media_id = compute_media_id(test_media_file)
        cache_mgr = MediaCacheManager(cache_dir)
        assert cache_mgr.has_baseline(media_id)
        
        # Invalidate cache
        result = orchestrator.invalidate_cache(test_media_file)
        assert result
        
        # Verify cache was cleared
        assert not cache_mgr.has_baseline(media_id)
    
    def test_get_cache_info(self, job_dir):
        """Test getting cache information."""
        orchestrator = BaselineCacheOrchestrator(job_dir, enabled=True)
        
        info = orchestrator.get_cache_info()
        
        assert isinstance(info, dict)
        assert 'enabled' in info


class TestErrorHandling:
    """Test error handling in cache operations."""
    
    def test_gather_baseline_missing_audio(self, job_dir):
        """Test gathering baseline when audio file is missing."""
        orchestrator = BaselineCacheOrchestrator(job_dir, enabled=True)
        
        # Create stage directories but no audio file
        result = orchestrator._gather_baseline_artifacts()
        
        assert result is None  # Should return None when artifacts missing
    
    def test_restore_cache_corrupted(self, job_dir, test_media_file, tmp_path):
        """Test restoration with corrupted cache."""
        cache_dir = tmp_path / "cache"
        cache_mgr = MediaCacheManager(cache_dir)
        
        # Create corrupted cache (metadata file without actual data)
        media_id = compute_media_id(test_media_file)
        baseline_dir = cache_dir / "media" / media_id / "baseline"
        baseline_dir.mkdir(parents=True, exist_ok=True)
        
        # Write corrupted metadata
        with open(baseline_dir / "metadata.json", 'w') as f:
            f.write("{}")  # Empty metadata
        
        # Try to restore
        orchestrator = BaselineCacheOrchestrator(job_dir, enabled=True)
        orchestrator.cache_integration.cache_mgr = cache_mgr
        
        result = orchestrator.try_restore_from_cache(test_media_file)
        
        assert not result  # Should return False with corrupted cache


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
