#!/usr/bin/env python3
"""
Tests for Stage Dependencies System

Tests dependency validation, execution ordering, and workflow presets.
"""

# Standard library
import pytest
from typing import List

# Local
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.stage_dependencies import (
    STAGE_DEPENDENCIES,
    OPTIONAL_ENHANCEMENTS,
    STAGE_ORDER,
    WORKFLOW_PRESETS,
    validate_stage_dependencies,
    get_missing_enhancements,
    get_execution_order,
    get_stage_info,
    get_workflow_stages,
)


# ============================================================================
# TEST DEPENDENCY VALIDATION
# ============================================================================

def test_validate_valid_dependencies():
    """Test validation passes for valid dependencies"""
    stages = ["01_demux", "04_asr", "08_translation"]
    validate_stage_dependencies(stages)  # Should not raise


def test_validate_missing_dependency():
    """Test validation fails when required dependency is missing"""
    stages = ["04_asr"]  # Missing 01_demux
    with pytest.raises(ValueError, match="requires 01_demux"):
        validate_stage_dependencies(stages)


def test_validate_chain_dependencies():
    """Test validation checks entire dependency chain"""
    stages = ["10_mux"]  # Missing entire chain
    with pytest.raises(ValueError):
        validate_stage_dependencies(stages)


def test_validate_unknown_stage():
    """Test validation fails for unknown stage"""
    stages = ["01_demux", "99_unknown"]
    with pytest.raises(ValueError, match="Unknown stage"):
        validate_stage_dependencies(stages)


def test_validate_empty_list():
    """Test validation passes for empty stage list"""
    validate_stage_dependencies([])  # Should not raise


def test_validate_all_stages():
    """Test validation passes when all stages are enabled"""
    all_stages = list(STAGE_DEPENDENCIES.keys())
    validate_stage_dependencies(all_stages)  # Should not raise


# ============================================================================
# TEST OPTIONAL ENHANCEMENTS
# ============================================================================

def test_get_missing_enhancements_none():
    """Test when all enhancements are enabled"""
    stages = ["01_demux", "02_tmdb", "03_glossary_load", "04_asr"]
    missing = get_missing_enhancements(stages)
    assert "04_asr" not in missing or len(missing["04_asr"]) == 0


def test_get_missing_enhancements_some():
    """Test when some enhancements are missing"""
    stages = ["01_demux", "04_asr"]
    missing = get_missing_enhancements(stages)
    assert "04_asr" in missing
    assert "02_tmdb" in missing["04_asr"]
    assert "03_glossary_load" in missing["04_asr"]


def test_get_missing_enhancements_translation():
    """Test missing enhancements for translation stage"""
    stages = ["01_demux", "04_asr", "08_translation"]
    missing = get_missing_enhancements(stages)
    assert "08_translation" in missing


# ============================================================================
# TEST EXECUTION ORDER
# ============================================================================

def test_execution_order_maintains_dependencies():
    """Test execution order respects dependencies"""
    stages = ["08_translation", "01_demux", "04_asr"]
    ordered = get_execution_order(stages)
    
    # 01_demux should come before 04_asr
    assert ordered.index("01_demux") < ordered.index("04_asr")
    # 04_asr should come before 08_translation
    assert ordered.index("04_asr") < ordered.index("08_translation")


def test_execution_order_complete_pipeline():
    """Test execution order for complete pipeline"""
    stages = list(STAGE_DEPENDENCIES.keys())
    ordered = get_execution_order(stages)
    
    # Should match STAGE_ORDER
    assert ordered == STAGE_ORDER


def test_execution_order_partial_pipeline():
    """Test execution order for partial pipeline"""
    stages = ["04_asr", "01_demux", "02_tmdb"]
    ordered = get_execution_order(stages)
    
    # Should be in correct order
    expected = ["01_demux", "02_tmdb", "04_asr"]
    assert ordered == expected


def test_execution_order_single_stage():
    """Test execution order for single stage"""
    stages = ["01_demux"]
    ordered = get_execution_order(stages)
    assert ordered == ["01_demux"]


# ============================================================================
# TEST STAGE INFO
# ============================================================================

def test_get_stage_info_valid():
    """Test getting info for valid stage"""
    info = get_stage_info("04_asr")
    
    assert info["name"] == "04_asr"
    assert "01_demux" in info["required_dependencies"]
    assert "02_tmdb" in info["optional_dependencies"]
    assert info["order_index"] >= 0


def test_get_stage_info_unknown():
    """Test getting info for unknown stage"""
    info = get_stage_info("99_unknown")
    assert "error" in info


def test_get_stage_info_no_dependencies():
    """Test stage with no dependencies"""
    info = get_stage_info("01_demux")
    assert len(info["required_dependencies"]) == 0


# ============================================================================
# TEST WORKFLOW PRESETS
# ============================================================================

def test_workflow_presets_valid():
    """Test all workflow presets are valid"""
    for workflow_name, stages in WORKFLOW_PRESETS.items():
        # Should not raise
        validate_stage_dependencies(stages)


def test_get_workflow_stages_transcribe():
    """Test getting transcribe workflow stages"""
    stages = get_workflow_stages("transcribe")
    assert "01_demux" in stages
    assert "04_asr" in stages
    assert len(stages) >= 2


def test_get_workflow_stages_subtitle_full():
    """Test getting full subtitle workflow stages"""
    stages = get_workflow_stages("subtitle_full")
    assert "01_demux" in stages
    assert "10_mux" in stages
    assert len(stages) == 10  # All stages


def test_get_workflow_stages_unknown():
    """Test getting unknown workflow raises error"""
    with pytest.raises(ValueError, match="Unknown workflow"):
        get_workflow_stages("unknown_workflow")


def test_workflow_stages_ordered():
    """Test workflow stages are in correct order"""
    for workflow_name, stages in WORKFLOW_PRESETS.items():
        ordered = get_execution_order(stages)
        # Should be same as original (already ordered)
        assert ordered == stages


# ============================================================================
# TEST DEPENDENCY GRAPH INTEGRITY
# ============================================================================

def test_stage_dependencies_complete():
    """Test all stages in STAGE_ORDER have dependencies defined"""
    for stage in STAGE_ORDER:
        assert stage in STAGE_DEPENDENCIES


def test_stage_dependencies_valid():
    """Test all dependencies reference valid stages"""
    for stage, deps in STAGE_DEPENDENCIES.items():
        for dep in deps:
            assert dep in STAGE_DEPENDENCIES, f"{stage} depends on unknown stage {dep}"


def test_optional_enhancements_valid():
    """Test all optional enhancements reference valid stages"""
    for stage, deps in OPTIONAL_ENHANCEMENTS.items():
        assert stage in STAGE_DEPENDENCIES
        for dep in deps:
            assert dep in STAGE_DEPENDENCIES


def test_no_circular_dependencies():
    """Test there are no circular dependencies"""
    for stage in STAGE_DEPENDENCIES:
        visited = set()
        to_check = [stage]
        
        while to_check:
            current = to_check.pop()
            if current in visited:
                pytest.fail(f"Circular dependency detected for {stage}")
            visited.add(current)
            
            deps = STAGE_DEPENDENCIES.get(current, [])
            to_check.extend(deps)


def test_dependency_order_consistency():
    """Test dependencies appear before stages in STAGE_ORDER"""
    for i, stage in enumerate(STAGE_ORDER):
        deps = STAGE_DEPENDENCIES[stage]
        for dep in deps:
            dep_index = STAGE_ORDER.index(dep)
            assert dep_index < i, f"{stage} depends on {dep} but appears before it"


# ============================================================================
# TEST REAL-WORLD SCENARIOS
# ============================================================================

def test_minimal_transcription_pipeline():
    """Test minimal transcription pipeline configuration"""
    stages = ["01_demux", "04_asr"]
    validate_stage_dependencies(stages)
    ordered = get_execution_order(stages)
    assert ordered == ["01_demux", "04_asr"]


def test_enhanced_translation_pipeline():
    """Test enhanced translation pipeline configuration"""
    stages = [
        "01_demux",
        "02_tmdb",
        "03_glossary_load",
        "04_asr",
        "05_ner",
        "07_hallucination_removal",
        "08_translation",
    ]
    validate_stage_dependencies(stages)
    ordered = get_execution_order(stages)
    # Should be in correct order
    assert ordered[0] == "01_demux"
    assert ordered[-1] == "08_translation"


def test_skip_optional_stages():
    """Test skipping optional stages still works"""
    # Skip NER, lyrics, hallucination
    stages = ["01_demux", "04_asr", "08_translation", "09_subtitle_gen", "10_mux"]
    validate_stage_dependencies(stages)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
