#!/usr/bin/env python3
"""Stage 6: Pyannote Diarization - Speaker Identification"""
import sys
import json
import argparse
import os
from pathlib import Path

sys.path.insert(0, 'native/utils')
from device_manager import get_device
from native_logger import NativePipelineLogger
from manifest import StageManifest
from pyannote_diarization_wrapper import PyannoteDiarization


def load_secrets(secrets_path: Path = None) -> dict:
    """Load secrets from config/secrets.json."""
    if secrets_path is None:
        secrets_path = Path("config/secrets.json")
    
    if not secrets_path.exists():
        raise FileNotFoundError(f"Secrets file not found: {secrets_path}")
    
    with open(secrets_path, 'r') as f:
        secrets = json.load(f)
    
    return secrets


def load_env_config() -> dict:
    """Load configuration from environment variables."""
    return {
        'min_speakers': int(os.getenv('DIARIZATION_MIN_SPEAKERS', '1')) if os.getenv('DIARIZATION_MIN_SPEAKERS') else None,
        'max_speakers': int(os.getenv('DIARIZATION_MAX_SPEAKERS', '10')) if os.getenv('DIARIZATION_MAX_SPEAKERS') else None,
        'model_name': os.getenv('DIARIZATION_MODEL', 'pyannote/speaker-diarization-3.1'),
        'device': os.getenv('DIARIZATION_DEVICE', 'cpu'),
        'speaker_map': os.getenv('SPEAKER_MAP', ''),
        'auto_speaker_mapping': os.getenv('DIARIZATION_AUTO_SPEAKER_MAPPING', 'true').lower() == 'true'
    }


def load_tmdb_speaker_names(movie_dir: Path, logger, max_speakers: int = 10) -> Optional[dict]:
    """
    Load speaker names from TMDB metadata for auto-mapping.
    
    Args:
        movie_dir: Movie output directory
        logger: Logger instance
        max_speakers: Maximum number of speakers to extract from cast
    
    Returns:
        Dictionary mapping SPEAKER_XX to character names, or None
    """
    tmdb_file = movie_dir / 'metadata' / 'tmdb_data.json'
    if not tmdb_file.exists():
        logger.warning(f"TMDB metadata not found: {tmdb_file}")
        return None
    
    try:
        with open(tmdb_file, 'r', encoding='utf-8') as f:
            tmdb_data = json.load(f)
        
        cast = tmdb_data.get('cast', [])
        if not cast:
            logger.warning("No cast information in TMDB data")
            return None
        
        # Extract top N character names based on cast order
        character_names = []
        for actor in sorted(cast, key=lambda x: x.get('order', 999))[:max_speakers]:
            character = actor.get('character', '')
            if character:
                # Clean up character name (remove extra info in parentheses)
                character = character.split('(')[0].strip()
                character_names.append(character)
        
        if not character_names:
            logger.warning("No character names found in cast")
            return None
        
        logger.info(f"Loaded {len(character_names)} character names from TMDB")
        logger.debug(f"Characters: {', '.join(character_names)}")
        
        return character_names
    
    except Exception as e:
        logger.warning(f"Failed to load TMDB metadata: {e}")
        return None


def run_diarization(
    audio_file: Path,
    device: str,
    logger,
    config: dict = None
):
    """
    Run Pyannote diarization for speaker identification.
    
    Args:
        audio_file: Path to audio file
        device: Device to run on
        logger: Logger instance
        config: Configuration dict with diarization parameters
        
    Returns:
        Tuple of (speaker_segments, statistics, character_names)
    """
    # Default configuration
    default_config = {
        'min_speakers': None,
        'max_speakers': None,
        'model_name': 'pyannote/speaker-diarization-3.1',
        'speaker_map': '',
        'auto_speaker_mapping': True
    }
    
    if config:
        default_config.update(config)
    
    logger.info(f"Running Pyannote diarization on {device}")
    logger.info(f"Model: {default_config['model_name']}")
    logger.debug(f"Configuration: {default_config}")
    
    # Load secrets for HF token
    try:
        secrets = load_secrets()
        hf_token = secrets.get('hf_token') or secrets.get('pyannote_token')
        if not hf_token:
            logger.error("HuggingFace token not found in secrets.json")
            raise ValueError("HuggingFace token required for Pyannote diarization")
    except Exception as e:
        logger.error(f"Failed to load secrets: {e}")
        raise
    
    # Initialize Pyannote Diarization
    diarization = PyannoteDiarization(
        hf_token=hf_token, 
        device=device,
        model_name=default_config['model_name'],
        logger=logger
    )
    
    # Load model
    if not diarization.load_model():
        raise RuntimeError("Failed to load Pyannote diarization model")
    
    # Run diarization
    speaker_segments = diarization.diarize(
        audio_path=audio_file,
        min_speakers=default_config['min_speakers'],
        max_speakers=default_config['max_speakers']
    )
    
    # Apply speaker map if provided
    speaker_map = None
    if default_config['speaker_map']:
        try:
            speaker_map = json.loads(default_config['speaker_map']) if default_config['speaker_map'].startswith('{') else None
            if speaker_map:
                logger.info("Applying speaker name mapping...")
                for seg in speaker_segments:
                    if seg["speaker"] in speaker_map:
                        seg["speaker_original"] = seg["speaker"]
                        seg["speaker"] = speaker_map[seg["speaker"]]
        except Exception as e:
            logger.warning(f"Could not parse speaker map: {e}")
    
    # Calculate statistics
    num_speakers = len(set(seg['speaker'] for seg in speaker_segments))
    total_duration = max(seg['end'] for seg in speaker_segments) if speaker_segments else 0
    
    stats = {
        'num_speakers': num_speakers,
        'total_segments': len(speaker_segments),
        'total_duration': total_duration,
        'device': device,
        'model': default_config['model_name'],
        'speaker_map_applied': bool(speaker_map),
        'auto_speaker_mapping_enabled': default_config['auto_speaker_mapping']
    }
    
    logger.info(f"Diarization complete: {len(speaker_segments)} speaker segments")
    logger.info(f"Identified {num_speakers} unique speakers")
    
    return speaker_segments, stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, help='Input video file')
    parser.add_argument('--movie-dir', required=True, help='Movie output directory')
    args = parser.parse_args()
    
    movie_dir = Path(args.movie_dir)
    movie_name = movie_dir.name
    logger = NativePipelineLogger('diarization', movie_name)
    
    try:
        logger.log_stage_start("Pyannote Diarization - Speaker identification")
        
        # Load configuration from environment
        env_config = load_env_config()
        logger.info(f"Configuration: min_speakers={env_config['min_speakers']}, "
                   f"max_speakers={env_config['max_speakers']}, "
                   f"model={env_config['model_name']}")
        
        # Get device - use env config if specified, otherwise detect
        if env_config['device'].upper() not in ['CPU', 'MPS', 'CUDA']:
            device = get_device(prefer_mps=False, stage_name='diarization')
        else:
            device = env_config['device'].lower()
        
        logger.log_model_load("Pyannote Diarization", device)
        
        import time
        start = time.time()
        
        with StageManifest('diarization', movie_dir, logger.logger) as manifest:
            # Get paths
            audio_file = movie_dir / 'audio' / 'audio.wav'
            
            if not audio_file.exists():
                raise FileNotFoundError(f"Audio file not found: {audio_file}")
            
            logger.debug(f"Audio file: {audio_file}")
            
            # Load TMDB character names for auto-mapping if enabled
            character_names = None
            if env_config.get('auto_speaker_mapping', True):
                character_names = load_tmdb_speaker_names(
                    movie_dir, 
                    logger, 
                    max_speakers=env_config.get('max_speakers') or 10
                )
                if character_names:
                    logger.info(f"Auto speaker mapping enabled: {len(character_names)} character names loaded")
            
            # Run Pyannote diarization with configuration
            speaker_segments, stats = run_diarization(
                audio_file=audio_file,
                device=device,
                logger=logger,
                config=env_config
            )
            
            # Apply auto speaker mapping if available and no manual map provided
            if character_names and not env_config['speaker_map']:
                logger.info("Applying auto speaker mapping from TMDB cast...")
                speaker_ids = sorted(set(seg['speaker'] for seg in speaker_segments))
                
                # Map SPEAKER_XX to character names
                for i, speaker_id in enumerate(speaker_ids):
                    if i < len(character_names):
                        character_name = character_names[i]
                        for seg in speaker_segments:
                            if seg['speaker'] == speaker_id:
                                seg['speaker_original'] = speaker_id
                                seg['speaker'] = character_name
                        logger.info(f"Mapped {speaker_id} → {character_name}")
                
                stats['tmdb_speaker_mapping'] = True
                stats['character_names'] = character_names[:len(speaker_ids)]
            
            duration = time.time() - start
            
            # Log results
            logger.log_processing("Diarization complete", duration)
            logger.log_metric("Speaker segments", len(speaker_segments))
            logger.log_metric("Unique speakers", stats['num_speakers'])
            logger.log_metric("Total duration", f"{stats['total_duration']:.2f}", "seconds")
            
            # Create output directory
            diar_dir = movie_dir / 'diarization'
            diar_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Diarization directory: {diar_dir}")
            
            # Save speaker segments
            output_file = diar_dir / 'speaker_segments.json'
            output_data = {
                'speaker_segments': speaker_segments,
                'statistics': stats,
                'config': {
                    'min_speakers': env_config['min_speakers'],
                    'max_speakers': env_config['max_speakers'],
                    'model': env_config['model_name'],
                    'device': device,
                    'speaker_map': env_config['speaker_map'],
                    'method': 'pyannote_diarization'
                }
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2)
            
            logger.log_file_operation("Saved diarization segments", output_file, success=True)
            
            # Add to manifest
            manifest.add_output('segments', output_file, 'Pyannote diarization speaker segments')
            manifest.add_metadata('device', device)
            manifest.add_metadata('num_speakers', stats['num_speakers'])
            manifest.add_metadata('total_segments', len(speaker_segments))
            manifest.add_metadata('model', env_config['model_name'])
            manifest.add_metadata('method', 'pyannote_diarization')
        
        logger.log_stage_end(success=True)
        
    except Exception as e:
        logger.error(f"Stage failed with error: {e}")
        logger.log_stage_end(success=False)
        raise


if __name__ == '__main__':
    main()
