#!/usr/bin/env python3
"""
Lyrics Detection Core - Detect song/musical segments in audio

Uses multiple approaches:
1. Audio feature analysis (tempo, rhythm, spectral features)
2. Repetition detection in ASR transcripts
3. Energy/pitch pattern analysis
"""

import numpy as np
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import logging

# Local
from shared.logger import get_logger
logger = get_logger(__name__)

# Optional librosa for audio analysis
try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False


class LyricsDetector:
    """Detect song/musical segments in audio"""
    
    def __init__(
        self,
        threshold: float = 0.5,
        min_duration: float = 30.0,
        device: str = "cpu",
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize lyrics detector
        
        Args:
            threshold: Confidence threshold for lyrics detection
            min_duration: Minimum duration for a lyric segment (seconds)
            device: Device to use (cpu/cuda)
            logger: Logger instance
        """
        self.threshold = threshold
        self.min_duration = min_duration
        self.device = device
        self.logger = logger or logging.getLogger(__name__)
        
    def detect_from_audio_features(
        self,
        audio_file: Path,
        vad_segments: List[Dict]
    ) -> List[Dict]:
        """
        Detect lyrics using audio feature analysis
        
        Args:
            audio_file: Path to audio file
            vad_segments: VAD segments with start/end times
            
        Returns:
            List of detected lyric segments with confidence scores
        """
        if not LIBROSA_AVAILABLE:
            self.logger.warning("librosa not available, skipping audio analysis")
            return []
        
        try:
            # Load audio
            y, sr = librosa.load(str(audio_file), sr=16000)
            
            lyric_segments = []
            
            # Analyze each VAD segment
            for seg in vad_segments:
                start = seg.get('start', 0)
                end = seg.get('end', 0)
                
                # Skip short segments
                if end - start < self.min_duration:
                    continue
                
                # Extract audio segment
                start_sample = int(start * sr)
                end_sample = int(end * sr)
                segment_audio = y[start_sample:end_sample]
                
                # Calculate features
                confidence = self._calculate_music_confidence(segment_audio, sr)
                
                if confidence > self.threshold:
                    lyric_segments.append({
                        'start': start,
                        'end': end,
                        'confidence': float(confidence),
                        'type': 'lyric',
                        'detection_method': 'audio_features'
                    })
            
            return lyric_segments
            
        except Exception as e:
            self.logger.error(f"Audio feature analysis failed: {e}")
            return []
    
    def _calculate_music_confidence(self, audio: np.ndarray, sr: int) -> float:
        """
        Calculate confidence that audio segment contains music/lyrics
        
        Uses multiple features:
        - Tempo consistency (songs have steady beat)
        - Spectral contrast (music has richer harmonics)
        - Zero crossing rate patterns
        - Chroma features (musical pitch content)
        
        Args:
            audio: Audio samples
            sr: Sample rate
            
        Returns:
            Confidence score (0-1)
        """
        features_scores = []
        
        try:
            # Feature 1: Tempo consistency
            tempo, _ = librosa.beat.beat_track(y=audio, sr=sr)
            # Songs typically have tempo between 60-180 BPM
            tempo_score = 1.0 if 60 <= tempo <= 180 else 0.3
            features_scores.append(tempo_score)
            
            # Feature 2: Spectral contrast (music has more harmonic content)
            spectral_contrast = librosa.feature.spectral_contrast(y=audio, sr=sr)
            contrast_mean = np.mean(spectral_contrast)
            # Higher contrast suggests music
            contrast_score = min(1.0, contrast_mean / 30.0)
            features_scores.append(contrast_score)
            
            # Feature 3: Chroma features (pitch class content)
            chroma = librosa.feature.chroma_stft(y=audio, sr=sr)
            chroma_variance = np.var(chroma, axis=1).mean()
            # Music has varied pitch content
            chroma_score = min(1.0, chroma_variance * 10)
            features_scores.append(chroma_score)
            
            # Feature 4: Rhythm regularity
            onset_env = librosa.onset.onset_strength(y=audio, sr=sr)
            # Calculate autocorrelation to detect periodic patterns
            ac = np.correlate(onset_env, onset_env, mode='full')
            ac = ac[len(ac)//2:]
            # Normalize
            ac = ac / ac[0] if ac[0] > 0 else ac
            # Find peaks (periodic beats)
            peaks = np.where(ac[1:] > 0.5)[0]
            rhythm_score = 1.0 if len(peaks) > 5 else 0.3
            features_scores.append(rhythm_score)
            
        except Exception as e:
            self.logger.warning(f"Feature extraction failed: {e}")
            return 0.0
        
        # Combine scores (weighted average)
        if not features_scores:
            return 0.0
        
        return np.mean(features_scores)
    
    def detect_from_transcript_patterns(
        self,
        segments: List[Dict]
    ) -> List[Dict]:
        """
        Detect lyrics by analyzing transcript patterns
        
        Lyrics typically have:
        - Repetitive phrases
        - Poetic structure
        - Shorter segments
        - Less conversational language
        
        Args:
            segments: ASR transcript segments
            
        Returns:
            List of detected lyric segments
        """
        lyric_segments = []
        
        if not segments:
            return lyric_segments
        
        # Look for repetitive patterns (verse/chorus)
        text_blocks = []
        current_block = []
        current_start = None
        
        for i, seg in enumerate(segments):
            text = seg.get('text', '').strip()
            if not text:
                continue
            
            if current_start is None:
                current_start = seg.get('start', 0)
            
            current_block.append(text)
            
            # Check for block boundaries (pauses, pattern changes)
            is_block_end = False
            
            # End block after ~30 seconds
            if i < len(segments) - 1:
                next_start = segments[i + 1].get('start', 0)
                current_time = seg.get('end', 0)
                if next_start - current_time > 2.0:  # Long pause
                    is_block_end = True
                elif current_time - current_start > 45.0:  # Max block size
                    is_block_end = True
            else:
                is_block_end = True
            
            if is_block_end and current_block:
                block_text = ' '.join(current_block)
                text_blocks.append({
                    'start': current_start,
                    'end': seg.get('end', 0),
                    'text': block_text,
                    'segment_count': len(current_block)
                })
                current_block = []
                current_start = None
        
        # Find repetitions (simple n-gram matching)
        for i, block1 in enumerate(text_blocks):
            max_similarity = 0.0
            
            for j, block2 in enumerate(text_blocks):
                if i == j:
                    continue
                
                # Calculate word overlap
                words1 = set(block1['text'].lower().split())
                words2 = set(block2['text'].lower().split())
                
                if not words1 or not words2:
                    continue
                
                similarity = len(words1 & words2) / max(len(words1), len(words2))
                max_similarity = max(max_similarity, similarity)
            
            # High repetition suggests lyrics
            # Lower threshold for better detection of songs and poetic segments
            if max_similarity > 0.35:  # 35% word overlap (more sensitive)
                duration = block1['end'] - block1['start']
                # Use a more flexible duration threshold
                # Allow shorter segments (15s minimum) if high confidence
                min_dur = 15.0 if max_similarity > 0.5 else self.min_duration
                if duration >= min_dur:
                    lyric_segments.append({
                        'start': block1['start'],
                        'end': block1['end'],
                        'confidence': float(max_similarity),
                        'type': 'lyric',
                        'detection_method': 'transcript_pattern'
                    })
        
        # Additional pass: detect short poetic lines (common in Bollywood songs)
        # Look for consecutive short segments with simple language patterns
        for i, block in enumerate(text_blocks):
            duration = block['end'] - block['start']
            # Short segments (10-45 seconds) with few words per segment suggest lyrics
            if 10.0 <= duration <= 45.0 and block['segment_count'] >= 4:
                avg_words_per_seg = len(block['text'].split()) / block['segment_count']
                # Lyrics often have 3-8 words per line
                if 3 <= avg_words_per_seg <= 10:
                    # Check if not already detected
                    overlaps = any(
                        seg['start'] <= block['start'] <= seg['end'] or
                        seg['start'] <= block['end'] <= seg['end']
                        for seg in lyric_segments
                    )
                    if not overlaps:
                        lyric_segments.append({
                            'start': block['start'],
                            'end': block['end'],
                            'confidence': 0.4,  # Lower confidence for pattern-only detection
                            'type': 'lyric',
                            'detection_method': 'transcript_pattern_short'
                        })
        
        return lyric_segments
    
    def detect_from_soundtrack_durations(
        self,
        segments: List[Dict],
        soundtrack: List[Dict]
    ) -> List[Dict]:
        """
        Detect song segments by matching duration with known soundtrack
        
        Args:
            segments: ASR transcript segments
            soundtrack: List of soundtrack tracks with duration_ms
        
        Returns:
            List of detected lyric segments
        """
        if not soundtrack:
            self.logger.debug("No soundtrack data available")
            return []
        
        self.logger.info("Detecting songs using soundtrack duration matching...")
        
        # Build continuous segment groups (potential song segments)
        song_candidates = []
        current_group = []
        last_end = 0
        
        for seg in segments:
            seg_start = seg.get('start', 0)
            seg_end = seg.get('end', 0)
            
            # If gap > 5 seconds, start new group
            if seg_start - last_end > 5.0:
                if current_group:
                    group_start = current_group[0]['start']
                    group_end = current_group[-1]['end']
                    group_duration = group_end - group_start
                    
                    song_candidates.append({
                        'start': group_start,
                        'end': group_end,
                        'duration': group_duration,
                        'segments': current_group
                    })
                
                current_group = []
            
            current_group.append(seg)
            last_end = seg_end
        
        # Add last group
        if current_group:
            group_start = current_group[0]['start']
            group_end = current_group[-1]['end']
            group_duration = group_end - group_start
            
            song_candidates.append({
                'start': group_start,
                'end': group_end,
                'duration': group_duration,
                'segments': current_group
            })
        
        self.logger.debug(f"Found {len(song_candidates)} candidate segments")
        
        # Match candidates with soundtrack durations
        detected_lyrics = []
        
        for candidate in song_candidates:
            candidate_duration = candidate['duration']
            
            # Skip very short segments
            if candidate_duration < self.min_duration:
                continue
            
            best_match = None
            best_score = 0
            
            for track in soundtrack:
                # Get track duration in seconds
                track_duration_ms = track.get('duration_ms', 0)
                if not track_duration_ms:
                    continue
                
                track_duration = track_duration_ms / 1000.0
                
                # Calculate similarity (1 - normalized difference)
                # Allow ±20% variation
                duration_diff = abs(candidate_duration - track_duration)
                duration_ratio = duration_diff / track_duration
                
                if duration_ratio < 0.20:  # Within 20%
                    # Score: 1.0 for exact match, decreasing with difference
                    score = 1.0 - (duration_ratio * 2)  # Scale to 0.6-1.0 range
                    
                    if score > best_score:
                        best_score = score
                        best_match = track
            
            # If good match found, mark as lyrics
            if best_match and best_score > 0.6:
                detected_lyrics.append({
                    'start': candidate['start'],
                    'end': candidate['end'],
                    'duration': candidate['duration'],
                    'confidence': best_score,
                    'detection_method': 'soundtrack_duration',
                    'matched_song': best_match.get('title', 'Unknown'),
                    'matched_artist': best_match.get('artist', 'Unknown'),
                    'expected_duration': best_match.get('duration_ms', 0) / 1000.0
                })
                
                self.logger.debug(
                    f"Matched segment {candidate['start']:.1f}-{candidate['end']:.1f}s "
                    f"({candidate['duration']:.1f}s) to '{best_match.get('title')}' "
                    f"(confidence: {best_score:.2f})"
                )
        
        self.logger.info(f"Detected {len(detected_lyrics)} song segments using soundtrack")
        
        return detected_lyrics
    
    def detect_from_music_separation(
        self,
        vocals_file: Path,
        accompaniment_file: Path,
        segments: List[Dict]
    ) -> List[Dict]:
        """
        Detect lyrics using source-separated vocals and accompaniment tracks
        
        This method combines analysis of:
        - accompaniment.wav: Pure music signal (no speech)
        - vocals.wav: Clean vocals (no music)
        
        Args:
            vocals_file: Path to vocals-only audio (clean speech/singing)
            accompaniment_file: Path to music-only audio (no vocals)
            segments: ASR segments with timing information
            
        Returns:
            List of detected lyric segments with confidence scores
        """
        if not LIBROSA_AVAILABLE:
            self.logger.warning("librosa not available, cannot perform music separation analysis")
            return []
        
        detected_lyrics = []
        
        try:
            # Load both audio files
            self.logger.debug(f"Loading vocals from: {vocals_file}")
            y_vocals, sr = librosa.load(str(vocals_file), sr=16000)
            
            self.logger.debug(f"Loading accompaniment from: {accompaniment_file}")
            y_music, sr = librosa.load(str(accompaniment_file), sr=16000)
            
            # Analyze music energy from accompaniment (pure music signal)
            hop_length = 512
            music_energy = librosa.feature.rms(y=y_music, hop_length=hop_length)[0]
            music_times = librosa.frames_to_time(
                np.arange(len(music_energy)),
                sr=sr,
                hop_length=hop_length
            )
            
            # Detect high music energy segments (likely songs)
            music_threshold = np.mean(music_energy) + 0.5 * np.std(music_energy)
            music_segments = []
            
            in_music = False
            music_start = 0
            
            for i, (time, energy) in enumerate(zip(music_times, music_energy)):
                if energy > music_threshold and not in_music:
                    # Start of music segment
                    in_music = True
                    music_start = time
                elif energy <= music_threshold and in_music:
                    # End of music segment
                    in_music = False
                    duration = time - music_start
                    if duration >= self.min_duration:
                        music_segments.append({
                            'start': music_start,
                            'end': time,
                            'music_energy': float(np.mean(music_energy[max(0, i-10):i]))
                        })
            
            # Close final segment if still in music
            if in_music:
                duration = music_times[-1] - music_start
                if duration >= self.min_duration:
                    music_segments.append({
                        'start': music_start,
                        'end': music_times[-1],
                        'music_energy': float(np.mean(music_energy[-10:]))
                    })
            
            self.logger.debug(f"Detected {len(music_segments)} high-energy music segments")
            
            # Analyze vocals for singing patterns (pitch variance)
            if len(music_segments) > 0:
                # Extract pitch from vocals
                pitches, magnitudes = librosa.piptrack(
                    y=y_vocals,
                    sr=sr,
                    hop_length=hop_length
                )
                
                # For each music segment, check if vocals show singing patterns
                for music_seg in music_segments:
                    start_frame = int(music_seg['start'] * sr / hop_length)
                    end_frame = int(music_seg['end'] * sr / hop_length)
                    
                    if end_frame > pitches.shape[1]:
                        end_frame = pitches.shape[1]
                    
                    if start_frame >= end_frame:
                        continue
                    
                    # Get pitch contour for this segment
                    segment_pitches = []
                    for frame in range(start_frame, end_frame):
                        # Get max magnitude pitch for this frame
                        index = magnitudes[:, frame].argmax()
                        pitch = pitches[index, frame]
                        if pitch > 0:  # Valid pitch
                            segment_pitches.append(pitch)
                    
                    if len(segment_pitches) < 10:
                        continue
                    
                    # Calculate pitch variance (singing has high variance)
                    pitch_variance = np.std(segment_pitches)
                    pitch_mean = np.mean(segment_pitches)
                    
                    # Singing typically has:
                    # - High pitch variance (melodic)
                    # - Consistent pitch presence (not just noise)
                    if pitch_variance > 50 and pitch_mean > 100:
                        # This looks like singing!
                        confidence = min(1.0, (pitch_variance / 200) * (music_seg['music_energy'] / music_threshold))
                        
                        if confidence > self.threshold:
                            detected_lyrics.append({
                                'start': music_seg['start'],
                                'end': music_seg['end'],
                                'confidence': float(confidence),
                                'type': 'lyric',
                                'detection_method': 'music_separation',
                                'features': {
                                    'music_energy': music_seg['music_energy'],
                                    'pitch_variance': float(pitch_variance),
                                    'pitch_mean': float(pitch_mean)
                                }
                            })
            
            self.logger.info(
                f"Detected {len(detected_lyrics)} lyric segments using music separation "
                f"(analyzed {len(music_segments)} music regions)"
            )
            
        except Exception as e:
            self.logger.error(f"Music separation analysis failed: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
        
        return detected_lyrics
    
    def merge_detections(
        self,
        audio_detections: List[Dict],
        transcript_detections: List[Dict],
        soundtrack_detections: List[Dict] = None,
        music_separation_detections: List[Dict] = None
    ) -> List[Dict]:
        """
        Merge and consolidate detections from multiple methods
        
        Args:
            audio_detections: Detections from audio features
            transcript_detections: Detections from transcript patterns
            soundtrack_detections: Detections from soundtrack duration matching (optional)
            music_separation_detections: Detections from music separation analysis (optional)
            
        Returns:
            Merged list of lyric segments
        """
        all_detections = audio_detections + transcript_detections
        if soundtrack_detections:
            all_detections += soundtrack_detections
        if music_separation_detections:
            all_detections += music_separation_detections
        
        if not all_detections:
            return []
        
        # Sort by start time
        all_detections.sort(key=lambda x: x['start'])
        
        # Merge overlapping segments
        merged = []
        current = all_detections[0].copy()
        
        for det in all_detections[1:]:
            # Check for overlap
            if det['start'] <= current['end'] + 5.0:  # 5s tolerance
                # Merge
                current['end'] = max(current['end'], det['end'])
                current['confidence'] = max(current['confidence'], det['confidence'])
                
                # Combine methods
                methods = current.get('detection_method', '').split(',')
                det_method = det.get('detection_method', '')
                if det_method and det_method not in methods:
                    methods.append(det_method)
                current['detection_method'] = ','.join(filter(None, methods))
                
                # Preserve song metadata if available
                if 'matched_song' in det and 'matched_song' not in current:
                    current['matched_song'] = det['matched_song']
                    current['matched_artist'] = det.get('matched_artist', '')
            else:
                # No overlap, save current and start new
                merged.append(current)
                current = det.copy()
        
        # Add last segment
        merged.append(current)
        
        # Filter by minimum duration
        merged = [seg for seg in merged if seg['end'] - seg['start'] >= self.min_duration]
        
        return merged


def run_lyrics_detection(
    audio_file: Path,
    output_dir: Path,
    vad_segments: List[Dict],
    asr_segments: List[Dict],
    threshold: float = 0.5,
    min_duration: float = 30.0,
    device: str = "cpu",
    logger: Optional[logging.Logger] = None
) -> Dict:
    """
    Run complete lyrics detection pipeline
    
    Args:
        audio_file: Path to audio file
        output_dir: Output directory
        vad_segments: VAD segments
        asr_segments: ASR transcript segments
        threshold: Detection threshold
        min_duration: Minimum lyric segment duration
        device: Device to use
        logger: Logger instance
        
    Returns:
        Detection results dict
    """
    detector = LyricsDetector(
        threshold=threshold,
        min_duration=min_duration,
        device=device,
        logger=logger
    )
    
    # Detect from audio features
    audio_detections = []
    if audio_file.exists() and vad_segments:
        audio_detections = detector.detect_from_audio_features(audio_file, vad_segments)
    
    # Detect from transcript patterns
    transcript_detections = []
    if asr_segments:
        transcript_detections = detector.detect_from_transcript_patterns(asr_segments)
    
    # Merge detections
    lyric_segments = detector.merge_detections(audio_detections, transcript_detections)
    
    # Save results
    lyrics_dir = output_dir / "lyrics"
    lyrics_dir.mkdir(parents=True, exist_ok=True)
    
    result = {
        "detected": len(lyric_segments) > 0,
        "total_segments": len(lyric_segments),
        "total_duration": sum(seg['end'] - seg['start'] for seg in lyric_segments),
        "lyric_segments": lyric_segments,
        "detection_methods": {
            "audio_features": len(audio_detections),
            "transcript_patterns": len(transcript_detections)
        }
    }
    
    result_file = lyrics_dir / "segments.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    if logger:
        logger.info(f"Lyrics detection complete: {len(lyric_segments)} segments found")
        logger.info(f"Results saved to: {result_file}")
    
    return result


if __name__ == "__main__":
    print("This is a library module. Use lyrics_detection.py or bias_injection.py for main entry point.")
