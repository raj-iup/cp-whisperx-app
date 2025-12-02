#!/usr/bin/env python3
"""
Translation Validator - Phase 4: Advanced Features

Validates translation quality and glossary compliance after translation.

Features:
1. Glossary compliance checking
2. Length ratio validation
3. Term preservation verification
4. Batch validation with statistics

Usage:
    validator = TranslationValidator(glossary)
    result = validator.validate_glossary_compliance(source_text, translated_text)
    if not result['compliant']:
        logger.warning(f"Missing terms: {result['missing_terms']}")
"""

import logging
import re
from typing import Dict, List, Tuple, Optional, Any


class TranslationValidator:
    """
    Validate translation quality and glossary compliance.

    Checks:
    - Glossary terms are preserved in translation
    - Translation length is reasonable (not too long/short)
    - Required proper nouns appear in output
    """

    def __init__(
        self,
        glossary=None,
        logger: Optional[logging.Logger] = None,
        max_length_ratio: float = 3.0,
        min_length_ratio: float = 0.3
    ):
        """
        Initialize translation validator.

        Args:
            glossary: UnifiedGlossaryManager or compatible glossary object
            logger: Logger instance
            max_length_ratio: Maximum acceptable target/source length ratio
            min_length_ratio: Minimum acceptable target/source length ratio
        """
        self.glossary = glossary
        self.logger = logger or logging.getLogger(__name__)
        self.max_length_ratio = max_length_ratio
        self.min_length_ratio = min_length_ratio

        # Statistics
        self.stats = {
            'total_validations': 0,
            'compliant': 0,
            'missing_terms_count': 0,
            'length_issues': 0
        }

    def find_terms_in_text(self, text: str) -> List[str]:
        """
        Find glossary terms present in source text.

        Args:
            text: Source text to search

        Returns:
            List of glossary terms found in text
        """
        if not self.glossary or not text:
            return []

        found_terms = []

        # Try different glossary APIs
        if hasattr(self.glossary, 'find_terms_in_text'):
            found_terms = self.glossary.find_terms_in_text(text)

        elif hasattr(self.glossary, 'get_proper_nouns'):
            # Check if any proper nouns appear in text
            proper_nouns = self.glossary.get_proper_nouns()
            for term in proper_nouns:
                if term and re.search(r'\b' + re.escape(term) + r'\b', text, re.IGNORECASE):
                    found_terms.append(term)

        elif hasattr(self.glossary, 'glossary_dict'):
            # Check dictionary keys
            for source_term in self.glossary.glossary_dict.keys():
                if source_term and re.search(r'\b' + re.escape(source_term) + r'\b', text, re.IGNORECASE):
                    found_terms.append(source_term)

        return found_terms

    def get_expected_translation(self, term: str) -> Optional[str]:
        """
        Get expected translation for a glossary term.

        Args:
            term: Source term

        Returns:
            Expected translation or None
        """
        if not self.glossary:
            return None

        # Try different glossary APIs
        if hasattr(self.glossary, 'get_translation'):
            return self.glossary.get_translation(term)

        elif hasattr(self.glossary, 'glossary_dict'):
            return self.glossary.glossary_dict.get(term)

        elif hasattr(self.glossary, 'apply_to_text'):
            # For proper nouns, we expect them to be preserved as-is
            # (UnifiedGlossaryManager preserves proper nouns)
            return term

        return None

    def validate_glossary_compliance(
        self,
        source_text: str,
        translated_text: str
    ) -> Dict[str, Any]:
        """
        Check if required glossary terms are preserved in translation.

        Args:
            source_text: Original source text
            translated_text: Translated text

        Returns:
            Dict with:
            - compliant (bool): Whether translation is compliant
            - missing_terms (List[str]): Terms that should appear but don't
            - confidence (float): 0.0-1.0 confidence score
            - found_terms (List[str]): Terms that were found in source
        """
        result = {
            'compliant': True,
            'missing_terms': [],
            'confidence': 1.0,
            'found_terms': []
        }

        if not self.glossary or not source_text or not translated_text:
            return result

        # Find terms in source text
        required_terms = self.find_terms_in_text(source_text)
        result['found_terms'] = required_terms

        if not required_terms:
            # No glossary terms in source - automatically compliant
            return result

        self.logger.debug(f"Found {len(required_terms)} glossary terms in source text")

        # Check each term
        translated_lower = translated_text.lower()

        for term in required_terms:
            term_lower = term.lower()

            # Get expected translation
            expected = self.get_expected_translation(term)

            # Check if term or its translation appears in output
            term_found = False

            # Check for original term (often preserved for proper nouns)
            if term_lower in translated_lower:
                term_found = True
                self.logger.debug(f"Term '{term}' found in translation (original)")

            # Check for expected translation
            elif expected:
                expected_lower = expected.lower()
                if expected_lower in translated_lower:
                    term_found = True
                    self.logger.debug(f"Term '{term}' found in translation (as '{expected}')")

            if not term_found:
                result['missing_terms'].append(term)
                result['compliant'] = False
                self.logger.warning(f"Glossary term '{term}' missing from translation")

        # Calculate confidence score
        if required_terms:
            preserved_count = len(required_terms) - len(result['missing_terms'])
            result['confidence'] = preserved_count / len(required_terms)
        else:
            result['confidence'] = 1.0

        self.stats['total_validations'] += 1
        if result['compliant']:
            self.stats['compliant'] += 1
        self.stats['missing_terms_count'] += len(result['missing_terms'])

        return result

    def validate_length_ratio(
        self,
        source_text: str,
        translated_text: str
    ) -> Dict[str, Any]:
        """
        Check if translation length is reasonable.

        Very long or very short translations may indicate errors:
        - Too long: Translation may have added hallucinated content
        - Too short: Translation may have dropped content

        Args:
            source_text: Original source text
            translated_text: Translated text

        Returns:
            Dict with:
            - valid (bool): Whether length ratio is acceptable
            - ratio (float): Actual target/source length ratio
            - issue (str): Description of issue if any
        """
        result = {
            'valid': True,
            'ratio': 0.0,
            'issue': None
        }

        if not source_text or not translated_text:
            result['valid'] = False
            result['issue'] = "Empty text"
            return result

        src_len = len(source_text.strip())
        tgt_len = len(translated_text.strip())

        if src_len == 0:
            result['valid'] = False
            result['issue'] = "Empty source text"
            return result

        ratio = tgt_len / src_len
        result['ratio'] = ratio

        if ratio > self.max_length_ratio:
            result['valid'] = False
            result['issue'] = f"Translation too long (ratio {ratio:.2f} > {self.max_length_ratio})"
            self.stats['length_issues'] += 1
            self.logger.warning(result['issue'])

        elif ratio < self.min_length_ratio:
            result['valid'] = False
            result['issue'] = f"Translation too short (ratio {ratio:.2f} < {self.min_length_ratio})"
            self.stats['length_issues'] += 1
            self.logger.warning(result['issue'])

        return result

    def validate_translation(
        self,
        source_text: str,
        translated_text: str
    ) -> Dict[str, Any]:
        """
        Comprehensive validation of a single translation.

        Args:
            source_text: Original source text
            translated_text: Translated text

        Returns:
            Dict with validation results
        """
        # Glossary compliance
        glossary_result = self.validate_glossary_compliance(source_text, translated_text)

        # Length ratio
        length_result = self.validate_length_ratio(source_text, translated_text)

        # Combined result
        result = {
            'valid': glossary_result['compliant'] and length_result['valid'],
            'glossary': glossary_result,
            'length': length_result,
            'confidence': glossary_result['confidence']
        }

        return result

    def validate_batch(
        self,
        source_segments: List[Dict[str, Any]],
        translated_segments: List[Dict[str, Any]],
        text_field: str = 'text'
    ) -> Dict[str, Any]:
        """
        Validate entire batch of segment translations.

        Args:
            source_segments: List of source segment dicts
            translated_segments: List of translated segment dicts
            text_field: Name of field containing text

        Returns:
            Dict with batch statistics
        """
        if len(source_segments) != len(translated_segments):
            self.logger.error(
                f"Segment count mismatch: {len(source_segments)} source vs "
                f"{len(translated_segments)} translated"
            )
            return {
                'error': 'Segment count mismatch',
                'total': 0
            }

        stats = {
            'total': len(source_segments),
            'valid': 0,
            'glossary_compliant': 0,
            'length_valid': 0,
            'total_missing_terms': 0,
            'avg_confidence': 0.0,
            'issues': []
        }

        total_confidence = 0.0

        for i, (src_seg, tgt_seg) in enumerate(zip(source_segments, translated_segments)):
            src_text = src_seg.get(text_field, '')
            tgt_text = tgt_seg.get(text_field, '')

            if not src_text or not tgt_text:
                continue

            # Validate this translation
            validation = self.validate_translation(src_text, tgt_text)

            if validation['valid']:
                stats['valid'] += 1

            if validation['glossary']['compliant']:
                stats['glossary_compliant'] += 1
            else:
                # Record issue
                stats['issues'].append({
                    'segment_index': i,
                    'type': 'glossary',
                    'missing_terms': validation['glossary']['missing_terms'],
                    'source_text': src_text[:100]
                })

            if validation['length']['valid']:
                stats['length_valid'] += 1
            else:
                stats['issues'].append({
                    'segment_index': i,
                    'type': 'length',
                    'issue': validation['length']['issue'],
                    'ratio': validation['length']['ratio'],
                    'source_text': src_text[:100]
                })

            stats['total_missing_terms'] += len(validation['glossary']['missing_terms'])
            total_confidence += validation['confidence']

        # Calculate averages
        if stats['total'] > 0:
            stats['avg_confidence'] = total_confidence / stats['total']
            stats['valid_percentage'] = (stats['valid'] / stats['total']) * 100
            stats['glossary_compliance_percentage'] = (stats['glossary_compliant'] / stats['total']) * 100

        # Log summary
        self.logger.info("=" * 80)
        self.logger.info("Translation Validation Summary:")
        self.logger.info(f"  Total segments: {stats['total']}")
        self.logger.info(f"  Valid: {stats['valid']} ({stats.get('valid_percentage', 0):.1f}%)")
        self.logger.info(f"  Glossary compliant: {stats['glossary_compliant']} ({stats.get('glossary_compliance_percentage', 0):.1f}%)")
        self.logger.info(f"  Length valid: {stats['length_valid']}")
        self.logger.info(f"  Missing terms (total): {stats['total_missing_terms']}")
        self.logger.info(f"  Average confidence: {stats['avg_confidence']:.2%}")
        self.logger.info(f"  Issues found: {len(stats['issues'])}")
        self.logger.info("=" * 80)

        # Log issues (first 5)
        if stats['issues']:
            self.logger.warning(f"Found {len(stats['issues'])} validation issues:")
            for issue in stats['issues'][:5]:
                if issue['type'] == 'glossary':
                    self.logger.warning(
                        f"  Segment {issue['segment_index']}: Missing terms {issue['missing_terms']} "
                        f"in '{issue['source_text']}...'"
                    )
                elif issue['type'] == 'length':
                    self.logger.warning(
                        f"  Segment {issue['segment_index']}: {issue['issue']} "
                        f"in '{issue['source_text']}...'"
                    )
            if len(stats['issues']) > 5:
                self.logger.warning(f"  ... and {len(stats['issues']) - 5} more issues")

        return stats

    def get_statistics(self) -> Dict[str, int]:
        """Get validation statistics."""
        return self.stats.copy()

    def reset_statistics(self):
        """Reset statistics counters."""
        self.stats = {
            'total_validations': 0,
            'compliant': 0,
            'missing_terms_count': 0,
            'length_issues': 0
        }
