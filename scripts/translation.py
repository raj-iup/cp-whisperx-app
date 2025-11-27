#!/usr/bin/env python3
"""
translation.py - Standalone translation stage

Stage: 10_translation (Stage 10)
Purpose: Translate transcripts from source language to target language

Supports multiple translation backends:
- IndicTrans2: For Indic languages → English (AI4Bharat model)
- NLLB: For general multilingual translation
- Whisper: Built-in Whisper translation (if available)

Input: transcript.json from ASR or aligned transcript
Output: translated_transcript.json with translations

Can also translate existing SRT files for retranslation workflows.
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.stage_utils import StageIO, get_stage_logger
from shared.config import load_config


def translate_with_indictrans2(
    segments: List[Dict[str, Any]],
    source_lang: str,
    target_lang: str,
    logger
) -> List[Dict[str, Any]]:
    """
    Translate segments using IndicTrans2
    
    Args:
        segments: List of segment dictionaries with 'text' field
        source_lang: Source language code (e.g., 'hi')
        target_lang: Target language code (e.g., 'en')
        logger: Logger instance
        
    Returns:
        Segments with 'translation' field added
    """
    try:
        from indictrans2_translator import translate_segments
        logger.info("Using IndicTrans2 translator")
        
        # Extract texts
        texts = [seg.get('text', '') for seg in segments]
        
        # Translate
        translations = translate_segments(
            texts,
            source_lang=source_lang,
            target_lang=target_lang,
            logger=logger
        )
        
        # Add translations to segments
        translated_segments = []
        for seg, translation in zip(segments, translations):
            translated_seg = seg.copy()
            translated_seg['translation'] = translation
            translated_segments.append(translated_seg)
        
        return translated_segments
        
    except ImportError:
        logger.error("IndicTrans2 not available. Install with: pip install indictrans2")
        raise
    except Exception as e:
        logger.error(f"IndicTrans2 translation failed: {e}")
        raise


def translate_with_nllb(
    segments: List[Dict[str, Any]],
    source_lang: str,
    target_lang: str,
    logger
) -> List[Dict[str, Any]]:
    """
    Translate segments using NLLB
    
    Args:
        segments: List of segment dictionaries with 'text' field
        source_lang: Source language code
        target_lang: Target language code
        logger: Logger instance
        
    Returns:
        Segments with 'translation' field added
    """
    try:
        from nllb_translator import translate_text
        logger.info("Using NLLB translator")
        
        translated_segments = []
        for seg in segments:
            text = seg.get('text', '')
            if not text:
                translated_seg = seg.copy()
                translated_seg['translation'] = ''
                translated_segments.append(translated_seg)
                continue
            
            translation = translate_text(
                text,
                source_lang=source_lang,
                target_lang=target_lang
            )
            
            translated_seg = seg.copy()
            translated_seg['translation'] = translation
            translated_segments.append(translated_seg)
        
        return translated_segments
        
    except ImportError:
        logger.error("NLLB not available. Install with: pip install transformers")
        raise
    except Exception as e:
        logger.error(f"NLLB translation failed: {e}")
        raise


def translate_with_whisper(
    segments: List[Dict[str, Any]],
    audio_file: Path,
    logger
) -> List[Dict[str, Any]]:
    """
    Translate segments using Whisper's built-in translation
    
    Note: This requires re-running Whisper with task='translate'
    which is less efficient. Prefer IndicTrans2 or NLLB.
    
    Args:
        segments: List of segment dictionaries
        audio_file: Path to audio file
        logger: Logger instance
        
    Returns:
        Segments with 'translation' field added
    """
    logger.warning("Whisper translation requires re-processing audio")
    logger.warning("Consider using IndicTrans2 or NLLB for better performance")
    
    # For now, we won't implement this as it's inefficient
    # The user should use IndicTrans2 or NLLB instead
    raise NotImplementedError(
        "Whisper translation not implemented. Use IndicTrans2 or NLLB instead."
    )


def main():
    """
    Main entry point for translation stage
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    try:
        # Setup stage I/O
        stage_io = StageIO("translation")
        logger = get_stage_logger("translation", stage_io=stage_io)
        
        logger.info("=" * 70)
        logger.info("TRANSLATION STAGE: Transcript Translation")
        logger.info("=" * 70)
        
        # Load config
        try:
            config = load_config()
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return 1
        
        # Get translation settings from config
        source_lang = getattr(config, 'whisper_language', 'hi')
        target_lang = getattr(config, 'target_language', 'en')
        translator = getattr(config, 'translator', 'indictrans2').lower()
        
        logger.info(f"Source language: {source_lang}")
        logger.info(f"Target language: {target_lang}")
        logger.info(f"Translator: {translator}")
        
        # Check if translation is needed
        if source_lang == target_lang:
            logger.info("Source and target languages are the same, skipping translation")
            return 0
        
        # Get input transcript
        # Try aligned transcript first, fall back to regular transcript
        transcript_file = stage_io.get_input_path(
            "aligned_transcript.json",
            from_stage="alignment",
            required=False
        )
        
        if not transcript_file or not transcript_file.exists():
            transcript_file = stage_io.get_input_path(
                "transcript.json",
                from_stage="asr"
            )
        
        if not transcript_file.exists():
            logger.error(f"Transcript file not found: {transcript_file}")
            return 1
        
        logger.info(f"Input transcript: {transcript_file}")
        
        # Load transcript data
        try:
            with open(transcript_file, 'r', encoding='utf-8') as f:
                transcript_data = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load transcript: {e}")
            return 1
        
        segments = transcript_data.get('segments', [])
        logger.info(f"Loaded {len(segments)} segments")
        
        if len(segments) == 0:
            logger.warning("No segments found in transcript")
            return 1
        
        # Translate based on selected translator
        try:
            if translator == 'indictrans2':
                translated_segments = translate_with_indictrans2(
                    segments, source_lang, target_lang, logger
                )
            elif translator == 'nllb':
                translated_segments = translate_with_nllb(
                    segments, source_lang, target_lang, logger
                )
            elif translator == 'whisper':
                # Need audio file for Whisper translation
                audio_file = stage_io.get_input_path("audio.wav", from_stage="demux")
                translated_segments = translate_with_whisper(
                    segments, audio_file, logger
                )
            else:
                logger.error(f"Unknown translator: {translator}")
                logger.error("Supported: indictrans2, nllb")
                return 1
        
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return 1
        
        # Save translated transcript
        output_data = transcript_data.copy()
        output_data['segments'] = translated_segments
        output_data['translation_metadata'] = {
            'source_language': source_lang,
            'target_language': target_lang,
            'translator': translator
        }
        
        output_file = stage_io.get_output_path("translated_transcript.json")
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save translated transcript: {e}")
            return 1
        
        logger.info(f"✓ Saved translated transcript: {output_file}")
        
        # Calculate statistics
        original_chars = sum(len(seg.get('text', '')) for seg in segments)
        translated_chars = sum(len(seg.get('translation', '')) for seg in translated_segments)
        
        logger.info(f"Translated {len(translated_segments)} segments")
        logger.info(f"Original text: {original_chars} characters")
        logger.info(f"Translated text: {translated_chars} characters")
        
        logger.info("=" * 70)
        logger.info("TRANSLATION STAGE COMPLETED")
        logger.info("=" * 70)
        
        return 0
        
    except KeyboardInterrupt:
        logger.warning("✗ Translation interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"✗ Translation failed: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
