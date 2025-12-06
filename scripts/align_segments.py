#!/usr/bin/env python3
"""
Alignment subprocess script - runs in WhisperX environment

This script is called as a subprocess to perform word-level alignment
using WhisperX, avoiding MLX segfaults.

Architecture:
- Runs in separate process (isolation from MLX)
- Uses WhisperX alignment model (stable)
- Takes segments + audio, returns aligned segments with word timestamps

Usage:
    python align_segments.py --audio <path> --segments <json> --language <code>
"""
# Standard library
import argparse
import json
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List

# Add parent to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Configure logging to stderr (not stdout - we use stdout for JSON)
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stderr  # ← Send logs to stderr, not stdout
)

logger = logging.getLogger(__name__)

# Suppress whisperx warnings that interfere with JSON output
import warnings
warnings.filterwarnings('ignore')
logging.getLogger('whisperx').setLevel(logging.ERROR)


def load_segments(segments_file: Path) -> List[Dict[str, Any]]:
    """Load segments from JSON file"""
    with open(segments_file) as f:
        data = json.load(f)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and "segments" in data:
            return data["segments"]
        else:
            raise ValueError(f"Unexpected segments file format: {type(data)}")


def align_with_whisperx(
    segments: List[Dict[str, Any]],
    audio_file: str,
    language: str,
    device: str = "mps"
) -> Dict[str, Any]:
    """
    Align segments using WhisperX alignment model
    
    Args:
        segments: List of segments with start/end times
        audio_file: Path to audio file
        language: Language code (en, hi, etc.)
        device: Device to use (mps, cuda, cpu)
        
    Returns:
        Dict with aligned segments including word-level timestamps
    """
    try:
        import whisperx
    except ImportError:
        logger.error("WhisperX not installed in current environment")
        logger.error("Install with: pip install git+https://github.com/m-bain/whisperx.git")
        return {"segments": segments}  # Return original
    
    try:
        logger.info(f"Loading alignment model for language: {language}")
        
        # Load alignment model
        align_model, align_metadata = whisperx.load_align_model(
            language_code=language,
            device=device
        )
        
        logger.info(f"Loading audio: {audio_file}")
        
        # Load audio
        audio = whisperx.load_audio(audio_file)
        
        logger.info(f"Aligning {len(segments)} segments...")
        
        # Align segments
        result = whisperx.align(
            segments,
            align_model,
            align_metadata,
            audio,
            device
        )
        
        logger.info(f"✓ Alignment complete: {len(result.get('segments', []))} segments")
        
        return result
        
    except Exception as e:
        logger.error(f"Alignment failed: {e}", exc_info=True)
        return {"segments": segments}  # Return original on failure


def main() -> int:
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Align ASR segments with word-level timestamps using WhisperX"
    )
    parser.add_argument("--audio", required=True, help="Path to audio file")
    parser.add_argument("--segments", required=True, help="Path to segments JSON file")
    parser.add_argument("--language", required=True, help="Language code (en, hi, etc.)")
    parser.add_argument("--device", default="mps", help="Device (mps, cuda, cpu)")
    parser.add_argument("--output", help="Output file path (optional, defaults to stdout)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    # Adjust log level if debug
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Load segments
        segments = load_segments(Path(args.segments))
        
        # Align
        result = align_with_whisperx(
            segments,
            args.audio,
            args.language,
            args.device
        )
        
        # Output result - either to file or stdout
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            logger.info(f"Alignment written to: {args.output}")
        else:
            # Output to stdout (may be mixed with logs)
            sys.stdout.write(json.dumps(result))
            sys.stdout.flush()
        
        return 0
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        # Still output something valid
        sys.stdout.write(json.dumps({"segments": [], "error": str(e)}))
        sys.stdout.flush()
        return 1


if __name__ == "__main__":
    sys.exit(main())
