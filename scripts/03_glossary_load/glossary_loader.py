#!/usr/bin/env python3
"""
Glossary Load Stage (03_glossary_load)

Loads glossary files and prepares them for use in downstream stages
(ASR biasing, translation preservation, NER correction).

Input: Glossary files from glossary/ directory
Output: Processed glossary data structures
"""

# Standard library
import sys
import json
import csv
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Local
from shared.stage_utils import StageIO
from shared.config import load_config
from shared.logger import get_logger

logger = get_logger(__name__)


def load_tsv_glossary(tsv_path: Path) -> List[Dict[str, str]]:
    """
    Load TSV glossary file.
    
    Args:
        tsv_path: Path to TSV file
        
    Returns:
        List of glossary entries as dicts
    """
    entries = []
    
    try:
        with open(tsv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                entries.append(row)
        
        logger.info(f"Loaded {len(entries)} entries from {tsv_path.name}")
        
    except Exception as e:
        logger.error(f"Failed to load {tsv_path}: {e}", exc_info=True)
        
    return entries


def prepare_asr_glossary(entries: List[Dict[str, str]]) -> Dict[str, List[str]]:
    """
    Prepare glossary for ASR biasing.
    
    Args:
        entries: Raw glossary entries
        
    Returns:
        Dict mapping terms to alternatives for ASR
    """
    asr_glossary = {}
    
    for entry in entries:
        term = entry.get('term', '').strip()
        alternatives = entry.get('alternatives', '').strip()
        
        if term:
            # Split alternatives and add term itself
            alt_list = [term]
            if alternatives:
                alt_list.extend([a.strip() for a in alternatives.split('|') if a.strip()])
            
            asr_glossary[term] = list(set(alt_list))  # Remove duplicates
    
    logger.info(f"Prepared ASR glossary with {len(asr_glossary)} terms")
    return asr_glossary


def prepare_translation_glossary(entries: List[Dict[str, str]]) -> Dict[str, str]:
    """
    Prepare glossary for translation preservation.
    
    Args:
        entries: Raw glossary entries
        
    Returns:
        Dict mapping source terms to preferred translations
    """
    trans_glossary = {}
    
    for entry in entries:
        term = entry.get('term', '').strip()
        english = entry.get('english', '').strip()
        
        if term and english:
            # Use first alternative if multiple
            if '|' in english:
                english = english.split('|')[0].strip()
            trans_glossary[term] = english
    
    logger.info(f"Prepared translation glossary with {len(trans_glossary)} terms")
    return trans_glossary


def run_stage(job_dir: Path, stage_name: str = "03_glossary_load") -> int:
    """
    Glossary Load Stage
    
    Loads glossary files and prepares them for downstream stages.
    
    Args:
        job_dir: Job directory
        stage_name: Stage name for logging
        
    Returns:
        0 on success, 1 on failure
    """
    io = StageIO(stage_name, job_dir, enable_manifest=True)
    logger = io.get_stage_logger()
    
    try:
        logger.info("=" * 80)
        logger.info("STAGE: Glossary Load")
        logger.info("=" * 80)
        
        # Load configuration
        config = load_config()
        
        # Get glossary directory (project root / glossary)
        project_root = Path(__file__).parent.parent.parent
        glossary_dir = project_root / "glossary"
        
        if not glossary_dir.exists():
            logger.warning(f"Glossary directory not found: {glossary_dir}")
            logger.info("Creating empty glossary outputs")
            
            # Create empty outputs
            asr_file = io.stage_dir / "glossary_asr.json"
            trans_file = io.stage_dir / "glossary_translation.json"
            
            with open(asr_file, 'w') as f:
                json.dump({}, f, indent=2)
            with open(trans_file, 'w') as f:
                json.dump({}, f, indent=2)
            
            io.track_output(asr_file, "glossary")
            io.track_output(trans_file, "glossary")
            
            io.finalize(status="success")
            return 0
        
        logger.info(f"Loading glossaries from: {glossary_dir}")
        
        # Load unified glossary (primary source)
        unified_tsv = glossary_dir / "unified_glossary.tsv"
        entries = []
        
        if unified_tsv.exists():
            logger.info(f"Loading unified glossary: {unified_tsv}")
            io.track_input(unified_tsv, "glossary")
            entries = load_tsv_glossary(unified_tsv)
        else:
            logger.warning(f"Unified glossary not found: {unified_tsv}")
        
        # Load Hinglish master glossary (additional source)
        hinglish_tsv = glossary_dir / "hinglish_master.tsv"
        if hinglish_tsv.exists() and hinglish_tsv != unified_tsv:
            logger.info(f"Loading Hinglish master glossary: {hinglish_tsv}")
            io.track_input(hinglish_tsv, "glossary")
            hinglish_entries = load_tsv_glossary(hinglish_tsv)
            
            # Merge with unified (unified takes precedence)
            existing_terms = {e.get('term', '') for e in entries}
            for entry in hinglish_entries:
                if entry.get('term', '') not in existing_terms:
                    entries.append(entry)
        
        logger.info(f"Total glossary entries loaded: {len(entries)}")
        
        # Prepare ASR glossary
        asr_glossary = prepare_asr_glossary(entries)
        asr_file = io.stage_dir / "glossary_asr.json"
        with open(asr_file, 'w', encoding='utf-8') as f:
            json.dump(asr_glossary, f, indent=2, ensure_ascii=False)
        io.track_output(asr_file, "glossary")
        logger.info(f"Created ASR glossary: {asr_file}")
        
        # Prepare translation glossary
        trans_glossary = prepare_translation_glossary(entries)
        trans_file = io.stage_dir / "glossary_translation.json"
        with open(trans_file, 'w', encoding='utf-8') as f:
            json.dump(trans_glossary, f, indent=2, ensure_ascii=False)
        io.track_output(trans_file, "glossary")
        logger.info(f"Created translation glossary: {trans_file}")
        
        # Save raw entries for reference
        raw_file = io.stage_dir / "glossary_raw.json"
        with open(raw_file, 'w', encoding='utf-8') as f:
            json.dump(entries, f, indent=2, ensure_ascii=False)
        io.track_output(raw_file, "glossary")
        logger.info(f"Created raw glossary: {raw_file}")
        
        # Summary
        logger.info("=" * 80)
        logger.info("Glossary Load Complete")
        logger.info(f"  Total entries: {len(entries)}")
        logger.info(f"  ASR terms: {len(asr_glossary)}")
        logger.info(f"  Translation terms: {len(trans_glossary)}")
        logger.info("=" * 80)
        
        io.finalize(status="success")
        return 0
        
    except Exception as e:
        logger.error(f"Glossary load stage failed: {e}", exc_info=True)
        io.finalize(status="failed")
        return 1


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Glossary Load Stage")
    parser.add_argument("--job-dir", type=Path, required=True, help="Job directory")
    parser.add_argument("--stage-name", default="03_glossary_load", help="Stage name")
    
    args = parser.parse_args()
    
    exit_code = run_stage(args.job_dir, args.stage_name)
    sys.exit(exit_code)
