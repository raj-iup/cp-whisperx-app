#!/usr/bin/env python3
"""
Performance Benchmark Tests

Tests that measure and validate performance characteristics.

Phase 2: Testing Infrastructure - Session 4, Task 1
"""

# Standard library
import sys
import time
import psutil
from pathlib import Path
from typing import Dict, Any
from dataclasses import dataclass

# Third-party
import pytest

# Local
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@dataclass
class PerformanceBenchmark:
    """Performance benchmark thresholds."""
    max_execution_time: float
    max_memory_mb: float
    name: str


@pytest.fixture
def stage_performance_benchmarks() -> Dict[str, PerformanceBenchmark]:
    """Performance benchmarks for stages."""
    return {
        "01_demux": PerformanceBenchmark("01_demux", 20.0, 500.0),
        "02_tmdb": PerformanceBenchmark("02_tmdb", 10.0, 200.0),
        "06_whisperx_asr": PerformanceBenchmark("06_whisperx_asr", 300.0, 4000.0),
        "08_translation": PerformanceBenchmark("08_translation", 120.0, 3000.0),
        "10_mux": PerformanceBenchmark("10_mux", 30.0, 500.0),
    }


@pytest.mark.performance
class TestPerformanceInfrastructure:
    """Test performance testing infrastructure."""
    
    def test_performance_benchmarks_defined(
        self,
        stage_performance_benchmarks: Dict[str, PerformanceBenchmark]
    ):
        """Test that performance benchmarks are defined."""
        expected = ["01_demux", "02_tmdb", "06_whisperx_asr", "08_translation", "10_mux"]
        for stage in expected:
            assert stage in stage_performance_benchmarks
    
    def test_benchmark_values_reasonable(
        self,
        stage_performance_benchmarks: Dict[str, PerformanceBenchmark]
    ):
        """Test that benchmark values are reasonable."""
        for stage_name, benchmark in stage_performance_benchmarks.items():
            assert 0 < benchmark.max_execution_time <= 600
            assert 0 < benchmark.max_memory_mb <= 10000


@pytest.mark.performance
class TestSystemResources:
    """Test system resource availability."""
    
    def test_system_has_sufficient_memory(self):
        """Test that system has sufficient memory."""
        memory = psutil.virtual_memory()
        total_gb = memory.total / 1024 / 1024 / 1024
        if total_gb < 8:
            pytest.skip(f"System has {total_gb:.1f}GB RAM, recommended ≥8GB")
        assert total_gb >= 4
    
    def test_system_has_sufficient_disk_space(self):
        """Test that system has sufficient disk space."""
        disk = psutil.disk_usage(str(PROJECT_ROOT))
        free_gb = disk.free / 1024 / 1024 / 1024
        assert free_gb >= 10
    
    def test_system_cpu_count(self):
        """Test system CPU count."""
        cpu_count = psutil.cpu_count()
        assert cpu_count >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
