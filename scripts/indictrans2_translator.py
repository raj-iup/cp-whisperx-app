#!/usr/bin/env python3
"""
IndicTrans2 Translator Module - Wrapper for subprocess calls

This module provides translation functions that can be imported
by subprocess workers running in the IndicTrans2 environment.
"""
# Standard library
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import from the main translation stage module
# Note: 10_translation.py can't be imported directly due to leading digit,
# so we use importlib
import importlib.util

spec = importlib.util.spec_from_file_location(
    "translation_stage",
    PROJECT_ROOT / "scripts" / "10_translation.py"
)
translation_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(translation_module)

# Re-export the translate function
translate_whisperx_result = translation_module.translate_whisperx_result

# Re-export the translator class
IndicTrans2Translator = translation_module.IndicTrans2Translator

__all__ = ['translate_whisperx_result', 'IndicTrans2Translator']
