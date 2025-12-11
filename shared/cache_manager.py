"""
Cache manager for multi-phase subtitle workflow.

Per AD-014: Manage baseline, glossary, and translation cache artifacts
to enable 70-80% faster iterations on subsequent runs.

Architecture Decision: AD-014 (Multi-Phase Subtitle Workflow)
"""
from pathlib import Path
import json
import shutil
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class BaselineArtifacts:
    """Baseline artifacts from Phase 1 (ASR, alignment, VAD)."""
    
    media_id: str
    audio_file: Path
    segments: List[Dict[str, Any]]
    aligned_segments: List[Dict[str, Any]]
    vad_segments: List[Dict[str, Any]]
    diarization: Optional[Dict[str, Any]]
    metadata: Dict[str, Any]
    created_at: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Convert Path objects to strings
        data['audio_file'] = str(data['audio_file'])
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaselineArtifacts':
        """Create from dictionary."""
        data['audio_file'] = Path(data['audio_file'])
        return cls(**data)


@dataclass
class GlossaryResults:
    """Results from Phase 2 (glossary application)."""
    
    media_id: str
    glossary_hash: str
    applied_segments: List[Dict[str, Any]]
    quality_metrics: Dict[str, float]
    created_at: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GlossaryResults':
        """Create from dictionary."""
        return cls(**data)


class MediaCacheManager:
    """
    Manage cached artifacts for multi-phase subtitle workflow.
    
    Cache Structure:
        cache/media/{media_id}/
        ├── baseline/
        │   ├── audio.wav
        │   ├── segments.json
        │   ├── aligned.json
        │   ├── vad.json
        │   └── metadata.json
        ├── glossary/{glossary_hash}/
        │   ├── applied.json
        │   └── quality_metrics.json
        └── translations/{target_lang}/
            └── translated.json
    
    Usage:
        >>> cache_mgr = MediaCacheManager()
        >>> 
        >>> # Check for baseline
        >>> if cache_mgr.has_baseline(media_id):
        >>>     baseline = cache_mgr.get_baseline(media_id)
        >>> else:
        >>>     baseline = generate_baseline()
        >>>     cache_mgr.store_baseline(media_id, baseline)
    """
    
    def __init__(self, cache_root: Optional[Path] = None):
        """
        Initialize cache manager.
        
        Args:
            cache_root: Root directory for cache (default: ~/.cp-whisperx/cache)
        """
        if cache_root is None:
            cache_root = Path.home() / '.cp-whisperx' / 'cache'
        
        self.cache_root = Path(cache_root)
        self.cache_root.mkdir(parents=True, exist_ok=True)
    
    def _get_media_cache_dir(self, media_id: str) -> Path:
        """Get cache directory for specific media."""
        return self.cache_root / 'media' / media_id
    
    # ========== Baseline Cache (Phase 1) ==========
    
    def has_baseline(self, media_id: str) -> bool:
        """
        Check if baseline exists for media.
        
        Args:
            media_id: Media identifier from compute_media_id()
            
        Returns:
            True if baseline artifacts exist
        """
        baseline_dir = self._get_media_cache_dir(media_id) / 'baseline'
        metadata_file = baseline_dir / 'metadata.json'
        return metadata_file.exists()
    
    def get_baseline(self, media_id: str) -> Optional[BaselineArtifacts]:
        """
        Load baseline artifacts from cache.
        
        Args:
            media_id: Media identifier
            
        Returns:
            BaselineArtifacts if found, None otherwise
        """
        if not self.has_baseline(media_id):
            return None
        
        baseline_dir = self._get_media_cache_dir(media_id) / 'baseline'
        
        try:
            # Load metadata
            with open(baseline_dir / 'metadata.json') as f:
                metadata = json.load(f)
            
            # Load segments
            with open(baseline_dir / 'segments.json') as f:
                segments = json.load(f)
            
            # Load aligned segments
            with open(baseline_dir / 'aligned.json') as f:
                aligned_segments = json.load(f)
            
            # Load VAD segments
            with open(baseline_dir / 'vad.json') as f:
                vad_segments = json.load(f)
            
            # Load diarization (optional)
            diarization = None
            diarization_file = baseline_dir / 'diarization.json'
            if diarization_file.exists():
                with open(diarization_file) as f:
                    diarization = json.load(f)
            
            # Construct artifacts
            return BaselineArtifacts(
                media_id=media_id,
                audio_file=baseline_dir / 'audio.wav',
                segments=segments,
                aligned_segments=aligned_segments,
                vad_segments=vad_segments,
                diarization=diarization,
                metadata=metadata,
                created_at=metadata.get('created_at', '')
            )
            
        except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
            # Cache corrupted or incomplete
            return None
    
    def store_baseline(
        self,
        media_id: str,
        baseline: BaselineArtifacts
    ) -> bool:
        """
        Store baseline artifacts in cache.
        
        Args:
            media_id: Media identifier
            baseline: Baseline artifacts to store
            
        Returns:
            True if stored successfully
        """
        baseline_dir = self._get_media_cache_dir(media_id) / 'baseline'
        baseline_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Store audio file (if not already there)
            target_audio = baseline_dir / 'audio.wav'
            if baseline.audio_file.exists() and baseline.audio_file != target_audio:
                shutil.copy2(baseline.audio_file, target_audio)
            
            # Store segments
            with open(baseline_dir / 'segments.json', 'w') as f:
                json.dump(baseline.segments, f, indent=2)
            
            # Store aligned segments
            with open(baseline_dir / 'aligned.json', 'w') as f:
                json.dump(baseline.aligned_segments, f, indent=2)
            
            # Store VAD segments
            with open(baseline_dir / 'vad.json', 'w') as f:
                json.dump(baseline.vad_segments, f, indent=2)
            
            # Store diarization (optional)
            if baseline.diarization:
                with open(baseline_dir / 'diarization.json', 'w') as f:
                    json.dump(baseline.diarization, f, indent=2)
            
            # Store metadata
            metadata = baseline.metadata.copy()
            metadata['created_at'] = baseline.created_at or datetime.now().isoformat()
            with open(baseline_dir / 'metadata.json', 'w') as f:
                json.dump(metadata, f, indent=2)
            
            return True
            
        except (IOError, OSError) as e:
            # Storage failed
            return False
    
    def clear_baseline(self, media_id: str) -> bool:
        """
        Remove baseline artifacts from cache.
        
        Args:
            media_id: Media identifier
            
        Returns:
            True if cleared successfully
        """
        baseline_dir = self._get_media_cache_dir(media_id) / 'baseline'
        
        if baseline_dir.exists():
            try:
                shutil.rmtree(baseline_dir)
                return True
            except OSError:
                return False
        
        return True
    
    # ========== Glossary Cache (Phase 2) ==========
    
    def has_glossary_results(
        self,
        media_id: str,
        glossary_hash: str
    ) -> bool:
        """
        Check if glossary results exist for this media and glossary.
        
        Args:
            media_id: Media identifier
            glossary_hash: Hash of glossary file
            
        Returns:
            True if glossary results exist
        """
        glossary_dir = self._get_media_cache_dir(media_id) / 'glossary' / glossary_hash
        applied_file = glossary_dir / 'applied.json'
        return applied_file.exists()
    
    def get_glossary_results(
        self,
        media_id: str,
        glossary_hash: str
    ) -> Optional[GlossaryResults]:
        """
        Load glossary results from cache.
        
        Args:
            media_id: Media identifier
            glossary_hash: Hash of glossary file
            
        Returns:
            GlossaryResults if found, None otherwise
        """
        if not self.has_glossary_results(media_id, glossary_hash):
            return None
        
        glossary_dir = self._get_media_cache_dir(media_id) / 'glossary' / glossary_hash
        
        try:
            # Load applied segments
            with open(glossary_dir / 'applied.json') as f:
                applied_segments = json.load(f)
            
            # Load quality metrics
            with open(glossary_dir / 'quality_metrics.json') as f:
                quality_metrics = json.load(f)
            
            # Get creation time
            created_at = quality_metrics.get('created_at', '')
            
            return GlossaryResults(
                media_id=media_id,
                glossary_hash=glossary_hash,
                applied_segments=applied_segments,
                quality_metrics=quality_metrics,
                created_at=created_at
            )
            
        except (json.JSONDecodeError, FileNotFoundError, KeyError):
            return None
    
    def store_glossary_results(
        self,
        media_id: str,
        glossary_hash: str,
        results: GlossaryResults
    ) -> bool:
        """
        Store glossary results in cache.
        
        Args:
            media_id: Media identifier
            glossary_hash: Hash of glossary file
            results: Glossary results to store
            
        Returns:
            True if stored successfully
        """
        glossary_dir = self._get_media_cache_dir(media_id) / 'glossary' / glossary_hash
        glossary_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Store applied segments
            with open(glossary_dir / 'applied.json', 'w') as f:
                json.dump(results.applied_segments, f, indent=2)
            
            # Store quality metrics
            metrics = results.quality_metrics.copy()
            metrics['created_at'] = results.created_at or datetime.now().isoformat()
            with open(glossary_dir / 'quality_metrics.json', 'w') as f:
                json.dump(metrics, f, indent=2)
            
            return True
            
        except (IOError, OSError):
            return False
    
    # ========== Cache Management ==========
    
    def get_cache_size(self, media_id: Optional[str] = None) -> int:
        """
        Get total cache size in bytes.
        
        Args:
            media_id: Specific media ID, or None for all cache
            
        Returns:
            Total size in bytes
        """
        if media_id:
            cache_dir = self._get_media_cache_dir(media_id)
        else:
            cache_dir = self.cache_root
        
        if not cache_dir.exists():
            return 0
        
        total_size = 0
        for file_path in cache_dir.rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        
        return total_size
    
    def clear_all_cache(self) -> bool:
        """
        Clear entire cache (use with caution).
        
        Returns:
            True if cleared successfully
        """
        if self.cache_root.exists():
            try:
                shutil.rmtree(self.cache_root)
                self.cache_root.mkdir(parents=True, exist_ok=True)
                return True
            except OSError:
                return False
        
        return True
    
    def list_cached_media(self) -> List[str]:
        """
        List all media IDs in cache.
        
        Returns:
            List of media IDs
        """
        media_dir = self.cache_root / 'media'
        
        if not media_dir.exists():
            return []
        
        return [d.name for d in media_dir.iterdir() if d.is_dir()]
