#!/usr/bin/env python3
"""
MusicBrainz Client for Soundtrack Enrichment

Fetches soundtrack data from MusicBrainz open music database.
Rate limited to 1 request per second per MusicBrainz guidelines.
Includes caching layer to minimize API calls.
"""

import musicbrainzngs
from typing import Optional, List, Dict
import time
from pathlib import Path
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.logger import PipelineLogger
from shared.musicbrainz_cache import MusicBrainzCache

# Configure MusicBrainz client
musicbrainzngs.set_useragent(
    "CP-WhisperX-App",
    "1.0",
    "https://github.com/your-repo/cp-whisperx-app"
)


class MusicBrainzClient:
    """Client for fetching soundtrack data from MusicBrainz with caching"""
    
    def __init__(self, logger: Optional[PipelineLogger] = None, enable_cache: bool = True):
        """
        Initialize MusicBrainz client
        
        Args:
            logger: Optional logger instance
            enable_cache: Enable caching (default: True)
        """
        self.logger = logger
        self.rate_limit_delay = 1.0  # 1 second between requests (MusicBrainz requirement)
        self.last_request_time = 0
        
        # Initialize cache
        self.enable_cache = enable_cache
        self.cache = MusicBrainzCache() if enable_cache else None
    
    def _rate_limit(self):
        """Enforce rate limiting per MusicBrainz guidelines"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - elapsed
            if self.logger:
                self.logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def get_soundtrack(self, imdb_id: str, title: str = None, year: int = None) -> Optional[Dict]:
        """
        Get soundtrack for movie
        
        Note: MusicBrainz doesn't support browsing by IMDb ID directly.
        Falls back to title/year search if IMDb search fails.
        
        Args:
            imdb_id: IMDb identifier (e.g., 'tt0473367') - currently not used
            title: Movie title (recommended)
            year: Release year (recommended)
        
        Returns:
            Dict with soundtrack data or None if not found
            Format: {
                'found': bool,
                'source': 'musicbrainz',
                'release_id': str,
                'release_title': str,
                'tracks': [{'title': str, 'artist': str, 'composer': str, 'duration_ms': int}]
            }
        """
        # MusicBrainz doesn't support IMDb browsing, use title search
        if not title:
            if self.logger:
                self.logger.warning("MusicBrainz requires movie title for search")
            return None
        
        return self.search_by_title(title, year)
    
    def _parse_tracks(self, release: Dict) -> List[Dict[str, str]]:
        """
        Parse tracks from MusicBrainz release data
        
        Args:
            release: Release data from MusicBrainz
        
        Returns:
            List of track dictionaries
        """
        tracks = []
        
        for medium in release.get('medium-list', []):
            for track in medium.get('track-list', []):
                recording = track.get('recording', {})
                
                # Get track title
                title = recording.get('title', '').strip()
                if not title:
                    continue
                
                # Get artists
                artists = []
                for credit in recording.get('artist-credit', []):
                    if isinstance(credit, dict):
                        artist_name = credit.get('artist', {}).get('name')
                        if artist_name:
                            artists.append(artist_name)
                
                artist_str = ', '.join(artists) if artists else ''
                
                # Get composer from work relationships
                composer = ''
                work_relations = recording.get('work-relation-list', [])
                for relation in work_relations:
                    if relation.get('type') == 'composer':
                        composer = relation.get('artist', {}).get('name', '')
                        break
                
                # Get duration (in milliseconds)
                duration_ms = recording.get('length', 0)
                if isinstance(duration_ms, str):
                    try:
                        duration_ms = int(duration_ms)
                    except ValueError:
                        duration_ms = 0
                
                tracks.append({
                    'title': title,
                    'artist': artist_str,
                    'composer': composer,
                    'duration_ms': duration_ms
                })
        
        return tracks
    
    def search_by_title(
        self,
        movie_title: str,
        year: Optional[int] = None
    ) -> Optional[Dict]:
        """
        Search for soundtrack by movie title with caching
        
        Args:
            movie_title: Movie title
            year: Optional release year
        
        Returns:
            Dict with soundtrack data or None
        """
        # Check search cache first
        if self.enable_cache and self.cache:
            release_id = self.cache.get_release_id_from_search(movie_title, year)
            
            if release_id:
                if self.logger:
                    self.logger.info(f"Found release ID in search cache: {release_id}")
                
                # Try to get release from cache
                cached_release = self.cache.get_release(release_id)
                if cached_release:
                    if self.logger:
                        age_days = cached_release.get('_cache', {}).get('age_days', 'unknown')
                        self.logger.info(f"Using cached MusicBrainz data (age: {age_days} days)")
                    return cached_release
        
        # Cache miss - perform API search
        if self.logger:
            self.logger.info(f"Searching MusicBrainz for: {movie_title}" + (f" ({year})" if year else ""))
        
        # Rate limit
        self._rate_limit()
        
        # Search for release
        query_parts = [f'release:"{movie_title}"']
        if year:
            query_parts.append(f'date:{year}')
        
        query = ' AND '.join(query_parts)
        
        try:
            result = musicbrainzngs.search_releases(
                query=query,
                limit=5,
                strict=False
            )
            
            releases = result.get('release-list', [])
            
            if not releases:
                if self.logger:
                    self.logger.info(f"No MusicBrainz release found for: {movie_title}")
                return None
            
            # Use first result
            release_summary = releases[0]
            release_id = release_summary['id']
            
            if self.logger:
                self.logger.info(f"Found release: {release_summary.get('title', 'Unknown')} (ID: {release_id})")
            
            # Cache the search result (title+year -> release_id)
            if self.enable_cache and self.cache:
                self.cache.cache_search_result(movie_title, year, release_id)
            
            # Get full release details
            self._rate_limit()
            
            full_release = musicbrainzngs.get_release_by_id(
                release_id,
                includes=['recordings', 'artist-credits', 'work-rels']
            )
            
            release_data = full_release.get('release', {})
            
            # Parse tracks
            tracks = self._parse_tracks(release_data)
            
            result_dict = {
                'found': True,
                'source': 'musicbrainz',
                'release_id': release_id,
                'release_title': release_data.get('title', ''),
                'tracks': tracks
            }
            
            # Cache the full release data
            if self.enable_cache and self.cache:
                self.cache.set_release(release_id, result_dict)
                if self.logger:
                    self.logger.info(f"Cached MusicBrainz release: {release_id}")
            
            return result_dict
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"MusicBrainz search error: {e}")
            return None


if __name__ == '__main__':
    """Quick test of MusicBrainz client"""
    import logging
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("test")
    
    client = MusicBrainzClient(logger=logger, enable_cache=True)
    
    # Test search
    result = client.search_by_title("Jaane Tu Ya Jaane Na", 2008)
    
    if result:
        print(f"\nFound: {result['release_title']}")
        print(f"Tracks: {len(result['tracks'])}")
        for track in result['tracks'][:3]:
            print(f"  - {track['title']} by {track['artist']}")
    else:
        print("No result found")
