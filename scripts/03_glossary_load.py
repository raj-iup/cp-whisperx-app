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


def extract_glossary_from_youtube_metadata(metadata: Dict) -> List[Dict[str, str]]:
    """
    Extract glossary terms from YouTube video metadata.
    
    Enhancement #3: Auto-generate glossary from YouTube title/description.
    Extracts proper nouns, technical terms, and domain-specific vocabulary.
    
    Args:
        metadata: YouTube metadata dict with 'title', 'description', etc.
        
    Returns:
        List of glossary entries (format: {'term': str, 'type': str})
    """
    import re
    
    glossary_entries = []
    
    # Extract from title
    title = metadata.get('title', '')
    if title:
        logger.info(f"Extracting terms from title: {title}")
        
        # Extract words (3+ chars, starts with capital)
        title_words = re.findall(r'\b[A-Z][a-z]{2,}\b', title)
        for word in title_words:
            if word not in ['The', 'And', 'For', 'With', 'From']:  # Filter common words
                glossary_entries.append({
                    'term': word,
                    'type': 'proper_noun',
                    'source': 'youtube_title'
                })
        
        # Extract phrases in quotes
        quoted = re.findall(r'"([^"]+)"', title)
        for phrase in quoted:
            glossary_entries.append({
                'term': phrase,
                'type': 'quoted_phrase',
                'source': 'youtube_title'
            })
    
    # Extract from description (first 500 chars for performance)
    description = metadata.get('description', '')[:500]
    if description:
        logger.info(f"Extracting terms from description (first 500 chars)")
        
        # Extract hashtags
        hashtags = re.findall(r'#(\w+)', description)
        for tag in hashtags:
            glossary_entries.append({
                'term': tag,
                'type': 'hashtag',
                'source': 'youtube_description'
            })
        
        # Extract @mentions (channel names, people)
        mentions = re.findall(r'@([\w\-]+)', description)
        for mention in mentions:
            glossary_entries.append({
                'term': mention,
                'type': 'mention',
                'source': 'youtube_description'
            })
    
    # Deduplicate
    unique_terms = {}
    for entry in glossary_entries:
        term = entry['term']
        if term not in unique_terms:
            unique_terms[term] = entry
    
    glossary_entries = list(unique_terms.values())
    
    logger.info(f"Extracted {len(glossary_entries)} terms from YouTube metadata:")
    for entry in glossary_entries[:10]:  # Show first 10
        logger.info(f"  • {entry['term']} ({entry['type']})")
    if len(glossary_entries) > 10:
        logger.info(f"  ... and {len(glossary_entries) - 10} more")
    
    return glossary_entries


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
        
        # 1. Load system defaults from config
        config = load_config()
        
        # Get glossary directory (project root / glossary)
        project_root = Path(__file__).parent.parent.parent
        glossary_dir_default = project_root / "glossary"
        glossary_dir = glossary_dir_default
        workflow = config.get("WORKFLOW", "transcribe")
        
        # 2. Override with job.json parameters (AD-006)
        job_json_path = job_dir / "job.json"
        youtube_metadata = None  # Store YouTube metadata if available
        
        if job_json_path.exists():
            logger.info("Reading job-specific parameters from job.json...")
            with open(job_json_path) as f:
                job_data = json.load(f)
                
                # Enhancement #3: Extract YouTube metadata for glossary
                if 'youtube_metadata' in job_data and job_data['youtube_metadata']:
                    youtube_metadata = job_data['youtube_metadata']
                    logger.info("✓ YouTube metadata found in job.json")
                
                # Override glossary path if specified
                if 'glossary' in job_data:
                    glossary_config = job_data['glossary']
                    if 'path' in glossary_config and glossary_config['path']:
                        old_value = glossary_dir
                        glossary_dir = Path(glossary_config['path'])
                        logger.info(f"  glossary_path override: {old_value} → {glossary_dir} (from job.json)")
                
                # Override workflow if specified
                if 'workflow' in job_data and job_data['workflow']:
                    old_value = workflow
                    workflow = job_data['workflow']
                    logger.info(f"  workflow override: {old_value} → {workflow} (from job.json)")
        else:
            logger.warning(f"job.json not found at {job_json_path}, using system defaults")
        
        # 3. Track config in manifest
        io.add_config("glossary_dir", str(glossary_dir))
        io.add_config("workflow", workflow)
        
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
        
        # ========================================
        # YOUTUBE METADATA EXTRACTION (Enhancement #3)
        # ========================================
        if youtube_metadata:
            logger.info("=" * 80)
            logger.info("YouTube Metadata Glossary Extraction (Enhancement #3)")
            logger.info("=" * 80)
            
            youtube_entries = extract_glossary_from_youtube_metadata(youtube_metadata)
            
            if youtube_entries:
                # Convert YouTube entries to standard glossary format
                existing_terms = {e.get('term', '').lower() for e in entries}
                
                for yt_entry in youtube_entries:
                    term = yt_entry['term']
                    
                    # Skip if already in glossary
                    if term.lower() in existing_terms:
                        continue
                    
                    # Add to glossary with proper format
                    entries.append({
                        'term': term,
                        'alternatives': term,  # Use term itself as alternative
                        'english': term,  # Keep as-is for translation
                        'category': yt_entry['type'],
                        'source': 'youtube_metadata'
                    })
                
                logger.info(f"✓ Added {len(youtube_entries)} terms from YouTube metadata")
                logger.info(f"✓ Total glossary entries: {len(entries)}")
            else:
                logger.info("No terms extracted from YouTube metadata")
        
        # ========================================
        # CONTEXT LEARNING INTEGRATION (Task #17)
        # ========================================
        try:
            logger.info("=" * 80)
            logger.info("Context Learning Enhancement")
            logger.info("=" * 80)
            
            from shared.context_learner import get_context_learner
            
            # Check if context learning is enabled
            context_learning_enabled = config.get("ENABLE_CONTEXT_LEARNING", "true").lower() == "true"
            
            if context_learning_enabled:
                learner = get_context_learner()
                
                # Get source language
                source_lang = config.get("SOURCE_LANGUAGE", "hi")
                
                # Override with job.json if specified
                if job_json_path.exists():
                    with open(job_json_path) as f:
                        job_data = json.load(f)
                        if 'source_language' in job_data and job_data['source_language']:
                            source_lang = job_data['source_language']
                
                logger.info(f"Loading learned terms for language: {source_lang}")
                
                # Get learned character names
                character_names = learner.get_learned_terms(source_lang, category="character_name")
                logger.info(f"  Found {len(character_names)} learned character names")
                
                # Get learned cultural terms
                cultural_terms = learner.get_learned_terms(source_lang, category="cultural_term")
                logger.info(f"  Found {len(cultural_terms)} learned cultural terms")
                
                # Add learned terms to glossary
                original_count = len(entries)
                existing_terms = {e.get('term', '').lower() for e in entries}
                
                # Add character names (high confidence only)
                for learned in character_names:
                    if learned.term.lower() not in existing_terms and learned.confidence >= 0.7:
                        entries.append({
                            'term': learned.term,
                            'type': 'character_name',
                            'category': 'learned',
                            'alternatives': '',
                            'source': 'context_learning',
                            'confidence': learned.confidence,
                            'frequency': learned.frequency
                        })
                        existing_terms.add(learned.term.lower())
                        logger.debug(f"  Added learned character: {learned.term} (confidence: {learned.confidence:.1%})")
                
                # Add cultural terms (high confidence only)
                for learned in cultural_terms:
                    if learned.term.lower() not in existing_terms and learned.confidence >= 0.7:
                        entries.append({
                            'term': learned.term,
                            'type': 'cultural_term',
                            'category': 'learned',
                            'alternatives': '',
                            'source': 'context_learning',
                            'confidence': learned.confidence,
                            'frequency': learned.frequency
                        })
                        existing_terms.add(learned.term.lower())
                        logger.debug(f"  Added learned cultural term: {learned.term} (confidence: {learned.confidence:.1%})")
                
                learned_count = len(entries) - original_count
                if learned_count > 0:
                    logger.info(f"✓ Added {learned_count} learned terms to glossary")
                    
                    # Save enhanced glossary
                    enhanced_file = io.stage_dir / "glossary_enhanced.json"
                    with open(enhanced_file, 'w', encoding='utf-8') as f:
                        json.dump({
                            'original_count': original_count,
                            'learned_count': learned_count,
                            'total_count': len(entries),
                            'learned_terms': [
                                {
                                    'term': e['term'],
                                    'type': e.get('type', ''),
                                    'confidence': e.get('confidence', 0),
                                    'frequency': e.get('frequency', 0)
                                }
                                for e in entries if e.get('source') == 'context_learning'
                            ]
                        }, f, indent=2)
                    io.track_output(enhanced_file, "context_learning")
                    logger.info(f"✓ Enhanced glossary saved: {enhanced_file}")
                else:
                    logger.info("ℹ️  No new learned terms to add (all already in glossary)")
            else:
                logger.info("ℹ️  Context learning disabled")
                
        except Exception as e:
            # Don't fail the stage if context learning fails
            logger.warning(f"Context learning enhancement failed: {e}")
            logger.debug("Continuing with original glossary", exc_info=True)
        
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
