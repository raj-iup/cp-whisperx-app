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

CONFIGURATION FLOW:
==================

1. Hardware Detection (Existing + Enhanced):
   - shared/hardware_detection.py detects CPU, memory, GPU type (MPS/CUDA/CPU)
   - Calculates optimal batch sizes based on GPU memory
   - Saves recommendations to out/hardware_cache.json
   - Updates config/.env.pipeline with tuned parameters (DEVICE, BATCH_SIZE, etc.)

2. Auto-Configuration (Enhanced):
   - scripts/bootstrap.sh reads hardware cache
   - Exports DEVICE_OVERRIDE with detected device
   - Logs recommended batch size (saved to config/.env.pipeline)
   - Sets MPS environment variables if macOS (PYTORCH_MPS_HIGH_WATERMARK_RATIO, etc.)
   - All tuned parameters saved to config/.env.pipeline

3. Job Preparation:
   - prepare-job.sh/prepare-job.py copies config/.env.pipeline
   - Creates job-specific .env file with output directory structure
   - Job inherits all hardware-optimized settings from config/.env.pipeline

4. Runtime Integration (Existing):
   - All ML stages use device_selector.py
   - Reads DEVICE from job environment file (inherited from config/.env.pipeline)
   - Falls back gracefully (mps → cuda → cpu)
   - MPS batch sizes auto-optimized for stability by pipeline orchestrator
"""

import json
import platform
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

# Fix Unicode encoding issues on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


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


def detect_nvidia_gpu() -> Tuple[bool, Optional[str], Optional[str], Optional[float], Optional[str]]:
    """
    Detect NVIDIA GPU using nvidia-smi.
    
    Returns:
        Tuple of (has_gpu, gpu_name, cuda_version, gpu_memory_gb, compute_capability)
    """
    try:
        # Check if nvidia-smi exists
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=name,memory.total,compute_cap', '--format=csv,noheader'],
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
                compute_cap = parts[2].strip() if len(parts) > 2 else None
                
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
                
                return True, gpu_name, cuda_version, gpu_memory_gb, compute_cap
        
        return False, None, None, None, None
        
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        return False, None, None, None, None


def detect_apple_silicon() -> Tuple[bool, Optional[str], Optional[float]]:
    """
    Detect Apple Silicon (M1/M2/M3/M4).
    
    Returns:
        Tuple of (is_apple_silicon, chip_name, estimated_gpu_memory_gb)
    """
    if platform.system() != 'Darwin':
        return False, None, None
    
    try:
        result = subprocess.run(
            ['sysctl', '-n', 'machdep.cpu.brand_string'],
            capture_output=True,
            text=True,
            timeout=2
        )
        
        if result.returncode == 0:
            brand = result.stdout.strip()
            if 'Apple' in brand:
                # Try to determine chip type and estimate memory
                chip_name = brand
                
                # Get total RAM to estimate GPU memory (unified memory)
                try:
                    import psutil
                    total_ram = psutil.virtual_memory().total / (1024**3)
                    
                    # Estimate GPU memory based on total RAM
                    # Apple Silicon uses unified memory
                    if total_ram >= 64:
                        gpu_memory = 32.0  # M1/M2/M3 Ultra or Max with 64GB+
                    elif total_ram >= 32:
                        gpu_memory = 16.0  # M1/M2/M3 Max
                    elif total_ram >= 16:
                        gpu_memory = 10.0  # M1/M2/M3 Pro
                    else:
                        gpu_memory = 8.0   # M1/M2/M3 Base
                    
                    return True, chip_name, gpu_memory
                except:
                    return True, chip_name, 8.0
            
    except Exception:
        pass
    
    return False, None, None


def detect_gpu_with_torch() -> Tuple[str, Optional[str], Optional[float], Optional[str], Optional[str]]:
    """
    Detect GPU using PyTorch (if available) with enhanced support for all hardware.
    
    Returns:
        Tuple of (gpu_type, gpu_name, gpu_memory_gb, compute_capability, pytorch_compatible)
        gpu_type: 'cuda', 'mps', or 'cpu'
        pytorch_compatible: 'full', 'legacy', or 'incompatible'
    """
    try:
        import torch
        
        # Check CUDA
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory_bytes = torch.cuda.get_device_properties(0).total_memory
            gpu_memory_gb = round(gpu_memory_bytes / (1024**3), 2)
            
            # Get compute capability
            props = torch.cuda.get_device_properties(0)
            compute_cap = f"{props.major}.{props.minor}"
            
            # Determine PyTorch compatibility
            major_cc = props.major
            if major_cc >= 7:
                pytorch_compatible = 'full'  # Fully supported by PyTorch 2.x
            elif major_cc >= 5:
                pytorch_compatible = 'legacy'  # Needs PyTorch 1.x
            else:
                pytorch_compatible = 'incompatible'  # Too old
            
            return 'cuda', gpu_name, gpu_memory_gb, compute_cap, pytorch_compatible
        
        # Check MPS (Apple Silicon)
        if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            # Get Apple Silicon info
            is_apple, chip_name, gpu_memory = detect_apple_silicon()
            if is_apple:
                return 'mps', chip_name, gpu_memory, 'N/A', 'full'
            else:
                # Fallback estimation
                import psutil
                total_ram = psutil.virtual_memory().total / (1024**3)
                gpu_memory_gb = round(min(total_ram * 0.5, 16.0), 2)
                return 'mps', 'Apple Silicon (MPS)', gpu_memory_gb, 'N/A', 'full'
        
        return 'cpu', None, None, None, None
        
    except ImportError:
        # PyTorch not available, use nvidia-smi fallback for detection
        has_gpu, gpu_name, cuda_version, gpu_memory, compute_cap = detect_nvidia_gpu()
        if has_gpu:
            # Determine compatibility without PyTorch
            if compute_cap:
                major_cc = int(float(compute_cap))
                if major_cc >= 7:
                    pytorch_compatible = 'full'
                elif major_cc >= 5:
                    pytorch_compatible = 'legacy'
                else:
                    pytorch_compatible = 'incompatible'
            else:
                pytorch_compatible = 'unknown'
            
            return 'cuda', gpu_name, gpu_memory, compute_cap, pytorch_compatible
        
        # Check Apple Silicon without torch
        is_apple, chip_name, gpu_memory = detect_apple_silicon()
        if is_apple:
            return 'mps', chip_name, gpu_memory, 'N/A', 'full'
        
        return 'cpu', None, None, None, None


def calculate_optimal_batch_size(gpu_type: str, gpu_memory_gb: float, whisper_model: str) -> int:
    """
    Calculate optimal batch size based on GPU memory and model size.
    
    Phase 3 Enhancement: Smart batch size calculation
    
    Args:
        gpu_type: 'cuda', 'mps', or 'cpu'
        gpu_memory_gb: Available GPU memory in GB
        whisper_model: Whisper model name ('base', 'medium', 'large-v3')
    
    Returns:
        Optimal batch size
    """
    if gpu_type == 'cpu':
        return 1
    
    # Model memory requirements (approximate, in GB)
    model_memory = {
        'tiny': 0.5,
        'base': 1.0,
        'small': 2.0,
        'medium': 3.5,
        'large': 6.0,
        'large-v2': 6.5,
        'large-v3': 7.0,
    }
    
    model_size = model_memory.get(whisper_model, 1.0)
    
    # Calculate available memory for batches (leave 20% headroom)
    available_for_batches = (gpu_memory_gb - model_size) * 0.8
    
    # Estimate memory per batch item (varies by model)
    memory_per_item = {
        'tiny': 0.3,
        'base': 0.4,
        'small': 0.6,
        'medium': 0.8,
        'large': 1.0,
        'large-v2': 1.1,
        'large-v3': 1.2,
    }
    
    item_memory = memory_per_item.get(whisper_model, 0.5)
    
    # Calculate batch size
    if available_for_batches > 0:
        batch_size = int(available_for_batches / item_memory)
        # Cap at reasonable limits
        batch_size = max(1, min(batch_size, 32 if gpu_type == 'cuda' else 16))
    else:
        batch_size = 1
    
    return batch_size


def calculate_optimal_settings(hw_info: Dict) -> Dict:
    """
    Calculate optimal pipeline settings based on hardware.
    
    ENHANCED: Prioritizes large-v3 for Bollywood/Hinglish content accuracy
    Supports older GPUs (CC 5.0+) and Apple Silicon MPS
    Handles cases where physical GPU exists but PyTorch can't use it
    
    Args:
        hw_info: Hardware information dict
        
    Returns:
        Dict with recommended settings optimized for Hinglish transcription
    """
    gpu_type = hw_info.get('gpu_type', 'cpu')
    gpu_memory_gb = hw_info.get('gpu_memory_gb', 0) or 0
    memory_gb = hw_info.get('memory_gb', 8)
    cpu_cores = hw_info.get('cpu_cores', 1)
    compute_cap = hw_info.get('compute_capability', None)
    pytorch_compatible = hw_info.get('pytorch_compatible', 'unknown')
    gpu_name = hw_info.get('gpu_name', None)
    
    settings = {
        'whisper_model': 'large-v3',  # DEFAULT: large-v3 for Bollywood/Hinglish accuracy
        'whisper_model_reason': '',
        'batch_size': 1,
        'batch_size_reason': '',
        'compute_type': 'int8',
        'compute_type_reason': '',
        'chunk_length_s': 30,
        'chunk_length_reason': 'Standard chunk size for Hinglish movies',
        'max_speakers': 10,
        'max_speakers_reason': 'Default for multi-speaker Bollywood content',
        'use_docker_cpu_fallback': True,
        'docker_recommendation': '',
        'performance_profile': 'high-accuracy',
        'estimated_speedup': '1x',
        'gpu_compatibility': pytorch_compatible,
        'legacy_gpu_support': False
    }
    
    # ========================================================================
    # GPU ACCELERATION (Modern GPUs with PyTorch 2.x support - CC >= 7.0)
    # ========================================================================
    if gpu_type in ['cuda', 'mps'] and pytorch_compatible == 'full':
        
        if gpu_memory_gb >= 12:
            # High-end GPU (RTX 3090, 4090, A100, M2/M3 Max, etc.)
            settings['whisper_model'] = 'large-v3'
            settings['whisper_model_reason'] = f'GPU has {gpu_memory_gb}GB - perfect for large-v3 Hinglish accuracy'
            settings['compute_type'] = 'float16'
            settings['compute_type_reason'] = 'GPU supports efficient float16 for best quality'
            settings['docker_recommendation'] = 'Use GPU images for maximum performance'
            settings['performance_profile'] = 'ultra-quality-bollywood'
            settings['estimated_speedup'] = '15-20x vs CPU'
            
        elif gpu_memory_gb >= 8:
            # Mid-high GPU (RTX 3070, 4070, M1/M2 Pro, etc.)
            settings['whisper_model'] = 'large-v3'
            settings['whisper_model_reason'] = f'GPU has {gpu_memory_gb}GB - can run large-v3 with optimized batches'
            settings['compute_type'] = 'float16'
            settings['compute_type_reason'] = 'GPU float16 for high-quality Hinglish'
            settings['docker_recommendation'] = 'Use GPU images for best quality'
            settings['performance_profile'] = 'high-quality-bollywood'
            settings['estimated_speedup'] = '12-15x vs CPU'
            
        elif gpu_memory_gb >= 6:
            # Mid-range GPU (RTX 3060, 4060, M1/M2 base)
            settings['whisper_model'] = 'large-v3'
            settings['whisper_model_reason'] = f'GPU has {gpu_memory_gb}GB - large-v3 feasible with batch_size=1'
            settings['compute_type'] = 'float16'
            settings['compute_type_reason'] = 'GPU float16 for quality Hinglish transcription'
            settings['docker_recommendation'] = 'Use GPU images'
            settings['performance_profile'] = 'balanced-quality-bollywood'
            settings['estimated_speedup'] = '10-12x vs CPU'
            
        elif gpu_memory_gb >= 4:
            # Entry GPU (RTX 3050, GTX 1650)
            settings['whisper_model'] = 'medium'
            settings['whisper_model_reason'] = f'GPU has {gpu_memory_gb}GB - medium model balances speed/accuracy for Hinglish'
            settings['compute_type'] = 'float16'
            settings['compute_type_reason'] = 'GPU float16 optimization'
            settings['docker_recommendation'] = 'Use GPU images'
            settings['performance_profile'] = 'balanced-bollywood'
            settings['estimated_speedup'] = '8-10x vs CPU'
            
        else:
            # Minimal GPU (<4GB)
            settings['whisper_model'] = 'base'
            settings['whisper_model_reason'] = f'GPU has {gpu_memory_gb}GB - base model for speed'
            settings['compute_type'] = 'float16' if gpu_type == 'cuda' else 'float32'
            settings['compute_type_reason'] = 'Limited VRAM requires smaller model'
            settings['docker_recommendation'] = 'GPU limited - consider CPU mode'
            settings['performance_profile'] = 'speed-focused'
            settings['estimated_speedup'] = '6-8x vs CPU'
        
        # Smart Batch Size Calculation
        settings['batch_size'] = calculate_optimal_batch_size(gpu_type, gpu_memory_gb, settings['whisper_model'])
        settings['batch_size_reason'] = f'Auto-calculated for {gpu_memory_gb}GB VRAM + {settings["whisper_model"]} model'
    
    # ========================================================================
    # LEGACY GPU SUPPORT (Older GPUs with PyTorch 1.x - CC 5.0-6.9)
    # ========================================================================
    elif gpu_type == 'cuda' and pytorch_compatible == 'legacy':
        settings['legacy_gpu_support'] = True
        settings['gpu_compatibility'] = 'legacy'
        
        if gpu_memory_gb >= 6:
            # GTX 980 Ti, GTX 1060 6GB
            settings['whisper_model'] = 'large-v3'
            settings['whisper_model_reason'] = f'Legacy GPU ({compute_cap}) with {gpu_memory_gb}GB - large-v3 for Hinglish accuracy'
            settings['compute_type'] = 'float16'
            settings['compute_type_reason'] = 'Legacy GPU with float16 support'
            settings['docker_recommendation'] = 'Requires PyTorch 1.13 for legacy GPU support'
            settings['performance_profile'] = 'legacy-quality-bollywood'
            settings['estimated_speedup'] = '5-8x vs CPU'
            settings['batch_size'] = 1
            settings['batch_size_reason'] = f'Conservative batch for legacy GPU (CC {compute_cap})'
            
        elif gpu_memory_gb >= 4:
            # GTX 970, GTX 1050 Ti, GTX 750 Ti
            settings['whisper_model'] = 'medium'
            settings['whisper_model_reason'] = f'Legacy GPU ({compute_cap}) with {gpu_memory_gb}GB - medium for balanced Hinglish'
            settings['compute_type'] = 'float16'
            settings['compute_type_reason'] = 'Legacy GPU optimization'
            settings['docker_recommendation'] = 'Requires PyTorch 1.13 for legacy GPU (CC {})'.format(compute_cap)
            settings['performance_profile'] = 'legacy-balanced-bollywood'
            settings['estimated_speedup'] = '3-5x vs CPU'
            settings['batch_size'] = 1
            settings['batch_size_reason'] = f'Legacy GPU (CC {compute_cap}) limited batching'
            
        else:
            # GTX 750, very old cards
            settings['whisper_model'] = 'base'
            settings['whisper_model_reason'] = f'Legacy GPU ({compute_cap}) with {gpu_memory_gb}GB - base model only'
            settings['compute_type'] = 'float16'
            settings['compute_type_reason'] = 'Legacy GPU - minimal requirements'
            settings['docker_recommendation'] = 'Legacy GPU limited - consider CPU mode or PyTorch 1.13'
            settings['performance_profile'] = 'legacy-speed'
            settings['estimated_speedup'] = '2-3x vs CPU'
            settings['batch_size'] = 1
            settings['batch_size_reason'] = 'Legacy GPU minimal batch'
    
    # ========================================================================
    # GPU-UNAVAILABLE MODE (Physical GPU exists but PyTorch can't use it)
    # ========================================================================
    elif gpu_type == 'cuda-unavailable':
        # Physical GPU detected but PyTorch is CPU-only build or legacy
        settings['docker_recommendation'] = 'CPU images (PyTorch cannot use GPU)'
        
        if pytorch_compatible == 'cpu-only-build':
            # Modern GPU but CPU-only PyTorch build
            settings['whisper_model_reason'] = f'{gpu_name} detected but PyTorch is CPU-only build - install CUDA PyTorch to use GPU'
            settings['docker_recommendation'] += f'\n  → Install: pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121'
        elif pytorch_compatible == 'legacy':
            # Legacy GPU  
            settings['whisper_model_reason'] = f'{gpu_name} (CC {compute_cap}) requires PyTorch 1.13 - currently using CPU'
            settings['docker_recommendation'] += f'\n  → Or install PyTorch 1.13 for GPU support (not recommended)'
            settings['legacy_gpu_support'] = True
        else:
            settings['whisper_model_reason'] = f'{gpu_name} detected but cannot be used'
        
        # Fall through to CPU settings
        if memory_gb >= 32:
            settings['whisper_model'] = 'large-v3'
            settings['whisper_model_reason'] += f' | High RAM ({memory_gb}GB) allows large-v3 on CPU'
        elif memory_gb >= 16:
            settings['whisper_model'] = 'large-v3'
            settings['whisper_model_reason'] += f' | Good RAM ({memory_gb}GB) allows large-v3 on CPU (slow)'
        elif memory_gb >= 8:
            settings['whisper_model'] = 'medium'
            settings['whisper_model_reason'] += f' | Limited RAM ({memory_gb}GB) - medium recommended'
        else:
            settings['whisper_model'] = 'base'
            settings['whisper_model_reason'] += f' | Very limited RAM ({memory_gb}GB)'
        
        settings['batch_size'] = 1
        settings['batch_size_reason'] = 'CPU mode (GPU unavailable to PyTorch)'
        settings['compute_type'] = 'int8'
        settings['compute_type_reason'] = 'CPU mode benefits from int8 quantization'
        settings['performance_profile'] = 'cpu-quality-bollywood'
        settings['estimated_speedup'] = 'baseline (1x - GPU not usable)'
        
        if cpu_cores >= 16:
            settings['batch_size'] = 2
            settings['batch_size_reason'] = f'{cpu_cores} CPU cores allow small parallel batches (GPU unavailable)'
    
    # ========================================================================
    # CPU-ONLY MODE (No GPU or incompatible GPU)
    # ========================================================================
    else:
        if memory_gb >= 32:
            # High-end CPU system
            settings['whisper_model'] = 'large-v3'
            settings['whisper_model_reason'] = f'High RAM ({memory_gb}GB) - large-v3 for best Hinglish accuracy (slower)'
            settings['batch_size'] = 1
            settings['batch_size_reason'] = f'{cpu_cores} CPU cores - sequential processing'
            
        elif memory_gb >= 16:
            # Mid-range CPU system
            settings['whisper_model'] = 'large-v3'
            settings['whisper_model_reason'] = f'Good RAM ({memory_gb}GB) - large-v3 feasible for Hinglish (will be slow)'
            settings['batch_size'] = 1
            settings['batch_size_reason'] = f'{cpu_cores} cores - CPU sequential optimal'
            
        elif memory_gb >= 8:
            # Entry-level system
            settings['whisper_model'] = 'medium'
            settings['whisper_model_reason'] = f'Limited RAM ({memory_gb}GB) - medium balances speed/accuracy for Hinglish'
            settings['batch_size'] = 1
            settings['batch_size_reason'] = 'CPU with limited RAM'
            
        else:
            # Very limited system
            settings['whisper_model'] = 'base'
            settings['whisper_model_reason'] = f'Very limited RAM ({memory_gb}GB) - base model only'
            settings['batch_size'] = 1
            settings['batch_size_reason'] = 'Minimal resources'
        
        settings['compute_type'] = 'int8'
        settings['compute_type_reason'] = 'CPU mode benefits from int8 quantization'
        settings['docker_recommendation'] = 'Use CPU images (native mode faster)'
        settings['performance_profile'] = 'cpu-quality-bollywood'
        settings['estimated_speedup'] = 'baseline (1x - will be slow)'
        
        # Adjust for high-core CPUs
        if cpu_cores >= 16:
            settings['batch_size'] = 2
            settings['batch_size_reason'] = f'{cpu_cores} CPU cores allow small parallel batches'
        elif cpu_cores >= 8:
            settings['batch_size'] = 1
            settings['batch_size_reason'] = f'{cpu_cores} CPU cores - sequential optimal'
    
    # Adjust chunk length based on memory
    if memory_gb < 8:
        settings['chunk_length_s'] = 20
        settings['chunk_length_reason'] = 'Limited RAM requires shorter chunks for Hinglish processing'
    elif memory_gb >= 16:
        settings['chunk_length_s'] = 30
        settings['chunk_length_reason'] = 'Sufficient RAM for standard Hinglish movie chunks'
    
    # Adjust max speakers based on resources
    if gpu_type in ['cuda', 'mps'] and gpu_memory_gb >= 6:
        settings['max_speakers'] = 15
        settings['max_speakers_reason'] = 'GPU resources support more speakers for complex Bollywood scenes'
    elif memory_gb >= 16:
        settings['max_speakers'] = 12
        settings['max_speakers_reason'] = 'Good RAM allows more speakers for Hinglish dialogue'
    else:
        settings['max_speakers'] = 8
        settings['max_speakers_reason'] = 'Limited resources cap speaker count'
    
    # ========================================================================
    # WHISPER BACKEND RECOMMENDATION
    # ========================================================================
    # CTranslate2 (faster-whisper) DOES NOT support MPS at all
    # Trade-off for Apple Silicon users:
    #   whisperx (CTranslate2): Supports bias ✅ but CPU-only on MPS (slow)
    #   mlx: Supports MPS GPU ✅ but NO bias prompting ❌
    
    if gpu_type == 'mps':
        # Apple Silicon: MLX is only option for GPU acceleration
        settings['whisper_backend'] = 'mlx'
        settings['whisper_backend_reason'] = 'MPS requires MLX backend (CTranslate2 not compatible with MPS)'
        settings['bias_prompting_supported'] = False
        settings['bias_prompting_note'] = 'MLX does not support bias prompting - speed prioritized over name accuracy'
    elif gpu_type == 'cuda':
        # NVIDIA: CTranslate2 supports CUDA with bias
        settings['whisper_backend'] = 'whisperx'
        settings['whisper_backend_reason'] = 'CUDA-compatible CTranslate2 with bias prompting support'
        settings['bias_prompting_supported'] = True
        settings['bias_prompting_note'] = 'Full bias support (initial_prompt + hotwords)'
    else:
        # CPU: CTranslate2 with bias support
        settings['whisper_backend'] = 'whisperx'
        settings['whisper_backend_reason'] = 'CPU mode with CTranslate2 and bias prompting support'
        settings['bias_prompting_supported'] = True
        settings['bias_prompting_note'] = 'Full bias support (initial_prompt + hotwords) but slow on CPU'
    
    return settings


def detect_hardware_full() -> Dict:
    """
    Complete hardware detection with enhanced GPU support.
    
    ENHANCED: Detects older GPUs (CC 5.0+), Apple Silicon MPS, and all modern GPUs
    Always reports physical GPU hardware even if PyTorch can't use it
    
    Returns:
        Dict with all hardware info and recommended settings optimized for Hinglish
    """
    print("🔍 Detecting hardware capabilities (enhanced)...")
    
    # CPU detection
    cpu_info = detect_cpu_info()
    print(f"  ✓ CPU: {cpu_info['cores']} cores, {cpu_info['threads']} threads")
    
    # Memory detection
    mem_info = detect_memory_info()
    print(f"  ✓ RAM: {mem_info['total_gb']} GB total, {mem_info['available_gb']} GB available")
    
    # GPU detection (enhanced - always check nvidia-smi first)
    physical_gpu_detected = False
    nvidia_gpu_name = None
    nvidia_gpu_memory = None
    nvidia_compute_cap = None
    nvidia_cuda_version = None
    
    # First, check for physical NVIDIA GPU via nvidia-smi
    has_nvidia, gpu_name_nvidia, cuda_ver, gpu_mem_nvidia, compute_cap_nvidia = detect_nvidia_gpu()
    if has_nvidia:
        physical_gpu_detected = True
        nvidia_gpu_name = gpu_name_nvidia
        nvidia_gpu_memory = gpu_mem_nvidia
        nvidia_compute_cap = compute_cap_nvidia
        nvidia_cuda_version = cuda_ver
        print(f"  ✓ Physical GPU: {nvidia_gpu_name}")
        print(f"  ✓ VRAM: {nvidia_gpu_memory} GB")
        print(f"  ✓ CUDA Driver: {nvidia_cuda_version or 'unknown'}")
        print(f"  ✓ Compute Capability: {nvidia_compute_cap}")
    
    # Then check PyTorch GPU availability
    gpu_type, gpu_name, gpu_memory_gb, compute_cap, pytorch_compatible = detect_gpu_with_torch()
    
    # Report PyTorch status
    if gpu_type == 'cuda':
        print(f"  ✓ PyTorch CUDA: Available")
        print(f"  ✓ PyTorch Compatibility: Full support (modern GPU)")
            
    elif gpu_type == 'mps':
        print(f"  ✓ Apple Silicon: {gpu_name}")
        print(f"  ✓ Unified Memory: ~{gpu_memory_gb} GB available for GPU")
        print(f"  ✓ PyTorch MPS: Available")
        
    else:
        # CPU mode - but we might have detected a physical GPU
        if physical_gpu_detected:
            print(f"  ⚠ PyTorch: CPU-only build (cannot use {nvidia_gpu_name})")
            
            # Determine why PyTorch can't use the GPU
            if nvidia_compute_cap:
                major_cc = int(float(nvidia_compute_cap))
                if major_cc >= 7:
                    print(f"  ℹ GPU is modern (CC {nvidia_compute_cap}) but PyTorch is CPU-only build")
                    print(f"  → Install CUDA-enabled PyTorch to use GPU")
                elif major_cc >= 5:
                    print(f"  ℹ GPU is legacy (CC {nvidia_compute_cap}) - requires PyTorch 1.13")
                    print(f"  → Current PyTorch 2.x doesn't support CC < 7.0")
                else:
                    print(f"  ℹ GPU too old (CC {nvidia_compute_cap}) - not supported by modern PyTorch")
        else:
            print(f"  ✓ GPU: Not available (CPU mode)")
    
    # Build hardware info - use physical GPU info if available
    hw_info = {
        'detected_at': datetime.now().isoformat(),
        'platform': platform.system(),
        'cpu_cores': cpu_info['cores'],
        'cpu_threads': cpu_info['threads'],
        'cpu_brand': cpu_info['brand'],
        'memory_gb': mem_info['total_gb'],
        'memory_available_gb': mem_info['available_gb'],
    }
    
    # GPU info - prefer physical detection over PyTorch
    if physical_gpu_detected:
        # Physical NVIDIA GPU detected
        hw_info['gpu_available'] = (gpu_type == 'cuda')  # Only true if PyTorch can use it
        hw_info['gpu_type'] = 'cuda' if gpu_type == 'cuda' else 'cuda-unavailable'
        hw_info['gpu_name'] = nvidia_gpu_name
        hw_info['gpu_memory_gb'] = nvidia_gpu_memory
        hw_info['compute_capability'] = nvidia_compute_cap
        hw_info['cuda_version'] = nvidia_cuda_version
        
        # Determine PyTorch compatibility
        if nvidia_compute_cap:
            major_cc = int(float(nvidia_compute_cap))
            if gpu_type == 'cuda':
                hw_info['pytorch_compatible'] = 'full'
            elif major_cc >= 7:
                hw_info['pytorch_compatible'] = 'cpu-only-build'  # GPU is modern but PyTorch is CPU build
            elif major_cc >= 5:
                hw_info['pytorch_compatible'] = 'legacy'  # Needs PyTorch 1.x
            else:
                hw_info['pytorch_compatible'] = 'incompatible'
        else:
            hw_info['pytorch_compatible'] = pytorch_compatible
            
    elif gpu_type == 'mps':
        # Apple Silicon
        hw_info['gpu_available'] = True
        hw_info['gpu_type'] = 'mps'
        hw_info['gpu_name'] = gpu_name
        hw_info['gpu_memory_gb'] = gpu_memory_gb
        hw_info['compute_capability'] = 'N/A'
        hw_info['pytorch_compatible'] = 'full'
        
    else:
        # No GPU at all
        hw_info['gpu_available'] = False
        hw_info['gpu_type'] = 'cpu'
        hw_info['gpu_name'] = None
        hw_info['gpu_memory_gb'] = None
        hw_info['compute_capability'] = None
        hw_info['pytorch_compatible'] = None
    
    # Calculate optimal settings (enhanced for Bollywood/Hinglish)
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


def update_pipeline_config(hw_info: Dict, config_file: Path = None) -> bool:
    """
    Update config/.env.pipeline with hardware-optimized settings.
    
    Writes detected device, batch size, and MPS environment vars to the
    pipeline configuration file for use by prepare-job and pipeline stages.
    
    Args:
        hw_info: Hardware information dict with recommended_settings
        config_file: Path to pipeline config (default: config/.env.pipeline)
    
    Returns:
        True if successful, False otherwise
    """
    if config_file is None:
        config_file = Path('config/.env.pipeline')
    
    if not config_file.exists():
        print(f"  ⚠ Config file not found: {config_file}")
        return False
    
    try:
        # Read existing config
        with open(config_file, 'r') as f:
            lines = f.readlines()
        
        # Extract settings
        gpu_type = hw_info.get('gpu_type', 'cpu')
        settings = hw_info.get('recommended_settings', {})
        batch_size = settings.get('batch_size', 16)
        whisper_model = settings.get('whisper_model', 'large-v3')
        compute_type = settings.get('compute_type', 'float16')
        
        # Determine if we need to add MPS environment variables
        is_mps = (gpu_type == 'mps')
        
        # Update lines
        updated_lines = []
        updated_device = False
        updated_batch = False
        updated_whisperx_device = False
        updated_model = False
        updated_compute = False
        found_mps_section = False
        
        for line in lines:
            # Update global DEVICE
            if line.startswith('DEVICE='):
                updated_lines.append(f'DEVICE={gpu_type}\n')
                updated_device = True
            # Update BATCH_SIZE
            elif line.startswith('BATCH_SIZE='):
                updated_lines.append(f'BATCH_SIZE={batch_size}\n')
                updated_batch = True
            # Update WHISPERX_DEVICE
            elif line.startswith('WHISPERX_DEVICE='):
                updated_lines.append(f'WHISPERX_DEVICE={gpu_type}\n')
                updated_whisperx_device = True
            # Update WHISPER_MODEL
            elif line.startswith('WHISPER_MODEL='):
                updated_lines.append(f'WHISPER_MODEL={whisper_model}\n')
                updated_model = True
            # Update WHISPER_COMPUTE_TYPE
            elif line.startswith('WHISPER_COMPUTE_TYPE='):
                updated_lines.append(f'WHISPER_COMPUTE_TYPE={compute_type}\n')
                updated_compute = True
            # Update stage-specific devices (optional - make them follow global)
            elif line.startswith('SILERO_DEVICE='):
                updated_lines.append(f'SILERO_DEVICE={gpu_type}\n')
            elif line.startswith('PYANNOTE_DEVICE='):
                updated_lines.append(f'PYANNOTE_DEVICE={gpu_type}\n')
            elif line.startswith('DIARIZATION_DEVICE='):
                updated_lines.append(f'DIARIZATION_DEVICE={gpu_type}\n')
            # Check if MPS section already exists
            elif 'MPS ENVIRONMENT VARIABLES' in line or line.startswith('PYTORCH_MPS_HIGH_WATERMARK_RATIO='):
                found_mps_section = True
                updated_lines.append(line)
            else:
                updated_lines.append(line)
        
        # Add MPS environment variables section if MPS is detected and section doesn't exist
        if is_mps and not found_mps_section:
            updated_lines.append('\n')
            updated_lines.append('# ============================================================\n')
            updated_lines.append('# MPS ENVIRONMENT VARIABLES (Apple Silicon)\n')
            updated_lines.append('# ============================================================\n')
            updated_lines.append('# Auto-configured by hardware detection\n')
            updated_lines.append('PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0\n')
            updated_lines.append('PYTORCH_ENABLE_MPS_FALLBACK=0\n')
            updated_lines.append('MPS_ALLOC_MAX_SIZE_MB=4096\n')
            updated_lines.append('\n')
        
        # Write updated config
        with open(config_file, 'w') as f:
            f.writelines(updated_lines)
        
        print(f"  ✓ Updated pipeline config: {config_file}")
        if updated_device:
            print(f"    • DEVICE={gpu_type}")
        if updated_batch:
            print(f"    • BATCH_SIZE={batch_size}")
        if updated_whisperx_device:
            print(f"    • WHISPERX_DEVICE={gpu_type}")
        if updated_model:
            print(f"    • WHISPER_MODEL={whisper_model}")
        if updated_compute:
            print(f"    • WHISPER_COMPUTE_TYPE={compute_type}")
        if is_mps and not found_mps_section:
            print(f"    • MPS environment variables added")
        
        return True
        
    except Exception as e:
        print(f"  ⚠ Failed to update config: {e}")
        return False


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
    
    # Update pipeline config with optimized settings
    update_pipeline_config(hw_info)
    
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
