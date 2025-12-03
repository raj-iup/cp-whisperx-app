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

# Local
from shared.logger import get_logger
logger = get_logger(__name__)

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Add project root
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class HallucinationRemover:
    """
    Detect and remove Whisper hallucinations from transcripts (Phase 2 Enhanced).

    Enhancements:
    - Extended hallucination pattern library
    - Compression ratio analysis
    - Improved sequential duplicate detection
    - Better statistics and reporting
    """

    # Phase 2: Enhanced hallucination patterns (case-insensitive)
    COMMON_PATTERNS = [
        r'^thank you\.?$',
        r'^thanks\.?$',
        r'^thank you for watching\.?$',
        r"^what did you do\??$",
        r"^i'?m sorry\.?$",
        r'^sorry\.?$',
        r'^(uh|um|ah|eh)\.?$',
        r'^subscribe',
        r'^please subscribe',
        r'^like and subscribe',
        r'^click the bell',
        r'^thank you for watching',
        r'^so\.?$',
        r'^okay\.?$',
        r'^बलल',  # Hindi artifacts
        r'^ना ना( ना)*$',  # Repetitive Hindi
        r'^हा हा( हा)*$',  # Repetitive Hindi
    ]

    # Very short segments (likely noise)
    MIN_TEXT_LENGTH = 3

    # Max consecutive repeats (Phase 2 default)
    MAX_CONSECUTIVE_REPEATS = 2

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

        # Phase 2: Compile regex patterns
        import re
        self.patterns = [re.compile(p, re.IGNORECASE) for p in self.COMMON_PATTERNS]

        # Phase 2: Statistics tracking
        self.stats = {
            'total_segments': 0,
            'removed_by_pattern': 0,
            'removed_by_length': 0,
            'removed_by_repetition': 0,
            'removed_by_compression': 0,
        }
        
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

    def is_hallucination_pattern(self, text: str) -> bool:
        """
        Check if text matches known hallucination patterns (Phase 2).

        Args:
            text: Text to check

        Returns:
            True if text matches a hallucination pattern
        """
        text_clean = text.strip().lower()

        for pattern in self.patterns:
            if pattern.match(text_clean):
                return True

        return False

    def is_too_short(self, text: str) -> bool:
        """
        Check if text is suspiciously short (Phase 2).

        Args:
            text: Text to check

        Returns:
            True if text is too short to be legitimate
        """
        import re
        # Remove punctuation and whitespace
        clean_text = re.sub(r'[^\w\s]', '', text).strip()
        return len(clean_text) < self.MIN_TEXT_LENGTH

    def calculate_compression_ratio(self, text: str) -> float:
        """
        Calculate compression ratio to detect repetitive text (Phase 2).

        High ratio = likely hallucination/repetition.

        Args:
            text: Text to analyze

        Returns:
            Compression ratio (higher = more repetitive)
        """
        import zlib

        if not text:
            return 0

        # Compress the text
        try:
            compressed = zlib.compress(text.encode('utf-8'))
            ratio = len(text) / len(compressed) if len(compressed) > 0 else 0
            return ratio
        except:
            return 0

    def remove_sequential_duplicates(self, segments: List[Dict]) -> List[Dict]:
        """
        Remove segments that repeat more than MAX_CONSECUTIVE_REPEATS times (Phase 2).

        Args:
            segments: List of segments

        Returns:
            Filtered segments with duplicates removed
        """
        if not segments:
            return segments

        result = []
        repeat_count = 1
        last_text = None

        for seg in segments:
            text = seg.get('text', '').strip().lower()

            # Empty text - skip
            if not text:
                continue

            # Same as previous
            if text == last_text:
                repeat_count += 1
                if repeat_count <= self.MAX_CONSECUTIVE_REPEATS:
                    result.append(seg)
                else:
                    self.stats['removed_by_repetition'] += 1
                    self.logger.debug(f"Removed duplicate #{repeat_count}: {text[:50]}")
            else:
                repeat_count = 1
                result.append(seg)
                last_text = text

        return result

    def remove_hallucinations_enhanced(self, segments: List[Dict]) -> Tuple[List[Dict], Dict]:
        """
        Enhanced hallucination removal pipeline (Phase 2).

        Applies multiple detection strategies:
        1. Pattern matching for common phrases
        2. Length filtering
        3. Compression ratio analysis
        4. Sequential duplicate removal

        Args:
            segments: List of segments with 'text' field

        Returns:
            Tuple of (filtered segments, statistics)
        """
        if not segments:
            return segments, self.stats

        self.stats['total_segments'] = len(segments)
        filtered = []

        # Step 1: Remove known patterns and short segments
        for seg in segments:
            text = seg.get('text', '').strip()

            # Check for hallucination patterns
            if self.is_hallucination_pattern(text):
                self.stats['removed_by_pattern'] += 1
                self.logger.debug(f"Removed by pattern: {text[:50]}")
                continue

            # Check if too short
            if self.is_too_short(text):
                self.stats['removed_by_length'] += 1
                self.logger.debug(f"Removed by length: {text[:50]}")
                continue

            # Check compression ratio (repetitive text)
            compression = self.calculate_compression_ratio(text)
            if compression > 2.2:  # Threshold from config
                self.stats['removed_by_compression'] += 1
                self.logger.debug(f"Removed by compression ({compression:.2f}): {text[:50]}")
                continue

            filtered.append(seg)

        # Step 2: Remove sequential duplicates
        filtered = self.remove_sequential_duplicates(filtered)

        # Log statistics
        removed = self.stats['total_segments'] - len(filtered)
        if removed > 0:
            self.logger.info(f"🧹 Enhanced hallucination removal: {removed}/{self.stats['total_segments']} segments removed")
            self.logger.info(f"   - By pattern: {self.stats['removed_by_pattern']}")
            self.logger.info(f"   - By length: {self.stats['removed_by_length']}")
            self.logger.info(f"   - By compression: {self.stats['removed_by_compression']}")
            self.logger.info(f"   - By repetition: {self.stats['removed_by_repetition']}")
        else:
            self.logger.debug(f"Enhanced hallucination removal: All {self.stats['total_segments']} segments passed")

        return filtered, self.stats

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
        segments: List[Dict],
        use_enhanced: bool = True
    ) -> Tuple[List[Dict], Dict]:
        """
        Process segments to remove hallucinations.

        Args:
            segments: List of transcript segments
            use_enhanced: Use Phase 2 enhanced detection (default: True)

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

        # Phase 2: Use enhanced removal if enabled
        if use_enhanced:
            self.logger.info("Using Phase 2 enhanced hallucination removal")
            cleaned, enhanced_stats = self.remove_hallucinations_enhanced(segments)

            # Also detect loops for backward compatibility
            loops = self.detect_looping_hallucinations(segments)

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
                'before_stats': before_stats,
                'after_stats': after_stats,
                'enhanced_stats': enhanced_stats,
                'method': 'enhanced'
            }

        else:
            # Original method (backward compatibility)
            self.logger.info("Using original hallucination removal")

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
                'after_stats': after_stats,
                'method': 'original'
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
