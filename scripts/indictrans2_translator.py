"""
indictrans2_translator.py - IndicTrans2-based translation for Indic→English/non-Indic subtitles

Provides local, GPU-accelerated translation using AI4Bharat's IndicTrans2 model.
Replaces Whisper's translation with a more accurate Indic language specialist model.
Supports all 22 scheduled Indian languages translating to English or other non-Indic languages.

Based on IndicTrans2:
    "IndicTrans2: Towards High-Quality and Accessible Machine Translation Models 
    for all 22 Scheduled Indian Languages"
    
    Jay Gala, Pranjal A Chitale, A K Raghavan, Varun Gumma, Sumanth Doddapaneni,
    Aswanth Kumar M, Janki Atul Nawale, Anupama Sujatha, Ratish Puduppully,
    Vivek Raghavan, Pratyush Kumar, Mitesh M Khapra, Raj Dabre, Anoop Kunchukuttan
    
    Transactions on Machine Learning Research (2023)
    https://openreview.net/forum?id=vfT4YuzAYA
    
Model: ai4bharat/indictrans2-indic-en-1B
https://huggingface.co/ai4bharat/indictrans2-indic-en-1B
"""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import torch
import json
import srt
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

try:
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    INDICTRANS2_AVAILABLE = True
except ImportError:
    INDICTRANS2_AVAILABLE = False

# Try to import IndicTransToolkit for better preprocessing
try:
    from IndicTransToolkit.processor import IndicProcessor
    INDICTRANS_TOOLKIT_AVAILABLE = True
except ImportError:
    INDICTRANS_TOOLKIT_AVAILABLE = False


# Mapping from Whisper language codes to IndicTrans2 language codes
# All 22 scheduled Indian languages supported by IndicTrans2
WHISPER_TO_INDICTRANS2_LANG = {
    "hi": "hin_Deva",  # Hindi
    "as": "asm_Beng",  # Assamese
    "bn": "ben_Beng",  # Bengali
    "gu": "guj_Gujr",  # Gujarati
    "kn": "kan_Knda",  # Kannada
    "ml": "mal_Mlym",  # Malayalam
    "mr": "mar_Deva",  # Marathi
    "or": "ory_Orya",  # Odia
    "pa": "pan_Guru",  # Punjabi
    "ta": "tam_Taml",  # Tamil
    "te": "tel_Telu",  # Telugu
    "ur": "urd_Arab",  # Urdu
    "ne": "npi_Deva",  # Nepali
    "sd": "snd_Arab",  # Sindhi
    "si": "sin_Sinh",  # Sinhala
    "sa": "san_Deva",  # Sanskrit
    "ks": "kas_Arab",  # Kashmiri (Arabic script)
    "doi": "doi_Deva", # Dogri
    "mni": "mni_Mtei", # Manipuri (Meitei script)
    "kok": "kok_Deva", # Konkani
    "mai": "mai_Deva", # Maithili
    "sat": "sat_Olck", # Santali
}

# Non-Indic target languages that IndicTrans2 can translate to
# For indic-en model, primarily English
NON_INDIC_LANGUAGES = {
    "en": "eng_Latn",  # English
    # Add more non-Indic languages if using different IndicTrans2 models
}


def is_indic_language(lang_code: str) -> bool:
    """
    Check if a language code represents an Indic language.
    
    Args:
        lang_code: Whisper language code (e.g., 'hi', 'ta', 'bn')
        
    Returns:
        True if the language is an Indic language supported by IndicTrans2
    """
    return lang_code in WHISPER_TO_INDICTRANS2_LANG


def can_use_indictrans2(source_lang: str, target_lang: str) -> bool:
    """
    Check if IndicTrans2 should be used for translation.
    
    Args:
        source_lang: Whisper source language code
        target_lang: Whisper target language code
        
    Returns:
        True if IndicTrans2 can handle this language pair
    """
    return (
        is_indic_language(source_lang) and 
        target_lang in NON_INDIC_LANGUAGES
    )


def get_indictrans2_lang_code(whisper_lang: str, default: str = None) -> str:
    """
    Convert Whisper language code to IndicTrans2 language code.
    
    Args:
        whisper_lang: Whisper language code (e.g., 'hi', 'en')
        default: Default value if not found
        
    Returns:
        IndicTrans2 language code (e.g., 'hin_Deva', 'eng_Latn')
    """
    # Check Indic languages first
    if whisper_lang in WHISPER_TO_INDICTRANS2_LANG:
        return WHISPER_TO_INDICTRANS2_LANG[whisper_lang]
    # Check non-Indic languages
    if whisper_lang in NON_INDIC_LANGUAGES:
        return NON_INDIC_LANGUAGES[whisper_lang]
    return default


@dataclass
class TranslationConfig:
    """Configuration for IndicTrans2 translation"""
    model_name: str = "ai4bharat/indictrans2-indic-en-1B"
    src_lang: str = "hin_Deva"  # Hindi (Devanagari)
    tgt_lang: str = "eng_Latn"  # English (Latin)
    device: str = "mps"  # auto-detect: mps, cuda, or cpu
    max_new_tokens: int = 128
    num_beams: int = 4
    batch_size: int = 8  # for batch processing
    skip_english_threshold: float = 0.7  # skip if already mostly English
    use_toolkit: bool = True  # use IndicTransToolkit if available
    

class IndicTrans2Translator:
    """
    Indic to English/non-Indic translator using IndicTrans2 model.
    Supports all 22 scheduled Indian languages (Hindi, Tamil, Telugu, Bengali, etc.).
    Optimized for Apple Silicon (MPS) but works on CPU/CUDA too.
    
    Uses IndicTransToolkit for preprocessing/postprocessing if available,
    falls back to basic tokenization otherwise.
    """
    
    def __init__(
        self,
        config: Optional[TranslationConfig] = None,
        logger = None
    ):
        """
        Initialize the IndicTrans2 translator.
        
        Args:
            config: Translation configuration
            logger: Logger instance for output
        """
        if not INDICTRANS2_AVAILABLE:
            raise ImportError(
                "transformers library not available. "
                "Install with: pip install 'transformers>=4.44' sentencepiece sacremoses"
            )
        
        self.config = config or TranslationConfig()
        self.logger = logger
        self.model = None
        self.tokenizer = None
        self.processor = None
        self.device = self._select_device()
        
        # Check if toolkit should be used
        self.use_toolkit = (
            self.config.use_toolkit and 
            INDICTRANS_TOOLKIT_AVAILABLE
        )
        
    def _log(self, message: str, level: str = "info"):
        """Log message if logger available"""
        if self.logger:
            getattr(self.logger, level)(message)
        else:
            print(f"[{level.upper()}] {message}")
    
    def _select_device(self) -> str:
        """Auto-detect best available device"""
        if self.config.device == "auto":
            if torch.backends.mps.is_available() and torch.backends.mps.is_built():
                return "mps"
            elif torch.cuda.is_available():
                return "cuda"
            else:
                return "cpu"
        return self.config.device
    
    def load_model(self):
        """Load IndicTrans2 model and tokenizer"""
        if self.model is not None:
            return  # Already loaded
        
        self._log(f"Loading IndicTrans2 model: {self.config.model_name}")
        self._log(f"Using device: {self.device}")
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.config.model_name,
                trust_remote_code=True
            )
            self.model = AutoModelForSeq2SeqLM.from_pretrained(
                self.config.model_name,
                trust_remote_code=True
            )
            self.model.to(self.device)
            self.model.eval()
            
            # Initialize IndicTransToolkit processor if available
            if self.use_toolkit:
                self.processor = IndicProcessor(inference=True)
                self._log("✓ Using IndicTransToolkit for preprocessing/postprocessing")
            else:
                if self.config.use_toolkit and not INDICTRANS_TOOLKIT_AVAILABLE:
                    self._log(
                        "IndicTransToolkit not available, using basic tokenization. "
                        "Install with: pip install IndicTransToolkit",
                        level="warning"
                    )
            self.model.eval()
            
            self._log("✓ IndicTrans2 model loaded successfully")
        except Exception as e:
            error_msg = str(e)
            
            # Check for authentication/gated repo errors
            if "gated" in error_msg.lower() or "401" in error_msg or "unauthorized" in error_msg.lower():
                self._log("=" * 70, level="error")
                self._log("AUTHENTICATION ERROR: IndicTrans2 model access denied", level="error")
                self._log("=" * 70, level="error")
                self._log("", level="error")
                self._log("The IndicTrans2 model is gated and requires authentication.", level="error")
                self._log("", level="error")
                self._log("To fix this issue:", level="error")
                self._log("  1. Create HuggingFace account: https://huggingface.co/join", level="error")
                self._log("  2. Request access: https://huggingface.co/ai4bharat/indictrans2-indic-en-1B", level="error")
                self._log("     (Click 'Agree and access repository' - instant approval)", level="error")
                self._log("  3. Create access token: https://huggingface.co/settings/tokens", level="error")
                self._log("  4. Authenticate: huggingface-cli login", level="error")
                self._log("  5. Re-run the pipeline", level="error")
                self._log("", level="error")
                self._log("Pipeline will fall back to Whisper translation for now.", level="warning")
                self._log("=" * 70, level="error")
                raise RuntimeError("IndicTrans2 authentication required") from e
            else:
                self._log(f"Failed to load IndicTrans2 model: {e}", level="error")
                raise
    
    def _is_mostly_english(self, text: str) -> bool:
        """
        Check if text is already mostly English (for Hinglish detection).
        Returns True if text is >= threshold ASCII characters.
        """
        if not text.strip():
            return True
        
        ascii_chars = sum(c.isascii() for c in text)
        ratio = ascii_chars / max(len(text), 1)
        return ratio >= self.config.skip_english_threshold
    
    def translate_text(self, text: str, skip_english: bool = True) -> str:
        """
        Translate a single text string from source Indic language to target language.
        
        Args:
            text: Source text to translate (in Indic language)
            skip_english: If True, skip translation for mostly-English text (for Hinglish)
            
        Returns:
            Translated text in target language
        """
        if not self.model:
            self.load_model()
        
        text = text.strip()
        if not text:
            return text
        
        # Skip translation if already mostly English (Hinglish handling)
        if skip_english and self._is_mostly_english(text):
            return text
        
        try:
            # Preprocess with IndicTransToolkit if available
            if self.use_toolkit and self.processor:
                batch = self.processor.preprocess_batch(
                    [text],
                    src_lang=self.config.src_lang,
                    tgt_lang=self.config.tgt_lang,
                )
                input_text = batch[0]
            else:
                # Fallback: Basic prompt format
                input_text = f"<2{self.config.tgt_lang}> {text}"
            
            # Tokenize
            encoded = self.tokenizer(
                input_text,
                truncation=True,
                padding=True,
                return_tensors="pt",
            )
            encoded = {k: v.to(self.device) for k, v in encoded.items()}
            
            # Generate translation
            with torch.no_grad():
                output = self.model.generate(
                    **encoded,
                    max_new_tokens=self.config.max_new_tokens,
                    num_beams=self.config.num_beams,
                    use_cache=True,
                )
            
            # Decode
            translation = self.tokenizer.batch_decode(
                output,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=True,
            )[0]
            
            # Postprocess with IndicTransToolkit if available
            if self.use_toolkit and self.processor:
                translations = self.processor.postprocess_batch(
                    [translation],
                    lang=self.config.tgt_lang
                )
                translation = translations[0]
            
            return translation.strip()
            
        except Exception as e:
            self._log(f"Translation failed for text: {text[:50]}... Error: {e}", level="warning")
            return text  # Return original on error
    
    def translate_segments(
        self,
        segments: List[Dict[str, Any]],
        skip_english: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Translate WhisperX segments from source Indic language to target language.
        Preserves all timing information and metadata.
        
        Args:
            segments: List of WhisperX segment dictionaries
            skip_english: If True, skip mostly-English segments (for Hinglish)
            
        Returns:
            List of translated segments with same structure
        """
        if not self.model:
            self.load_model()
        
        self._log(f"Translating {len(segments)} segments...")
        translated_segments = []
        
        for i, segment in enumerate(segments):
            # Create a copy of the segment
            translated_seg = segment.copy()
            
            # Translate the main text
            original_text = segment.get('text', '')
            translated_text = self.translate_text(original_text, skip_english=skip_english)
            translated_seg['text'] = translated_text
            
            # Translate word-level data if present
            if 'words' in segment and isinstance(segment['words'], list):
                translated_words = []
                for word_data in segment['words']:
                    word_copy = word_data.copy()
                    if 'word' in word_data:
                        word_copy['word'] = self.translate_text(
                            word_data['word'],
                            skip_english=skip_english
                        )
                    translated_words.append(word_copy)
                translated_seg['words'] = translated_words
            
            translated_segments.append(translated_seg)
            
            # Progress logging
            if (i + 1) % 50 == 0 or (i + 1) == len(segments):
                self._log(f"  Translated {i + 1}/{len(segments)} segments...")
        
        self._log("✓ Translation complete")
        return translated_segments
    
    def translate_srt_file(
        self,
        input_srt: Path,
        output_srt: Path,
        skip_english: bool = True
    ) -> int:
        """
        Translate an SRT file from Hindi to English.
        Preserves all timestamps and formatting.
        
        Args:
            input_srt: Path to input Hindi SRT file
            output_srt: Path to output English SRT file
            skip_english: If True, skip mostly-English lines
            
        Returns:
            Number of subtitles translated
        """
        if not self.model:
            self.load_model()
        
        self._log(f"Reading SRT: {input_srt}")
        
        with open(input_srt, "r", encoding="utf-8") as f:
            subtitles = list(srt.parse(f.read()))
        
        self._log(f"Total subtitles found: {len(subtitles)}")
        
        for i, sub in enumerate(subtitles):
            original = sub.content
            
            # Preserve multi-line structure within subtitle blocks
            lines = original.split("\n")
            translated_lines = []
            
            for line in lines:
                if line.strip():
                    translated_lines.append(
                        self.translate_text(line, skip_english=skip_english)
                    )
                else:
                    # Preserve empty lines
                    translated_lines.append("")
            
            sub.content = "\n".join(translated_lines)
            
            # Progress logging
            if (i + 1) % 50 == 0 or (i + 1) == len(subtitles):
                self._log(f"  Translated {i + 1}/{len(subtitles)} subtitles...")
        
        self._log(f"Writing translated SRT to: {output_srt}")
        output_srt.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_srt, "w", encoding="utf-8") as f:
            f.write(srt.compose(subtitles))
        
        self._log("✓ SRT translation complete")
        return len(subtitles)
    
    def cleanup(self):
        """Clean up model resources"""
        if self.model is not None:
            del self.model
            del self.tokenizer
            self.model = None
            self.tokenizer = None
            
            if self.device == "mps":
                torch.mps.empty_cache()
            elif self.device == "cuda":
                torch.cuda.empty_cache()
            
            self._log("Model resources cleaned up")


def translate_whisperx_result(
    source_result: Dict[str, Any],
    source_lang: str = "hi",
    target_lang: str = "en",
    logger = None
) -> Dict[str, Any]:
    """
    Translate WhisperX result from Indic language to English/non-Indic using IndicTrans2.
    
    Supports all 22 scheduled Indian languages (Hindi, Tamil, Telugu, Bengali, etc.)
    translating to English or other non-Indic languages.
    
    Args:
        source_result: WhisperX result dictionary with 'segments' key
        source_lang: Source language code (Whisper code, e.g., 'hi', 'ta', 'bn')
        target_lang: Target language code (Whisper code, e.g., 'en')
        logger: Logger instance
        
    Returns:
        Translated result dictionary with same structure
    """
    # Check if this language pair is supported
    if not can_use_indictrans2(source_lang, target_lang):
        if logger:
            logger.warning(
                f"IndicTrans2 does not support {source_lang}→{target_lang}. "
                f"Supported: Any Indic language → English/non-Indic"
            )
        return source_result
    
    # Get IndicTrans2 language codes
    src_lang_code = get_indictrans2_lang_code(source_lang)
    tgt_lang_code = get_indictrans2_lang_code(target_lang)
    
    if not src_lang_code or not tgt_lang_code:
        if logger:
            logger.warning(
                f"Could not map language codes: {source_lang}→{target_lang}"
            )
        return source_result
    
    # Create translator with appropriate language codes
    config = TranslationConfig(
        device="auto",
        src_lang=src_lang_code,
        tgt_lang=tgt_lang_code
    )
    translator = IndicTrans2Translator(config=config, logger=logger)
    
    try:
        # Translate segments
        if 'segments' in source_result:
            translated_segments = translator.translate_segments(
                source_result['segments'],
                skip_english=True
            )
            
            # Create translated result
            target_result = source_result.copy()
            target_result['segments'] = translated_segments
            target_result['language'] = target_lang
            
            return target_result
        else:
            if logger:
                logger.warning("No segments found in source result")
            return source_result
    
    except RuntimeError as e:
        # Check for authentication errors
        if "authentication required" in str(e).lower():
            if logger:
                logger.error("=" * 70)
                logger.error("IndicTrans2 authentication required - falling back to Whisper")
                logger.error("=" * 70)
                logger.warning("Translation will continue using Whisper (slower)")
            return source_result
        else:
            raise
    
    except Exception as e:
        if logger:
            logger.error(f"IndicTrans2 translation failed: {e}")
            logger.warning("Falling back to returning source result")
        return source_result
            
    finally:
        translator.cleanup()


# CLI interface for standalone testing
def main():
    """CLI entry point for testing IndicTrans2 translation"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Translate Indic language SRT to English using IndicTrans2"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Input Indic language SRT file (Hindi, Tamil, Telugu, Bengali, etc.)"
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output English SRT file"
    )
    parser.add_argument(
        "--no-skip-english",
        action="store_true",
        help="Translate all text, even if mostly English"
    )
    parser.add_argument(
        "--device",
        default="auto",
        choices=["auto", "mps", "cuda", "cpu"],
        help="Device to use for translation"
    )
    parser.add_argument(
        "--num-beams",
        type=int,
        default=4,
        help="Number of beams for beam search (higher = better quality, slower)"
    )
    
    args = parser.parse_args()
    
    # Create configuration
    config = TranslationConfig(
        device=args.device,
        num_beams=args.num_beams,
    )
    
    # Create translator
    translator = IndicTrans2Translator(config=config)
    
    try:
        # Translate file
        num_translated = translator.translate_srt_file(
            input_srt=Path(args.input),
            output_srt=Path(args.output),
            skip_english=not args.no_skip_english
        )
        
        print(f"\n✓ Successfully translated {num_translated} subtitles")
        print(f"  Output: {args.output}")
        return 0
        
    except Exception as e:
        print(f"\n✗ Translation failed: {e}")
        return 1
    finally:
        translator.cleanup()


if __name__ == "__main__":
    import sys
    sys.exit(main())
