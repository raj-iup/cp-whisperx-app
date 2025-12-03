#!/usr/bin/env python3
"""
Test TMDB Stage Integration - Task 4.1

Tests the run_stage() wrapper function for TMDB enrichment stage.
"""

# Standard library
import sys
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Third-party
import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestTMDBStageIntegration:
    """Test TMDB stage integration with pipeline"""
    
    def test_run_stage_function_exists(self) -> None:
        """Test that run_stage() function exists"""
        # Import with mocking to avoid dependency issues
        with patch('shared.tmdb_client.TMDBClient'):
            from scripts.tmdb_enrichment_stage import run_stage
            assert callable(run_stage)
    
    def test_run_stage_signature(self) -> None:
        """Test run_stage() has correct signature"""
        with patch('shared.tmdb_client.TMDBClient'):
            from scripts.tmdb_enrichment_stage import run_stage
            import inspect
            sig = inspect.signature(run_stage)
            
            # Check parameters
            assert 'job_dir' in sig.parameters
            assert 'stage_name' in sig.parameters
            
            # Check default value
            assert sig.parameters['stage_name'].default == "02_tmdb"
            
            # Check return type
            assert sig.return_annotation == int
    
    def test_tmdb_class_exists(self) -> None:
        """Test that TMDBEnrichmentStage class exists"""
        with patch('shared.tmdb_client.TMDBClient'):
            from scripts.tmdb_enrichment_stage import TMDBEnrichmentStage
            assert TMDBEnrichmentStage is not None
    
    @patch('scripts.tmdb_enrichment_stage.load_config')
    @patch('scripts.tmdb_enrichment_stage.StageIO')
    @patch('scripts.tmdb_enrichment_stage.TMDBEnrichmentStage')
    def test_run_stage_creates_stage_io(self, mock_stage_class: Mock, mock_stageio: Mock, mock_config: Mock, tmp_path: Path) -> None:
        """Test that run_stage creates StageIO with manifest enabled"""
        # Setup
        mock_config.return_value = Mock(get=Mock(return_value=None))
        mock_io_instance = MagicMock()
        mock_stageio.return_value = mock_io_instance
        mock_stage_instance = MagicMock()
        mock_stage_instance.run.return_value = True
        mock_stage_class.return_value = mock_stage_instance
        
        # Execute
        from scripts.tmdb_enrichment_stage import run_stage
        result = run_stage(tmp_path, "02_tmdb")
        
        # Verify
        mock_stageio.assert_called_once_with("02_tmdb", tmp_path, enable_manifest=True)
        assert result == 0
    
    @patch('scripts.tmdb_enrichment_stage.load_config')
    @patch('scripts.tmdb_enrichment_stage.StageIO')
    @patch('scripts.tmdb_enrichment_stage.TMDBEnrichmentStage')
    def test_run_stage_loads_config(self, mock_stage_class: Mock, mock_stageio: Mock, mock_config: Mock, tmp_path: Path) -> None:
        """Test that run_stage loads config for title and year"""
        # Setup
        mock_cfg = Mock()
        mock_cfg.get = Mock(side_effect=lambda k: {
            "FILM_TITLE": "Test Movie",
            "FILM_YEAR": "2020"
        }.get(k))
        mock_config.return_value = mock_cfg
        
        mock_io_instance = MagicMock()
        mock_stageio.return_value = mock_io_instance
        mock_stage_instance = MagicMock()
        mock_stage_instance.run.return_value = True
        mock_stage_class.return_value = mock_stage_instance
        
        # Execute
        from scripts.tmdb_enrichment_stage import run_stage
        result = run_stage(tmp_path)
        
        # Verify config was loaded
        mock_config.assert_called_once()
        mock_cfg.get.assert_any_call("FILM_TITLE")
        mock_cfg.get.assert_any_call("FILM_YEAR")
        
        # Verify stage was created with config values
        mock_stage_class.assert_called_once()
        call_kwargs = mock_stage_class.call_args[1]
        assert call_kwargs['title'] == "Test Movie"
        assert call_kwargs['year'] == 2020
    
    @patch('scripts.tmdb_enrichment_stage.load_config')
    @patch('scripts.tmdb_enrichment_stage.StageIO')
    @patch('scripts.tmdb_enrichment_stage.TMDBEnrichmentStage')
    def test_run_stage_returns_success(self, mock_stage_class: Mock, mock_stageio: Mock, mock_config: Mock, tmp_path: Path) -> None:
        """Test run_stage returns 0 on success"""
        # Setup
        mock_config.return_value = Mock(get=Mock(return_value=None))
        mock_io_instance = MagicMock()
        mock_stageio.return_value = mock_io_instance
        mock_stage_instance = MagicMock()
        mock_stage_instance.run.return_value = True
        mock_stage_class.return_value = mock_stage_instance
        
        # Execute
        from scripts.tmdb_enrichment_stage import run_stage
        result = run_stage(tmp_path)
        
        # Verify
        assert result == 0
    
    @patch('scripts.tmdb_enrichment_stage.load_config')
    @patch('scripts.tmdb_enrichment_stage.StageIO')
    @patch('scripts.tmdb_enrichment_stage.TMDBEnrichmentStage')
    def test_run_stage_returns_failure(self, mock_stage_class: Mock, mock_stageio: Mock, mock_config: Mock, tmp_path: Path) -> None:
        """Test run_stage returns 1 on failure"""
        # Setup
        mock_config.return_value = Mock(get=Mock(return_value=None))
        mock_io_instance = MagicMock()
        mock_stageio.return_value = mock_io_instance
        mock_stage_instance = MagicMock()
        mock_stage_instance.run.return_value = False
        mock_stage_class.return_value = mock_stage_instance
        
        # Execute
        from scripts.tmdb_enrichment_stage import run_stage
        result = run_stage(tmp_path)
        
        # Verify
        assert result == 1
    
    @patch('scripts.tmdb_enrichment_stage.load_config')
    @patch('scripts.tmdb_enrichment_stage.StageIO')
    def test_run_stage_handles_exceptions(self, mock_stageio: Mock, mock_config: Mock, tmp_path: Path) -> None:
        """Test run_stage handles exceptions gracefully"""
        # Setup - force an exception
        mock_config.side_effect = ValueError("Config error")
        mock_io_instance = MagicMock()
        mock_stageio.return_value = mock_io_instance
        
        # Execute
        from scripts.tmdb_enrichment_stage import run_stage
        result = run_stage(tmp_path)
        
        # Verify
        assert result == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
