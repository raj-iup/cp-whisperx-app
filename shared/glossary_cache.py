#!/usr/bin/env python3
"""
Glossary Cache Manager

Handles persistent caching of TMDB glossaries and learned terms with TTL
management, validation, and automatic cleanup.

Compliance: DEVELOPMENT_STANDARDS.md
"""

import json
import shutil
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import logging


class GlossaryCache:
    """
    Persistent cache for glossary data
    
    Features:
    - TMDB glossary caching (by film title + year)
    - Learned term persistence (frequency data)
    - TTL management (configurable, default 30 days)
    - Automatic cleanup of expired entries
    - Cache statistics and hit/miss tracking
    - Thread-safe operations
    
    Cache Structure:
        glossary/cache/
        ├── tmdb/
        │   ├── {title_slug}_{year}/
        │   │   ├── glossary.json      # Cached glossary data
        │   │   ├── metadata.json      # Cache metadata (timestamp, TTL)
        │   │   └── enrichment.json    # Optional: full TMDB enrichment
        │   └── index.json             # Film → cache path mapping
        └── learned/
            └── {title_slug}_{year}/
                ├── term_frequency.json    # Term usage frequencies
                └── metadata.json          # Learning metadata
    
    Usage:
        cache = GlossaryCache(project_root)
        
        # TMDB glossary caching
        glossary = cache.get_tmdb_glossary("3 Idiots", 2009)
        if not glossary:
            glossary = fetch_and_generate_glossary()
            cache.save_tmdb_glossary("3 Idiots", 2009, glossary)
        
        # Learned terms
        learned = cache.get_learned_terms("3 Idiots", 2009)
        cache.update_learned_terms("3 Idiots", 2009, new_data)
    """
    
    def __init__(
        self,
        project_root: Path,
        cache_dir: Optional[Path] = None,
        ttl_days: int = 30,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize glossary cache manager
        
        Args:
            project_root: Project root directory
            cache_dir: Cache directory (default: glossary/cache)
            ttl_days: Cache TTL in days (default: 30)
            logger: Optional logger instance
        """
        self.project_root = Path(project_root)
        self.cache_dir = cache_dir or (self.project_root / "glossary" / "cache")
        self.ttl_days = ttl_days
        self.logger = logger or logging.getLogger(__name__)
        
        # Cache subdirectories
        self.tmdb_cache_dir = self.cache_dir / "tmdb"
        self.learned_cache_dir = self.cache_dir / "learned"
        
        # Ensure cache directories exist
        self.tmdb_cache_dir.mkdir(parents=True, exist_ok=True)
        self.learned_cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Statistics
        self.stats = {
            'tmdb_hits': 0,
            'tmdb_misses': 0,
            'learned_hits': 0,
            'learned_misses': 0
        }
    
    def get_tmdb_glossary(
        self,
        title: str,
        year: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached TMDB glossary
        
        Args:
            title: Film title
            year: Film year
            
        Returns:
            Cached glossary dict or None if not found/expired
        """
        film_slug = self._get_film_slug(title, year)
        cache_path = self.tmdb_cache_dir / film_slug / "glossary.json"
        metadata_path = self.tmdb_cache_dir / film_slug / "metadata.json"
        
        if not cache_path.exists():
            self.stats['tmdb_misses'] += 1
            return None
        
        # Check TTL
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                cached_date = datetime.fromisoformat(metadata['cached_at'])
                expiry_date = cached_date + timedelta(days=self.ttl_days)
                
                if datetime.now() > expiry_date:
                    self.logger.debug(f"Cache expired for {film_slug}")
                    self.stats['tmdb_misses'] += 1
                    return None
            except Exception as e:
                self.logger.warning(f"Error reading cache metadata: {e}")
                self.stats['tmdb_misses'] += 1
                return None
        
        # Load cached glossary
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                glossary = json.load(f)
            
            self.stats['tmdb_hits'] += 1
            self.logger.debug(f"Cache hit for {film_slug}")
            return glossary
            
        except Exception as e:
            self.logger.error(f"Error loading cached glossary: {e}")
            self.stats['tmdb_misses'] += 1
            return None
    
    def save_tmdb_glossary(
        self,
        title: str,
        year: int,
        glossary_data: Dict[str, Any],
        enrichment_data: Optional[Dict] = None
    ) -> bool:
        """
        Save TMDB glossary to cache
        
        Args:
            title: Film title
            year: Film year
            glossary_data: Glossary dictionary to cache
            enrichment_data: Optional full TMDB enrichment data
            
        Returns:
            True if saved successfully
        """
        film_slug = self._get_film_slug(title, year)
        cache_dir = self.tmdb_cache_dir / film_slug
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Save glossary
            glossary_path = cache_dir / "glossary.json"
            with open(glossary_path, 'w', encoding='utf-8') as f:
                json.dump(glossary_data, f, indent=2, ensure_ascii=False)
            
            # Save metadata
            metadata = {
                'title': title,
                'year': year,
                'cached_at': datetime.now().isoformat(),
                'ttl_days': self.ttl_days,
                'expires_at': (datetime.now() + timedelta(days=self.ttl_days)).isoformat()
            }
            metadata_path = cache_dir / "metadata.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            # Optionally save full enrichment
            if enrichment_data:
                enrichment_path = cache_dir / "enrichment.json"
                with open(enrichment_path, 'w', encoding='utf-8') as f:
                    json.dump(enrichment_data, f, indent=2, ensure_ascii=False)
            
            # Update index
            self._update_cache_index(film_slug, title, year)
            
            self.logger.debug(f"Saved glossary cache for {film_slug}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving glossary cache: {e}")
            return False
    
    def get_learned_terms(
        self,
        title: str,
        year: int
    ) -> Dict[str, Dict[str, float]]:
        """
        Get learned term frequencies
        
        Args:
            title: Film title
            year: Film year
            
        Returns:
            Dictionary of {term: {translation: frequency}}
        """
        film_slug = self._get_film_slug(title, year)
        learned_path = self.learned_cache_dir / film_slug / "term_frequency.json"
        
        if not learned_path.exists():
            self.stats['learned_misses'] += 1
            return {}
        
        try:
            with open(learned_path, 'r', encoding='utf-8') as f:
                learned_data = json.load(f)
            
            self.stats['learned_hits'] += 1
            return learned_data
            
        except Exception as e:
            self.logger.error(f"Error loading learned terms: {e}")
            self.stats['learned_misses'] += 1
            return {}
    
    def update_learned_terms(
        self,
        title: str,
        year: int,
        term_frequencies: Dict[str, Dict[str, float]]
    ) -> bool:
        """
        Update learned term frequencies
        
        Args:
            title: Film title
            year: Film year
            term_frequencies: Dictionary of term frequencies
            
        Returns:
            True if saved successfully
        """
        film_slug = self._get_film_slug(title, year)
        learned_dir = self.learned_cache_dir / film_slug
        learned_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Save term frequencies
            learned_path = learned_dir / "term_frequency.json"
            with open(learned_path, 'w', encoding='utf-8') as f:
                json.dump(term_frequencies, f, indent=2, ensure_ascii=False)
            
            # Save metadata
            metadata = {
                'title': title,
                'year': year,
                'updated_at': datetime.now().isoformat(),
                'term_count': len(term_frequencies)
            }
            metadata_path = learned_dir / "metadata.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            self.logger.debug(f"Updated learned terms for {film_slug}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving learned terms: {e}")
            return False
    
    def cleanup_expired(self) -> int:
        """
        Clean up expired cache entries
        
        Returns:
            Number of entries cleaned up
        """
        cleaned_count = 0
        
        # Clean TMDB cache
        for film_dir in self.tmdb_cache_dir.iterdir():
            if not film_dir.is_dir():
                continue
            
            metadata_path = film_dir / "metadata.json"
            if not metadata_path.exists():
                continue
            
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                expires_at = datetime.fromisoformat(metadata['expires_at'])
                
                if datetime.now() > expires_at:
                    # Remove expired entry
                    shutil.rmtree(film_dir)
                    cleaned_count += 1
                    self.logger.debug(f"Cleaned expired cache: {film_dir.name}")
                    
            except Exception as e:
                self.logger.warning(f"Error cleaning cache entry {film_dir.name}: {e}")
        
        return cleaned_count
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Statistics dictionary
        """
        tmdb_count = sum(1 for _ in self.tmdb_cache_dir.iterdir() if _.is_dir())
        learned_count = sum(1 for _ in self.learned_cache_dir.iterdir() if _.is_dir())
        
        cache_size_mb = sum(
            f.stat().st_size for f in self.cache_dir.rglob('*') if f.is_file()
        ) / (1024 * 1024)
        
        return {
            'tmdb_entries': tmdb_count,
            'learned_entries': learned_count,
            'cache_size_mb': round(cache_size_mb, 2),
            'tmdb_hit_rate': self._calculate_hit_rate(
                self.stats['tmdb_hits'], 
                self.stats['tmdb_misses']
            ),
            'learned_hit_rate': self._calculate_hit_rate(
                self.stats['learned_hits'],
                self.stats['learned_misses']
            ),
            'stats': self.stats.copy()
        }
    
    def _get_film_slug(self, title: str, year: int) -> str:
        """Generate film slug for cache paths"""
        import re
        slug = title.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[\s_]+', '_', slug)
        return f"{slug}_{year}"
    
    def _update_cache_index(self, film_slug: str, title: str, year: int) -> None:
        """Update cache index with new entry"""
        index_path = self.tmdb_cache_dir / "index.json"
        
        # Load existing index
        if index_path.exists():
            try:
                with open(index_path, 'r', encoding='utf-8') as f:
                    index = json.load(f)
            except:
                index = {}
        else:
            index = {}
        
        # Update index
        index[film_slug] = {
            'title': title,
            'year': year,
            'cached_at': datetime.now().isoformat()
        }
        
        # Save index
        try:
            with open(index_path, 'w', encoding='utf-8') as f:
                json.dump(index, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.warning(f"Error updating cache index: {e}")
    
    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate"""
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)
