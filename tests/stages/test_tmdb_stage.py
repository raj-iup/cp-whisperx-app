#!/usr/bin/env python3
"""
Unit Tests for TMDB Enrichment Stage

Tests the TMDB metadata enrichment stage.
Phase 2: Testing Infrastructure - Task 2.2
"""

# Standard library
import sys
from pathlib import Path

# Third-party
import pytest

# Local
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tests.utils.test_helpers import (
    TestJobBuilder,
    assert_stage_completed,
    assert_logs_exist,
    assert_manifest_valid
)


@pytest.mark.stage
@pytest.mark.skip(reason="Stage not fully integrated - Phase 3")
class TestTMDBStage:
    """Unit tests for TMDB enrichment stage."""
    
    @pytest.fixture
    def job_builder(self, tmp_path):
        """Create job builder for tests."""
        builder = TestJobBuilder(base_dir=tmp_path)
        yield builder
        builder.cleanup()
    
    def test_tmdb_stage_creates_output(self, job_builder):
        """Test TMDB stage creates metadata output."""
        job_dir = job_builder.create_job()
        
        # TODO: Run stage when integrated
        # from scripts.tmdb_enrichment_stage import run_stage
        # exit_code = run_stage(job_dir, "02_tmdb")
        # assert exit_code == 0
        
        # Verify output
        # metadata_file = job_dir / "02_tmdb" / "metadata.json"
        # assert metadata_file.exists()
    
    def test_tmdb_stage_handles_missing_api_key(self, job_builder):
        """Test TMDB stage handles missing API key gracefully."""
        job_dir = job_builder.create_job()
        
        # TODO: Test error handling
        pass
    
    def test_tmdb_stage_creates_manifest(self, job_builder):
        """Test TMDB stage creates manifest."""
        job_dir = job_builder.create_job()
        
        # TODO: Run stage and verify manifest
        # from scripts.tmdb_enrichment_stage import run_stage
        # run_stage(job_dir, "02_tmdb")
        # 
        # manifest_path = job_dir / "02_tmdb" / "manifest.json"
        # assert_manifest_valid(manifest_path)
    
    def test_tmdb_stage_creates_log(self, job_builder):
        """Test TMDB stage creates log file."""
        job_dir = job_builder.create_job()
        
        # TODO: Run stage and verify logs
        # from scripts.tmdb_enrichment_stage import run_stage
        # run_stage(job_dir, "02_tmdb")
        # assert_logs_exist(job_dir, "02_tmdb")


@pytest.mark.stage
@pytest.mark.requires_network
@pytest.mark.skip(reason="Requires TMDB API key")
class TestTMDBAPIIntegration:
    """Integration tests for TMDB API."""
    
    def test_tmdb_api_search(self):
        """Test TMDB API search functionality."""
        # TODO: Test actual API calls
        pass
    
    def test_tmdb_api_details(self):
        """Test TMDB API details retrieval."""
        # TODO: Test actual API calls
        pass
