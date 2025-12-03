"""

logger = get_logger(__name__)

whisper_backends.py - Unified backend abstraction for Whisper models

Supports multiple backends:
- ctranslate2: WhisperX with CTranslate2 (CPU/CUDA only)
- mlx: Apple MLX framework (MPS/Metal acceleration)
- openai: Official OpenAI Whisper (fallback)

Auto-selects best backend based on device availability.
"""

# Standard library
import os
import json
import warnings
import sys
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple

# Third-party
from abc import ABC, abstractmethod

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Use lightweight audio loader
from shared.audio_utils import load_audio

warnings.filterwarnings('ignore', message='Model was trained with pyannote')
warnings.filterwarnings('ignore', message='Model was trained with torch')


class WhisperBackend(ABC):
    """Abstract base class for Whisper backends"""
    
    @abstractmethod
    def load_model(self) -> bool:
        """Load the model. Returns True if successful."""
        pass
    
    @abstractmethod
    def transcribe(
        self,
        audio_file: str,
        language: Optional[str] = None,
        task: str = "transcribe",
        batch_size: int = 16,
        initial_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Transcribe audio file with optional bias prompting. Returns WhisperX-compatible result dict."""
        pass
    
    @abstractmethod
    def load_align_model(self, language: str) -> bool:
        """Load alignment model for word-level timestamps. Returns True if successful."""
        pass
    
    @abstractmethod
    def align_segments(
        self,
        segments: List[Dict],
        audio_file: str,
        language: str
    ) -> Dict[str, Any]:
        """Align segments for word-level timestamps."""
        pass
    
    @abstractmethod
    def supports_device(self, device: str) -> bool:
        """Check if backend supports the given device."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Backend name."""
        pass
    
    def cleanup(self) -> None:
        """Clean up resources (optional, can be overridden)."""
        pass


class WhisperXBackend(WhisperBackend):
    """WhisperX backend using CTranslate2 (CPU/CUDA only)"""
    
    def __init__(
        self,
        model_name: str,
        device: str,
        compute_type: str,
        logger: logging.Logger,
        condition_on_previous_text: bool = False,  # False prevents hallucination loops
        logprob_threshold: float = -1.0,
        no_speech_threshold: float = 0.6,
        compression_ratio_threshold: float = 2.4
    ):
        self.model_name = model_name
        self.device = device
        self.compute_type = compute_type
        self.logger = logger
        self.model = None
        self.align_model = None
        self.align_metadata = None
        # Anti-hallucination parameters
        self.condition_on_previous_text = condition_on_previous_text
        self.logprob_threshold = logprob_threshold
        self.no_speech_threshold = no_speech_threshold
        self.compression_ratio_threshold = compression_ratio_threshold
        
    @property
    def name(self) -> str:
        """Name."""
        return "whisperx-ctranslate2"
    
    def supports_device(self, device: str) -> bool:
        """CTranslate2 only supports CPU and CUDA"""
        return device.lower() in ["cpu", "cuda"]
    
    def load_model(self) -> bool:
        """Load WhisperX model with CTranslate2 backend"""
        import whisperx
        from device_selector import validate_device_and_compute_type
        
        self.logger.info(f"Loading WhisperX model: {self.model_name}")
        self.logger.info(f"  Backend: CTranslate2")
        self.logger.info(f"  Device: {self.device}")
        self.logger.info(f"  Compute type: {self.compute_type}")
        
        cache_dir = os.environ.get('TORCH_HOME', str(Path.home() / '.cache' / 'torch'))
        
        # Validate device and compute type compatibility
        device_to_use, compute_type_to_use = validate_device_and_compute_type(
            self.device, self.compute_type, self.logger
        )
        
        # Try with download_root first, fall back without it if not supported
        for use_download_root in [True, False]:
            try:
                kwargs = {
                    'device': device_to_use,
                    'compute_type': compute_type_to_use
                }
                
                if use_download_root:
                    kwargs['download_root'] = cache_dir
                
                self.model = whisperx.load_model(
                    self.model_name,
                    **kwargs
                )
                self.device = device_to_use
                self.compute_type = compute_type_to_use
                self.logger.info(f"  Model loaded successfully")
                return True
                
            except TypeError as e:
                if use_download_root and "download_root" in str(e):
                    # download_root not supported, try without it
                    self.logger.debug(f"  download_root not supported, retrying without it")
                    continue
                else:
                    raise
            except Exception as e:
                if device_to_use != "cpu":
                    self.logger.warning(f"  Failed on {device_to_use}: {e}")
                    self.logger.warning("  Retrying with CPU...")
                    self.device = "cpu"
                    self.compute_type = "int8"
                    
                    # Try CPU with and without download_root
                    for use_dr in [True, False]:
                        try:
                            kwargs = {'device': 'cpu', 'compute_type': 'int8'}
                            if use_dr:
                                kwargs['download_root'] = cache_dir
                            
                            self.model = whisperx.load_model(self.model_name, **kwargs)
                            self.logger.info("  Model loaded successfully on CPU")
                            return True
                        except TypeError as te:
                            if use_dr and "download_root" in str(te):
                                continue
                            else:
                                raise
                    
                    return True
                else:
                    self.logger.error(f"  Failed to load model: {e}", exc_info=True)
                    return False
        
        self.logger.error("  Failed to load model after all attempts", exc_info=True)
        return False
    
    def transcribe(
        self,
        audio_file: str,
        language: Optional[str] = None,
        task: str = "transcribe",
        batch_size: int = 16,
        initial_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribe using WhisperX with optional bias prompting
        
        ARCHITECTURE:
        - CPU/CUDA: Bias parameters applied during ASR (optimal path)
        - bias_injection stage provides additional correction pass
        
        Bias parameters help improve recognition of proper nouns,
        character names, and domain-specific terminology.
        
        Args:
            audio_file: Path to audio file
            language: Source language code
            task: 'transcribe' or 'translate'
            batch_size: Batch size for inference
            initial_prompt: Text prompt to guide transcription
            
        Returns:
            WhisperX-compatible result dict
        """
        import whisperx
        
        if not self.model:
            raise RuntimeError("Model not loaded")
        
        audio = load_audio(audio_file)
        
        # Build transcribe parameters
        transcribe_params = {
            'audio': audio,
            'language': language,
            'task': task,
            'batch_size': batch_size
        }
        
        # Add bias parameters if provided (works on CPU/CUDA)
        if initial_prompt:
            transcribe_params['initial_prompt'] = initial_prompt
            self.logger.debug(f"  Using initial_prompt: {initial_prompt[:100]}...")
        
        try:
            result = self.model.transcribe(**transcribe_params)
        except TypeError as e:
            # If parameters not supported, fallback to basic transcription
            if 'initial_prompt' in str(e):
                self.logger.warning("  initial_prompt not supported by this WhisperX version")
                self.logger.warning("  Falling back to transcription without bias")
                result = self.model.transcribe(
                    audio=audio,
                    language=language,
                    task=task,
                    batch_size=batch_size
                )
            else:
                raise
        
        return result
    
    def load_align_model(self, language: str) -> bool:
        """Load WhisperX alignment model"""
        import whisperx
        
        try:
            self.align_model, self.align_metadata = whisperx.load_align_model(
                language_code=language,
                device=self.device
            )
            self.logger.info(f"  Alignment model loaded for {language}")
            return True
        except Exception as e:
            self.logger.warning(f"  Failed to load alignment model: {e}")
            return False
    
    def align_segments(
        self,
        segments: List[Dict],
        audio_file: str,
        language: str
    ) -> Dict[str, Any]:
        """Align segments using WhisperX"""
        import whisperx
        
        if not self.align_model:
            self.logger.warning("Alignment model not loaded")
            return {"segments": segments}
        
        audio = load_audio(audio_file)
        
        result = whisperx.align(
            segments,
            self.align_model,
            self.align_metadata,
            audio,
            self.device,
            return_char_alignments=False
        )
        
        return result
    
    def cleanup(self) -> None:
        """Clean up WhisperX resources"""
        import gc
        if self.model is not None:
            del self.model
            self.model = None
        if self.align_model is not None:
            del self.align_model
            self.align_model = None
        gc.collect()
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except:
            pass


class MLXWhisperBackend(WhisperBackend):
    """MLX-Whisper backend using Apple MLX framework (MPS/Metal)"""
    
    def __init__(
        self,
        model_name: str,
        device: str,
        compute_type: str,
        logger: logging.Logger,
        condition_on_previous_text: bool = False,  # False prevents hallucination loops
        logprob_threshold: float = -1.0,
        no_speech_threshold: float = 0.6,
        compression_ratio_threshold: float = 2.4
    ):
        """
        Initialize MLX Whisper backend.
        
        Args:
            model_name: Name of the Whisper model to use
            device: Device to run on (mps)
            compute_type: Compute precision type
            logger: Logger instance for logging
            condition_on_previous_text: Whether to condition on previous text
            logprob_threshold: Log probability threshold
            no_speech_threshold: No speech detection threshold
            compression_ratio_threshold: Compression ratio threshold
        """
        self.model_name = model_name
        self.device = device
        self.compute_type = compute_type
        self.logger = logger
        self.model = None
        self.model_loaded = False
        # Anti-hallucination parameters
        self.condition_on_previous_text = condition_on_previous_text
        self.logprob_threshold = logprob_threshold
        self.no_speech_threshold = no_speech_threshold
        self.compression_ratio_threshold = compression_ratio_threshold
        
    @property
    def name(self) -> str:
        """Name."""
        return "mlx-whisper"
    
    def supports_device(self, device: str) -> bool:
        """MLX only works on Apple Silicon (MPS)"""
        return device.lower() == "mps"
    
    def load_model(self) -> Any:
        """
        Load MLX-Whisper model with graceful fallback support
        
        Returns:
            True if model loaded successfully
            "fallback_to_whisperx" if MLX unavailable and fallback needed
            False for other errors
        """
        try:
            import mlx_whisper
            self.mlx = mlx_whisper
        except ImportError:
            self.logger.warning("MLX-Whisper not installed in current environment")
            self.logger.warning("Install with: pip install mlx-whisper")
            self.logger.info("Signaling fallback to WhisperX backend...")
            return "fallback_to_whisperx"
        
        self.logger.info(f"Loading MLX-Whisper model: {self.model_name}")
        self.logger.info(f"  Backend: Apple MLX (Metal)")
        self.logger.info(f"  Device: MPS (Apple Silicon GPU)")
        self.logger.info(f"  → Using Metal Performance Shaders for GPU acceleration")
        self.logger.info(f"  Anti-hallucination settings:")
        self.logger.info(f"    condition_on_previous_text: {self.condition_on_previous_text}")
        self.logger.info(f"    logprob_threshold: {self.logprob_threshold}")
        self.logger.info(f"    no_speech_threshold: {self.no_speech_threshold}")
        self.logger.info(f"    compression_ratio_threshold: {self.compression_ratio_threshold}")
        
        try:
            # MLX loads model on-demand, just validate it's available
            cache_dir = Path.home() / '.cache' / 'huggingface' / 'hub'
            self.logger.info(f"  Cache directory: {cache_dir}")
            self.model_loaded = True
            self.logger.info("  ✓ MLX backend ready (2-4x faster than CPU)")
            return True
        except Exception as e:
            self.logger.error(f"  Failed to initialize MLX backend: {e}", exc_info=True)
            return False
    
    def transcribe(
        self,
        audio_file: str,
        language: Optional[str] = None,
        task: str = "transcribe",
        batch_size: int = 16,
        initial_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribe using MLX-Whisper (native MPS acceleration)
        
        MPS ARCHITECTURE:
        - Clean ASR transcription on native MPS (no bias parameters)
        - Bias correction handled in separate post-ASR stage
        - This separation allows:
          * Full MPS GPU acceleration (2-4x faster)
          * No CTranslate2 limitations
          * Flexible bias correction methods
        
        Args:
            audio_file: Path to audio file
            language: Source language
            task: 'transcribe' or 'translate'
            batch_size: Batch size (unused by MLX)
            initial_prompt: Ignored (bias in separate stage)
            
        Returns:
            Transcription result
        """
        if not self.model_loaded:
            raise RuntimeError("MLX backend not loaded")
        
        # MPS Architecture: Bias handled in separate stage
        if initial_prompt:
            self.logger.info("  ℹ️  MPS Architecture: Bias injection deferred to post-ASR stage")
            self.logger.info("     (MLX runs clean ASR on native MPS acceleration)")
        
        # Map model names to MLX format
        model_path = self._map_model_name(self.model_name)
        
        # MLX transcribe parameters with anti-hallucination settings
        mlx_options = {
            "path_or_hf_repo": model_path,
            "verbose": False,
            "condition_on_previous_text": self.condition_on_previous_text,
            "logprob_threshold": self.logprob_threshold,
            "no_speech_threshold": self.no_speech_threshold,
            "compression_ratio_threshold": self.compression_ratio_threshold,
        }
        
        if language:
            mlx_options["language"] = language
        
        if task == "translate":
            mlx_options["task"] = "translate"
        
        self.logger.info(f"  Transcribing with MLX-Whisper...")
        
        try:
            # MLX transcribe returns segments directly
            result = self.mlx.transcribe(
                audio_file,
                **mlx_options
            )
            
            # Convert MLX format to WhisperX-compatible format
            segments = []
            if isinstance(result, dict) and "segments" in result:
                segments = result["segments"]
            else:
                # MLX might return just segments list
                segments = result if isinstance(result, list) else []
            
            # Normalize segment format
            normalized_segments = []
            for seg in segments:
                normalized_seg = {
                    "start": seg.get("start", 0.0),
                    "end": seg.get("end", 0.0),
                    "text": seg.get("text", ""),
                }
                # Copy optional fields
                for key in ["id", "seek", "tokens", "temperature", "avg_logprob", 
                           "compression_ratio", "no_speech_prob"]:
                    if key in seg:
                        normalized_seg[key] = seg[key]
                normalized_segments.append(normalized_seg)
            
            return {"segments": normalized_segments}
            
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"  MLX transcription failed: {e}", exc_info=True)
            
            # Check for HuggingFace authentication errors
            if "401" in error_msg or "expired" in error_msg.lower() or "unauthorized" in error_msg.lower():
                self.logger.error("  ✗ HuggingFace token is invalid or expired", exc_info=True)
                self.logger.error("  → Get a new token from: https://huggingface.co/settings/tokens", exc_info=True)
                self.logger.error("  → Set HF_TOKEN environment variable or update config/.env.pipeline")
                self.logger.info("  → Alternatively, use CPU backend which doesn't require HF authentication")
            elif "repository not found" in error_msg.lower() or "404" in error_msg:
                self.logger.error("  ✗ Model repository not found or not accessible")
                self.logger.error("  → Make sure you have accepted the model terms")
            
            raise
    
    def _map_model_name(self, model_name: str) -> str:
        """Map WhisperX model names to MLX format"""
        # MLX uses model sizes: tiny, base, small, medium, large, large-v2, large-v3
        model_map = {
            "large-v3": "mlx-community/whisper-large-v3-mlx",
            "large-v2": "mlx-community/whisper-large-v2-mlx",
            "large": "mlx-community/whisper-large-v3-mlx",
            "medium": "mlx-community/whisper-medium-mlx",
            "small": "mlx-community/whisper-small-mlx",
            "base": "mlx-community/whisper-base-mlx",
            "tiny": "mlx-community/whisper-tiny-mlx",
        }
        return model_map.get(model_name, model_name)
    
    def load_align_model(self, language: str) -> bool:
        """MLX doesn't have separate alignment - done during transcription"""
        self.logger.info(f"  MLX alignment: integrated in transcription")
        return True
    
    def align_segments(
        self,
        segments: List[Dict],
        audio_file: str,
        language: str
    ) -> Dict[str, Any]:
        """
        MLX-Whisper provides word-level timestamps during transcription.
        If segments don't have word timestamps, we need to re-transcribe with word_timestamps=True
        """
        # Check if we already have word-level timestamps
        if segments and "words" in segments[0]:
            return {"segments": segments}
        
        # Need to re-transcribe with word-level timestamps
        self.logger.info("  Re-transcribing with word-level timestamps...")
        
        model_path = self._map_model_name(self.model_name)
        
        try:
            result = self.mlx.transcribe(
                audio_file,
                path_or_hf_repo=model_path,
                word_timestamps=True,
                verbose=False
            )
            
            segments = result.get("segments", result if isinstance(result, list) else [])
            return {"segments": segments}
            
        except Exception as e:
            self.logger.warning(f"  Word-level alignment failed: {e}")
            return {"segments": segments}
    
    def cleanup(self) -> None:
        """Clean up MLX resources"""
        import gc
        # MLX uses lazy loading, just force garbage collection
        gc.collect()
        try:
            import mlx.core as mx
            # Clear MLX memory cache (use mx.clear_cache instead of deprecated mx.metal.clear_cache)
            mx.clear_cache()
        except:
            pass


def create_backend(
    backend_type: str,
    model_name: str,
    device: str,
    compute_type: str,
    logger: logging.Logger,
    condition_on_previous_text: bool = False,  # False prevents hallucination loops
    logprob_threshold: float = -1.0,
    no_speech_threshold: float = 0.6,
    compression_ratio_threshold: float = 2.4
) -> Optional[WhisperBackend]:
    """
    Factory function to create appropriate backend
    
    Args:
        backend_type: 'auto', 'whisperx', 'mlx', 'ctranslate2'
        model_name: Model name
        device: Target device (cpu, cuda, mps)
        compute_type: Compute type
        logger: Logger instance
        condition_on_previous_text: Condition on previous text (anti-hallucination)
        logprob_threshold: Log probability threshold (anti-hallucination)
        no_speech_threshold: No speech threshold (anti-hallucination)
        compression_ratio_threshold: Compression ratio threshold (anti-hallucination)
    
    Returns:
        WhisperBackend instance or None if creation failed
    """
    # Auto-detect best backend
    if backend_type == "auto":
        if device.lower() == "mps":
            # Check if MLX is available
            try:
                import mlx_whisper
                logger.info("Auto-detected: MLX backend for MPS device")
                backend_type = "mlx"
            except ImportError:
                logger.warning("MLX-Whisper not available, falling back to WhisperX")
                backend_type = "whisperx"
        else:
            backend_type = "whisperx"
    
    # Create backend
    if backend_type in ["whisperx", "ctranslate2"]:
        return WhisperXBackend(
            model_name, device, compute_type, logger,
            condition_on_previous_text, logprob_threshold,
            no_speech_threshold, compression_ratio_threshold
        )
    elif backend_type == "mlx":
        return MLXWhisperBackend(
            model_name, device, compute_type, logger,
            condition_on_previous_text, logprob_threshold,
            no_speech_threshold, compression_ratio_threshold
        )
    else:
        logger.error(f"Unknown backend type: {backend_type}")
        return None


def get_recommended_backend(device: str, logger: logging.Logger) -> str:
    """
    Get recommended backend for the given device
    
    Architecture:
    - MPS: Use MLX for native acceleration (no bias in ASR)
           → Bias injection handled in separate post-ASR stage
    - CUDA: Use WhisperX with bias parameters (optimal)
    - CPU: Use WhisperX with bias parameters (optimal)
    
    Preference: MPS > CUDA > CPU (performance-based)
    
    Args:
        device: Target device (cpu, cuda, mps)
        logger: Logger instance
    
    Returns:
        Recommended backend type
    """
    device_lower = device.lower()
    
    if device_lower == "mps":
        try:
            import mlx_whisper
            logger.info("✓ MPS: Using MLX-Whisper (native GPU acceleration)")
            logger.info("  → ASR runs clean on MPS (2-4x faster than CPU)")
            logger.info("  → Bias injection: post-ASR stage (bias_injection)")
            return "mlx"
        except ImportError:
            logger.warning("⚠ MLX-Whisper not installed (recommended for MPS)")
            logger.warning("  Install with: pip install mlx-whisper")
            logger.warning("  Falling back to WhisperX on CPU (with bias)")
            return "whisperx"
    elif device_lower == "cuda":
        logger.info("✓ CUDA: Using WhisperX (GPU acceleration + bias parameters)")
        return "whisperx"
    else:
        logger.info(f"✓ CPU: Using WhisperX (with bias parameters)")
        return "whisperx"
