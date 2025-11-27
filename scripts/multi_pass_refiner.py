#!/usr/bin/env python3
"""
Multi-Pass Refinement System for ASR

Re-processes low-confidence segments with enhanced parameters for improved accuracy.
Phase 3, Task 1: Multi-pass refinement for difficult segments.

Architecture:
- Pass 1: Standard transcription (existing pipeline)
- Pass 2-N: Targeted refinement of low-confidence segments
- Selection: Choose best result based on confidence scores

Expected Impact: +3-5% accuracy improvement on difficult segments
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import statistics

# Add project root to path
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.logger import PipelineLogger
from shared.config import Config


@dataclass
class SegmentConfidence:
    """Confidence metrics for a segment."""
    segment_id: int
    start: float
    end: float
    text: str
    avg_logprob: float
    no_speech_prob: float
    compression_ratio: float
    overall_confidence: float
    needs_refinement: bool


class MultiPassRefiner:
    """
    Multi-pass refinement system for low-confidence ASR segments.
    
    Workflow:
    1. Analyze initial transcription for low-confidence segments
    2. Re-transcribe flagged segments with enhanced parameters
    3. Compare results and select best version
    4. Merge refined segments back into transcript
    
    Configuration:
    - MULTIPASS_ENABLED: Enable/disable multi-pass (default: false)
    - MULTIPASS_CONFIDENCE_THRESHOLD: Threshold for refinement (default: 0.6)
    - MULTIPASS_MAX_ITERATIONS: Max refinement passes (default: 3)
    - MULTIPASS_BEAM_SIZE_INCREMENT: Beam size increase per pass (default: 5)
    - MULTIPASS_MIN_SEGMENT_DURATION: Min segment length (default: 1.0s)
    """
    
    def __init__(self, config: Config, logger: PipelineLogger):
        """Initialize multi-pass refiner with configuration."""
        self.config = config
        self.logger = logger
        
        # Configuration parameters
        self.enabled = config.get('MULTIPASS_ENABLED', 'false').lower() == 'true'
        self.confidence_threshold = float(config.get('MULTIPASS_CONFIDENCE_THRESHOLD', '0.6'))
        self.max_iterations = int(config.get('MULTIPASS_MAX_ITERATIONS', '3'))
        self.beam_size_increment = int(config.get('MULTIPASS_BEAM_SIZE_INCREMENT', '5'))
        self.min_segment_duration = float(config.get('MULTIPASS_MIN_SEGMENT_DURATION', '1.0'))
        
        # Base parameters from config
        self.base_beam_size = int(config.get('WHISPER_BEAM_SIZE', '10'))
        self.base_temperature = config.get('WHISPER_TEMPERATURE', '0.0')
        
        self.logger.info(f"Multi-pass refiner initialized: enabled={self.enabled}")
        if self.enabled:
            self.logger.info(f"  Confidence threshold: {self.confidence_threshold}")
            self.logger.info(f"  Max iterations: {self.max_iterations}")
            self.logger.info(f"  Beam size: {self.base_beam_size} (+{self.beam_size_increment}/pass)")
    
    def is_enabled(self) -> bool:
        """Check if multi-pass refinement is enabled."""
        return self.enabled
    
    def analyze_segments(self, segments: List[Dict]) -> List[SegmentConfidence]:
        """
        Analyze segments and calculate confidence scores.
        
        Args:
            segments: List of WhisperX segments with metadata
            
        Returns:
            List of SegmentConfidence objects with analysis results
        """
        self.logger.info(f"Analyzing {len(segments)} segments for confidence...")
        
        analyzed = []
        for idx, seg in enumerate(segments):
            confidence = self._calculate_segment_confidence(seg, idx)
            analyzed.append(confidence)
        
        # Statistics
        low_conf = sum(1 for c in analyzed if c.needs_refinement)
        avg_conf = statistics.mean(c.overall_confidence for c in analyzed) if analyzed else 0
        
        self.logger.info(f"  Average confidence: {avg_conf:.3f}")
        self.logger.info(f"  Low-confidence segments: {low_conf}/{len(segments)} ({low_conf/len(segments)*100:.1f}%)")
        
        return analyzed
    
    def _calculate_segment_confidence(self, segment: Dict, segment_id: int) -> SegmentConfidence:
        """
        Calculate overall confidence score for a segment.
        
        Confidence factors:
        1. Average log probability (higher is better)
        2. No-speech probability (lower is better)
        3. Compression ratio (closer to 1.0 is better)
        4. Segment duration (very short segments are suspicious)
        
        Returns:
            SegmentConfidence object with calculated metrics
        """
        # Extract metrics from segment
        avg_logprob = segment.get('avg_logprob', -0.5)
        no_speech_prob = segment.get('no_speech_prob', 0.0)
        compression_ratio = segment.get('compression_ratio', 1.5)
        text = segment.get('text', '').strip()
        start = segment.get('start', 0.0)
        end = segment.get('end', 0.0)
        duration = end - start
        
        # Calculate confidence components (0.0 to 1.0 scale)
        
        # 1. Log probability confidence (normalize from -1.0 to 0.0 range)
        logprob_conf = max(0.0, min(1.0, (avg_logprob + 1.0)))
        
        # 2. No-speech confidence (invert: high no-speech = low confidence)
        no_speech_conf = 1.0 - no_speech_prob
        
        # 3. Compression ratio confidence (ideal is 1.0-2.0, penalize >2.4)
        if compression_ratio < 2.0:
            comp_conf = 1.0
        elif compression_ratio < 2.4:
            comp_conf = 0.8
        else:
            comp_conf = 0.5  # High compression = likely hallucination
        
        # 4. Duration confidence (very short segments are suspicious)
        if duration < self.min_segment_duration:
            dur_conf = 0.7
        else:
            dur_conf = 1.0
        
        # 5. Text quality heuristics
        text_conf = self._calculate_text_confidence(text)
        
        # Weighted average (emphasize logprob and no-speech)
        overall_confidence = (
            logprob_conf * 0.35 +
            no_speech_conf * 0.30 +
            comp_conf * 0.20 +
            dur_conf * 0.10 +
            text_conf * 0.05
        )
        
        # Determine if refinement needed
        needs_refinement = (
            overall_confidence < self.confidence_threshold and
            duration >= self.min_segment_duration and
            len(text) > 0
        )
        
        return SegmentConfidence(
            segment_id=segment_id,
            start=start,
            end=end,
            text=text,
            avg_logprob=avg_logprob,
            no_speech_prob=no_speech_prob,
            compression_ratio=compression_ratio,
            overall_confidence=overall_confidence,
            needs_refinement=needs_refinement
        )
    
    def _calculate_text_confidence(self, text: str) -> float:
        """
        Calculate confidence based on text characteristics.
        
        Red flags:
        - Empty or very short text
        - Excessive repetition
        - Non-linguistic patterns
        """
        if not text or len(text) < 3:
            return 0.3
        
        # Check for repetition (e.g., "na na na na na")
        words = text.lower().split()
        if len(words) > 2:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio < 0.5:  # More than 50% repeated words
                return 0.5
        
        return 1.0
    
    def identify_refinement_candidates(self, 
                                       analyzed: List[SegmentConfidence]) -> List[SegmentConfidence]:
        """
        Filter segments that need refinement.
        
        Args:
            analyzed: List of analyzed segments
            
        Returns:
            List of segments needing refinement
        """
        candidates = [seg for seg in analyzed if seg.needs_refinement]
        
        self.logger.info(f"Identified {len(candidates)} segments for refinement:")
        for i, cand in enumerate(candidates[:5]):  # Show first 5
            self.logger.info(f"  [{i+1}] {cand.start:.1f}s-{cand.end:.1f}s: "
                           f"conf={cand.overall_confidence:.3f} text='{cand.text[:50]}'")
        if len(candidates) > 5:
            self.logger.info(f"  ... and {len(candidates)-5} more")
        
        return candidates
    
    def get_refinement_parameters(self, pass_num: int) -> Dict:
        """
        Get enhanced parameters for refinement pass.
        
        Args:
            pass_num: Refinement pass number (1-based)
            
        Returns:
            Dictionary of WhisperX parameters
        """
        # Increase beam size with each pass for more thorough search
        beam_size = self.base_beam_size + (pass_num * self.beam_size_increment)
        
        params = {
            'beam_size': beam_size,
            'best_of': beam_size,  # Match beam size for consistency
            'temperature': 0.0,  # Always use deterministic for refinement
            'patience': 1.5,  # Slightly more patient
            'compression_ratio_threshold': 1.8,  # Stricter
            'logprob_threshold': -0.3,  # Stricter confidence
            'no_speech_threshold': 0.85,  # Stricter silence detection
        }
        
        self.logger.debug(f"Pass {pass_num} parameters: beam_size={beam_size}")
        
        return params
    
    def create_refinement_report(self, 
                                 original_segments: List[Dict],
                                 refined_segments: List[Dict],
                                 original_analysis: List[SegmentConfidence],
                                 refinement_candidates: List[SegmentConfidence]) -> Dict:
        """
        Create a detailed report of the refinement process.
        
        Returns:
            Dictionary with refinement statistics and results
        """
        total_segments = len(original_segments)
        refined_count = len(refinement_candidates)
        
        report = {
            'enabled': self.enabled,
            'total_segments': total_segments,
            'analyzed_segments': len(original_analysis),
            'low_confidence_segments': refined_count,
            'refinement_rate': refined_count / total_segments if total_segments > 0 else 0,
            'confidence_threshold': self.confidence_threshold,
            'average_confidence': statistics.mean(
                a.overall_confidence for a in original_analysis
            ) if original_analysis else 0,
            'low_confidence_average': statistics.mean(
                c.overall_confidence for c in refinement_candidates
            ) if refinement_candidates else 0,
            'refinement_candidates': [
                {
                    'segment_id': c.segment_id,
                    'start': c.start,
                    'end': c.end,
                    'original_text': c.text,
                    'confidence': c.overall_confidence,
                    'avg_logprob': c.avg_logprob,
                    'no_speech_prob': c.no_speech_prob,
                    'compression_ratio': c.compression_ratio,
                }
                for c in refinement_candidates
            ]
        }
        
        return report
    
    def save_report(self, report: Dict, output_dir: Path) -> None:
        """Save refinement report to JSON file."""
        report_file = output_dir / "multipass_refinement_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"Refinement report saved: {report_file}")


def main():
    """
    Main entry point for testing multi-pass refiner.
    
    Usage:
        python multi_pass_refiner.py <job_dir>
    """
    if len(sys.argv) != 2:
        print("Usage: python multi_pass_refiner.py <job_dir>")
        sys.exit(1)
    
    job_dir = Path(sys.argv[1])
    
    # Initialize
    logger = PipelineLogger(job_dir, "multipass", "analysis")
    config = Config(PROJECT_ROOT)
    
    refiner = MultiPassRefiner(config, logger)
    
    # Load segments from a stage output
    segments_file = None
    for pattern in ["*/segments.json", "*/asr_output.json", "*/transcript*.json"]:
        matches = list(job_dir.glob(pattern))
        if matches:
            segments_file = matches[0]
            break
    
    if not segments_file or not segments_file.exists():
        logger.error(f"No segments file found in {job_dir}")
        sys.exit(1)
    
    with open(segments_file) as f:
        data = json.load(f)
        segments = data.get('segments', data.get('results', []))
    
    logger.info(f"Loaded {len(segments)} segments from {segments_file}")
    
    # Analyze segments
    analyzed = refiner.analyze_segments(segments)
    candidates = refiner.identify_refinement_candidates(analyzed)
    
    # Create report
    report = refiner.create_refinement_report(
        segments, segments, analyzed, candidates
    )
    
    # Save report
    output_dir = job_dir / "analysis"
    output_dir.mkdir(parents=True, exist_ok=True)
    refiner.save_report(report, output_dir)
    
    logger.info("Multi-pass analysis complete!")
    logger.info(f"  Total segments: {report['total_segments']}")
    logger.info(f"  Low confidence: {report['low_confidence_segments']}")
    logger.info(f"  Refinement rate: {report['refinement_rate']*100:.1f}%")


if __name__ == "__main__":
    main()
