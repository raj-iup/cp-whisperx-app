#!/usr/bin/env python3
"""
WhisperX ASR stage: Automatic Speech Recognition

This is a thin wrapper around whisperx_integration.py which contains
the actual ASR logic. The separation allows for easier testing and
maintains compatibility with the pipeline architecture.

Stage: 06_asr (Stage 6)
Input: audio.wav from demux or source_separation
Output: transcript.json with word-level timestamps
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from whisperx_integration import main as whisperx_main


def main():
    """
    Main entry point for ASR stage.
    
    Delegates to whisperx_integration.main() which handles:
    - Backend selection (WhisperX/MLX)
    - Model loading
    - Audio transcription
    - Word-level alignment
    - Translation (if enabled)
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    try:
        return whisperx_main()
    except KeyboardInterrupt:
        logger.info("\n✗ ASR stage interrupted by user", file=sys.stderr)
        return 130
    except Exception as e:
        logger.info(f"\n✗ ASR stage failed with unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
