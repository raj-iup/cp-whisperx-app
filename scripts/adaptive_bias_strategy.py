#!/usr/bin/env python3
"""
adaptive_bias_strategy.py - Phase 5: Dynamic Strategy Switching

Dynamically switches bias strategies mid-transcription based on:
- Complexity of current scene
- Recognition accuracy in real-time
- Available resources

This is the most advanced bias strategy that adapts in real-time.
"""

import sys
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import deque


class BiasStrategy(Enum):
    """Available bias strategies for dynamic switching"""
    GLOBAL = "global"
    HYBRID = "hybrid"
    CHUNKED_WINDOWS = "chunked_windows"


@dataclass
class SceneMetrics:
    """Metrics for current scene/segment"""
    start_time: float
    end_time: float
    num_speakers: int = 0
    speech_rate: float = 0.0  # words per second
    confidence_avg: float = 0.0  # average transcription confidence
    num_unique_terms: int = 0  # unique named entities
    overlapping_speech: bool = False


@dataclass
class PerformanceMetrics:
    """Real-time performance tracking"""
    processing_time: float = 0.0
    accuracy_estimate: float = 0.0
    memory_usage_mb: float = 0.0
    segments_processed: int = 0
    corrections_made: int = 0


@dataclass
class AdaptiveState:
    """State for adaptive strategy selection"""
    current_strategy: BiasStrategy = BiasStrategy.HYBRID
    strategy_history: List[Tuple[float, BiasStrategy]] = field(default_factory=list)
    recent_accuracies: deque = field(default_factory=lambda: deque(maxlen=10))
    recent_complexities: deque = field(default_factory=lambda: deque(maxlen=10))
    switch_count: int = 0
    last_switch_time: float = 0.0


class AdaptiveBiasStrategy:
    """
    Phase 5: Dynamic strategy switching during transcription
    
    Monitors transcription progress and switches strategies based on:
    - Scene complexity changes
    - Recognition accuracy drops
    - Resource availability
    - Processing time constraints
    """
    
    def __init__(
        self,
        initial_strategy: BiasStrategy = BiasStrategy.HYBRID,
        min_switch_interval: float = 60.0,  # Don't switch more than once per minute
        accuracy_threshold: float = 0.75,    # Switch if accuracy drops below
        complexity_threshold: float = 0.7,   # Switch if complexity rises above
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize adaptive bias strategy
        
        Args:
            initial_strategy: Starting strategy
            min_switch_interval: Minimum seconds between strategy switches
            accuracy_threshold: Accuracy below which we escalate strategy
            complexity_threshold: Complexity above which we escalate strategy
            logger: Logger instance
        """
        self.state = AdaptiveState(current_strategy=initial_strategy)
        self.min_switch_interval = min_switch_interval
        self.accuracy_threshold = accuracy_threshold
        self.complexity_threshold = complexity_threshold
        self.logger = logger or logging.getLogger(__name__)
        
        # Strategy hierarchy (low to high accuracy/cost)
        self.strategy_hierarchy = [
            BiasStrategy.GLOBAL,
            BiasStrategy.HYBRID,
            BiasStrategy.CHUNKED_WINDOWS
        ]
        
        self.logger.info(f"Adaptive bias strategy initialized: {initial_strategy.value}")
    
    def should_switch_strategy(
        self,
        scene_metrics: SceneMetrics,
        performance_metrics: PerformanceMetrics,
        current_time: float
    ) -> Tuple[bool, Optional[BiasStrategy], List[str]]:
        """
        Determine if strategy should be switched
        
        Args:
            scene_metrics: Current scene characteristics
            performance_metrics: Real-time performance data
            current_time: Current transcription timestamp
            
        Returns:
            Tuple of (should_switch, new_strategy, reasoning)
        """
        reasoning = []
        
        # Check minimum switch interval
        time_since_switch = current_time - self.state.last_switch_time
        if time_since_switch < self.min_switch_interval:
            return False, None, []
        
        # Calculate scene complexity
        complexity = self._calculate_scene_complexity(scene_metrics)
        self.state.recent_complexities.append(complexity)
        
        # Track accuracy
        self.state.recent_accuracies.append(performance_metrics.accuracy_estimate)
        
        current_strategy = self.state.current_strategy
        new_strategy = None
        
        # Decision logic: Escalate or de-escalate?
        
        # 1. Check if accuracy is dropping
        if len(self.state.recent_accuracies) >= 3:
            avg_accuracy = sum(self.state.recent_accuracies) / len(self.state.recent_accuracies)
            
            if avg_accuracy < self.accuracy_threshold:
                # Accuracy too low, escalate to more accurate strategy
                new_strategy = self._escalate_strategy(current_strategy)
                if new_strategy != current_strategy:
                    reasoning.append(f"Low accuracy ({avg_accuracy:.2f} < {self.accuracy_threshold})")
                    reasoning.append(f"Escalating: {current_strategy.value} → {new_strategy.value}")
                    return True, new_strategy, reasoning
        
        # 2. Check if complexity is high
        if complexity > self.complexity_threshold:
            # High complexity scene, use more accurate strategy
            new_strategy = self._escalate_strategy(current_strategy)
            if new_strategy != current_strategy:
                reasoning.append(f"High scene complexity ({complexity:.2f})")
                reasoning.append(f"Escalating: {current_strategy.value} → {new_strategy.value}")
                return True, new_strategy, reasoning
        
        # 3. Check if we can de-escalate to save time
        if complexity < 0.4 and len(self.state.recent_accuracies) >= 5:
            avg_accuracy = sum(self.state.recent_accuracies) / len(self.state.recent_accuracies)
            
            if avg_accuracy > 0.85:
                # Low complexity + good accuracy = can use simpler strategy
                new_strategy = self._de_escalate_strategy(current_strategy)
                if new_strategy != current_strategy:
                    reasoning.append(f"Low complexity ({complexity:.2f}), good accuracy ({avg_accuracy:.2f})")
                    reasoning.append(f"De-escalating: {current_strategy.value} → {new_strategy.value}")
                    return True, new_strategy, reasoning
        
        # 4. Check for special scene characteristics
        if scene_metrics.overlapping_speech and current_strategy != BiasStrategy.CHUNKED_WINDOWS:
            # Overlapping speech is hard, use best strategy
            reasoning.append("Overlapping speech detected")
            reasoning.append(f"Escalating to chunked_windows for accuracy")
            return True, BiasStrategy.CHUNKED_WINDOWS, reasoning
        
        if scene_metrics.num_speakers > 4 and current_strategy == BiasStrategy.GLOBAL:
            # Many speakers, need better strategy
            reasoning.append(f"Many speakers ({scene_metrics.num_speakers})")
            reasoning.append("Escalating to hybrid")
            return True, BiasStrategy.HYBRID, reasoning
        
        # No switch needed
        return False, None, []
    
    def apply_strategy_switch(
        self,
        new_strategy: BiasStrategy,
        current_time: float,
        reasoning: List[str]
    ):
        """
        Apply strategy switch and update state
        
        Args:
            new_strategy: New strategy to switch to
            current_time: Current time in transcription
            reasoning: Reasons for the switch
        """
        old_strategy = self.state.current_strategy
        
        self.logger.info(f"Strategy switch at {current_time:.1f}s: {old_strategy.value} → {new_strategy.value}")
        for reason in reasoning:
            self.logger.info(f"  - {reason}")
        
        # Update state
        self.state.strategy_history.append((current_time, new_strategy))
        self.state.current_strategy = new_strategy
        self.state.switch_count += 1
        self.state.last_switch_time = current_time
    
    def _calculate_scene_complexity(self, scene_metrics: SceneMetrics) -> float:
        """
        Calculate complexity score for current scene (0-1)
        
        Factors:
        - Number of speakers (more = higher complexity)
        - Speech rate (faster = higher complexity)
        - Unique named entities (more = higher complexity)
        - Overlapping speech (yes = higher complexity)
        """
        # Normalize each factor
        speaker_score = min(scene_metrics.num_speakers / 5, 1.0)
        speech_rate_score = min(scene_metrics.speech_rate / 3.0, 1.0)
        entities_score = min(scene_metrics.num_unique_terms / 10, 1.0)
        overlap_score = 1.0 if scene_metrics.overlapping_speech else 0.0
        
        # Weighted average
        complexity = (
            speaker_score * 0.3 +
            speech_rate_score * 0.2 +
            entities_score * 0.3 +
            overlap_score * 0.2
        )
        
        return complexity
    
    def _escalate_strategy(self, current: BiasStrategy) -> BiasStrategy:
        """Move up the strategy hierarchy"""
        try:
            current_idx = self.strategy_hierarchy.index(current)
            if current_idx < len(self.strategy_hierarchy) - 1:
                return self.strategy_hierarchy[current_idx + 1]
        except ValueError:
            pass
        return current
    
    def _de_escalate_strategy(self, current: BiasStrategy) -> BiasStrategy:
        """Move down the strategy hierarchy"""
        try:
            current_idx = self.strategy_hierarchy.index(current)
            if current_idx > 0:
                return self.strategy_hierarchy[current_idx - 1]
        except ValueError:
            pass
        return current
    
    def get_strategy_for_segment(
        self,
        segment_start: float,
        segment_end: float,
        scene_metrics: Optional[SceneMetrics] = None,
        performance_metrics: Optional[PerformanceMetrics] = None
    ) -> BiasStrategy:
        """
        Get appropriate strategy for a specific segment
        
        This is the main method called during transcription
        
        Args:
            segment_start: Segment start time
            segment_end: Segment end time
            scene_metrics: Optional scene characteristics
            performance_metrics: Optional performance data
            
        Returns:
            BiasStrategy to use for this segment
        """
        current_time = (segment_start + segment_end) / 2
        
        # If we have metrics, check if we should switch
        if scene_metrics and performance_metrics:
            should_switch, new_strategy, reasoning = self.should_switch_strategy(
                scene_metrics,
                performance_metrics,
                current_time
            )
            
            if should_switch and new_strategy:
                self.apply_strategy_switch(new_strategy, current_time, reasoning)
        
        return self.state.current_strategy
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about adaptive strategy behavior"""
        strategy_times = {}
        
        # Calculate time spent in each strategy
        history = [(0.0, self.state.current_strategy)] + self.state.strategy_history
        for i in range(len(history) - 1):
            time1, strategy1 = history[i]
            time2, strategy2 = history[i + 1]
            duration = time2 - time1
            
            strategy_name = strategy1.value
            strategy_times[strategy_name] = strategy_times.get(strategy_name, 0.0) + duration
        
        return {
            "total_switches": self.state.switch_count,
            "current_strategy": self.state.current_strategy.value,
            "strategy_history": [
                {"time": t, "strategy": s.value}
                for t, s in self.state.strategy_history
            ],
            "time_per_strategy": strategy_times,
            "avg_complexity": (
                sum(self.state.recent_complexities) / len(self.state.recent_complexities)
                if self.state.recent_complexities else 0.0
            ),
            "avg_accuracy": (
                sum(self.state.recent_accuracies) / len(self.state.recent_accuracies)
                if self.state.recent_accuracies else 0.0
            )
        }


class AdaptiveTranscriptionMonitor:
    """
    Monitors transcription progress and provides metrics for adaptive strategy
    
    This can be integrated into the main transcription pipeline
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.segments_processed = []
        self.start_time = time.time()
    
    def analyze_segment(
        self,
        segment: Dict,
        transcription_result: Dict
    ) -> Tuple[SceneMetrics, PerformanceMetrics]:
        """
        Analyze a transcribed segment to extract metrics
        
        Args:
            segment: Original segment data
            transcription_result: Whisper transcription result
            
        Returns:
            Tuple of (SceneMetrics, PerformanceMetrics)
        """
        # Extract scene metrics
        scene_metrics = SceneMetrics(
            start_time=segment.get('start', 0.0),
            end_time=segment.get('end', 0.0),
            num_speakers=self._count_speakers(transcription_result),
            speech_rate=self._calculate_speech_rate(transcription_result),
            confidence_avg=self._average_confidence(transcription_result),
            num_unique_terms=self._count_unique_terms(transcription_result),
            overlapping_speech=self._detect_overlapping_speech(transcription_result)
        )
        
        # Extract performance metrics
        performance_metrics = PerformanceMetrics(
            processing_time=time.time() - self.start_time,
            accuracy_estimate=scene_metrics.confidence_avg,  # Use confidence as proxy
            segments_processed=len(self.segments_processed),
            corrections_made=0  # Would come from bias correction stage
        )
        
        self.segments_processed.append(segment)
        
        return scene_metrics, performance_metrics
    
    def _count_speakers(self, result: Dict) -> int:
        """Count unique speakers in result"""
        speakers = set()
        for seg in result.get('segments', []):
            if 'speaker' in seg:
                speakers.add(seg['speaker'])
        return len(speakers) if speakers else 1
    
    def _calculate_speech_rate(self, result: Dict) -> float:
        """Calculate words per second"""
        segments = result.get('segments', [])
        if not segments:
            return 0.0
        
        total_words = sum(len(seg.get('text', '').split()) for seg in segments)
        total_time = segments[-1].get('end', 0) - segments[0].get('start', 0)
        
        return total_words / total_time if total_time > 0 else 0.0
    
    def _average_confidence(self, result: Dict) -> float:
        """Calculate average transcription confidence"""
        segments = result.get('segments', [])
        if not segments:
            return 0.0
        
        confidences = [
            seg.get('confidence', seg.get('avg_logprob', 0.0))
            for seg in segments
        ]
        
        return sum(confidences) / len(confidences) if confidences else 0.0
    
    def _count_unique_terms(self, result: Dict) -> int:
        """Count unique named entities (simple word count for now)"""
        segments = result.get('segments', [])
        unique_words = set()
        
        for seg in segments:
            text = seg.get('text', '')
            # Simple heuristic: capitalized words are likely named entities
            words = text.split()
            for word in words:
                if word and word[0].isupper():
                    unique_words.add(word.lower())
        
        return len(unique_words)
    
    def _detect_overlapping_speech(self, result: Dict) -> bool:
        """Detect if there's overlapping speech"""
        segments = result.get('segments', [])
        
        # Check for temporal overlaps
        for i in range(len(segments) - 1):
            seg1 = segments[i]
            seg2 = segments[i + 1]
            
            if seg1.get('end', 0) > seg2.get('start', 0):
                return True
        
        return False


def main():
    """Demo/test of adaptive bias strategy"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Phase 5: Adaptive Bias Strategy (Dynamic Switching)"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run demo simulation"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    if args.demo:
        logger.info("=" * 70)
        logger.info("ADAPTIVE BIAS STRATEGY DEMO")
        logger.info("=" * 70)
        
        # Initialize adaptive strategy
        adaptive = AdaptiveBiasStrategy(
            initial_strategy=BiasStrategy.HYBRID,
            logger=logger
        )
        
        # Simulate different scenes
        scenes = [
            # Scene 1: Simple dialogue (2 speakers, normal pace)
            SceneMetrics(0, 60, num_speakers=2, speech_rate=1.5, confidence_avg=0.85, num_unique_terms=3),
            
            # Scene 2: Complex scene (4 speakers, fast pace, many names)
            SceneMetrics(60, 120, num_speakers=4, speech_rate=2.5, confidence_avg=0.70, num_unique_terms=8),
            
            # Scene 3: Overlapping speech (chaos!)
            SceneMetrics(120, 180, num_speakers=5, speech_rate=3.0, confidence_avg=0.65, num_unique_terms=10, overlapping_speech=True),
            
            # Scene 4: Back to simple
            SceneMetrics(180, 240, num_speakers=2, speech_rate=1.5, confidence_avg=0.88, num_unique_terms=4),
        ]
        
        logger.info("")
        logger.info("Simulating transcription with adaptive strategy...")
        logger.info("")
        
        for i, scene in enumerate(scenes, 1):
            logger.info(f"Scene {i}: {scene.start_time:.0f}-{scene.end_time:.0f}s")
            
            # Create performance metrics
            perf = PerformanceMetrics(
                accuracy_estimate=scene.confidence_avg,
                segments_processed=i
            )
            
            # Get strategy for this scene
            strategy = adaptive.get_strategy_for_segment(
                scene.start_time,
                scene.end_time,
                scene,
                perf
            )
            
            logger.info(f"  Strategy: {strategy.value}")
            logger.info("")
        
        # Print statistics
        stats = adaptive.get_statistics()
        logger.info("=" * 70)
        logger.info("FINAL STATISTICS")
        logger.info("=" * 70)
        logger.info(f"Total switches: {stats['total_switches']}")
        logger.info(f"Final strategy: {stats['current_strategy']}")
        logger.info(f"Average complexity: {stats['avg_complexity']:.2f}")
        logger.info(f"Average accuracy: {stats['avg_accuracy']:.2f}")
        logger.info("")
        logger.info("Time per strategy:")
        for strategy, time_spent in stats['time_per_strategy'].items():
            logger.info(f"  {strategy}: {time_spent:.1f}s")
        logger.info("=" * 70)
    
    else:
        logger.info("Use --demo to run a demonstration")
        logger.info("This module is meant to be imported and used in the transcription pipeline")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
