"""
device_selector.py - Device selection with graceful fallback

Handles device selection for WhisperX, diarization, transformers, and spaCy
with automatic fallback to CPU if requested device unavailable.

Cross-platform support:
- Windows: CUDA, CPU
- Linux: CUDA, CPU
- macOS: MPS, CPU

DEVELOPER STANDARDS COMPLIANCE:
- Lazy import of torch (environment-specific dependency)
- Graceful fallback if torch unavailable
- Multi-environment architecture support
"""

# Standard library
from typing import Tuple, Literal, Optional

# Third-party
import platform

# Local
from shared.logger import get_logger
logger = get_logger(__name__)

DeviceType = Literal["cpu", "cuda", "mps"]

# Lazy-loaded torch module
_torch = None
_torch_available = None


def _get_torch():
    """
    Lazy-load torch module with graceful fallback.
    
    Returns:
        (torch_module, is_available)
    
    Developer Standards: Section 7.2 - Graceful Degradation
    """
    global _torch, _torch_available
    
    if _torch_available is None:
        try:
            import torch as _torch_module
            _torch = _torch_module
            _torch_available = True
        except ImportError:
            _torch = None
            _torch_available = False
    
    return _torch, _torch_available


def check_device_available(device: str) -> bool:
    """
    Check if a device is available (cross-platform).

    Args:
        device: Device name (cpu, cuda, mps)

    Returns:
        True if device is available
        
    Note:
        - Windows: CUDA or CPU only
        - Linux: CUDA or CPU
        - macOS: MPS or CPU
        - Returns False for CUDA/MPS if torch unavailable
    """
    device = device.lower()

    if device == "cpu":
        return True
    elif device == "cuda":
        # CUDA available on Windows and Linux with NVIDIA GPU
        torch, torch_available = _get_torch()
        if not torch_available:
            return False
        return torch.cuda.is_available()
    elif device == "mps":
        # MPS only available on Apple Silicon (macOS)
        if platform.system() != 'Darwin':
            return False
        torch, torch_available = _get_torch()
        if not torch_available:
            # Fallback: assume MPS available on macOS (let MLX handle it)
            return True
        return hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
    else:
        return False


def select_device(requested: str, fallback: str = "cpu") -> Tuple[str, bool]:
    """
    Select device with fallback and auto-detection

    Args:
        requested: Requested device (cpu, cuda, mps, auto)
        fallback: Fallback device (default: cpu)

    Returns:
        Tuple of (actual_device, did_fallback)

    Examples:
        >>> select_device("auto")
        ("mps", False)  # on Apple Silicon

        >>> select_device("mps", "cpu")
        ("mps", False)  # if MPS available

        >>> select_device("mps", "cpu")
        ("cpu", True)   # if MPS not available
    """
    requested = requested.lower()

    # Auto-detect best available device
    if requested == "auto":
        if check_device_available("mps"):
            return "mps", False
        elif check_device_available("cuda"):
            return "cuda", False
        else:
            return "cpu", False
    
    # Use requested device if available
    if check_device_available(requested):
        return requested, False

    # Fall back
    if check_device_available(fallback):
        return fallback, True

    # Ultimate fallback to CPU
    return "cpu", True


def get_compute_type_for_device(device: str, prefer_int8: bool = True) -> str:
    """
    Get appropriate compute type for device

    Args:
        device: Device name (cpu, cuda, mps)
        prefer_int8: Prefer int8 quantization on CPU for stability (default: True)

    Returns:
        Compute type string for WhisperX (e.g., "int8", "float16", "float32")
    """
    device = device.lower()

    if device == "cpu":
        return "int8" if prefer_int8 else "float32"
    elif device == "cuda":
        # CUDA supports float16 for faster inference
        return "float16"
    elif device == "mps":
        # MPS can be flaky; use float32 for stability
        return "float32"
    else:
        return "float32"


def select_whisperx_device(requested: str) -> Tuple[str, str, bool]:
    """
    Select device for WhisperX with compute type

    Args:
        requested: Requested device

    Returns:
        Tuple of (device, compute_type, did_fallback)
    """
    device, did_fallback = select_device(requested, fallback="cpu")
    compute_type = get_compute_type_for_device(device, prefer_int8=True)

    return device, compute_type, did_fallback


def select_diarization_device(requested: str) -> Tuple[str, bool]:
    """
    Select device for diarization (pyannote)

    Args:
        requested: Requested device

    Returns:
        Tuple of (device, did_fallback)
    """
    # Diarization prefers CUDA, falls back to CPU
    if requested.lower() == "cuda":
        device, did_fallback = select_device("cuda", fallback="cpu")
    else:
        device, did_fallback = select_device("cpu", fallback="cpu")

    return device, did_fallback


def select_transformers_device(requested: str) -> Tuple[str, bool]:
    """
    Select device for transformers (second-pass translation)

    Args:
        requested: Requested device

    Returns:
        Tuple of (device, did_fallback)
    """
    device, did_fallback = select_device(requested, fallback="cpu")
    return device, did_fallback


def select_spacy_device(requested: str) -> Tuple[str, bool]:
    """
    Select device for spaCy NER

    Args:
        requested: Requested device

    Returns:
        Tuple of (device_id, did_fallback)

    Note:
        Returns device_id as integer for spaCy (-1 for CPU, 0+ for CUDA)
    """
    requested = requested.lower()

    if requested == "cuda" and check_device_available("cuda"):
        return 0, False  # spaCy uses integer device IDs
    else:
        return -1, requested != "cpu"  # -1 means CPU in spaCy


def get_platform_optimal_device() -> str:
    """
    Get the optimal device for current platform.
    
    Returns:
        Optimal device name: 'cuda', 'mps', or 'cpu'
        
    Platform-specific recommendations:
        - Windows: CUDA (NVIDIA GPU) or CPU
        - Linux: CUDA (NVIDIA GPU) or CPU
        - macOS: MPS (Apple Silicon) or CPU
    """
    system = platform.system()
    
    if system == 'Windows' or system == 'Linux':
        # Windows and Linux: prefer CUDA
        if check_device_available('cuda'):
            return 'cuda'
    elif system == 'Darwin':
        # macOS: prefer MPS on Apple Silicon
        if check_device_available('mps'):
            return 'mps'
        # Fallback to CUDA if available (Intel Mac with eGPU)
        if check_device_available('cuda'):
            return 'cuda'
    
    # Ultimate fallback
    return 'cpu'


def get_cuda_info() -> Optional[dict]:
    """
    Get CUDA device information (Windows/Linux only).
    
    Returns:
        Dictionary with CUDA info or None if CUDA not available
    """
    if not torch.cuda.is_available():
        return None
    
    return {
        'available': True,
        'device_count': torch.cuda.device_count(),
        'current_device': torch.cuda.current_device(),
        'device_name': torch.cuda.get_device_name(0),
        'cuda_version': torch.version.cuda,
        'cudnn_version': torch.backends.cudnn.version() if torch.backends.cudnn.is_available() else None,
    }


def get_device_memory_info(device: str) -> Optional[dict]:
    """
    Get memory information for device.
    
    Args:
        device: Device name (cuda, mps, cpu)
        
    Returns:
        Dictionary with memory info or None
    """
    if device == 'cuda' and torch.cuda.is_available():
        props = torch.cuda.get_device_properties(0)
        return {
            'total_memory': props.total_memory,
            'total_memory_gb': props.total_memory / (1024**3),
            'compute_capability': f"{props.major}.{props.minor}",
        }
    elif device == 'mps' and platform.system() == 'Darwin':
        # MPS uses unified memory, harder to query
        return {
            'type': 'unified_memory',
            'note': 'MPS uses shared system memory'
        }
    
    return None


def validate_device_and_compute_type(device: str, compute_type: Optional[str] = None, logger=None) -> Tuple[str, Optional[str]]:
    """
    Validate device and compute_type compatibility for ML stages.
    
    This function ensures that:
    1. MPS devices fall back to CPU (MPS not supported by CTranslate2)
    2. CPU uses int8 compute type when compute_type is provided
    3. float16 on CPU is converted to int8
    
    Args:
        device: Requested device (cpu, cuda, mps)
        compute_type: Requested compute type (int8, float16, float32, or None for PyTorch models)
        logger: Optional logger for warnings
    
    Returns:
        Tuple of (validated_device, validated_compute_type)
    
    Examples:
        >>> validate_device_and_compute_type("mps", "float32")
        ("cpu", "int8")
        
        >>> validate_device_and_compute_type("cpu", "float16")
        ("cpu", "int8")
        
        >>> validate_device_and_compute_type("cuda", "float16")
        ("cuda", "float16")
        
        >>> validate_device_and_compute_type("cpu", None)  # PyTorch model
        ("cpu", None)
    """
    device_to_use = device.lower()
    compute_type_to_use = compute_type.lower() if compute_type else None
    
    # MPS not supported by CTranslate2, fallback to CPU
    if device_to_use == "mps":
        if logger:
            logger.warning("  MPS device not supported by CTranslate2 (faster-whisper backend)")
            logger.warning("  Falling back to CPU")
        device_to_use = "cpu"
        # If compute_type was specified, force int8 for CPU
        if compute_type_to_use:
            compute_type_to_use = "int8"
    
    # CPU only efficiently supports int8 for CTranslate2
    # float16 on CPU causes: "ValueError: Requested float16 compute type, but the target device 
    # or backend do not support efficient float16 computation"
    if device_to_use == "cpu" and compute_type_to_use:
        if compute_type_to_use not in ["int8", "int8_float32", "int8_float16"]:
            if logger:
                logger.info(f"  CPU mode: adjusting {compute_type_to_use} → int8 for optimal performance")
            compute_type_to_use = "int8"
    
    return device_to_use, compute_type_to_use
