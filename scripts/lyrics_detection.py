#!/usr/bin/env python3
"""
Lyrics Detection stage: Detect and handle lyrics
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from bias_injection import main

if __name__ == "__main__":
    sys.exit(main())
