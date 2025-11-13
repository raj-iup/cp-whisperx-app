#!/usr/bin/env python3
"""
MPS/Metal Utilities for Memory Management and Monitoring

Shared utilities for all ML stages to optimize MPS performance and prevent
segfaults, memory fragmentation, and hangs.

Usage:
    from mps_utils import cleanup_mps_memory, log_mps_memory, retry_with_degradation
"""
import gc
import logging
import time
import threading
from functools import wraps
from typing import Optional, Callable, Any

# ============================================================================
# Memory Management
# ============================================================================

def cleanup_mps_memory(logger: Optional[logging.Logger] = None):
    """
    Clean up MPS memory to prevent fragmentation.
    
    Call this after processing chunks or completing stages to release
    MPS memory and prevent accumulation issues.
    
    Args:
        logger: Optional logger for debug messages
    """
    try:
        import torch
        if hasattr(torch, 'mps') and torch.backends.mps.is_available():
            # Force garbage collection first
            gc.collect()
            
            # Clear MPS cache
            torch.mps.empty_cache()
            
            if logger:
                logger.debug("  🧹 MPS memory cleared")
    except Exception as e:
        if logger:
            logger.warning(f"  ⚠️  MPS cleanup failed: {e}")


def get_mps_memory_allocated() -> float:
    """
    Get current MPS memory allocated in GB.
    
    Note: MPS doesn't expose memory stats like CUDA, so we estimate
    based on process memory usage.
    
    Returns:
        Memory allocated in GB
    """
    try:
        import torch
        if hasattr(torch, 'mps') and torch.backends.mps.is_available():
            # MPS doesn't have .memory_allocated() like CUDA
            # Use process memory as proxy
            try:
                import psutil
                process = psutil.Process()
                return process.memory_info().rss / (1024**3)  # GB
            except ImportError:
                # If psutil not available, return 0
                return 0.0
    except:
        pass
    return 0.0


def log_mps_memory(logger: logging.Logger, prefix: str = ""):
    """
    Log current MPS memory usage.
    
    Args:
        logger: Logger instance
        prefix: Prefix for log message
    """
    mem_gb = get_mps_memory_allocated()
    if mem_gb > 0:
        logger.info(f"{prefix}Memory: {mem_gb:.2f} GB")


# ============================================================================
# Retry Logic with Degradation
# ============================================================================

def retry_with_degradation(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0
):
    """
    Decorator for retrying functions with exponential backoff and parameter degradation.
    
    On failure, automatically:
    1. First retry: Reduce batch_size by 50%
    2. Second retry: Reduce chunk_duration by 50%
    3. Third retry: Final attempt with degraded params
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds before first retry
        backoff_factor: Multiplier for delay on each retry
        
    Usage:
        @retry_with_degradation(max_retries=3)
        def process_chunk(self, chunk, batch_size=16):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Extract degradable parameters
            batch_size = kwargs.get('batch_size', 16)
            original_batch_size = batch_size
            
            # Try to get chunk_duration from self
            original_chunk_duration = getattr(self, 'chunk_duration', None)
            
            for attempt in range(max_retries):
                try:
                    return func(self, *args, **kwargs)
                    
                except Exception as e:
                    logger = getattr(self, 'logger', None)
                    
                    if logger:
                        logger.warning(f"  ⚠️  Attempt {attempt + 1}/{max_retries} failed: {e}")
                    
                    if attempt < max_retries - 1:
                        # Apply degradation strategy
                        if attempt == 0:
                            # First retry: reduce batch size
                            new_batch_size = max(batch_size // 2, 4)
                            kwargs['batch_size'] = new_batch_size
                            if logger:
                                logger.warning(
                                    f"  🔄 Retry {attempt + 1}: Reducing batch_size "
                                    f"{batch_size} → {new_batch_size}"
                                )
                            batch_size = new_batch_size
                            
                        elif attempt == 1:
                            # Second retry: reduce chunk size if available
                            if hasattr(self, 'chunk_duration') and original_chunk_duration:
                                new_chunk_duration = max(original_chunk_duration // 2, 60)
                                self.chunk_duration = new_chunk_duration
                                if logger:
                                    logger.warning(
                                        f"  🔄 Retry {attempt + 1}: Reducing chunk_duration "
                                        f"{original_chunk_duration}s → {new_chunk_duration}s"
                                    )
                        
                        # Exponential backoff
                        delay = initial_delay * (backoff_factor ** attempt)
                        if logger:
                            logger.info(f"  ⏳ Waiting {delay:.1f}s before retry...")
                        time.sleep(delay)
                        
                        # Clean up memory before retry
                        cleanup_mps_memory(logger)
                    else:
                        # Final retry failed
                        if logger:
                            logger.error(f"  ❌ All {max_retries} retries exhausted")
                        raise
            
        return wrapper
    return decorator


# ============================================================================
# Process Watchdog
# ============================================================================

class ProcessWatchdog:
    """
    Monitor process for hangs and lack of activity.
    
    Usage:
        watchdog = ProcessWatchdog(timeout=600, logger=logger)
        watchdog.start()
        
        # During processing, call periodically:
        watchdog.heartbeat()
        
        # When done:
        watchdog.stop()
    """
    
    def __init__(self, timeout: int, logger: logging.Logger):
        """
        Args:
            timeout: Timeout in seconds without activity
            logger: Logger instance
        """
        self.timeout = timeout
        self.logger = logger
        self.last_activity = time.time()
        self.monitoring = False
        self.thread = None
        self.hung = False
    
    def heartbeat(self):
        """Signal that process is still active. Call this periodically."""
        self.last_activity = time.time()
    
    def _monitor(self):
        """Internal monitoring loop (runs in thread)."""
        while self.monitoring:
            elapsed = time.time() - self.last_activity
            
            if elapsed > self.timeout:
                self.logger.error(
                    f"🚨 WATCHDOG ALERT: No activity for {elapsed:.1f}s "
                    f"(timeout: {self.timeout}s) - Possible hang!"
                )
                self.hung = True
                # Could terminate process here if needed
                break
            
            # Check every 10 seconds
            time.sleep(10)
    
    def start(self):
        """Start monitoring."""
        self.monitoring = True
        self.last_activity = time.time()
        self.hung = False
        self.thread = threading.Thread(target=self._monitor, daemon=True)
        self.thread.start()
        self.logger.debug("  👁️  Watchdog monitoring started")
    
    def stop(self):
        """Stop monitoring."""
        self.monitoring = False
        if self.thread:
            self.thread.join(timeout=1)
        
        if not self.hung:
            self.logger.debug("  ✓ Watchdog monitoring stopped (no issues)")
    
    def is_hung(self) -> bool:
        """Check if watchdog detected a hang."""
        return self.hung


# ============================================================================
# MPS-Specific Helpers
# ============================================================================

def optimize_batch_size_for_mps(
    batch_size: int,
    device: str,
    model_size: str = "medium"
) -> int:
    """
    Optimize batch size for MPS device.
    
    MPS has different memory characteristics than CUDA, typically requiring
    smaller batch sizes to prevent fragmentation.
    
    Args:
        batch_size: Requested batch size
        device: Device type ('mps', 'cuda', 'cpu')
        model_size: Model size hint ('small', 'medium', 'large')
        
    Returns:
        Optimized batch size
    """
    if device != 'mps':
        return batch_size
    
    # MPS-specific optimization
    size_limits = {
        'small': 16,
        'medium': 8,
        'large': 4,
        'xlarge': 2
    }
    
    max_batch = size_limits.get(model_size, 8)
    optimized = min(batch_size, max_batch)
    
    return optimized


def setup_mps_environment():
    """
    Set up MPS environment variables for optimal performance.
    
    Call this early in the script, before importing PyTorch.
    """
    import os
    
    # Prevent memory fragmentation
    os.environ['PYTORCH_MPS_HIGH_WATERMARK_RATIO'] = '0.0'
    
    # Disable MPS fallback (fail fast instead of silent CPU fallback)
    os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '0'
    
    # Set memory allocator max size (4GB)
    os.environ['MPS_ALLOC_MAX_SIZE_MB'] = '4096'


# ============================================================================
# Convenience Functions
# ============================================================================

def mps_safe_operation(
    operation: Callable,
    logger: logging.Logger,
    cleanup: bool = True,
    *args,
    **kwargs
) -> Any:
    """
    Execute an operation with MPS safety measures.
    
    Args:
        operation: Function to execute
        logger: Logger instance
        cleanup: Whether to cleanup memory after operation
        *args, **kwargs: Arguments to pass to operation
        
    Returns:
        Result of operation
    """
    try:
        # Log memory before
        log_mps_memory(logger, "  Before operation - ")
        
        # Execute operation
        result = operation(*args, **kwargs)
        
        return result
        
    finally:
        # Always cleanup if requested
        if cleanup:
            cleanup_mps_memory(logger)
            log_mps_memory(logger, "  After operation - ")
