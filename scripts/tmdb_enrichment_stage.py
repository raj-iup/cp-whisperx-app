#!/usr/bin/env python3
"""
TMDB Enrichment Stage - Phase 1 Integration

Fetches movie metadata from TMDB and generates glossaries for
use in ASR biasing and translation stages.

Stage: 03_tmdb (runs after demux, before ASR)

Input:
  - Movie title and year from job config or filename
  
Output:
  - enrichment.json: Full TMDB metadata
  - glossary_asr.json: Terms for ASR biasing
  - glossary_translation.json: Terms for translation preservation
  - glossary.yaml: Human-readable glossary

Usage:
  python scripts/tmdb_enrichment_stage.py \
      --job-dir out/20250124_0001_movie \
      --title "Movie Title" \
      --year 2008
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.logger import PipelineLogger
from shared.stage_utils import StageIO, get_stage_logger
from shared.config import load_config
from shared.tmdb_client import TMDBClient, load_api_key
from shared.glossary_generator import GlossaryGenerator


class TMDBEnrichmentStage:
    """TMDB enrichment pipeline stage"""
    
    def __init__(
        self,
        job_dir: Optional[Path] = None,
        stage_io: Optional[StageIO] = None,
        title: Optional[str] = None,
        year: Optional[int] = None,
        logger: Optional[PipelineLogger] = None
    ):
        """
        Initialize TMDB enrichment stage
        
        Args:
            job_dir: Job output directory (legacy, use stage_io instead)
            stage_io: StageIO instance (preferred)
            title: Movie title (optional, can auto-detect)
            year: Release year (optional)
            logger: Logger instance (optional)
        """
        # Support both legacy job_dir and new StageIO
        if stage_io:
            self.stage_io = stage_io
            self.job_dir = stage_io.output_base
            self.output_dir = stage_io.stage_dir
        elif job_dir:
            self.job_dir = Path(job_dir)
            self.output_dir = self.job_dir / "02_tmdb"
            self.output_dir.mkdir(parents=True, exist_ok=True)
            self.stage_io = None
        else:
            raise ValueError("Either job_dir or stage_io must be provided")
        
        self.title = title
        self.year = year
        
        # Setup logger
        if logger:
            self.logger = logger
        elif self.stage_io:
            self.logger = get_stage_logger("tmdb_enrichment", stage_io=self.stage_io)
        else:
            self.logger = self._create_logger()
        
        # Initialize TMDB client
        self.api_key = load_api_key()
        if not self.api_key:
            self.logger.warning("TMDB API key not found - stage will be skipped")
            self.client = None
        else:
            self.client = TMDBClient(self.api_key, logger=self.logger)
    
    def _create_logger(self) -> PipelineLogger:
        """Create default logger"""
        return PipelineLogger(
            module_name="tmdb_enrichment",
            log_file=self.job_dir / "logs" / "02_tmdb.log"
        )
    
    def auto_detect_title(self) -> Optional[str]:
        """
        Auto-detect movie title from filename or job config
        
        Returns:
            Movie title or None
        """
        # Try to get from job config
        config_file = self.job_dir / "job_config.json"
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    if 'movie_title' in config:
                        return config['movie_title']
                    if 'title' in config:
                        return config['title']
            except Exception as e:
                self.logger.debug(f"Could not read job config: {e}")
        
        # Try to parse from input filename
        demux_dir = self.job_dir / "01_demux"
        if demux_dir.exists():
            audio_files = list(demux_dir.glob("*.wav"))
            if audio_files:
                filename = audio_files[0].stem
                # Remove timestamps and common suffixes
                title = filename.replace('_audio', '').replace('-', ' ')
                return title
        
        return None
    
    def run(self) -> bool:
        """
        Execute TMDB enrichment stage
        
        Returns:
            True if successful, False otherwise
        """
        self.logger.info("=" * 60)
        self.logger.info("STAGE: TMDB Enrichment")
        self.logger.info("=" * 60)
        
        # Check if API key is available
        if not self.client:
            self.logger.warning("TMDB API key not configured")
            self.logger.info("Skipping TMDB enrichment stage")
            self._create_empty_outputs()
            return True  # Not a failure, just skipped
        
        # Auto-detect title if not provided
        if not self.title:
            self.title = self.auto_detect_title()
            if self.title:
                self.logger.info(f"Auto-detected title: {self.title}")
        
        if not self.title:
            self.logger.warning("No movie title provided or detected")
            self.logger.info("Skipping TMDB enrichment stage")
            self._create_empty_outputs()
            return True
        
        try:
            # Search for movie
            self.logger.info(f"Searching TMDB for: {self.title}")
            if self.year:
                self.logger.info(f"  Year filter: {self.year}")
            
            movie = self.client.search_movie(self.title, year=self.year)
            
            if not movie:
                self.logger.warning(f"Movie not found on TMDB: {self.title}")
                self._create_empty_outputs()
                return True
            
            self.logger.info(f"✓ Found: {movie['title']} ({movie['year']})")
            self.logger.info(f"  TMDB ID: {movie['id']}")
            
            # Fetch detailed metadata
            self.logger.info("Fetching detailed metadata...")
            metadata = self.client.get_movie_metadata(movie['id'])
            
            if not metadata:
                self.logger.error("Failed to fetch metadata")
                return False
            
            self.logger.info(f"✓ Metadata retrieved:")
            self.logger.info(f"  Cast: {len(metadata['cast'])} members")
            self.logger.info(f"  Crew: {len(metadata['crew'])} members")
            self.logger.info(f"  Genres: {', '.join(metadata['genres'])}")
            
            # Save enrichment data
            self._save_enrichment(metadata)
            
            # Generate glossaries
            self._generate_glossaries(metadata)
            
            self.logger.info("=" * 60)
            self.logger.info("✓ TMDB Enrichment Complete")
            self.logger.info("=" * 60)
            
            return True
            
        except Exception as e:
            self.logger.error(f"TMDB enrichment failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _save_enrichment(self, metadata: Dict[str, Any]):
        """Save enrichment data to JSON"""
        enrichment_file = self.output_dir / "enrichment.json"
        
        # Prepare enrichment data
        enrichment = {
            'tmdb_id': metadata['id'],
            'imdb_id': metadata.get('imdb_id'),
            'title': metadata['title'],
            'original_title': metadata.get('original_title'),
            'year': metadata.get('year'),
            'overview': metadata.get('overview', ''),
            'genres': metadata.get('genres', []),
            'runtime': metadata.get('runtime'),
            'cast': metadata.get('cast', []),
            'crew': metadata.get('crew', []),
            'vote_average': metadata.get('vote_average'),
            'popularity': metadata.get('popularity'),
            'found': True,
            'fetched_at': datetime.now().isoformat()
        }
        
        with open(enrichment_file, 'w', encoding='utf-8') as f:
            json.dump(enrichment, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"✓ Saved enrichment: {enrichment_file.name}")
    
    def _generate_glossaries(self, metadata: Dict[str, Any]):
        """Generate glossaries from metadata"""
        self.logger.info("Generating glossaries...")
        
        generator = GlossaryGenerator(metadata, logger=self.logger)
        
        # Generate ASR glossary (flat list)
        asr_terms = generator.generate_for_asr()
        asr_file = self.output_dir / "glossary_asr.json"
        with open(asr_file, 'w', encoding='utf-8') as f:
            json.dump({'terms': asr_terms}, f, indent=2, ensure_ascii=False)
        self.logger.info(f"✓ ASR glossary: {len(asr_terms)} terms")
        
        # Generate translation glossary (mappings)
        trans_glossary = generator.generate_for_translation()
        trans_file = self.output_dir / "glossary_translation.json"
        with open(trans_file, 'w', encoding='utf-8') as f:
            json.dump(trans_glossary, f, indent=2, ensure_ascii=False)
        self.logger.info(f"✓ Translation glossary: {len(trans_glossary)} mappings")
        
        # Generate full glossary (YAML for human readability)
        glossary = generator.generate()
        yaml_file = self.output_dir / "glossary.yaml"
        generator.save_yaml(yaml_file, glossary)
        self.logger.info(f"✓ Full glossary: {len(glossary)} entries")
    
    def _create_empty_outputs(self):
        """Create empty output files when stage is skipped"""
        # Create minimal enrichment file
        enrichment = {
            'found': False,
            'title': self.title or 'unknown',
            'year': self.year,
            'cast': [],
            'crew': [],
            'soundtrack': [],
            'genres': [],
            'skipped_at': datetime.now().isoformat()
        }
        
        enrichment_file = self.output_dir / "enrichment.json"
        with open(enrichment_file, 'w', encoding='utf-8') as f:
            json.dump(enrichment, f, indent=2)
        
        # Create empty glossaries
        with open(self.output_dir / "glossary_asr.json", 'w') as f:
            json.dump({'terms': []}, f, indent=2)
        
        with open(self.output_dir / "glossary_translation.json", 'w') as f:
            json.dump({}, f, indent=2)
        
        self.logger.info("Created empty output files (stage skipped)")


def main():
    """Main entry point - supports both pipeline and CLI modes"""
    parser = argparse.ArgumentParser(
        description='TMDB Enrichment Stage - Fetch movie metadata and generate glossaries'
    )
    
    parser.add_argument(
        '--job-dir',
        type=Path,
        help='Job output directory (legacy mode, optional if using StageIO)'
    )
    
    parser.add_argument(
        '--title',
        type=str,
        help='Movie title (optional, will auto-detect if not provided)'
    )
    
    parser.add_argument(
        '--year',
        type=int,
        help='Release year (optional, helps with matching)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    parser.add_argument(
        '--pipeline-mode',
        action='store_true',
        help='Use StageIO for paths (automatic if no job-dir provided)'
    )
    
    args = parser.parse_args()
    
    # Determine mode
    use_pipeline = args.pipeline_mode or not args.job_dir
    
    try:
        if use_pipeline:
            # Pipeline mode: Use StageIO
            stage_io = StageIO("tmdb_enrichment")
            
            # Try to load config for title/year
            try:
                config = load_config()
                title = args.title or getattr(config, 'film_title', None)
                year = args.year or getattr(config, 'film_year', None)
            except Exception:
                title = args.title
                year = args.year
            
            # Create stage with StageIO
            stage = TMDBEnrichmentStage(
                stage_io=stage_io,
                title=title,
                year=year
            )
        else:
            # Legacy mode: Use job_dir
            stage = TMDBEnrichmentStage(
                job_dir=args.job_dir,
                title=args.title,
                year=args.year
            )
        
        success = stage.run()
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n✗ TMDB enrichment interrupted by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"\n✗ TMDB enrichment failed: {e}", file=sys.stderr)
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
