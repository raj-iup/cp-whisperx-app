#!/usr/bin/env python3
"""
Unit Tests for Core Pipeline Stages

Tests for stages: 01_demux, 02_tmdb_enrichment, 04_source_separation,
05_pyannote_vad, 06_whisperx_asr, 07_alignment, 08_translation, 10_mux

Phase 2: Testing Infrastructure - Session 2, Task 1
"""

# Standard library
import sys
import importlib
from pathlib import Path
from typing import Callable

# Third-party
import pytest

# Local
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================================
# STAGE 01: DEMUX TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.stage
class TestDemuxStage:
    """Unit tests for 01_demux stage."""
    
    def test_demux_script_exists(self, scripts_dir: Path):
        """Test that demux script exists."""
        demux_script = scripts_dir / "01_demux.py"
        assert demux_script.exists(), "01_demux.py not found"
        assert demux_script.is_file(), "01_demux.py is not a file"
    
    def test_demux_is_executable(self, scripts_dir: Path):
        """Test that demux script is executable."""
        demux_script = scripts_dir / "01_demux.py"
        # Check if it has shebang
        with open(demux_script, 'r') as f:
            first_line = f.readline()
            assert first_line.startswith('#!'), "demux script missing shebang"
    
    def test_demux_imports_correctly(self):
        """Test that demux module imports without errors."""
        try:
            # Note: 01_demux is typically run as script, may not have module interface
            # This test validates the file is importable Python
            import py_compile
            py_compile.compile(str(PROJECT_ROOT / "scripts" / "01_demux.py"), doraise=True)
        except Exception as e:
            pytest.fail(f"01_demux.py has syntax errors: {e}")


# ============================================================================
# STAGE 02: TMDB ENRICHMENT TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.stage
class TestTMDBEnrichmentStage:
    """Unit tests for 02_tmdb_enrichment stage."""
    
    def test_tmdb_enrichment_module_importable(self):
        """Test that TMDB enrichment module can be imported."""
        try:
            module = importlib.import_module("scripts.02_tmdb_enrichment")
            assert module is not None
        except ImportError as e:
            pytest.fail(f"Failed to import 02_tmdb_enrichment: {e}")
    
    def test_tmdb_enrichment_has_run_stage(self):
        """Test that TMDB enrichment has run_stage() function."""
        module = importlib.import_module("scripts.02_tmdb_enrichment")
        assert hasattr(module, "run_stage"), "Missing run_stage() function"
        assert callable(module.run_stage), "run_stage is not callable"
    
    def test_tmdb_enrichment_has_docstring(self):
        """Test that TMDB enrichment module has docstring."""
        module = importlib.import_module("scripts.02_tmdb_enrichment")
        assert module.__doc__ is not None, "Module missing docstring"
        assert len(module.__doc__.strip()) > 0, "Module has empty docstring"


# ============================================================================
# STAGE 04: SOURCE SEPARATION TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.stage
class TestSourceSeparationStage:
    """Unit tests for 04_source_separation stage."""
    
    def test_source_separation_module_importable(self):
        """Test that source separation module can be imported."""
        try:
            module = importlib.import_module("scripts.04_source_separation")
            assert module is not None
        except ImportError as e:
            pytest.fail(f"Failed to import 04_source_separation: {e}")
    
    def test_source_separation_has_run_stage(self):
        """Test that source separation has run_stage() function."""
        module = importlib.import_module("scripts.04_source_separation")
        assert hasattr(module, "run_stage"), "Missing run_stage() function"
        assert callable(module.run_stage), "run_stage is not callable"
    
    def test_source_separation_uses_logger(self):
        """Test that source separation uses logger."""
        script_path = PROJECT_ROOT / "scripts" / "04_source_separation.py"
        content = script_path.read_text()
        assert "from shared.logger import" in content or "import shared.logger" in content, \
            "Should import logger from shared"


# ============================================================================
# STAGE 05: PYANNOTE VAD TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.stage
class TestPyannoteVADStage:
    """Unit tests for 05_pyannote_vad stage."""
    
    def test_pyannote_vad_module_importable(self):
        """Test that PyAnnote VAD module can be imported."""
        try:
            module = importlib.import_module("scripts.05_pyannote_vad")
            assert module is not None
        except ImportError as e:
            pytest.fail(f"Failed to import 05_pyannote_vad: {e}")
    
    def test_pyannote_vad_has_run_stage(self):
        """Test that PyAnnote VAD has run_stage() function."""
        module = importlib.import_module("scripts.05_pyannote_vad")
        assert hasattr(module, "run_stage"), "Missing run_stage() function"
        assert callable(module.run_stage), "run_stage is not callable"
    
    def test_pyannote_vad_has_docstring(self):
        """Test that PyAnnote VAD module has docstring."""
        module = importlib.import_module("scripts.05_pyannote_vad")
        assert module.__doc__ is not None, "Module missing docstring"


# ============================================================================
# STAGE 06: WHISPERX ASR TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.stage
class TestWhisperXASRStage:
    """Unit tests for 06_whisperx_asr stage."""
    
    def test_whisperx_asr_module_importable(self):
        """Test that WhisperX ASR module can be imported."""
        try:
            module = importlib.import_module("scripts.06_whisperx_asr")
            assert module is not None
        except ImportError as e:
            pytest.fail(f"Failed to import 06_whisperx_asr: {e}")
    
    def test_whisperx_asr_has_run_stage(self):
        """Test that WhisperX ASR has run_stage() function."""
        module = importlib.import_module("scripts.06_whisperx_asr")
        assert hasattr(module, "run_stage"), "Missing run_stage() function"
        assert callable(module.run_stage), "run_stage is not callable"
    
    def test_whisperx_asr_uses_logger(self):
        """Test that WhisperX ASR uses logger."""
        script_path = PROJECT_ROOT / "scripts" / "06_whisperx_asr.py"
        content = script_path.read_text()
        assert "from shared.logger import" in content or "import shared.logger" in content, \
            "Should import logger from shared"


# ============================================================================
# STAGE 07: ALIGNMENT TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.stage
class TestAlignmentStage:
    """Unit tests for 07_alignment stage."""
    
    def test_alignment_module_importable(self):
        """Test that alignment module can be imported."""
        try:
            module = importlib.import_module("scripts.07_alignment")
            assert module is not None
        except ImportError as e:
            pytest.fail(f"Failed to import 07_alignment: {e}")
    
    def test_alignment_has_run_stage(self):
        """Test that alignment has run_stage() function."""
        module = importlib.import_module("scripts.07_alignment")
        assert hasattr(module, "run_stage"), "Missing run_stage() function"
        assert callable(module.run_stage), "run_stage is not callable"
    
    def test_alignment_has_docstring(self):
        """Test that alignment module has docstring."""
        module = importlib.import_module("scripts.07_alignment")
        assert module.__doc__ is not None, "Module missing docstring"


# ============================================================================
# STAGE 08: TRANSLATION TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.stage
class TestTranslationStage:
    """Unit tests for 08_translation stage."""
    
    def test_translation_module_importable(self):
        """Test that translation module can be imported."""
        try:
            module = importlib.import_module("scripts.08_translation")
            assert module is not None
        except ImportError as e:
            pytest.fail(f"Failed to import 08_translation: {e}")
    
    def test_translation_has_run_stage(self):
        """Test that translation has run_stage() function."""
        module = importlib.import_module("scripts.08_translation")
        assert hasattr(module, "run_stage"), "Missing run_stage() function"
        assert callable(module.run_stage), "run_stage is not callable"
    
    def test_translation_uses_logger(self):
        """Test that translation uses logger."""
        script_path = PROJECT_ROOT / "scripts" / "08_translation.py"
        content = script_path.read_text()
        assert "from shared.logger import" in content or "import shared.logger" in content, \
            "Should import logger from shared"
    
    def test_translation_has_docstring(self):
        """Test that translation module has comprehensive docstring."""
        module = importlib.import_module("scripts.08_translation")
        assert module.__doc__ is not None, "Module missing docstring"
        assert len(module.__doc__.strip()) > 100, "Docstring should be comprehensive"


# ============================================================================
# STAGE 10: MUX TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.stage
class TestMuxStage:
    """Unit tests for 10_mux stage."""
    
    def test_mux_module_importable(self):
        """Test that mux module can be imported."""
        try:
            module = importlib.import_module("scripts.10_mux")
            assert module is not None
        except ImportError as e:
            pytest.fail(f"Failed to import 10_mux: {e}")
    
    def test_mux_has_run_stage(self):
        """Test that mux has run_stage() function."""
        module = importlib.import_module("scripts.10_mux")
        assert hasattr(module, "run_stage"), "Missing run_stage() function"
        assert callable(module.run_stage), "run_stage is not callable"
    
    def test_mux_has_docstring(self):
        """Test that mux module has docstring."""
        module = importlib.import_module("scripts.10_mux")
        assert module.__doc__ is not None, "Module missing docstring"


# ============================================================================
# ALL STAGES COMPREHENSIVE TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.stage
class TestAllStagesCommon:
    """Common tests for all stage modules."""
    
    ALL_STAGES = [
        "scripts.01_demux",
        "scripts.02_tmdb_enrichment",
        "scripts.04_source_separation",
        "scripts.05_pyannote_vad",
        "scripts.06_whisperx_asr",
        "scripts.07_alignment",
        "scripts.08_translation",
        "scripts.10_mux",
    ]
    
    @pytest.mark.parametrize("module_name", ALL_STAGES)
    def test_stage_file_exists(self, module_name: str):
        """Test that stage file exists."""
        file_name = module_name.split(".")[-1] + ".py"
        file_path = PROJECT_ROOT / "scripts" / file_name
        assert file_path.exists(), f"Stage file {file_name} not found"
    
    @pytest.mark.parametrize("module_name", ALL_STAGES)
    def test_stage_has_no_syntax_errors(self, module_name: str):
        """Test that stage file has no syntax errors."""
        file_name = module_name.split(".")[-1] + ".py"
        file_path = PROJECT_ROOT / "scripts" / file_name
        
        try:
            import py_compile
            py_compile.compile(str(file_path), doraise=True)
        except Exception as e:
            pytest.fail(f"{file_name} has syntax errors: {e}")
    
    @pytest.mark.parametrize("module_name", ALL_STAGES)
    def test_stage_follows_naming_pattern(self, module_name: str):
        """Test that stage follows {NN}_{name}.py naming pattern."""
        import re
        file_name = module_name.split(".")[-1]
        pattern = re.compile(r'^\d{2}_[a-z_]+$')
        assert pattern.match(file_name), \
            f"Stage {file_name} doesn't follow {{NN}}_{{name}} pattern"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
