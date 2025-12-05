"""
transcription.py - Core transcription strategies

Handles:
- Whole file transcription
- Hybrid transcription (whole + bias)
- Windowed transcription with rolling context

Status: Module structure placeholder
Future: Extract transcription strategies from whisperx_integration.py
"""

# Standard library
from typing import List, Dict, Optional, Any


class TranscriptionEngine:
    """Core transcription strategies implementation"""
    
    def __init__(self, model: Any, backend: Any, logger: Any, chunker: Any):
        """Initialize transcription engine"""
        self.model = model
        self.backend = backend
        self.logger = logger
        self.chunker = chunker
    
    def transcribe_whole(self, audio_file: str, language: Optional[str] = None, **kwargs) -> Dict:
        """Transcribe entire file at once"""
        raise NotImplementedError("Extract from WhisperXProcessor._transcribe_whole()")


__all__ = ['TranscriptionEngine']
