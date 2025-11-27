#!/usr/bin/env python3
"""
Hallucination Removal Post-Processor

Removes Whisper hallucinations from transcripts:
1. Looping/Repetition hallucinations (same text repeated many times)
2. Non-speech hallucinations (filler words in silence)
3. Excessive repetition (suspicious patterns)

Based on research: "Whisper sometimes repeats a word or phrase ad nauseam"
"""

import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from collections import Counter

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Add project root
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class HallucinationRemover:
    """Detect and remove Whisper hallucinations from transcripts"""
    
    def __init__(
        self,
        loop_threshold: int = 3,
        max_repeats: int = 2,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize hallucination remover
        
        Args:
            loop_threshold: Min consecutive identical segments to consider loop
            max_repeats: Max allowed consecutive identical segments
            logger: Logger instance
        """
        self.loop_threshold = loop_threshold
        self.max_repeats = max_repeats
        self.logger = logger or logging.getLogger(__name__)
        
    def detect_looping_hallucinations(
        self,
        segments: List[Dict]
    ) -> List[Tuple[int, int, str]]:
        """
        Detect looping hallucinations (same text repeated many times)
        
        Args:
            segments: List of transcript segments
            
        Returns:
            List of (start_idx, end_idx, repeated_text) tuples
        """
        loops = []
        i = 0
        
        while i < len(segments):
            current_text = segments[i].get('text', '').strip()
            if not current_text:
                i += 1
                continue
            
            # Count consecutive identical segments
            repeat_count = 1
            j = i + 1
            
            while j < len(segments):
                next_text = segments[j].get('text', '').strip()
                if next_text == current_text:
                    repeat_count += 1
                    j += 1
                else:
                    break
            
            # If repeats exceed threshold, it's likely a hallucination
            if repeat_count >= self.loop_threshold:
                loops.append((i, j - 1, current_text))
                self.logger.warning(
                    f"Looping hallucination detected: '{current_text}' "
                    f"repeated {repeat_count} times (segments {i}-{j-1})"
                )
                i = j
            else:
                i += 1
        
        return loops
    
    def detect_suspicious_patterns(
        self,
        segments: List[Dict]
    ) -> List[int]:
        """
        Detect suspicious patterns that may indicate hallucinations
        
        Args:
            segments: List of transcript segments
            
        Returns:
            List of suspicious segment indices
        """
        suspicious = []
        
        # Common hallucination patterns in Whisper
        hallucination_phrases = {
            'thank you',
            'thanks for watching',
            'subscribe',
            'like and subscribe',
            'so',
            'okay',
            'uh',
            'um',
            'बलल',  # From current example
            'ना ना ना',
            'हा हा हा',
        }
        
        for idx, seg in enumerate(segments):
            text = seg.get('text', '').strip().lower()
            
            # Check for common hallucination phrases
            if text in hallucination_phrases:
                # Check if it's isolated (no context)
                has_context = False
                if idx > 0 and segments[idx - 1].get('text', '').strip():
                    has_context = True
                if idx < len(segments) - 1 and segments[idx + 1].get('text', '').strip():
                    has_context = True
                
                if not has_context:
                    suspicious.append(idx)
                    self.logger.debug(
                        f"Suspicious isolated phrase at segment {idx}: '{text}'"
                    )
        
        return suspicious
    
    def remove_looping_hallucinations(
        self,
        segments: List[Dict],
        loops: List[Tuple[int, int, str]]
    ) -> List[Dict]:
        """
        Remove looping hallucinations from segments
        
        Args:
            segments: List of transcript segments
            loops: List of detected loops (start_idx, end_idx, text)
            
        Returns:
            Cleaned segments with loops reduced
        """
        if not loops:
            return segments
        
        cleaned = []
        skip_until = -1
        
        for i, seg in enumerate(segments):
            # Skip segments that are part of a removed loop
            if i < skip_until:
                continue
            
            # Check if this segment starts a loop
            is_loop_start = False
            for loop_start, loop_end, loop_text in loops:
                if i == loop_start:
                    is_loop_start = True
                    # Keep only max_repeats occurrences
                    for j in range(min(self.max_repeats, loop_end - loop_start + 1)):
                        if loop_start + j < len(segments):
                            cleaned.append(segments[loop_start + j])
                    
                    # Skip the rest of the loop
                    skip_until = loop_end + 1
                    
                    removed_count = (loop_end - loop_start + 1) - self.max_repeats
                    if removed_count > 0:
                        self.logger.info(
                            f"Removed {removed_count} hallucinated repetitions "
                            f"of '{loop_text}' (kept {self.max_repeats})"
                        )
                    break
            
            if not is_loop_start and i >= skip_until:
                cleaned.append(seg)
        
        return cleaned
    
    def analyze_segments(
        self,
        segments: List[Dict]
    ) -> Dict:
        """
        Analyze segments for hallucination statistics
        
        Args:
            segments: List of transcript segments
            
        Returns:
            Analysis results dictionary
        """
        if not segments:
            return {
                'total_segments': 0,
                'unique_texts': 0,
                'most_common': [],
                'repetition_rate': 0.0
            }
        
        texts = [seg.get('text', '').strip() for seg in segments if seg.get('text', '').strip()]
        text_counts = Counter(texts)
        
        # Find most repeated texts
        most_common = text_counts.most_common(10)
        
        # Calculate repetition rate
        unique_texts = len(text_counts)
        total_texts = len(texts)
        repetition_rate = 1.0 - (unique_texts / total_texts) if total_texts > 0 else 0.0
        
        return {
            'total_segments': len(segments),
            'total_texts': total_texts,
            'unique_texts': unique_texts,
            'most_common': most_common,
            'repetition_rate': repetition_rate
        }
    
    def process_segments(
        self,
        segments: List[Dict]
    ) -> Tuple[List[Dict], Dict]:
        """
        Process segments to remove hallucinations
        
        Args:
            segments: List of transcript segments
            
        Returns:
            Tuple of (cleaned_segments, stats)
        """
        if not segments:
            return segments, {'removed': 0, 'loops_detected': 0}
        
        original_count = len(segments)
        
        # Analyze before cleaning
        before_stats = self.analyze_segments(segments)
        self.logger.info(f"Before cleaning: {original_count} segments")
        self.logger.info(f"  Unique texts: {before_stats['unique_texts']}")
        self.logger.info(f"  Repetition rate: {before_stats['repetition_rate']:.2%}")
        
        # Detect looping hallucinations
        loops = self.detect_looping_hallucinations(segments)
        
        # Remove loops
        cleaned = self.remove_looping_hallucinations(segments, loops)
        
        # Analyze after cleaning
        after_stats = self.analyze_segments(cleaned)
        removed_count = original_count - len(cleaned)
        
        self.logger.info(f"After cleaning: {len(cleaned)} segments")
        self.logger.info(f"  Removed: {removed_count} hallucinated segments")
        self.logger.info(f"  Unique texts: {after_stats['unique_texts']}")
        self.logger.info(f"  Repetition rate: {after_stats['repetition_rate']:.2%}")
        
        stats = {
            'original_count': original_count,
            'cleaned_count': len(cleaned),
            'removed_count': removed_count,
            'loops_detected': len(loops),
            'loops_removed': loops,
            'before_stats': before_stats,
            'after_stats': after_stats
        }
        
        return cleaned, stats


def main():
    """Main entry point for hallucination removal stage"""
    
    # Import here to avoid issues when used as library
    from shared.logger import PipelineLogger
    from shared.stage_utils import StageIO
    from shared.config import load_config
    
    # Setup stage I/O
    stage_io = StageIO("hallucination_removal")
    
    # Setup logger
    log_file = stage_io.get_log_path()
    logger = PipelineLogger("hallucination_removal", log_file)
    
    logger.info("=" * 70)
    logger.info("HALLUCINATION REMOVAL STAGE - Clean Transcripts")
    logger.info("=" * 70)
    logger.info(f"Output base: {stage_io.output_base}")
    logger.info(f"Stage directory: {stage_io.stage_dir}")
    
    # Load configuration
    config_path = stage_io.output_base / f".{stage_io.output_base.name}.env"
    if not config_path.exists():
        config_path = Path("config/.env.pipeline")
    
    logger.info(f"Loading config from: {config_path}")
    config = load_config(config_path)
    
    # Check if hallucination removal is enabled
    enabled = config.get('HALLUCINATION_REMOVAL_ENABLED', 'true').lower() == 'true'
    if not enabled:
        logger.info("Hallucination removal is disabled - skipping")
        # Copy segments as-is
        segments = stage_io.load_json("segments.json", from_stage="whisperx_asr")
        stage_io.save_json(segments, "segments.json")
        logger.info("=" * 70)
        return 0
    
    # Load segments from ASR stage
    logger.info("Loading segments from WhisperX ASR stage...")
    try:
        data = stage_io.load_json("segments.json", from_stage="whisperx_asr")
    except Exception as e:
        logger.error(f"Failed to load segments: {e}")
        return 1
    
    # Extract segments and metadata
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
    
    # Initialize hallucination remover
    loop_threshold = int(config.get('HALLUCINATION_LOOP_THRESHOLD', '3'))
    max_repeats = int(config.get('HALLUCINATION_MAX_REPEATS', '2'))
    
    remover = HallucinationRemover(
        loop_threshold=loop_threshold,
        max_repeats=max_repeats,
        logger=logger
    )
    
    # Process segments
    logger.info("Processing segments for hallucination removal...")
    cleaned_segments, stats = remover.process_segments(segments)
    
    # Save cleaned segments
    output_data = metadata.copy()
    output_data['segments'] = cleaned_segments
    output_data['hallucination_removal'] = stats
    
    stage_io.save_json(output_data, "segments.json")
    
    # Save statistics
    stats_file = stage_io.stage_dir / "hallucination_stats.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    logger.info(f"Statistics saved to: {stats_file}")
    
    # Log summary
    logger.info("")
    logger.info("=" * 70)
    logger.info("HALLUCINATION REMOVAL SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Original segments: {stats['original_count']}")
    logger.info(f"Cleaned segments: {stats['cleaned_count']}")
    logger.info(f"Removed segments: {stats['removed_count']}")
    logger.info(f"Loops detected: {stats['loops_detected']}")
    
    if stats['loops_removed']:
        logger.info("")
        logger.info("Detected loops:")
        for start_idx, end_idx, text in stats['loops_removed']:
            count = end_idx - start_idx + 1
            logger.info(f"  • '{text}' x {count} (segments {start_idx}-{end_idx})")
    
    logger.info("=" * 70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
