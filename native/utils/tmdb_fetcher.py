"""
TMDB API client for fetching movie metadata.
Supports both real API calls and offline fallback.
"""
import os
import json
import requests
from typing import Optional, Dict, List, Any
from pathlib import Path


class TMDBFetcher:
    """Fetch movie metadata from TMDB API."""
    
    BASE_URL = "https://api.themoviedb.org/3"
    IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"
    
    def __init__(self, api_key: Optional[str] = None, logger=None):
        """
        Initialize TMDB fetcher.
        
        Args:
            api_key: TMDB API key (required for API access)
            logger: Logger instance for logging
        """
        self.api_key = api_key
        self.logger = logger
        self.session = requests.Session()
        
        # Check if API key is available
        if not self.api_key or self.api_key.strip() == '':
            if self.logger:
                self.logger.warning("No TMDB API key provided - will use fallback data")
            self.offline_mode = True
        else:
            self.offline_mode = False
            if self.logger:
                self.logger.debug(f"TMDB API key configured: {self.api_key[:8]}...")
    
    def search_movie(self, title: str, year: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Search for a movie by title and optional year.
        
        Args:
            title: Movie title to search for
            year: Optional release year to narrow search
            
        Returns:
            Movie data dict or None if not found
        """
        if self.offline_mode:
            return self._get_fallback_data(title, year)
        
        try:
            # Search for movie
            params = {
                'api_key': self.api_key,
                'query': title,
                'language': 'en-US'
            }
            
            if year:
                params['year'] = year
            
            if self.logger:
                self.logger.debug(f"Searching TMDB for: {title} ({year})")
            
            response = self.session.get(
                f"{self.BASE_URL}/search/movie",
                params=params,
                timeout=10
            )
            
            if response.status_code != 200:
                if self.logger:
                    self.logger.error(f"TMDB API error: {response.status_code}")
                return self._get_fallback_data(title, year)
            
            results = response.json()
            
            if not results.get('results'):
                if self.logger:
                    self.logger.warning(f"No results found for: {title}")
                return self._get_fallback_data(title, year)
            
            # Get first result (best match)
            movie = results['results'][0]
            movie_id = movie['id']
            
            if self.logger:
                self.logger.info(f"Found: {movie.get('title')} ({movie.get('release_date', '')[:4]})")
            
            # Fetch detailed movie data
            return self.get_movie_details(movie_id)
            
        except requests.exceptions.RequestException as e:
            if self.logger:
                self.logger.error(f"TMDB API request failed: {e}")
            return self._get_fallback_data(title, year)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Unexpected error fetching TMDB data: {e}")
            return self._get_fallback_data(title, year)
    
    def get_movie_details(self, movie_id: int) -> Dict[str, Any]:
        """
        Get detailed movie information including cast and crew.
        
        Args:
            movie_id: TMDB movie ID
            
        Returns:
            Detailed movie data dict
        """
        try:
            # Get movie details
            response = self.session.get(
                f"{self.BASE_URL}/movie/{movie_id}",
                params={
                    'api_key': self.api_key,
                    'append_to_response': 'credits,keywords'
                },
                timeout=10
            )
            
            if response.status_code != 200:
                if self.logger:
                    self.logger.error(f"Failed to get movie details: {response.status_code}")
                return {}
            
            movie_data = response.json()
            
            # Extract relevant data
            data = {
                'id': movie_data.get('id'),
                'imdb_id': movie_data.get('imdb_id'),
                'title': movie_data.get('title'),
                'original_title': movie_data.get('original_title'),
                'year': movie_data.get('release_date', '')[:4] if movie_data.get('release_date') else None,
                'release_date': movie_data.get('release_date'),
                'runtime': movie_data.get('runtime'),
                'overview': movie_data.get('overview', ''),
                'plot': movie_data.get('overview', ''),  # Alias
                'tagline': movie_data.get('tagline', ''),
                'genres': [g['name'] for g in movie_data.get('genres', [])],
                'languages': [lang['name'] for lang in movie_data.get('spoken_languages', [])],
                'countries': [c['name'] for c in movie_data.get('production_countries', [])],
                'budget': movie_data.get('budget'),
                'revenue': movie_data.get('revenue'),
                'popularity': movie_data.get('popularity'),
                'vote_average': movie_data.get('vote_average'),
                'vote_count': movie_data.get('vote_count'),
                'poster_path': movie_data.get('poster_path'),
                'backdrop_path': movie_data.get('backdrop_path'),
            }
            
            # Extract cast
            credits = movie_data.get('credits', {})
            data['cast'] = [
                {
                    'id': person.get('id'),
                    'name': person.get('name'),
                    'character': person.get('character'),
                    'order': person.get('order'),
                    'profile_path': person.get('profile_path')
                }
                for person in credits.get('cast', [])[:20]  # Top 20 cast
            ]
            
            # Extract crew (directors, writers, producers)
            crew = credits.get('crew', [])
            data['directors'] = [
                {'id': p.get('id'), 'name': p.get('name')}
                for p in crew if p.get('job') == 'Director'
            ]
            data['writers'] = [
                {'id': p.get('id'), 'name': p.get('name')}
                for p in crew if p.get('department') == 'Writing'
            ][:10]
            data['producers'] = [
                {'id': p.get('id'), 'name': p.get('name')}
                for p in crew if 'Producer' in p.get('job', '')
            ][:5]
            
            # Store full crew for reference
            data['crew'] = crew
            
            # Extract keywords
            keywords = movie_data.get('keywords', {}).get('keywords', [])
            data['keywords'] = [kw.get('name') for kw in keywords]
            
            if self.logger:
                self.logger.debug(f"Fetched {len(data['cast'])} cast, {len(data['crew'])} crew")
            
            return data
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error getting movie details: {e}")
            return {}
    
    def _get_fallback_data(self, title: str, year: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate fallback data when TMDB API is unavailable.
        
        Args:
            title: Movie title
            year: Optional year
            
        Returns:
            Minimal movie data dict
        """
        if self.logger:
            self.logger.warning(f"Using fallback data for: {title}")
        
        return {
            'id': None,
            'imdb_id': None,
            'title': title,
            'original_title': title,
            'year': str(year) if year else None,
            'release_date': f"{year}-01-01" if year else None,
            'runtime': None,
            'overview': f"Movie metadata for {title} - TMDB API unavailable",
            'plot': f"Movie metadata for {title} - TMDB API unavailable",
            'tagline': '',
            'genres': [],
            'languages': [],
            'countries': [],
            'budget': None,
            'revenue': None,
            'popularity': None,
            'vote_average': None,
            'vote_count': None,
            'poster_path': None,
            'backdrop_path': None,
            'cast': [],
            'directors': [],
            'writers': [],
            'producers': [],
            'crew': [],
            'keywords': [],
            'data_source': 'fallback',
            'note': 'TMDB API key not configured - using placeholder data'
        }
    
    def get_person_details(self, person_id: int) -> Dict[str, Any]:
        """
        Get detailed person information.
        
        Args:
            person_id: TMDB person ID
            
        Returns:
            Person data dict
        """
        if self.offline_mode:
            return {}
        
        try:
            response = self.session.get(
                f"{self.BASE_URL}/person/{person_id}",
                params={'api_key': self.api_key},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            return {}
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error getting person details: {e}")
            return {}
    
    def close(self):
        """Close the requests session."""
        self.session.close()
