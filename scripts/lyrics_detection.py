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

from shared.stage_utils import StageIO, get_stage_logger
from shared.config import load_config
from lyrics_detection_core import LyricsDetector


def main():
    """Main entry point for lyrics detection stage"""
    
    # Setup stage I/O
    stage_io = StageIO("lyrics_detection")
    
    # Setup logger using get_stage_logger
    logger = get_stage_logger("lyrics_detection", stage_io=stage_io)
    
    logger.info("=" * 70)
    logger.info("LYRICS DETECTION STAGE - Song Segment Identification")
    logger.info("=" * 70)
    logger.info(f"Output base: {stage_io.output_base}")
    logger.info(f"Stage directory: {stage_io.stage_dir}")
    
    # Load configuration
    try:
        config = load_config()
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return 1
    
    # Check if lyrics detection is enabled
    lyrics_detection_enabled = getattr(config, 'lyrics_detection_enabled', True)
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
    device = getattr(config, 'device', 'cpu')
    threshold = getattr(config, 'lyrics_detection_threshold', 0.5)
    min_duration = getattr(config, 'lyrics_min_duration', 30.0)
    
    detector = LyricsDetector(
        threshold=threshold,
        min_duration=min_duration,
        device=device,
        logger=logger
    )
    
    # Method 1: Audio feature analysis (if audio file available)
    audio_lyrics = []
    
    # Check for source-separated audio first (vocals only - better for analysis)
    sep_audio_numbered = stage_io.output_base / "99_source_separation" / "audio.wav"
    sep_audio_plain = stage_io.output_base / "source_separation" / "audio.wav"
    
    if sep_audio_numbered.exists():
        audio_file = sep_audio_numbered
        logger.info("Method 1: Analyzing audio features (using source-separated vocals)...")
        logger.info(f"  Input: {audio_file}")
    elif sep_audio_plain.exists():
        audio_file = sep_audio_plain
        logger.info("Method 1: Analyzing audio features (using source-separated vocals)...")
        logger.info(f"  Input: {audio_file}")
    else:
        # Fallback to original audio
        audio_file = stage_io.output_base / "media" / "audio.wav"
        if not audio_file.exists():
            audio_file = stage_io.output_base / "01_demux" / "audio.wav"
        logger.info("Method 1: Analyzing audio features (using original audio)...")
        logger.info(f"  Input: {audio_file}")
    
    if audio_file.exists():
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
    
    # Method 4: Music separation analysis (NEW - uses accompaniment.wav)
    music_separation_lyrics = []
    
    # Check for accompaniment.wav from source separation
    accompaniment_numbered = stage_io.output_base / "99_source_separation" / "accompaniment.wav"
    accompaniment_plain = stage_io.output_base / "source_separation" / "accompaniment.wav"
    
    accompaniment_file = None
    if accompaniment_numbered.exists():
        accompaniment_file = accompaniment_numbered
    elif accompaniment_plain.exists():
        accompaniment_file = accompaniment_plain
    
    if accompaniment_file and accompaniment_file.exists():
        logger.info("Method 4: Analyzing music separation (accompaniment + vocals)...")
        logger.info(f"  Accompaniment: {accompaniment_file}")
        logger.info(f"  Vocals: {audio_file}")
        try:
            # Get vocals file (already determined above)
            vocals_file = audio_file if (sep_audio_numbered.exists() or sep_audio_plain.exists()) else None
            
            if vocals_file:
                music_separation_lyrics = detector.detect_from_music_separation(
                    vocals_file,
                    accompaniment_file,
                    segments
                )
                logger.info(f"  Found {len(music_separation_lyrics)} lyric segments from music separation analysis")
            else:
                logger.warning("  Vocals file not available, skipping music separation analysis")
        except Exception as e:
            logger.warning(f"  Music separation analysis failed: {e}")
    else:
        logger.info("Method 4: No accompaniment file found, skipping music separation analysis")
    
    # Merge detections (now includes music separation detections)
    logger.info("Merging detection results...")
    all_lyrics = detector.merge_detections(
        audio_lyrics, 
        transcript_lyrics, 
        soundtrack_lyrics,
        music_separation_lyrics
    )
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
