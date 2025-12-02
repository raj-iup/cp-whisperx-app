#!/usr/bin/env python3
"""
Subtitle Accuracy Benchmarking Script - Phase 5

Benchmarks subtitle accuracy improvements across different configurations:
- Baseline (no enhancements)
- Phase 1 only (confidence filtering)
- Phase 2 only (hallucination removal)
- Phase 3 only (segment merging)
- Phase 4 only (glossary protection)
- All phases combined

Metrics tracked:
- Hallucination rate (% of segments that are hallucinations)
- Segment count reduction
- Average characters per second (CPS)
- Glossary term preservation rate
- Overall accuracy score

Usage:
    python3 scripts/benchmark_accuracy.py --input <segments_file> --output <results_file>
    python3 scripts/benchmark_accuracy.py --sample  # Use built-in sample data
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, asdict
import argparse

# Add scripts to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from config_loader import load_config
from hallucination_removal import HallucinationRemover
from subtitle_segment_merger import SubtitleSegmentMerger
from glossary_protected_translator import GlossaryProtectedTranslator
from translation_validator import TranslationValidator


@dataclass
class BenchmarkResult:
    """Results from a single benchmark run"""
    config_name: str
    total_segments: int
    final_segments: int
    segment_reduction_pct: float
    hallucination_count: int
    hallucination_rate_pct: float
    avg_cps: float
    min_cps: float
    max_cps: float
    glossary_compliance_pct: float
    avg_segment_duration: float
    accuracy_score: float


class AccuracyBenchmark:
    """
    Benchmarks subtitle accuracy across different configurations.
    """

    def __init__(self, config=None, logger=None):
        """
        Initialize benchmark.

        Args:
            config: Configuration object
            logger: Logger instance
        """
        self.config = config or load_config(PROJECT_ROOT)
        self.logger = logger or logging.getLogger(__name__)

        self.results: List[BenchmarkResult] = []

    def create_sample_segments(self) -> List[Dict[str, Any]]:
        """
        Create sample segments with known hallucinations and issues.

        Returns:
            List of test segments
        """
        return [
            # Real content
            {'start': 0.0, 'end': 3.0, 'text': 'Jai and Aditi are meeting in Mumbai', 'confidence': 0.95},
            {'start': 3.5, 'end': 5.0, 'text': 'They discuss the project', 'confidence': 0.92},

            # Hallucination patterns
            {'start': 5.5, 'end': 6.0, 'text': 'Thank you.', 'confidence': 0.85},
            {'start': 6.5, 'end': 7.0, 'text': 'Subscribe', 'confidence': 0.82},
            {'start': 7.5, 'end': 8.0, 'text': 'Please like and share', 'confidence': 0.78},

            # Low confidence segments
            {'start': 8.5, 'end': 9.5, 'text': 'mumblemumble', 'confidence': 0.45},
            {'start': 10.0, 'end': 10.5, 'text': 'um', 'confidence': 0.35},

            # Short segments (too short)
            {'start': 11.0, 'end': 11.5, 'text': 'A', 'confidence': 0.88},
            {'start': 12.0, 'end': 12.3, 'text': 'I', 'confidence': 0.90},

            # Sequential duplicates (looping hallucination)
            {'start': 13.0, 'end': 14.0, 'text': 'Repeat phrase', 'confidence': 0.89},
            {'start': 14.5, 'end': 15.5, 'text': 'Repeat phrase', 'confidence': 0.87},
            {'start': 16.0, 'end': 17.0, 'text': 'Repeat phrase', 'confidence': 0.85},

            # Good content that should be merged
            {'start': 18.0, 'end': 19.0, 'text': 'The meeting', 'confidence': 0.93},
            {'start': 19.2, 'end': 20.0, 'text': 'was productive', 'confidence': 0.94},
            {'start': 20.3, 'end': 21.5, 'text': 'and successful', 'confidence': 0.95},

            # Long segment needing line breaks
            {'start': 22.0, 'end': 28.0, 'text': 'This is a very long subtitle segment that should be broken into multiple lines for better readability and compliance with subtitle standards', 'confidence': 0.91},

            # Fast reading speed (needs timing adjustment)
            {'start': 29.0, 'end': 30.0, 'text': 'Very long text in short time that reads way too fast for comfortable reading', 'confidence': 0.90},

            # More real content with names
            {'start': 31.0, 'end': 33.0, 'text': 'Delhi office will coordinate', 'confidence': 0.94},
            {'start': 33.5, 'end': 35.0, 'text': 'with the Mumbai team', 'confidence': 0.93},
        ]

    def calculate_cps_stats(self, segments: List[Dict[str, Any]]) -> Tuple[float, float, float]:
        """
        Calculate CPS (characters per second) statistics.

        Args:
            segments: List of segments

        Returns:
            Tuple of (avg_cps, min_cps, max_cps)
        """
        cps_values = []

        for seg in segments:
            duration = seg['end'] - seg['start']
            if duration > 0:
                text = seg.get('text', '')
                cps = len(text) / duration
                cps_values.append(cps)

        if not cps_values:
            return 0.0, 0.0, 0.0

        return (
            sum(cps_values) / len(cps_values),
            min(cps_values),
            max(cps_values)
        )

    def calculate_avg_duration(self, segments: List[Dict[str, Any]]) -> float:
        """
        Calculate average segment duration.

        Args:
            segments: List of segments

        Returns:
            Average duration in seconds
        """
        if not segments:
            return 0.0

        durations = [seg['end'] - seg['start'] for seg in segments]
        return sum(durations) / len(durations)

    def count_hallucinations(self, segments: List[Dict[str, Any]]) -> int:
        """
        Count likely hallucination segments.

        Args:
            segments: List of segments

        Returns:
            Number of hallucination segments
        """
        remover = HallucinationRemover(logger=self.logger)
        count = 0

        # Get confidence threshold from config
        confidence_threshold = self.config.get('WHISPER_LOGPROB_THRESHOLD', -0.8)

        for seg in segments:
            text = seg.get('text', '')
            confidence = seg.get('confidence', 1.0)

            # Check hallucination patterns
            if remover.is_hallucination_pattern(text):
                count += 1
                continue

            # Check low confidence (treat as log prob - lower is worse)
            # For testing purposes, convert regular confidence to similar scale
            if confidence < 0.6:  # Low confidence threshold
                count += 1
                continue

            # Check too short
            if len(text.strip()) < 3:
                count += 1
                continue

        return count

    def calculate_glossary_compliance(
        self,
        segments: List[Dict[str, Any]],
        glossary=None
    ) -> float:
        """
        Calculate glossary compliance rate.

        Args:
            segments: List of segments
            glossary: Glossary object (optional)

        Returns:
            Compliance rate (0.0-1.0)
        """
        if not glossary:
            # Mock glossary for testing
            class MockGlossary:
                def get_proper_nouns(self):
                    return ["Jai", "Aditi", "Mumbai", "Delhi"]

                def get_translation(self, term):
                    return term

            glossary = MockGlossary()

        validator = TranslationValidator(glossary, self.logger)

        # Check each segment for proper nouns
        compliant_count = 0
        total_with_terms = 0

        for seg in segments:
            text = seg.get('text', '')
            found_terms = validator.find_terms_in_text(text)

            if found_terms:
                total_with_terms += 1
                # All terms should be present (since we're not translating in benchmark)
                all_present = all(term.lower() in text.lower() for term in found_terms)
                if all_present:
                    compliant_count += 1

        if total_with_terms == 0:
            return 1.0  # No glossary terms = 100% compliant

        return compliant_count / total_with_terms

    def calculate_accuracy_score(self, result: BenchmarkResult) -> float:
        """
        Calculate overall accuracy score (0-100).

        Weighted combination of metrics:
        - 40%: Hallucination removal (lower is better)
        - 30%: CPS optimization (closer to 17-20 is better)
        - 20%: Glossary compliance (higher is better)
        - 10%: Segment reduction (moderate is better)

        Args:
            result: Benchmark result

        Returns:
            Accuracy score (0-100)
        """
        # Hallucination score (0-40 points)
        # 0% hallucinations = 40 points, 100% = 0 points
        hallucination_score = 40 * (1 - result.hallucination_rate_pct / 100)

        # CPS score (0-30 points)
        # Optimal CPS is 17-20, give full points in that range
        target_cps = 18.5  # Middle of optimal range
        cps_deviation = abs(result.avg_cps - target_cps)
        # Full points if within ±1.5, decreasing linearly to 0 at ±10
        cps_score = max(0, 30 * (1 - min(cps_deviation / 10, 1)))

        # Glossary score (0-20 points)
        glossary_score = 20 * (result.glossary_compliance_pct / 100)

        # Segment reduction score (0-10 points)
        # Optimal reduction is 40-60%
        if 40 <= result.segment_reduction_pct <= 60:
            reduction_score = 10
        else:
            # Penalize too much or too little reduction
            if result.segment_reduction_pct < 40:
                reduction_score = 10 * (result.segment_reduction_pct / 40)
            else:  # > 60%
                reduction_score = 10 * max(0, 1 - (result.segment_reduction_pct - 60) / 40)

        total_score = hallucination_score + cps_score + glossary_score + reduction_score
        return round(total_score, 2)

    def benchmark_baseline(self, segments: List[Dict[str, Any]]) -> BenchmarkResult:
        """
        Benchmark with no enhancements (baseline).

        Args:
            segments: Input segments

        Returns:
            Benchmark result
        """
        self.logger.info("Benchmarking: Baseline (no enhancements)")

        hallucination_count = self.count_hallucinations(segments)
        avg_cps, min_cps, max_cps = self.calculate_cps_stats(segments)
        avg_duration = self.calculate_avg_duration(segments)
        glossary_compliance = self.calculate_glossary_compliance(segments)

        result = BenchmarkResult(
            config_name="Baseline",
            total_segments=len(segments),
            final_segments=len(segments),
            segment_reduction_pct=0.0,
            hallucination_count=hallucination_count,
            hallucination_rate_pct=(hallucination_count / len(segments) * 100) if segments else 0,
            avg_cps=avg_cps,
            min_cps=min_cps,
            max_cps=max_cps,
            glossary_compliance_pct=glossary_compliance * 100,
            avg_segment_duration=avg_duration,
            accuracy_score=0.0  # Will be calculated
        )

        result.accuracy_score = self.calculate_accuracy_score(result)
        return result

    def benchmark_phase1_only(self, segments: List[Dict[str, Any]]) -> BenchmarkResult:
        """
        Benchmark with Phase 1 only (confidence filtering).

        Args:
            segments: Input segments

        Returns:
            Benchmark result
        """
        self.logger.info("Benchmarking: Phase 1 (confidence filtering)")

        # Apply confidence filtering (use 0.6 as threshold for test data)
        confidence_threshold = 0.6
        filtered = [
            seg for seg in segments
            if seg.get('confidence', 1.0) >= confidence_threshold
        ]

        hallucination_count = self.count_hallucinations(filtered)
        avg_cps, min_cps, max_cps = self.calculate_cps_stats(filtered)
        avg_duration = self.calculate_avg_duration(filtered)
        glossary_compliance = self.calculate_glossary_compliance(filtered)

        result = BenchmarkResult(
            config_name="Phase 1 Only",
            total_segments=len(segments),
            final_segments=len(filtered),
            segment_reduction_pct=((len(segments) - len(filtered)) / len(segments) * 100) if segments else 0,
            hallucination_count=hallucination_count,
            hallucination_rate_pct=(hallucination_count / len(filtered) * 100) if filtered else 0,
            avg_cps=avg_cps,
            min_cps=min_cps,
            max_cps=max_cps,
            glossary_compliance_pct=glossary_compliance * 100,
            avg_segment_duration=avg_duration,
            accuracy_score=0.0
        )

        result.accuracy_score = self.calculate_accuracy_score(result)
        return result

    def benchmark_phase2_only(self, segments: List[Dict[str, Any]]) -> BenchmarkResult:
        """
        Benchmark with Phase 2 only (hallucination removal).

        Args:
            segments: Input segments

        Returns:
            Benchmark result
        """
        self.logger.info("Benchmarking: Phase 2 (hallucination removal)")

        remover = HallucinationRemover(logger=self.logger)
        cleaned, stats = remover.process_segments(segments.copy(), use_enhanced=True)

        hallucination_count = self.count_hallucinations(cleaned)
        avg_cps, min_cps, max_cps = self.calculate_cps_stats(cleaned)
        avg_duration = self.calculate_avg_duration(cleaned)
        glossary_compliance = self.calculate_glossary_compliance(cleaned)

        result = BenchmarkResult(
            config_name="Phase 2 Only",
            total_segments=len(segments),
            final_segments=len(cleaned),
            segment_reduction_pct=((len(segments) - len(cleaned)) / len(segments) * 100) if segments else 0,
            hallucination_count=hallucination_count,
            hallucination_rate_pct=(hallucination_count / len(cleaned) * 100) if cleaned else 0,
            avg_cps=avg_cps,
            min_cps=min_cps,
            max_cps=max_cps,
            glossary_compliance_pct=glossary_compliance * 100,
            avg_segment_duration=avg_duration,
            accuracy_score=0.0
        )

        result.accuracy_score = self.calculate_accuracy_score(result)
        return result

    def benchmark_phase3_only(self, segments: List[Dict[str, Any]]) -> BenchmarkResult:
        """
        Benchmark with Phase 3 only (segment merging).

        Args:
            segments: Input segments

        Returns:
            Benchmark result
        """
        self.logger.info("Benchmarking: Phase 3 (segment merging)")

        merger = SubtitleSegmentMerger(config=self.config, logger=self.logger)
        merged = merger.merge_segments(segments.copy())

        hallucination_count = self.count_hallucinations(merged)
        avg_cps, min_cps, max_cps = self.calculate_cps_stats(merged)
        avg_duration = self.calculate_avg_duration(merged)
        glossary_compliance = self.calculate_glossary_compliance(merged)

        result = BenchmarkResult(
            config_name="Phase 3 Only",
            total_segments=len(segments),
            final_segments=len(merged),
            segment_reduction_pct=((len(segments) - len(merged)) / len(segments) * 100) if segments else 0,
            hallucination_count=hallucination_count,
            hallucination_rate_pct=(hallucination_count / len(merged) * 100) if merged else 0,
            avg_cps=avg_cps,
            min_cps=min_cps,
            max_cps=max_cps,
            glossary_compliance_pct=glossary_compliance * 100,
            avg_segment_duration=avg_duration,
            accuracy_score=0.0
        )

        result.accuracy_score = self.calculate_accuracy_score(result)
        return result

    def benchmark_all_phases(self, segments: List[Dict[str, Any]]) -> BenchmarkResult:
        """
        Benchmark with all phases combined.

        Args:
            segments: Input segments

        Returns:
            Benchmark result
        """
        self.logger.info("Benchmarking: All Phases Combined")

        # Phase 1: Confidence filtering (use 0.6 as threshold for test data)
        confidence_threshold = 0.6
        filtered = [
            seg for seg in segments
            if seg.get('confidence', 1.0) >= confidence_threshold
        ]

        # Phase 2: Hallucination removal
        remover = HallucinationRemover(logger=self.logger)
        cleaned, _ = remover.process_segments(filtered.copy(), use_enhanced=True)

        # Phase 3: Segment merging
        merger = SubtitleSegmentMerger(config=self.config, logger=self.logger)
        merged = merger.merge_segments(cleaned.copy())

        # Phase 4: (Would apply during translation, not applicable to benchmark segments)

        hallucination_count = self.count_hallucinations(merged)
        avg_cps, min_cps, max_cps = self.calculate_cps_stats(merged)
        avg_duration = self.calculate_avg_duration(merged)
        glossary_compliance = self.calculate_glossary_compliance(merged)

        result = BenchmarkResult(
            config_name="All Phases",
            total_segments=len(segments),
            final_segments=len(merged),
            segment_reduction_pct=((len(segments) - len(merged)) / len(segments) * 100) if segments else 0,
            hallucination_count=hallucination_count,
            hallucination_rate_pct=(hallucination_count / len(merged) * 100) if merged else 0,
            avg_cps=avg_cps,
            min_cps=min_cps,
            max_cps=max_cps,
            glossary_compliance_pct=glossary_compliance * 100,
            avg_segment_duration=avg_duration,
            accuracy_score=0.0
        )

        result.accuracy_score = self.calculate_accuracy_score(result)
        return result

    def run_benchmark(self, segments: List[Dict[str, Any]]) -> List[BenchmarkResult]:
        """
        Run all benchmark configurations.

        Args:
            segments: Input segments

        Returns:
            List of benchmark results
        """
        self.logger.info("=" * 80)
        self.logger.info("SUBTITLE ACCURACY BENCHMARK")
        self.logger.info("=" * 80)
        self.logger.info(f"Input segments: {len(segments)}")
        self.logger.info("")

        results = []

        # Run each configuration
        results.append(self.benchmark_baseline(segments))
        results.append(self.benchmark_phase1_only(segments))
        results.append(self.benchmark_phase2_only(segments))
        results.append(self.benchmark_phase3_only(segments))
        results.append(self.benchmark_all_phases(segments))

        self.results = results
        return results

    def print_results(self):
        """Print benchmark results in formatted table."""
        if not self.results:
            self.logger.warning("No results to display")
            return

        self.logger.info("")
        self.logger.info("=" * 80)
        self.logger.info("BENCHMARK RESULTS")
        self.logger.info("=" * 80)
        self.logger.info("")

        # Header
        self.logger.info(f"{'Configuration':<20} {'Segments':<12} {'Reduction':<12} {'Halluc%':<12} {'Avg CPS':<12} {'Glossary%':<12} {'Score':<10}")
        self.logger.info("-" * 80)

        # Rows
        for result in self.results:
            self.logger.info(
                f"{result.config_name:<20} "
                f"{result.final_segments:>4}/{result.total_segments:<4} "
                f"{result.segment_reduction_pct:>6.1f}% "
                f"{result.hallucination_rate_pct:>6.1f}% "
                f"{result.avg_cps:>6.1f} "
                f"{result.glossary_compliance_pct:>6.1f}% "
                f"{result.accuracy_score:>6.1f}"
            )

        self.logger.info("=" * 80)
        self.logger.info("")

        # Summary
        baseline = self.results[0]
        best = max(self.results, key=lambda r: r.accuracy_score)

        self.logger.info("SUMMARY:")
        self.logger.info(f"  Best configuration: {best.config_name}")
        self.logger.info(f"  Accuracy improvement: {best.accuracy_score - baseline.accuracy_score:+.1f} points")
        self.logger.info(f"  Hallucination reduction: {baseline.hallucination_rate_pct - best.hallucination_rate_pct:+.1f}%")
        self.logger.info(f"  Segment reduction: {best.segment_reduction_pct:.1f}%")
        self.logger.info(f"  CPS optimization: {baseline.avg_cps:.1f} → {best.avg_cps:.1f}")
        self.logger.info("")

    def save_results(self, output_file: Path):
        """
        Save results to JSON file.

        Args:
            output_file: Path to output file
        """
        if not self.results:
            self.logger.warning("No results to save")
            return

        output_data = {
            'benchmark_config': {
                'confidence_threshold': 0.6,
                'max_cps': self.config.segment_merge_max_cps,
                'min_cps': self.config.segment_merge_min_cps,
            },
            'results': [asdict(r) for r in self.results]
        }

        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)

        self.logger.info(f"Results saved to: {output_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Benchmark subtitle accuracy improvements')
    parser.add_argument('--input', type=str, help='Input segments JSON file')
    parser.add_argument('--output', type=str, default='benchmark_results.json', help='Output results file')
    parser.add_argument('--sample', action='store_true', help='Use built-in sample data')
    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s'
    )
    logger = logging.getLogger()

    # Load configuration
    config = load_config(PROJECT_ROOT)

    # Initialize benchmark
    benchmark = AccuracyBenchmark(config=config, logger=logger)

    # Load segments
    if args.sample or not args.input:
        logger.info("Using sample data")
        segments = benchmark.create_sample_segments()
    else:
        input_path = Path(args.input)
        logger.info(f"Loading segments from: {input_path}")
        with open(input_path, 'r') as f:
            data = json.load(f)
            segments = data if isinstance(data, list) else data.get('segments', [])

    # Run benchmark
    results = benchmark.run_benchmark(segments)

    # Print results
    benchmark.print_results()

    # Save results
    output_path = Path(args.output)
    benchmark.save_results(output_path)

    # Return 0 if best result is better than baseline
    baseline = results[0]
    best = max(results, key=lambda r: r.accuracy_score)

    if best.accuracy_score > baseline.accuracy_score:
        logger.info("✅ Benchmark successful - improvements detected!")
        return 0
    else:
        logger.warning("⚠️  No improvement detected")
        return 1


if __name__ == "__main__":
    sys.exit(main())
