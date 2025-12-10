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

# Standard library
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import sys
import logging
from pathlib import Path

# Ensure toolkit is importable
toolkit_path = Path(__file__).parent.parent / "venv/indictrans2" / "lib"
python_version = f"python{sys.version_info.major}.{sys.version_info.minor}"
site_packages = toolkit_path / python_version / "site-packages"
if site_packages.exists():
    sys.path.insert(0, str(site_packages))

import torch
import json
import srt
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

# Local
from shared.logger import get_logger
logger = get_logger(__name__)

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
    
    Supports two modes:
    1. Indic → English/non-Indic (using indictrans2-indic-en-1B model)
    2. Indic → Indic (using indictrans2-indic-indic-1B model)
    
    Args:
        source_lang: Whisper source language code
        target_lang: Whisper target language code
        
    Returns:
        True if IndicTrans2 can handle this language pair
    """
    # Indic → English/non-Indic
    if is_indic_language(source_lang) and target_lang in NON_INDIC_LANGUAGES:
        return True
    
    # Indic → Indic  
    if is_indic_language(source_lang) and is_indic_language(target_lang):
        return True
    
    return False


def get_indictrans2_model_name(source_lang: str, target_lang: str) -> str:
    """
    Get the appropriate IndicTrans2 model based on language pair.
    
    Args:
        source_lang: Whisper source language code
        target_lang: Whisper target language code
        
    Returns:
        Model name for HuggingFace
    """
    if is_indic_language(source_lang):
        if target_lang in NON_INDIC_LANGUAGES:
            # Indic → English/non-Indic
            return "ai4bharat/indictrans2-indic-en-1B"
        elif is_indic_language(target_lang):
            # Indic → Indic
            return "ai4bharat/indictrans2-indic-indic-1B"
    
    # Fallback to indic-en model
    return "ai4bharat/indictrans2-indic-en-1B"


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
    Indic language translator using IndicTrans2 models.
    
    Supports two translation modes:
    1. Indic → English/non-Indic (using indictrans2-indic-en-1B)
    2. Indic → Indic (using indictrans2-indic-indic-1B)
    
    Supports all 22 scheduled Indian languages (Hindi, Tamil, Telugu, Bengali, etc.).
    Optimized for Apple Silicon (MPS) but works on CPU/CUDA too.
    
    Uses IndicTransToolkit for preprocessing/postprocessing if available,
    falls back to basic tokenization otherwise.
    """
    
    def __init__(
        self,
        config: Optional[TranslationConfig] = None,
        logger: logging.Logger = None,
        source_lang: Optional[str] = None,
        target_lang: Optional[str] = None
    ):
        """
        Initialize the IndicTrans2 translator.
        
        Args:
            config: Translation configuration
            logger: Logger instance for output
            source_lang: Source language code (Whisper format) - auto-selects model
            target_lang: Target language code (Whisper format) - auto-selects model
        """
        if not INDICTRANS2_AVAILABLE:
            raise ImportError(
                "transformers library not available. "
                "Install with: pip install 'transformers>=4.44' sentencepiece sacremoses"
            )
        
        self.config = config or TranslationConfig()
        self.logger = logger
        
        # Auto-select model based on language pair
        if source_lang and target_lang:
            model_name = get_indictrans2_model_name(source_lang, target_lang)
            if model_name != self.config.model_name:
                self._log(f"Auto-selecting model: {model_name}", level="info")
                self.config.model_name = model_name
        
        self.model = None
        self.tokenizer = None
        self.processor = None
        self.device = self._select_device()
        
        # Check if toolkit should be used
        self.use_toolkit = (
            self.config.use_toolkit and 
            INDICTRANS_TOOLKIT_AVAILABLE
        )
        
    def _log(self, message: str, level: str = "info") -> None:
        """Log message if logger available"""
        if self.logger:
            getattr(self.logger, level)(message)
        else:
            logger.info(f"[{level.upper()}] {message}")
    
    def _get_hf_token(self) -> Optional[str]:
        """
        Get HuggingFace token from user profile.
        
        Checks user profile first, then falls back to multiple sources:
        1. User profile (userId from job.json)
        2. Environment variable HF_TOKEN
        3. ~/.cache/huggingface/token (huggingface-cli login location)
        
        Returns:
            HuggingFace token or None if not found
        """
        # 1. Try to get from user profile
        try:
            from shared.user_profile import UserProfile
            
            # Get userId from job.json
            user_id = 1  # Default
            job_json = Path(os.environ.get('JOB_DIR', '.')) / 'job.json'
            if job_json.exists():
                try:
                    with open(job_json) as f:
                        job_data = json.load(f)
                        user_id = job_data.get('userId', 1)
                except Exception:
                    pass
            
            # Load profile and get token
            profile = UserProfile.load(user_id)
            token = profile.get_credential('huggingface', 'token')
            if token:
                self._log(f"✓ HuggingFace token loaded from user profile (userId={user_id})")
                return token
        except Exception as e:
            self._log(f"Could not load from user profile: {e}", level="debug")
        
        # 2. Check environment variable
        token = os.environ.get('HF_TOKEN')
        if token:
            self._log("✓ HuggingFace token loaded from environment")
            return token
        
        # 3. Check huggingface-cli token location
        try:
            hf_token_file = Path.home() / '.cache' / 'huggingface' / 'token'
            if hf_token_file.exists():
                with open(hf_token_file, 'r') as f:
                    token = f.read().strip()
                    if token:
                        self._log("✓ HuggingFace token loaded from cache")
                        return token
        except Exception as e:
            self._log(f"Could not load HF token from cache: {e}", level="debug")
        
        return None
    
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
    
    def load_model(self) -> Any:
        """Load IndicTrans2 model and tokenizer"""
        if self.model is not None:
            return  # Already loaded
        
        self._log(f"Loading IndicTrans2 model: {self.config.model_name}")
        self._log(f"Using device: {self.device}")
        
        # Load HuggingFace token from secrets.json or environment
        hf_token = self._get_hf_token()
        if hf_token:
            self._log("✓ HuggingFace token found")
        else:
            self._log("⚠ No HuggingFace token found - may fail for gated models", level="warning")
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.config.model_name,
                trust_remote_code=True,
                token=hf_token
            )
            self.model = AutoModelForSeq2SeqLM.from_pretrained(
                self.config.model_name,
                trust_remote_code=True,
                token=hf_token
            )
            self.model.to(self.device)
            self.model.eval()
            
            # MPS cache workaround
            if self.device == "mps":
                self._log("⚠ Note: Disabling cache on MPS to avoid generation errors (slight performance impact)")
            
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
                
                # Determine which model URL to show based on what's being loaded
                if "indic-indic" in self.config.model_name:
                    model_url = "https://huggingface.co/ai4bharat/indictrans2-indic-indic-1B"
                else:
                    model_url = "https://huggingface.co/ai4bharat/indictrans2-indic-en-1B"
                
                self._log(f"  2. Request access: {model_url}", level="error")
                self._log("     (Click 'Agree and access repository' - instant approval)", level="error")
                self._log("  3. Create access token: https://huggingface.co/settings/tokens", level="error")
                self._log("  4. Add token to config/secrets.json:", level="error")
                self._log('     {"hf_token": "hf_..."} ', level="error")
                self._log("     OR run: huggingface-cli login", level="error")
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
        
        # Skip only empty or single-character punctuation
        # Note: Many meaningful Hindi words are 2-3 characters (आओ, जा, etc.)
        if len(text) == 1 and not text.isalnum():
            return text
        
        # Skip translation if already mostly English (Hinglish handling)
        if skip_english and self._is_mostly_english(text):
            return text
        
        try:
            # Preprocess with IndicTransToolkit if available
            input_text = None
            use_toolkit_for_this = self.use_toolkit and self.processor
            
            if use_toolkit_for_this:
                try:
                    batch = self.processor.preprocess_batch(
                        [text],
                        src_lang=self.config.src_lang,
                        tgt_lang=self.config.tgt_lang,
                    )
                    # More robust validation of preprocessing output
                    if batch and len(batch) > 0 and batch[0] is not None and str(batch[0]).strip():
                        input_text = batch[0]
                    else:
                        input_text = None
                except Exception as e:
                    self._log(f"Preprocessing error for text: '{text[:50]}...' Error: {e}", level="warning")
                    input_text = None
                    use_toolkit_for_this = False  # Disable toolkit for this segment
                
                # Fallback if preprocessing returns None or fails
                if input_text is None or not str(input_text).strip():
                    self._log(f"Preprocessing returned empty/None for text: '{text[:50]}...', using basic format", level="debug")
                    use_toolkit_for_this = False  # Disable toolkit
                    input_text = None
            
            # Use basic format if toolkit failed or not available
            if not use_toolkit_for_this or input_text is None:
                # IndicTrans2 expects: "src_lang tgt_lang text" format
                input_text = f"{self.config.src_lang} {self.config.tgt_lang} {text}"
            
            # Final validation - ensure input_text is never None or empty
            if not input_text or not str(input_text).strip():
                self._log(f"Input text is empty after preprocessing/fallback for: '{text[:50]}...', skipping", level="warning")
                return text
            
            # Tokenize
            try:
                encoded = self.tokenizer(
                    input_text,
                    truncation=True,
                    padding=True,
                    return_tensors="pt",
                )
            except Exception as e:
                self._log(f"Tokenization exception for text: '{text[:50]}...' Error: {e}", level="warning")
                return text
            
            # Validate encoded tensors
            if not encoded or 'input_ids' not in encoded or encoded['input_ids'] is None:
                self._log(f"Tokenization failed (no input_ids) for text: '{text[:50]}...'", level="warning")
                return text
            
            # Check for empty input_ids
            if encoded['input_ids'].numel() == 0:
                self._log(f"Tokenization produced empty input_ids for text: '{text[:50]}...'", level="warning")
                return text
            
            # Move tensors to device, filtering out None values
            try:
                encoded = {k: v.to(self.device) if v is not None else None for k, v in encoded.items()}
                # Remove None values after moving
                encoded = {k: v for k, v in encoded.items() if v is not None}
            except Exception as e:
                self._log(f"Failed to move tensors to device for text: '{text[:50]}...' Error: {e}", level="warning")
                return text
            
            # Final validation before generation
            if not encoded or 'input_ids' not in encoded or encoded['input_ids'] is None:
                self._log(f"Encoded missing valid input_ids after device transfer for text: '{text[:50]}...'", level="warning")
                return text
            
            # Validate tensor shapes
            try:
                if not hasattr(encoded['input_ids'], 'shape') or encoded['input_ids'].shape[0] == 0:
                    self._log(f"Input_ids has invalid shape for text: '{text[:50]}...'", level="warning")
                    return text
            except Exception as e:
                self._log(f"Shape validation failed for text: '{text[:50]}...' Error: {e}", level="warning")
                return text
            
            # Generate translation
            # NOTE: use_cache=True is broken on MPS for IndicTrans2, causing 'NoneType' errors
            # We disable cache to fix this issue (slightly slower but works correctly)
            use_cache_param = False if self.device == "mps" else True
            
            try:
                # Debug: Log encoded keys and their shapes
                if self.logger and hasattr(self.logger, 'debug'):
                    for key, tensor in encoded.items():
                        if tensor is not None and hasattr(tensor, 'shape'):
                            self.logger.debug(f"  encoded['{key}'].shape = {tensor.shape}")
                        else:
                            self.logger.debug(f"  encoded['{key}'] = {tensor}")
                
                with torch.no_grad():
                    output = self.model.generate(
                        **encoded,
                        max_new_tokens=self.config.max_new_tokens,
                        num_beams=self.config.num_beams,
                        use_cache=use_cache_param,  # Disable cache on MPS to avoid NoneType errors
                    )
                
                # Validate output
                if output is None or not hasattr(output, 'shape') or output.shape[0] == 0:
                    self._log(f"Model generated invalid output for text: '{text[:50]}...'", level="warning")
                    return text
                    
            except AttributeError as e:
                # Specific handling for 'NoneType' object has no attribute 'shape' error
                if "'NoneType' object has no attribute 'shape'" in str(e):
                    self._log(f"Model generation failed (None tensor) for text: '{text[:50]}...'", level="warning")
                    # Debug: Print what we're passing to generate
                    self._log(f"  Encoded keys: {list(encoded.keys())}", level="debug")
                    for key, tensor in encoded.items():
                        if tensor is None:
                            self._log(f"  encoded['{key}'] = None (THIS IS THE PROBLEM!)", level="warning")
                        elif hasattr(tensor, 'shape'):
                            self._log(f"  encoded['{key}'].shape = {tensor.shape}", level="debug")
                    return text
                else:
                    self._log(f"Model generation failed for text: '{text[:50]}...' Error: {e}", level="warning")
                    return text
            except Exception as e:
                self._log(f"Model generation failed for text: '{text[:50]}...' Error: {e}", level="warning")
                return text
            
            # Decode
            try:
                translation = self.tokenizer.batch_decode(
                    output,
                    skip_special_tokens=True,
                    clean_up_tokenization_spaces=True,
                )[0]
            except Exception as e:
                self._log(f"Decoding failed for text: '{text[:50]}...' Error: {e}", level="warning")
                return text
            
            # Validate decoded output
            if not translation or not translation.strip():
                self._log(f"Decoded translation is empty for text: '{text[:50]}...'", level="warning")
                return text
            
            # Postprocess with IndicTransToolkit only if we used it for preprocessing
            if use_toolkit_for_this and self.processor:
                try:
                    translations = self.processor.postprocess_batch(
                        [translation],
                        lang=self.config.tgt_lang
                    )
                    if translations and len(translations) > 0 and translations[0]:
                        translation = translations[0]
                except Exception as e:
                    self._log(f"Postprocessing error, using raw translation: {e}", level="debug")
                    # Keep the raw translation
            
            return translation.strip()
            
        except Exception as e:
            self._log(f"Translation failed for text: '{text[:50]}...' Error: {e}", level="warning")
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
    
    def cleanup(self) -> None:
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
    logger: logging.Logger = None
) -> Dict[str, Any]:
    """
    Translate WhisperX result using IndicTrans2.
    
    Supports:
    - Indic → English (direct, single-step using indictrans2-indic-en-1B)
    - Indic → Indic (direct, single-step using indictrans2-indic-indic-1B)
    - Indic → non-Indic (direct, single-step)
    
    Args:
        source_result: WhisperX result dictionary with 'segments' key
        source_lang: Source language code (Whisper code, e.g., 'hi', 'ta', 'bn')
        target_lang: Target language code (Whisper code, e.g., 'en', 'gu')
        logger: Logger instance
        
    Returns:
        Translated result dictionary with same structure
    """
    # Check if IndicTrans2 can handle this language pair
    if not can_use_indictrans2(source_lang, target_lang):
        if logger:
            logger.warning(
                f"IndicTrans2 does not support {source_lang}→{target_lang}. "
                f"Supported: Any Indic language → English/non-Indic, or Indic → Indic"
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
    
    # Determine the correct model based on language pair
    model_name = get_indictrans2_model_name(source_lang, target_lang)
    
    if logger:
        logger.info(f"Using model: {model_name}")
        logger.info(f"Translation: {source_lang} ({src_lang_code}) → {target_lang} ({tgt_lang_code})")
    
    # Create translator with appropriate model and language codes
    config = TranslationConfig(
        model_name=model_name,
        device="auto",
        src_lang=src_lang_code,
        tgt_lang=tgt_lang_code
    )
    translator = IndicTrans2Translator(
        config=config,
        logger=logger,
        source_lang=source_lang,
        target_lang=target_lang
    )
    
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
                logger.error("=" * 70, exc_info=True)
                logger.error("IndicTrans2 authentication required - falling back to source", exc_info=True)
                logger.error("=" * 70, exc_info=True)
                logger.error("Please authenticate with HuggingFace:", exc_info=True)
                logger.error(f"  1. Visit: https://huggingface.co/{model_name}", exc_info=True)
                logger.error("  2. Request access to the model", exc_info=True)
                logger.error("  3. Run: huggingface-cli login")
            return source_result
        else:
            raise
    
    except Exception as e:
        if logger:
            logger.error(f"IndicTrans2 translation failed: {e}", exc_info=True)
            logger.warning("Falling back to returning source result")
        return source_result
            
    finally:
        translator.cleanup()


# CLI interface for standalone testing

def run_stage(job_dir: Path, stage_name: str = "08_translation") -> int:
    """
    IndicTrans2 Translation Stage - run_stage() wrapper
    
    Provides StageIO interface for IndicTrans2 translation.
    
    Args:
        job_dir: Job directory path
        stage_name: Stage name for logging/manifest
        
    Returns:
        0 on success, 1 on failure
    """
    # Import here to avoid circular dependencies
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from shared.stage_utils import StageIO
    from shared.config_loader import load_config
    
    io = StageIO(stage_name, job_dir, enable_manifest=True)
    logger_stage = io.get_stage_logger()
    
    try:
        logger_stage.info("=" * 80)
        logger_stage.info("STAGE: IndicTrans2 Translation")
        logger_stage.info("=" * 80)
        
        # Check if translation is enabled
        config = load_config()
        translation_enabled = config.get("STAGE_08_TRANSLATION_ENABLED", "true").lower() == "true"
        translation_model = config.get("TRANSLATION_MODEL", "indictrans2")
        source_language = config.get("SOURCE_LANGUAGE", "hi")
        target_langs = config.get("TARGET_LANGUAGE", "en").split(",")
        device = config.get("TRANSLATION_DEVICE", "auto")
        num_beams = int(config.get("TRANSLATION_NUM_BEAMS", "4"))
        workflow = config.get("WORKFLOW", "transcribe")
        
        # Override with job.json parameters (AD-006)
        job_json_path = job_dir / "job.json"
        if job_json_path.exists():
            logger_stage.info("Reading job-specific parameters from job.json...")
            try:
                with open(job_json_path) as f:
                    job_data = json.load(f)
                    
                    # Override source_language
                    if 'source_language' in job_data and job_data['source_language']:
                        old_source = source_language
                        source_language = job_data['source_language']
                        logger_stage.info(f"  source_language override: {old_source} → {source_language} (from job.json)")
                    
                    # Override target_languages
                    if 'target_languages' in job_data and job_data['target_languages']:
                        old_targets = target_langs
                        target_langs = job_data['target_languages'] if isinstance(job_data['target_languages'], list) else job_data['target_languages'].split(',')
                        logger_stage.info(f"  target_languages override: {old_targets} → {target_langs} (from job.json)")
                    
                    # Override translation parameters
                    if 'translation' in job_data:
                        trans_config = job_data['translation']
                        if 'model' in trans_config and trans_config['model']:
                            old_model = translation_model
                            translation_model = trans_config['model']
                            logger_stage.info(f"  translation.model override: {old_model} → {translation_model} (from job.json)")
                        if 'device' in trans_config and trans_config['device']:
                            old_device = device
                            device = trans_config['device']
                            logger_stage.info(f"  translation.device override: {old_device} → {device} (from job.json)")
                        if 'num_beams' in trans_config and trans_config['num_beams']:
                            old_beams = num_beams
                            num_beams = int(trans_config['num_beams'])
                            logger_stage.info(f"  translation.num_beams override: {old_beams} → {num_beams} (from job.json)")
                    
                    # Override workflow
                    if 'workflow' in job_data and job_data['workflow']:
                        old_workflow = workflow
                        workflow = job_data['workflow']
                        logger_stage.info(f"  workflow override: {old_workflow} → {workflow} (from job.json)")
            except Exception as e:
                logger_stage.warning(f"Failed to read job.json parameters: {e}")
        else:
            logger_stage.warning(f"job.json not found at {job_json_path}, using system defaults")
        
        logger_stage.info(f"Using source_language: {source_language}")
        logger_stage.info(f"Using target_languages: {target_langs}")
        logger_stage.info(f"Using translation_model: {translation_model}")
        logger_stage.info(f"Using device: {device}")
        logger_stage.info(f"Using workflow: {workflow}")
        
        if not translation_enabled:
            logger_stage.info("Translation stage disabled in configuration, skipping")
            io.finalize(status="success")
            return 0
        
        # Find input transcript/subtitle files
        # Look for ASR output or previous stage outputs
        input_files = []
        search_dirs = [
            io.output_base / "07_hallucination_removal",
            io.output_base / "06_lyrics_detection",
            io.output_base / "04_asr",
            io.output_base / "transcripts"
        ]
        
        for search_dir in search_dirs:
            if search_dir.exists():
                # Look for JSON transcripts
                for pattern in ["transcript_cleaned.json", "transcript_with_lyrics.json", "transcript.json", "segments.json"]:
                    candidate = search_dir / pattern
                    if candidate.exists():
                        input_files.append(candidate)
                        io.track_input(candidate, "transcript")
                        logger_stage.info(f"Input: {candidate}")
                        break
                if input_files:
                    break
        
        if not input_files:
            logger_stage.warning("No input transcript found for translation")
            io.finalize(status="success")
            return 0
        
        # Get target languages (already loaded from job.json above)
        logger_stage.info(f"Target languages: {target_langs}")
        
        # Get translation configuration (already loaded from job.json above)
        # device and num_beams are set above
        
        # Create translator configuration
        trans_config = TranslationConfig(
            device=device,
            num_beams=num_beams
        )
        
        # Create translator
        logger_stage.info(f"Initializing IndicTrans2 translator (device: {device})...")
        translator = IndicTrans2Translator(config=trans_config)
        
        try:
            # For each target language, translate
            for target_lang in target_langs:
                output_file = io.stage_dir / f"translated_{target_lang}.json"
                
                logger_stage.info(f"Translating to {target_lang}...")
                
                # Load input transcript
                with open(input_files[0], 'r', encoding='utf-8') as f:
                    transcript_data = json.load(f)
                
                # Extract segments
                if isinstance(transcript_data, dict):
                    segments = transcript_data.get('segments', [])
                else:
                    segments = transcript_data
                
                # Translate segments
                translated_segments = []
                for segment in segments:
                    text = segment.get('text', '')
                    if text:
                        # Translate text
                        translated_text = translator.translate_text(text)
                        
                        # Create translated segment
                        translated_seg = segment.copy()
                        translated_seg['text'] = translated_text
                        translated_seg['original_text'] = text
                        translated_segments.append(translated_seg)
                
                # Save translated output
                output_data = {
                    'segments': translated_segments,
                    'language': target_lang,
                    'source_language': transcript_data.get('language', 'unknown') if isinstance(transcript_data, dict) else 'unknown'
                }
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(output_data, f, indent=2, ensure_ascii=False)
                
                io.track_output(output_file, "translation")
                logger_stage.info(f"Created: {output_file}")
                logger_stage.info(f"  Translated {len(translated_segments)} segments")
            
            logger_stage.info("=" * 80)
            logger_stage.info("IndicTrans2 Translation Complete")
            logger_stage.info("=" * 80)
            
            io.finalize(status="success")
            return 0
            
        finally:
            translator.cleanup()
        
    except Exception as e:
        logger_stage.error(f"Translation stage failed: {e}", exc_info=True)
        io.finalize(status="failed")
        return 1


def main() -> None:
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
        
        logger.info(f"\n✓ Successfully translated {num_translated} subtitles")
        logger.info(f"  Output: {args.output}")
        return 0
        
    except Exception as e:
        logger.info(f"\n✗ Translation failed: {e}")
        return 1
    finally:
        translator.cleanup()


if __name__ == "__main__":
    import sys
    sys.exit(main())
