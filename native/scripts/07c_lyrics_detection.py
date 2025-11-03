#!/usr/bin/env python3
"""Stage 7c: Lyrics Detection - Identify and mark song sequences for special subtitle treatment"""
import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Tuple
import time

sys.path.insert(0, 'native/utils')
from device_manager import get_device
from native_logger import NativePipelineLogger
from manifest import StageManifest


def load_env_config() -> dict:
    """Load configuration from environment variables."""
    return {
        'enabled': os.getenv('LYRIC_DETECT_ENABLED', 'false').lower() == 'true',
        'threshold': float(os.getenv('LYRIC_THRESHOLD', '0.5')),
        'style': os.getenv('LYRIC_STYLE', 'lyric'),
        'min_duration': float(os.getenv('LYRIC_MIN_DURATION', '30.0')),  # 30 seconds minimum
        'device': os.getenv('WHISPERX_DEVICE', 'cpu')
    }


def detect_lyrics_heuristic(segments: List[Dict], logger) -> List[Tuple[float, float, str]]:
    """
    Detect lyrics using heuristic methods.
    
    Indicators of song/lyrics:
    - Repetitive phrases
    - Rhyming patterns
    - Musical tempo (consistent timing)
    - Higher word density
    - Emotional/poetic language
    
    Returns:
        List of (start, end, confidence) tuples for song sequences
    """
    logger.info("Running heuristic lyrics detection...")
    
    if not segments:
        return []
    
    song_sequences = []
    
    # Analyze segments for song patterns
    window_size = 10  # Analyze 10 segments at a time
    
    for i in range(0, len(segments), 5):  # Slide by 5 segments
        window = segments[i:i+window_size]
        if len(window) < 3:
            continue
        
        # Calculate song indicators
        score = 0.0
        
        # 1. Check for repetition
        texts = [seg.get('text', '').lower().strip() for seg in window]
        unique_ratio = len(set(texts)) / len(texts) if texts else 1.0
        if unique_ratio < 0.7:  # More than 30% repetition
            score += 0.3
        
        # 2. Check timing consistency (musical tempo)
        durations = [seg.get('end', 0) - seg.get('start', 0) for seg in window]
        if durations:
            avg_dur = sum(durations) / len(durations)
            # Check if durations are consistent (within 30% of average)
            consistent = sum(1 for d in durations if abs(d - avg_dur) / avg_dur < 0.3) / len(durations)
            if consistent > 0.7:
                score += 0.2
        
        # 3. Check word density (songs tend to have more words)
        word_counts = [len(seg.get('text', '').split()) for seg in window]
        if word_counts:
            avg_words = sum(word_counts) / len(word_counts)
            if avg_words > 8:  # More than 8 words per segment
                score += 0.2
        
        # 4. Check for poetic markers (Hindi/English)
        poetic_markers = ['love', 'heart', 'soul', 'dil', 'pyaar', 'ishq', 'jaana', 'sajna']
        text_combined = ' '.join(texts).lower()
        marker_count = sum(1 for marker in poetic_markers if marker in text_combined)
        if marker_count > 2:
            score += 0.2
        
        # 5. Check for musical terms
        music_terms = ['la la', 'na na', 'oh oh', 'yeah', 'ho ho', 'tra la', 'dum dum']
        music_count = sum(1 for term in music_terms if term in text_combined)
        if music_count > 0:
            score += 0.3
        
        # If score exceeds threshold, mark as song
        if score >= 0.5:  # Threshold
            start_time = window[0].get('start', 0)
            end_time = window[-1].get('end', 0)
            song_sequences.append((start_time, end_time, score))
    
    # Merge overlapping/adjacent song sequences
    if song_sequences:
        merged = []
        current_start, current_end, current_score = song_sequences[0]
        
        for start, end, score in song_sequences[1:]:
            if start <= current_end + 5.0:  # Gap less than 5 seconds
                current_end = end
                current_score = max(current_score, score)
            else:
                merged.append((current_start, current_end, current_score))
                current_start, current_end, current_score = start, end, score
        
        merged.append((current_start, current_end, current_score))
        song_sequences = merged
    
    logger.info(f"✓ Detected {len(song_sequences)} potential song sequences (heuristic)")
    return song_sequences


def detect_lyrics_ml(audio_file: Path, segments: List[Dict], device: str, logger) -> List[Tuple[float, float, str]]:
    """
    Detect lyrics using ML audio classifier.
    
    Uses audio features to detect music vs speech:
    - Spectral features
    - Rhythm patterns
    - Harmonic content
    
    Returns:
        List of (start, end, confidence) tuples for song sequences
    """
    logger.info("Running ML-based lyrics detection...")
    
    try:
        import librosa
        import numpy as np
        
        # Load audio
        logger.debug(f"Loading audio: {audio_file}")
        y, sr = librosa.load(str(audio_file), sr=16000, mono=True)
        
        # Analyze segments
        song_sequences = []
        
        for seg in segments:
            start = seg.get('start', 0)
            end = seg.get('end', 0)
            
            # Extract audio segment
            start_sample = int(start * sr)
            end_sample = int(end * sr)
            audio_seg = y[start_sample:end_sample]
            
            if len(audio_seg) < sr * 0.5:  # Skip very short segments
                continue
            
            # Calculate features
            # 1. Spectral centroid (brightness - music tends to be brighter)
            spec_centroid = librosa.feature.spectral_centroid(y=audio_seg, sr=sr)[0]
            spec_centroid_mean = np.mean(spec_centroid)
            
            # 2. Tempo (music has consistent tempo)
            tempo, beats = librosa.beat.beat_track(y=audio_seg, sr=sr)
            
            # 3. Harmonic vs percussive ratio
            y_harmonic, y_percussive = librosa.effects.hpss(audio_seg)
            harmonic_ratio = np.sum(np.abs(y_harmonic)) / (np.sum(np.abs(y_percussive)) + 1e-6)
            
            # 4. Zero crossing rate (speech has higher ZCR)
            zcr = librosa.feature.zero_crossing_rate(audio_seg)[0]
            zcr_mean = np.mean(zcr)
            
            # Calculate music probability
            score = 0.0
            
            # Higher spectral centroid indicates music
            if spec_centroid_mean > 2000:
                score += 0.25
            
            # Consistent tempo indicates music
            if 60 < tempo < 180:  # Typical song tempo
                score += 0.25
            
            # Higher harmonic content indicates music
            if harmonic_ratio > 2.0:
                score += 0.25
            
            # Lower ZCR indicates singing (smoother than speech)
            if zcr_mean < 0.1:
                score += 0.25
            
            if score >= 0.5:  # Threshold
                song_sequences.append((start, end, score))
        
        # Merge adjacent song segments
        if song_sequences:
            merged = []
            current_start, current_end, current_score = song_sequences[0]
            
            for start, end, score in song_sequences[1:]:
                if start <= current_end + 2.0:  # Gap less than 2 seconds
                    current_end = end
                    current_score = max(current_score, score)
                else:
                    merged.append((current_start, current_end, current_score))
                    current_start, current_end, current_score = start, end, score
            
            merged.append((current_start, current_end, current_score))
            song_sequences = merged
        
        logger.info(f"✓ Detected {len(song_sequences)} potential song sequences (ML)")
        return song_sequences
        
    except ImportError as e:
        logger.warning(f"librosa not available: {e}")
        logger.warning("Falling back to heuristic detection")
        return []
    except Exception as e:
        logger.error(f"ML detection failed: {e}")
        return []


def mark_lyrics_in_segments(segments: List[Dict], song_sequences: List[Tuple[float, float, str]], logger) -> List[Dict]:
    """Mark segments that fall within song sequences."""
    
    if not song_sequences:
        logger.info("No song sequences detected")
        return segments
    
    marked_count = 0
    
    for seg in segments:
        seg_start = seg.get('start', 0)
        seg_end = seg.get('end', 0)
        seg_mid = (seg_start + seg_end) / 2
        
        # Check if segment overlaps with any song sequence
        for song_start, song_end, confidence in song_sequences:
            if song_start <= seg_mid <= song_end:
                seg['is_lyric'] = True
                seg['lyric_confidence'] = confidence
                marked_count += 1
                break
    
    logger.info(f"✓ Marked {marked_count}/{len(segments)} segments as lyrics")
    return segments


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, help='Input video file')
    parser.add_argument('--movie-dir', required=True, help='Movie output directory')
    args = parser.parse_args()
    
    movie_dir = Path(args.movie_dir)
    movie_name = movie_dir.name
    logger = NativePipelineLogger('lyrics_detection', movie_name)
    
    try:
        logger.log_stage_start("Lyrics Detection - Identifying song sequences")
        
        # Load configuration
        env_config = load_env_config()
        
        # Check if enabled
        if not env_config['enabled']:
            logger.info("Lyrics detection disabled in config")
            logger.log_stage_success("Skipped (disabled)")
            return 0
        
        logger.info(f"Threshold: {env_config['threshold']}")
        logger.info(f"Style: {env_config['style']}")
        
        start = time.time()
        
        with StageManifest('lyrics_detection', movie_dir, logger.logger) as manifest:
            # Load ASR result
            asr_file = movie_dir / "asr" / f"{movie_name}.asr.json"
            if not asr_file.exists():
                logger.error(f"ASR file not found: {asr_file}")
                raise FileNotFoundError(f"ASR file not found: {asr_file}")
            
            with open(asr_file, 'r') as f:
                asr_result = json.load(f)
            
            segments = asr_result.get('segments', [])
            logger.info(f"Loaded {len(segments)} segments from ASR")
            
            # Detect lyrics using both methods
            song_sequences_heuristic = detect_lyrics_heuristic(segments, logger)
            
            # Try ML detection
            audio_file = movie_dir / "audio" / "audio.wav"
            song_sequences_ml = []
            if audio_file.exists():
                device = env_config['device'].lower()
                song_sequences_ml = detect_lyrics_ml(audio_file, segments, device, logger)
            
            # Combine results (use ML if available, otherwise heuristic)
            if song_sequences_ml:
                song_sequences = song_sequences_ml
                detection_method = 'ml'
            else:
                song_sequences = song_sequences_heuristic
                detection_method = 'heuristic'
            
            # Filter by minimum duration
            min_duration = env_config['min_duration']
            song_sequences = [(s, e, c) for s, e, c in song_sequences if (e - s) >= min_duration]
            
            logger.info(f"✓ Found {len(song_sequences)} song sequences (min {min_duration}s)")
            
            # Mark segments
            segments = mark_lyrics_in_segments(segments, song_sequences, logger)
            asr_result['segments'] = segments
            asr_result['lyrics_detected'] = True
            asr_result['detection_method'] = detection_method
            asr_result['song_sequences'] = [
                {'start': s, 'end': e, 'confidence': c, 'duration': e - s}
                for s, e, c in song_sequences
            ]
            
            # Save enhanced result
            output_file = asr_file
            with open(output_file, 'w') as f:
                json.dump(asr_result, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved enhanced result: {output_file}")
            
            # Save lyrics summary
            lyrics_summary_file = movie_dir / "asr" / f"{movie_name}.lyrics_summary.json"
            lyrics_summary = {
                'detection_method': detection_method,
                'total_segments': len(segments),
                'lyric_segments': sum(1 for seg in segments if seg.get('is_lyric', False)),
                'song_sequences': asr_result['song_sequences'],
                'total_lyrics_duration': sum(e - s for s, e, _ in song_sequences)
            }
            
            with open(lyrics_summary_file, 'w') as f:
                json.dump(lyrics_summary, f, indent=2)
            
            logger.info(f"Saved lyrics summary: {lyrics_summary_file}")
            
            duration = time.time() - start
            
            # Update manifest
            manifest.add_output_file(output_file, "ASR with lyrics detection")
            manifest.add_output_file(lyrics_summary_file, "Lyrics detection summary")
            manifest.add_stat('duration', duration)
            manifest.add_stat('num_song_sequences', len(song_sequences))
            manifest.add_stat('detection_method', detection_method)
            manifest.add_stat('lyric_segments', lyrics_summary['lyric_segments'])
        
        logger.log_stage_success(f"Detected {len(song_sequences)} song sequences in {duration:.1f}s")
        return 0
        
    except Exception as e:
        logger.log_stage_error(f"Lyrics detection failed: {e}")
        import traceback
        logger.logger.error(traceback.format_exc())
        return 1


if __name__ == '__main__':
    sys.exit(main())
