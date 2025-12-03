#!/usr/bin/env python3
"""
Centralized Bias Terms Registry

Provides unified access to bias terms from multiple sources:
- TMDB cast/crew
- Soundtrack data (songs, artists, composers)
- Glossary terms
- Character names

Eliminates duplicate loading logic across stages.
"""

from pathlib import Path
from typing import List, Dict, Set, Optional
from dataclasses import dataclass, field

# Local
from shared.logger import get_logger
logger = get_logger(__name__)


@dataclass
class BiasTerms:
    """Container for bias terms from various sources"""
    
    # Character names from TMDB
    cast_names: List[str] = field(default_factory=list)
    crew_names: List[str] = field(default_factory=list)
    
    # Song-related terms
    song_titles: List[str] = field(default_factory=list)
    artist_names: List[str] = field(default_factory=list)
    composer_names: List[str] = field(default_factory=list)
    
    # Glossary terms
    glossary_terms: List[str] = field(default_factory=list)
    
    def get_character_bias_terms(self) -> List[str]:
        """Get bias terms for character names (ASR stage)"""
        return self._unique_terms(self.cast_names + self.crew_names)
    
    def get_song_bias_terms(self) -> List[str]:
        """Get bias terms for songs (song bias injection stage)"""
        return self._unique_terms(
            self.song_titles + 
            self.artist_names + 
            self.composer_names
        )
    
    def get_all_bias_terms(self) -> List[str]:
        """Get all bias terms combined"""
        return self._unique_terms(
            self.cast_names +
            self.crew_names +
            self.song_titles +
            self.artist_names +
            self.composer_names +
            self.glossary_terms
        )
    
    def _unique_terms(self, terms: List[str]) -> List[str]:
        """Remove duplicates while preserving order"""
        seen: Set[str] = set()
        unique = []
        for term in terms:
            term = term.strip()
            if term and term not in seen:
                seen.add(term)
                unique.append(term)
        return unique
    
    def count(self) -> Dict[str, int]:
        """Get count of terms by category"""
        return {
            'cast': len(self.cast_names),
            'crew': len(self.crew_names),
            'songs': len(self.song_titles),
            'artists': len(self.artist_names),
            'composers': len(self.composer_names),
            'glossary': len(self.glossary_terms),
            'total_character': len(self.get_character_bias_terms()),
            'total_song': len(self.get_song_bias_terms()),
            'total_all': len(self.get_all_bias_terms())
        }


class BiasRegistry:
    """Centralized registry for all bias terms"""
    
    def __init__(self, output_base: Path, logger=None):
        """
        Initialize bias registry
        
        Args:
            output_base: Pipeline output base directory
            logger: Optional logger instance
        """
        self.output_base = Path(output_base)
        self.logger = logger
        self._cache: Optional[BiasTerms] = None
    
    def load(self, force_reload: bool = False) -> BiasTerms:
        """
        Load all bias terms
        
        Args:
            force_reload: Force reload even if cached
        
        Returns:
            BiasTerms instance
        """
        if self._cache and not force_reload:
            return self._cache
        
        terms = BiasTerms()
        
        # Load TMDB data
        try:
            from shared.tmdb_loader import TMDBLoader
            tmdb_loader = TMDBLoader(self.output_base, self.logger)
            tmdb_data = tmdb_loader.load()
            
            if tmdb_data.found:
                terms.cast_names = tmdb_data.cast
                terms.crew_names = tmdb_data.crew
                
                # Extract song terms
                for song in tmdb_data.soundtrack:
                    # Song title
                    title = song.get('title', '').strip()
                    if title:
                        terms.song_titles.append(title)
                    
                    # Artists (may be comma-separated)
                    artist = song.get('artist', '').strip()
                    if artist:
                        for name in artist.split(','):
                            name = name.strip()
                            if name:
                                terms.artist_names.append(name)
                    
                    # Composer
                    composer = song.get('composer', '').strip()
                    if composer:
                        terms.composer_names.append(composer)
                
                if self.logger:
                    self.logger.debug(f"Loaded TMDB bias terms:")
                    self.logger.debug(f"  Cast: {len(terms.cast_names)}")
                    self.logger.debug(f"  Crew: {len(terms.crew_names)}")
                    self.logger.debug(f"  Songs: {len(terms.song_titles)}")
                    self.logger.debug(f"  Artists: {len(terms.artist_names)}")
        
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Could not load TMDB bias terms: {e}")
        
        # Load glossary terms
        try:
            glossary_file = self.output_base / "11_glossary_builder" / "glossary.txt"
            if glossary_file.exists():
                with open(glossary_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        term = line.split('\t')[0].strip()
                        if term:
                            terms.glossary_terms.append(term)
                
                if self.logger:
                    self.logger.debug(f"  Glossary: {len(terms.glossary_terms)} terms")
        
        except Exception as e:
            if self.logger:
                self.logger.debug(f"Could not load glossary: {e}")
        
        self._cache = terms
        return terms
    
    def get_for_stage(self, stage_name: str) -> List[str]:
        """
        Get bias terms appropriate for a specific stage
        
        Args:
            stage_name: Stage name (e.g., 'asr', 'song_bias_injection')
        
        Returns:
            List of bias terms
        """
        terms = self.load()
        
        if stage_name == 'asr':
            # ASR stage: character names only
            return terms.get_character_bias_terms()
        
        elif stage_name == 'song_bias_injection':
            # Song bias: song-specific terms
            return terms.get_song_bias_terms()
        
        elif stage_name == 'bias_correction':
            # General bias correction: all terms
            return terms.get_all_bias_terms()
        
        else:
            # Default: all terms
            return terms.get_all_bias_terms()
    
    def log_summary(self):
        """Log summary of loaded bias terms"""
        terms = self.load()
        counts = terms.count()
        
        if self.logger:
            self.logger.info("=== Bias Terms Summary ===")
            self.logger.info(f"Character names: {counts['total_character']} (cast: {counts['cast']}, crew: {counts['crew']})")
            self.logger.info(f"Song terms: {counts['total_song']} (songs: {counts['songs']}, artists: {counts['artists']}, composers: {counts['composers']})")
            self.logger.info(f"Glossary terms: {counts['glossary']}")
            self.logger.info(f"Total unique terms: {counts['total_all']}")
