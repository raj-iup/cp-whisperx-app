#!/usr/bin/env python3
"""
Shared Hardware Detection Module

Provides unified hardware detection and caching across all scripts.
Used by bootstrap, prepare-job, and preflight.

Features:
- CPU cores/threads detection
- RAM detection
- GPU detection (CUDA/MPS/CPU)
- Hardware capability caching (1-hour validity)
- Optimal settings calculation
"""

import json
import platform
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple


def detect_cpu_info() -> Dict:
    """Detect CPU information."""
    try:
        import psutil
        
        return {
            'cores': psutil.cpu_count(logical=False) or 1,
            'threads': psutil.cpu_count(logical=True) or 1,
            'brand': platform.processor() or 'Unknown'
        }
    except ImportError:
        # Fallback if psutil not available
        import os
        return {
            'cores': os.cpu_count() or 1,
            'threads': os.cpu_count() or 1,
            'brand': platform.processor() or 'Unknown'
        }


def detect_memory_info() -> Dict:
    """Detect system memory."""
    try:
        import psutil
        mem = psutil.virtual_memory()
        return {
            'total_gb': round(mem.total / (1024**3), 2),
            'available_gb': round(mem.available / (1024**3), 2),
            'used_percent': mem.percent
        }
    except ImportError:
        # Fallback estimation
        return {
            'total_gb': 8.0,
            'available_gb': 4.0,
            'used_percent': 50.0
        }


def detect_nvidia_gpu() -> Tuple[bool, Optional[str], Optional[str], Optional[float]]:
    """
    Detect NVIDIA GPU using nvidia-smi.
    
    Returns:
        Tuple of (has_gpu, gpu_name, cuda_version, gpu_memory_gb)
    """
    try:
        # Check if nvidia-smi exists
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0 and result.stdout.strip():
            lines = result.stdout.strip().split('\n')
            if lines:
                # Parse first GPU
                parts = lines[0].split(',')
                gpu_name = parts[0].strip()
                gpu_memory_mb = float(parts[1].strip().replace(' MiB', ''))
                gpu_memory_gb = round(gpu_memory_mb / 1024, 2)
                
                # Get CUDA version
                cuda_version = None
                result2 = subprocess.run(
                    ['nvidia-smi'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result2.returncode == 0:
                    # Parse "CUDA Version: X.Y"
                    import re
                    match = re.search(r'CUDA Version:\s*(\d+\.\d+)', result2.stdout)
                    if match:
                        cuda_version = match.group(1)
                
                return True, gpu_name, cuda_version, gpu_memory_gb
        
        return False, None, None, None
        
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        return False, None, None, None


def detect_apple_silicon() -> bool:
    """Detect Apple Silicon (M1/M2/M3)."""
    if platform.system() != 'Darwin':
        return False
    
    try:
        result = subprocess.run(
            ['sysctl', '-n', 'machdep.cpu.brand_string'],
            capture_output=True,
            text=True,
            timeout=2
        )
        
        if result.returncode == 0:
            brand = result.stdout.strip()
            return 'Apple' in brand
            
    except Exception:
        pass
    
    return False


def detect_gpu_with_torch() -> Tuple[str, Optional[str], Optional[float]]:
    """
    Detect GPU using PyTorch (if available).
    
    Returns:
        Tuple of (gpu_type, gpu_name, gpu_memory_gb)
        gpu_type: 'cuda', 'mps', or 'cpu'
    """
    try:
        import torch
        
        # Check CUDA
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory_bytes = torch.cuda.get_device_properties(0).total_memory
            gpu_memory_gb = round(gpu_memory_bytes / (1024**3), 2)
            return 'cuda', gpu_name, gpu_memory_gb
        
        # Check MPS (Apple Silicon)
        if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            # Estimate MPS memory based on system RAM
            import psutil
            total_ram = psutil.virtual_memory().total / (1024**3)
            # MPS typically uses unified memory (50% of RAM as estimate)
            gpu_memory_gb = round(min(total_ram * 0.5, 16.0), 2)
            return 'mps', 'Apple Silicon (MPS)', gpu_memory_gb
        
        return 'cpu', None, None
        
    except ImportError:
        # PyTorch not available, use nvidia-smi fallback
        has_gpu, gpu_name, cuda_version, gpu_memory = detect_nvidia_gpu()
        if has_gpu:
            return 'cuda', gpu_name, gpu_memory
        
        # Check Apple Silicon without torch
        if detect_apple_silicon():
            return 'mps', 'Apple Silicon (MPS)', 8.0
        
        return 'cpu', None, None


def calculate_optimal_settings(hw_info: Dict) -> Dict:
    """
    Calculate optimal pipeline settings based on hardware.
    
    Args:
        hw_info: Hardware information dict
        
    Returns:
        Dict with recommended settings
    """
    gpu_type = hw_info.get('gpu_type', 'cpu')
    gpu_memory_gb = hw_info.get('gpu_memory_gb', 0) or 0
    memory_gb = hw_info.get('memory_gb', 8)
    cpu_cores = hw_info.get('cpu_cores', 1)
    
    settings = {
        'whisper_model': 'base',
        'whisper_model_reason': '',
        'batch_size': 1,
        'batch_size_reason': '',
        'compute_type': 'int8',
        'compute_type_reason': '',
        'chunk_length_s': 30,
        'chunk_length_reason': 'Standard chunk size for most media',
        'max_speakers': 10,
        'max_speakers_reason': 'Default maximum speakers',
        'use_docker_cpu_fallback': True,
        'docker_recommendation': ''
    }
    
    # Model selection based on GPU memory
    if gpu_type in ['cuda', 'mps']:
        if gpu_memory_gb >= 10:
            settings['whisper_model'] = 'large-v3'
            settings['whisper_model_reason'] = f'GPU has {gpu_memory_gb}GB VRAM - can handle large-v3 model'
            settings['batch_size'] = 16
            settings['batch_size_reason'] = f'{gpu_memory_gb}GB VRAM supports large batches'
            settings['compute_type'] = 'float16'
            settings['compute_type_reason'] = 'GPU supports float16 precision'
            settings['docker_recommendation'] = 'Use GPU images for best performance'
            
        elif gpu_memory_gb >= 6:
            settings['whisper_model'] = 'medium'
            settings['whisper_model_reason'] = f'GPU has {gpu_memory_gb}GB VRAM - medium model recommended'
            settings['batch_size'] = 8
            settings['batch_size_reason'] = f'{gpu_memory_gb}GB VRAM supports medium batches'
            settings['compute_type'] = 'float16'
            settings['compute_type_reason'] = 'GPU supports float16 precision'
            settings['docker_recommendation'] = 'Use GPU images for good performance'
            
        else:
            settings['whisper_model'] = 'base'
            settings['whisper_model_reason'] = f'GPU has {gpu_memory_gb}GB VRAM - base model recommended'
            settings['batch_size'] = 4
            settings['batch_size_reason'] = f'{gpu_memory_gb}GB VRAM limits batch size'
            settings['compute_type'] = 'float16' if gpu_type == 'cuda' else 'float32'
            settings['compute_type_reason'] = 'Limited VRAM requires smaller precision' if gpu_type == 'cuda' else 'MPS prefers float32'
            settings['docker_recommendation'] = 'GPU available but limited - native mode recommended'
    
    else:
        # CPU-only mode
        settings['whisper_model'] = 'base'
        settings['whisper_model_reason'] = 'CPU-only mode - base model for reasonable speed'
        settings['batch_size'] = 1
        settings['batch_size_reason'] = 'CPU mode uses sequential processing'
        settings['compute_type'] = 'int8'
        settings['compute_type_reason'] = 'CPU mode benefits from quantization'
        settings['docker_recommendation'] = 'Use CPU images (native mode faster)'
        
        # Adjust for high-core CPUs
        if cpu_cores >= 8:
            settings['batch_size'] = 2
            settings['batch_size_reason'] = f'{cpu_cores} CPU cores allow small batches'
    
    # Adjust chunk length based on memory
    if memory_gb < 8:
        settings['chunk_length_s'] = 20
        settings['chunk_length_reason'] = 'Limited RAM requires shorter chunks'
    elif memory_gb >= 16:
        settings['chunk_length_s'] = 30
        settings['chunk_length_reason'] = 'Sufficient RAM for standard chunks'
    
    # Adjust max speakers based on resources
    if gpu_type in ['cuda', 'mps'] and gpu_memory_gb >= 6:
        settings['max_speakers'] = 15
        settings['max_speakers_reason'] = 'GPU resources support more speakers'
    elif memory_gb >= 16:
        settings['max_speakers'] = 12
        settings['max_speakers_reason'] = 'Good RAM allows more speakers'
    else:
        settings['max_speakers'] = 8
        settings['max_speakers_reason'] = 'Limited resources cap speaker count'
    
    return settings


def detect_hardware_full() -> Dict:
    """
    Complete hardware detection.
    
    Returns:
        Dict with all hardware info and recommended settings
    """
    print("🔍 Detecting hardware capabilities...")
    
    # CPU detection
    cpu_info = detect_cpu_info()
    print(f"  ✓ CPU: {cpu_info['cores']} cores, {cpu_info['threads']} threads")
    
    # Memory detection
    mem_info = detect_memory_info()
    print(f"  ✓ RAM: {mem_info['total_gb']} GB total, {mem_info['available_gb']} GB available")
    
    # GPU detection
    gpu_type, gpu_name, gpu_memory_gb = detect_gpu_with_torch()
    
    if gpu_type == 'cuda':
        # Get CUDA version from nvidia-smi
        _, _, cuda_version, _ = detect_nvidia_gpu()
        print(f"  ✓ GPU: {gpu_name} (CUDA {cuda_version or 'unknown'})")
        print(f"  ✓ VRAM: {gpu_memory_gb} GB")
    elif gpu_type == 'mps':
        print(f"  ✓ GPU: {gpu_name}")
        print(f"  ✓ Unified Memory: ~{gpu_memory_gb} GB available for GPU")
    else:
        print(f"  ✓ GPU: Not available (CPU mode)")
    
    # Build hardware info
    hw_info = {
        'detected_at': datetime.now().isoformat(),
        'platform': platform.system(),
        'cpu_cores': cpu_info['cores'],
        'cpu_threads': cpu_info['threads'],
        'cpu_brand': cpu_info['brand'],
        'memory_gb': mem_info['total_gb'],
        'memory_available_gb': mem_info['available_gb'],
        'gpu_available': gpu_type in ['cuda', 'mps'],
        'gpu_type': gpu_type,
        'gpu_name': gpu_name,
        'gpu_memory_gb': gpu_memory_gb,
    }
    
    # Add CUDA version if available
    if gpu_type == 'cuda':
        _, _, cuda_version, _ = detect_nvidia_gpu()
        hw_info['cuda_version'] = cuda_version
    
    # Calculate optimal settings
    hw_info['recommended_settings'] = calculate_optimal_settings(hw_info)
    
    return hw_info


def save_hardware_cache(hw_info: Dict, cache_file: Path = None) -> None:
    """
    Save hardware info to cache file.
    
    Args:
        hw_info: Hardware information dict
        cache_file: Path to cache file (default: out/hardware_cache.json)
    """
    if cache_file is None:
        cache_file = Path('out/hardware_cache.json')
    
    # Ensure directory exists
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Save with pretty formatting
    with open(cache_file, 'w') as f:
        json.dump(hw_info, f, indent=2)
    
    print(f"  ✓ Hardware cache saved: {cache_file}")


def load_hardware_cache(cache_file: Path = None, max_age_hours: float = 1.0) -> Optional[Dict]:
    """
    Load hardware info from cache if fresh.
    
    Args:
        cache_file: Path to cache file (default: out/hardware_cache.json)
        max_age_hours: Maximum cache age in hours (default: 1.0)
        
    Returns:
        Hardware info dict if cache is fresh, None otherwise
    """
    if cache_file is None:
        cache_file = Path('out/hardware_cache.json')
    
    if not cache_file.exists():
        return None
    
    # Check age
    age_seconds = time.time() - cache_file.stat().st_mtime
    age_hours = age_seconds / 3600
    
    if age_hours > max_age_hours:
        return None
    
    # Load cache
    try:
        with open(cache_file) as f:
            hw_info = json.load(f)
        
        print(f"  ✓ Using cached hardware info (age: {age_hours:.1f}h)")
        return hw_info
        
    except (json.JSONDecodeError, Exception) as e:
        print(f"  ⚠ Failed to load hardware cache: {e}")
        return None


def get_hardware_info(use_cache: bool = True, max_age_hours: float = 1.0) -> Dict:
    """
    Get hardware info with optional caching.
    
    Args:
        use_cache: Whether to use cached info if available
        max_age_hours: Maximum cache age in hours
        
    Returns:
        Hardware info dict
    """
    cache_file = Path('out/hardware_cache.json')
    
    # Try cache first if enabled
    if use_cache:
        cached = load_hardware_cache(cache_file, max_age_hours)
        if cached:
            return cached
    
    # Detect hardware
    hw_info = detect_hardware_full()
    
    # Save to cache
    save_hardware_cache(hw_info, cache_file)
    
    return hw_info


def display_hardware_summary(hw_info: Dict) -> None:
    """Display hardware info summary."""
    settings = hw_info.get('recommended_settings', {})
    
    print("\n" + "="*70)
    print("HARDWARE PROFILE")
    print("="*70)
    print(f"CPU: {hw_info['cpu_cores']} cores ({hw_info['cpu_threads']} threads)")
    print(f"RAM: {hw_info['memory_gb']} GB")
    
    if hw_info['gpu_available']:
        print(f"GPU: {hw_info['gpu_name']} ({hw_info['gpu_type'].upper()})")
        print(f"VRAM: {hw_info['gpu_memory_gb']} GB")
    else:
        print("GPU: Not available (CPU mode)")
    
    print("\nRECOMMENDED SETTINGS:")
    print(f"  Whisper Model: {settings['whisper_model']}")
    print(f"    → {settings['whisper_model_reason']}")
    print(f"  Batch Size: {settings['batch_size']}")
    print(f"    → {settings['batch_size_reason']}")
    print(f"  Compute Type: {settings['compute_type']}")
    print(f"    → {settings['compute_type_reason']}")
    print(f"  Docker: {settings['docker_recommendation']}")
    print("="*70 + "\n")


if __name__ == "__main__":
    """CLI interface for hardware detection."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Hardware detection utility")
    parser.add_argument('--no-cache', action='store_true', help="Force fresh detection")
    parser.add_argument('--max-age', type=float, default=1.0, help="Max cache age in hours")
    parser.add_argument('--json', action='store_true', help="Output JSON only")
    args = parser.parse_args()
    
    # Get hardware info
    hw_info = get_hardware_info(use_cache=not args.no_cache, max_age_hours=args.max_age)
    
    if args.json:
        # JSON output only
        print(json.dumps(hw_info, indent=2))
    else:
        # Human-readable summary
        display_hardware_summary(hw_info)
