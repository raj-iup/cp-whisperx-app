#!/usr/bin/env python3
"""
Centralized TMDB Data Loader

Provides unified access to TMDB enrichment data across all pipeline stages.
Eliminates code duplication and provides consistent error handling.
"""

import json
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass


@dataclass
class TMDBData:
    """TMDB enrichment data"""
    title: str
    year: Optional[int]
    cast: List[str]
    crew: List[str]
    soundtrack: List[Dict[str, str]]
    genres: List[str]
    imdb_id: Optional[str]
    tmdb_id: Optional[int]
    found: bool
    
    @classmethod
    def empty(cls) -> 'TMDBData':
        """Return empty TMDB data"""
        return cls(
            title="",
            year=None,
            cast=[],
            crew=[],
            soundtrack=[],
            genres=[],
            imdb_id=None,
            tmdb_id=None,
            found=False
        )


class TMDBLoader:
    """Centralized loader for TMDB enrichment data"""
    
    def __init__(self, output_base: Path, logger=None):
        """
        Initialize TMDB loader
        
        Args:
            output_base: Pipeline output base directory
            logger: Optional logger instance
        """
        self.output_base = Path(output_base)
        self.logger = logger
        self._cache: Optional[TMDBData] = None
    
    def load(self, force_reload: bool = False) -> TMDBData:
        """
        Load TMDB enrichment data
        
        Args:
            force_reload: Force reload even if cached
        
        Returns:
            TMDBData instance
        """
        # Return cached if available
        if self._cache and not force_reload:
            return self._cache
        
        # Find enrichment file
        enrichment_file = self.output_base / "02_tmdb" / "enrichment.json"
        
        if not enrichment_file.exists():
            if self.logger:
                self.logger.debug(f"TMDB enrichment not found: {enrichment_file}")
            self._cache = TMDBData.empty()
            return self._cache
        
        try:
            with open(enrichment_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Parse into TMDBData
            self._cache = TMDBData(
                title=data.get('title', ''),
                year=data.get('year'),
                cast=data.get('cast', []),
                crew=data.get('crew', []),
                soundtrack=data.get('soundtrack', []),
                genres=data.get('genres', []),
                imdb_id=data.get('imdb_id'),
                tmdb_id=data.get('tmdb_id'),
                found=data.get('found', False)
            )
            
            if self.logger:
                self.logger.debug(f"Loaded TMDB data: {self._cache.title} ({self._cache.year})")
                self.logger.debug(f"  Cast: {len(self._cache.cast)} | Crew: {len(self._cache.crew)}")
                self.logger.debug(f"  Soundtrack: {len(self._cache.soundtrack)} tracks")
            
            return self._cache
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to load TMDB enrichment: {e}")
            self._cache = TMDBData.empty()
            return self._cache
    
    def get_soundtrack(self) -> List[Dict[str, str]]:
        """
        Get soundtrack information
        
        Returns:
            List of soundtrack entries with title, artist, composer
        """
        data = self.load()
        return data.soundtrack
    
    def get_cast_names(self) -> List[str]:
        """Get list of cast member names"""
        data = self.load()
        return data.cast
    
    def get_crew_names(self) -> List[str]:
        """Get list of crew member names"""
        data = self.load()
        return data.crew
    
    def get_all_person_names(self) -> List[str]:
        """Get combined list of all cast and crew names"""
        data = self.load()
        return data.cast + data.crew
    
    def get_genres(self) -> List[str]:
        """Get movie genres"""
        data = self.load()
        return data.genres
    
    def is_bollywood(self) -> bool:
        """
        Detect if movie is Bollywood/Indian cinema
        
        Uses heuristics:
        - Has Hindi genre/language
        - IMDb ID patterns
        - Common Bollywood cast/crew
        
        Returns:
            True if likely Bollywood
        """
        data = self.load()
        
        if not data.found:
            return False
        
        # Check genres for Indian cinema markers
        bollywood_markers = ['bollywood', 'hindi', 'tamil', 'telugu', 'indian']
        genres_lower = [g.lower() for g in data.genres]
        
        if any(marker in ' '.join(genres_lower) for marker in bollywood_markers):
            return True
        
        # Check if has soundtrack (most Bollywood movies do)
        if len(data.soundtrack) >= 4:  # Typically 4+ songs
            # Check for Indian artist names
            indian_artists = [
                'kumar', 'sanu', 'kishore', 'lata', 'asha', 'rafi', 
                'udit', 'alka', 'sonu', 'shreya', 'arijit', 'neha'
            ]
            
            soundtrack_text = ' '.join([
                song.get('artist', '').lower() for song in data.soundtrack
            ])
            
            if any(artist in soundtrack_text for artist in indian_artists):
                return True
        
        return False
    
    def should_enable_song_bias(self) -> bool:
        """
        Determine if song bias should be enabled
        
        Enables song bias if:
        - Movie is Bollywood
        - Has soundtrack data
        
        Returns:
            True if song bias should be enabled
        """
        data = self.load()
        
        if not data.found:
            return False
        
        # Must have soundtrack
        if not data.soundtrack:
            return False
        
        # Auto-enable for Bollywood
        if self.is_bollywood():
            return True
        
        # Enable if has significant soundtrack (5+ songs)
        if len(data.soundtrack) >= 5:
            return True
        
        return False
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get all TMDB metadata as dict
        
        Returns:
            Dict with all TMDB data
        """
        data = self.load()
        return {
            'title': data.title,
            'year': data.year,
            'cast': data.cast,
            'crew': data.crew,
            'soundtrack': data.soundtrack,
            'genres': data.genres,
            'imdb_id': data.imdb_id,
            'tmdb_id': data.tmdb_id,
            'found': data.found,
            'is_bollywood': self.is_bollywood(),
            'should_enable_song_bias': self.should_enable_song_bias()
        }
