#!/usr/bin/env python3
"""
MusicBrainz Caching Layer

Caches MusicBrainz soundtrack data to avoid repeated API calls.
Cache expires after 90 days (music metadata is very static).
"""

# Standard library
import json
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime, timedelta


class MusicBrainzCache:
    """Cache MusicBrainz soundtrack data with expiry"""
    
    def __init__(self, cache_dir: Optional[Path] = None, expiry_days: int = 90):
        """
        Initialize MusicBrainz cache
        
        Args:
            cache_dir: Directory to store cache files (default: out/musicbrainz_cache)
            expiry_days: Number of days before cache expires (default: 90)
        """
        if cache_dir is None:
            cache_dir = Path("out/musicbrainz_cache")
        
        self.cache_dir = Path(cache_dir)
        self.expiry_days = expiry_days
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Subdirectories
        self.releases_dir = self.cache_dir / "releases"
        self.releases_dir.mkdir(exist_ok=True)
        
        # Search cache file (title+year -> release_id mapping)
        self.search_cache_file = self.cache_dir / "search_cache.json"
        self.search_cache = self._load_search_cache()
    
    def _load_search_cache(self) -> Dict:
        """Load search cache from file"""
        if not self.search_cache_file.exists():
            return {}
        
        try:
            with open(self.search_cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    
    def _save_search_cache(self) -> None:
        """Save search cache to file"""
        try:
            with open(self.search_cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.search_cache, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
    
    def _get_search_key(self, title: str, year: Optional[int] = None) -> str:
        """Generate search cache key from title and year"""
        key = title.lower().strip()
        if year:
            key = f"{key}_{year}"
        return key
    
    def get_release_id_from_search(self, title: str, year: Optional[int] = None) -> Optional[str]:
        """
        Get cached release ID from search cache
        
        Args:
            title: Movie title
            year: Release year
        
        Returns:
            Release ID if found in search cache, None otherwise
        """
        key = self._get_search_key(title, year)
        entry = self.search_cache.get(key)
        
        if not entry:
            return None
        
        # Check expiry
        cached_at = datetime.fromisoformat(entry['cached_at'])
        age = datetime.now() - cached_at
        
        if age.days > self.expiry_days:
            # Expired
            del self.search_cache[key]
            self._save_search_cache()
            return None
        
        return entry.get('release_id')
    
    def cache_search_result(self, title: str, year: Optional[int], release_id: str) -> None:
        """
        Cache a search result (title+year -> release_id mapping)
        
        Args:
            title: Movie title
            year: Release year
            release_id: MusicBrainz release ID
        """
        key = self._get_search_key(title, year)
        self.search_cache[key] = {
            'release_id': release_id,
            'title': title,
            'year': year,
            'cached_at': datetime.now().isoformat()
        }
        self._save_search_cache()
    
    def get_release(self, release_id: str) -> Optional[Dict]:
        """
        Get cached release data if available and not expired
        
        Args:
            release_id: MusicBrainz release ID
        
        Returns:
            Cached data dict or None if not found/expired
        """
        cache_file = self.releases_dir / f"mb_{release_id}.json"
        
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
            
        except Exception:
            # If error, treat as cache miss
            return None
    
    def set_release(self, release_id: str, data: Dict) -> None:
        """
        Cache release data
        
        Args:
            release_id: MusicBrainz release ID
            data: Release data to cache
        """
        cache_file = self.releases_dir / f"mb_{release_id}.json"
        
        try:
            # Remove cache metadata before saving
            data_to_save = {k: v for k, v in data.items() if k != '_cache'}
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=2, ensure_ascii=False)
        
        except Exception:
            # Non-critical - log but don't fail
            pass
    
    def get_age_days(self, release_id: str) -> Optional[int]:
        """
        Get age of cached release in days
        
        Args:
            release_id: MusicBrainz release ID
        
        Returns:
            Age in days or None if not cached
        """
        cache_file = self.releases_dir / f"mb_{release_id}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
            age = datetime.now() - mtime
            return age.days
        except:
            return None
    
    def clear(self, release_id: Optional[str] = None) -> None:
        """
        Clear cache
        
        Args:
            release_id: If specified, clear only this entry. If None, clear all.
        """
        if release_id is not None:
            # Clear specific entry
            cache_file = self.releases_dir / f"mb_{release_id}.json"
            if cache_file.exists():
                cache_file.unlink()
        else:
            # Clear all entries
            for cache_file in self.releases_dir.glob("mb_*.json"):
                cache_file.unlink()
            
            # Clear search cache
            self.search_cache = {}
            self._save_search_cache()
    
    def clear_expired(self) -> None:
        """Clear all expired cache entries"""
        # Clear expired releases
        for cache_file in self.releases_dir.glob("mb_*.json"):
            try:
                mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
                age = datetime.now() - mtime
                
                if age.days > self.expiry_days:
                    cache_file.unlink()
            except:
                continue
        
        # Clear expired search results
        expired_keys = []
        for key, entry in self.search_cache.items():
            try:
                cached_at = datetime.fromisoformat(entry['cached_at'])
                age = datetime.now() - cached_at
                if age.days > self.expiry_days:
                    expired_keys.append(key)
            except:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.search_cache[key]
        
        if expired_keys:
            self._save_search_cache()
    
    def get_stats(self) -> Dict:
        """
        Get cache statistics
        
        Returns:
            Dict with cache stats
        """
        release_files = list(self.releases_dir.glob("mb_*.json"))
        
        if not release_files:
            return {
                'total_releases': 0,
                'total_searches': len(self.search_cache),
                'oldest_days': None,
                'newest_days': None
            }
        
        ages = []
        for cache_file in release_files:
            try:
                mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
                age = (datetime.now() - mtime).days
                ages.append(age)
            except:
                continue
        
        return {
            'total_releases': len(release_files),
            'total_searches': len(self.search_cache),
            'oldest_days': max(ages) if ages else None,
            'newest_days': min(ages) if ages else None
        }
