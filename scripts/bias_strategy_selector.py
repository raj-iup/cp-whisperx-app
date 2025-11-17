#!/usr/bin/env python3
"""
bias_strategy_selector.py - Phase 4: ML-Based Strategy Selection

Automatically selects the optimal bias strategy based on:
- Audio duration
- Number of unique characters
- Scene change frequency
- Available processing time/resources

Architecture:
- Rule-based decision tree (Phase 4A)
- ML model predictions (Phase 4B - future)
- Resource-aware selection
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class BiasStrategy(Enum):
    """Available bias strategies"""
    GLOBAL = "global"
    HYBRID = "hybrid"
    CHUNKED_WINDOWS = "chunked_windows"
    ADAPTIVE = "adaptive"  # Dynamic switching (Phase 5)


@dataclass
class AudioCharacteristics:
    """Characteristics of the audio/video content"""
    duration_seconds: float
    num_characters: int
    scene_change_frequency: float  # changes per minute
    avg_dialogue_density: float  # words per minute
    complexity_score: float  # 0-1, overall complexity


@dataclass
class SystemResources:
    """Available system resources"""
    device: str  # cpu, cuda, mps
    available_memory_gb: float
    cpu_cores: int
    time_budget_minutes: Optional[float] = None  # None = unlimited


@dataclass
class StrategyRecommendation:
    """Strategy recommendation with reasoning"""
    strategy: BiasStrategy
    confidence: float  # 0-1
    reasoning: List[str]
    estimated_time_minutes: float
    expected_accuracy: float  # 0-1


class BiasStrategySelector:
    """
    Intelligently selects optimal bias strategy based on content and resources
    
    Phase 4A: Rule-based selection (implemented)
    Phase 4B: ML-based selection (future)
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
    
    def select_strategy(
        self,
        audio_chars: AudioCharacteristics,
        system_resources: SystemResources,
        user_preference: Optional[str] = None
    ) -> StrategyRecommendation:
        """
        Select optimal strategy based on characteristics and resources
        
        Args:
            audio_chars: Audio/content characteristics
            system_resources: Available system resources
            user_preference: User override (None = auto-select)
            
        Returns:
            StrategyRecommendation with selected strategy and reasoning
        """
        # User override takes precedence
        if user_preference and user_preference != "auto":
            try:
                strategy = BiasStrategy(user_preference)
                return self._create_recommendation(
                    strategy,
                    confidence=1.0,
                    reasoning=[f"User-specified: {user_preference}"],
                    audio_chars=audio_chars,
                    system_resources=system_resources
                )
            except ValueError:
                self.logger.warning(f"Invalid user preference: {user_preference}, auto-selecting")
        
        # Auto-select based on characteristics
        return self._auto_select_strategy(audio_chars, system_resources)
    
    def _auto_select_strategy(
        self,
        audio_chars: AudioCharacteristics,
        system_resources: SystemResources
    ) -> StrategyRecommendation:
        """
        Auto-select strategy using decision tree
        
        Decision factors (in priority order):
        1. Time budget (if specified)
        2. Content complexity
        3. Audio duration
        4. Number of characters
        5. System resources
        """
        reasoning = []
        
        # Factor 1: Time budget constraint
        if system_resources.time_budget_minutes is not None:
            result = self._select_by_time_budget(
                audio_chars,
                system_resources,
                reasoning
            )
            if result:
                return result
        
        # Factor 2: Content complexity
        if audio_chars.complexity_score > 0.7:
            # High complexity -> use best strategy available
            reasoning.append(f"High complexity ({audio_chars.complexity_score:.2f})")
            
            if system_resources.device in ["cuda", "mps"]:
                # GPU available -> can afford chunked_windows
                reasoning.append(f"GPU available ({system_resources.device})")
                return self._create_recommendation(
                    BiasStrategy.CHUNKED_WINDOWS,
                    confidence=0.9,
                    reasoning=reasoning,
                    audio_chars=audio_chars,
                    system_resources=system_resources
                )
            else:
                # CPU only -> hybrid is best balance
                reasoning.append("CPU only, using hybrid for balance")
                return self._create_recommendation(
                    BiasStrategy.HYBRID,
                    confidence=0.85,
                    reasoning=reasoning,
                    audio_chars=audio_chars,
                    system_resources=system_resources
                )
        
        # Factor 3: Audio duration
        if audio_chars.duration_seconds > 7200:  # > 2 hours
            reasoning.append(f"Long duration ({audio_chars.duration_seconds/3600:.1f}h)")
            
            if system_resources.device in ["cuda", "mps"]:
                # Long + GPU -> chunked_windows handles it well
                reasoning.append("GPU can handle chunked windows for long content")
                return self._create_recommendation(
                    BiasStrategy.CHUNKED_WINDOWS,
                    confidence=0.85,
                    reasoning=reasoning,
                    audio_chars=audio_chars,
                    system_resources=system_resources
                )
            else:
                # Long + CPU -> hybrid is safer
                reasoning.append("CPU: hybrid is more efficient for long content")
                return self._create_recommendation(
                    BiasStrategy.HYBRID,
                    confidence=0.8,
                    reasoning=reasoning,
                    audio_chars=audio_chars,
                    system_resources=system_resources
                )
        
        # Factor 4: Number of characters
        if audio_chars.num_characters > 20:
            reasoning.append(f"Many characters ({audio_chars.num_characters})")
            reasoning.append("Chunked windows better for large cast")
            return self._create_recommendation(
                BiasStrategy.CHUNKED_WINDOWS,
                confidence=0.8,
                reasoning=reasoning,
                audio_chars=audio_chars,
                system_resources=system_resources
            )
        
        # Factor 5: Scene change frequency
        if audio_chars.scene_change_frequency > 4:  # > 4 changes/min
            reasoning.append(f"Frequent scene changes ({audio_chars.scene_change_frequency:.1f}/min)")
            reasoning.append("Chunked windows adapts to scenes")
            return self._create_recommendation(
                BiasStrategy.CHUNKED_WINDOWS,
                confidence=0.75,
                reasoning=reasoning,
                audio_chars=audio_chars,
                system_resources=system_resources
            )
        
        # Default: Hybrid (best all-around)
        reasoning.append("Standard content characteristics")
        reasoning.append("Hybrid provides best balance")
        return self._create_recommendation(
            BiasStrategy.HYBRID,
            confidence=0.9,
            reasoning=reasoning,
            audio_chars=audio_chars,
            system_resources=system_resources
        )
    
    def _select_by_time_budget(
        self,
        audio_chars: AudioCharacteristics,
        system_resources: SystemResources,
        reasoning: List[str]
    ) -> Optional[StrategyRecommendation]:
        """
        Select strategy based on time budget constraint
        
        Returns:
            StrategyRecommendation if time budget is constraining, None otherwise
        """
        time_budget = system_resources.time_budget_minutes
        
        # Estimate processing time for each strategy
        est_times = self._estimate_processing_times(audio_chars, system_resources)
        
        reasoning.append(f"Time budget: {time_budget:.1f} min")
        
        # Check if we can afford chunked_windows
        if est_times["chunked_windows"] <= time_budget:
            reasoning.append(f"Enough time for chunked_windows ({est_times['chunked_windows']:.1f} min)")
            return self._create_recommendation(
                BiasStrategy.CHUNKED_WINDOWS,
                confidence=0.9,
                reasoning=reasoning,
                audio_chars=audio_chars,
                system_resources=system_resources
            )
        
        # Check if we can afford hybrid
        if est_times["hybrid"] <= time_budget:
            reasoning.append(f"Time allows hybrid ({est_times['hybrid']:.1f} min)")
            return self._create_recommendation(
                BiasStrategy.HYBRID,
                confidence=0.85,
                reasoning=reasoning,
                audio_chars=audio_chars,
                system_resources=system_resources
            )
        
        # Must use global (fastest)
        reasoning.append(f"Limited time, using global ({est_times['global']:.1f} min)")
        return self._create_recommendation(
            BiasStrategy.GLOBAL,
            confidence=0.8,
            reasoning=reasoning,
            audio_chars=audio_chars,
            system_resources=system_resources
        )
    
    def _estimate_processing_times(
        self,
        audio_chars: AudioCharacteristics,
        system_resources: SystemResources
    ) -> Dict[str, float]:
        """
        Estimate processing time for each strategy
        
        Returns:
            Dict of {strategy_name: estimated_minutes}
        """
        duration_hours = audio_chars.duration_seconds / 3600
        
        # Base time multipliers per strategy
        if system_resources.device == "cuda":
            base_multipliers = {
                "global": 0.3,          # 0.3x realtime (fast GPU)
                "hybrid": 0.3,          # Same as global (single pass)
                "chunked_windows": 0.5  # 0.5x realtime (multiple passes)
            }
        elif system_resources.device == "mps":
            base_multipliers = {
                "global": 0.4,
                "hybrid": 0.4,
                "chunked_windows": 0.7
            }
        else:  # CPU
            base_multipliers = {
                "global": 1.0,          # 1.0x realtime
                "hybrid": 1.0,
                "chunked_windows": 1.5
            }
        
        # Adjust for complexity
        complexity_factor = 1.0 + (audio_chars.complexity_score * 0.5)
        
        return {
            strategy: (duration_hours * 60 * multiplier * complexity_factor)
            for strategy, multiplier in base_multipliers.items()
        }
    
    def _create_recommendation(
        self,
        strategy: BiasStrategy,
        confidence: float,
        reasoning: List[str],
        audio_chars: AudioCharacteristics,
        system_resources: SystemResources
    ) -> StrategyRecommendation:
        """Create recommendation with estimates"""
        est_times = self._estimate_processing_times(audio_chars, system_resources)
        
        # Expected accuracy by strategy
        accuracy_map = {
            BiasStrategy.GLOBAL: 0.82,
            BiasStrategy.HYBRID: 0.88,
            BiasStrategy.CHUNKED_WINDOWS: 0.93,
            BiasStrategy.ADAPTIVE: 0.95
        }
        
        return StrategyRecommendation(
            strategy=strategy,
            confidence=confidence,
            reasoning=reasoning,
            estimated_time_minutes=est_times.get(strategy.value, 0),
            expected_accuracy=accuracy_map.get(strategy, 0.85)
        )


def analyze_audio_characteristics(
    audio_file: Path,
    metadata: Optional[Dict] = None,
    logger: Optional[logging.Logger] = None
) -> AudioCharacteristics:
    """
    Analyze audio file to extract characteristics
    
    Args:
        audio_file: Path to audio file
        metadata: Optional TMDB metadata
        logger: Logger instance
        
    Returns:
        AudioCharacteristics with analysis results
    """
    logger = logger or logging.getLogger(__name__)
    
    # Get duration from audio file
    try:
        import librosa
        duration = librosa.get_duration(path=str(audio_file))
    except Exception as e:
        logger.warning(f"Could not get duration with librosa: {e}")
        duration = 7200  # Default 2 hours
    
    # Get number of characters from metadata
    num_characters = 0
    if metadata:
        cast = metadata.get('cast', [])
        num_characters = len(cast)
    
    # Estimate scene change frequency (could be improved with actual scene detection)
    # For now, use heuristic based on duration
    if duration < 3600:  # < 1 hour
        scene_change_freq = 2.5  # Low-paced
    elif duration < 7200:  # 1-2 hours
        scene_change_freq = 3.5  # Medium-paced
    else:
        scene_change_freq = 4.5  # Fast-paced
    
    # Estimate dialogue density (could use VAD results)
    avg_dialogue_density = 120  # Default: 120 words/min
    
    # Calculate complexity score
    complexity_score = calculate_complexity_score(
        duration,
        num_characters,
        scene_change_freq,
        avg_dialogue_density
    )
    
    return AudioCharacteristics(
        duration_seconds=duration,
        num_characters=num_characters,
        scene_change_frequency=scene_change_freq,
        avg_dialogue_density=avg_dialogue_density,
        complexity_score=complexity_score
    )


def calculate_complexity_score(
    duration: float,
    num_characters: int,
    scene_freq: float,
    dialogue_density: float
) -> float:
    """
    Calculate overall complexity score (0-1)
    
    Factors:
    - Duration (longer = more complex)
    - Cast size (more characters = more complex)
    - Scene changes (more changes = more complex)
    - Dialogue density (higher density = more complex)
    """
    # Normalize each factor to 0-1
    duration_score = min(duration / 10800, 1.0)  # Max at 3 hours
    cast_score = min(num_characters / 30, 1.0)   # Max at 30 characters
    scene_score = min(scene_freq / 6, 1.0)       # Max at 6 changes/min
    dialogue_score = min(dialogue_density / 180, 1.0)  # Max at 180 wpm
    
    # Weighted average
    complexity = (
        duration_score * 0.2 +
        cast_score * 0.3 +
        scene_score * 0.3 +
        dialogue_score * 0.2
    )
    
    return complexity


def detect_system_resources(logger: Optional[logging.Logger] = None) -> SystemResources:
    """
    Detect available system resources
    
    Returns:
        SystemResources with current system capabilities
    """
    logger = logger or logging.getLogger(__name__)
    
    # Detect device
    device = "cpu"
    try:
        import torch
        if torch.cuda.is_available():
            device = "cuda"
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            device = "mps"
    except ImportError:
        pass
    
    # Detect memory
    available_memory_gb = 8.0  # Default
    try:
        import psutil
        available_memory_gb = psutil.virtual_memory().available / (1024**3)
    except ImportError:
        pass
    
    # Detect CPU cores
    import multiprocessing
    cpu_cores = multiprocessing.cpu_count()
    
    return SystemResources(
        device=device,
        available_memory_gb=available_memory_gb,
        cpu_cores=cpu_cores,
        time_budget_minutes=None  # No constraint by default
    )


def main():
    """CLI interface for strategy selection"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Phase 4: ML-Based Bias Strategy Selection"
    )
    parser.add_argument(
        "--audio",
        type=Path,
        help="Audio file to analyze"
    )
    parser.add_argument(
        "--metadata",
        type=Path,
        help="TMDB metadata JSON file"
    )
    parser.add_argument(
        "--preference",
        choices=["auto", "global", "hybrid", "chunked_windows"],
        default="auto",
        help="User preference (auto = intelligent selection)"
    )
    parser.add_argument(
        "--time-budget",
        type=float,
        help="Processing time budget in minutes"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output JSON file with recommendation"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # Load metadata if provided
    metadata = None
    if args.metadata and args.metadata.exists():
        with open(args.metadata, 'r') as f:
            metadata = json.load(f)
    
    # Analyze audio
    logger.info("Analyzing audio characteristics...")
    audio_chars = analyze_audio_characteristics(args.audio, metadata, logger)
    
    logger.info(f"  Duration: {audio_chars.duration_seconds/60:.1f} minutes")
    logger.info(f"  Characters: {audio_chars.num_characters}")
    logger.info(f"  Scene frequency: {audio_chars.scene_change_frequency:.1f}/min")
    logger.info(f"  Complexity: {audio_chars.complexity_score:.2f}")
    
    # Detect system resources
    logger.info("Detecting system resources...")
    system_resources = detect_system_resources(logger)
    if args.time_budget:
        system_resources.time_budget_minutes = args.time_budget
    
    logger.info(f"  Device: {system_resources.device}")
    logger.info(f"  Memory: {system_resources.available_memory_gb:.1f} GB")
    logger.info(f"  CPU cores: {system_resources.cpu_cores}")
    if system_resources.time_budget_minutes:
        logger.info(f"  Time budget: {system_resources.time_budget_minutes:.1f} min")
    
    # Select strategy
    logger.info("Selecting optimal strategy...")
    selector = BiasStrategySelector(logger)
    recommendation = selector.select_strategy(
        audio_chars,
        system_resources,
        args.preference if args.preference != "auto" else None
    )
    
    # Log recommendation
    logger.info("")
    logger.info("=" * 70)
    logger.info("STRATEGY RECOMMENDATION")
    logger.info("=" * 70)
    logger.info(f"Strategy: {recommendation.strategy.value}")
    logger.info(f"Confidence: {recommendation.confidence * 100:.1f}%")
    logger.info(f"Expected accuracy: {recommendation.expected_accuracy * 100:.1f}%")
    logger.info(f"Estimated time: {recommendation.estimated_time_minutes:.1f} minutes")
    logger.info("")
    logger.info("Reasoning:")
    for i, reason in enumerate(recommendation.reasoning, 1):
        logger.info(f"  {i}. {reason}")
    logger.info("=" * 70)
    
    # Save to file if requested
    if args.output:
        output_data = {
            "strategy": recommendation.strategy.value,
            "confidence": recommendation.confidence,
            "expected_accuracy": recommendation.expected_accuracy,
            "estimated_time_minutes": recommendation.estimated_time_minutes,
            "reasoning": recommendation.reasoning,
            "audio_characteristics": {
                "duration_seconds": audio_chars.duration_seconds,
                "num_characters": audio_chars.num_characters,
                "scene_change_frequency": audio_chars.scene_change_frequency,
                "complexity_score": audio_chars.complexity_score
            },
            "system_resources": {
                "device": system_resources.device,
                "available_memory_gb": system_resources.available_memory_gb,
                "cpu_cores": system_resources.cpu_cores
            }
        }
        
        with open(args.output, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        logger.info(f"Recommendation saved to: {args.output}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
