#!/usr/bin/env python3
"""
Beam Search Optimizer for Translation Quality

Automatically finds optimal beam size by testing range 4-10 and selecting
the configuration that produces highest quality translations.

Usage:
    from scripts.beam_optimizer import BeamOptimizer
    
    optimizer = BeamOptimizer(logger=logger)
    optimal_beam, results = optimizer.optimize_beam_size(
        segments, source_lang, target_lang, translate_func
    )
"""

import json
import random
from pathlib import Path
from typing import List, Dict, Tuple, Callable, Optional, Any
from collections import Counter

class BeamOptimizer:
    """
    Optimize beam size for translation quality using sample-based testing.
    
    Tests multiple beam sizes (4-10) on a representative sample of segments
    and selects the beam size that produces highest quality translations.
    """
    
    def __init__(self, logger: Optional[Any] = None):
        """
        Initialize beam optimizer.
        
        Args:
            logger: Optional PipelineLogger instance for logging
        """
        self.logger = logger
        
    def select_representative_sample(
        self, 
        segments: List[Dict], 
        sample_size: int = 20
    ) -> List[Dict]:
        """
        Select diverse sample of segments for testing.
        
        Uses stratified sampling by text length to ensure representative
        coverage of short, medium, and long segments.
        
        Args:
            segments: Full list of segments
            sample_size: Number of segments to sample
            
        Returns:
            List of sampled segments
        """
        if len(segments) <= sample_size:
            return segments
        
        # Stratified sampling by text length
        short = [s for s in segments if len(s.get('text', '')) < 30]
        medium = [s for s in segments if 30 <= len(s.get('text', '')) < 80]
        long = [s for s in segments if len(s.get('text', '')) >= 80]
        
        # Proportional sampling
        total = len(segments)
        n_short = int(sample_size * len(short) / total) if short else 0
        n_medium = int(sample_size * len(medium) / total) if medium else 0
        n_long = sample_size - n_short - n_medium
        
        sample = []
        if short:
            sample.extend(random.sample(short, min(n_short, len(short))))
        if medium:
            sample.extend(random.sample(medium, min(n_medium, len(medium))))
        if long:
            sample.extend(random.sample(long, min(n_long, len(long))))
        
        # Fill up to sample_size if needed
        while len(sample) < sample_size and len(sample) < len(segments):
            remaining = [s for s in segments if s not in sample]
            if remaining:
                sample.append(random.choice(remaining))
            else:
                break
        
        return sample
    
    def calculate_quality_score(
        self, 
        translated_segments: List[Dict]
    ) -> Tuple[float, Dict[str, float]]:
        """
        Calculate composite quality score for translations.
        
        Evaluates multiple quality metrics:
        - Repetition rate: Fewer repeated words = better
        - Word diversity: More unique words = better
        - Length consistency: Reasonable translation length
        - Completeness: No empty segments
        - Character variety: Rich vocabulary usage
        
        Args:
            translated_segments: List of translated segment dicts
            
        Returns:
            Tuple of (composite_score, individual_scores_dict)
        """
        scores = {}
        
        # 1. Repetition rate (lower is better, so invert)
        all_text = ' '.join(s.get('text', '') for s in translated_segments)
        words = all_text.split()
        
        if len(words) > 0:
            word_counts = Counter(words)
            # Count words that appear more than 2 times (potential hallucinations)
            repeated = sum(1 for count in word_counts.values() if count > 2)
            scores['repetition'] = max(0.0, 1.0 - (repeated / len(words)))
        else:
            scores['repetition'] = 0.0
        
        # 2. Word diversity (higher is better)
        if len(words) > 0:
            unique_words = len(set(words))
            scores['diversity'] = unique_words / len(words)
        else:
            scores['diversity'] = 0.0
        
        # 3. Length consistency (penalize very short/long translations)
        if translated_segments:
            avg_len = sum(len(s.get('text', '')) for s in translated_segments) / len(translated_segments)
            # Expect reasonable length (20-100 chars per segment)
            if 20 <= avg_len <= 100:
                scores['length'] = 1.0
            elif avg_len < 20:
                scores['length'] = avg_len / 20.0
            else:
                scores['length'] = max(0.0, 1.0 - (avg_len - 100) / 100.0)
        else:
            scores['length'] = 0.0
        
        # 4. Completeness (no empty segments)
        if translated_segments:
            empty_count = sum(1 for s in translated_segments if len(s.get('text', '').strip()) == 0)
            scores['completeness'] = 1.0 - (empty_count / len(translated_segments))
        else:
            scores['completeness'] = 0.0
        
        # 5. Character variation (detect stuck patterns)
        char_set = set(all_text)
        if len(all_text) > 0:
            # Expect at least 50 unique characters for good variety
            scores['char_variety'] = min(1.0, len(char_set) / 50.0)
        else:
            scores['char_variety'] = 0.0
        
        # Weighted composite score
        weights = {
            'repetition': 0.25,
            'diversity': 0.25,
            'length': 0.20,
            'completeness': 0.20,
            'char_variety': 0.10
        }
        
        composite_score = sum(scores[k] * weights[k] for k in scores)
        
        return composite_score, scores
    
    def optimize_beam_size(
        self,
        segments: List[Dict],
        source_lang: str,
        target_lang: str,
        translate_func: Callable[[List[Dict], int], List[Dict]],
        beam_min: int = 4,
        beam_max: int = 10,
        sample_size: int = 20
    ) -> Tuple[int, Dict[str, Any]]:
        """
        Find optimal beam size through sample-based testing.
        
        Tests each beam size from beam_min to beam_max on a representative
        sample, evaluates quality, and returns the beam size with highest score.
        
        Args:
            segments: Full segment list
            source_lang: Source language code (e.g., 'hi')
            target_lang: Target language code (e.g., 'en')
            translate_func: Function(segments, num_beams) -> translated_segments
            beam_min: Minimum beam size to test (default: 4)
            beam_max: Maximum beam size to test (default: 10)
            sample_size: Number of segments in sample (default: 20)
            
        Returns:
            Tuple of (optimal_beam_size, results_dict)
            
        Example:
            def translate_with_beam(sample, num_beams):
                return translator.translate(sample, num_beams=num_beams)
            
            optimal, results = optimizer.optimize_beam_size(
                segments, 'hi', 'en', translate_with_beam
            )
        """
        # Select representative sample
        if self.logger:
            self.logger.info(f"Selecting {sample_size} representative segments for beam optimization...")
        
        sample = self.select_representative_sample(segments, sample_size)
        
        if self.logger:
            self.logger.info(f"Testing beam sizes {beam_min}-{beam_max}...")
        
        results = {}
        best_beam = beam_min
        best_score = -1.0
        
        # Test each beam size
        for num_beams in range(beam_min, beam_max + 1):
            if self.logger:
                self.logger.info(f"  Testing beam size: {num_beams}")
            
            try:
                # Translate sample with this beam size
                translated = translate_func(sample, num_beams)
                
                # Calculate quality score
                score, metrics = self.calculate_quality_score(translated)
                
                results[num_beams] = {
                    'score': score,
                    'metrics': metrics
                }
                
                # Log results
                if self.logger:
                    metrics_str = ', '.join(f"{k}={v:.2f}" for k, v in metrics.items())
                    marker = " ⭐" if score > best_score else ""
                    self.logger.info(f"    Beam {num_beams}: Score={score:.3f} ({metrics_str}){marker}")
                
                # Track best
                if score > best_score:
                    best_score = score
                    best_beam = num_beams
                    
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"    Beam {num_beams} failed: {e}")
                results[num_beams] = {
                    'score': 0.0,
                    'error': str(e)
                }
        
        if self.logger:
            self.logger.info(f"✓ Optimal beam size: {best_beam} (quality score: {best_score:.3f})")
        
        # Build comprehensive results report
        optimization_report = {
            'enabled': True,
            'strategy': 'sample_based',
            'beam_range': [beam_min, beam_max],
            'sample_size': sample_size,
            'tested_beams': list(range(beam_min, beam_max + 1)),
            'results': results,
            'optimal_beam': best_beam,
            'optimal_score': best_score
        }
        
        return best_beam, optimization_report


def main():
    """Example usage"""
    import sys
    from pathlib import Path
    
    # Add project root to path
    PROJECT_ROOT = Path(__file__).parent.parent
    sys.path.insert(0, str(PROJECT_ROOT))
    
    from shared.logger import PipelineLogger
    
    # Example segments
    test_segments = [
        {'text': 'नमस्ते, आप कैसे हैं?', 'start': 0.0, 'end': 2.0},
        {'text': 'मैं ठीक हूं, धन्यवाद', 'start': 2.0, 'end': 4.0},
        {'text': 'आज मौसम बहुत अच्छा है', 'start': 4.0, 'end': 6.0},
    ]
    
    # Example translation function
    def mock_translate(segments, num_beams):
        # Simulate translation
        return [
            {**s, 'text': f"Translation {num_beams}b: {s['text']}"} 
            for s in segments
        ]
    
    # Run optimizer
    logger = PipelineLogger("beam_optimizer_test")
    optimizer = BeamOptimizer(logger=logger)
    
    optimal_beam, results = optimizer.optimize_beam_size(
        test_segments, 'hi', 'en', mock_translate,
        beam_min=4, beam_max=6, sample_size=3
    )
    
    print(f"\nOptimal beam: {optimal_beam}")
    print(f"Results: {json.dumps(results, indent=2)}")


if __name__ == "__main__":
    main()
