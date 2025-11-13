#!/usr/bin/env python3
"""
Finalize stage: Organize and finalize output
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from finalize_output import main

if __name__ == "__main__":
    sys.exit(main())
