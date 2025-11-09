#!/usr/bin/env python3
"""
Lyrics Detection container - Identify song sequences

Workflow: Stage 7c (new stage)
Input: asr/*.asr.json, audio/audio.wav
Output: asr/*.asr.json (with lyrics markers), asr/*.lyrics_summary.json
"""
import sys
import json
import os
from pathlib import Path
from typing import List, Dict, Tuple

# Setup paths - handle both Docker and native execution
execution_mode = os.getenv('EXECUTION_MODE', 'docker')
if execution_mode == 'native':
    # Native mode: add project root to path
    project_root = Path(__file__).resolve().parents[2]  # docker/lyrics-detection -> root
    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(project_root / 'shared'))
else:
    # Docker mode: use /app paths
    sys.path.insert(0, '/app')
    sys.path.insert(0, '/app/shared')

from logger import PipelineLogger


def detect_lyrics_heuristic(segments: List[Dict], logger: PipelineLogger) -> List[Tuple[float, float, float]]:
    """Detect lyrics using heuristic analysis."""
    logger.info("Running heuristic lyrics detection...")
    
    if not segments:
        return []
    
    song_sequences = []
    window_size = 10
    
    for i in range(0, len(segments), 5):
        window = segments[i:i+window_size]
        if len(window) < 3:
            continue
        
        score = 0.0
        
        # Repetition check
        texts = [seg.get('text', '').lower().strip() for seg in window]
        unique_ratio = len(set(texts)) / len(texts) if texts else 1.0
        if unique_ratio < 0.7:
            score += 0.3
        
        # Timing consistency
        durations = [seg.get('end', 0) - seg.get('start', 0) for seg in window]
        if durations:
            avg_dur = sum(durations) / len(durations)
            consistent = sum(1 for d in durations if abs(d - avg_dur) / avg_dur < 0.3) / len(durations)
            if consistent > 0.7:
                score += 0.2
        
        # Word density
        word_counts = [len(seg.get('text', '').split()) for seg in window]
        if word_counts:
            avg_words = sum(word_counts) / len(word_counts)
            if avg_words > 8:
                score += 0.2
        
        # Poetic markers
        poetic_markers = ['love', 'heart', 'soul', 'dil', 'pyaar', 'ishq', 'jaana', 'sajna']
        text_combined = ' '.join(texts).lower()
        marker_count = sum(1 for marker in poetic_markers if marker in text_combined)
        if marker_count > 2:
            score += 0.2
        
        # Musical terms
        music_terms = ['la la', 'na na', 'oh oh', 'yeah', 'ho ho', 'tra la', 'dum dum']
        music_count = sum(1 for term in music_terms if term in text_combined)
        if music_count > 0:
            score += 0.3
        
        if score >= 0.5:
            start_time = window[0].get('start', 0)
            end_time = window[-1].get('end', 0)
            song_sequences.append((start_time, end_time, score))
    
    # Merge overlapping sequences
    if song_sequences:
        merged = []
        current_start, current_end, current_score = song_sequences[0]
        
        for start, end, score in song_sequences[1:]:
            if start <= current_end + 5.0:
                current_end = end
                current_score = max(current_score, score)
            else:
                merged.append((current_start, current_end, current_score))
                current_start, current_end, current_score = start, end, score
        
        merged.append((current_start, current_end, current_score))
        song_sequences = merged
    
    logger.info(f"[OK] Detected {len(song_sequences)} song sequences")
    return song_sequences


def detect_lyrics_ml(audio_file: Path, segments: List[Dict], device: str, logger: PipelineLogger) -> List[Tuple[float, float, float]]:
    """Detect lyrics using ML audio analysis."""
    logger.info("Running ML-based lyrics detection...")
    
    try:
        import librosa
        import numpy as np
        
        y, sr = librosa.load(str(audio_file), sr=16000, mono=True)
        song_sequences = []
        
        for seg in segments:
            start = seg.get('start', 0)
            end = seg.get('end', 0)
            
            start_sample = int(start * sr)
            end_sample = int(end * sr)
            audio_seg = y[start_sample:end_sample]
            
            if len(audio_seg) < sr * 0.5:
                continue
            
            # Calculate audio features
            spec_centroid = librosa.feature.spectral_centroid(y=audio_seg, sr=sr)[0]
            spec_centroid_mean = np.mean(spec_centroid)
            
            tempo, beats = librosa.beat.beat_track(y=audio_seg, sr=sr)
            
            y_harmonic, y_percussive = librosa.effects.hpss(audio_seg)
            harmonic_ratio = np.sum(np.abs(y_harmonic)) / (np.sum(np.abs(y_percussive)) + 1e-6)
            
            zcr = librosa.feature.zero_crossing_rate(audio_seg)[0]
            zcr_mean = np.mean(zcr)
            
            # Calculate music score
            score = 0.0
            if spec_centroid_mean > 2000:
                score += 0.25
            if 60 < tempo < 180:
                score += 0.25
            if harmonic_ratio > 2.0:
                score += 0.25
            if zcr_mean < 0.1:
                score += 0.25
            
            if score >= 0.5:
                song_sequences.append((start, end, score))
        
        # Merge adjacent segments
        if song_sequences:
            merged = []
            current_start, current_end, current_score = song_sequences[0]
            
            for start, end, score in song_sequences[1:]:
                if start <= current_end + 2.0:
                    current_end = end
                    current_score = max(current_score, score)
                else:
                    merged.append((current_start, current_end, current_score))
                    current_start, current_end, current_score = start, end, score
            
            merged.append((current_start, current_end, current_score))
            song_sequences = merged
        
        logger.info(f"[OK] Detected {len(song_sequences)} song sequences (ML)")
        return song_sequences
        
    except ImportError:
        logger.warning("librosa not available, falling back to heuristic")
        return []
    except Exception as e:
        logger.error(f"ML detection failed: {e}")
        return []


def mark_lyrics_in_segments(segments: List[Dict], song_sequences: List[Tuple[float, float, float]], logger: PipelineLogger) -> List[Dict]:
    """Mark segments that fall within song sequences."""
    
    if not song_sequences:
        return segments
    
    marked_count = 0
    
    for seg in segments:
        seg_start = seg.get('start', 0)
        seg_end = seg.get('end', 0)
        seg_mid = (seg_start + seg_end) / 2
        
        for song_start, song_end, confidence in song_sequences:
            if song_start <= seg_mid <= song_end:
                seg['is_lyric'] = True
                seg['lyric_confidence'] = confidence
                marked_count += 1
                break
    
    logger.info(f"[OK] Marked {marked_count}/{len(segments)} segments as lyrics")
    return segments


def main():
    if len(sys.argv) < 2:
        print("Usage: lyrics_detection.py <movie_dir>")
        sys.exit(1)
    
    movie_dir = Path(sys.argv[1])
    
    from config import load_config
    config = load_config()
    
    log_level = config.log_level.upper() if hasattr(config, 'log_level') else "INFO"
    logger = PipelineLogger("lyrics_detection", log_level=log_level)
    logger.info(f"Starting lyrics detection for: {movie_dir}")
    
    # Log config source
    config_path = os.getenv('CONFIG_PATH', '/app/config/.env')
    logger.info(f"Using config: {config_path}")
    
    # Check if enabled
    enabled = config.get('lyric_detect_enabled', False)
    if not enabled:
        logger.info("Lyrics detection disabled in config")
        logger.info("To enable: set LYRIC_DETECT_ENABLED=true in job config")
        sys.exit(0)
    
    # Get config with detailed logging
    threshold = config.get('lyric_threshold', 0.5)
    min_duration = config.get('lyric_min_duration', 30.0)
    device = config.get('device', 'cpu')
    use_ml = config.get('lyric_use_ml', False)
    
    logger.info(f"Configuration:")
    logger.info(f"  Detection threshold: {threshold} (from LYRIC_THRESHOLD)")
    logger.info(f"  Minimum duration: {min_duration}s (from LYRIC_MIN_DURATION)")
    logger.info(f"  Device: {device}")
    logger.info(f"  Use ML detection: {use_ml}")
    
    try:
        # Load ASR result
        asr_file = movie_dir / "asr" / f"{movie_dir.name}.asr.json"
        if not asr_file.exists():
            logger.error(f"ASR file not found: {asr_file}")
            sys.exit(1)
        
        with open(asr_file, 'r') as f:
            asr_result = json.load(f)
        
        segments = asr_result.get('segments', [])
        logger.info(f"Loaded {len(segments)} segments")
        
        # Detect lyrics using both methods
        song_sequences_heuristic = detect_lyrics_heuristic(segments, logger)
        
        audio_file = movie_dir / "audio" / "audio.wav"
        song_sequences_ml = []
        if audio_file.exists():
            song_sequences_ml = detect_lyrics_ml(audio_file, segments, device, logger)
        
        # Use ML if available, otherwise heuristic
        if song_sequences_ml:
            song_sequences = song_sequences_ml
            detection_method = 'ml'
        else:
            song_sequences = song_sequences_heuristic
            detection_method = 'heuristic'
        
        # Filter by minimum duration
        song_sequences = [(s, e, c) for s, e, c in song_sequences if (e - s) >= min_duration]
        logger.info(f"[OK] Found {len(song_sequences)} song sequences (min {min_duration}s)")
        
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
        with open(asr_file, 'w') as f:
            json.dump(asr_result, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved enhanced result: {asr_file}")
        
        # Save lyrics summary
        lyrics_summary_file = movie_dir / "asr" / f"{movie_dir.name}.lyrics_summary.json"
        lyrics_summary = {
            'detection_method': detection_method,
            'total_segments': len(segments),
            'lyric_segments': sum(1 for seg in segments if seg.get('is_lyric', False)),
            'song_sequences': asr_result['song_sequences'],
            'total_lyrics_duration': sum(e - s for s, e, c in song_sequences)
        }
        
        with open(lyrics_summary_file, 'w') as f:
            json.dump(lyrics_summary, f, indent=2)
        
        logger.info(f"Saved lyrics summary: {lyrics_summary_file}")
        logger.info(f"[OK] Detected {len(song_sequences)} song sequences")
        
    except Exception as e:
        logger.error(f"Lyrics detection failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == '__main__':
    main()
