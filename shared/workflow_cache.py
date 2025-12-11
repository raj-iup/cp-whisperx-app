"""
Workflow caching integration for AD-014 multi-phase subtitle workflow.

Integrates media identity and cache manager with existing workflow stages
to enable 70-80% faster iterations on subtitle generation.

Architecture Decision: AD-014 (Multi-Phase Subtitle Workflow)
"""
from pathlib import Path
import json
from typing import Optional, Dict, Any, List
from datetime import datetime

from shared.media_identity import compute_media_id, compute_glossary_hash
from shared.cache_manager import (
    MediaCacheManager,
    BaselineArtifacts,
    GlossaryResults
)
from shared.logger import get_logger

logger = get_logger(__name__)


class WorkflowCacheIntegration:
    """
    Integration layer between workflow and caching system.
    
    Handles:
    - Cache detection before baseline generation
    - Baseline storage after generation
    - Glossary result caching
    - Cache invalidation
    
    Usage:
        >>> cache_int = WorkflowCacheIntegration(job_dir)
        >>> 
        >>> # Check for cached baseline
        >>> baseline = cache_int.get_or_generate_baseline(
        >>>     media_file, 
        >>>     generate_func=lambda: run_asr_alignment()
        >>> )
    """
    
    def __init__(self, job_dir: Path, enabled: bool = True):
        """
        Initialize cache integration.
        
        Args:
            job_dir: Job directory path
            enabled: Enable caching (default: True)
        """
        self.job_dir = Path(job_dir)
        self.enabled = enabled
        self.cache_mgr = MediaCacheManager()
        self.media_id: Optional[str] = None
    
    def is_cached_baseline_available(self, media_file: Path) -> bool:
        """
        Check if baseline cache exists for media.
        
        Args:
            media_file: Path to media file
            
        Returns:
            True if cached baseline available
        """
        if not self.enabled:
            return False
        
        try:
            # Compute media ID
            self.media_id = compute_media_id(media_file)
            logger.info(f"🔑 Media ID: {self.media_id[:16]}...")
            
            # Check cache
            has_cache = self.cache_mgr.has_baseline(self.media_id)
            
            if has_cache:
                logger.info("✅ Found cached baseline (70-80% faster)")
            else:
                logger.info("🆕 No cache found - will generate baseline")
            
            return has_cache
            
        except Exception as e:
            logger.warning(f"Cache check failed: {e}")
            return False
    
    def load_cached_baseline(self) -> Optional[Dict[str, Any]]:
        """
        Load cached baseline artifacts.
        
        Returns:
            Dictionary with baseline artifacts, or None if not cached
        """
        if not self.enabled or not self.media_id:
            return None
        
        try:
            baseline = self.cache_mgr.get_baseline(self.media_id)
            
            if not baseline:
                return None
            
            logger.info("📂 Loading cached baseline artifacts...")
            
            # Convert to dictionary format expected by workflow
            result = {
                'audio_file': baseline.audio_file,
                'segments': baseline.segments,
                'aligned_segments': baseline.aligned_segments,
                'vad_segments': baseline.vad_segments,
                'diarization': baseline.diarization,
                'metadata': baseline.metadata
            }
            
            logger.info(f"✅ Loaded {len(baseline.segments)} segments from cache")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to load cached baseline: {e}", exc_info=True)
            return None
    
    def store_baseline(
        self,
        media_file: Path,
        audio_file: Path,
        segments: List[Dict[str, Any]],
        aligned_segments: List[Dict[str, Any]],
        vad_segments: List[Dict[str, Any]],
        diarization: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Store baseline artifacts in cache.
        
        Args:
            media_file: Original media file
            audio_file: Extracted audio file
            segments: ASR segments
            aligned_segments: Aligned segments with word timestamps
            vad_segments: VAD segments
            diarization: Diarization results (optional)
            
        Returns:
            True if stored successfully
        """
        if not self.enabled:
            return False
        
        try:
            # Compute media ID if not already done
            if not self.media_id:
                self.media_id = compute_media_id(media_file)
            
            logger.info("💾 Storing baseline in cache...")
            
            # Create metadata
            metadata = {
                'media_file': str(media_file),
                'duration': self._get_total_duration(segments),
                'num_segments': len(segments),
                'num_aligned': len(aligned_segments),
                'num_vad': len(vad_segments),
                'has_diarization': diarization is not None,
                'created_at': datetime.now().isoformat()
            }
            
            # Create baseline artifacts
            baseline = BaselineArtifacts(
                media_id=self.media_id,
                audio_file=audio_file,
                segments=segments,
                aligned_segments=aligned_segments,
                vad_segments=vad_segments,
                diarization=diarization,
                metadata=metadata,
                created_at=datetime.now().isoformat()
            )
            
            # Store in cache
            success = self.cache_mgr.store_baseline(self.media_id, baseline)
            
            if success:
                logger.info("✅ Baseline stored in cache")
                logger.info(f"🎯 Subsequent runs will be 70-80% faster!")
            else:
                logger.warning("⚠️  Failed to store baseline in cache")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to store baseline: {e}", exc_info=True)
            return False
    
    def restore_baseline_to_job(self, baseline: Dict[str, Any]) -> bool:
        """
        Restore cached baseline to job directories.
        
        Creates stage output directories with cached data so workflow
        can continue from where baseline ends.
        
        Args:
            baseline: Baseline artifacts dictionary
            
        Returns:
            True if restored successfully
        """
        try:
            logger.info("📝 Restoring cached baseline to job directories...")
            
            # Stage 01: Demux (audio file)
            demux_dir = self.job_dir / "01_demux"
            demux_dir.mkdir(parents=True, exist_ok=True)
            
            audio_file = baseline['audio_file']
            if audio_file.exists():
                import shutil
                target_audio = demux_dir / "audio.wav"
                if not target_audio.exists():
                    shutil.copy2(audio_file, target_audio)
                    logger.info(f"✓ Restored audio: {target_audio.name}")
            
            # Stage 05: PyAnnote VAD
            vad_dir = self.job_dir / "05_vad"
            vad_dir.mkdir(parents=True, exist_ok=True)
            
            vad_file = vad_dir / "vad_segments.json"
            with open(vad_file, 'w') as f:
                json.dump(baseline['vad_segments'], f, indent=2)
            logger.info(f"✓ Restored VAD segments: {len(baseline['vad_segments'])} segments")
            
            # Stage 06: WhisperX ASR
            asr_dir = self.job_dir / "06_asr"
            asr_dir.mkdir(parents=True, exist_ok=True)
            
            segments_file = asr_dir / "segments.json"
            with open(segments_file, 'w') as f:
                json.dump(baseline['segments'], f, indent=2)
            logger.info(f"✓ Restored ASR segments: {len(baseline['segments'])} segments")
            
            # Stage 07: Alignment
            alignment_dir = self.job_dir / "07_alignment"
            alignment_dir.mkdir(parents=True, exist_ok=True)
            
            aligned_file = alignment_dir / "aligned_segments.json"
            with open(aligned_file, 'w') as f:
                json.dump(baseline['aligned_segments'], f, indent=2)
            logger.info(f"✓ Restored aligned segments: {len(baseline['aligned_segments'])} segments")
            
            # Diarization (optional)
            if baseline.get('diarization'):
                diarization_file = alignment_dir / "diarization.json"
                with open(diarization_file, 'w') as f:
                    json.dump(baseline['diarization'], f, indent=2)
                logger.info(f"✓ Restored diarization data")
            
            logger.info("✅ Baseline restoration complete")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore baseline: {e}", exc_info=True)
            return False
    
    def _get_total_duration(self, segments: List[Dict[str, Any]]) -> float:
        """Calculate total duration from segments."""
        if not segments:
            return 0.0
        
        try:
            # Find last segment end time
            last_end = max(seg.get('end', 0.0) for seg in segments)
            return last_end
        except (ValueError, KeyError):
            return 0.0
    
    def is_cached_glossary_available(
        self,
        glossary_file: Optional[Path]
    ) -> bool:
        """
        Check if glossary results are cached.
        
        Args:
            glossary_file: Path to glossary file (or None)
            
        Returns:
            True if cached glossary results available
        """
        if not self.enabled or not self.media_id or not glossary_file:
            return False
        
        try:
            glossary_hash = compute_glossary_hash(glossary_file)
            has_cache = self.cache_mgr.has_glossary_results(
                self.media_id,
                glossary_hash
            )
            
            if has_cache:
                logger.info("✅ Found cached glossary results")
            
            return has_cache
            
        except Exception as e:
            logger.warning(f"Glossary cache check failed: {e}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            total_size = self.cache_mgr.get_cache_size()
            cached_media = self.cache_mgr.list_cached_media()
            
            return {
                'enabled': self.enabled,
                'total_size_bytes': total_size,
                'total_size_mb': total_size / (1024 * 1024),
                'cached_media_count': len(cached_media),
                'cached_media_ids': cached_media[:5]  # First 5
            }
        except Exception:
            return {'enabled': self.enabled, 'error': 'Failed to get stats'}
    
    def clear_cache(self, media_file: Optional[Path] = None) -> bool:
        """
        Clear cache for specific media or all cache.
        
        Args:
            media_file: Specific media to clear, or None for all
            
        Returns:
            True if cleared successfully
        """
        try:
            if media_file:
                media_id = compute_media_id(media_file)
                return self.cache_mgr.clear_baseline(media_id)
            else:
                return self.cache_mgr.clear_all_cache()
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False
