#!/usr/bin/env python3
"""
Pre-NER stage: Extract entities before processing
"""
# Standard library
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from ner_extraction import main

if __name__ == "__main__":
    # Run NER extraction in pre-processing mode
    sys.exit(main())
