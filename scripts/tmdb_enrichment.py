"""
tmdb_enrichment.py - TMDB metadata enrichment for proper-noun stabilization

Fetches cast and crew information from TMDB to improve ASR accuracy.
"""

import requests
from typing import Optional, List, Dict
from dataclasses import dataclass


@dataclass
class TMDBMetadata:
    """TMDB metadata for a movie"""
    title: str
    year: Optional[int]
    cast: List[str]
    crew: List[str]
    tmdb_id: Optional[int]
    found: bool


def search_tmdb(title: str, year: Optional[int], api_key: str) -> Optional[Dict]:
    """
    Search TMDB for a movie

    Args:
        title: Movie title
        year: Release year (optional, helps narrow results)
        api_key: TMDB API key

    Returns:
        First matching result or None
    """
    url = "https://api.themoviedb.org/3/search/movie"
    params = {
        "api_key": api_key,
        "query": title,
        "language": "en-US"
    }

    if year:
        params["year"] = year
        params["primary_release_year"] = year

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("results"):
            return data["results"][0]
        
        # If year was specified but no results, try without year
        if year and "year" in params:
            print(f"TMDB: No results with year {year}, retrying without year filter")
            params.pop("year", None)
            params.pop("primary_release_year", None)
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get("results"):
                return data["results"][0]
        
        return None
    except Exception as e:
        print(f"TMDB search error: {e}")
        return None


def get_movie_credits(tmdb_id: int, api_key: str) -> Dict:
    """
    Get cast and crew for a movie

    Args:
        tmdb_id: TMDB movie ID
        api_key: TMDB API key

    Returns:
        Dict with 'cast' and 'crew' lists
    """
    url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/credits"
    params = {"api_key": api_key}

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"TMDB credits error: {e}")
        return {"cast": [], "crew": []}


def enrich_from_tmdb(
    title: str,
    year: Optional[int],
    api_key: str,
    max_cast: int = 20,
    max_crew: int = 10
) -> TMDBMetadata:
    """
    Enrich movie metadata from TMDB

    Args:
        title: Movie title
        year: Release year (optional)
        api_key: TMDB API key
        max_cast: Maximum cast members to return
        max_crew: Maximum crew members to return

    Returns:
        TMDBMetadata with cast and crew lists
    """
    # Search for movie
    movie = search_tmdb(title, year, api_key)

    if not movie:
        return TMDBMetadata(
            title=title,
            year=year,
            cast=[],
            crew=[],
            tmdb_id=None,
            found=False
        )

    tmdb_id = movie["id"]
    tmdb_title = movie.get("title", title)
    release_date = movie.get("release_date", "")
    tmdb_year = int(release_date[:4]) if release_date else year

    # Get credits
    credits = get_movie_credits(tmdb_id, api_key)

    # Extract cast names
    cast_list = []
    for person in credits.get("cast", [])[:max_cast]:
        name = person.get("name")
        if name:
            cast_list.append(name)

    # Extract crew names (focus on director, writer, producer)
    crew_list = []
    important_jobs = ["Director", "Writer", "Screenplay", "Producer", "Music"]

    for person in credits.get("crew", []):
        name = person.get("name")
        job = person.get("job", "")

        if name and job in important_jobs and name not in crew_list:
            crew_list.append(name)

            if len(crew_list) >= max_crew:
                break

    return TMDBMetadata(
        title=tmdb_title,
        year=tmdb_year,
        cast=cast_list,
        crew=crew_list,
        tmdb_id=tmdb_id,
        found=True
    )


def format_tmdb_context(metadata: TMDBMetadata) -> str:
    """
    Format TMDB metadata as string for prompt injection

    Args:
        metadata: TMDBMetadata object

    Returns:
        Formatted string with cast and crew
    """
    if not metadata.found:
        return ""

    lines = []

    if metadata.cast:
        lines.append(f"Cast: {', '.join(metadata.cast[:15])}")

    if metadata.crew:
        lines.append(f"Crew: {', '.join(metadata.crew[:8])}")

    return "\n".join(lines)


def main():
    """Main entry point for TMDB enrichment stage."""
    import sys
    import os
    import json
    from pathlib import Path
    
    # Add project root to path
    PROJECT_ROOT = Path(__file__).parent.parent
    sys.path.insert(0, str(PROJECT_ROOT))
    
    from shared.stage_utils import StageIO, get_stage_logger
    from shared.config import load_config
    
    # Initialize stage I/O
    stage_io = StageIO("tmdb")
    logger = get_stage_logger("tmdb", log_level="DEBUG", stage_io=stage_io)
    
    logger.info("=" * 60)
    logger.info("TMDB STAGE: Fetch Cast and Crew Metadata")
    logger.info("=" * 60)
    
    # Load configuration
    config_path = os.environ.get('CONFIG_PATH', 'config/.env.pipeline')
    logger.debug(f"Loading configuration from: {config_path}")
    
    try:
        config = load_config(config_path)
        title = getattr(config, 'title', None)
        year = getattr(config, 'year', None)
        if year:
            try:
                year = int(year)
            except (ValueError, TypeError):
                year = None
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return 1
    
    if not title:
        logger.error("No title specified in configuration")
        return 1
    
    logger.info(f"Movie: {title} ({year if year else 'year unknown'})")
    
    # Get API key from secrets or environment
    api_key = None
    secrets_path = Path("config/secrets.json")
    if secrets_path.exists():
        logger.debug(f"Loading secrets from: {secrets_path}")
        try:
            with open(secrets_path, 'r') as f:
                secrets = json.load(f)
                api_key = secrets.get('tmdb_api_key')
        except Exception as e:
            logger.warning(f"Failed to load secrets: {e}")
    
    if not api_key:
        api_key = os.environ.get('TMDB_API_KEY')
    
    if not api_key:
        logger.warning("No TMDB API key found, skipping TMDB enrichment")
        # Still save empty metadata for downstream stages
        metadata = {
            'title': title,
            'year': year,
            'tmdb_id': None,
            'cast': [],
            'crew': [],
            'found': False
        }
        stage_io.save_json(metadata, 'tmdb_data.json')
        stage_io.save_metadata({'status': 'skipped', 'reason': 'no_api_key'})
        return 0
    
    # Fetch TMDB metadata
    logger.info("Fetching metadata from TMDB...")
    logger.debug(f"API Key: {'*' * (len(api_key) - 4)}{api_key[-4:]}")
    
    metadata_obj = enrich_from_tmdb(title, year, api_key)
    
    # Convert to dict
    metadata = {
        'title': metadata_obj.title,
        'year': metadata_obj.year,
        'tmdb_id': metadata_obj.tmdb_id,
        'cast': metadata_obj.cast,
        'crew': metadata_obj.crew,
        'found': metadata_obj.found
    }
    
    # Save metadata
    metadata_path = stage_io.save_json(metadata, 'tmdb_data.json')
    logger.debug(f"Saved TMDB data: {metadata_path}")
    
    if metadata_obj.found:
        logger.info(f"✓ TMDB metadata found (ID: {metadata_obj.tmdb_id})")
        logger.info(f"  Title: {metadata_obj.title}")
        logger.info(f"  Year: {metadata_obj.year}")
        logger.info(f"  Cast: {len(metadata_obj.cast)} members")
        logger.debug(f"  Cast names: {', '.join(metadata_obj.cast[:5])}...")
        logger.info(f"  Crew: {len(metadata_obj.crew)} members")
        logger.debug(f"  Crew names: {', '.join(metadata_obj.crew[:5])}")
        
        stage_io.save_metadata({
            'status': 'completed',
            'tmdb_id': metadata_obj.tmdb_id,
            'cast_count': len(metadata_obj.cast),
            'crew_count': len(metadata_obj.crew)
        })
    else:
        logger.warning("TMDB metadata not found")
        stage_io.save_metadata({'status': 'completed', 'found': False})
    
    logger.info("=" * 60)
    logger.info("TMDB STAGE COMPLETED")
    logger.info("=" * 60)
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
