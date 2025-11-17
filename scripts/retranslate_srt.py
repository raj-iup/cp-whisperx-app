#!/usr/bin/env python3
"""
Re-translate SRT files using a better translation model
Fixes translation mismatches from WhisperX translation
"""
import sys
import re
import argparse
from pathlib import Path
from typing import List, Tuple, Optional
from tqdm import tqdm

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.logger import PipelineLogger


class SRTSubtitle:
    """Represents a single SRT subtitle entry"""
    def __init__(self, index: int, start: str, end: str, text: str):
        self.index = index
        self.start = start
        self.end = end
        self.text = text
    
    def __str__(self):
        return f"{self.index}\n{self.start} --> {self.end}\n{self.text}\n"


def parse_srt(srt_path: Path) -> List[SRTSubtitle]:
    """Parse SRT file into subtitle objects"""
    subtitles = []
    
    with open(srt_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split by double newline (subtitle separator)
    blocks = re.split(r'\n\s*\n', content.strip())
    
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) >= 3:
            try:
                index = int(lines[0].strip())
                timestamp_line = lines[1].strip()
                
                # Parse timestamp
                if '-->' in timestamp_line:
                    parts = timestamp_line.split('-->')
                    start = parts[0].strip()
                    end = parts[1].strip()
                    
                    # Join all remaining lines as text (may be multi-line)
                    text = '\n'.join(lines[2:])
                    
                    subtitles.append(SRTSubtitle(index, start, end, text))
            except (ValueError, IndexError) as e:
                print(f"Warning: Failed to parse subtitle block: {e}", file=sys.stderr)
                continue
    
    return subtitles


def save_srt(subtitles: List[SRTSubtitle], output_path: Path):
    """Save subtitles to SRT file"""
    with open(output_path, 'w', encoding='utf-8') as f:
        for i, sub in enumerate(subtitles):
            f.write(str(sub))
            # Add blank line between subtitles (except after last one)
            if i < len(subtitles) - 1:
                f.write('\n')


def translate_text_googletrans(text: str, src_lang: str = 'auto', dest_lang: str = 'en') -> str:
    """Translate text using googletrans library"""
    try:
        from googletrans import Translator
        translator = Translator()
        result = translator.translate(text, src=src_lang, dest=dest_lang)
        return result.text
    except Exception as e:
        print(f"Error with googletrans: {e}", file=sys.stderr)
        return text


def translate_text_deep_translator(text: str, src_lang: str = 'auto', dest_lang: str = 'en') -> str:
    """Translate text using deep-translator library"""
    try:
        from deep_translator import GoogleTranslator
        import time
        
        # Map language codes
        src = src_lang if src_lang != 'auto' else 'auto'
        
        translator = GoogleTranslator(source=src, target=dest_lang)
        result = translator.translate(text)
        
        # Small delay to avoid rate limiting
        time.sleep(0.1)
        
        return result
    except Exception as e:
        print(f"Error with deep-translator: {e}", file=sys.stderr)
        return text


def translate_text_argos(text: str, src_lang: str = 'hi', dest_lang: str = 'en') -> str:
    """Translate text using argostranslate (offline)"""
    try:
        import argostranslate.package
        import argostranslate.translate
        
        # Get available packages
        available_packages = argostranslate.package.get_available_packages()
        
        # Find and install the package
        package_to_install = next(
            filter(
                lambda x: x.from_code == src_lang and x.to_code == dest_lang,
                available_packages
            )
        )
        
        if not package_to_install.package_version:
            argostranslate.package.install_from_path(package_to_install.download())
        
        # Translate
        result = argostranslate.translate.translate(text, src_lang, dest_lang)
        return result
    except Exception as e:
        print(f"Error with argostranslate: {e}", file=sys.stderr)
        return text


def detect_translation_method():
    """Detect which translation method is available"""
    methods = []
    
    # Try googletrans
    try:
        import googletrans
        methods.append('googletrans')
    except ImportError:
        pass
    
    # Try deep-translator
    try:
        import deep_translator
        methods.append('deep-translator')
    except ImportError:
        pass
    
    # Try argostranslate
    try:
        import argostranslate
        methods.append('argostranslate')
    except ImportError:
        pass
    
    return methods


def translate_subtitle(sub: SRTSubtitle, method: str = 'auto', src_lang: str = 'hi', dest_lang: str = 'en', logger: Optional[PipelineLogger] = None) -> SRTSubtitle:
    """Translate a single subtitle using specified method"""
    
    # Skip if text is empty or only punctuation/numbers
    if not sub.text.strip() or not any(c.isalpha() for c in sub.text):
        return sub
    
    # Skip if text is already in English (heuristic: mostly ASCII)
    ascii_count = sum(1 for c in sub.text if ord(c) < 128)
    if ascii_count / len(sub.text) > 0.9:
        if logger:
            logger.debug(f"Skipping translation for subtitle {sub.index} (already English)")
        return sub
    
    try:
        if method == 'googletrans':
            translated_text = translate_text_googletrans(sub.text, src_lang, dest_lang)
        elif method == 'deep-translator':
            translated_text = translate_text_deep_translator(sub.text, src_lang, dest_lang)
        elif method == 'argostranslate':
            translated_text = translate_text_argos(sub.text, src_lang, dest_lang)
        else:
            # Auto-detect
            available = detect_translation_method()
            if 'deep-translator' in available:
                translated_text = translate_text_deep_translator(sub.text, src_lang, dest_lang)
            elif 'googletrans' in available:
                translated_text = translate_text_googletrans(sub.text, src_lang, dest_lang)
            elif 'argostranslate' in available:
                translated_text = translate_text_argos(sub.text, src_lang, dest_lang)
            else:
                if logger:
                    logger.error("No translation library available!")
                return sub
        
        return SRTSubtitle(sub.index, sub.start, sub.end, translated_text)
    
    except Exception as e:
        if logger:
            logger.error(f"Failed to translate subtitle {sub.index}: {e}")
        return sub


def retranslate_srt(
    input_srt: Path,
    output_srt: Path,
    method: str = 'auto',
    src_lang: str = 'hi',
    dest_lang: str = 'en',
    logger: Optional[PipelineLogger] = None
):
    """
    Re-translate an SRT file
    
    Args:
        input_srt: Path to source SRT file
        output_srt: Path to output translated SRT file
        method: Translation method (googletrans, deep-translator, argostranslate, auto)
        src_lang: Source language code
        dest_lang: Destination language code
        logger: Logger instance
    """
    if logger:
        logger.info(f"Re-translating SRT: {input_srt}")
        logger.info(f"  Source language: {src_lang}")
        logger.info(f"  Target language: {dest_lang}")
        logger.info(f"  Method: {method}")
    
    # Parse source SRT
    subtitles = parse_srt(input_srt)
    if logger:
        logger.info(f"  Parsed {len(subtitles)} subtitles")
    
    # Detect available translation methods
    available_methods = detect_translation_method()
    if not available_methods:
        error_msg = "No translation libraries available. Install one of: googletrans, deep-translator, argostranslate"
        if logger:
            logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    if method == 'auto':
        method = available_methods[0]
    
    if logger:
        logger.info(f"  Using translation method: {method}")
        logger.info(f"  Available methods: {', '.join(available_methods)}")
    
    # Translate each subtitle
    translated_subtitles = []
    for sub in tqdm(subtitles, desc="Translating", disable=logger is None):
        translated_sub = translate_subtitle(sub, method, src_lang, dest_lang, logger)
        translated_subtitles.append(translated_sub)
    
    # Save translated SRT
    save_srt(translated_subtitles, output_srt)
    
    if logger:
        logger.info(f"  Saved translated SRT: {output_srt}")


def main():
    parser = argparse.ArgumentParser(
        description='Re-translate SRT files using better translation models',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Re-translate Hinglish to English (auto-detect method)
  python retranslate_srt.py input.srt -o output-English.srt
  
  # Use specific translation method
  python retranslate_srt.py input.srt -o output.srt --method deep-translator
  
  # Specify languages
  python retranslate_srt.py input.srt -o output.srt --src-lang hi --dest-lang en
  
  # Re-translate existing job output
  python retranslate_srt.py out/2025/11/16/1/20251116-0002/06_asr/20251116-0002.srt \\
      -o out/2025/11/16/1/20251116-0002/06_asr/20251116-0002-English-Fixed.srt

Translation Methods:
  googletrans     - Free Google Translate API (may have rate limits)
  deep-translator - More reliable Google Translate wrapper
  argostranslate  - Offline translation (requires model download)
  auto            - Auto-detect best available method (default)

Install translation libraries:
  pip install deep-translator googletrans==4.0.0-rc1 argostranslate
        """
    )
    
    parser.add_argument('input_srt', type=Path, help='Input SRT file to translate')
    parser.add_argument('-o', '--output', type=Path, help='Output translated SRT file (default: input-English.srt)')
    parser.add_argument('--method', choices=['auto', 'googletrans', 'deep-translator', 'argostranslate'], 
                        default='auto', help='Translation method (default: auto)')
    parser.add_argument('--src-lang', default='hi', help='Source language code (default: hi for Hindi)')
    parser.add_argument('--dest-lang', default='en', help='Destination language code (default: en)')
    parser.add_argument('--log', type=Path, help='Log file path')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Validate input file
    if not args.input_srt.exists():
        print(f"Error: Input file not found: {args.input_srt}", file=sys.stderr)
        return 1
    
    # Determine output file
    if args.output:
        output_srt = args.output
    else:
        output_srt = args.input_srt.parent / f"{args.input_srt.stem}-English.srt"
    
    # Setup logger
    if args.log:
        logger = PipelineLogger("retranslate_srt", args.log)
    else:
        logger = None
    
    # Use print for verbose output if no log file
    if args.verbose and not logger:
        print(f"Input: {args.input_srt}")
        print(f"Output: {output_srt}")
        print(f"Method: {args.method}")
        print(f"Source language: {args.src_lang}")
        print(f"Target language: {args.dest_lang}")
        print()
    
    try:
        retranslate_srt(
            args.input_srt,
            output_srt,
            method=args.method,
            src_lang=args.src_lang,
            dest_lang=args.dest_lang,
            logger=logger
        )
        
        print(f"✓ Translation complete: {output_srt}")
        return 0
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if logger:
            logger.error(f"Translation failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
