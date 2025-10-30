#!/usr/bin/env python3
"""Stage 2: TMDB - Fetch movie metadata"""
import sys
import json
import re
import argparse
import os
from pathlib import Path

sys.path.insert(0, 'native/utils')
sys.path.insert(0, 'shared')

from native_logger import NativePipelineLogger
from manifest import StageManifest
from tmdb_fetcher import TMDBFetcher
from secrets import get_secrets_manager

def extract_title_year(filename):
    """Extract title and year from filename"""
    name = Path(filename).stem
    
    # Try different patterns
    patterns = [
        r'(.+?)\s*[(\[]\s*(\d{4})\s*[)\]]',  # Title (2020) or Title [2020]
        r'(.+?)\s+(\d{4})(?:\s|$)',           # Title 2020
        r'(.+)',                               # Just title
    ]
    
    for pattern in patterns:
        match = re.search(pattern, name)
        if match:
            title = match.group(1).strip()
            year = int(match.group(2)) if len(match.groups()) > 1 else None
            
            # Clean up title (remove common suffixes)
            title = re.sub(r'\s+(1080p|720p|BluRay|WEB-DL|HDTV|x264|x265|HEVC).*$', '', title, flags=re.IGNORECASE)
            title = title.replace('.', ' ').replace('_', ' ')
            title = re.sub(r'\s+', ' ', title).strip()
            
            return title, year
    
    return name, None

def fetch_tmdb_data(title, year, api_key, logger):
    """Fetch movie data from TMDB API"""
    import time
    start = time.time()
    
    # Initialize TMDB fetcher with API key
    fetcher = TMDBFetcher(api_key=api_key, logger=logger)
    
    # Search for movie
    logger.info(f"Searching TMDB for: {title}" + (f" ({year})" if year else ""))
    
    try:
        data = fetcher.search_movie(title, year)
        
        if not data:
            logger.warning("No data returned from TMDB")
            data = fetcher._get_fallback_data(title, year)
        
        duration = time.time() - start
        logger.log_processing(f"TMDB fetch completed", duration)
        
        # Log metrics
        logger.log_metric("Cast members", len(data.get('cast', [])))
        logger.log_metric("Directors", len(data.get('directors', [])))
        logger.log_metric("Genres", len(data.get('genres', [])))
        logger.log_metric("Keywords", len(data.get('keywords', [])))
        
        # Log key info
        if data.get('imdb_id'):
            logger.info(f"IMDB ID: {data['imdb_id']}")
        if data.get('runtime'):
            logger.info(f"Runtime: {data['runtime']} minutes")
        if data.get('vote_average'):
            logger.info(f"Rating: {data['vote_average']}/10 ({data.get('vote_count', 0)} votes)")
        
        return data
        
    except Exception as e:
        logger.error(f"Error fetching TMDB data: {e}")
        return fetcher._get_fallback_data(title, year)
    finally:
        fetcher.close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--movie-dir', required=True)
    args = parser.parse_args()
    
    movie_dir = Path(args.movie_dir)
    movie_name = movie_dir.name
    logger = NativePipelineLogger('tmdb', movie_name)
    
    try:
        logger.log_stage_start("Fetching movie metadata from TMDB")
        
        # Load secrets from config/secrets.json
        secrets_manager = get_secrets_manager()
        api_key = secrets_manager.get_tmdb_api_key()
        
        # Log secrets status
        secrets_summary = secrets_manager.summary()
        logger.debug(f"Secrets loaded: {secrets_summary}")
        
        if api_key and api_key.strip():
            logger.info(f"✓ TMDB API key loaded from secrets: {secrets_manager.mask_secret(api_key)}")
            logger.info("Will fetch real movie data from TMDB")
        else:
            logger.warning("No TMDB API key found in config/secrets.json or environment")
            logger.info("Will use fallback data (title and year only)")
            logger.info("To enable TMDB: Add 'tmdb_api_key' to config/secrets.json")
        
        with StageManifest('tmdb', movie_dir, logger.logger) as manifest:
            title, year = extract_title_year(args.input)
            logger.debug(f"Extracted from filename - Title: {title}, Year: {year}")
            
            data = fetch_tmdb_data(title, year, api_key, logger)
            
            metadata_dir = movie_dir / 'metadata'
            metadata_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created metadata directory: {metadata_dir}")
            
            output_file = metadata_dir / 'tmdb_data.json'
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.log_file_operation("Saved TMDB metadata", output_file, success=True)
            
            # Log data source
            data_source = data.get('data_source', 'unknown')
            if data_source == 'tmdb_api':
                logger.info(f"✓ Real TMDB data fetched successfully")
            else:
                logger.warning(f"Using {data_source} data")
            
            # Add useful info to manifest
            manifest.add_output('tmdb_data', output_file, 'TMDB movie data')
            manifest.add_metadata('title', data.get('title', title))
            manifest.add_metadata('year', data.get('year', year))
            manifest.add_metadata('imdb_id', data.get('imdb_id'))
            manifest.add_metadata('tmdb_id', data.get('id'))
            manifest.add_metadata('cast_count', len(data.get('cast', [])))
            manifest.add_metadata('data_source', data.get('data_source', 'tmdb_api'))
        
        logger.log_stage_end(success=True)
        
    except Exception as e:
        logger.error(f"Stage failed with error: {e}")
        logger.log_stage_end(success=False)
        raise

if __name__ == '__main__':
    main()
