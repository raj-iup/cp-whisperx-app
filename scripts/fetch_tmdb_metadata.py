#!/usr/bin/env python3
"""
fetch_tmdb_metadata.py - CLI Tool for TMDB Metadata Fetching

Phase 1 Implementation: Manual TMDB testing tool

Usage:
    python scripts/fetch_tmdb_metadata.py \
        --title "Jaane Tu Ya Jaane Na" \
        --year 2008 \
        --output test_glossary.yaml \
        --cache-dir cache/tmdb
        
Features:
- Fetch movie metadata from TMDB
- Generate glossary from cast/crew
- Cache results for offline testing
- JSON and YAML output formats
"""

import sys
import argparse
import json
import yaml
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.logger import PipelineLogger
from shared.config import Config

# Local
from shared.logger import get_logger
logger = get_logger(__name__)


class TMDBFetcher:
    """Fetch and process TMDB metadata"""
    
    def __init__(self, api_key: str, cache_dir: Optional[Path] = None, logger: Optional[PipelineLogger] = None):
        """
        Initialize TMDB fetcher
        
        Args:
            api_key: TMDB API key
            cache_dir: Optional cache directory
            logger: Logger instance
        """
        self.api_key = api_key
        self.cache_dir = cache_dir
        self.logger = logger or self._create_default_logger()
        
        # Import TMDB library
        try:
            from tmdbv3api import TMDb, Movie
            self.tmdb = TMDb()
            self.tmdb.api_key = api_key
            self.tmdb.language = 'en-US'
            self.movie_api = Movie()
        except ImportError:
            self.logger.error("tmdbv3api not installed. Run: pip install tmdbv3api")
            sys.exit(1)
    
    def _create_default_logger(self) -> PipelineLogger:
        """Create default logger"""
        return PipelineLogger(
            module_name="fetch_tmdb",
            log_level="INFO"
        )
    
    def fetch_movie(self, title: str, year: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Fetch movie metadata from TMDB
        
        Args:
            title: Movie title
            year: Optional release year for better matching
            
        Returns:
            Movie metadata dict or None if not found
        """
        self.logger.info("=" * 60)
        self.logger.info("TMDB METADATA FETCH")
        self.logger.info("=" * 60)
        self.logger.info(f"Title: {title}")
        if year:
            self.logger.info(f"Year: {year}")
        
        try:
            # Search for movie
            search_query = title
            if year:
                search_query = f"{title} y:{year}"
            
            self.logger.info(f"Searching: {search_query}")
            search_results = self.movie_api.search(title)
            
            if not search_results:
                self.logger.error(f"No results found for '{title}'")
                return None
            
            # Find best match
            best_match = None
            for result in search_results:
                if year:
                    # Match by year
                    release_year = getattr(result, 'release_date', '')[:4]
                    if release_year == str(year):
                        best_match = result
                        break
                else:
                    # Use first result
                    best_match = result
                    break
            
            if not best_match:
                # Fallback to first result
                best_match = search_results[0]
            
            movie_id = best_match.id
            self.logger.info(f"✓ Found: {best_match.title} ({getattr(best_match, 'release_date', 'N/A')[:4]})")
            self.logger.info(f"  TMDB ID: {movie_id}")
            
            # Get detailed info
            movie = self.movie_api.details(movie_id)
            credits = self.movie_api.credits(movie_id)
            
            # Extract metadata
            metadata = {
                'title': movie.title,
                'original_title': getattr(movie, 'original_title', movie.title),
                'year': int(getattr(movie, 'release_date', '')[:4]) if getattr(movie, 'release_date', '') else None,
                'tmdb_id': movie_id,
                'imdb_id': getattr(movie, 'imdb_id', None),
                'overview': getattr(movie, 'overview', ''),
                'genres': [g['name'] for g in getattr(movie, 'genres', [])],
                'cast': [
                    {
                        'name': cast['name'],
                        'character': cast.get('character', ''),
                        'order': cast.get('order', 999)
                    }
                    for cast in credits.get('cast', [])[:20]  # Top 20 cast
                ],
                'crew': [
                    {
                        'name': crew['name'],
                        'job': crew.get('job', ''),
                        'department': crew.get('department', '')
                    }
                    for crew in credits.get('crew', [])
                    if crew.get('job') in ['Director', 'Writer', 'Producer', 'Music']
                ],
                'fetched_at': datetime.now().isoformat()
            }
            
            self.logger.info(f"  Cast: {len(metadata['cast'])} members")
            self.logger.info(f"  Crew: {len(metadata['crew'])} members")
            self.logger.info(f"  Genres: {', '.join(metadata['genres'])}")
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"Failed to fetch TMDB data: {e}")
            return None
    
    def generate_glossary(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate glossary from TMDB metadata
        
        Args:
            metadata: TMDB movie metadata
            
        Returns:
            Glossary dict
        """
        self.logger.info("")
        self.logger.info("Generating glossary from metadata...")
        
        glossary = {
            'movie': metadata['title'],
            'year': metadata['year'],
            'tmdb_id': metadata['tmdb_id'],
            'imdb_id': metadata['imdb_id'],
            'characters': [],
            'crew': [],
            'generated_at': datetime.now().isoformat()
        }
        
        # Extract character names
        for cast in metadata['cast'][:10]:  # Top 10 characters
            character_name = cast['character']
            if not character_name or character_name == '':
                continue
            
            # Split multi-character names (e.g., "Jai Singh Rathore / Ratty")
            character_names = character_name.split(' / ')
            primary_name = character_names[0].strip()
            
            # Generate aliases (first names, nicknames)
            aliases = []
            if ' ' in primary_name:
                # Add first name
                first_name = primary_name.split()[0]
                aliases.append(first_name)
            
            # Add alternate names
            for alt_name in character_names[1:]:
                aliases.append(alt_name.strip())
            
            glossary['characters'].append({
                'name': primary_name,
                'actor': cast['name'],
                'aliases': aliases if aliases else [],
                'order': cast['order']
            })
        
        # Extract crew names
        for crew_member in metadata['crew']:
            glossary['crew'].append({
                'name': crew_member['name'],
                'job': crew_member['job'],
                'department': crew_member.get('department', '')
            })
        
        self.logger.info(f"✓ Glossary generated:")
        self.logger.info(f"  {len(glossary['characters'])} characters")
        self.logger.info(f"  {len(glossary['crew'])} crew members")
        
        return glossary
    
    def save_metadata(self, metadata: Dict[str, Any], output_path: Path, format: str = 'json'):
        """
        Save metadata to file
        
        Args:
            metadata: Metadata dict
            output_path: Output file path
            format: Output format (json or yaml)
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == 'yaml':
            with open(output_path, 'w') as f:
                yaml.dump(metadata, f, default_flow_style=False, sort_keys=False)
        else:
            with open(output_path, 'w') as f:
                json.dump(metadata, f, indent=2)
        
        self.logger.info(f"✓ Saved to: {output_path}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Fetch movie metadata from TMDB and generate glossary',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch metadata and generate glossary
  %(prog)s --title "Jaane Tu Ya Jaane Na" --year 2008 --output glossary.yaml
  
  # Fetch metadata only (JSON format)
  %(prog)s --title "3 Idiots" --year 2009 --output metadata.json --format json
  
  # Use cache directory for offline testing
  %(prog)s --title "Zindagi Na Milegi Dobara" --year 2011 --cache-dir cache/tmdb
        """
    )
    
    parser.add_argument('--title', required=True, help='Movie title')
    parser.add_argument('--year', type=int, help='Release year (for better matching)')
    parser.add_argument('--output', type=Path, required=True, help='Output file path')
    parser.add_argument('--format', choices=['json', 'yaml'], default='yaml', help='Output format (default: yaml)')
    parser.add_argument('--cache-dir', type=Path, help='Cache directory (optional)')
    parser.add_argument('--metadata-only', action='store_true', help='Save full metadata (no glossary generation)')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    # Load config
    config = Config(PROJECT_ROOT)
    api_key = config.get_secret('tmdb_api_key')
    
    if not api_key:
        print("❌ TMDB API key not found in config/secrets.json")
        print("Get your free key at: https://www.themoviedb.org/signup")
        print('Add to config/secrets.json: {"tmdb_api_key": "your_key_here"}')
        return 1
    
    # Create logger
    logger = PipelineLogger(
        module_name="fetch_tmdb",
        log_level="DEBUG" if args.debug else "INFO"
    )
    
    # Fetch metadata
    fetcher = TMDBFetcher(api_key=api_key, cache_dir=args.cache_dir, logger=logger)
    metadata = fetcher.fetch_movie(title=args.title, year=args.year)
    
    if not metadata:
        logger.error("Failed to fetch metadata")
        return 1
    
    # Generate output
    if args.metadata_only:
        # Save full metadata
        output_data = metadata
        logger.info("")
        logger.info("Saving full metadata...")
    else:
        # Generate and save glossary
        output_data = fetcher.generate_glossary(metadata)
    
    # Save to file
    fetcher.save_metadata(output_data, args.output, format=args.format)
    
    logger.info("=" * 60)
    logger.info("✓ SUCCESS")
    logger.info("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
