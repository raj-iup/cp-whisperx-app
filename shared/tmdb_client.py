#!/usr/bin/env python3
"""
TMDB API Client - Phase 1 Implementation

Provides clean interface to TMDB API for fetching movie metadata,
cast, crew, and soundtrack information.

Usage:
    client = TMDBClient(api_key)
    movie = client.search_movie("Jaane Tu Ya Jaane Na", year=2008)
    metadata = client.get_movie_metadata(movie['id'])
"""

# Standard library
import json
import logging
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime

# Third-party
from tmdbv3api import TMDb, Movie, Person
from cachetools import TTLCache

# Local
from shared.logger import get_logger
logger = get_logger(__name__)


class TMDBClient:
    """TMDB API client wrapper"""
    
    def __init__(
        self,
        api_key: str,
        cache_ttl: int = 86400,  # 24 hours
        language: str = "en-US",
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize TMDB client
        
        Args:
            api_key: TMDB API key
            cache_ttl: Cache TTL in seconds
            language: API language
            logger: Optional logger instance
        """
        self.api_key = api_key
        self.language = language
        self.logger = logger
        
        # Initialize TMDB API
        self.tmdb = TMDb()
        self.tmdb.api_key = api_key
        self.tmdb.language = language
        
        # Initialize API objects
        self.movie_api = Movie()
        self.person_api = Person()
        
        # Cache for API results
        self._cache = TTLCache(maxsize=100, ttl=cache_ttl)
        
        if self.logger:
            self.logger.info(f"TMDB client initialized (language={language})")
    
    def search_movie(
        self,
        title: str,
        year: Optional[int] = None,
        exact_match: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Search for movie by title and optional year
        
        Args:
            title: Movie title
            year: Optional release year
            exact_match: Require exact title match
        
        Returns:
            Movie dict or None if not found
        """
        cache_key = f"search_{title}_{year}"
        if cache_key in self._cache:
            if self.logger:
                self.logger.debug(f"Using cached search result for: {title}")
            return self._cache[cache_key]
        
        try:
            if self.logger:
                self.logger.info(f"Searching TMDB for: {title} ({year or 'any year'})")
            
            # Search movies
            search_results = self.movie_api.search(title)
            
            if not search_results:
                if self.logger:
                    self.logger.warning(f"No results found for: {title}")
                return None
            
            # Filter by year if provided
            candidates = []
            for result in search_results:
                if year:
                    release_year = None
                    if hasattr(result, 'release_date') and result.release_date:
                        release_year = int(result.release_date.split('-')[0])
                    
                    # Allow ±1 year tolerance
                    if release_year and abs(release_year - year) <= 1:
                        candidates.append(result)
                else:
                    candidates.append(result)
            
            if not candidates:
                candidates = search_results[:3]  # Take top 3 if no year match
            
            # Apply exact match if requested
            if exact_match:
                for candidate in candidates:
                    if candidate.title.lower() == title.lower():
                        movie = self._movie_to_dict(candidate)
                        self._cache[cache_key] = movie
                        return movie
                return None
            
            # Return best match
            best_match = candidates[0]
            movie = self._movie_to_dict(best_match)
            
            if self.logger:
                self.logger.info(f"Found: {movie['title']} ({movie['year']}) [ID: {movie['id']}]")
            
            self._cache[cache_key] = movie
            return movie
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"TMDB search failed: {e}", exc_info=True)
            return None
    
    def get_movie_metadata(self, movie_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed movie metadata including cast and crew
        
        Args:
            movie_id: TMDB movie ID
        
        Returns:
            Metadata dict with cast, crew, genres, etc.
        """
        cache_key = f"metadata_{movie_id}"
        if cache_key in self._cache:
            if self.logger:
                self.logger.debug(f"Using cached metadata for movie ID: {movie_id}")
            return self._cache[cache_key]
        
        try:
            if self.logger:
                self.logger.info(f"Fetching metadata for movie ID: {movie_id}")
            
            # Get movie details
            movie = self.movie_api.details(movie_id)
            
            # Get credits (cast and crew)
            credits = self.movie_api.credits(movie_id)
            
            # Handle credits as dict or object
            cast_list = getattr(credits, 'cast', []) if hasattr(credits, 'cast') else credits.get('cast', [])
            crew_list = getattr(credits, 'crew', []) if hasattr(credits, 'crew') else credits.get('crew', [])
            
            # Parse cast (top 20)
            cast = []
            # Convert to list if needed
            cast_items = list(cast_list) if not isinstance(cast_list, list) else cast_list
            for i, person in enumerate(cast_items):
                if i >= 20:
                    break
                if isinstance(person, dict):
                    cast.append({
                        'name': person.get('name', ''),
                        'character': person.get('character', ''),
                        'order': person.get('order', 999)
                    })
                else:
                    cast.append({
                        'name': getattr(person, 'name', ''),
                        'character': getattr(person, 'character', ''),
                        'order': getattr(person, 'order', 999)
                    })
            
            # Parse crew (directors, writers, producers, composers)
            crew = []
            relevant_jobs = [
                'Director', 'Writer', 'Screenplay', 'Producer',
                'Music', 'Original Music Composer', 'Cinematography'
            ]
            crew_items = list(crew_list) if not isinstance(crew_list, list) else crew_list
            for person in crew_items:
                person_job = person.get('job') if isinstance(person, dict) else getattr(person, 'job', '')
                if person_job in relevant_jobs:
                    if isinstance(person, dict):
                        crew.append({
                            'name': person.get('name', ''),
                            'job': person.get('job', ''),
                            'department': person.get('department', '')
                        })
                    else:
                        crew.append({
                            'name': getattr(person, 'name', ''),
                            'job': getattr(person, 'job', ''),
                            'department': getattr(person, 'department', '')
                        })
            
            # Build metadata
            metadata = {
                'id': movie.id,
                'imdb_id': getattr(movie, 'imdb_id', None),
                'title': movie.title,
                'original_title': getattr(movie, 'original_title', movie.title),
                'year': int(movie.release_date.split('-')[0]) if movie.release_date else None,
                'overview': getattr(movie, 'overview', ''),
                'genres': [g['name'] for g in movie.genres] if hasattr(movie, 'genres') else [],
                'runtime': getattr(movie, 'runtime', None),
                'cast': cast,
                'crew': crew,
                'vote_average': getattr(movie, 'vote_average', 0),
                'vote_count': getattr(movie, 'vote_count', 0),
                'popularity': getattr(movie, 'popularity', 0)
            }
            
            if self.logger:
                self.logger.info(f"  Title: {metadata['title']} ({metadata['year']})")
                self.logger.info(f"  Cast: {len(cast)} members")
                self.logger.info(f"  Crew: {len(crew)} members")
                self.logger.info(f"  Genres: {', '.join(metadata['genres'])}")
            
            self._cache[cache_key] = metadata
            return metadata
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to fetch metadata: {e}", exc_info=True)
            import traceback
            traceback.print_exc()
            return None
    
    def get_soundtrack_info(self, movie_id: int) -> List[Dict[str, str]]:
        """
        Get soundtrack/music information for movie
        
        Note: TMDB doesn't have a direct soundtrack API.
        This returns music-related crew members.
        
        Args:
            movie_id: TMDB movie ID
        
        Returns:
            List of soundtrack entries
        """
        metadata = self.get_movie_metadata(movie_id)
        if not metadata:
            return []
        
        # Extract music crew
        soundtrack = []
        for person in metadata.get('crew', []):
            if person['department'] in ['Sound', 'Music']:
                soundtrack.append({
                    'name': person['name'],
                    'role': person['job']
                })
        
        return soundtrack
    
    def _movie_to_dict(self, movie) -> Dict[str, Any]:
        """Convert TMDB movie object to dict"""
        return {
            'id': movie.id,
            'title': movie.title,
            'original_title': getattr(movie, 'original_title', movie.title),
            'year': int(movie.release_date.split('-')[0]) if hasattr(movie, 'release_date') and movie.release_date else None,
            'overview': getattr(movie, 'overview', ''),
            'popularity': getattr(movie, 'popularity', 0),
            'vote_average': getattr(movie, 'vote_average', 0)
        }
    
    def clear_cache(self) -> None:
        """Clear API result cache"""
        self._cache.clear()
        if self.logger:
            self.logger.debug("TMDB cache cleared")


def load_api_key(config_path: Path = None) -> Optional[str]:
    """
    Load TMDB API key from config
    
    Args:
        config_path: Path to secrets.json
    
    Returns:
        API key or None
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config" / "secrets.json"
    
    if not config_path.exists():
        return None
    
    try:
        with open(config_path, 'r') as f:
            secrets = json.load(f)
            return secrets.get('tmdb_api_key')
    except Exception:
        return None
