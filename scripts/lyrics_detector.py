#!/usr/bin/env python3
"""
Lyrics Detection and Optimization for ASR

Detects song/music segments and applies optimized ASR parameters.
Phase 3, Task 3: Separate handling for lyrics vs dialogue.

Architecture:
- Detect music/song segments using audio analysis
- Apply different ASR parameters for lyrics
- Handle repetitive patterns common in songs
- Improve lyric transcription accuracy

Expected Impact: +2-3% accuracy on overall content
"""

# Standard library
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

# Third-party
import statistics

# Add project root to path
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.logger import PipelineLogger
from shared.config import Config

# Local
from shared.logger import get_logger
logger = get_logger(__name__)


@dataclass
class LyricsSegment:
    """A detected lyrics/music segment."""
    start: float
    end: float
    confidence: float
    segment_type: str  # 'dialogue', 'music', 'lyrics', 'mixed'


class LyricsDetector:
    """
    Lyrics and music detection for optimized ASR.
    
    Workflow:
    1. Analyze audio for music/song indicators:
       - Energy patterns (music has sustained energy)
       - Repetition (songs have repeated sections)
       - Pitch stability (singing vs speaking)
    2. Classify segments as dialogue, music, or lyrics
    3. Apply appropriate ASR parameters per type
    
    Configuration:
    - LYRICS_DETECTION_ENABLED: Enable/disable (default: false)
    - LYRICS_MUSIC_THRESHOLD: Confidence threshold for music (default: 0.7)
    - LYRICS_BEAM_SIZE: Beam size for lyrics (default: 12)
    - LYRICS_TEMPERATURE: Temperature for lyrics (default: 0.1)
    - LYRICS_ALLOW_REPETITION: Allow repetition in lyrics (default: true)
    """
    
    def __init__(self, config: Config, logger: logging.Logger: PipelineLogger):
        """Initialize lyrics detector."""
        self.config = config
        self.logger = logger
        
        # Configuration
        self.enabled = config.get('LYRICS_DETECTION_ENABLED', 'false').lower() == 'true'
        self.music_threshold = float(config.get('LYRICS_MUSIC_THRESHOLD', '0.7'))
        self.beam_size = int(config.get('LYRICS_BEAM_SIZE', '12'))
        self.temperature = float(config.get('LYRICS_TEMPERATURE', '0.1'))
        self.allow_repetition = config.get('LYRICS_ALLOW_REPETITION', 'true').lower() == 'true'
        
        self.detected_segments: List[LyricsSegment] = []
        
        self.logger.info(f"Lyrics detector initialized: enabled={self.enabled}")
        if self.enabled:
            self.logger.info(f"  Music threshold: {self.music_threshold}")
            self.logger.info(f"  Lyrics beam size: {self.beam_size}")
            self.logger.info(f"  Allow repetition: {self.allow_repetition}")
    
    def is_enabled(self) -> bool:
        """Check if lyrics detection is enabled."""
        return self.enabled
    
    def detect_from_transcript(self, segments: List[Dict]) -> List[LyricsSegment]:
        """
        Detect lyrics from transcript characteristics.
        
        Heuristics for lyrics:
        1. Repetitive text patterns (na na na, la la la)
        2. Rhyming patterns
        3. Higher compression ratios (acceptable for songs)
        4. Longer sustained segments
        
        Args:
            segments: List of transcript segments
            
        Returns:
            List of detected lyrics segments
        """
        self.logger.info(f"Analyzing {len(segments)} segments for lyrics...")
        
        detected = []
        
        for seg in segments:
            text = seg.get('text', '').lower().strip()
            start = seg.get('start', 0.0)
            end = seg.get('end', 0.0)
            
            # Calculate lyrics indicators
            confidence = self._calculate_lyrics_confidence(seg, text)
            
            # Classify segment
            if confidence >= self.music_threshold:
                segment_type = 'lyrics'
            elif confidence >= 0.5:
                segment_type = 'mixed'
            else:
                segment_type = 'dialogue'
            
            detected.append(LyricsSegment(
                start=start,
                end=end,
                confidence=confidence,
                segment_type=segment_type
            ))
        
        # Merge adjacent lyrics segments
        merged = self._merge_adjacent_segments(detected)
        
        self.detected_segments = merged
        
        # Statistics
        lyrics_count = sum(1 for s in merged if s.segment_type == 'lyrics')
        dialogue_count = sum(1 for s in merged if s.segment_type == 'dialogue')
        
        self.logger.info(f"  Detected: {lyrics_count} lyrics, {dialogue_count} dialogue segments")
        
        return merged
    
    def _calculate_lyrics_confidence(self, segment: Dict, text: str) -> float:
        """
        Calculate confidence that segment contains lyrics.
        
        Indicators:
        1. Repetitive words (na na, la la, oh oh)
        2. Musical exclamations (aah, ooh, hmm)
        3. High compression ratio (songs compress more)
        4. Specific patterns (repeated phrases)
        """
        confidence = 0.0
        
        if not text:
            return 0.0
        
        words = text.split()
        
        # 1. Repetition score
        if len(words) > 1:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio < 0.5:  # >50% repetition
                confidence += 0.4
            elif unique_ratio < 0.7:  # 30-50% repetition
                confidence += 0.2
        
        # 2. Musical words
        musical_words = {'na', 'la', 'aah', 'ooh', 'hmm', 'oh', 'ah', 'eh'}
        musical_count = sum(1 for w in words if w.strip(',.!?') in musical_words)
        if musical_count > 0:
            confidence += min(0.3, musical_count * 0.1)
        
        # 3. Compression ratio (songs often have higher compression)
        compression = segment.get('compression_ratio', 1.5)
        if compression > 2.5:
            confidence += 0.2
        elif compression > 2.0:
            confidence += 0.1
        
        # 4. Pattern detection (repeated phrases)
        if self._has_repeated_phrases(words):
            confidence += 0.2
        
        return min(1.0, confidence)
    
    def _has_repeated_phrases(self, words: List[str]) -> bool:
        """Check for repeated 2-3 word phrases."""
        if len(words) < 4:
            return False
        
        # Check 2-word phrases
        bigrams = [' '.join(words[i:i+2]) for i in range(len(words)-1)]
        if len(bigrams) != len(set(bigrams)):  # Has duplicates
            return True
        
        # Check 3-word phrases
        if len(words) >= 6:
            trigrams = [' '.join(words[i:i+3]) for i in range(len(words)-2)]
            if len(trigrams) != len(set(trigrams)):
                return True
        
        return False
    
    def _merge_adjacent_segments(self, segments: List[LyricsSegment], 
                                 max_gap: float = 2.0) -> List[LyricsSegment]:
        """
        Merge adjacent segments of same type.
        
        Args:
            segments: List of segments to merge
            max_gap: Maximum gap between segments to merge (seconds)
            
        Returns:
            List of merged segments
        """
        if not segments:
            return []
        
        merged = []
        current = segments[0]
        
        for next_seg in segments[1:]:
            gap = next_seg.start - current.end
            
            # Merge if same type and close enough
            if (next_seg.segment_type == current.segment_type and 
                gap <= max_gap):
                # Extend current segment
                current = LyricsSegment(
                    start=current.start,
                    end=next_seg.end,
                    confidence=(current.confidence + next_seg.confidence) / 2,
                    segment_type=current.segment_type
                )
            else:
                # Save current and start new
                merged.append(current)
                current = next_seg
        
        # Add final segment
        merged.append(current)
        
        return merged
    
    def get_asr_parameters(self, segment_type: str) -> Dict:
        """
        Get optimized ASR parameters for segment type.
        
        Args:
            segment_type: 'dialogue', 'lyrics', or 'mixed'
            
        Returns:
            Dictionary of WhisperX parameters
        """
        # Base parameters from config
        base_beam = int(self.config.get('WHISPER_BEAM_SIZE', '10'))
        base_temp = float(self.config.get('WHISPER_TEMPERATURE', '0.0'))
        
        if segment_type == 'lyrics':
            # Lyrics parameters: allow more creativity and repetition
            params = {
                'beam_size': self.beam_size,
                'temperature': self.temperature,  # Slightly higher for creativity
                'compression_ratio_threshold': 3.0,  # Allow more compression
                'repetition_penalty': 0.8,  # Lower penalty (songs repeat)
                'no_speech_threshold': 0.6,  # Lower (detect faint singing)
            }
        elif segment_type == 'mixed':
            # Mixed: balance between dialogue and lyrics
            params = {
                'beam_size': (base_beam + self.beam_size) // 2,
                'temperature': 0.05,
                'compression_ratio_threshold': 2.5,
                'repetition_penalty': 0.9,
                'no_speech_threshold': 0.7,
            }
        else:  # dialogue
            # Dialogue: use standard parameters
            params = {
                'beam_size': base_beam,
                'temperature': base_temp,
                'compression_ratio_threshold': 1.8,
                'repetition_penalty': 1.2,
                'no_speech_threshold': 0.8,
            }
        
        return params
    
    def get_segment_type_at_time(self, time: float) -> str:
        """Get segment type at given timestamp."""
        for seg in self.detected_segments:
            if seg.start <= time < seg.end:
                return seg.segment_type
        return 'dialogue'  # Default
    
    def create_report(self) -> Dict:
        """Create lyrics detection report."""
        if not self.detected_segments:
            return {
                'enabled': self.enabled,
                'segments_analyzed': 0,
                'lyrics_detected': False
            }
        
        lyrics_segs = [s for s in self.detected_segments if s.segment_type == 'lyrics']
        dialogue_segs = [s for s in self.detected_segments if s.segment_type == 'dialogue']
        mixed_segs = [s for s in self.detected_segments if s.segment_type == 'mixed']
        
        # Calculate total duration
        lyrics_duration = sum(s.end - s.start for s in lyrics_segs)
        dialogue_duration = sum(s.end - s.start for s in dialogue_segs)
        total_duration = sum(s.end - s.start for s in self.detected_segments)
        
        report = {
            'enabled': self.enabled,
            'total_segments': len(self.detected_segments),
            'lyrics_segments': len(lyrics_segs),
            'dialogue_segments': len(dialogue_segs),
            'mixed_segments': len(mixed_segs),
            'lyrics_duration_seconds': lyrics_duration,
            'dialogue_duration_seconds': dialogue_duration,
            'total_duration_seconds': total_duration,
            'lyrics_percentage': (lyrics_duration / total_duration * 100) if total_duration > 0 else 0,
            'music_threshold': self.music_threshold,
            'lyrics_beam_size': self.beam_size,
            'segments_detail': [
                {
                    'start': s.start,
                    'end': s.end,
                    'duration': s.end - s.start,
                    'type': s.segment_type,
                    'confidence': s.confidence
                }
                for s in lyrics_segs[:10]  # First 10 lyrics segments
            ]
        }
        
        return report
    
    def save_report(self, output_dir: Path) -> None:
        """Save lyrics detection report."""
        report = self.create_report()
        report_file = output_dir / "lyrics_detection_report.json"
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"Lyrics detection report saved: {report_file}")


def main():
    """
    Main entry point for testing lyrics detector.
    
    Usage:
        python lyrics_detector.py <job_dir>
    """
    if len(sys.argv) != 2:
        logger.info("Usage: python lyrics_detector.py <job_dir>")
        sys.exit(1)
    
    job_dir = Path(sys.argv[1])
    
    # Initialize
    logger = PipelineLogger(job_dir, "lyrics", "detection")
    config = Config(PROJECT_ROOT)
    
    detector = LyricsDetector(config, logger: logging.Logger)
    
    # Load transcript
    transcript_file = None
    for pattern in ["*/segments.json", "*/transcript*.json"]:
        matches = list(job_dir.glob(pattern))
        if matches:
            transcript_file = matches[0]
            break
    
    if not transcript_file or not transcript_file.exists():
        logger.error(f"No transcript file found in {job_dir}")
        sys.exit(1)
    
    with open(transcript_file) as f:
        data = json.load(f)
        segments = data.get('segments', [])
    
    logger.info(f"Loaded {len(segments)} segments from {transcript_file}")
    
    # Detect lyrics
    detected = detector.detect_from_transcript(segments)
    
    # Show sample detections
    logger.info("\nSample lyrics segments:")
    lyrics_segs = [s for s in detected if s.segment_type == 'lyrics']
    for i, seg in enumerate(lyrics_segs[:5]):
        logger.info(f"  [{i+1}] {seg.start:.1f}s-{seg.end:.1f}s "
                   f"(conf={seg.confidence:.2f})")
    
    # Save report
    output_dir = job_dir / "analysis"
    output_dir.mkdir(parents=True, exist_ok=True)
    detector.save_report(output_dir)
    
    report = detector.create_report()
    logger.info("Lyrics detection complete!")
    logger.info(f"  Total segments: {report['total_segments']}")
    logger.info(f"  Lyrics segments: {report['lyrics_segments']}")
    logger.info(f"  Lyrics duration: {report['lyrics_duration_seconds']:.1f}s "
               f"({report['lyrics_percentage']:.1f}%)")


if __name__ == "__main__":
    main()
