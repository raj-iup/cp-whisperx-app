#!/usr/bin/env python3
"""
Analyze Media Similarity

This script analyzes media files to find similar content and shows
potential optimization opportunities.

Usage:
    # Analyze all media in out/ directory
    python3 tools/analyze-similarity.py
    
    # Analyze specific media file
    python3 tools/analyze-similarity.py --media in/sample.mp4
    
    # Show optimization statistics
    python3 tools/analyze-similarity.py --stats

Architecture Decision: AD-015 (ML-Based Adaptive Optimization) - Task #18
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
from shared.similarity_optimizer import SimilarityOptimizer

logger = get_logger(__name__)


def analyze_historical_jobs(jobs_dir: Path, optimizer: SimilarityOptimizer) -> None:
    """Analyze all historical jobs for similarity."""
    logger.info("📊 Analyzing historical jobs for similarity...")
    
    jobs_found = 0
    fingerprints_computed = 0
    
    # Scan job directories
    for date_dir in jobs_dir.iterdir():
        if not date_dir.is_dir():
            continue
        
        for user_dir in date_dir.iterdir():
            if not user_dir.is_dir():
                continue
            
            for job_dir in user_dir.iterdir():
                if not job_dir.is_dir() or not job_dir.name.startswith("job-"):
                    continue
                
                jobs_found += 1
                
                # Find media file in demux stage
                demux_dir = job_dir / "01_demux"
                if not demux_dir.exists():
                    continue
                
                # Look for audio or video file
                audio_file = demux_dir / "audio.wav"
                video_file = None
                
                # Try to find original media
                for ext in ['.mp4', '.mkv', '.avi', '.mov']:
                    candidates = list(demux_dir.glob(f"*{ext}"))
                    if candidates:
                        video_file = candidates[0]
                        break
                
                media_file = audio_file if audio_file.exists() else video_file
                
                if media_file and media_file.exists():
                    try:
                        optimizer.compute_fingerprint(media_file)
                        fingerprints_computed += 1
                    except Exception as e:
                        logger.debug(f"Failed to fingerprint {media_file}: {e}")
    
    logger.info(f"✅ Analyzed {jobs_found} jobs, computed {fingerprints_computed} fingerprints")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze media similarity for optimization"
    )
    parser.add_argument(
        "--media",
        type=Path,
        help="Analyze specific media file"
    )
    parser.add_argument(
        "--jobs-dir",
        type=Path,
        default=PROJECT_ROOT / "out",
        help="Root directory containing job subdirectories (default: out/)"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.75,
        help="Similarity threshold (default: 0.75)"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show optimization statistics"
    )
    
    args = parser.parse_args()
    
    logger.info("🔍 Media Similarity Analyzer")
    logger.info("=" * 60)
    
    # Initialize optimizer
    optimizer = SimilarityOptimizer(similarity_threshold=args.threshold)
    
    # Show stats?
    if args.stats:
        stats = optimizer.get_optimization_stats()
        
        logger.info("")
        logger.info("📈 Similarity Optimization Statistics:")
        logger.info("-" * 60)
        logger.info(f"  Total fingerprints:      {stats['total_fingerprints']}")
        logger.info(f"  Total decisions:         {stats['total_decisions']}")
        logger.info(f"  Average similarity:      {stats['average_similarity']:.0%}")
        logger.info(f"  High similarity pairs:   {stats['high_similarity_pairs']}")
        logger.info(f"  Cache size:              {stats['cache_size_mb']:.2f} MB")
        logger.info("-" * 60)
        
        return 0
    
    # Analyze specific media?
    if args.media:
        if not args.media.exists():
            logger.error(f"❌ Media file not found: {args.media}")
            return 1
        
        logger.info(f"📊 Analyzing: {args.media.name}")
        logger.info("")
        
        # Compute fingerprint
        fingerprint = optimizer.compute_fingerprint(args.media)
        
        logger.info("✅ Fingerprint computed:")
        logger.info(f"  • Media ID: {fingerprint.media_id[:16]}...")
        logger.info(f"  • Duration: {fingerprint.duration:.1f}s")
        logger.info(f"  • Audio hash: {fingerprint.audio_hash[:16]}...")
        logger.info("")
        
        # Find similar media
        matches = optimizer.find_similar_media(fingerprint, threshold=args.threshold)
        
        if matches:
            logger.info(f"🎯 Found {len(matches)} similar media:")
            logger.info("")
            
            for i, match in enumerate(matches[:5], 1):  # Show top 5
                logger.info(f"  {i}. Media ID: {match.reference_media_id[:16]}...")
                logger.info(f"     • Similarity: {match.similarity_score:.0%}")
                logger.info(f"     • Confidence: {match.confidence:.0%}")
                logger.info(f"     • Reusable: {', '.join(match.reusable_decisions)}")
                
                # Get reusable decision
                decision = optimizer.get_reusable_decisions(match)
                if decision:
                    logger.info(f"     • Previous model: {decision.model_used}")
                    logger.info(f"     • Previous time: {decision.processing_time:.1f}s")
                
                logger.info("")
        else:
            logger.info("⚠️  No similar media found")
            logger.info("💡 This media will be processed from scratch")
        
        return 0
    
    # Analyze all historical jobs
    if not args.jobs_dir.exists():
        logger.warning(f"⚠️  Jobs directory not found: {args.jobs_dir}")
        logger.info("💡 Run some jobs first to generate data")
        return 1
    
    analyze_historical_jobs(args.jobs_dir, optimizer)
    
    # Show similarity matrix
    logger.info("")
    logger.info("🔍 Computing similarity matrix...")
    
    fingerprints = list(optimizer.fingerprints.values())
    if len(fingerprints) < 2:
        logger.warning("⚠️  Need at least 2 media files for similarity analysis")
        return 1
    
    # Find all high-similarity pairs
    high_sim_pairs = []
    for i in range(len(fingerprints)):
        for j in range(i + 1, len(fingerprints)):
            fp1 = fingerprints[i]
            fp2 = fingerprints[j]
            
            similarity = optimizer._compute_similarity(fp1, fp2)
            if similarity >= args.threshold:
                high_sim_pairs.append((fp1, fp2, similarity))
    
    if high_sim_pairs:
        logger.info("")
        logger.info(f"🎯 Found {len(high_sim_pairs)} high-similarity pairs:")
        logger.info("")
        
        for fp1, fp2, similarity in sorted(high_sim_pairs, key=lambda x: -x[2])[:10]:
            logger.info(f"  • {fp1.media_id[:12]}... ↔ {fp2.media_id[:12]}...")
            logger.info(f"    Similarity: {similarity:.0%}")
            logger.info(f"    Duration: {fp1.duration:.0f}s vs {fp2.duration:.0f}s")
            logger.info("")
        
        # Estimate time savings
        logger.info("")
        logger.info("💡 Optimization Opportunities:")
        logger.info("-" * 60)
        
        total_pairs = len(high_sim_pairs)
        estimated_savings_per_pair = 300  # seconds (5 minutes average)
        total_savings = total_pairs * estimated_savings_per_pair
        
        logger.info(f"  • High-similarity pairs: {total_pairs}")
        logger.info(f"  • Est. time savings/pair: {estimated_savings_per_pair}s (5 min)")
        logger.info(f"  • Total potential savings: {total_savings}s ({total_savings/60:.1f} min)")
        logger.info(f"  • Reuse strategy: Copy decisions, skip ASR if >90% similar")
        logger.info("-" * 60)
    else:
        logger.info("")
        logger.info("⚠️  No high-similarity pairs found")
        logger.info(f"💡 Media files are unique (threshold: {args.threshold:.0%})")
    
    # Summary
    logger.info("")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info("✅ SIMILARITY ANALYSIS COMPLETE")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info("")
    logger.info("💡 Next Steps:")
    logger.info("  1. Future jobs will automatically detect similar media")
    logger.info("  2. Reuse processing decisions for 40-95% time reduction")
    logger.info("  3. High-similarity media (>90%) can reuse ASR results")
    logger.info("")
    logger.info("📚 Fingerprints stored in: ~/.cp-whisperx/similarity/")
    logger.info("  • fingerprints.json - Media fingerprints")
    logger.info("  • decisions.json - Processing decisions")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
