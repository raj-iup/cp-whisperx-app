#!/usr/bin/env python3
"""
Hybrid Translation System - Combines IndicTrans2 + LLM-based translation

Strategy:
1. Dialogue segments → IndicTrans2 (fast, accurate for conversational text)
2. Song/Poetry segments → LLM with film context (creative, context-aware)
3. Named entities preserved across both methods

Uses lyrics_detection to identify song segments, then applies appropriate
translation method based on segment type.
"""

# Standard library
import sys
import json
import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.stage_utils import StageIO
from shared.config import load_config

# Local
from shared.logger import get_logger
logger = get_logger(__name__)


@dataclass
class TranslationResult:
    """Result from translation"""
    text: str
    method: str  # 'indictrans2', 'llm', 'hybrid', 'fallback'
    confidence: float
    is_song: bool
    lyric_confidence: float = 0.0  # From lyrics detection
    fallback_reason: Optional[str] = None  # Why fallback was triggered


class HybridTranslator:
    """
    Hybrid translator combining IndicTrans2 and LLM-based translation
    """
    
    def __init__(
        self,
        source_lang: str,
        target_lang: str,
        film_context: Optional[str] = None,
        glossary_path: Optional[Path] = None,
        use_llm_for_songs: bool = True,
        llm_provider: str = "anthropic",  # 'anthropic', 'openai'
        logger = None,
        confidence_threshold: float = 0.7,  # Min confidence for primary translation
        enable_fallback: bool = True  # Enable confidence-based fallback
    ):
        """
        Initialize hybrid translator
        
        Args:
            source_lang: Source language code (e.g., 'hi')
            target_lang: Target language code (e.g., 'en')
            film_context: Film-specific context (from prompt file)
            glossary_path: Path to glossary TSV
            use_llm_for_songs: Use LLM for song/poetry translation
            llm_provider: LLM provider to use
            logger: Logger instance
            confidence_threshold: Minimum confidence to accept translation
            enable_fallback: Enable confidence-based fallback to alternative methods
        """
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.film_context = film_context
        self.glossary_path = glossary_path
        self.use_llm_for_songs = use_llm_for_songs
        self.llm_provider = llm_provider
        self.logger = logger or self._create_default_logger()
        self.confidence_threshold = confidence_threshold
        self.enable_fallback = enable_fallback
        
        # Initialize translators
        self.indictrans2 = None
        self.llm_client = None
        
        # LLM availability tracking
        self.llm_available = True  # Assume available until first failure
        self.llm_error_logged = False  # Track if we've logged LLM errors
        
        # Statistics
        self.stats = {
            'total_segments': 0,
            'dialogue_segments': 0,
            'song_segments': 0,
            'indictrans2_used': 0,
            'llm_used': 0,
            'llm_skipped': 0,  # Skipped due to unavailability
            'fallback_triggered': 0,
            'low_confidence_count': 0,
            'errors': 0
        }
    
    def _create_default_logger(self):
        """Create default logger"""
        import logging
        logger = logging.getLogger("hybrid_translator")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def load_indictrans2(self) -> None:
        """Load IndicTrans2 model"""
        try:
            from indictrans2_translator import IndicTrans2Translator, TranslationConfig
            
            self.logger.info("Loading IndicTrans2 model for dialogue translation...")
            
            config = TranslationConfig(
                src_lang=self._map_to_indictrans2_lang(self.source_lang),
                tgt_lang=self._map_to_indictrans2_lang(self.target_lang),
                device="auto"
            )
            
            self.indictrans2 = IndicTrans2Translator(
                config=config,
                logger: logging.Logger=self.logger,
                source_lang=self.source_lang,
                target_lang=self.target_lang
            )
            
            self.indictrans2.load_model()
            self.logger.info("✓ IndicTrans2 loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to load IndicTrans2: {e}", exc_info=True)
            raise
    
    def load_llm_client(self) -> None:
        """Load LLM client for creative translation"""
        if not self.use_llm_for_songs:
            return
        
        try:
            if self.llm_provider == "anthropic":
                self._load_anthropic()
            elif self.llm_provider == "openai":
                self._load_openai()
            else:
                raise ValueError(f"Unknown LLM provider: {self.llm_provider}")
            
            self.logger.info(f"✓ LLM client ({self.llm_provider}) loaded successfully")
            
        except Exception as e:
            self.logger.warning(f"Failed to load LLM client: {e}")
            self.logger.warning("Will fallback to IndicTrans2 for all translations")
            self.use_llm_for_songs = False
    
    def _load_anthropic(self) -> None:
        """Load Anthropic Claude client"""
        try:
            import anthropic
            
            # Get API key from secrets or environment
            api_key = self._get_api_key("anthropic")
            if not api_key:
                raise ValueError("Anthropic API key not found")
            
            self.llm_client = anthropic.Anthropic(api_key=api_key)
            
        except ImportError:
            raise ImportError(
                "anthropic library not installed. "
                "Install with: pip install anthropic"
            )
    
    def _load_openai(self) -> None:
        """Load OpenAI client"""
        try:
            import openai
            
            # Get API key from secrets or environment
            api_key = self._get_api_key("openai")
            if not api_key:
                raise ValueError("OpenAI API key not found")
            
            self.llm_client = openai.OpenAI(api_key=api_key)
            
        except ImportError:
            raise ImportError(
                "openai library not installed. "
                "Install with: pip install openai"
            )
    
    def _get_api_key(self, provider: str) -> Optional[str]:
        """Get API key from secrets.json or environment"""
        # Check environment first
        env_var = f"{provider.upper()}_API_KEY"
        api_key = os.environ.get(env_var)
        if api_key:
            return api_key
        
        # Check secrets.json
        secrets_file = PROJECT_ROOT / 'config' / 'secrets.json'
        if secrets_file.exists():
            try:
                with open(secrets_file, 'r') as f:
                    secrets = json.load(f)
                    return secrets.get(f"{provider}_api_key")
            except Exception as e:
                self.logger.debug(f"Could not load secrets.json: {e}")
        
        return None
    
    def _map_to_indictrans2_lang(self, lang_code: str) -> str:
        """Map Whisper lang code to IndicTrans2 format"""
        mapping = {
            "hi": "hin_Deva",
            "en": "eng_Latn",
            "ta": "tam_Taml",
            "te": "tel_Telu",
            "bn": "ben_Beng",
            "gu": "guj_Gujr",
            "kn": "kan_Knda",
            "ml": "mal_Mlym",
            "mr": "mar_Deva",
            "pa": "pan_Guru",
            "ur": "urd_Arab",
        }
        return mapping.get(lang_code, lang_code)
    
    def translate_segment(
        self,
        text: str,
        is_song: bool = False,
        context: Optional[Dict] = None
    ) -> TranslationResult:
        """
        Translate a single segment using confidence-based hybrid approach
        
        Strategy:
        1. Primary translation (IndicTrans2 or LLM based on segment type)
        2. Evaluate confidence using multiple signals:
           - Lyrics detection confidence (if available)
           - Translation quality heuristics
           - Repetition detection
        3. If low confidence, try fallback method
        
        Args:
            text: Text to translate
            is_song: Whether this is a song/poetry segment
            context: Additional context (speaker, timestamp, etc.)
            
        Returns:
            TranslationResult with translation and metadata
        """
        self.stats['total_segments'] += 1
        
        if not text or not text.strip():
            return TranslationResult(
                text=text,
                method='skip',
                confidence=1.0,
                is_song=False
            )
        
        # Get lyric confidence from context if available
        lyric_confidence = context.get('lyric_confidence', 0.0) if context else 0.0
        
        try:
            # Step 1: Primary translation based on segment type
            if is_song and self.use_llm_for_songs and self.llm_client:
                primary_result = self._translate_with_llm(text, context)
                primary_method = 'llm'
            else:
                primary_result = self._translate_with_indictrans2(text)
                primary_method = 'indictrans2'
            
            # Step 2: Evaluate overall confidence
            overall_confidence = self._calculate_confidence(
                primary_result, 
                text, 
                lyric_confidence,
                is_song
            )
            primary_result.confidence = overall_confidence
            primary_result.lyric_confidence = lyric_confidence
            
            # Step 3: Apply confidence-based fallback if needed
            if self.enable_fallback and overall_confidence < self.confidence_threshold:
                self.stats['low_confidence_count'] += 1
                
                fallback_result = self._try_fallback_translation(
                    text, 
                    primary_result,
                    primary_method,
                    is_song,
                    context
                )
                
                if fallback_result:
                    self.stats['fallback_triggered'] += 1
                    return fallback_result
            
            return primary_result
                
        except Exception as e:
            self.logger.error(f"Translation error for text: {text[:50]}... Error: {e}", exc_info=True)
            self.stats['errors'] += 1
            
            # Fallback to original text
            return TranslationResult(
                text=text,
                method='error',
                confidence=0.0,
                is_song=is_song,
                lyric_confidence=lyric_confidence,
                fallback_reason=str(e)
            )
    
    def _calculate_confidence(
        self,
        result: TranslationResult,
        original_text: str,
        lyric_confidence: float,
        is_song: bool
    ) -> float:
        """
        Calculate overall confidence score using multiple signals
        
        Confidence factors:
        1. Lyrics detection confidence (if song segment)
        2. Translation quality heuristics:
           - Length ratio (translated vs original)
           - Repetition patterns
           - Empty/too short translations
           - Character variety
        
        Args:
            result: Initial translation result
            original_text: Original text
            lyric_confidence: Confidence from lyrics detection
            is_song: Whether this is a song segment
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        scores = []
        
        # Factor 1: Base method confidence
        scores.append(result.confidence)
        
        # Factor 2: Lyrics detection confidence (important signal!)
        if is_song and lyric_confidence > 0:
            # High lyric confidence = likely a song = LLM preferred
            # Low lyric confidence = might be dialogue = IndicTrans2 okay
            if result.method == 'llm':
                # LLM is good for high-confidence songs
                scores.append(lyric_confidence)
            else:
                # IndicTrans2 for low-confidence songs is risky
                scores.append(1.0 - (lyric_confidence * 0.5))  # Penalize slightly
        
        # Factor 3: Length ratio check (detect missing/truncated translations)
        translated_len = len(result.text.strip())
        original_len = len(original_text.strip())
        
        if translated_len == 0:
            scores.append(0.0)  # Empty translation = bad
        elif original_len > 0:
            length_ratio = translated_len / original_len
            if 0.3 <= length_ratio <= 3.0:  # Reasonable length range
                scores.append(0.9)
            elif 0.1 <= length_ratio <= 5.0:  # Acceptable range
                scores.append(0.7)
            else:
                scores.append(0.5)  # Suspicious length
        
        # Factor 4: Repetition detection (hallucinations)
        words = result.text.split()
        if len(words) > 3:
            word_set = set(words)
            unique_ratio = len(word_set) / len(words)
            if unique_ratio < 0.5:  # High repetition
                scores.append(0.6)
            else:
                scores.append(0.9)
        
        # Factor 5: Character variety (detect garbage output)
        if len(result.text) > 0:
            char_set = set(result.text.lower().replace(' ', ''))
            if len(char_set) < 3:  # Very low variety
                scores.append(0.5)
            else:
                scores.append(0.9)
        
        # Calculate weighted average
        return sum(scores) / len(scores) if scores else 0.5
    
    def _try_fallback_translation(
        self,
        text: str,
        primary_result: TranslationResult,
        primary_method: str,
        is_song: bool,
        context: Optional[Dict]
    ) -> Optional[TranslationResult]:
        """
        Try alternative translation method when primary has low confidence
        
        Fallback strategy:
        - If primary was IndicTrans2 and is_song: Try LLM
        - If primary was LLM (failed/low confidence): Try IndicTrans2
        - Compare results and pick better one
        
        Args:
            text: Original text
            primary_result: Result from primary method
            primary_method: Which method was used ('indictrans2' or 'llm')
            is_song: Whether segment is a song
            context: Additional context
            
        Returns:
            Better translation result, or None if fallback failed
        """
        try:
            self.logger.info(f"Low confidence ({primary_result.confidence:.2f}) - trying fallback for: {text[:50]}...")
            
            # Try alternative method
            if primary_method == 'indictrans2' and is_song and self.llm_client:
                # Song segment with low IndicTrans2 confidence -> try LLM
                fallback_result = self._translate_with_llm(text, context)
                fallback_reason = "low_confidence_indictrans2_for_song"
                
            elif primary_method == 'llm':
                # LLM failed or low confidence -> try IndicTrans2
                fallback_result = self._translate_with_indictrans2(text)
                fallback_reason = "llm_failed_or_low_confidence"
                
            else:
                # No fallback available
                return None
            
            # Calculate confidence for fallback
            fallback_confidence = self._calculate_confidence(
                fallback_result,
                text,
                context.get('lyric_confidence', 0.0) if context else 0.0,
                is_song
            )
            fallback_result.confidence = fallback_confidence
            
            # Pick better result
            if fallback_confidence > primary_result.confidence:
                self.logger.info(f"✓ Fallback improved confidence: {primary_result.confidence:.2f} -> {fallback_confidence:.2f}")
                fallback_result.method = f"hybrid_{primary_method}_fallback"
                fallback_result.fallback_reason = fallback_reason
                return fallback_result
            else:
                self.logger.info(f"Primary method still better: {primary_result.confidence:.2f} vs {fallback_confidence:.2f}")
                return primary_result
                
        except Exception as e:
            self.logger.warning(f"Fallback translation failed: {e}")
            return None
    
    def _translate_with_indictrans2(self, text: str) -> TranslationResult:
        """Translate using IndicTrans2"""
        self.stats['dialogue_segments'] += 1
        self.stats['indictrans2_used'] += 1
        
        translated = self.indictrans2.translate_text(text)
        
        return TranslationResult(
            text=translated,
            method='indictrans2',
            confidence=0.9,
            is_song=False
        )
    
    def _translate_with_llm(
        self,
        text: str,
        context: Optional[Dict] = None
    ) -> TranslationResult:
        """Translate song/poetry using LLM with film context"""
        
        # Skip LLM if we know it's unavailable
        if not self.llm_available:
            self.stats['llm_skipped'] += 1
            # Silently fall back to IndicTrans2
            return self._translate_with_indictrans2(text)
        
        self.stats['song_segments'] += 1
        self.stats['llm_used'] += 1
        
        # Build context-aware prompt
        prompt = self._build_llm_prompt(text, context)
        
        try:
            if self.llm_provider == "anthropic":
                translated = self._call_anthropic(prompt)
            elif self.llm_provider == "openai":
                translated = self._call_openai(prompt)
            else:
                raise ValueError(f"Unknown provider: {self.llm_provider}")
            
            return TranslationResult(
                text=translated,
                method='llm',
                confidence=0.95,
                is_song=True
            )
            
        except Exception as e:
            error_str = str(e)
            
            # Check if this is a persistent API error (credits, auth, etc.)
            is_persistent_error = any(err in error_str.lower() for err in [
                'credit balance',
                'authentication',
                'api key',
                'quota',
                'rate limit exceeded',
                'insufficient_quota'
            ])
            
            if is_persistent_error:
                # Mark LLM as unavailable to stop retrying
                if not self.llm_error_logged:
                    self.logger.warning(f"⚠️  LLM API unavailable: {error_str[:150]}")
                    self.logger.warning(f"    Switching to IndicTrans2 for all remaining segments")
                    self.llm_error_logged = True
                self.llm_available = False
            else:
                # Non-persistent error - log it
                self.logger.warning(f"LLM translation failed: {e}, falling back to IndicTrans2")
            
            # Fall back to IndicTrans2
            return self._translate_with_indictrans2(text)
    
    def _build_llm_prompt(self, text: str, context: Optional[Dict] = None) -> str:
        """Build context-aware prompt for LLM translation"""
        prompt_parts = [
            f"Translate this {self.source_lang} song lyric to natural, poetic {self.target_lang}.",
            "",
            "Guidelines:",
            "- Preserve poetic rhythm and emotion",
            "- Use natural, contemporary language",
            "- Maintain rhyme scheme if possible",
            "- Consider cultural context",
            ""
        ]
        
        # Add film context if available
        if self.film_context:
            prompt_parts.extend([
                "Film Context:",
                self.film_context,
                ""
            ])
        
        # Add segment context if available
        if context:
            if 'timestamp' in context:
                prompt_parts.append(f"Timestamp: {context['timestamp']}")
            if 'speaker' in context:
                prompt_parts.append(f"Speaker: {context['speaker']}")
            prompt_parts.append("")
        
        prompt_parts.extend([
            f"Original ({self.source_lang}):",
            text,
            "",
            f"Natural {self.target_lang} translation:"
        ])
        
        return "\n".join(prompt_parts)
    
    def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic Claude API"""
        response = self.llm_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=500,
            temperature=0.7,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        return response.content[0].text.strip()
    
    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI GPT API"""
        response = self.llm_client.chat.completions.create(
            model="gpt-4",
            max_tokens=500,
            temperature=0.7,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        return response.choices[0].message.content.strip()
    
    def translate_segments(
        self,
        segments: List[Dict]
    ) -> List[Dict]:
        """
        Translate all segments using hybrid approach
        
        Args:
            segments: List of segment dicts with 'text' and optional 'is_lyric'
            
        Returns:
            Segments with translated text
        """
        self.logger.info(f"Translating {len(segments)} segments using hybrid approach...")
        
        translated_segments = []
        
        for i, segment in enumerate(segments):
            text = segment.get('text', '').strip()
            is_song = segment.get('is_lyric', False) or segment.get('is_song', False)
            
            if not text:
                translated_segments.append(segment)
                continue
            
            # Build context with lyrics detection confidence
            context = {
                'timestamp': f"{segment.get('start', 0):.1f}s",
                'index': i,
                'lyric_confidence': segment.get('lyric_confidence', 0.0)  # From lyrics detection
            }
            
            # Translate
            result = self.translate_segment(text, is_song, context)
            
            # Update segment
            segment_copy = segment.copy()
            segment_copy['text'] = result.text
            segment_copy['translation_method'] = result.method
            segment_copy['translation_confidence'] = result.confidence
            segment_copy['lyric_confidence'] = result.lyric_confidence
            if result.fallback_reason:
                segment_copy['fallback_reason'] = result.fallback_reason
            
            translated_segments.append(segment_copy)
            
            # Progress logging
            if (i + 1) % 100 == 0:
                self.logger.info(f"  Translated {i + 1}/{len(segments)} segments")
        
        return translated_segments
    
    def get_statistics(self) -> Dict:
        """Get translation statistics"""
        return self.stats.copy()


def main() -> None:
    """Main entry point for hybrid translation stage"""
    
    # Setup stage I/O
    stage_io = StageIO("hybrid_translation")
    logger = stage_io.get_stage_logger("INFO")
    
    logger.info("=" * 70)
    logger.info("HYBRID TRANSLATION STAGE")
    logger.info("=" * 70)
    
    # Load configuration
    config_path = stage_io.output_base / f".{stage_io.output_base.name}.env"
    if not config_path.exists():
        config_path = Path("config/.env.pipeline")
    
    config = load_config(config_path)
    
    # Get translation settings
    source_lang = config.get('SOURCE_LANG', 'hi')
    target_lang = config.get('TARGET_LANG', 'en')
    use_llm = config.get('USE_LLM_FOR_SONGS', 'true').lower() == 'true'
    llm_provider = config.get('LLM_PROVIDER', 'anthropic')
    confidence_threshold = float(config.get('CONFIDENCE_THRESHOLD', '0.7'))
    enable_fallback = config.get('ENABLE_CONFIDENCE_FALLBACK', 'true').lower() == 'true'
    
    logger.info(f"Source language: {source_lang}")
    logger.info(f"Target language: {target_lang}")
    logger.info(f"LLM for songs: {use_llm}")
    if use_llm:
        logger.info(f"LLM provider: {llm_provider}")
    logger.info(f"Confidence threshold: {confidence_threshold}")
    logger.info(f"Confidence-based fallback: {enable_fallback}")
    
    # Load film context if available
    film_title = config.get('FILM_TITLE', '')
    film_year = config.get('FILM_YEAR', '')
    film_context = None
    
    if film_title and film_year:
        prompt_file = PROJECT_ROOT / "glossary" / "prompts" / f"{film_title.lower().replace(' ', '_')}_{film_year}.txt"
        if prompt_file.exists():
            with open(prompt_file, 'r', encoding='utf-8') as f:
                film_context = f.read()
            logger.info(f"✓ Loaded film context from: {prompt_file.name}")
    
    # Load glossary path
    glossary_path = PROJECT_ROOT / config.get('GLOSSARY_PATH', 'glossary/hinglish_master.tsv')
    
    # Load transcription segments from ASR
    try:
        data = stage_io.load_json("segments.json", from_stage="asr")
    except Exception as e:
        logger.error(f"Failed to load segments from ASR: {e}", exc_info=True)
        return 1
    
    segments = data.get('segments', []) if isinstance(data, dict) else data
    logger.info(f"Loaded {len(segments)} segments from ASR")
    
    # Load lyrics metadata and merge with segments
    try:
        lyrics_meta = stage_io.load_json("lyrics_metadata.json", from_stage="lyrics_detection")
        lyric_segments = lyrics_meta.get('lyric_segments', [])
        
        if lyric_segments:
            logger.info(f"Loaded {len(lyric_segments)} lyric segments from lyrics detection")
            
            # Mark segments that overlap with detected lyric regions
            for segment in segments:
                seg_start = segment.get('start', 0)
                seg_end = segment.get('end', 0)
                
                # Check if segment overlaps with any lyric region
                for lyric in lyric_segments:
                    if (seg_start >= lyric['start'] and seg_start < lyric['end']) or \
                       (seg_end > lyric['start'] and seg_end <= lyric['end']) or \
                       (seg_start <= lyric['start'] and seg_end >= lyric['end']):
                        segment['is_lyric'] = True
                        segment['lyric_confidence'] = lyric.get('confidence', 0.0)
                        break
        else:
            logger.warning("No lyric segments found in lyrics detection metadata")
            
    except Exception as e:
        logger.warning(f"Failed to load lyrics metadata: {e}")
        logger.warning("Continuing without lyric detection - all segments treated as dialogue")
    
    # Count song segments
    song_count = sum(1 for s in segments if s.get('is_lyric') or s.get('is_song'))
    logger.info(f"  Song segments: {song_count}")
    logger.info(f"  Dialogue segments: {len(segments) - song_count}")
    
    # Initialize hybrid translator
    translator = HybridTranslator(
        source_lang=source_lang,
        target_lang=target_lang,
        film_context=film_context,
        glossary_path=glossary_path if glossary_path.exists() else None,
        use_llm_for_songs=use_llm,
        llm_provider=llm_provider,
        logger: logging.Logger=logger,
        confidence_threshold=confidence_threshold,
        enable_fallback=enable_fallback
    )
    
    # Load models
    translator.load_indictrans2()
    if use_llm:
        translator.load_llm_client()
    
    # Translate segments
    translated_segments = translator.translate_segments(segments)
    
    # Save results with correct filename
    output_data = data.copy() if isinstance(data, dict) else {}
    output_data['segments'] = translated_segments
    output_data['translation_stats'] = translator.get_statistics()
    
    # Save to the output file specified by pipeline
    output_file = Path(os.environ.get('OUTPUT_FILE', ''))
    if output_file:
        # Save to pipeline-specified location
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        logger.info(f"✓ Saved translation to: {output_file}")
    else:
        # Fallback to StageIO (for standalone usage)
        stage_io.save_json(output_data, f"segments_{target_lang}.json")
        stage_io.save_json(output_data, "translated_segments.json")
    
    # Report statistics
    stats = translator.get_statistics()
    logger.info("=" * 70)
    logger.info("TRANSLATION STATISTICS")
    logger.info("=" * 70)
    logger.info(f"Total segments: {stats['total_segments']}")
    logger.info(f"Dialogue segments: {stats['dialogue_segments']}")
    logger.info(f"Song segments: {stats['song_segments']}")
    logger.info(f"IndicTrans2 used: {stats['indictrans2_used']}")
    logger.info(f"LLM used: {stats['llm_used']}")
    if stats.get('llm_skipped', 0) > 0:
        logger.info(f"LLM skipped (unavailable): {stats['llm_skipped']}")
    logger.info(f"Low confidence count: {stats['low_confidence_count']}")
    logger.info(f"Fallback triggered: {stats['fallback_triggered']}")
    logger.info(f"Errors: {stats['errors']}")
    logger.info("=" * 70)
    logger.info("✓ Hybrid translation complete")
    logger.info("=" * 70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
