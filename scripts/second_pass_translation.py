#!/usr/bin/env python3
"""
Second Pass Translation stage: Translation refinement
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from translation_refine import main

if __name__ == "__main__":
    sys.exit(main())
