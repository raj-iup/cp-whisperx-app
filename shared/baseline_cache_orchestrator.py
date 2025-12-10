#!/usr/bin/env python3
"""
Baseline cache orchestrator for AD-014 multi-phase subtitle workflow.

Coordinates baseline generation (demux, VAD, ASR, alignment) with caching
to enable 70-80% faster subsequent runs on same media.

Architecture Decision: AD-014 (Multi-Phase Subtitle Workflow)
"""
# Standard library
from pathlib import Path
import json
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime

# Local
from shared.media_identity import compute_media_id
from shared.cache_manager import MediaCacheManager, BaselineArtifacts
from shared.workflow_cache import WorkflowCacheIntegration
from shared.logger import get_logger

logger = get_logger(__name__)


class BaselineCacheOrchestrator:
    """
    Orchestrates baseline generation with intelligent caching.
    
    Phases:
    1. Check cache for existing baseline
    2. If cached: restore to job directories, skip stages 01-07
    3. If not cached: run stages 01-07, store in cache
    
    Usage:
        >>> orchestrator = BaselineCacheOrchestrator(job_dir)
        >>> 
        >>> # Check and restore from cache
        >>> if orchestrator.try_restore_from_cache(media_file):
        >>>     logger.info("✅ Using cached baseline")
        >>>     # Skip to stage 08 (lyrics detection)
        >>> else:
        >>>     # Run baseline stages 01-07
        >>>     run_baseline_stages()
        >>>     # Store in cache
        >>>     orchestrator.store_baseline_to_cache(media_file)
    """
    
    def __init__(
        self,
        job_dir: Path,
        enabled: bool = True,
        skip_cache: bool = False
    ):
        """
        Initialize baseline cache orchestrator.
        
        Args:
            job_dir: Job directory path
            enabled: Enable caching (default: True)
            skip_cache: Force regeneration even if cached (default: False)
        """
        self.job_dir = Path(job_dir)
        self.enabled = enabled and not skip_cache
        self.cache_integration = WorkflowCacheIntegration(
            job_dir,
            enabled=self.enabled
        )
        self.media_id: Optional[str] = None
    
    def try_restore_from_cache(self, media_file: Path) -> bool:
        """
        Attempt to restore baseline from cache.
        
        If successful, creates stage output directories (01-07) with
        cached artifacts so workflow can continue from stage 08.
        
        Args:
            media_file: Original media file
            
        Returns:
            True if restored from cache, False if needs generation
        """
        if not self.enabled:
            logger.info("🔄 Cache disabled - will generate baseline")
            return False
        
        try:
            logger.info("=" * 80)
            logger.info("🔍 Checking for cached baseline...")
            logger.info("=" * 80)
            
            # Compute media ID
            logger.info(f"📁 Media: {media_file.name}")
            self.media_id = compute_media_id(media_file)
            logger.info(f"🔑 Media ID: {self.media_id[:16]}...")
            
            # Check cache
            if not self.cache_integration.is_cached_baseline_available(media_file):
                logger.info("🆕 No cached baseline found")
                logger.info("📝 Will generate baseline (stages 01-07)")
                return False
            
            # Load from cache
            logger.info("✅ Found cached baseline!")
            logger.info("📂 Loading artifacts from cache...")
            
            baseline = self.cache_integration.load_cached_baseline()
            
            if not baseline:
                logger.warning("⚠️  Failed to load cached baseline")
                logger.info("📝 Will regenerate baseline")
                return False
            
            # Restore to job directories
            logger.info("📝 Restoring cached artifacts to job directories...")
            
            if not self.cache_integration.restore_baseline_to_job(baseline):
                logger.warning("⚠️  Failed to restore baseline to job")
                logger.info("📝 Will regenerate baseline")
                return False
            
            # Log statistics
            logger.info("")
            logger.info("=" * 80)
            logger.info("✅ BASELINE RESTORED FROM CACHE")
            logger.info("=" * 80)
            logger.info(f"📊 Segments: {len(baseline['segments'])}")
            logger.info(f"📊 Aligned: {len(baseline['aligned_segments'])}")
            logger.info(f"📊 VAD: {len(baseline['vad_segments'])}")
            logger.info(f"⏱️  Time saved: ~70-80% (stages 01-07 skipped)")
            logger.info(f"🎯 Pipeline will continue from stage 08")
            logger.info("=" * 80)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Cache restoration failed: {e}", exc_info=True)
            logger.info("📝 Will regenerate baseline")
            return False
    
    def store_baseline_to_cache(self, media_file: Path) -> bool:
        """
        Store generated baseline to cache.
        
        Call after stages 01-07 complete to cache baseline for future runs.
        
        Args:
            media_file: Original media file
            
        Returns:
            True if stored successfully
        """
        if not self.enabled:
            logger.debug("Cache disabled - skipping storage")
            return False
        
        try:
            logger.info("")
            logger.info("=" * 80)
            logger.info("💾 Storing baseline in cache...")
            logger.info("=" * 80)
            
            # Gather baseline artifacts from stage outputs
            baseline_data = self._gather_baseline_artifacts()
            
            if not baseline_data:
                logger.error("❌ Failed to gather baseline artifacts")
                return False
            
            # Store in cache
            success = self.cache_integration.store_baseline(
                media_file=media_file,
                audio_file=baseline_data['audio_file'],
                segments=baseline_data['segments'],
                aligned_segments=baseline_data['aligned_segments'],
                vad_segments=baseline_data['vad_segments'],
                diarization=baseline_data.get('diarization')
            )
            
            if success:
                logger.info("=" * 80)
                logger.info("✅ BASELINE CACHED SUCCESSFULLY")
                logger.info("=" * 80)
                logger.info(f"🎯 Subsequent runs will be 70-80% faster!")
                logger.info(f"💾 Cache location: ~/.cp-whisperx/cache")
                logger.info("=" * 80)
            else:
                logger.warning("⚠️  Failed to store baseline in cache")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Failed to store baseline: {e}", exc_info=True)
            return False
    
    def _gather_baseline_artifacts(self) -> Optional[Dict[str, Any]]:
        """
        Gather baseline artifacts from stage output directories.
        
        Returns:
            Dictionary with baseline artifacts, or None if incomplete
        """
        try:
            # Stage 01: Audio file
            audio_file = self.job_dir / "01_demux" / "audio.wav"
            if not audio_file.exists():
                logger.error("❌ Audio file not found in 01_demux/")
                return None
            
            # Stage 05: VAD segments
            vad_file = self.job_dir / "05_vad" / "vad_segments.json"
            if not vad_file.exists():
                logger.error("❌ VAD segments not found in 05_vad/")
                return None
            
            with open(vad_file) as f:
                vad_segments = json.load(f)
            
            # Stage 06: ASR segments
            segments_file = self.job_dir / "06_asr" / "segments.json"
            if not segments_file.exists():
                # Try alternative names
                for alt_name in ["asr_segments.json", "transcript.json", "whisperx_output.json"]:
                    alt_file = self.job_dir / "06_asr" / alt_name
                    if alt_file.exists():
                        segments_file = alt_file
                        break
                else:
                    logger.error("❌ ASR segments not found in 06_asr/")
                    return None
            
            with open(segments_file) as f:
                segments = json.load(f)
            
            # Handle wrapped format
            if isinstance(segments, dict) and 'segments' in segments:
                segments = segments['segments']
            
            # Stage 07: Aligned segments
            aligned_file = self.job_dir / "07_alignment" / "aligned_segments.json"
            if not aligned_file.exists():
                logger.warning("⚠️  Aligned segments not found, using ASR segments")
                aligned_segments = segments
            else:
                with open(aligned_file) as f:
                    aligned_segments = json.load(f)
                
                # Handle wrapped format
                if isinstance(aligned_segments, dict) and 'segments' in aligned_segments:
                    aligned_segments = aligned_segments['segments']
            
            # Diarization (optional)
            diarization = None
            diarization_file = self.job_dir / "07_alignment" / "diarization.json"
            if diarization_file.exists():
                with open(diarization_file) as f:
                    diarization = json.load(f)
            
            logger.info(f"✓ Gathered audio file: {audio_file.name}")
            logger.info(f"✓ Gathered {len(segments)} ASR segments")
            logger.info(f"✓ Gathered {len(aligned_segments)} aligned segments")
            logger.info(f"✓ Gathered {len(vad_segments)} VAD segments")
            if diarization:
                logger.info(f"✓ Gathered diarization data")
            
            return {
                'audio_file': audio_file,
                'segments': segments,
                'aligned_segments': aligned_segments,
                'vad_segments': vad_segments,
                'diarization': diarization
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to gather baseline artifacts: {e}", exc_info=True)
            return None
    
    def invalidate_cache(self, media_file: Path) -> bool:
        """
        Invalidate cached baseline for media.
        
        Args:
            media_file: Media file to invalidate
            
        Returns:
            True if invalidated successfully
        """
        try:
            media_id = compute_media_id(media_file)
            # Use the same cache manager instance
            return self.cache_integration.cache_mgr.clear_baseline(media_id)
        except Exception as e:
            logger.error(f"Failed to invalidate cache: {e}")
            return False
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get cache information for this media.
        
        Returns:
            Dictionary with cache information
        """
        return self.cache_integration.get_cache_stats()
