#!/usr/bin/env python3
"""
Stage Dependencies System - Phase 4

Defines dependency graph for pipeline stages and validates
that all required dependencies are satisfied before execution.

This ensures:
1. Stages run in correct order
2. Required inputs are available
3. Optional stages can be safely skipped
4. Clear error messages for missing dependencies

Usage:
    from shared.stage_dependencies import STAGE_DEPENDENCIES, validate_stage_dependencies
    
    enabled_stages = ["01_demux", "04_asr", "08_translation"]
    validate_stage_dependencies(enabled_stages)  # Raises ValueError if invalid
"""

# Standard library
from typing import List, Dict, Set

# Local
from shared.logger import get_logger

logger = get_logger(__name__)


# ============================================================================
# STAGE DEPENDENCY GRAPH
# ============================================================================

STAGE_DEPENDENCIES: Dict[str, List[str]] = {
    # Stage 01: Demux (no dependencies - extracts audio from video)
    "01_demux": [],
    
    # Stage 02: TMDB (no dependencies - fetches metadata independently)
    "02_tmdb": [],
    
    # Stage 03: Glossary Load (optional dependency on TMDB for names)
    "03_glossary_load": [],  # Can use TMDB data if available but not required
    
    # Stage 04: ASR (requires audio from demux)
    "04_asr": ["01_demux"],
    
    # Stage 05: NER (requires transcript from ASR)
    "05_ner": ["04_asr"],
    
    # Stage 06: Lyrics Detection (requires transcript from ASR)
    "06_lyrics_detection": ["04_asr"],
    
    # Stage 07: Hallucination Removal (requires ASR, benefits from lyrics detection)
    "07_hallucination_removal": ["04_asr"],  # lyrics_detection is optional enhancement
    
    # Stage 08: Translation (requires ASR, should use cleaned transcript)
    # Optional: NER, hallucination removal for better quality
    "08_translation": ["04_asr"],  # Core requirement only
    
    # Stage 09: Subtitle Generation (requires translation or ASR)
    "09_subtitle_gen": ["08_translation"],  # If translation enabled
    
    # Stage 10: Mux (requires subtitles)
    "10_mux": ["09_subtitle_gen"],
}


# ============================================================================
# OPTIONAL STAGE ENHANCEMENTS
# ============================================================================
# These stages enhance quality but are not strictly required

OPTIONAL_ENHANCEMENTS: Dict[str, List[str]] = {
    "04_asr": ["02_tmdb", "03_glossary_load"],  # Improves accuracy via biasing
    "07_hallucination_removal": ["06_lyrics_detection"],  # Better lyrics detection
    "08_translation": ["05_ner", "07_hallucination_removal"],  # Better quality
}


# ============================================================================
# STAGE EXECUTION ORDER
# ============================================================================
# Defines valid topological sort for stage execution

STAGE_ORDER: List[str] = [
    "01_demux",
    "02_tmdb",
    "03_glossary_load",
    "04_asr",
    "05_ner",
    "06_lyrics_detection",
    "07_hallucination_removal",
    "08_translation",
    "09_subtitle_gen",
    "10_mux",
]


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_stage_dependencies(enabled_stages: List[str]) -> None:
    """
    Validate that all stage dependencies are satisfied.
    
    Args:
        enabled_stages: List of stage names that will be executed
        
    Raises:
        ValueError: If required dependencies are missing
        
    Example:
        >>> validate_stage_dependencies(["01_demux", "04_asr", "08_translation"])
        # Passes - all dependencies satisfied
        
        >>> validate_stage_dependencies(["08_translation"])
        ValueError: Stage 08_translation requires 04_asr but it is not enabled
    """
    enabled_set = set(enabled_stages)
    errors = []
    
    for stage in enabled_stages:
        if stage not in STAGE_DEPENDENCIES:
            errors.append(f"Unknown stage: {stage}")
            continue
            
        required_deps = STAGE_DEPENDENCIES[stage]
        
        for dep in required_deps:
            if dep not in enabled_set:
                errors.append(
                    f"Stage {stage} requires {dep} but it is not enabled"
                )
    
    if errors:
        error_msg = "Stage dependency validation failed:\n  - " + "\n  - ".join(errors)
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info(f"Stage dependencies validated: {len(enabled_stages)} stages")


def get_missing_enhancements(enabled_stages: List[str]) -> Dict[str, List[str]]:
    """
    Identify optional enhancements that are not enabled.
    
    Args:
        enabled_stages: List of stage names that will be executed
        
    Returns:
        Dictionary mapping stage names to missing optional enhancements
        
    Example:
        >>> get_missing_enhancements(["01_demux", "04_asr"])
        {"04_asr": ["02_tmdb", "03_glossary_load"]}
    """
    enabled_set = set(enabled_stages)
    missing = {}
    
    for stage in enabled_stages:
        if stage in OPTIONAL_ENHANCEMENTS:
            optional_deps = OPTIONAL_ENHANCEMENTS[stage]
            missing_deps = [dep for dep in optional_deps if dep not in enabled_set]
            
            if missing_deps:
                missing[stage] = missing_deps
    
    return missing


def log_missing_enhancements(enabled_stages: List[str]) -> None:
    """
    Log warnings for missing optional enhancements.
    
    Args:
        enabled_stages: List of stage names that will be executed
    """
    missing = get_missing_enhancements(enabled_stages)
    
    if missing:
        logger.warning("Optional enhancements not enabled:")
        for stage, deps in missing.items():
            logger.warning(f"  {stage}: missing {', '.join(deps)}")
            logger.warning(f"    (Quality may be reduced)")


def get_execution_order(enabled_stages: List[str]) -> List[str]:
    """
    Get stages in valid execution order based on dependencies.
    
    Args:
        enabled_stages: List of stage names to execute
        
    Returns:
        Stages sorted in dependency-respecting execution order
        
    Example:
        >>> get_execution_order(["08_translation", "01_demux", "04_asr"])
        ["01_demux", "04_asr", "08_translation"]
    """
    enabled_set = set(enabled_stages)
    
    # Filter STAGE_ORDER to only include enabled stages
    ordered = [stage for stage in STAGE_ORDER if stage in enabled_set]
    
    # Validate we got all enabled stages
    if len(ordered) != len(enabled_stages):
        unknown = enabled_set - set(ordered)
        logger.warning(f"Unknown stages will be skipped: {unknown}")
    
    return ordered


def get_stage_info(stage_name: str) -> Dict[str, any]:
    """
    Get detailed information about a stage.
    
    Args:
        stage_name: Name of the stage
        
    Returns:
        Dictionary with stage information
        
    Example:
        >>> get_stage_info("04_asr")
        {
            "name": "04_asr",
            "required_dependencies": ["01_demux"],
            "optional_dependencies": ["02_tmdb", "03_glossary_load"],
            "order_index": 3
        }
    """
    if stage_name not in STAGE_DEPENDENCIES:
        return {
            "name": stage_name,
            "error": "Unknown stage"
        }
    
    return {
        "name": stage_name,
        "required_dependencies": STAGE_DEPENDENCIES[stage_name],
        "optional_dependencies": OPTIONAL_ENHANCEMENTS.get(stage_name, []),
        "order_index": STAGE_ORDER.index(stage_name) if stage_name in STAGE_ORDER else -1
    }


# ============================================================================
# WORKFLOW PRESETS
# ============================================================================
# Pre-defined stage combinations for common workflows

WORKFLOW_PRESETS: Dict[str, List[str]] = {
    # Transcription only (minimal)
    "transcribe": [
        "01_demux",
        "04_asr",
    ],
    
    # Transcription with enhancements
    "transcribe_enhanced": [
        "01_demux",
        "02_tmdb",
        "03_glossary_load",
        "04_asr",
        "05_ner",
        "06_lyrics_detection",
        "07_hallucination_removal",
    ],
    
    # Translation (minimal)
    "translate": [
        "01_demux",
        "04_asr",
        "08_translation",
    ],
    
    # Translation with enhancements
    "translate_enhanced": [
        "01_demux",
        "02_tmdb",
        "03_glossary_load",
        "04_asr",
        "05_ner",
        "06_lyrics_detection",
        "07_hallucination_removal",
        "08_translation",
    ],
    
    # Full subtitle pipeline (minimal)
    "subtitle": [
        "01_demux",
        "04_asr",
        "08_translation",
        "09_subtitle_gen",
        "10_mux",
    ],
    
    # Full subtitle pipeline with all enhancements
    "subtitle_full": [
        "01_demux",
        "02_tmdb",
        "03_glossary_load",
        "04_asr",
        "05_ner",
        "06_lyrics_detection",
        "07_hallucination_removal",
        "08_translation",
        "09_subtitle_gen",
        "10_mux",
    ],
}


def get_workflow_stages(workflow: str) -> List[str]:
    """
    Get stages for a named workflow preset.
    
    Args:
        workflow: Workflow name (transcribe, translate, subtitle, etc.)
        
    Returns:
        List of stage names in execution order
        
    Raises:
        ValueError: If workflow name is unknown
    """
    if workflow not in WORKFLOW_PRESETS:
        available = ", ".join(WORKFLOW_PRESETS.keys())
        raise ValueError(f"Unknown workflow: {workflow}. Available: {available}")
    
    return WORKFLOW_PRESETS[workflow]
