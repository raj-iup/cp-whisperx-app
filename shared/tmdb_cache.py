#!/usr/bin/env python3
"""
TMDB Caching Layer

Caches TMDB enrichment data to avoid repeated API calls.
Cache expires after 30 days.
"""

# Standard library
import json
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime, timedelta


class TMDBCache:
    """Cache TMDB enrichment data with expiry"""
    
    def __init__(self, cache_dir: Optional[Path] = None, expiry_days: int = 90):
        """
        Initialize TMDB cache
        
        Args:
            cache_dir: Directory to store cache files (default: out/tmdb_cache)
            expiry_days: Number of days before cache expires (default: 90)
        """
        if cache_dir is None:
            cache_dir = Path("out/tmdb_cache")
        
        self.cache_dir = Path(cache_dir)
        self.expiry_days = expiry_days
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get(self, tmdb_id: int) -> Optional[Dict]:
        """
        Get cached TMDB data if available and not expired
        
        Args:
            tmdb_id: TMDB movie ID
        
        Returns:
            Cached data dict or None if not found/expired
        """
        cache_file = self.cache_dir / f"tmdb_{tmdb_id}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            # Check age
            mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
            age = datetime.now() - mtime
            
            if age.days > self.expiry_days:
                # Cache expired
                return None
            
            # Load cached data
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Add cache metadata
            data['_cache'] = {
                'age_days': age.days,
                'cached_at': mtime.isoformat(),
                'expires_at': (mtime + timedelta(days=self.expiry_days)).isoformat()
            }
            
            return data
            
        except Exception as e:
            # If error, treat as cache miss
            return None
    
    def set(self, tmdb_id: int, data: Dict) -> None:
        """
        Cache TMDB data
        
        Args:
            tmdb_id: TMDB movie ID
            data: TMDB enrichment data to cache
        """
        cache_file = self.cache_dir / f"tmdb_{tmdb_id}.json"
        
        try:
            # Remove cache metadata before saving
            data_to_save = {k: v for k, v in data.items() if k != '_cache'}
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=2, ensure_ascii=False)
        
        except Exception as e:
            # Non-critical - log but don't fail
            pass
    
    def get_age_days(self, tmdb_id: int) -> Optional[int]:
        """
        Get age of cached data in days
        
        Args:
            tmdb_id: TMDB movie ID
        
        Returns:
            Age in days or None if not cached
        """
        cache_file = self.cache_dir / f"tmdb_{tmdb_id}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
            age = datetime.now() - mtime
            return age.days
        except:
            return None
    
    def clear(self, tmdb_id: Optional[int] = None) -> None:
        """
        Clear cache
        
        Args:
            tmdb_id: If specified, clear only this entry. If None, clear all.
        """
        if tmdb_id is not None:
            # Clear specific entry
            cache_file = self.cache_dir / f"tmdb_{tmdb_id}.json"
            if cache_file.exists():
                cache_file.unlink()
        else:
            # Clear all entries
            for cache_file in self.cache_dir.glob("tmdb_*.json"):
                cache_file.unlink()
    
    def clear_expired(self) -> None:
        """Clear all expired cache entries"""
        for cache_file in self.cache_dir.glob("tmdb_*.json"):
            try:
                mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
                age = datetime.now() - mtime
                
                if age.days > self.expiry_days:
                    cache_file.unlink()
            except:
                continue
    
    def get_stats(self) -> Dict:
        """
        Get cache statistics
        
        Returns:
            Dict with cache stats (total_entries, oldest_days, newest_days)
        """
        cache_files = list(self.cache_dir.glob("tmdb_*.json"))
        
        if not cache_files:
            return {
                'total_entries': 0,
                'oldest_days': None,
                'newest_days': None
            }
        
        ages = []
        for cache_file in cache_files:
            try:
                mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
                age = (datetime.now() - mtime).days
                ages.append(age)
            except:
                continue
        
        return {
            'total_entries': len(cache_files),
            'oldest_days': max(ages) if ages else None,
            'newest_days': min(ages) if ages else None
        }
