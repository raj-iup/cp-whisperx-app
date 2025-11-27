#!/usr/bin/env python3
"""
mlx_alignment.py - Word-level alignment for MLX-Whisper transcripts

MLX-Whisper can provide word-level timestamps when transcribing with word_timestamps=True.
This module performs alignment on existing segment-level transcripts.

Can be used in two modes:
1. Pipeline mode: Uses StageIO for path management
2. CLI mode: Direct file path arguments
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

# Add project root for StageIO import
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from shared.stage_utils import StageIO, get_stage_logger
    from shared.config import load_config
    STAGEIO_AVAILABLE = True
except ImportError:
    STAGEIO_AVAILABLE = False


def align_mlx_segments(
    audio_file: Path,
    segments_file: Path,
    output_file: Path,
    model: str = "mlx-community/whisper-large-v3-mlx",
    language: str = "hi",
    logger: logging.Logger = None
) -> bool:
    """
    Perform word-level alignment on MLX transcripts
    
    Args:
        audio_file: Path to audio file
        segments_file: Path to segments JSON (segment-level only)
        output_file: Path to output aligned segments JSON
        model: MLX model to use
        language: Source language code
        logger: Logger instance
        
    Returns:
        True if successful
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    try:
        import mlx_whisper
    except ImportError:
        logger.error("MLX-Whisper not installed. Install with: pip install mlx-whisper")
        return False
    
    # Load existing segments
    logger.info(f"Loading segments from: {segments_file}")
    with open(segments_file) as f:
        data = json.load(f)
    
    segments = data.get("segments", [])
    if not segments:
        logger.error("No segments found in input file")
        return False
    
    # Check if already aligned
    has_words = segments[0].get("words") if segments else []
    if has_words and len(has_words) > 0:
        logger.info(f"✓ Segments already have word-level timestamps ({len(has_words)} words in first segment)")
        logger.info("Skipping alignment - copying input to output")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    
    logger.info(f"Re-transcribing with word-level timestamps...")
    logger.info(f"Model: {model}")
    logger.info(f"Language: {language}")
    logger.info(f"Audio: {audio_file}")
    
    # Transcribe with word timestamps
    result = mlx_whisper.transcribe(
        str(audio_file),
        path_or_hf_repo=model,
        language=language,
        word_timestamps=True,
        verbose=False,
        # Anti-hallucination settings
        condition_on_previous_text=False,
        logprob_threshold=-1.0,
        no_speech_threshold=0.6,
        compression_ratio_threshold=2.4
    )
    
    # Extract aligned segments
    aligned_segments = result.get("segments", [])
    
    if not aligned_segments:
        logger.error("No segments returned from alignment")
        return False
    
    # Count words
    total_words = sum(len(seg.get("words", [])) for seg in aligned_segments)
    logger.info(f"✓ Alignment completed: {len(aligned_segments)} segments, {total_words} words")
    
    # Verify word timestamps exist
    words_with_timing = sum(
        1 for seg in aligned_segments 
        for word in seg.get("words", []) 
        if "start" in word and "end" in word
    )
    logger.info(f"✓ Words with timestamps: {words_with_timing}/{total_words}")
    
    # Save aligned segments
    output_data = {
        "segments": aligned_segments,
        "language": result.get("language", language),
        "text": result.get("text", "")
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"✓ Aligned segments saved: {output_file}")
    
    return True


def main():
    """
    Main entry point - supports both pipeline and CLI modes.
    
    Pipeline mode (no args): Uses StageIO to find input/output
    CLI mode (with args): Uses explicit file paths
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Perform word-level alignment on MLX-Whisper transcripts"
    )
    parser.add_argument("audio", nargs='?', type=Path, help="Audio file path (optional if using StageIO)")
    parser.add_argument("segments", nargs='?', type=Path, help="Input segments JSON (optional if using StageIO)")
    parser.add_argument("output", nargs='?', type=Path, help="Output aligned segments JSON (optional if using StageIO)")
    parser.add_argument("--model", default="mlx-community/whisper-large-v3-mlx",
                       help="MLX model to use")
    parser.add_argument("--language", default="hi", help="Source language code")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--pipeline-mode", action="store_true", 
                       help="Use StageIO for input/output (automatic if no args)")
    
    args = parser.parse_args()
    
    # Determine mode: pipeline or CLI
    use_pipeline = args.pipeline_mode or (args.audio is None and STAGEIO_AVAILABLE)
    
    if use_pipeline:
        if not STAGEIO_AVAILABLE:
            print("ERROR: Pipeline mode requires StageIO but it's not available", file=sys.stderr)
            print("Either provide file arguments or ensure shared modules are accessible", file=sys.stderr)
            sys.exit(1)
        
        # Pipeline mode: Use StageIO
        stage_io = StageIO("alignment")
        logger = get_stage_logger("alignment", stage_io=stage_io)
        
        logger.info("=" * 60)
        logger.info("MLX ALIGNMENT STAGE: Word-level Timestamp Alignment")
        logger.info("=" * 60)
        
        # Load config for model and language
        try:
            config = load_config()
            model = getattr(config, 'mlx_whisper_model', args.model)
            language = getattr(config, 'whisper_language', args.language)
        except Exception as e:
            logger.warning(f"Could not load config, using defaults: {e}")
            model = args.model
            language = args.language
        
        # Get paths from StageIO
        audio_file = stage_io.get_input_path("audio.wav", from_stage="demux")
        segments_file = stage_io.get_input_path("transcript.json", from_stage="asr")
        output_file = stage_io.get_output_path("aligned_transcript.json")
        
        logger.info(f"Input audio: {audio_file}")
        logger.info(f"Input segments: {segments_file}")
        logger.info(f"Output aligned: {output_file}")
        logger.info(f"Model: {model}")
        logger.info(f"Language: {language}")
        
    else:
        # CLI mode: Use provided arguments
        if not args.audio or not args.segments or not args.output:
            parser.error("In CLI mode, all of audio, segments, and output are required")
        
        # Setup logging
        logging.basicConfig(
            level=logging.DEBUG if args.debug else logging.INFO,
            format='[%(levelname)s] %(message)s'
        )
        logger = logging.getLogger(__name__)
        
        audio_file = args.audio
        segments_file = args.segments
        output_file = args.output
        model = args.model
        language = args.language
    
    # Verify inputs
    if not audio_file.exists():
        logger.error(f"Audio file not found: {audio_file}")
        sys.exit(1)
    
    if not segments_file.exists():
        logger.error(f"Segments file not found: {segments_file}")
        sys.exit(1)
    
    # Create output directory
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Perform alignment
    try:
        success = align_mlx_segments(
            audio_file,
            segments_file,
            output_file,
            model,
            language,
            logger
        )
        
        if use_pipeline:
            if success:
                logger.info("=" * 60)
                logger.info("MLX ALIGNMENT STAGE COMPLETED SUCCESSFULLY")
                logger.info("=" * 60)
            else:
                logger.error("=" * 60)
                logger.error("MLX ALIGNMENT STAGE FAILED")
                logger.error("=" * 60)
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        logger.warning("✗ Alignment interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"✗ Alignment failed with unexpected error: {e}")
        if args.debug:
            import traceback
            logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
