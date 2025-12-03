"""
nllb_translator.py - NLLB-based translation for non-Indic languages

Provides translation for 200+ languages using Meta's NLLB (No Language Left Behind) model.
Use for non-Indic languages like Spanish, Arabic, French, German, etc.

Model: facebook/nllb-200-distilled-600M (or 1.3B/3.3B for better quality)
https://huggingface.co/facebook/nllb-200-distilled-600M
"""

# Standard library
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

# Third-party
import torch

# Local
from shared.logger import get_logger
logger = get_logger(__name__)

try:
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
    NLLB_AVAILABLE = True
except ImportError:
    NLLB_AVAILABLE = False


# Mapping from Whisper language codes to NLLB language codes
# NLLB uses FLORES-200 codes (3-letter codes + script)
WHISPER_TO_NLLB_LANG = {
    # Major European languages
    "en": "eng_Latn",  # English
    "es": "spa_Latn",  # Spanish
    "fr": "fra_Latn",  # French
    "de": "deu_Latn",  # German
    "it": "ita_Latn",  # Italian
    "pt": "por_Latn",  # Portuguese
    "nl": "nld_Latn",  # Dutch
    "pl": "pol_Latn",  # Polish
    "ru": "rus_Cyrl",  # Russian
    "uk": "ukr_Cyrl",  # Ukrainian
    "cs": "ces_Latn",  # Czech
    "ro": "ron_Latn",  # Romanian
    "sv": "swe_Latn",  # Swedish
    "no": "nob_Latn",  # Norwegian
    "da": "dan_Latn",  # Danish
    "fi": "fin_Latn",  # Finnish
    "hu": "hun_Latn",  # Hungarian
    "el": "ell_Grek",  # Greek
    "tr": "tur_Latn",  # Turkish
    
    # Asian languages (non-Indic)
    "zh": "zho_Hans",  # Chinese (Simplified)
    "ja": "jpn_Jpan",  # Japanese
    "ko": "kor_Hang",  # Korean
    "th": "tha_Thai",  # Thai
    "vi": "vie_Latn",  # Vietnamese
    "id": "ind_Latn",  # Indonesian
    "ms": "zsm_Latn",  # Malay
    "tl": "tgl_Latn",  # Tagalog
    
    # Middle Eastern & African languages
    "ar": "arb_Arab",  # Arabic
    "he": "heb_Hebr",  # Hebrew
    "fa": "pes_Arab",  # Persian/Farsi
    "sw": "swh_Latn",  # Swahili
    "am": "amh_Ethi",  # Amharic
    "so": "som_Latn",  # Somali
    
    # Indic languages (fallback - prefer IndicTrans2)
    "hi": "hin_Deva",  # Hindi
    "bn": "ben_Beng",  # Bengali
    "ta": "tam_Taml",  # Tamil
    "te": "tel_Telu",  # Telugu
    "mr": "mar_Deva",  # Marathi
    "gu": "guj_Gujr",  # Gujarati
    "kn": "kan_Knda",  # Kannada
    "ml": "mal_Mlym",  # Malayalam
    "pa": "pan_Guru",  # Punjabi
    "ur": "urd_Arab",  # Urdu
}


def is_nllb_supported(lang_code: str) -> bool:
    """Check if a language code is supported by NLLB"""
    return lang_code in WHISPER_TO_NLLB_LANG


def get_nllb_lang_code(whisper_lang: str) -> Optional[str]:
    """Convert Whisper language code to NLLB language code"""
    return WHISPER_TO_NLLB_LANG.get(whisper_lang)


@dataclass
class NLLBConfig:
    """Configuration for NLLB translation"""
    model_name: str = "facebook/nllb-200-distilled-600M"  # Fast, good quality
    # Alternatives:
    # "facebook/nllb-200-1.3B" - Better quality, slower
    # "facebook/nllb-200-3.3B" - Best quality, much slower
    src_lang: str = "hin_Deva"
    tgt_lang: str = "eng_Latn"
    device: str = "mps"  # auto-detect: mps, cuda, or cpu
    max_length: int = 512
    batch_size: int = 8
    num_beams: int = 4


class NLLBTranslator:
    """
    Non-Indic language translator using Meta's NLLB model.
    
    Supports 200+ languages for high-quality translation.
    Optimized for Apple Silicon (MPS) but works on CPU/CUDA too.
    """
    
    def __init__(
        self,
        config: Optional[NLLBConfig] = None,
        logger: logging.Logger = None,
        source_lang: Optional[str] = None,
        target_lang: Optional[str] = None
    ):
        """
        Initialize NLLB translator.
        
        Args:
            config: NLLBConfig instance (optional)
            logger: Logger instance
            source_lang: Whisper source language code
            target_lang: Whisper target language code
        """
        if not NLLB_AVAILABLE:
            raise ImportError(
                "NLLB dependencies not installed. "
                "Please run: ./bootstrap.sh to install venv/nllb environment"
            )
        
        self.logger = logger
        self.config = config or NLLBConfig()
        
        # Override config with provided languages
        if source_lang:
            self.config.src_lang = get_nllb_lang_code(source_lang) or self.config.src_lang
        if target_lang:
            self.config.tgt_lang = get_nllb_lang_code(target_lang) or self.config.tgt_lang
        
        # Detect device
        if self.config.device == "mps" and not torch.backends.mps.is_available():
            self.config.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        if self.logger:
            self.logger.info(f"Loading NLLB model: {self.config.model_name}")
            self.logger.info(f"Device: {self.config.device}")
            self.logger.info(f"Translation: {source_lang} ({self.config.src_lang}) → {target_lang} ({self.config.tgt_lang})")
        
        # Load model and tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.config.model_name,
            src_lang=self.config.src_lang
        )
        
        self.model = AutoModelForSeq2SeqLM.from_pretrained(
            self.config.model_name
        ).to(self.config.device)
        
        self.model.eval()  # Set to evaluation mode
        
        if self.logger:
            self.logger.info("NLLB model loaded successfully")
    
    def translate_text(self, text: str) -> str:
        """
        Translate a single text string.
        
        Args:
            text: Input text to translate
            
        Returns:
            Translated text
        """
        if not text or not text.strip():
            return text
        
        # Tokenize
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=self.config.max_length
        ).to(self.config.device)
        
        # Generate translation
        with torch.no_grad():
            translated_tokens = self.model.generate(
                **inputs,
                forced_bos_token_id=self.tokenizer.convert_tokens_to_ids(self.config.tgt_lang),
                max_length=self.config.max_length,
                num_beams=self.config.num_beams,
                early_stopping=True
            )
        
        # Decode
        translated_text = self.tokenizer.batch_decode(
            translated_tokens,
            skip_special_tokens=True
        )[0]
        
        return translated_text
    
    def translate_batch(self, texts: List[str]) -> List[str]:
        """
        Translate a batch of texts.
        
        Args:
            texts: List of input texts
            
        Returns:
            List of translated texts
        """
        if not texts:
            return []
        
        # Filter empty texts
        non_empty_indices = [i for i, t in enumerate(texts) if t and t.strip()]
        non_empty_texts = [texts[i] for i in non_empty_indices]
        
        if not non_empty_texts:
            return texts
        
        # Tokenize batch
        inputs = self.tokenizer(
            non_empty_texts,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=self.config.max_length
        ).to(self.config.device)
        
        # Generate translations
        with torch.no_grad():
            translated_tokens = self.model.generate(
                **inputs,
                forced_bos_token_id=self.tokenizer.convert_tokens_to_ids(self.config.tgt_lang),
                max_length=self.config.max_length,
                num_beams=self.config.num_beams,
                early_stopping=True
            )
        
        # Decode
        translated_texts = self.tokenizer.batch_decode(
            translated_tokens,
            skip_special_tokens=True
        )
        
        # Reconstruct full list with empty texts in original positions
        result = texts.copy()
        for i, idx in enumerate(non_empty_indices):
            result[idx] = translated_texts[i]
        
        return result
    
    def translate_segments(self, segments: List[Dict]) -> List[Dict]:
        """
        Translate segments from WhisperX output.
        
        Args:
            segments: List of segment dictionaries with 'text' field
            
        Returns:
            List of translated segments
        """
        if not segments:
            return []
        
        # Extract texts
        texts = [seg.get('text', '') for seg in segments]
        
        # Translate in batches
        translated_texts = []
        for i in range(0, len(texts), self.config.batch_size):
            batch = texts[i:i + self.config.batch_size]
            translated_batch = self.translate_batch(batch)
            translated_texts.extend(translated_batch)
            
            if self.logger:
                progress = min(i + self.config.batch_size, len(texts))
                self.logger.info(f"Translated {progress}/{len(texts)} segments")
        
        # Create translated segments
        translated_segments = []
        for seg, translated_text in zip(segments, translated_texts):
            translated_seg = seg.copy()
            translated_seg['text'] = translated_text
            translated_segments.append(translated_seg)
        
        return translated_segments


def translate_whisperx_result(
    whisperx_result: Dict,
    source_lang: str,
    target_lang: str,
    logger: logging.Logger = None,
    config: Optional[NLLBConfig] = None
) -> Dict:
    """
    Translate WhisperX transcription result using NLLB.
    
    Args:
        whisperx_result: WhisperX output with 'segments' list
        source_lang: Whisper source language code
        target_lang: Whisper target language code
        logger: Logger instance
        config: NLLBConfig instance (optional)
        
    Returns:
        Translated WhisperX result
    """
    if not is_nllb_supported(target_lang):
        if logger:
            logger.error(f"Target language '{target_lang}' not supported by NLLB")
        raise ValueError(f"Unsupported target language: {target_lang}")
    
    # Initialize translator
    translator = NLLBTranslator(
        config=config,
        logger: logging.Logger=logger,
        source_lang=source_lang,
        target_lang=target_lang
    )
    
    # Get segments
    segments = whisperx_result.get('segments', [])
    
    if logger:
        logger.info(f"Translating {len(segments)} segments...")
    
    # Translate segments
    translated_segments = translator.translate_segments(segments)
    
    # Create result
    result = whisperx_result.copy()
    result['segments'] = translated_segments
    result['language'] = target_lang  # Update language field
    
    if logger:
        logger.info("Translation completed")
    
    return result
