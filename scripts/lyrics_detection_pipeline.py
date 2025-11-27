#!/usr/bin/env python3
"""
Lyrics Detection Pipeline Stage

Detects song/musical segments in audio for improved transcription.
Integrates with pipeline orchestrator following developer standards.

Usage:
    Called by run-pipeline.py via environment variables:
    - AUDIO_INPUT: Path to audio file
    - LYRICS_OUTPUT_DIR: Where to save results
    - CONFIG_PATH: Job configuration file
    - LYRICS_DETECTION_THRESHOLD: Detection threshold (0.0-1.0)
    - LYRICS_MIN_DURATION: Minimum song segment duration (seconds)
"""

import sys
import json
import os
from pathlib import Path
from typing import List, Dict

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.logger import PipelineLogger
from shared.config import Config, load_config

# Import core lyrics detection
from scripts.lyrics_detection_core import LyricsDetector


def main():
    """Main entry point for lyrics detection pipeline stage"""
    
    # Setup logger
    log_dir = Path(os.environ.get("LYRICS_OUTPUT_DIR", "out"))
    log_file = log_dir.parent / "logs" / "lyrics_detection.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    logger = PipelineLogger("lyrics_detection", log_file)
    
    logger.info("=" * 70)
    logger.info("LYRICS DETECTION STAGE - Song Segment Identification")
    logger.info("=" * 70)
    
    # Get configuration from environment
    audio_file = Path(os.environ.get("AUDIO_INPUT", ""))
    output_dir = Path(os.environ.get("LYRICS_OUTPUT_DIR", ""))
    segments_file = Path(os.environ.get("SEGMENTS_INPUT", ""))
    
    logger.info(f"📥 Input audio: {audio_file}")
    logger.info(f"📥 Input segments: {segments_file}")
    logger.info(f"📤 Output directory: {output_dir}")
    
    if not audio_file.exists():
        logger.error(f"Audio file not found: {audio_file}")
        return 1
    
    if not segments_file.exists():
        logger.warning(f"Segments file not found: {segments_file}")
        logger.warning("Lyrics detection requires ASR output - skipping")
        return 0
    
    # Load configuration using the correct Config class (simple loader)
    config = Config(PROJECT_ROOT)
    
    # Get detection parameters
    threshold = float(os.environ.get("LYRICS_DETECTION_THRESHOLD", 
                                     config.get("LYRICS_DETECTION_THRESHOLD", "0.5")))
    min_duration = float(os.environ.get("LYRICS_MIN_DURATION",
                                       config.get("LYRICS_MIN_DURATION", "30.0")))
    device = os.environ.get("LYRICS_DETECTION_DEVICE",
                           config.get("LYRICS_DETECTION_DEVICE", "cpu"))
    
    logger.info(f"Configuration:")
    logger.info(f"  Threshold: {threshold}")
    logger.info(f"  Min duration: {min_duration}s")
    logger.info(f"  Device: {device}")
    
    # Initialize lyrics detector
    detector = LyricsDetector(
        threshold=threshold,
        min_duration=min_duration,
        device=device,
        logger=logger
    )
    
    # Method 1: Audio feature analysis
    logger.info("Method 1: Analyzing audio features...")
    audio_lyrics = []
    
    try:
        # For audio analysis, we need some segments to analyze
        # Create basic segments from the full audio duration
        import librosa
        y, sr = librosa.load(str(audio_file), sr=16000, duration=None)
        duration = librosa.get_duration(y=y, sr=sr)
        
        logger.info(f"  Audio duration: {duration:.1f}s")
        
        # Create segments in 30-second chunks for analysis
        chunk_size = 30.0
        temp_segments = []
        for start in range(0, int(duration), int(chunk_size)):
            end = min(start + chunk_size, duration)
            temp_segments.append({
                'start': float(start),
                'end': float(end)
            })
        
        logger.info(f"  Analyzing {len(temp_segments)} audio chunks...")
        audio_lyrics = detector.detect_from_audio_features(audio_file, temp_segments)
        logger.info(f"  Found {len(audio_lyrics)} potential lyric segments from audio analysis")
        
    except ImportError:
        logger.warning("  librosa not available, skipping audio feature analysis")
    except Exception as e:
        logger.warning(f"  Audio analysis failed: {e}")
    
    # Method 2: TMDB soundtrack matching (if available)
    logger.info("Method 2: Checking TMDB soundtrack data...")
    tmdb_lyrics = []
    
    tmdb_enrichment = output_dir.parent / "tmdb" / "enrichment.json"
    if not tmdb_enrichment.exists():
        tmdb_enrichment = output_dir.parent / "02_tmdb" / "enrichment.json"
    
    if tmdb_enrichment.exists():
        try:
            with open(tmdb_enrichment, 'r', encoding='utf-8') as f:
                enrichment = json.load(f)
            
            soundtrack_data = enrichment.get('soundtrack', [])
            if soundtrack_data:
                logger.info(f"  Found {len(soundtrack_data)} soundtrack entries")
                
                # Use soundtrack durations to identify potential lyrics segments
                for song in soundtrack_data:
                    duration = song.get('duration_seconds', 0)
                    if duration >= min_duration:
                        # We don't have exact timestamps, but we know songs exist
                        # This metadata can be used by PyAnnote/WhisperX for bias
                        logger.info(f"  Song: '{song.get('title', 'Unknown')}' ({duration}s)")
                        tmdb_lyrics.append({
                            'title': song.get('title', 'Unknown'),
                            'duration': duration,
                            'confidence': 0.8,  # High confidence from TMDB
                            'source': 'tmdb'
                        })
            else:
                logger.info("  No soundtrack data in TMDB enrichment")
        except Exception as e:
            logger.warning(f"  Failed to load TMDB data: {e}")
    else:
        logger.info("  No TMDB enrichment available")
    
    # Merge results
    all_lyrics = audio_lyrics + tmdb_lyrics
    
    if all_lyrics:
        logger.info(f"✓ Total lyrics segments detected: {len(all_lyrics)}")
        
        # Save metadata
        metadata = {
            'lyric_segments': all_lyrics,
            'audio_file': str(audio_file),
            'threshold': threshold,
            'min_duration': min_duration,
            'detection_methods': []
        }
        
        if audio_lyrics:
            metadata['detection_methods'].append('audio_features')
        if tmdb_lyrics:
            metadata['detection_methods'].append('tmdb_soundtrack')
        
        output_file = output_dir / "lyrics_metadata.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✓ Saved lyrics metadata: {output_file}")
        logger.info("=" * 70)
        return 0
    else:
        logger.info("No song segments detected - content appears to be all dialog")
        logger.info("=" * 70)
        return 0


if __name__ == "__main__":
    sys.exit(main())
