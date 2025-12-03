#!/usr/bin/env python3
"""
Unit Tests for Individual Stage Entry Points

Tests that each renamed stage's run_stage() function works correctly.
Phase 2: Testing Infrastructure - Task 2.1
"""

# Standard library
import sys
import json
import importlib
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Third-party
import pytest

# Local
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================================
# STAGE 03: GLOSSARY LOAD TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.stage
class TestGlossaryLoadStage:
    """Unit tests for 03_glossary_load stage."""
    
    @pytest.fixture
    def mock_job_dir(self, tmp_path: Path) -> Path:
        """Create a mock job directory with minimal structure."""
        job_dir = tmp_path / "test_job"
        job_dir.mkdir()
        
        # Create minimal required directories
        (job_dir / "02_tmdb").mkdir()
        (job_dir / "glossary").mkdir(parents=True, exist_ok=True)
        
        # Create minimal job config
        config_path = job_dir / ".env.pipeline"
        config_path.write_text("STAGE_03_GLOSSARY_ENABLED=true\n")
        
        return job_dir
    
    def test_glossary_load_entry_point_exists(self):
        """Test that glossary_load has run_stage() entry point."""
        module = importlib.import_module("scripts.03_glossary_load")
        assert hasattr(module, "run_stage")
        assert callable(module.run_stage)
    
    @pytest.mark.skip(reason="Phase 3 - Requires full stage implementation")
    def test_glossary_load_creates_output_dir(self, mock_job_dir: Path):
        """Test that glossary_load creates its output directory."""
        module = importlib.import_module("scripts.03_glossary_load")
        
        # Run stage
        exit_code = module.run_stage(mock_job_dir, "03_glossary_load")
        
        # Verify output directory created
        output_dir = mock_job_dir / "03_glossary_load"
        assert output_dir.exists()
    
    @pytest.mark.skip(reason="Phase 3 - Requires full stage implementation")
    def test_glossary_load_returns_exit_code(self, mock_job_dir: Path):
        """Test that glossary_load returns proper exit code."""
        module = importlib.import_module("scripts.03_glossary_load")
        
        exit_code = module.run_stage(mock_job_dir, "03_glossary_load")
        
        assert isinstance(exit_code, int)
        assert exit_code in [0, 1]  # Success or failure


# ============================================================================
# STAGE 05: NER TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.stage
class TestNERStage:
    """Unit tests for 05_ner stage."""
    
    @pytest.fixture
    def mock_job_dir(self, tmp_path: Path) -> Path:
        """Create a mock job directory."""
        job_dir = tmp_path / "test_job"
        job_dir.mkdir()
        
        # Create prerequisite stage output
        (job_dir / "04_asr").mkdir()
        
        # Create minimal config
        config_path = job_dir / ".env.pipeline"
        config_path.write_text("STAGE_05_NER_ENABLED=true\n")
        
        return job_dir
    
    def test_ner_entry_point_exists(self):
        """Test that NER stage has run_stage() entry point."""
        module = importlib.import_module("scripts.05_ner")
        assert hasattr(module, "run_stage")
        assert callable(module.run_stage)
    
    @pytest.mark.skip(reason="Phase 3 - Requires full stage implementation")
    def test_ner_creates_output_dir(self, mock_job_dir: Path):
        """Test that NER stage creates its output directory."""
        module = importlib.import_module("scripts.05_ner")
        
        exit_code = module.run_stage(mock_job_dir, "05_ner")
        
        output_dir = mock_job_dir / "05_ner"
        assert output_dir.exists()


# ============================================================================
# STAGE 06: LYRICS DETECTION TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.stage
class TestLyricsDetectionStage:
    """Unit tests for 06_lyrics_detection stage."""
    
    @pytest.fixture
    def mock_job_dir(self, tmp_path: Path) -> Path:
        """Create a mock job directory."""
        job_dir = tmp_path / "test_job"
        job_dir.mkdir()
        
        # Create prerequisite directories
        (job_dir / "01_demux").mkdir()
        
        # Create minimal config
        config_path = job_dir / ".env.pipeline"
        config_path.write_text("STAGE_06_LYRICS_ENABLED=true\n")
        
        return job_dir
    
    def test_lyrics_detection_entry_point_exists(self):
        """Test that lyrics_detection has run_stage() entry point."""
        module = importlib.import_module("scripts.06_lyrics_detection")
        assert hasattr(module, "run_stage")
        assert callable(module.run_stage)
    
    @pytest.mark.skip(reason="Phase 3 - Requires full stage implementation")
    def test_lyrics_detection_creates_output_dir(self, mock_job_dir: Path):
        """Test that lyrics_detection creates its output directory."""
        module = importlib.import_module("scripts.06_lyrics_detection")
        
        exit_code = module.run_stage(mock_job_dir, "06_lyrics_detection")
        
        output_dir = mock_job_dir / "06_lyrics_detection"
        assert output_dir.exists()


# ============================================================================
# STAGE 07: HALLUCINATION REMOVAL TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.stage
class TestHallucinationRemovalStage:
    """Unit tests for 07_hallucination_removal stage."""
    
    @pytest.fixture
    def mock_job_dir(self, tmp_path: Path) -> Path:
        """Create a mock job directory."""
        job_dir = tmp_path / "test_job"
        job_dir.mkdir()
        
        # Create prerequisite directories
        (job_dir / "06_asr").mkdir()
        
        # Create minimal transcript
        transcript_file = job_dir / "06_asr" / "transcript.json"
        transcript_file.write_text('{"segments": []}')
        
        # Create minimal config
        config_path = job_dir / ".env.pipeline"
        config_path.write_text("STAGE_07_HALLUCINATION_ENABLED=true\n")
        
        return job_dir
    
    def test_hallucination_removal_entry_point_exists(self):
        """Test that hallucination_removal has run_stage() entry point."""
        module = importlib.import_module("scripts.07_hallucination_removal")
        assert hasattr(module, "run_stage")
        assert callable(module.run_stage)
    
    @pytest.mark.skip(reason="Phase 3 - Requires full stage implementation")
    def test_hallucination_removal_creates_output_dir(self, mock_job_dir: Path):
        """Test that hallucination_removal creates its output directory."""
        module = importlib.import_module("scripts.07_hallucination_removal")
        
        exit_code = module.run_stage(mock_job_dir, "07_hallucination_removal")
        
        output_dir = mock_job_dir / "07_hallucination_removal"
        assert output_dir.exists()


# ============================================================================
# STAGE 09: SUBTITLE GEN TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.stage
class TestSubtitleGenStage:
    """Unit tests for 09_subtitle_gen stage."""
    
    @pytest.fixture
    def mock_job_dir(self, tmp_path: Path) -> Path:
        """Create a mock job directory."""
        job_dir = tmp_path / "test_job"
        job_dir.mkdir()
        
        # Create prerequisite directories
        (job_dir / "08_translate").mkdir()
        
        # Create minimal translation output
        translation_file = job_dir / "08_translate" / "translation_en.json"
        translation_file.write_text('{"segments": []}')
        
        # Create minimal config
        config_path = job_dir / ".env.pipeline"
        config_path.write_text("STAGE_09_SUBTITLE_ENABLED=true\n")
        
        return job_dir
    
    def test_subtitle_gen_entry_point_exists(self):
        """Test that subtitle_gen has run_stage() entry point."""
        module = importlib.import_module("scripts.09_subtitle_gen")
        assert hasattr(module, "run_stage")
        assert callable(module.run_stage)
    
    @pytest.mark.skip(reason="Phase 3 - Requires full stage implementation")
    def test_subtitle_gen_creates_output_dir(self, mock_job_dir: Path):
        """Test that subtitle_gen creates its output directory."""
        module = importlib.import_module("scripts.09_subtitle_gen")
        
        exit_code = module.run_stage(mock_job_dir, "09_subtitle_gen")
        
        output_dir = mock_job_dir / "09_subtitle_gen"
        assert output_dir.exists()


# ============================================================================
# STAGE ERROR HANDLING TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.stage
class TestStageErrorHandling:
    """Test that stages handle errors gracefully."""
    
    RENAMED_STAGES = [
        "scripts.03_glossary_load",
        "scripts.05_ner",
        "scripts.06_lyrics_detection",
        "scripts.07_hallucination_removal",
        "scripts.09_subtitle_gen",
    ]
    
    @pytest.mark.skip(reason="Phase 3 - Requires full error handling implementation")
    @pytest.mark.parametrize("module_name", RENAMED_STAGES)
    def test_stage_handles_missing_job_dir(self, module_name: str, tmp_path: Path):
        """Test that stage handles missing job directory gracefully."""
        module = importlib.import_module(module_name)
        
        # Use non-existent job directory
        fake_job_dir = tmp_path / "nonexistent"
        
        # Should return error code, not crash
        exit_code = module.run_stage(fake_job_dir, module_name.split(".")[-1])
        
        assert isinstance(exit_code, int)
        assert exit_code != 0  # Should indicate failure
    
    @pytest.mark.skip(reason="Phase 3 - Requires full error handling implementation")
    @pytest.mark.parametrize("module_name", RENAMED_STAGES)
    def test_stage_handles_missing_prerequisites(self, module_name: str, tmp_path: Path):
        """Test that stage handles missing prerequisite stages gracefully."""
        module = importlib.import_module(module_name)
        
        # Create job dir but no prerequisite stages
        job_dir = tmp_path / "test_job"
        job_dir.mkdir()
        
        # Should return error code or skip gracefully
        exit_code = module.run_stage(job_dir, module_name.split(".")[-1])
        
        assert isinstance(exit_code, int)


# ============================================================================
# STAGE MANIFEST TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.stage
@pytest.mark.skip(reason="Phase 3 - Requires full StageIO implementation")
class TestStageManifests:
    """Test that stages create proper manifests."""
    
    RENAMED_STAGES = [
        "scripts.03_glossary_load",
        "scripts.05_ner",
        "scripts.06_lyrics_detection",
        "scripts.07_hallucination_removal",
        "scripts.09_subtitle_gen",
    ]
    
    @pytest.mark.parametrize("module_name", RENAMED_STAGES)
    def test_stage_creates_manifest(self, module_name: str, tmp_path: Path):
        """Test that stage creates manifest.json."""
        module = importlib.import_module(module_name)
        stage_name = module_name.split(".")[-1]
        
        # Create minimal job dir
        job_dir = tmp_path / "test_job"
        job_dir.mkdir()
        
        # Run stage
        exit_code = module.run_stage(job_dir, stage_name)
        
        # Check manifest exists
        manifest_path = job_dir / stage_name / "manifest.json"
        assert manifest_path.exists(), f"Stage {stage_name} did not create manifest"
        
        # Validate manifest structure
        with open(manifest_path) as f:
            manifest = json.load(f)
        
        assert "stage_name" in manifest
        assert "inputs" in manifest
        assert "outputs" in manifest
        assert "exit_code" in manifest


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
