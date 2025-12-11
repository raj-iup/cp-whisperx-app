"""
processor.py - Main WhisperX processor coordinator

This module serves as the main entry point for the modularized WhisperX system.
Currently wraps the original whisperx_integration.py for backward compatibility.

Future: Will orchestrate ModelManager, TranscriptionEngine, etc.
"""

# Standard library
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Add scripts directory to path for whisperx_integration import
SCRIPTS_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

# Import original WhisperXProcessor for now
# This maintains 100% backward compatibility while establishing module structure
import whisperx_integration
WhisperXProcessor = whisperx_integration.WhisperXProcessor

__all__ = ['WhisperXProcessor']
