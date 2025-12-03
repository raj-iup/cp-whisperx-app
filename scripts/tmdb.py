#!/usr/bin/env python3
"""
TMDB stage: Wrapper for tmdb_enrichment.py
"""
# Standard library
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from tmdb_enrichment import main

if __name__ == "__main__":
    sys.exit(main())
