#!/usr/bin/env python3
"""
Lyrics Detection stage: Detect and handle lyrics using multiple methods

Implements proper lyrics detection using:
1. Audio feature analysis (tempo, rhythm, spectral features)
2. Repetition detection in transcripts
3. Pattern matching (short lines, poetic structure)
"""
import sys
import json
from pathlib import Path
from typing import List, Dict, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Add project root
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.logger import PipelineLogger
from shared.stage_utils import StageIO
from shared.config import load_config
from lyrics_detection_core import LyricsDetector


def main():
    """Main entry point for lyrics detection stage"""
    
    # Setup stage I/O
    stage_io = StageIO("lyrics_detection")
    
    # Setup logger
    log_file = stage_io.get_log_path()
    logger = PipelineLogger("lyrics_detection", log_file)
    
    logger.info("=" * 70)
    logger.info("LYRICS DETECTION STAGE - Song Segment Identification")
    logger.info("=" * 70)
    logger.info(f"Output base: {stage_io.output_base}")
    logger.info(f"Stage directory: {stage_io.stage_dir}")
    
    # Load configuration
    config_path = stage_io.output_base / f".{stage_io.output_base.name}.env"
    if not config_path.exists():
        config_path = Path("config/.env.pipeline")
    
    logger.info(f"Loading config from: {config_path}")
    config = load_config(config_path)
    
    # Check if lyrics detection is enabled
    lyrics_detection_enabled = config.get('LYRICS_DETECTION_ENABLED', 'true').lower() == 'true'
    if not lyrics_detection_enabled:
        logger.info("Lyrics detection is disabled - skipping")
        # Copy segments as-is
        segments = stage_io.load_json("segments.json", from_stage="song_bias_injection")
        stage_io.save_json(segments, "segments.json")
        logger.info("=" * 70)
        return 0
    
    # Load segments from previous stage
    logger.info("Loading segments from song bias injection stage...")
    try:
        data = stage_io.load_json("segments.json", from_stage="song_bias_injection")
    except Exception as e:
        logger.error(f"Failed to load segments: {e}")
        return 1
    
    # Extract segments
    if isinstance(data, dict):
        segments = data.get('segments', [])
        metadata = {k: v for k, v in data.items() if k != 'segments'}
    else:
        segments = data
        metadata = {}
    
    logger.info(f"Loaded {len(segments)} segments")
    
    if not segments:
        logger.warning("No segments found")
        stage_io.save_json(data, "segments.json")
        logger.info("=" * 70)
        return 0
    
    # Initialize lyrics detector
    device = config.get('DEVICE', 'cpu')
    threshold = float(config.get('LYRICS_DETECTION_THRESHOLD', '0.5'))
    min_duration = float(config.get('LYRICS_MIN_DURATION', '30.0'))
    
    detector = LyricsDetector(
        threshold=threshold,
        min_duration=min_duration,
        device=device,
        logger=logger
    )
    
    # Method 1: Audio feature analysis (if audio file available)
    audio_lyrics = []
    audio_file = stage_io.output_base / "01_demux" / "audio.wav"
    
    if audio_file.exists():
        logger.info("Method 1: Analyzing audio features...")
        try:
            audio_lyrics = detector.detect_from_audio_features(audio_file, segments)
            logger.info(f"  Found {len(audio_lyrics)} lyric segments from audio analysis")
        except Exception as e:
            logger.warning(f"  Audio analysis failed: {e}")
    else:
        logger.warning("Audio file not found, skipping audio feature analysis")
    
    # Method 2: Transcript pattern analysis (repetition detection)
    logger.info("Method 2: Analyzing transcript patterns...")
    try:
        transcript_lyrics = detector.detect_from_transcript_patterns(segments)
        logger.info(f"  Found {len(transcript_lyrics)} lyric segments from transcript patterns")
    except Exception as e:
        logger.warning(f"  Transcript analysis failed: {e}")
        transcript_lyrics = []
    
    # Method 3: Soundtrack duration matching (NEW)
    soundtrack_lyrics = []
    tmdb_enrichment = stage_io.output_base / "02_tmdb" / "enrichment.json"
    
    if tmdb_enrichment.exists():
        try:
            logger.info("Method 3: Loading soundtrack data from TMDB enrichment...")
            with open(tmdb_enrichment, 'r', encoding='utf-8') as f:
                enrichment = json.load(f)
            
            soundtrack_data = enrichment.get('soundtrack', [])
            
            if soundtrack_data:
                logger.info(f"  Loaded {len(soundtrack_data)} songs from soundtrack")
                soundtrack_lyrics = detector.detect_from_soundtrack_durations(
                    segments,
                    soundtrack_data
                )
                logger.info(f"  Found {len(soundtrack_lyrics)} lyric segments from soundtrack matching")
            else:
                logger.info("  No soundtrack data available in enrichment")
        except Exception as e:
            logger.warning(f"  Failed to load soundtrack data: {e}")
    else:
        logger.info("Method 3: No TMDB enrichment file found, skipping soundtrack matching")
    
    # Merge detections (now includes soundtrack detections)
    logger.info("Merging detection results...")
    all_lyrics = detector.merge_detections(audio_lyrics, transcript_lyrics, soundtrack_lyrics)
    logger.info(f"✓ Total unique lyric segments detected: {len(all_lyrics)}")
    
    # Log detection method breakdown
    methods_count = {}
    for lyric in all_lyrics:
        method = lyric.get('detection_method', 'unknown')
        methods_count[method] = methods_count.get(method, 0) + 1
    
    if methods_count:
        logger.info("Detection method breakdown:")
        for method, count in methods_count.items():
            logger.info(f"  {method}: {count} segments")
    
    # Mark segments with lyrics flag
    logger.info("Annotating segments with lyrics flags...")
    for seg in segments:
        seg_start = seg.get('start', 0)
        seg_end = seg.get('end', 0)
        
        # Check if segment overlaps with any detected lyric segment
        is_lyrics = False
        max_confidence = 0.0
        matched_song = None
        matched_artist = None
        
        for lyric_seg in all_lyrics:
            lyric_start = lyric_seg.get('start', 0)
            lyric_end = lyric_seg.get('end', 0)
            
            # Check for overlap
            if not (seg_end < lyric_start or seg_start > lyric_end):
                is_lyrics = True
                max_confidence = max(max_confidence, lyric_seg.get('confidence', 0.0))
                
                # Capture song metadata if available
                if 'matched_song' in lyric_seg and not matched_song:
                    matched_song = lyric_seg['matched_song']
                    matched_artist = lyric_seg.get('matched_artist', '')
        
        seg['is_lyrics'] = is_lyrics
        if is_lyrics:
            seg['lyrics_confidence'] = max_confidence
            if matched_song:
                seg['song_title'] = matched_song
                seg['song_artist'] = matched_artist
        
        seg['is_lyrics'] = is_lyrics
        if is_lyrics:
            seg['lyrics_confidence'] = max_confidence
    
    # Count lyric vs dialogue segments
    lyric_count = sum(1 for s in segments if s.get('is_lyrics', False))
    dialogue_count = len(segments) - lyric_count
    
    logger.info(f"Segment breakdown:")
    logger.info(f"  Lyrics: {lyric_count} segments")
    logger.info(f"  Dialogue: {dialogue_count} segments")
    
    # Prepare output
    output_data = metadata.copy() if metadata else {}
    output_data['segments'] = segments
    output_data['lyrics_detected'] = True
    output_data['lyrics_detection_method'] = 'audio+transcript'
    output_data['total_lyric_segments'] = lyric_count
    output_data['total_dialogue_segments'] = dialogue_count
    
    # Save annotated segments
    stage_io.save_json(output_data, "segments.json")
    
    # Save detected lyric regions for reference
    stage_io.save_json(all_lyrics, "detected_lyric_regions.json")
    
    # Save metadata
    save_metadata = {
        "status": "completed",
        "lyric_segments_detected": len(all_lyrics),
        "lyric_segments_annotated": lyric_count,
        "dialogue_segments": dialogue_count,
        "detection_threshold": threshold,
        "min_duration": min_duration
    }
    stage_io.save_metadata(save_metadata)
    
    logger.info("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
