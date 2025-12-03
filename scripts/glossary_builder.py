#!/usr/bin/env python3
"""
Glossary Builder stage: Build comprehensive film-specific glossary

Integrates multiple sources:
- Master Hinglish glossary
- TMDB cast/crew data
- Film-specific overrides
- ASR transcript analysis

Generates:
- film_glossary.tsv (13-column comprehensive glossary)
- film_profile.json (metadata and statistics)
- coverage_report.json (quality metrics)

Compliance: DEVELOPER_STANDARDS.md
"""
import sys
import os
import json
import csv
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import Counter

# Add project root to path for shared imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.stage_utils import StageIO, get_stage_logger
from shared.config import load_config
from shared.glossary_manager import UnifiedGlossaryManager

# Local
from shared.logger import get_logger
logger = get_logger(__name__)

# Try to import MPS utils for future-proofing
try:
    from mps_utils import cleanup_mps_memory
    HAS_MPS_UTILS = True
except:
    HAS_MPS_UTILS = False


def generate_film_glossary_tsv(manager: UnifiedGlossaryManager) -> List[Dict[str, Any]]:
    """
    Generate film glossary in 13-column TSV format
    
    Returns:
        List of glossary entries as dicts
    """
    entries = []
    
    # Process master glossary
    for source_term, translations in manager.master_glossary.items():
        entries.append({
            'term': source_term,
            'script': 'rom',
            'rom': source_term,
            'hi': '',
            'type': 'idiom',
            'english': translations[0] if translations else source_term,
            'do_not_translate': 'false',
            'capitalize': 'false',
            'example_hi': '',
            'example_en': '',
            'aliases': '|'.join(translations) if len(translations) > 1 else '',
            'source': 'manual:master',
            'confidence': '1.0'
        })
    
    # Process TMDB glossary (character/cast names)
    for source_term, translations in manager.tmdb_glossary.items():
        entries.append({
            'term': source_term,
            'script': 'rom',
            'rom': source_term,
            'hi': '',
            'type': 'character',
            'english': translations[0] if translations else source_term,
            'do_not_translate': 'true',
            'capitalize': 'true',
            'example_hi': '',
            'example_en': '',
            'aliases': '|'.join(translations) if len(translations) > 1 else '',
            'source': 'tmdb:cast',
            'confidence': '0.95'
        })
    
    # Process film-specific glossary
    for source_term, translations in manager.film_specific.items():
        entries.append({
            'term': source_term,
            'script': 'rom',
            'rom': source_term,
            'hi': '',
            'type': 'film_specific',
            'english': translations[0] if translations else source_term,
            'do_not_translate': 'true',
            'capitalize': 'false',
            'example_hi': '',
            'example_en': '',
            'aliases': '|'.join(translations) if len(translations) > 1 else '',
            'source': 'film:override',
            'confidence': '1.0'
        })
    
    return entries


def generate_film_profile(
    manager: UnifiedGlossaryManager,
    tmdb_data: Optional[Dict],
    asr_data: Dict,
    glossary_entries: int
) -> Dict[str, Any]:
    """
    Generate film profile with metadata and statistics
    
    Args:
        manager: Glossary manager instance
        tmdb_data: TMDB enrichment data
        asr_data: ASR transcript data
        glossary_entries: Number of glossary entries
        
    Returns:
        Film profile dictionary
    """
    # Extract ASR statistics
    segments = asr_data.get('segments', [])
    total_words = sum(len(seg.get('text', '').split()) for seg in segments)
    unique_words = len(set(
        word for seg in segments 
        for word in seg.get('text', '').split()
    ))
    
    # Calculate duration
    if segments:
        last_segment = segments[-1]
        total_duration = last_segment.get('end', 0)
    else:
        total_duration = 0
    
    # Build profile
    profile = {
        'title': manager.film_title or 'Unknown',
        'year': str(manager.film_year) if manager.film_year else 'Unknown',
        'tmdb_id': tmdb_data.get('id', '') if tmdb_data else '',
        'runtime_minutes': tmdb_data.get('runtime', 0) if tmdb_data else 0,
        'language': tmdb_data.get('original_language', 'Unknown') if tmdb_data else 'Unknown',
        'cast': [],
        'crew': [],
        'statistics': {
            'glossary_entries': glossary_entries,
            'asr_segments': len(segments),
            'total_duration_seconds': int(total_duration),
            'total_words': total_words,
            'unique_words': unique_words
        },
        'glossary_breakdown': {
            'idiom': len(manager.master_glossary),
            'character': len(manager.tmdb_glossary),
            'film_specific': len(manager.film_specific),
            'learned': len(manager.learned_terms)
        },
        'generation_metadata': {
            'timestamp': datetime.now().isoformat(),
            'version': '1.0',
            'sources': [],
            'cache_hit': False
        }
    }
    
    # Add TMDB cast/crew if available
    if tmdb_data:
        profile['cast'] = tmdb_data.get('cast', [])[:20]  # Top 20
        profile['crew'] = [
            c for c in tmdb_data.get('crew', [])
            if c.get('job') in ['Director', 'Writer', 'Screenplay', 'Producer']
        ][:10]
        profile['generation_metadata']['sources'].append('tmdb')
    
    if len(manager.master_glossary) > 0:
        profile['generation_metadata']['sources'].append('master')
    
    if len(manager.film_specific) > 0:
        profile['generation_metadata']['sources'].append('film_specific')
    
    return profile


def generate_coverage_report(
    manager: UnifiedGlossaryManager,
    asr_data: Dict,
    glossary_entries: List[Dict]
) -> Dict[str, Any]:
    """
    Generate coverage report with quality metrics
    
    Args:
        manager: Glossary manager instance
        asr_data: ASR transcript data
        glossary_entries: Glossary entries
        
    Returns:
        Coverage report dictionary
    """
    segments = asr_data.get('segments', [])
    
    # Build term lookup
    glossary_terms = {entry['term'].lower() for entry in glossary_entries}
    
    # Analyze coverage
    segments_with_terms = 0
    term_usage = Counter()
    all_words = []
    
    for segment in segments:
        text = segment.get('text', '')
        words = text.split()
        all_words.extend(words)
        
        has_glossary_term = False
        for word in words:
            clean_word = word.strip('.,!?;:"\'"()[]{}').lower()
            if clean_word in glossary_terms:
                term_usage[clean_word] += 1
                has_glossary_term = True
        
        if has_glossary_term:
            segments_with_terms += 1
    
    # Calculate coverage percentage
    coverage_pct = (segments_with_terms / len(segments) * 100) if segments else 0
    
    # Find unused terms
    used_terms = set(term_usage.keys())
    unused_terms = [
        entry['term'] for entry in glossary_entries
        if entry['term'].lower() not in used_terms
    ][:20]  # Limit to top 20
    
    # Find unknown term candidates (frequent words not in glossary)
    word_freq = Counter(word.strip('.,!?;:"\'"()[]{}').lower() for word in all_words)
    unknown_candidates = []
    
    for word, freq in word_freq.most_common(100):
        if (word not in glossary_terms and 
            len(word) > 2 and 
            word.isalpha() and
            freq >= 3):
            unknown_candidates.append({
                'term': word,
                'frequency': freq,
                'confidence': min(0.99, freq / len(segments))
            })
    
    unknown_candidates = unknown_candidates[:20]  # Top 20
    
    # Calculate quality metrics
    total_words = len(all_words)
    glossary_word_count = sum(term_usage.values())
    term_precision = len(used_terms) / len(glossary_entries) if glossary_entries else 0
    term_recall = glossary_word_count / total_words if total_words > 0 else 0
    
    # Build report
    report = {
        'total_segments': len(segments),
        'segments_with_glossary_terms': segments_with_terms,
        'coverage_pct': round(coverage_pct, 2),
        'terms_used': dict(term_usage.most_common(30)),  # Top 30
        'terms_unused': unused_terms,
        'unknown_term_candidates': unknown_candidates,
        'quality_metrics': {
            'term_precision': round(term_precision, 2),
            'term_recall': round(term_recall, 4),
            'avg_confidence': 0.87  # Placeholder
        },
        'recommendations': []
    }
    
    # Add recommendations
    if unknown_candidates:
        for candidate in unknown_candidates[:5]:
            report['recommendations'].append(
                f"Consider adding '{candidate['term']}' (appears {candidate['frequency']} times)"
            )
    
    if len(unused_terms) > len(glossary_entries) * 0.5:
        report['recommendations'].append(
            "Many glossary terms unused - consider refining glossary"
        )
    
    if coverage_pct < 50:
        report['recommendations'].append(
            "Low coverage - consider expanding glossary with more terms"
        )
    
    return report


def main():
    stage_io = None
    logger = None
    
    try:
        # Initialize StageIO with manifest tracking
        stage_io = StageIO("glossary_load", enable_manifest=True)
        logger = stage_io.get_stage_logger("INFO")
        
        logger.info("=" * 60)
        logger.info("GLOSSARY BUILDER STAGE")
        logger.info("=" * 60)
        
        # Load configuration
        try:
            config = load_config()
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            stage_io.add_error(f"Config load failed: {e}", e)
            stage_io.finalize(status="failed")
            return 1
        
        # Get configuration parameters
        glossary_enabled = getattr(config, 'glossary_enable', True)
        glossary_strategy = getattr(config, 'glossary_strategy', 'cascade')
        glossary_cache_enabled = getattr(config, 'glossary_cache_enabled', True)
        glossary_learning_enabled = getattr(config, 'glossary_learning_enabled', False)
        glossary_seed_sources = getattr(config, 'glossary_seed_sources', 'asr,tmdb,master')
        glossary_min_conf = getattr(config, 'glossary_min_conf', 0.55)
        
        logger.info(f"Glossary enabled: {glossary_enabled}")
        logger.info(f"Strategy: {glossary_strategy}")
        logger.info(f"Seed sources: {glossary_seed_sources}")
        logger.info(f"Min confidence: {glossary_min_conf}")
        logger.info(f"Caching: {glossary_cache_enabled}")
        
        # Track configuration
        stage_io.set_config({
            "glossary_enable": glossary_enabled,
            "glossary_strategy": glossary_strategy,
            "glossary_seed_sources": glossary_seed_sources,
            "glossary_min_conf": glossary_min_conf,
            "glossary_cache_enabled": glossary_cache_enabled,
            "glossary_learning_enabled": glossary_learning_enabled
        })
        
        if not glossary_enabled:
            logger.info("Glossary building disabled, skipping...")
            logger.info("=" * 60)
            stage_io.finalize(status="skipped", reason="Glossary disabled in config")
            return 0
        
        # Get input files using StageIO
        asr_file = stage_io.get_input_path("transcript.json", from_stage="asr")
        tmdb_file = stage_io.get_input_path("enrichment.json", from_stage="tmdb")
        
        logger.info(f"ASR transcript: {asr_file}")
        logger.info(f"TMDB enrichment: {tmdb_file}")
        
        # Check ASR file (required)
        if not asr_file.exists():
            logger.warning(f"ASR output not found: {asr_file}")
            logger.warning("Skipping glossary building (not critical)")
            stage_io.add_warning("ASR output not found")
            stage_io.finalize(status="skipped", reason="No ASR output")
            return 0  # Not critical, continue pipeline
        
        # Track inputs
        stage_io.track_input(asr_file, "transcript", format="json")
        if tmdb_file.exists():
            stage_io.track_input(tmdb_file, "tmdb_enrichment", format="json")
        
        # Read ASR transcript
        logger.info("Reading ASR transcript...")
        with open(asr_file, 'r', encoding='utf-8', errors='replace') as f:
            asr_data = json.load(f)
        
        segments = asr_data.get('segments', [])
        logger.info(f"Found {len(segments)} segments in transcript")
        
        # Read TMDB data (optional)
        tmdb_data = None
        if tmdb_file.exists():
            logger.info("Reading TMDB enrichment data...")
            with open(tmdb_file, 'r', encoding='utf-8', errors='replace') as f:
                tmdb_data = json.load(f)
            
            film_title = tmdb_data.get('title', 'Unknown')
            film_year = tmdb_data.get('release_date', '')[:4] if tmdb_data.get('release_date') else None
            logger.info(f"Film: {film_title} ({film_year})")
        else:
            logger.warning("TMDB enrichment not available (will use master glossary only)")
            film_title = None
            film_year = None
        
        # Initialize UnifiedGlossaryManager
        logger.info("Initializing glossary manager...")
        manager = UnifiedGlossaryManager(
            project_root=PROJECT_ROOT,
            film_title=film_title,
            film_year=int(film_year) if film_year and film_year.isdigit() else None,
            tmdb_enrichment_path=tmdb_file if tmdb_file.exists() else None,
            enable_cache=glossary_cache_enabled,
            enable_learning=glossary_learning_enabled,
            strategy=glossary_strategy,
            logger=logger
        )
        
        # Load all glossary sources
        logger.info("Loading glossary sources...")
        stats = manager.load_all_sources()
        
        logger.info(f"✓ Loaded {stats['master_terms']} master terms")
        logger.info(f"✓ Loaded {stats['tmdb_terms']} TMDB terms")
        logger.info(f"✓ Loaded {stats['film_terms']} film-specific terms")
        logger.info(f"✓ Total unique terms: {stats['total_terms']}")
        if stats.get('cache_hit'):
            logger.info("✓ Used cached TMDB glossary")
        
        # Generate film glossary (13-column TSV format)
        logger.info("Generating film glossary...")
        glossary_entries = generate_film_glossary_tsv(manager)
        
        # Save film_glossary.tsv
        glossary_file = stage_io.output_dir / "film_glossary.tsv"
        with open(glossary_file, 'w', encoding='utf-8', newline='') as f:
            if glossary_entries:
                writer = csv.DictWriter(f, fieldnames=glossary_entries[0].keys(), delimiter='\t')
                writer.writeheader()
                writer.writerows(glossary_entries)
        
        logger.info(f"✓ Saved {len(glossary_entries)} entries to film_glossary.tsv")
        stage_io.track_output(glossary_file, "film_glossary", 
                              format="tsv", entries=len(glossary_entries))
        
        # Generate film profile
        logger.info("Generating film profile...")
        film_profile = generate_film_profile(manager, tmdb_data, asr_data, len(glossary_entries))
        
        profile_file = stage_io.save_json(film_profile, "film_profile.json")
        logger.info(f"✓ Saved film profile to {profile_file.name}")
        stage_io.track_output(profile_file, "film_profile", format="json")
        
        # Generate coverage report
        logger.info("Generating coverage report...")
        coverage_report = generate_coverage_report(manager, asr_data, glossary_entries)
        
        coverage_file = stage_io.save_json(coverage_report, "coverage_report.json")
        logger.info(f"✓ Saved coverage report to {coverage_file.name}")
        logger.info(f"  Coverage: {coverage_report['coverage_pct']}% of segments")
        logger.info(f"  Used terms: {len(coverage_report['terms_used'])}")
        logger.info(f"  Unused terms: {len(coverage_report['terms_unused'])}")
        logger.info(f"  Candidates: {len(coverage_report['unknown_term_candidates'])}")
        
        stage_io.track_output(coverage_file, "coverage_report", format="json",
                              coverage_pct=coverage_report['coverage_pct'])
        
        # Save glossary snapshot for debugging
        snapshot_file = stage_io.output_dir / "glossary_snapshot.json"
        manager.save_snapshot(snapshot_file)
        stage_io.track_intermediate(snapshot_file, retained=True,
                                   reason="Debugging snapshot")
        
        # Finalize with success
        stage_io.finalize(
            status="success",
            glossary_entries=len(glossary_entries),
            coverage_pct=coverage_report['coverage_pct'],
            cache_hit=stats.get('cache_hit', False),
            sources=film_profile['generation_metadata']['sources']
        )
        
        logger.info("=" * 60)
        logger.info("GLOSSARY BUILDER COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Outputs:")
        logger.info(f"  • film_glossary.tsv: {len(glossary_entries)} entries")
        logger.info(f"  • film_profile.json: metadata + statistics")
        logger.info(f"  • coverage_report.json: quality metrics")
        logger.info(f"Stage log: {stage_io.stage_log.relative_to(stage_io.output_base)}")
        logger.info(f"Stage manifest: {stage_io.manifest_path.relative_to(stage_io.output_base)}")
        
        # Cleanup memory
        if HAS_MPS_UTILS:
            cleanup_mps_memory()
        
        return 0
        
        return 0
        
    except FileNotFoundError as e:
        if logger:
            logger.error(f"File not found: {e}", exc_info=True)
        if stage_io:
            stage_io.add_error(f"File not found: {e}")
            stage_io.finalize(status="failed", error=f"Missing file: {e}")
        return 1
    
    except IOError as e:
        if logger:
            logger.error(f"I/O error: {e}", exc_info=True)
        if stage_io:
            stage_io.add_error(f"I/O error: {e}")
            stage_io.finalize(status="failed", error=f"IO error: {e}")
        return 1
    
    except json.JSONDecodeError as e:
        if logger:
            logger.error(f"Invalid JSON in input: {e}", exc_info=True)
        if stage_io:
            stage_io.add_error(f"JSON decode error: {e}")
            stage_io.finalize(status="failed", error=f"Invalid JSON: {e}")
        return 1
    
    except KeyboardInterrupt:
        if logger:
            logger.warning("Interrupted by user")
        if stage_io:
            stage_io.add_error("User interrupted")
            stage_io.finalize(status="failed", error="User interrupted")
        return 130
    
    except Exception as e:
        if logger:
            logger.error(f"Glossary building failed: {e}", exc_info=True)
        else:
            print(f"ERROR: {e}", file=sys.stderr)
        if stage_io:
            stage_io.add_error(f"Glossary build failed: {e}")
            stage_io.finalize(status="failed", error=str(e))
        return 1

if __name__ == "__main__":
    sys.exit(main())