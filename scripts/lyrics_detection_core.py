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
            if max_similarity > 0.4:  # 40% word overlap
                duration = block1['end'] - block1['start']
                if duration >= self.min_duration:
                    lyric_segments.append({
                        'start': block1['start'],
                        'end': block1['end'],
                        'confidence': float(max_similarity),
                        'type': 'lyric',
                        'detection_method': 'transcript_pattern'
                    })
        
        return lyric_segments
    
    def merge_detections(
        self,
        audio_detections: List[Dict],
        transcript_detections: List[Dict]
    ) -> List[Dict]:
        """
        Merge and consolidate detections from multiple methods
        
        Args:
            audio_detections: Detections from audio features
            transcript_detections: Detections from transcript patterns
            
        Returns:
            Merged list of lyric segments
        """
        all_detections = audio_detections + transcript_detections
        
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
