#!/usr/bin/env python3
"""
Performance Metrics Tracker for CP-WhisperX-App

Purpose: Track pipeline performance metrics (timing, memory, GPU)
Input: Called by pipeline stages during execution
Output: Performance metrics report (JSON)
"""

import sys
import time
import json
import psutil
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.logger import PipelineLogger


class PerformanceTracker:
    """Track pipeline performance metrics."""
    
    def __init__(self, job_dir: Optional[Path] = None):
        """Initialize performance tracker.
        
        Args:
            job_dir: Optional job directory for saving reports
        """
        self.job_dir = Path(job_dir) if job_dir else None
        self.logger = PipelineLogger("performance_tracker")
        
        self.stage_timings = {}
        self.memory_samples = []
        self.start_time = time.time()
        self.audio_duration = 0.0
    
    def start_stage(self, stage_name: str) -> None:
        """Start timing a stage.
        
        Args:
            stage_name: Name of the stage
        """
        self.stage_timings[stage_name] = {
            'start': time.time(),
            'memory_start': self._get_memory_usage_mb(),
        }
        self.logger.debug(f"Started tracking: {stage_name}")
    
    def end_stage(self, stage_name: str) -> Dict[str, Any]:
        """End timing a stage and calculate metrics.
        
        Args:
            stage_name: Name of the stage
            
        Returns:
            Stage metrics dictionary
        """
        if stage_name not in self.stage_timings:
            self.logger.warning(f"Stage '{stage_name}' was not started")
            return {}
        
        timing = self.stage_timings[stage_name]
        timing['end'] = time.time()
        timing['duration'] = timing['end'] - timing['start']
        timing['memory_end'] = self._get_memory_usage_mb()
        timing['memory_delta'] = timing['memory_end'] - timing['memory_start']
        
        self.logger.debug(
            f"Completed tracking: {stage_name} "
            f"({timing['duration']:.1f}s, {timing['memory_delta']:+.0f}MB)"
        )
        
        return timing
    
    def set_audio_duration(self, duration: float) -> None:
        """Set audio duration for RTF calculation.
        
        Args:
            duration: Audio duration in seconds
        """
        self.audio_duration = duration
        self.logger.debug(f"Audio duration set: {duration:.1f}s")
    
    def calculate_rtf(self) -> float:
        """Calculate Real-Time Factor (RTF).
        
        Returns:
            RTF value (audio_duration / processing_time)
        """
        total_time = sum(
            t.get('duration', 0) 
            for t in self.stage_timings.values()
        )
        
        if total_time == 0 or self.audio_duration == 0:
            return 0.0
        
        # RTF > 1.0 means faster than realtime
        # RTF < 1.0 means slower than realtime
        rtf = self.audio_duration / total_time
        
        return round(rtf, 2)
    
    def _get_memory_usage_mb(self) -> float:
        """Get current memory usage in MB.
        
        Returns:
            Memory usage in MB
        """
        try:
            process = psutil.Process()
            mem_info = process.memory_info()
            return round(mem_info.rss / 1024 / 1024, 1)  # Convert to MB
        except Exception as e:
            self.logger.debug(f"Could not get memory usage: {e}")
            return 0.0
    
    def _get_memory_peak_mb(self) -> float:
        """Get peak memory usage.
        
        Returns:
            Peak memory in MB
        """
        if not self.stage_timings:
            return 0.0
        
        peak = max(
            max(
                t.get('memory_start', 0),
                t.get('memory_end', 0)
            )
            for t in self.stage_timings.values()
        )
        
        return round(peak, 1)
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate performance metrics report.
        
        Returns:
            Performance metrics dictionary
        """
        total_time = sum(
            t.get('duration', 0) 
            for t in self.stage_timings.values()
        )
        
        # Calculate stage percentages
        stage_percentages = {}
        if total_time > 0:
            for stage, timing in self.stage_timings.items():
                duration = timing.get('duration', 0)
                percentage = (duration / total_time) * 100
                stage_percentages[stage] = round(percentage, 1)
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_processing_time': round(total_time, 2),
            'audio_duration': self.audio_duration,
            'real_time_factor': self.calculate_rtf(),
            'memory_peak_mb': self._get_memory_peak_mb(),
            'stage_timings': self.stage_timings,
            'stage_percentages': stage_percentages,
        }
        
        return report
    
    def save_report(self, filename: str = "performance_report.json") -> Optional[Path]:
        """Save performance report to file.
        
        Args:
            filename: Output filename
            
        Returns:
            Path to saved report, or None if no job_dir
        """
        if not self.job_dir:
            self.logger.warning("No job directory specified, cannot save report")
            return None
        
        report = self.generate_report()
        report_path = self.job_dir / filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"✓ Performance report saved: {filename}")
        
        return report_path
    
    def print_summary(self) -> None:
        """Print performance summary to console."""
        report = self.generate_report()
        
        print("\n" + "=" * 80)
        print("PERFORMANCE SUMMARY")
        print("=" * 80)
        print(f"Total Processing Time: {report['total_processing_time']:.1f}s")
        print(f"Audio Duration: {report['audio_duration']:.1f}s")
        print(f"Real-Time Factor: {report['real_time_factor']:.2f}x")
        print(f"Peak Memory Usage: {report['memory_peak_mb']:.0f}MB")
        print("\nStage Breakdown:")
        print("-" * 80)
        
        # Sort stages by duration
        sorted_stages = sorted(
            self.stage_timings.items(),
            key=lambda x: x[1].get('duration', 0),
            reverse=True
        )
        
        for stage, timing in sorted_stages:
            duration = timing.get('duration', 0)
            percentage = report['stage_percentages'].get(stage, 0)
            print(f"  {stage:30s} {duration:8.1f}s  ({percentage:5.1f}%)")
        
        print("=" * 80)


def main():
    """Command-line interface for performance tracker."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Track pipeline performance")
    parser.add_argument("job_dir", type=Path, help="Job directory path")
    parser.add_argument("--audio-duration", type=float, help="Audio duration in seconds")
    
    args = parser.parse_args()
    
    # This is mainly for testing; real usage is integrated in pipeline
    tracker = PerformanceTracker(args.job_dir)
    
    if args.audio_duration:
        tracker.set_audio_duration(args.audio_duration)
    
    # Example: simulate some stages
    stages = ["demux", "asr", "translation", "subtitle_generation"]
    
    for stage in stages:
        tracker.start_stage(stage)
        time.sleep(0.1)  # Simulate work
        tracker.end_stage(stage)
    
    # Generate and save report
    tracker.save_report()
    tracker.print_summary()


if __name__ == "__main__":
    main()
