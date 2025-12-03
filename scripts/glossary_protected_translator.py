#!/usr/bin/env python3
"""
Glossary Protected Translator - Phase 4: Advanced Features

Protects glossary terms (proper nouns, character names, places) during translation
by replacing them with placeholders before translation and restoring after.

Strategy:
1. Extract proper nouns from glossary
2. Replace with placeholders before translation (__TERM_0001__, __TERM_0002__, etc.)
3. Translate text with placeholders
4. Restore original terms after translation

This prevents translation systems from mistranslating names like:
- "Jai" → "Victory" (should stay "Jai")
- "Mumbai" → "Bombay" (should stay "Mumbai")
- "Aditi" → "Beginning" (should stay "Aditi")
"""

# Standard library
import re
import logging
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path

# Local
from shared.logger import get_logger
logger = get_logger(__name__)


class GlossaryProtectedTranslator:
    """
    Translator wrapper that protects glossary terms during translation.

    Usage:
        base_translator = IndicTrans2Translator(config)
        glossary = UnifiedGlossaryManager(...)
        translator = GlossaryProtectedTranslator(glossary, base_translator)

        result = translator.translate("Jai lives in Mumbai", "hi", "en")
        # Output: "Jai lives in Mumbai" (names preserved)
    """

    def __init__(
        self,
        glossary,
        base_translator,
        logger: Optional[logging.Logger] = None,
        placeholder_pattern: str = "__TERM_{:04d}__"
    ):
        """
        Initialize glossary-protected translator.

        Args:
            glossary: UnifiedGlossaryManager or compatible glossary object
            base_translator: Base translator (IndicTrans2, NLLB, etc.)
            logger: Logger instance
            placeholder_pattern: Format string for placeholders (must include {:04d})
        """
        self.glossary = glossary
        self.translator = base_translator
        self.logger = logger or logging.getLogger(__name__)
        self.placeholder_pattern = placeholder_pattern

        # Statistics
        self.stats = {
            'total_translations': 0,
            'terms_protected': 0,
            'terms_restored': 0,
            'protection_failures': 0
        }

    def extract_proper_nouns(self) -> List[str]:
        """
        Extract proper nouns from glossary that should be protected.

        Returns:
            List of proper noun strings to protect
        """
        proper_nouns = []

        # Try different glossary API methods
        if hasattr(self.glossary, 'get_proper_nouns'):
            # UnifiedGlossaryManager API
            proper_nouns = self.glossary.get_proper_nouns()

        elif hasattr(self.glossary, 'entries'):
            # Direct access to entries
            for entry in self.glossary.entries:
                if isinstance(entry, dict):
                    entry_type = entry.get('type', '').lower()
                    if entry_type in ['name', 'place', 'title', 'character']:
                        source = entry.get('source', '').strip()
                        if source:
                            proper_nouns.append(source)

        elif hasattr(self.glossary, 'glossary_dict'):
            # Dictionary-based glossary
            for source_term, target_term in self.glossary.glossary_dict.items():
                # Heuristic: Capitalized words are likely proper nouns
                if source_term and source_term[0].isupper():
                    proper_nouns.append(source_term)

        self.logger.debug(f"Extracted {len(proper_nouns)} proper nouns for protection")
        return proper_nouns

    def protect_terms(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Replace glossary terms with placeholders.

        Args:
            text: Source text to protect

        Returns:
            Tuple of (protected_text, term_map)
            - protected_text: Text with placeholders
            - term_map: Dict mapping placeholder -> original term
        """
        if not text or not text.strip():
            return text, {}

        term_map = {}
        protected = text
        proper_nouns = self.extract_proper_nouns()

        if not proper_nouns:
            self.logger.debug("No proper nouns to protect")
            return text, {}

        # Sort by length (longest first) to avoid partial matches
        # e.g., "Jai" should not match inside "Jaipur"
        proper_nouns_sorted = sorted(set(proper_nouns), key=len, reverse=True)

        term_index = 0
        for term in proper_nouns_sorted:
            if not term or len(term) < 2:  # Skip very short terms
                continue

            # Check if term exists in text (case-insensitive)
            pattern = re.compile(r'\b' + re.escape(term) + r'\b', re.IGNORECASE)
            matches = pattern.findall(protected)

            if matches:
                placeholder = self.placeholder_pattern.format(term_index)
                term_map[placeholder] = term  # Store original term

                # Replace all occurrences
                protected = pattern.sub(placeholder, protected)
                term_index += 1

                self.logger.debug(f"Protected term: '{term}' → '{placeholder}'")

        self.stats['terms_protected'] += len(term_map)
        return protected, term_map

    def restore_terms(self, text: str, term_map: Dict[str, str]) -> str:
        """
        Restore original terms from placeholders.

        Args:
            text: Translated text with placeholders
            term_map: Dict mapping placeholder -> original term

        Returns:
            Text with original terms restored
        """
        if not text or not term_map:
            return text

        restored = text
        restored_count = 0

        for placeholder, original_term in term_map.items():
            if placeholder in restored:
                restored = restored.replace(placeholder, original_term)
                restored_count += 1
                self.logger.debug(f"Restored term: '{placeholder}' → '{original_term}'")
            else:
                self.logger.warning(
                    f"Placeholder '{placeholder}' not found in translated text. "
                    f"Original term '{original_term}' may have been lost."
                )
                self.stats['protection_failures'] += 1

        self.stats['terms_restored'] += restored_count
        return restored

    def translate(
        self,
        text: str,
        src_lang: str,
        tgt_lang: str,
        **kwargs
    ) -> str:
        """
        Translate with glossary protection.

        Args:
            text: Source text to translate
            src_lang: Source language code (e.g., 'hi')
            tgt_lang: Target language code (e.g., 'en')
            **kwargs: Additional arguments to pass to base translator

        Returns:
            Translated text with glossary terms preserved
        """
        self.stats['total_translations'] += 1

        # Step 1: Protect terms
        protected_text, term_map = self.protect_terms(text)

        if term_map:
            self.logger.debug(
                f"Protected {len(term_map)} terms before translation: "
                f"{list(term_map.values())[:5]}{'...' if len(term_map) > 5 else ''}"
            )

        # Step 2: Translate
        try:
            translated = self.translator.translate(
                protected_text,
                src_lang,
                tgt_lang,
                **kwargs
            )
        except Exception as e:
            self.logger.error(f"Translation failed: {e}", exc_info=True)
            # Return original text as fallback
            return text

        # Step 3: Restore terms
        final = self.restore_terms(translated, term_map)

        return final

    def translate_batch(
        self,
        texts: List[str],
        src_lang: str,
        tgt_lang: str,
        **kwargs
    ) -> List[str]:
        """
        Batch translation with glossary protection.

        Args:
            texts: List of source texts to translate
            src_lang: Source language code
            tgt_lang: Target language code
            **kwargs: Additional arguments to pass to base translator

        Returns:
            List of translated texts with glossary terms preserved
        """
        results = []

        # Check if base translator supports batch translation
        if hasattr(self.translator, 'translate_batch'):
            # Protect all texts first
            protected_texts = []
            term_maps = []

            for text in texts:
                protected, term_map = self.protect_terms(text)
                protected_texts.append(protected)
                term_maps.append(term_map)

            # Batch translate
            try:
                translated_texts = self.translator.translate_batch(
                    protected_texts,
                    src_lang,
                    tgt_lang,
                    **kwargs
                )
            except Exception as e:
                self.logger.error(f"Batch translation failed: {e}", exc_info=True)
                # Fallback to individual translation
                return [self.translate(text, src_lang, tgt_lang, **kwargs) for text in texts]

            # Restore terms
            for translated, term_map in zip(translated_texts, term_maps):
                restored = self.restore_terms(translated, term_map)
                results.append(restored)
        else:
            # Fallback: Translate one by one
            for text in texts:
                result = self.translate(text, src_lang, tgt_lang, **kwargs)
                results.append(result)

        return results

    def translate_segment(
        self,
        segment: Dict[str, Any],
        src_lang: str,
        tgt_lang: str,
        text_field: str = 'text',
        **kwargs
    ) -> Dict[str, Any]:
        """
        Translate a segment dict (with start, end, text, etc.).

        Args:
            segment: Segment dict with text field
            src_lang: Source language code
            tgt_lang: Target language code
            text_field: Name of field containing text to translate
            **kwargs: Additional arguments to pass to base translator

        Returns:
            Segment dict with translated text
        """
        if text_field not in segment:
            self.logger.warning(f"Segment missing '{text_field}' field")
            return segment

        # Translate text
        original_text = segment[text_field]
        translated_text = self.translate(original_text, src_lang, tgt_lang, **kwargs)

        # Update segment
        segment_copy = segment.copy()
        segment_copy[text_field] = translated_text

        # Add metadata
        segment_copy['glossary_protected'] = True

        return segment_copy

    def get_statistics(self) -> Dict[str, int]:
        """Get protection statistics."""
        return self.stats.copy()

    def reset_statistics(self):
        """Reset statistics counters."""
        self.stats = {
            'total_translations': 0,
            'terms_protected': 0,
            'terms_restored': 0,
            'protection_failures': 0
        }


def create_protected_translator(
    base_translator,
    glossary=None,
    config=None,
    logger=None
) -> Any:
    """
    Factory function to create appropriate translator with optional glossary protection.

    Args:
        base_translator: Base translator instance (IndicTrans2, NLLB, etc.)
        glossary: Glossary manager instance (optional)
        config: Configuration object (optional)
        logger: Logger instance (optional)

    Returns:
        GlossaryProtectedTranslator if glossary provided and enabled,
        otherwise returns base_translator unchanged
    """
    # Check if glossary protection is enabled
    if config:
        protection_enabled = getattr(config, 'translation_glossary_protection', True)
        if not protection_enabled:
            if logger:
                logger.info("Glossary protection disabled by configuration")
            return base_translator

    # Wrap with glossary protection if glossary available
    if glossary:
        if logger:
            logger.info("Wrapping translator with glossary protection")
        return GlossaryProtectedTranslator(glossary, base_translator, logger)

    if logger:
        logger.info("No glossary available - using base translator")
    return base_translator
