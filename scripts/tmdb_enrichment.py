"""
tmdb_enrichment.py - TMDB metadata enrichment for proper-noun stabilization

Fetches cast, crew, and soundtrack information from TMDB to improve ASR accuracy.
For soundtrack data, uses a combination of TMDB external IDs and local database.
"""

import requests
import json
from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass


@dataclass
class TMDBMetadata:
    """TMDB metadata for a movie"""
    title: str
    year: Optional[int]
    cast: List[str]
    crew: List[str]
    soundtrack: List[Dict[str, str]]  # List of {title, artist, composer}
    genres: List[str]
    imdb_id: Optional[str]
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


def get_movie_details(tmdb_id: int, api_key: str) -> Dict:
    """
    Get detailed movie information including external IDs and keywords
    
    Args:
        tmdb_id: TMDB movie ID
        api_key: TMDB API key
    
    Returns:
        Dict with movie details, external_ids, and keywords
    """
    url = f"https://api.themoviedb.org/3/movie/{tmdb_id}"
    params = {
        "api_key": api_key,
        "append_to_response": "external_ids,keywords"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"TMDB details error: {e}")
        return {}


def load_soundtrack_database(db_path: Optional[Path] = None) -> Dict:
    """
    Load local soundtrack database
    
    Args:
        db_path: Path to soundtrack JSON database
    
    Returns:
        Dict mapping (title, year) to soundtrack list
    """
    if db_path is None:
        db_path = Path(__file__).parent.parent / "config" / "bollywood_soundtracks.json"
    
    if not db_path.exists():
        return {}
    
    try:
        with open(db_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Failed to load soundtrack database: {e}")
        return {}


def get_soundtrack_for_movie(
    title: str,
    year: Optional[int],
    imdb_id: Optional[str] = None,
    soundtrack_db: Optional[Dict] = None,
    use_musicbrainz: bool = True,
    logger: Optional['PipelineLogger'] = None
) -> List[Dict[str, str]]:
    """
    Get soundtrack information for a movie using cascade fallback strategy
    
    Priority:
    1. MusicBrainz API (if enabled)
    2. Local database
    
    Args:
        title: Movie title
        year: Release year
        imdb_id: IMDb ID (if available)
        soundtrack_db: Preloaded soundtrack database
        use_musicbrainz: Whether to use MusicBrainz API
        logger: Optional logger instance
    
    Returns:
        List of soundtrack entries with title, artist, composer
    """
    # Try MusicBrainz first
    if use_musicbrainz and title:
        try:
            from scripts.musicbrainz_client import MusicBrainzClient
            
            if logger:
                logger.info(f"Querying MusicBrainz for: {title} ({year})")
            
            client = MusicBrainzClient(logger)
            mb_result = client.get_soundtrack(imdb_id=imdb_id, title=title, year=year)
            
            if mb_result and mb_result['found']:
                tracks = mb_result['tracks']
                if logger:
                    logger.info(f"✓ MusicBrainz: Found {len(tracks)} tracks")
                
                # Cache to local database for future use
                if soundtrack_db is not None:
                    _cache_to_local_db(title, year, imdb_id, tracks, soundtrack_db, logger)
                
                return tracks
            else:
                if logger:
                    logger.info("✗ MusicBrainz: No soundtrack found")
        except Exception as e:
            if logger:
                logger.warning(f"MusicBrainz error: {e}")
            # Continue to fallback
    
    # Fallback to local database
    if soundtrack_db is None:
        soundtrack_db = load_soundtrack_database()
    
    if not soundtrack_db:
        return []
    
    if logger:
        logger.info("Checking local database...")
    
    # Try exact title + year match first
    if year:
        key = f"{title} ({year})"
        if key in soundtrack_db:
            tracks = soundtrack_db[key].get("tracks", [])
            if logger and tracks:
                logger.info(f"✓ Local DB: Found {len(tracks)} tracks")
            return tracks
    
    # Try title only match
    if title in soundtrack_db:
        tracks = soundtrack_db[title].get("tracks", [])
        if logger and tracks:
            logger.info(f"✓ Local DB: Found {len(tracks)} tracks")
        return tracks
    
    # Try IMDb ID match
    if imdb_id:
        for movie_key, movie_data in soundtrack_db.items():
            if movie_data.get("imdb_id") == imdb_id:
                tracks = movie_data.get("tracks", [])
                if logger and tracks:
                    logger.info(f"✓ Local DB (IMDb match): Found {len(tracks)} tracks")
                return tracks
    
    # Try fuzzy title match (case-insensitive, punctuation-insensitive)
    title_normalized = title.lower().replace("...", "").replace(".", "").strip()
    for movie_key, movie_data in soundtrack_db.items():
        db_title = movie_data.get("title", movie_key)
        db_title_normalized = db_title.lower().replace("...", "").replace(".", "").strip()
        
        if title_normalized == db_title_normalized:
            tracks = movie_data.get("tracks", [])
            if logger and tracks:
                logger.info(f"✓ Local DB (fuzzy match): Found {len(tracks)} tracks")
            return tracks
    
    if logger:
        logger.info("✗ Local DB: No soundtrack found")
    
    return []


def _cache_to_local_db(
    title: str,
    year: Optional[int],
    imdb_id: Optional[str],
    tracks: List[Dict],
    soundtrack_db: Dict,
    logger: Optional['PipelineLogger'] = None
):
    """
    Cache MusicBrainz results to local database
    
    Args:
        title: Movie title
        year: Release year
        imdb_id: IMDb ID
        tracks: Track list
        soundtrack_db: Database dict
        logger: Optional logger
    """
    try:
        from datetime import datetime
        
        db_path = Path(__file__).parent.parent / "config" / "bollywood_soundtracks.json"
        
        # Create key
        key = f"{title} ({year})" if year else title
        
        # Add to database
        soundtrack_db[key] = {
            'title': title,
            'year': year,
            'imdb_id': imdb_id,
            'tracks': tracks,
            'source': 'musicbrainz',
            'cached_at': datetime.now().isoformat()
        }
        
        # Save to file
        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump(soundtrack_db, f, indent=2, ensure_ascii=False)
        
        if logger:
            logger.debug(f"Cached soundtrack to local DB: {key}")
            
    except Exception as e:
        if logger:
            logger.warning(f"Failed to cache soundtrack: {e}")


def enrich_from_tmdb(
    title: str,
    year: Optional[int],
    api_key: str,
    max_cast: int = 20,
    max_crew: int = 10,
    include_soundtrack: bool = True,
    use_musicbrainz: bool = True,
    use_cache: bool = True,
    logger: Optional['PipelineLogger'] = None
) -> TMDBMetadata:
    """
    Enrich movie metadata from TMDB with caching support

    Args:
        title: Movie title
        year: Release year (optional)
        api_key: TMDB API key
        max_cast: Maximum cast members to return
        max_crew: Maximum crew members to return
        include_soundtrack: Whether to include soundtrack data
        use_musicbrainz: Whether to use MusicBrainz for soundtrack
        use_cache: Whether to use cached data (default: True)
        logger: Optional logger instance

    Returns:
        TMDBMetadata with cast, crew, soundtrack, and genres
    """
    # Try cache first
    if use_cache:
        try:
            # Import here to avoid circular dependency
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from shared.tmdb_cache import TMDBCache
            
            cache = TMDBCache()
            
            # Do initial search to get TMDB ID for cache lookup
            movie = search_tmdb(title, year, api_key)
            if movie:
                tmdb_id = movie["id"]
                cached_data = cache.get(tmdb_id)
                
                if cached_data:
                    if logger:
                        age_days = cached_data.get('_cache', {}).get('age_days', 'unknown')
                        logger.info(f"Using cached TMDB data (age: {age_days} days)")
                    
                    # Convert cached dict back to TMDBMetadata
                    return TMDBMetadata(
                        title=cached_data.get('title', title),
                        year=cached_data.get('year', year),
                        cast=cached_data.get('cast', []),
                        crew=cached_data.get('crew', []),
                        soundtrack=cached_data.get('soundtrack', []),
                        genres=cached_data.get('genres', []),
                        imdb_id=cached_data.get('imdb_id'),
                        tmdb_id=cached_data.get('tmdb_id'),
                        found=cached_data.get('found', True)
                    )
        except Exception as e:
            if logger:
                logger.debug(f"Cache lookup failed: {e}")
            # Continue with API fetch
    
    # Search for movie (or use existing search from cache attempt)
    try:
        movie
    except NameError:
        movie = search_tmdb(title, year, api_key)

    if not movie:
        return TMDBMetadata(
            title=title,
            year=year,
            cast=[],
            crew=[],
            soundtrack=[],
            genres=[],
            imdb_id=None,
            tmdb_id=None,
            found=False
        )

    tmdb_id = movie["id"]
    tmdb_title = movie.get("title", title)
    release_date = movie.get("release_date", "")
    tmdb_year = int(release_date[:4]) if release_date else year

    # Get detailed movie information (includes external IDs and genres)
    details = get_movie_details(tmdb_id, api_key)
    
    # Extract genres
    genres_list = []
    for genre in details.get("genres", []):
        genre_name = genre.get("name")
        if genre_name:
            genres_list.append(genre_name)
    
    # Get IMDb ID
    external_ids = details.get("external_ids", {})
    imdb_id = external_ids.get("imdb_id")
    
    # Get credits
    credits = get_movie_credits(tmdb_id, api_key)

    # Extract cast names
    cast_list = []
    for person in credits.get("cast", [])[:max_cast]:
        name = person.get("name")
        if name:
            cast_list.append(name)

    # Extract crew names (focus on director, writer, producer, music director)
    crew_list = []
    important_jobs = ["Director", "Writer", "Screenplay", "Producer", "Music", "Original Music Composer"]

    for person in credits.get("crew", []):
        name = person.get("name")
        job = person.get("job", "")

        if name and job in important_jobs and name not in crew_list:
            crew_list.append(name)

            if len(crew_list) >= max_crew:
                break
    
    # Get soundtrack data (MusicBrainz -> Local DB fallback)
    soundtrack_list = []
    if include_soundtrack:
        soundtrack_list = get_soundtrack_for_movie(
            title=tmdb_title,
            year=tmdb_year,
            imdb_id=imdb_id,
            use_musicbrainz=use_musicbrainz,
            logger=logger
        )

    metadata = TMDBMetadata(
        title=tmdb_title,
        year=tmdb_year,
        cast=cast_list,
        crew=crew_list,
        soundtrack=soundtrack_list,
        genres=genres_list,
        imdb_id=imdb_id,
        tmdb_id=tmdb_id,
        found=True
    )
    
    # Cache the results
    if use_cache:
        try:
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from shared.tmdb_cache import TMDBCache
            
            cache = TMDBCache()
            cache_data = {
                'title': tmdb_title,
                'year': tmdb_year,
                'cast': cast_list,
                'crew': crew_list,
                'soundtrack': soundtrack_list,
                'genres': genres_list,
                'imdb_id': imdb_id,
                'tmdb_id': tmdb_id,
                'found': True
            }
            cache.set(tmdb_id, cache_data)
            
            if logger:
                logger.debug(f"Cached TMDB data for ID {tmdb_id}")
        except Exception as e:
            if logger:
                logger.debug(f"Cache save failed: {e}")
    
    return metadata


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
    
    # Fetch TMDB metadata (including soundtrack via MusicBrainz)
    logger.info("Fetching metadata from TMDB...")
    logger.debug(f"API Key: {'*' * (len(api_key) - 4)}{api_key[-4:]}")
    
    # Check if MusicBrainz is enabled
    use_musicbrainz = getattr(config, 'use_musicbrainz', True) if config else True
    
    metadata_obj = enrich_from_tmdb(
        title=title,
        year=year,
        api_key=api_key,
        include_soundtrack=True,
        use_musicbrainz=use_musicbrainz,
        logger=logger
    )
    
    # Convert to dict
    metadata = {
        'title': metadata_obj.title,
        'year': metadata_obj.year,
        'tmdb_id': metadata_obj.tmdb_id,
        'imdb_id': metadata_obj.imdb_id,
        'cast': metadata_obj.cast,
        'crew': metadata_obj.crew,
        'genres': metadata_obj.genres,
        'found': metadata_obj.found
    }
    
    # Save basic metadata
    metadata_path = stage_io.save_json(metadata, 'tmdb_data.json')
    logger.debug(f"Saved TMDB data: {metadata_path}")
    
    # Save enrichment data (includes soundtrack for song bias injection)
    enrichment = {
        'title': metadata_obj.title,
        'year': metadata_obj.year,
        'tmdb_id': metadata_obj.tmdb_id,
        'imdb_id': metadata_obj.imdb_id,
        'cast': metadata_obj.cast,
        'crew': metadata_obj.crew,
        'genres': metadata_obj.genres,
        'soundtrack': metadata_obj.soundtrack,
        'found': metadata_obj.found
    }
    enrichment_path = stage_io.save_json(enrichment, 'enrichment.json')
    logger.debug(f"Saved enrichment data: {enrichment_path}")
    
    if metadata_obj.found:
        logger.info(f"✓ TMDB metadata found (ID: {metadata_obj.tmdb_id})")
        logger.info(f"  Title: {metadata_obj.title}")
        logger.info(f"  Year: {metadata_obj.year}")
        if metadata_obj.imdb_id:
            logger.info(f"  IMDb ID: {metadata_obj.imdb_id}")
        if metadata_obj.genres:
            logger.info(f"  Genres: {', '.join(metadata_obj.genres)}")
        logger.info(f"  Cast: {len(metadata_obj.cast)} members")
        logger.debug(f"  Cast names: {', '.join(metadata_obj.cast[:5])}...")
        logger.info(f"  Crew: {len(metadata_obj.crew)} members")
        logger.debug(f"  Crew names: {', '.join(metadata_obj.crew[:5])}")
        
        if metadata_obj.soundtrack:
            logger.info(f"  Soundtrack: {len(metadata_obj.soundtrack)} tracks")
            logger.debug(f"  Track 1: {metadata_obj.soundtrack[0].get('title', 'Unknown')}")
        else:
            logger.info("  Soundtrack: Not available (add to config/bollywood_soundtracks.json)")
        
        stage_io.save_metadata({
            'status': 'completed',
            'tmdb_id': metadata_obj.tmdb_id,
            'imdb_id': metadata_obj.imdb_id,
            'cast_count': len(metadata_obj.cast),
            'crew_count': len(metadata_obj.crew),
            'soundtrack_count': len(metadata_obj.soundtrack),
            'genres': metadata_obj.genres
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
