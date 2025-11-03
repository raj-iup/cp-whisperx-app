#!/usr/bin/env python3
"""
TMDB Metadata Fetch Step
Fetches movie metadata from TMDB API to enrich ASR prompts.
Outputs to: out/{movie}/metadata/
"""
import sys
import json
from pathlib import Path
from typing import Optional, Dict, List

sys.path.insert(0, '/app/shared')
from config import load_config
from logger import setup_logger
from utils import save_json, parse_filename, get_movie_dir


def search_tmdb(title: str, year: Optional[str], api_key: str, language: str, logger) -> Optional[Dict]:
    """
    Search TMDB for movie metadata.
    
    Args:
        title: Movie title
        year: Release year (optional)
        api_key: TMDB API key
        language: TMDB language code (e.g., 'en-US', 'es-ES')
        logger: Logger instance
    
    Returns:
        Movie metadata dict or None if not found
    """
    try:
        from tmdbv3api import TMDb, Movie
        
        # Initialize TMDB
        tmdb = TMDb()
        tmdb.api_key = api_key
        tmdb.language = language
        
        movie_api = Movie()
        
        # Search for movie
        logger.info(f"Searching TMDB for: '{title}' ({year if year else 'any year'})")
        
        search_results = movie_api.search(title)
        
        if not search_results:
            logger.warning(f"No results found for '{title}'")
            return None
        
        # Find best match (prioritize year match if provided)
        best_match = None
        for result in search_results:
            if year:
                release_year = result.release_date.split('-')[0] if result.release_date else None
                if release_year == year:
                    best_match = result
                    break
            if not best_match:
                best_match = result
        
        if not best_match:
            best_match = search_results[0]
        
        logger.info(f"Found match: {best_match.title} ({best_match.release_date})")
        logger.info(f"TMDB ID: {best_match.id}")
        
        # Get full movie details
        movie_details = movie_api.details(best_match.id)
        
        # Get credits (cast and crew)
        credits = movie_api.credits(best_match.id)
        
        # Extract metadata
        metadata = {
            "tmdb_id": movie_details.id,
            "title": movie_details.title,
            "original_title": getattr(movie_details, 'original_title', movie_details.title),
            "release_date": getattr(movie_details, 'release_date', ''),
            "overview": getattr(movie_details, 'overview', ''),
            "tagline": getattr(movie_details, 'tagline', ''),
            "runtime": getattr(movie_details, 'runtime', 0),
            "genres": [g['name'] for g in getattr(movie_details, 'genres', [])] if hasattr(movie_details, 'genres') else [],
            "production_countries": [c['name'] for c in getattr(movie_details, 'production_countries', [])] if hasattr(movie_details, 'production_countries') else [],
            "spoken_languages": [l['name'] for l in getattr(movie_details, 'spoken_languages', [])] if hasattr(movie_details, 'spoken_languages') else [],
            "cast": [],
            "crew": [],
            "keywords": []
        }
        
        # Extract cast (top 20)
        if credits and hasattr(credits, 'cast'):
            try:
                for i, person in enumerate(credits.cast):
                    if i >= 20:
                        break
                    metadata["cast"].append({
                        "name": getattr(person, 'name', ''),
                        "character": getattr(person, 'character', ''),
                        "order": getattr(person, 'order', i)
                    })
            except Exception as e:
                logger.debug(f"Error extracting cast: {e}")
        
        # Extract key crew (directors, writers, producers)
        if credits and hasattr(credits, 'crew'):
            try:
                key_jobs = ['Director', 'Writer', 'Screenplay', 'Producer']
                for person in credits.crew:
                    if getattr(person, 'job', '') in key_jobs:
                        metadata["crew"].append({
                            "name": getattr(person, 'name', ''),
                            "job": getattr(person, 'job', '')
                        })
            except Exception as e:
                logger.debug(f"Error extracting crew: {e}")
        
        # Get keywords
        try:
            keywords_result = movie_api.keywords(best_match.id)
            if keywords_result and hasattr(keywords_result, 'keywords'):
                metadata["keywords"] = [kw['name'] for kw in keywords_result.keywords]
        except Exception as e:
            logger.debug(f"Could not fetch keywords: {e}")
        
        logger.info(f"Extracted {len(metadata['cast'])} cast members")
        logger.info(f"Extracted {len(metadata['crew'])} crew members")
        logger.info(f"Extracted {len(metadata['keywords'])} keywords")
        
        return metadata
        
    except Exception as e:
        logger.error(f"TMDB API error: {e}")
        return None


def generate_asr_prompt(metadata: Dict, logger) -> str:
    """
    Generate ASR initial prompt from TMDB metadata.
    
    Args:
        metadata: TMDB metadata dict
        logger: Logger instance
    
    Returns:
        Initial prompt string for WhisperX
    """
    prompt_parts = []
    
    # Title and year
    if metadata.get('title'):
        year = metadata.get('release_date', '')[:4] if metadata.get('release_date') else ''
        prompt_parts.append(f"Title: {metadata['title']}")
        if year:
            prompt_parts.append(f"Year: {year}")
    
    # Genres
    if metadata.get('genres'):
        prompt_parts.append(f"Genres: {', '.join(metadata['genres'][:3])}")
    
    # Cast names (for better name recognition)
    if metadata.get('cast'):
        cast_names = [person['name'] for person in metadata['cast'][:10]]
        prompt_parts.append(f"Cast: {', '.join(cast_names)}")
    
    # Directors
    directors = [person['name'] for person in metadata.get('crew', []) if person['job'] == 'Director']
    if directors:
        prompt_parts.append(f"Director: {', '.join(directors)}")
    
    # Keywords (context for content)
    if metadata.get('keywords'):
        prompt_parts.append(f"Themes: {', '.join(metadata['keywords'][:5])}")
    
    prompt = "\n".join(prompt_parts)
    
    logger.info(f"Generated prompt with {len(prompt)} characters")
    
    return prompt


def main():
    """Main entry point."""
    # Validate arguments BEFORE setting up logger
    if len(sys.argv) < 3:
        # Check if we can fall back to config
        try:
            config = load_config()
            if not config.output_root:
                print("ERROR: Usage: tmdb.py <output_dir> <title> [year]", file=sys.stderr)
                sys.exit(1)
        except:
            print("ERROR: Usage: tmdb.py <output_dir> <title> [year]", file=sys.stderr)
            sys.exit(1)
    else:
        config = load_config()
    
    logger = setup_logger(
        "tmdb",
        log_level=config.log_level,
        log_format=config.log_format,
        log_to_console=config.log_to_console,
        log_to_file=config.log_to_file,
        log_dir=config.log_root
    )
    
    logger.info("Starting TMDB metadata fetch")
    
    # Check if TMDB is enabled
    if not config.tmdb_enabled:
        logger.info("TMDB metadata fetch is disabled in config")
        sys.exit(0)
    
    # Get API key
    secrets = config.load_secrets()
    api_key = config.tmdb_api_key or secrets.get('TMDB_API_KEY') or secrets.get('tmdb_api_key')
    
    if not api_key:
        logger.error("TMDB API key not found in config or secrets.json")
        logger.error("Please set TMDB_API_KEY in config/.env or config/secrets.json")
        sys.exit(1)
    
    # Get movie title, year, and output directory from command line
    # Expected: tmdb.py <output_dir> <title> [year]
    if len(sys.argv) >= 3:
        movie_dir = Path(sys.argv[1])
        title = sys.argv[2]
        year = sys.argv[3] if len(sys.argv) >= 4 else None
        logger.info(f"Using output directory from argument: {movie_dir}")
    else:
        # Must have been validated earlier - use output_root
        # Always use output_root directly when it's set (should be job-specific)
        movie_dir = Path(config.output_root)
        # Parse from config - this path shouldn't normally be reached
        title = "Unknown"
        year = None
        logger.info(f"Using output_root as movie directory: {movie_dir}")
    
    logger.info(f"Movie: {title}")
    if year:
        logger.info(f"Year: {year}")
    logger.info(f"Output directory: {movie_dir}")
    
    # Get TMDB language from config
    tmdb_language = getattr(config, 'tmdb_language', 'en-US')
    logger.info(f"TMDB language: {tmdb_language}")
    
    # Search TMDB
    metadata = search_tmdb(title, year, api_key, tmdb_language, logger)
    
    if not metadata:
        logger.warning("Could not fetch TMDB metadata")
        # Create empty metadata file so pipeline can continue
        metadata = {
            "tmdb_id": None,
            "title": title,
            "year": year,
            "cast": [],
            "crew": [],
            "keywords": [],
            "error": "No results found"
        }
    
    # Save metadata
    metadata_dir = movie_dir / "metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    
    metadata_file = metadata_dir / "tmdb_data.json"
    save_json(metadata, metadata_file)
    logger.info(f"Metadata saved: {metadata_file}")
    
    # Generate and save ASR prompt
    if metadata.get('tmdb_id'):
        prompt = generate_asr_prompt(metadata, logger)
        
        prompt_dir = movie_dir / "prompts"
        prompt_dir.mkdir(parents=True, exist_ok=True)
        
        prompt_file = prompt_dir / "tmdb_prompt.txt"
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(prompt)
        
        logger.info(f"ASR prompt saved: {prompt_file}")
        logger.debug(f"Prompt preview:\n{prompt[:200]}...")
    
    logger.info("TMDB metadata fetch completed successfully")
    sys.exit(0)


if __name__ == "__main__":
    main()
