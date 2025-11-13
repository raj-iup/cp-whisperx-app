#!/usr/bin/env python3
"""
WhisperX ASR stage: Automatic Speech Recognition
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from whisperx_integration import main

if __name__ == "__main__":
    sys.exit(main())
