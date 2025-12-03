#!/usr/bin/env python3
"""
Unit Tests for Phase 1 Renamed Stage Modules

Tests that all renamed stage modules can be imported and have correct entry points.
Phase 2: Testing Infrastructure - Task 2.1
"""

# Standard library
import sys
import importlib
from pathlib import Path
from typing import Callable

# Third-party
import pytest

# Local
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================================
# STAGE MODULE IMPORT TESTS
# ============================================================================

@pytest.mark.unit
class TestPhase1RenamedStages:
    """Test that all Phase 1 renamed stages can be imported and have run_stage()."""
    
    RENAMED_STAGES = [
        ("scripts.03_glossary_load", "03_glossary_load"),
        ("scripts.05_ner", "05_ner"),
        ("scripts.06_lyrics_detection", "06_lyrics_detection"),
        ("scripts.07_hallucination_removal", "07_hallucination_removal"),
        ("scripts.09_subtitle_gen", "09_subtitle_gen"),
    ]
    
    @pytest.mark.parametrize("module_name,stage_name", RENAMED_STAGES)
    def test_stage_module_importable(self, module_name: str, stage_name: str):
        """Test that stage module can be imported via importlib."""
        try:
            module = importlib.import_module(module_name)
            assert module is not None, f"Module {module_name} imported as None"
        except ImportError as e:
            pytest.fail(f"Failed to import {module_name}: {e}")
    
    @pytest.mark.parametrize("module_name,stage_name", RENAMED_STAGES)
    def test_stage_has_run_stage_function(self, module_name: str, stage_name: str):
        """Test that stage module has run_stage() entry point."""
        module = importlib.import_module(module_name)
        assert hasattr(module, "run_stage"), \
            f"Module {module_name} missing run_stage() function"
        
        run_stage = getattr(module, "run_stage")
        assert callable(run_stage), \
            f"Module {module_name} run_stage is not callable"
    
    @pytest.mark.parametrize("module_name,stage_name", RENAMED_STAGES)
    def test_run_stage_signature(self, module_name: str, stage_name: str):
        """Test that run_stage() has correct signature."""
        import inspect
        
        module = importlib.import_module(module_name)
        run_stage = getattr(module, "run_stage")
        
        # Get function signature
        sig = inspect.signature(run_stage)
        params = list(sig.parameters.keys())
        
        # Should have at least job_dir parameter
        assert len(params) >= 1, \
            f"{module_name}.run_stage() should have at least 1 parameter (job_dir)"
        
        # First parameter should be job_dir
        assert params[0] in ["job_dir", "job_path"], \
            f"{module_name}.run_stage() first param should be job_dir, got {params[0]}"


# ============================================================================
# HELPER MODULE TESTS
# ============================================================================

@pytest.mark.unit
class TestGlossaryLearnerModule:
    """Test glossary_learner helper module."""
    
    def test_glossary_learner_importable(self):
        """Test that glossary_learner module can be imported."""
        try:
            module = importlib.import_module("scripts.03_glossary_learner")
            assert module is not None
        except ImportError as e:
            pytest.fail(f"Failed to import scripts.03_glossary_learner: {e}")
    
    def test_glossary_learner_has_class(self):
        """Test that glossary_learner has GlossaryLearner class."""
        module = importlib.import_module("scripts.03_glossary_learner")
        assert hasattr(module, "GlossaryLearner"), \
            "glossary_learner module missing GlossaryLearner class"
        
        GlossaryLearner = getattr(module, "GlossaryLearner")
        assert callable(GlossaryLearner), \
            "GlossaryLearner is not instantiable"


# ============================================================================
# FILE NAMING COMPLIANCE TESTS
# ============================================================================

@pytest.mark.unit
class TestStageFileNaming:
    """Test that all stage files follow {NN}_{stage_name}.py naming pattern."""
    
    def test_all_stage_files_in_scripts_dir(self, project_root: Path):
        """Test that all stage files are directly in scripts/ directory."""
        scripts_dir = project_root / "scripts"
        
        # Stage files that should exist (from Phase 1)
        expected_stages = [
            "01_demux.py",
            "02_tmdb_enrichment.py",
            "03_glossary_load.py",
            "03_glossary_learner.py",
            "04_source_separation.py",
            "05_ner.py",
            "05_pyannote_vad.py",
            "06_lyrics_detection.py",
            "06_whisperx_asr.py",
            "07_alignment.py",
            "07_hallucination_removal.py",
            "08_translation.py",
            "09_subtitle_gen.py",
            "09_subtitle_generation.py",
            "10_mux.py",
        ]
        
        for stage_file in expected_stages:
            stage_path = scripts_dir / stage_file
            assert stage_path.exists(), \
                f"Stage file {stage_file} not found in scripts/ directory"
            assert stage_path.is_file(), \
                f"{stage_file} exists but is not a file"
    
    def test_no_stage_subdirectories_remain(self, project_root: Path):
        """Test that old stage subdirectories have been removed."""
        scripts_dir = project_root / "scripts"
        
        # Subdirectories that should NOT exist after Phase 1
        old_subdirs = [
            "03_glossary_load",
            "05_ner",
            "06_lyrics_detection",
            "07_hallucination_removal",
            "09_subtitle_gen",
        ]
        
        for subdir in old_subdirs:
            subdir_path = scripts_dir / subdir
            assert not subdir_path.exists(), \
                f"Old stage subdirectory {subdir} still exists after Phase 1"
    
    def test_stage_files_follow_naming_pattern(self, project_root: Path):
        """Test that stage files follow {NN}_{stage_name}.py pattern."""
        import re
        
        scripts_dir = project_root / "scripts"
        stage_pattern = re.compile(r"^\d{2}_[a-z_]+\.py$")
        
        # Get all Python files in scripts/ that look like stages
        stage_files = [
            f for f in scripts_dir.glob("*.py")
            if f.stem[0:2].isdigit()  # Starts with digits
        ]
        
        for stage_file in stage_files:
            assert stage_pattern.match(stage_file.name), \
                f"Stage file {stage_file.name} does not follow {{NN}}_{{stage_name}}.py pattern"


# ============================================================================
# IMPORT PATTERN TESTS
# ============================================================================

@pytest.mark.unit
class TestStageImportPatterns:
    """Test that stage import patterns in orchestrator are correct."""
    
    def test_run_pipeline_uses_importlib(self, project_root: Path):
        """Test that run-pipeline.py uses importlib for numeric module names."""
        run_pipeline = project_root / "scripts" / "run-pipeline.py"
        assert run_pipeline.exists(), "run-pipeline.py not found"
        
        content = run_pipeline.read_text()
        
        # Should use importlib for numeric module imports
        assert "importlib.import_module" in content, \
            "run-pipeline.py should use importlib.import_module for numeric modules"
        
        # Should import specific renamed modules
        expected_imports = [
            '"scripts.03_glossary_load"',
            '"scripts.05_ner"',
            '"scripts.06_lyrics_detection"',
            '"scripts.09_subtitle_gen"',
        ]
        
        for import_str in expected_imports:
            assert import_str in content, \
                f"run-pipeline.py should import {import_str}"
    
    def test_run_pipeline_no_old_sys_path_insertions(self, project_root: Path):
        """Test that old sys.path insertions to subdirectories are removed."""
        run_pipeline = project_root / "scripts" / "run-pipeline.py"
        content = run_pipeline.read_text()
        
        # Old patterns that should NOT exist
        old_patterns = [
            'scripts/03_glossary_load"',  # Old path
            'scripts/05_ner"',
            'scripts/06_lyrics_detection"',
            'scripts/09_subtitle_gen"',
        ]
        
        for pattern in old_patterns:
            # Check if old sys.path.insert pattern exists
            if f'sys.path.insert(0, str(PROJECT_ROOT / "{pattern}' in content:
                pytest.fail(
                    f"run-pipeline.py still has old sys.path.insert for {pattern}"
                )


# ============================================================================
# MODULE METADATA TESTS
# ============================================================================

@pytest.mark.unit
class TestStageModuleMetadata:
    """Test that stage modules have proper metadata and documentation."""
    
    RENAMED_STAGES_FULL = [
        "scripts.03_glossary_load",
        "scripts.03_glossary_learner",
        "scripts.05_ner",
        "scripts.06_lyrics_detection",
        "scripts.07_hallucination_removal",
        "scripts.09_subtitle_gen",
    ]
    
    @pytest.mark.parametrize("module_name", RENAMED_STAGES_FULL)
    def test_module_has_docstring(self, module_name: str):
        """Test that module has a docstring."""
        module = importlib.import_module(module_name)
        assert module.__doc__ is not None, \
            f"Module {module_name} missing docstring"
        assert len(module.__doc__.strip()) > 0, \
            f"Module {module_name} has empty docstring"
    
    @pytest.mark.parametrize("module_name", RENAMED_STAGES_FULL)
    def test_module_has_logger(self, module_name: str):
        """Test that module uses logger (not print)."""
        module_path = PROJECT_ROOT / module_name.replace(".", "/")
        module_path = module_path.with_suffix(".py")
        
        if not module_path.exists():
            pytest.skip(f"Module file {module_path} not found")
        
        content = module_path.read_text()
        
        # Should import logger
        assert "from shared.logger import" in content or "import shared.logger" in content, \
            f"Module {module_name} should import logger from shared"
        
        # Should use logger, not print (except for CLI/main)
        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            if "print(" in line:
                # Check if it's in main/CLI context
                context_start = max(0, i - 10)
                context = "\n".join(lines[context_start:i])
                if "def main" not in context and "__name__ == '__main__'" not in context:
                    # Allow print in main() or CLI context
                    pytest.fail(
                        f"{module_name}:{i} uses print() instead of logger (outside main/CLI)"
                    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
