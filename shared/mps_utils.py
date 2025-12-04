#!/usr/bin/env python3
"""
MPS Utilities - Apple Silicon Optimization

Provides memory management and batch size optimization for Apple Silicon (MPS):
- Prevents OOM errors on M1/M2/M3/M4 devices
- Automatic batch size optimization
- Memory cleanup between processing stages
- Performance monitoring

Part of Phase 5: Advanced Features (ML Optimization)
See: docs/ARCHITECTURE_IMPLEMENTATION_ROADMAP.md § Phase 5

Module: shared/mps_utils.py
Status: ✅ Implemented for Apple Silicon optimization
"""

# Standard library
from typing import Optional, Any, Dict

# Local
from shared.logger import get_logger

logger = get_logger(__name__)


def is_mps_available() -> bool:
    """
    Check if MPS is available on this system.
    
    Returns:
        True if MPS is available, False otherwise
    """
    try:
        import torch
        return torch.backends.mps.is_available()
    except Exception:
        return False


def cleanup_mps_memory(logger_instance: Optional[Any] = None) -> None:
    """
    Clean up MPS memory cache.
    
    Should be called:
    - After processing each chunk
    - Between pipeline stages
    - When switching models
    
    Args:
        logger_instance: Optional logger for debugging
        
    Example:
        >>> cleanup_mps_memory(logger)
        >>> # Memory freed for next operation
    """
    if logger_instance is None:
        logger_instance = logger
    
    try:
        import torch
        if torch.backends.mps.is_available():
            # Clear MPS cache
            if hasattr(torch.mps, 'empty_cache'):
                torch.mps.empty_cache()
                logger_instance.debug("MPS cache cleared")
            
            # Synchronize to ensure cleanup completes
            if hasattr(torch.mps, 'synchronize'):
                torch.mps.synchronize()
                
    except Exception as e:
        logger_instance.debug(f"MPS cleanup skipped: {e}")


def log_mps_memory(
    logger_instance: Optional[Any] = None,
    prefix: str = ""
) -> None:
    """
    Log MPS memory usage information.
    
    Args:
        logger_instance: Optional logger for output
        prefix: Prefix string for log message
        
    Note:
        MPS doesn't provide detailed memory stats like CUDA,
        so this logs basic device information.
    """
    if logger_instance is None:
        logger_instance = logger
    
    try:
        import torch
        if torch.backends.mps.is_available():
            # MPS is active
            logger_instance.debug(f"{prefix}Running on MPS device (Apple Silicon)")
            
            # Try to get current memory if available
            if hasattr(torch.mps, 'current_allocated_memory'):
                allocated = torch.mps.current_allocated_memory() / (1024**3)  # GB
                logger_instance.debug(f"{prefix}MPS allocated: {allocated:.2f} GB")
        else:
            logger_instance.debug(f"{prefix}MPS not available")
            
    except Exception as e:
        logger_instance.debug(f"{prefix}MPS memory logging failed: {e}")


def optimize_batch_size_for_mps(
    batch_size: int,
    device: str,
    model_size: str = "large"
) -> int:
    """
    Optimize batch size for MPS device to prevent OOM.
    
    Apple Silicon has unified memory but limited compared to dedicated GPUs.
    This function caps batch size based on model size to prevent crashes.
    
    Args:
        batch_size: Requested batch size
        device: Device string (e.g., "mps", "cuda", "cpu")
        model_size: Model size (e.g., "large-v3", "medium", "small")
        
    Returns:
        Optimized batch size (capped if MPS)
        
    Optimization Rules:
        - Large models (large-v2, large-v3): max batch_size = 2
        - Medium models: max batch_size = 4
        - Small/Base models: max batch_size = 8
        - Non-MPS devices: return original batch_size
        
    Example:
        >>> batch_size = optimize_batch_size_for_mps(16, "mps", "large-v3")
        >>> logger.info(f"Optimized batch size: {batch_size}")
        # Output: 2  # Capped for MPS
    """
    # If not MPS, return original batch size
    if device.lower() != "mps":
        return batch_size
    
    # Determine cap based on model size
    model_size_lower = model_size.lower()
    
    if "large" in model_size_lower:
        # Large models: 1-2 GB VRAM per sample
        cap = 2
    elif "medium" in model_size_lower:
        # Medium models: 500-700 MB VRAM per sample
        cap = 4
    elif "small" in model_size_lower:
        # Small models: 200-400 MB VRAM per sample
        cap = 8
    elif "base" in model_size_lower or "tiny" in model_size_lower:
        # Base/Tiny models: <200 MB VRAM per sample
        cap = 16
    else:
        # Unknown model: conservative default
        cap = 4
    
    if batch_size > cap:
        logger.debug(
            f"MPS optimization: Capping batch_size {batch_size} → {cap} "
            f"(model: {model_size})"
        )
        return cap
    
    return batch_size


def get_mps_memory_info() -> Dict[str, Any]:
    """
    Get MPS memory information.
    
    Returns:
        Dictionary with memory info:
        - available: bool - MPS available
        - device: str - Device name
        - allocated_gb: float - Allocated memory (if available)
        - note: str - Additional information
        
    Example:
        >>> info = get_mps_memory_info()
        >>> logger.info(f"MPS: {info['available']}, Allocated: {info.get('allocated_gb', 'N/A')} GB")
    """
    result = {
        "available": False,
        "device": "unknown"
    }
    
    try:
        import torch
        
        if torch.backends.mps.is_available():
            result["available"] = True
            result["device"] = "mps"
            result["note"] = "Apple Silicon (MPS) detected"
            
            # Try to get allocated memory
            if hasattr(torch.mps, 'current_allocated_memory'):
                allocated = torch.mps.current_allocated_memory()
                result["allocated_gb"] = allocated / (1024**3)
                result["allocated_bytes"] = allocated
            else:
                result["note"] = "MPS available, detailed stats not supported"
        else:
            result["note"] = "MPS not available on this device"
            
    except ImportError:
        result["note"] = "PyTorch not installed"
    except Exception as e:
        result["note"] = f"Error checking MPS: {e}"
    
    return result


def suggest_model_size_for_memory(
    available_memory_gb: float,
    target: str = "accuracy"
) -> str:
    """
    Suggest Whisper model size based on available memory.
    
    Args:
        available_memory_gb: Available memory in GB
        target: Optimization target ("accuracy", "speed", "balanced")
        
    Returns:
        Recommended model name (e.g., "large-v3", "medium", "base")
        
    Memory Requirements (approximate):
        - large-v3: 10-12 GB VRAM
        - large-v2: 10-12 GB VRAM
        - medium: 5-6 GB VRAM
        - small: 2-3 GB VRAM
        - base: 1-2 GB VRAM
        - tiny: <1 GB VRAM
    """
    if target == "accuracy":
        # Prioritize accuracy
        if available_memory_gb >= 12:
            return "large-v3"
        elif available_memory_gb >= 10:
            return "large-v2"
        elif available_memory_gb >= 5:
            return "medium"
        elif available_memory_gb >= 2:
            return "small"
        else:
            return "base"
    
    elif target == "speed":
        # Prioritize speed
        if available_memory_gb >= 5:
            return "medium"
        elif available_memory_gb >= 2:
            return "small"
        else:
            return "base"
    
    else:  # balanced
        # Balance accuracy and speed
        if available_memory_gb >= 10:
            return "large-v3"
        elif available_memory_gb >= 5:
            return "medium"
        elif available_memory_gb >= 2:
            return "small"
        else:
            return "base"


def estimate_processing_time(
    duration_seconds: float,
    model_size: str,
    device: str
) -> float:
    """
    Estimate processing time for audio.
    
    Args:
        duration_seconds: Audio duration in seconds
        model_size: Whisper model size
        device: Device type ("mps", "cuda", "cpu")
        
    Returns:
        Estimated processing time in seconds
        
    Note:
        These are rough estimates. Actual time varies by:
        - Audio quality
        - Batch size
        - System load
        - Model optimizations
    """
    # Processing speed factors (seconds audio per second real-time)
    speed_factors = {
        "mps": {
            "large-v3": 0.15,    # 100s audio in ~15s
            "large-v2": 0.15,
            "medium": 0.08,       # 100s audio in ~8s
            "small": 0.05,
            "base": 0.03
        },
        "cuda": {
            "large-v3": 0.10,    # Faster on dedicated GPU
            "large-v2": 0.10,
            "medium": 0.05,
            "small": 0.03,
            "base": 0.02
        },
        "cpu": {
            "large-v3": 1.5,     # Slower on CPU
            "large-v2": 1.5,
            "medium": 0.8,
            "small": 0.4,
            "base": 0.2
        }
    }
    
    device_lower = device.lower()
    model_lower = model_size.lower()
    
    # Get speed factor
    device_factors = speed_factors.get(device_lower, speed_factors["cpu"])
    
    # Match model size
    for key in device_factors:
        if key in model_lower:
            factor = device_factors[key]
            break
    else:
        # Default to medium if unknown
        factor = device_factors.get("medium", 0.1)
    
    return duration_seconds * factor
