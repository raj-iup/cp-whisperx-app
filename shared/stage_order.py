"""
Centralized Stage Order Configuration

This module defines the canonical ordering of pipeline stages.
All stage numbering should reference this single source of truth.

IMPORTANT: When adding/removing stages, only modify STAGE_ORDER list.
All other components will automatically update.
"""

from typing import Dict, List, Optional

# ============================================================================
# STAGE ORDER CONFIGURATION (SINGLE SOURCE OF TRUTH)
# ============================================================================

STAGE_ORDER: List[str] = [
    # Stage 1: Audio extraction
    "demux",
    
    # Stage 2: TMDB enrichment (metadata, cast, crew)
    "tmdb",
    
    # Stage 3: Glossary system (character names, entities)
    "glossary_load",
    
    # Stage 4: Vocal separation from background music
    "source_separation",
    
    # Stage 5: Voice activity detection
    "pyannote_vad",
    
    # Stage 6: Speech-to-text transcription
    "asr",
    
    # Stage 7: Word-level alignment
    "alignment",
    
    # Stage 8: Song/lyrics detection
    "lyrics_detection",
    
    # Stage 9: Export transcript to plain text
    "export_transcript",
    
    # Stage 10: Translation (hybrid/indictrans2/nllb)
    "translation",
    "hybrid_translation",      # Alias for translation
    "indictrans2_translation",  # Alias for translation
    "nllb_translation",         # Alias for translation
    
    # Stage 11: Subtitle generation
    "subtitle_generation",
    "subtitle_generation_source",   # Alias for subtitle_generation
    "subtitle_generation_target",   # Alias for subtitle_generation
    
    # Stage 12: Muxing final output
    "mux",
]

# Sub-stages that belong to parent stages (don't get their own number)
SUB_STAGES: Dict[str, str] = {
    "hallucination_removal": "asr",  # Part of ASR stage
    "load_transcript": "translation",  # Part of translation stage
    "hinglish_detection": "subtitle_generation",  # Part of subtitle generation
}

# ============================================================================
# DERIVED MAPPINGS (AUTO-GENERATED)
# ============================================================================

def _generate_stage_numbers() -> Dict[str, int]:
    """
    Generate stage number mappings from STAGE_ORDER.
    
    Returns:
        Dictionary mapping stage names to numbers
    """
    stage_numbers = {}
    current_number = 1
    seen_base_stages = set()
    
    for stage_name in STAGE_ORDER:
        # Get base name (e.g., "translation" from "hybrid_translation")
        base_name = stage_name
        for alias in ["hybrid_", "indictrans2_", "nllb_", "subtitle_generation_"]:
            if stage_name.startswith(alias):
                if alias == "subtitle_generation_":
                    base_name = "subtitle_generation"
                else:
                    base_name = stage_name.replace(alias, "")
                break
        
        # Check if we've seen this base stage before
        if base_name not in seen_base_stages:
            seen_base_stages.add(base_name)
            stage_numbers[stage_name] = current_number
            current_number += 1
        else:
            # Alias for existing stage, use same number
            for existing_name, existing_num in stage_numbers.items():
                if existing_name == base_name or existing_name.endswith(base_name):
                    stage_numbers[stage_name] = existing_num
                    break
    
    # Add sub-stages (inherit parent's number)
    for sub_stage, parent_stage in SUB_STAGES.items():
        if parent_stage in stage_numbers:
            stage_numbers[sub_stage] = stage_numbers[parent_stage]
    
    return stage_numbers


def _generate_stage_dirs() -> List[str]:
    """
    Generate list of stage directories to create at job preparation.
    
    Returns:
        List of stage directory names (e.g., "01_demux")
    """
    stage_dirs = []
    seen_base_stages = set()
    
    for stage_name in STAGE_ORDER:
        # Get base name for grouping aliases
        base_name = stage_name
        for alias in ["hybrid_", "indictrans2_", "nllb_"]:
            if stage_name.startswith(alias):
                base_name = stage_name.replace(alias, "")
                break
        
        # Only create directory for base stage (not aliases)
        if base_name not in seen_base_stages:
            seen_base_stages.add(base_name)
            stage_num = STAGE_NUMBERS[stage_name]
            # Use base name for directory (not alias)
            if base_name.startswith("subtitle_generation_"):
                base_name = "subtitle_generation"
            stage_dirs.append(f"{stage_num:02d}_{base_name}")
    
    return stage_dirs


# Auto-generate mappings
STAGE_NUMBERS: Dict[str, int] = _generate_stage_numbers()
STAGE_DIRECTORIES: List[str] = _generate_stage_dirs()


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_stage_number(stage_name: str) -> int:
    """
    Get the stage number for a given stage name.
    
    Args:
        stage_name: Name of the stage
        
    Returns:
        Stage number (1-based)
        
    Raises:
        ValueError: If stage name is not found
    """
    if stage_name not in STAGE_NUMBERS:
        raise ValueError(f"Unknown stage: {stage_name}")
    return STAGE_NUMBERS[stage_name]


def get_stage_dir(stage_name: str, job_dir: Optional[str] = None) -> str:
    """
    Get the directory name for a stage.
    
    Args:
        stage_name: Name of the stage
        job_dir: Optional job directory to prepend
        
    Returns:
        Stage directory path (e.g., "01_demux" or "/path/to/job/01_demux")
    """
    stage_num = get_stage_number(stage_name)
    
    # Get base name (handle aliases)
    base_name = stage_name
    for alias in ["hybrid_", "indictrans2_", "nllb_"]:
        if stage_name.startswith(alias):
            base_name = stage_name.replace(alias, "")
            break
    if base_name.startswith("subtitle_generation_"):
        base_name = "subtitle_generation"
    
    # Sub-stages use parent directory
    if stage_name in SUB_STAGES:
        base_name = SUB_STAGES[stage_name]
    
    stage_dir = f"{stage_num:02d}_{base_name}"
    
    if job_dir:
        from pathlib import Path
        return str(Path(job_dir) / stage_dir)
    
    return stage_dir


def get_all_stage_dirs() -> List[str]:
    """
    Get list of all stage directories that should be created.
    
    Returns:
        List of stage directory names
    """
    return STAGE_DIRECTORIES.copy()


def print_stage_order():
    """Print the stage order for debugging/documentation."""
    print("\n" + "=" * 70)
    print("PIPELINE STAGE ORDER")
    print("=" * 70)
    
    seen = set()
    for stage_name in STAGE_ORDER:
        stage_num = STAGE_NUMBERS[stage_name]
        stage_dir = get_stage_dir(stage_name)
        
        # Only print base stages (not aliases)
        if stage_dir not in seen:
            seen.add(stage_dir)
            print(f"{stage_num:2d}. {stage_dir}")
    
    print("=" * 70)
    
    if SUB_STAGES:
        print("\nSub-stages (inherit parent number):")
        for sub, parent in SUB_STAGES.items():
            parent_num = STAGE_NUMBERS[parent]
            print(f"  {sub} → {parent} (stage {parent_num})")
        print("=" * 70)


# ============================================================================
# VALIDATION
# ============================================================================

def validate_stage_order():
    """
    Validate that stage order is consistent and has no conflicts.
    
    Raises:
        ValueError: If validation fails
    """
    # Check for duplicates in STAGE_ORDER
    seen_base = set()
    for stage_name in STAGE_ORDER:
        base = stage_name.split("_")[0] if "_" in stage_name else stage_name
        
        # Skip translation and subtitle aliases
        if base in ["hybrid", "indictrans2", "nllb", "subtitle"]:
            continue
            
        if base in seen_base and base != "translation" and base != "subtitle":
            raise ValueError(f"Duplicate base stage in STAGE_ORDER: {base}")
        seen_base.add(base)
    
    # Check that all sub-stages reference valid parent stages
    for sub_stage, parent_stage in SUB_STAGES.items():
        if parent_stage not in STAGE_NUMBERS:
            raise ValueError(f"Sub-stage '{sub_stage}' references unknown parent '{parent_stage}'")
    
    # Check that stage numbers are sequential
    unique_numbers = sorted(set(STAGE_NUMBERS.values()))
    expected_numbers = list(range(1, len(unique_numbers) + 1))
    if unique_numbers != expected_numbers:
        raise ValueError(f"Stage numbers not sequential: {unique_numbers}")


# Run validation on import
try:
    validate_stage_order()
except Exception as e:
    print(f"WARNING: Stage order validation failed: {e}")


# ============================================================================
# MAIN (for testing)
# ============================================================================

if __name__ == "__main__":
    print_stage_order()
    
    # Test some lookups
    print("\nExample lookups:")
    print(f"  get_stage_number('translation') = {get_stage_number('translation')}")
    print(f"  get_stage_number('hybrid_translation') = {get_stage_number('hybrid_translation')}")
    print(f"  get_stage_dir('translation') = {get_stage_dir('translation')}")
    print(f"  get_stage_dir('hybrid_translation') = {get_stage_dir('hybrid_translation')}")
    print(f"  get_stage_dir('hallucination_removal') = {get_stage_dir('hallucination_removal')}")
