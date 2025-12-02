#!/usr/bin/env python3
"""
Quality Metrics Analyzer - Phase 5

Analyzes subtitle quality metrics from generated subtitles:
- Reading speed distribution (CPS - characters per second)
- Segment duration distribution
- Hallucination patterns and frequency
- Glossary compliance rates
- Translation quality scores
- Readability metrics

Generates comprehensive quality reports with visualizations and statistics.

Usage:
    python3 scripts/quality_metrics_analyzer.py --input <segments_file> --output <report_file>
    python3 scripts/quality_metrics_analyzer.py --benchmark <benchmark_results.json>
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, asdict
from collections import Counter
import argparse

# Add scripts to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from config_loader import load_config
from hallucination_removal import HallucinationRemover


@dataclass
class QualityMetrics:
    """Quality metrics for subtitle analysis"""
    # Reading speed metrics
    avg_cps: float
    median_cps: float
    min_cps: float
    max_cps: float
    cps_std_dev: float
    optimal_cps_pct: float  # % in 17-20 CPS range

    # Duration metrics
    avg_duration: float
    median_duration: float
    min_duration: float
    max_duration: float
    duration_std_dev: float

    # Segment metrics
    total_segments: int
    total_duration: float
    total_characters: int
    avg_chars_per_segment: float

    # Quality metrics
    hallucination_count: int
    hallucination_rate_pct: float
    short_segment_count: int  # < 1 second
    long_segment_count: int  # > 7 seconds
    fast_segment_count: int  # > 20 CPS
    slow_segment_count: int  # < 15 CPS

    # Readability metrics
    avg_words_per_segment: float
    avg_words_per_line: float
    multi_line_segment_pct: float

    # Overall score
    quality_score: float  # 0-100


class QualityMetricsAnalyzer:
    """
    Analyzes subtitle quality metrics and generates reports.
    """

    def __init__(self, config=None, logger=None):
        """
        Initialize analyzer.

        Args:
            config: Configuration object
            logger: Logger instance
        """
        self.config = config or load_config(PROJECT_ROOT)
        self.logger = logger or logging.getLogger(__name__)

    def calculate_cps_metrics(self, segments: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate reading speed (CPS) metrics.

        Args:
            segments: List of segments

        Returns:
            Dict of CPS metrics
        """
        cps_values = []

        for seg in segments:
            duration = seg['end'] - seg['start']
            if duration > 0:
                text = seg.get('text', '')
                cps = len(text) / duration
                cps_values.append(cps)

        if not cps_values:
            return {
                'avg': 0.0,
                'median': 0.0,
                'min': 0.0,
                'max': 0.0,
                'std_dev': 0.0,
                'optimal_pct': 0.0
            }

        cps_values.sort()
        n = len(cps_values)

        # Calculate statistics
        avg = sum(cps_values) / n
        median = cps_values[n // 2] if n % 2 == 1 else (cps_values[n // 2 - 1] + cps_values[n // 2]) / 2

        # Standard deviation
        variance = sum((x - avg) ** 2 for x in cps_values) / n
        std_dev = variance ** 0.5

        # Optimal CPS range (17-20)
        optimal_count = sum(1 for cps in cps_values if 17 <= cps <= 20)
        optimal_pct = (optimal_count / n) * 100

        return {
            'avg': avg,
            'median': median,
            'min': min(cps_values),
            'max': max(cps_values),
            'std_dev': std_dev,
            'optimal_pct': optimal_pct
        }

    def calculate_duration_metrics(self, segments: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate segment duration metrics.

        Args:
            segments: List of segments

        Returns:
            Dict of duration metrics
        """
        durations = [seg['end'] - seg['start'] for seg in segments]

        if not durations:
            return {
                'avg': 0.0,
                'median': 0.0,
                'min': 0.0,
                'max': 0.0,
                'std_dev': 0.0
            }

        durations.sort()
        n = len(durations)

        avg = sum(durations) / n
        median = durations[n // 2] if n % 2 == 1 else (durations[n // 2 - 1] + durations[n // 2]) / 2

        variance = sum((x - avg) ** 2 for x in durations) / n
        std_dev = variance ** 0.5

        return {
            'avg': avg,
            'median': median,
            'min': min(durations),
            'max': max(durations),
            'std_dev': std_dev
        }

    def count_quality_issues(self, segments: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Count various quality issues.

        Args:
            segments: List of segments

        Returns:
            Dict of issue counts
        """
        remover = HallucinationRemover(logger=self.logger)

        issues = {
            'hallucinations': 0,
            'short_segments': 0,  # < 1 second
            'long_segments': 0,   # > 7 seconds
            'fast_segments': 0,   # > 20 CPS
            'slow_segments': 0,   # < 15 CPS
            'very_short_text': 0  # < 3 characters
        }

        for seg in segments:
            text = seg.get('text', '')
            duration = seg['end'] - seg['start']

            # Check hallucinations
            if remover.is_hallucination_pattern(text):
                issues['hallucinations'] += 1

            # Check duration issues
            if duration < 1.0:
                issues['short_segments'] += 1
            elif duration > 7.0:
                issues['long_segments'] += 1

            # Check CPS issues
            if duration > 0:
                cps = len(text) / duration
                if cps > 20:
                    issues['fast_segments'] += 1
                elif cps < 15:
                    issues['slow_segments'] += 1

            # Check very short text
            if len(text.strip()) < 3:
                issues['very_short_text'] += 1

        return issues

    def calculate_readability_metrics(self, segments: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate readability metrics.

        Args:
            segments: List of segments

        Returns:
            Dict of readability metrics
        """
        total_words = 0
        total_lines = 0
        multi_line_count = 0

        for seg in segments:
            text = seg.get('text', '')

            # Count words
            words = len(text.split())
            total_words += words

            # Count lines (approximation based on newlines)
            lines = text.count('\n') + 1
            total_lines += lines

            if lines > 1:
                multi_line_count += 1

        n = len(segments)

        return {
            'avg_words_per_segment': total_words / n if n > 0 else 0,
            'avg_words_per_line': total_words / total_lines if total_lines > 0 else 0,
            'multi_line_pct': (multi_line_count / n * 100) if n > 0 else 0
        }

    def calculate_quality_score(self, metrics: QualityMetrics) -> float:
        """
        Calculate overall quality score (0-100).

        Scoring:
        - 30%: CPS optimization (closer to 17-20 is better)
        - 25%: Hallucination rate (lower is better)
        - 20%: Duration appropriateness (1-7 seconds ideal)
        - 15%: Reading speed consistency (lower std dev is better)
        - 10%: Readability (multi-line usage)

        Args:
            metrics: Quality metrics

        Returns:
            Quality score (0-100)
        """
        # CPS score (0-30 points)
        # Optimal CPS is 17-20
        target_cps = 18.5
        cps_deviation = abs(metrics.avg_cps - target_cps)
        cps_score = max(0, 30 * (1 - min(cps_deviation / 10, 1)))

        # Hallucination score (0-25 points)
        # 0% hallucinations = 25 points, 100% = 0 points
        hallucination_score = 25 * (1 - metrics.hallucination_rate_pct / 100)

        # Duration score (0-20 points)
        # Ideal duration is 1-7 seconds
        if 1.0 <= metrics.avg_duration <= 7.0:
            duration_score = 20
        elif metrics.avg_duration < 1.0:
            duration_score = 20 * metrics.avg_duration
        else:  # > 7.0
            duration_score = 20 * max(0, 1 - (metrics.avg_duration - 7) / 10)

        # Consistency score (0-15 points)
        # Lower CPS standard deviation is better
        # Ideal std dev is < 3
        consistency_score = max(0, 15 * (1 - min(metrics.cps_std_dev / 10, 1)))

        # Readability score (0-10 points)
        # Some multi-line usage is good (30-50% ideal)
        if 30 <= metrics.multi_line_segment_pct <= 50:
            readability_score = 10
        else:
            deviation = abs(metrics.multi_line_segment_pct - 40)
            readability_score = max(0, 10 * (1 - deviation / 40))

        total_score = cps_score + hallucination_score + duration_score + consistency_score + readability_score
        return round(total_score, 2)

    def analyze_segments(self, segments: List[Dict[str, Any]]) -> QualityMetrics:
        """
        Analyze segments and calculate all quality metrics.

        Args:
            segments: List of segments

        Returns:
            Quality metrics
        """
        if not segments:
            # Return empty metrics
            return QualityMetrics(
                avg_cps=0, median_cps=0, min_cps=0, max_cps=0, cps_std_dev=0, optimal_cps_pct=0,
                avg_duration=0, median_duration=0, min_duration=0, max_duration=0, duration_std_dev=0,
                total_segments=0, total_duration=0, total_characters=0, avg_chars_per_segment=0,
                hallucination_count=0, hallucination_rate_pct=0,
                short_segment_count=0, long_segment_count=0,
                fast_segment_count=0, slow_segment_count=0,
                avg_words_per_segment=0, avg_words_per_line=0, multi_line_segment_pct=0,
                quality_score=0
            )

        # Calculate all metrics
        cps_metrics = self.calculate_cps_metrics(segments)
        duration_metrics = self.calculate_duration_metrics(segments)
        quality_issues = self.count_quality_issues(segments)
        readability = self.calculate_readability_metrics(segments)

        # Aggregate metrics
        total_duration = sum(seg['end'] - seg['start'] for seg in segments)
        total_characters = sum(len(seg.get('text', '')) for seg in segments)

        metrics = QualityMetrics(
            avg_cps=cps_metrics['avg'],
            median_cps=cps_metrics['median'],
            min_cps=cps_metrics['min'],
            max_cps=cps_metrics['max'],
            cps_std_dev=cps_metrics['std_dev'],
            optimal_cps_pct=cps_metrics['optimal_pct'],

            avg_duration=duration_metrics['avg'],
            median_duration=duration_metrics['median'],
            min_duration=duration_metrics['min'],
            max_duration=duration_metrics['max'],
            duration_std_dev=duration_metrics['std_dev'],

            total_segments=len(segments),
            total_duration=total_duration,
            total_characters=total_characters,
            avg_chars_per_segment=total_characters / len(segments),

            hallucination_count=quality_issues['hallucinations'],
            hallucination_rate_pct=(quality_issues['hallucinations'] / len(segments) * 100),
            short_segment_count=quality_issues['short_segments'],
            long_segment_count=quality_issues['long_segments'],
            fast_segment_count=quality_issues['fast_segments'],
            slow_segment_count=quality_issues['slow_segments'],

            avg_words_per_segment=readability['avg_words_per_segment'],
            avg_words_per_line=readability['avg_words_per_line'],
            multi_line_segment_pct=readability['multi_line_pct'],

            quality_score=0  # Will be calculated
        )

        # Calculate quality score
        metrics.quality_score = self.calculate_quality_score(metrics)

        return metrics

    def print_report(self, metrics: QualityMetrics, title: str = "Quality Metrics Report"):
        """
        Print formatted quality metrics report.

        Args:
            metrics: Quality metrics to report
            title: Report title
        """
        self.logger.info("")
        self.logger.info("=" * 80)
        self.logger.info(title.center(80))
        self.logger.info("=" * 80)
        self.logger.info("")

        # Segment overview
        self.logger.info("SEGMENT OVERVIEW:")
        self.logger.info(f"  Total segments: {metrics.total_segments}")
        self.logger.info(f"  Total duration: {metrics.total_duration:.1f}s")
        self.logger.info(f"  Total characters: {metrics.total_characters}")
        self.logger.info(f"  Avg chars/segment: {metrics.avg_chars_per_segment:.1f}")
        self.logger.info("")

        # Reading speed (CPS)
        self.logger.info("READING SPEED (CPS):")
        self.logger.info(f"  Average: {metrics.avg_cps:.1f}")
        self.logger.info(f"  Median: {metrics.median_cps:.1f}")
        self.logger.info(f"  Range: {metrics.min_cps:.1f} - {metrics.max_cps:.1f}")
        self.logger.info(f"  Std deviation: {metrics.cps_std_dev:.1f}")
        self.logger.info(f"  Optimal range (17-20 CPS): {metrics.optimal_cps_pct:.1f}%")

        # CPS quality indicator
        if metrics.avg_cps < 15:
            self.logger.info("  ⚠️  Too slow - consider merging segments")
        elif metrics.avg_cps > 20:
            self.logger.info("  ⚠️  Too fast - consider breaking segments")
        else:
            self.logger.info("  ✅ Within optimal range")
        self.logger.info("")

        # Duration metrics
        self.logger.info("SEGMENT DURATION:")
        self.logger.info(f"  Average: {metrics.avg_duration:.1f}s")
        self.logger.info(f"  Median: {metrics.median_duration:.1f}s")
        self.logger.info(f"  Range: {metrics.min_duration:.1f}s - {metrics.max_duration:.1f}s")
        self.logger.info(f"  Std deviation: {metrics.duration_std_dev:.1f}s")
        self.logger.info(f"  Short segments (< 1s): {metrics.short_segment_count}")
        self.logger.info(f"  Long segments (> 7s): {metrics.long_segment_count}")
        self.logger.info("")

        # Quality issues
        self.logger.info("QUALITY ISSUES:")
        self.logger.info(f"  Hallucinations: {metrics.hallucination_count} ({metrics.hallucination_rate_pct:.1f}%)")
        self.logger.info(f"  Fast segments (> 20 CPS): {metrics.fast_segment_count}")
        self.logger.info(f"  Slow segments (< 15 CPS): {metrics.slow_segment_count}")

        total_issues = (metrics.hallucination_count + metrics.fast_segment_count +
                       metrics.slow_segment_count + metrics.short_segment_count +
                       metrics.long_segment_count)

        if total_issues == 0:
            self.logger.info("  ✅ No quality issues detected")
        elif total_issues < metrics.total_segments * 0.1:
            self.logger.info(f"  ⚠️  {total_issues} minor issues detected")
        else:
            self.logger.info(f"  ❌ {total_issues} issues detected - review needed")
        self.logger.info("")

        # Readability
        self.logger.info("READABILITY:")
        self.logger.info(f"  Avg words/segment: {metrics.avg_words_per_segment:.1f}")
        self.logger.info(f"  Avg words/line: {metrics.avg_words_per_line:.1f}")
        self.logger.info(f"  Multi-line segments: {metrics.multi_line_segment_pct:.1f}%")
        self.logger.info("")

        # Overall score
        self.logger.info("=" * 80)
        self.logger.info(f"OVERALL QUALITY SCORE: {metrics.quality_score:.1f}/100")

        if metrics.quality_score >= 90:
            self.logger.info("Rating: ⭐⭐⭐⭐⭐ Excellent")
        elif metrics.quality_score >= 80:
            self.logger.info("Rating: ⭐⭐⭐⭐ Very Good")
        elif metrics.quality_score >= 70:
            self.logger.info("Rating: ⭐⭐⭐ Good")
        elif metrics.quality_score >= 60:
            self.logger.info("Rating: ⭐⭐ Fair")
        else:
            self.logger.info("Rating: ⭐ Needs Improvement")

        self.logger.info("=" * 80)
        self.logger.info("")

    def save_report(self, metrics: QualityMetrics, output_file: Path):
        """
        Save quality metrics to JSON file.

        Args:
            metrics: Quality metrics
            output_file: Path to output file
        """
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(asdict(metrics), f, indent=2)

        self.logger.info(f"Quality report saved to: {output_file}")

    def analyze_benchmark_results(self, benchmark_file: Path):
        """
        Analyze benchmark results and generate comparative report.

        Args:
            benchmark_file: Path to benchmark results JSON
        """
        with open(benchmark_file, 'r') as f:
            data = json.load(f)

        results = data.get('results', [])

        if not results:
            self.logger.warning("No benchmark results found")
            return

        self.logger.info("")
        self.logger.info("=" * 80)
        self.logger.info("BENCHMARK QUALITY ANALYSIS".center(80))
        self.logger.info("=" * 80)
        self.logger.info("")

        # Print comparison table
        self.logger.info(f"{'Configuration':<20} {'Score':<10} {'Halluc%':<12} {'Avg CPS':<12} {'Segment Reduction':<20}")
        self.logger.info("-" * 80)

        for result in results:
            self.logger.info(
                f"{result['config_name']:<20} "
                f"{result['accuracy_score']:>6.1f} "
                f"{result['hallucination_rate_pct']:>8.1f}% "
                f"{result['avg_cps']:>8.1f} "
                f"{result['segment_reduction_pct']:>12.1f}%"
            )

        self.logger.info("")

        # Find best and worst
        best = max(results, key=lambda r: r['accuracy_score'])
        worst = min(results, key=lambda r: r['accuracy_score'])

        self.logger.info("BENCHMARK SUMMARY:")
        self.logger.info(f"  Best configuration: {best['config_name']} (score: {best['accuracy_score']:.1f})")
        self.logger.info(f"  Worst configuration: {worst['config_name']} (score: {worst['accuracy_score']:.1f})")
        self.logger.info(f"  Improvement range: {best['accuracy_score'] - worst['accuracy_score']:.1f} points")
        self.logger.info("")

        # Recommendations
        self.logger.info("RECOMMENDATIONS:")

        if best['hallucination_rate_pct'] > 10:
            self.logger.info("  ⚠️  Consider enabling Phase 2 (hallucination removal)")

        if best['avg_cps'] < 15 or best['avg_cps'] > 20:
            self.logger.info("  ⚠️  Consider enabling Phase 3 (segment merging) for optimal CPS")

        if best['segment_reduction_pct'] < 30:
            self.logger.info("  ℹ️  Low segment reduction - merging may improve readability")

        if best['accuracy_score'] >= 85:
            self.logger.info("  ✅ Excellent results - configuration is production-ready")

        self.logger.info("")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Analyze subtitle quality metrics')
    parser.add_argument('--input', type=str, help='Input segments JSON file')
    parser.add_argument('--output', type=str, default='quality_report.json', help='Output report file')
    parser.add_argument('--benchmark', type=str, help='Analyze benchmark results file')
    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s'
    )
    logger = logging.getLogger()

    # Load configuration
    config = load_config(PROJECT_ROOT)

    # Initialize analyzer
    analyzer = QualityMetricsAnalyzer(config=config, logger=logger)

    # Analyze benchmark results if provided
    if args.benchmark:
        benchmark_path = Path(args.benchmark)
        if not benchmark_path.exists():
            logger.error(f"Benchmark file not found: {benchmark_path}")
            return 1

        analyzer.analyze_benchmark_results(benchmark_path)
        return 0

    # Load and analyze segments
    if not args.input:
        logger.error("Must provide --input or --benchmark")
        return 1

    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return 1

    logger.info(f"Loading segments from: {input_path}")
    with open(input_path, 'r') as f:
        data = json.load(f)
        segments = data if isinstance(data, list) else data.get('segments', [])

    # Analyze segments
    metrics = analyzer.analyze_segments(segments)

    # Print report
    analyzer.print_report(metrics)

    # Save report
    output_path = Path(args.output)
    analyzer.save_report(metrics, output_path)

    # Return success if quality score is good
    if metrics.quality_score >= 70:
        logger.info("✅ Quality analysis complete - good quality detected")
        return 0
    else:
        logger.warning("⚠️  Quality below threshold - review recommended")
        return 1


if __name__ == "__main__":
    sys.exit(main())
