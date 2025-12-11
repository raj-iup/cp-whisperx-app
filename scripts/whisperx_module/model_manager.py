"""
model_manager.py - Whisper model loading and lifecycle management

Handles:
- Backend selection (MLX, WhisperX, CUDA)
- Model loading with fallback support
- Alignment model loading
- Resource cleanup
"""

# Standard library
import sys
from pathlib import Path
from typing import Any, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Local
from shared.logger import get_logger
from whisper_backends import create_backend, get_recommended_backend


class ModelManager:
    """Manages Whisper model loading and lifecycle"""
    
    def __init__(
        self,
        model_name: str,
        device: str,
        compute_type: str,
        backend_type: str,
        logger: Any,
        condition_on_previous_text: bool = True,
        logprob_threshold: float = -1.0,
        no_speech_threshold: float = 0.6,
        compression_ratio_threshold: float = 2.4
    ):
        """
        Initialize ModelManager
        
        Args:
            model_name: Whisper model name (e.g., "large-v3")
            device: Device to use (cpu, cuda, mps)
            compute_type: Computation type (float16, int8, etc.)
            backend_type: Backend type (auto, mlx, whisperx)
            logger: Logger instance
            condition_on_previous_text: Use previous text for context
            logprob_threshold: Log probability threshold
            no_speech_threshold: No speech detection threshold
            compression_ratio_threshold: Compression ratio threshold
        """
        self.model_name = model_name
        self.device = device
        self.compute_type = compute_type
        self.backend_type = backend_type
        self.logger = logger
        self.condition_on_previous_text = condition_on_previous_text
        self.logprob_threshold = logprob_threshold
        self.no_speech_threshold = no_speech_threshold
        self.compression_ratio_threshold = compression_ratio_threshold
        
        self.backend = None
        self.backend_name = backend_type
    
    def load_model(self) -> None:
        """Load Whisper model using appropriate backend"""
        self.logger.info(f"Loading Whisper model: {self.model_name}")
        self.logger.info(f"  Device requested: {self.device}")
        self.logger.info(f"  Backend: {self.backend_type}")
        
        # Get recommended backend if auto
        if self.backend_type == "auto":
            recommended = get_recommended_backend(self.device, self.logger)
            self.logger.info(f"  Auto-detected backend: {recommended}")
            backend_to_use = recommended
        else:
            backend_to_use = self.backend_type
        
        # Create backend instance
        self.backend = create_backend(
            backend_to_use,
            self.model_name,
            self.device,
            self.compute_type,
            self.logger,
            self.condition_on_previous_text,
            self.logprob_threshold,
            self.no_speech_threshold,
            self.compression_ratio_threshold
        )
        
        if not self.backend:
            raise RuntimeError(f"Failed to create backend: {backend_to_use}")
        
        # Load model with fallback support
        success = self.backend.load_model()
        
        # Handle fallback from MLX to WhisperX
        if success == "fallback_to_whisperx":
            self.logger.info("=" * 60)
            self.logger.info("MLX BACKEND FALLBACK")
            self.logger.info("=" * 60)
            self.logger.info("Recreating backend with WhisperX...")
            
            # Switch to WhisperX backend
            backend_to_use = "whisperx"
            self.backend_name = backend_to_use
            
            # Recreate backend
            self.backend = create_backend(
                backend_to_use,
                self.model_name,
                self.device,
                self.compute_type,
                self.logger,
                self.condition_on_previous_text,
                self.logprob_threshold,
                self.no_speech_threshold,
                self.compression_ratio_threshold
            )
            
            if not self.backend:
                raise RuntimeError(f"Failed to create fallback backend: {backend_to_use}")
            
            # Try loading with WhisperX
            success = self.backend.load_model()
            
            if not success:
                raise RuntimeError(f"Failed to load model with fallback backend: {backend_to_use}")
            
            self.logger.info(f"  ✓ Successfully fell back to WhisperX backend")
        elif not success:
            raise RuntimeError(f"Failed to load model with backend: {self.backend.name}")
        
        # Update device to actual device used (may have fallen back)
        self.device = self.backend.device
        self.logger.info(f"  ✓ Model loaded with backend: {self.backend.name}")
        self.logger.info(f"  ✓ Active device: {self.device}")
    
    def load_align_model(self, language: str) -> None:
        """
        Load alignment model for word-level timestamps
        
        Args:
            language: Language code (e.g., "en", "hi")
        """
        if not self.backend:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        self.logger.info(f"Loading alignment model for language: {language}")
        success = self.backend.load_align_model(language)
        
        if success:
            self.logger.info("  ✓ Alignment model loaded")
        else:
            self.logger.warning("  ⚠ Alignment model not available")
    
    def cleanup(self) -> None:
        """Clean up resources"""
        if self.backend:
            self.backend.cleanup()
            self.backend = None
    
    def __del__(self) -> None:
        """Destructor to ensure cleanup"""
        try:
            self.cleanup()
        except:
            pass
