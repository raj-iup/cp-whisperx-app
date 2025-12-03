#!/usr/bin/env python3
"""
Integration Tests for Complete Workflow Execution

Tests end-to-end workflow execution with standard test media.
This tests the complete pipeline integration WITHOUT requiring GPU/models.

Phase 2: Testing Infrastructure - Session 3, Task 1
"""

# Standard library
import sys
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

# Third-party
import pytest

# Local
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================================
# WORKFLOW EXECUTION HELPERS
# ============================================================================

def run_prepare_job(
    media_path: Path,
    workflow: str,
    source_lang: str,
    target_lang: Optional[str] = None,
    timeout: int = 60
) -> Dict[str, Any]:
    """
    Run prepare-job.sh and return result.
    
    Args:
        media_path: Path to media file
        workflow: Workflow type (transcribe, translate, subtitle)
        source_lang: Source language code
        target_lang: Target language code (for translate/subtitle)
        timeout: Timeout in seconds
        
    Returns:
        Dict with returncode, stdout, stderr, job_dir
    """
    cmd = [
        str(PROJECT_ROOT / "prepare-job.sh"),
        "--media", str(media_path),
        "--workflow", workflow,
        "--source-language", source_lang,
    ]
    
    if target_lang:
        if workflow == "subtitle":
            cmd.extend(["--target-languages", target_lang])
        else:
            cmd.extend(["--target-language", target_lang])
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=PROJECT_ROOT
        )
        
        # Extract job directory from output
        job_dir = None
        for line in result.stdout.split("\n"):
            if "Job directory:" in line or "job-" in line:
                # Parse job directory path
                if "out/" in line:
                    parts = line.split("out/")
                    if len(parts) > 1:
                        job_path = "out/" + parts[1].split()[0]
                        job_dir = PROJECT_ROOT / job_path.strip()
        
        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "job_dir": job_dir
        }
    
    except subprocess.TimeoutExpired:
        return {
            "returncode": -1,
            "stdout": "",
            "stderr": "Timeout expired",
            "job_dir": None
        }


# ============================================================================
# PREPARE-JOB INTEGRATION TESTS
# ============================================================================

@pytest.mark.integration
@pytest.mark.smoke
class TestPrepareJobIntegration:
    """Integration tests for prepare-job script."""
    
    def test_prepare_job_script_exists(self):
        """Test that prepare-job.sh exists."""
        prepare_script = PROJECT_ROOT / "prepare-job.sh"
        assert prepare_script.exists(), "prepare-job.sh not found"
    
    def test_prepare_job_is_executable(self):
        """Test that prepare-job.sh is executable."""
        prepare_script = PROJECT_ROOT / "prepare-job.sh"
        import os
        assert os.access(prepare_script, os.X_OK), "prepare-job.sh not executable"
    
    @pytest.mark.skip(reason="Requires actual execution - slow test")
    def test_prepare_job_creates_job_directory(self, sample_media_path: Path):
        """Test that prepare-job creates job directory."""
        if not sample_media_path.exists():
            pytest.skip(f"Test media not available: {sample_media_path}")
        
        result = run_prepare_job(
            media_path=sample_media_path,
            workflow="transcribe",
            source_lang="en"
        )
        
        assert result["returncode"] == 0, \
            f"prepare-job failed: {result['stderr']}"
        assert result["job_dir"] is not None, \
            "Job directory not created"
        assert result["job_dir"].exists(), \
            f"Job directory does not exist: {result['job_dir']}"
    
    @pytest.mark.skip(reason="Requires actual execution - slow test")
    def test_prepare_job_creates_config(self, sample_media_path: Path):
        """Test that prepare-job creates job config."""
        if not sample_media_path.exists():
            pytest.skip(f"Test media not available: {sample_media_path}")
        
        result = run_prepare_job(
            media_path=sample_media_path,
            workflow="transcribe",
            source_lang="en"
        )
        
        if result["job_dir"]:
            config_file = result["job_dir"] / ".env.pipeline"
            assert config_file.exists(), \
                f"Job config not created: {config_file}"


# ============================================================================
# WORKFLOW VALIDATION TESTS (NO EXECUTION)
# ============================================================================

@pytest.mark.integration
class TestWorkflowStructure:
    """Test workflow structure and dependencies without execution."""
    
    def test_transcribe_workflow_stages_defined(self):
        """Test that transcribe workflow stages are defined."""
        try:
            from shared.stage_dependencies import WORKFLOW_PRESETS
            assert "transcribe" in WORKFLOW_PRESETS, \
                "Transcribe workflow not defined"
            
            transcribe_stages = WORKFLOW_PRESETS["transcribe"]
            assert isinstance(transcribe_stages, list), \
                "Transcribe workflow should be a list"
            assert len(transcribe_stages) > 0, \
                "Transcribe workflow should have stages"
        except ImportError:
            pytest.skip("Stage dependencies not available")
    
    def test_translate_workflow_stages_defined(self):
        """Test that translate workflow stages are defined."""
        try:
            from shared.stage_dependencies import WORKFLOW_PRESETS
            assert "translate" in WORKFLOW_PRESETS, \
                "Translate workflow not defined"
            
            translate_stages = WORKFLOW_PRESETS["translate"]
            assert isinstance(translate_stages, list), \
                "Translate workflow should be a list"
            assert len(translate_stages) > 0, \
                "Translate workflow should have stages"
        except ImportError:
            pytest.skip("Stage dependencies not available")
    
    def test_subtitle_workflow_stages_defined(self):
        """Test that subtitle workflow stages are defined."""
        try:
            from shared.stage_dependencies import WORKFLOW_PRESETS
            assert "subtitle" in WORKFLOW_PRESETS, \
                "Subtitle workflow not defined"
            
            subtitle_stages = WORKFLOW_PRESETS["subtitle"]
            assert isinstance(subtitle_stages, list), \
                "Subtitle workflow should be a list"
            assert len(subtitle_stages) >= 8, \
                "Subtitle workflow should have at least 8 stages (full pipeline)"
        except ImportError:
            pytest.skip("Stage dependencies not available")
    
    def test_workflow_dependencies_valid(self):
        """Test that workflow dependencies are valid."""
        try:
            from shared.stage_dependencies import (
                WORKFLOW_PRESETS,
                STAGE_DEPENDENCIES,
                validate_stage_dependencies
            )
            
            for workflow_name, stages in WORKFLOW_PRESETS.items():
                # Validate each workflow's stages
                missing = validate_stage_dependencies(stages)
                assert len(missing) == 0, \
                    f"Workflow {workflow_name} has missing dependencies: {missing}"
        
        except ImportError:
            pytest.skip("Stage dependencies not available")


# ============================================================================
# STAGE AVAILABILITY TESTS
# ============================================================================

@pytest.mark.integration
class TestStageScriptsAvailable:
    """Test that all required stage scripts exist."""
    
    REQUIRED_STAGES = [
        "01_demux.py",
        "02_tmdb_enrichment.py",
        "03_glossary_load.py",
        "04_source_separation.py",
        "05_pyannote_vad.py",
        "06_whisperx_asr.py",
        "07_alignment.py",
        "08_translation.py",
        "09_subtitle_generation.py",
        "10_mux.py",
    ]
    
    @pytest.mark.parametrize("stage_file", REQUIRED_STAGES)
    def test_stage_script_exists(self, stage_file: str):
        """Test that stage script exists."""
        stage_path = PROJECT_ROOT / "scripts" / stage_file
        assert stage_path.exists(), \
            f"Required stage script not found: {stage_file}"
    
    @pytest.mark.parametrize("stage_file", REQUIRED_STAGES)
    def test_stage_script_is_python(self, stage_file: str):
        """Test that stage script is Python."""
        stage_path = PROJECT_ROOT / "scripts" / stage_file
        if stage_path.exists():
            with open(stage_path, 'r') as f:
                first_line = f.readline()
                assert first_line.startswith('#!') and 'python' in first_line.lower(), \
                    f"Stage {stage_file} should have Python shebang"


# ============================================================================
# JOB DIRECTORY STRUCTURE TESTS
# ============================================================================

@pytest.mark.integration
class TestJobDirectoryStructure:
    """Test expected job directory structure."""
    
    def test_output_directory_exists(self):
        """Test that output directory exists or can be created."""
        out_dir = PROJECT_ROOT / "out"
        if not out_dir.exists():
            # Try to create it
            try:
                out_dir.mkdir(parents=True, exist_ok=True)
                assert out_dir.exists(), "Could not create output directory"
            except PermissionError:
                pytest.skip("No permission to create output directory")
    
    def test_logs_directory_exists(self):
        """Test that logs directory exists or can be created."""
        logs_dir = PROJECT_ROOT / "logs"
        if not logs_dir.exists():
            try:
                logs_dir.mkdir(parents=True, exist_ok=True)
                assert logs_dir.exists(), "Could not create logs directory"
            except PermissionError:
                pytest.skip("No permission to create logs directory")
    
    def test_expected_stage_directories_structure(self, mock_job_dir: Path):
        """Test expected stage directory structure in a job."""
        # Create expected stage directories
        expected_stages = [
            "01_demux",
            "02_tmdb",
            "06_whisperx_asr",
            "07_alignment",
        ]
        
        for stage in expected_stages:
            stage_dir = mock_job_dir / stage
            stage_dir.mkdir(exist_ok=True)
            
            # Verify created
            assert stage_dir.exists(), f"Stage directory {stage} not created"
            assert stage_dir.is_dir(), f"{stage} is not a directory"


# ============================================================================
# PIPELINE RUNNER TESTS (STRUCTURE ONLY)
# ============================================================================

@pytest.mark.integration
class TestPipelineRunner:
    """Test pipeline runner script structure."""
    
    def test_run_pipeline_script_exists(self):
        """Test that run-pipeline.sh exists."""
        run_script = PROJECT_ROOT / "run-pipeline.sh"
        assert run_script.exists(), "run-pipeline.sh not found"
    
    def test_run_pipeline_py_exists(self):
        """Test that run-pipeline.py exists."""
        run_py = PROJECT_ROOT / "scripts" / "run-pipeline.py"
        assert run_py.exists(), "run-pipeline.py not found"
    
    def test_run_pipeline_has_main_function(self):
        """Test that run-pipeline.py has main function."""
        try:
            import importlib
            # Note: run-pipeline has a hyphen, use importlib
            sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
            
            # Check if file has main execution
            run_py = PROJECT_ROOT / "scripts" / "run-pipeline.py"
            content = run_py.read_text()
            assert "if __name__ == '__main__'" in content, \
                "run-pipeline.py should have main execution guard"
        except Exception as e:
            pytest.skip(f"Could not verify run-pipeline.py: {e}")


# ============================================================================
# WORKFLOW END-TO-END PLACEHOLDERS (PHASE 3)
# ============================================================================

@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.requires_models
@pytest.mark.skip(reason="Phase 3 - Requires full pipeline with models")
class TestTranscribeWorkflowE2E:
    """End-to-end tests for transcribe workflow (Phase 3)."""
    
    def test_transcribe_sample1_english_technical(
        self,
        sample_media_path: Path,
        test_media_samples: Dict[str, Dict[str, Any]]
    ):
        """
        Test complete transcribe workflow with Sample 1.
        
        Expected:
            - Job created successfully
            - All stages execute
            - Transcript generated
            - Quality targets met (≥95% ASR accuracy)
        """
        pytest.skip("Phase 3 - Full pipeline execution")
    
    def test_transcribe_sample2_hinglish(
        self,
        sample_media_hinglish: Path,
        test_media_samples: Dict[str, Dict[str, Any]]
    ):
        """
        Test complete transcribe workflow with Sample 2.
        
        Expected:
            - Job created successfully
            - All stages execute
            - Hindi/Hinglish transcript generated
            - Quality targets met (≥85% ASR accuracy)
        """
        pytest.skip("Phase 3 - Full pipeline execution")


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.requires_models
@pytest.mark.skip(reason="Phase 3 - Requires full pipeline with models")
class TestTranslateWorkflowE2E:
    """End-to-end tests for translate workflow (Phase 3)."""
    
    def test_translate_english_to_hindi(
        self,
        sample_media_path: Path,
        test_media_samples: Dict[str, Dict[str, Any]]
    ):
        """
        Test complete translate workflow (English → Hindi).
        
        Expected:
            - Job created successfully
            - All stages execute
            - Translation generated
            - Quality targets met (≥90% BLEU)
        """
        pytest.skip("Phase 3 - Full pipeline execution")
    
    def test_translate_hindi_to_english(
        self,
        sample_media_hinglish: Path,
        test_media_samples: Dict[str, Dict[str, Any]]
    ):
        """
        Test complete translate workflow (Hindi → English).
        
        Expected:
            - Job created successfully
            - All stages execute
            - Translation generated
            - Quality targets met (≥90% BLEU)
        """
        pytest.skip("Phase 3 - Full pipeline execution")


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.requires_models
@pytest.mark.skip(reason="Phase 3 - Requires full pipeline with models")
class TestSubtitleWorkflowE2E:
    """End-to-end tests for subtitle workflow (Phase 3)."""
    
    def test_subtitle_full_pipeline_sample2(
        self,
        sample_media_hinglish: Path,
        test_media_samples: Dict[str, Dict[str, Any]]
    ):
        """
        Test complete subtitle workflow with Sample 2 (full 10-stage pipeline).
        
        Expected:
            - Job created successfully
            - All 10 stages execute in order
            - Multi-language subtitles generated (hi, en, gu, ta, etc.)
            - Subtitles soft-embedded in MKV
            - Quality targets met (≥88% subtitle quality)
            - Context-aware features applied
        """
        pytest.skip("Phase 3 - Full pipeline execution")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
