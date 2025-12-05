"""
WhisperX ASR Integration Module

Modularized ASR processing with support for:
- Multiple backends (MLX, WhisperX, CUDA)
- Bias prompting strategies
- Large file chunking
- Word-level alignment

Version: 2.0.0 (Modularized from whisperx_integration.py)
Architectural Decision: AD-002

Note: Currently imports from whisperx_integration.py for backward compatibility.
      Module structure established for incremental extraction.
"""

# Standard library
import sys
from pathlib import Path

# Add project root and scripts to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
SCRIPTS_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(SCRIPTS_DIR))

# Import from original file (avoiding circular import with whisperx.audio)
import whisperx_integration

# Re-export main class
WhisperXProcessor = whisperx_integration.WhisperXProcessor

# Import modularized components (placeholders for now)
from .model_manager import ModelManager
from .bias_prompting import BiasPromptingStrategy
from .chunking import AudioChunker
from .transcription import TranscriptionEngine
from .postprocessing import ResultProcessor
from .alignment import AlignmentEngine

__all__ = [
    'WhisperXProcessor',
    'ModelManager',
    'BiasPromptingStrategy',
    'AudioChunker',
    'TranscriptionEngine',
    'ResultProcessor',
    'AlignmentEngine',
]

__version__ = "2.0.0"
