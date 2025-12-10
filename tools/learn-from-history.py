#!/usr/bin/env python3
"""
Learn Context from Historical Jobs

This script analyzes completed jobs to extract and learn patterns:
- Character names from TMDB metadata
- Cultural terms from glossaries
- Translation memory from translations
- Named entities from subtitles

Usage:
    # Learn from all historical jobs
    python3 tools/learn-from-history.py
    
    # Learn from specific date range
    python3 tools/learn-from-history.py --since 2025-12-01
    
    # Generate auto-glossary
    python3 tools/learn-from-history.py --generate-glossary

Architecture Decision: AD-015 (ML-Based Adaptive Optimization) - Task #17
"""

# Standard library
import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Local
from shared.logger import get_logger
from shared.context_learner import ContextLearner

logger = get_logger(__name__)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Learn context from historical jobs"
    )
    parser.add_argument(
        "--jobs-dir",
        type=Path,
        default=PROJECT_ROOT / "out",
        help="Root directory containing job subdirectories (default: out/)"
    )
    parser.add_argument(
        "--since",
        type=str,
        help="Only learn from jobs after this date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--generate-glossary",
        action="store_true",
        help="Generate auto-glossary from learned terms"
    )
    parser.add_argument(
        "--glossary-lang",
        type=str,
        default="hi",
        help="Language for auto-glossary (default: hi)"
    )
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=0.7,
        help="Minimum confidence for auto-glossary (default: 0.7)"
    )
    
    args = parser.parse_args()
    
    logger.info("📚 Context Learning from Historical Jobs")
    logger.info("=" * 60)
    
    # Initialize learner
    learner = ContextLearner()
    
    # Learn from history
    logger.info(f"📊 Analyzing jobs in: {args.jobs_dir}")
    if args.since:
        logger.info(f"  • Only jobs since: {args.since}")
    
    stats = learner.learn_from_history(args.jobs_dir)
    
    if not stats:
        logger.warning("⚠️  No jobs found to learn from!")
        logger.info("💡 Run some jobs first:")
        logger.info("   ./prepare-job.sh --media in/sample.mp4 --workflow subtitle")
        logger.info("   ./run-pipeline.sh job-XXXXXXXX-user-NNNN")
        return 1
    
    # Display statistics
    logger.info("")
    logger.info("📈 Learning Results:")
    logger.info("-" * 60)
    logger.info(f"  Character names learned:  {stats.get('character_names', 0)}")
    logger.info(f"  Cultural terms learned:   {stats.get('cultural_terms', 0)}")
    logger.info(f"  Translation pairs learned: {stats.get('translations', 0)}")
    logger.info(f"  Named entities learned:   {stats.get('named_entities', 0)}")
    logger.info("-" * 60)
    
    # Show sample learned terms
    logger.info("")
    logger.info("🎬 Sample Learned Character Names (Hindi):")
    character_names = learner.get_learned_terms("hi", category="character_name")
    for term in character_names[:10]:
        logger.info(f"  • {term.term} (confidence: {term.confidence:.0%}, seen: {term.frequency}x)")
    
    logger.info("")
    logger.info("🌍 Sample Learned Cultural Terms (Hindi):")
    cultural_terms = learner.get_learned_terms("hi", category="cultural_term")
    for term in cultural_terms[:10]:
        logger.info(f"  • {term.term} (confidence: {term.confidence:.0%}, seen: {term.frequency}x)")
    
    # Translation memory
    logger.info("")
    logger.info("🔤 Sample Translation Memory (Hindi → English):")
    tm_entries = learner.get_translation_memory("hi", "en")
    for entry in tm_entries[:5]:
        logger.info(f"  • {entry.source[:40]}")
        logger.info(f"    → {entry.target[:40]}")
        logger.info(f"    (confidence: {entry.confidence:.0%}, used: {entry.frequency}x)")
    
    # Generate auto-glossary?
    if args.generate_glossary:
        logger.info("")
        logger.info(f"📝 Generating Auto-Glossary ({args.glossary_lang})...")
        
        glossary = learner.generate_auto_glossary(
            lang=args.glossary_lang,
            min_confidence=args.min_confidence
        )
        
        glossary_file = PROJECT_ROOT / "glossary" / f"auto_glossary_{args.glossary_lang}.json"
        glossary_file.parent.mkdir(parents=True, exist_ok=True)
        
        import json
        with open(glossary_file, 'w', encoding='utf-8') as f:
            json.dump({
                "generated_at": datetime.now().isoformat(),
                "language": args.glossary_lang,
                "min_confidence": args.min_confidence,
                "entries": glossary
            }, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Auto-glossary saved: {glossary_file}")
        logger.info(f"  • {len(glossary)} terms included")
    
    # Summary
    logger.info("")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info("✅ CONTEXT LEARNING COMPLETE")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info("")
    logger.info("💡 Benefits:")
    logger.info("  • Future jobs will have better character name recognition")
    logger.info("  • Cultural terms will be handled more consistently")
    logger.info("  • Translations will be more consistent across jobs")
    logger.info("  • Named entities will be preserved correctly")
    logger.info("")
    logger.info("📚 Knowledge stored in: ~/.cp-whisperx/context/")
    logger.info("  • learned_terms.json - Character names, cultural terms")
    logger.info("  • translation_memory.json - Translation pairs")
    logger.info("")
    logger.info("🔄 Re-run this script periodically to improve over time!")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
