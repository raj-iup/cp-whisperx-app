#!/usr/bin/env python3
"""
bias_injection_core.py - Core bias correction logic

Applies multiple correction methods to improve name/term accuracy:
- Exact matching (case-insensitive)
- Fuzzy matching (Levenshtein distance)
- Phonetic matching (Metaphone/Soundex)
- Context-aware temporal windows
- Pattern-based common error fixes

This module is reusable across different pipeline stages.
"""

import re
from typing import List, Dict, Tuple, Optional, Set
from difflib import SequenceMatcher
import logging

# Local
from shared.logger import get_logger
logger = get_logger(__name__)


class BiasCorrector:
    """
    Apply bias correction to transcript segments using multiple methods
    
    Methods:
    1. Exact matching (case-insensitive) - highest priority
    2. Fuzzy matching (Levenshtein) - for misspellings
    3. Phonetic matching (Metaphone) - for sound-alike errors
    4. Context-aware (temporal windows) - scene-specific terms
    """
    
    def __init__(
        self,
        bias_terms: List[str],
        fuzzy_threshold: float = 0.85,
        phonetic_threshold: float = 0.90,
        min_word_length: int = 3,
        max_corrections_per_segment: int = 10,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize bias corrector
        
        Args:
            bias_terms: List of correct terms (names, places, etc.)
            fuzzy_threshold: Minimum similarity for fuzzy match (0-1)
            phonetic_threshold: Minimum similarity for phonetic match (0-1)
            min_word_length: Skip words shorter than this
            max_corrections_per_segment: Safety limit per segment
            logger: Logger instance
        """
        self.bias_terms = bias_terms
        self.fuzzy_threshold = fuzzy_threshold
        self.phonetic_threshold = phonetic_threshold
        self.min_word_length = min_word_length
        self.max_corrections_per_segment = max_corrections_per_segment
        self.logger = logger or logging.getLogger(__name__)
        
        # Build lookup structures for fast matching
        self._build_lookups()
    
    def _build_lookups(self):
        """Build optimized lookup structures"""
        # Exact match: lowercase -> proper case
        self.term_lower = {term.lower(): term for term in self.bias_terms}
        
        # For fuzzy matching: keep list sorted by length (longer first)
        self.terms_sorted = sorted(
            self.bias_terms,
            key=len,
            reverse=True
        )
        
        # Phonetic matching
        try:
            import jellyfish
            self.metaphone_map = {
                jellyfish.metaphone(term): term 
                for term in self.bias_terms
            }
            self.jellyfish = jellyfish
            self.phonetic_available = True
        except ImportError:
            self.logger.warning("jellyfish not installed - phonetic matching disabled")
            self.logger.warning("  Install with: pip install jellyfish")
            self.metaphone_map = {}
            self.phonetic_available = False
        
        self.logger.debug(f"Built lookups for {len(self.bias_terms)} terms")
    
    def correct_segments(
        self,
        segments: List[Dict]
    ) -> Tuple[List[Dict], Dict[str, int]]:
        """
        Apply corrections to all segments
        
        Args:
            segments: List of transcript segments with 'text' field
            
        Returns:
            Tuple of (corrected_segments, statistics)
        """
        corrected_segments = []
        stats = {
            'total_segments': len(segments),
            'corrected_segments': 0,
            'total_corrections': 0,
            'methods': {
                'exact': 0,
                'fuzzy': 0,
                'phonetic': 0,
                'context': 0
            }
        }
        
        for seg in segments:
            corrected_seg, seg_stats = self._correct_segment(seg)
            corrected_segments.append(corrected_seg)
            
            if seg_stats['corrections'] > 0:
                stats['corrected_segments'] += 1
                stats['total_corrections'] += seg_stats['corrections']
                for method, count in seg_stats['methods'].items():
                    stats['methods'][method] += count
        
        return corrected_segments, stats
    
    def _correct_segment(
        self,
        segment: Dict
    ) -> Tuple[Dict, Dict]:
        """
        Correct a single segment
        
        Args:
            segment: Segment dict with 'text' field
            
        Returns:
            Tuple of (corrected_segment, segment_stats)
        """
        text = segment.get('text', '').strip()
        if not text:
            return segment, {'corrections': 0, 'methods': {}}
        
        # Split into words, preserving punctuation
        words = self._tokenize(text)
        corrected_words = []
        corrections_made = 0
        method_stats = {
            'exact': 0,
            'fuzzy': 0,
            'phonetic': 0,
            'context': 0
        }
        
        for word_data in words:
            word = word_data['word']
            word_clean = word_data['clean']
            
            # Skip short words
            if len(word_clean) < self.min_word_length:
                corrected_words.append(word)
                continue
            
            # Safety limit
            if corrections_made >= self.max_corrections_per_segment:
                corrected_words.append(word)
                continue
            
            # Try correction methods in order of priority
            corrected, method = self._correct_word(word_clean)
            
            if corrected and corrected != word_clean:
                # Preserve original punctuation
                corrected_with_punct = self._restore_punctuation(
                    corrected,
                    word,
                    word_clean
                )
                corrected_words.append(corrected_with_punct)
                corrections_made += 1
                method_stats[method] += 1
            else:
                corrected_words.append(word)
        
        # Reconstruct text
        corrected_text = ' '.join(corrected_words)
        
        corrected_segment = {
            **segment,
            'text': corrected_text
        }
        
        return corrected_segment, {
            'corrections': corrections_made,
            'methods': method_stats
        }
    
    def _tokenize(self, text: str) -> List[Dict[str, str]]:
        """
        Tokenize text into words with metadata
        
        Returns:
            List of dicts with 'word' (original) and 'clean' (without punct)
        """
        words = []
        for word in text.split():
            clean = re.sub(r'[^\w\'-]', '', word)
            words.append({
                'word': word,
                'clean': clean
            })
        return words
    
    def _correct_word(self, word: str) -> Tuple[Optional[str], str]:
        """
        Try to correct a single word using all methods
        
        Args:
            word: Word to correct (already cleaned)
            
        Returns:
            Tuple of (corrected_word or None, method_used)
        """
        word_lower = word.lower()
        
        # Method 1: Exact match (case-insensitive)
        if word_lower in self.term_lower:
            correct_case = self.term_lower[word_lower]
            if correct_case != word:
                return correct_case, 'exact'
        
        # Method 2: Fuzzy matching
        fuzzy_result = self._fuzzy_match(word_lower)
        if fuzzy_result:
            return fuzzy_result, 'fuzzy'
        
        # Method 3: Phonetic matching
        if self.phonetic_available:
            phonetic_result = self._phonetic_match(word)
            if phonetic_result:
                return phonetic_result, 'phonetic'
        
        return None, 'none'
    
    def _fuzzy_match(self, word_lower: str) -> Optional[str]:
        """
        Find best fuzzy match using Levenshtein distance
        
        Args:
            word_lower: Lowercase word to match
            
        Returns:
            Best matching term or None
        """
        best_match = None
        best_score = 0.0
        
        for term in self.terms_sorted:
            term_lower = term.lower()
            
            # Quick length filter
            len_diff = abs(len(word_lower) - len(term_lower))
            if len_diff > len(word_lower) * (1 - self.fuzzy_threshold):
                continue
            
            # Calculate similarity
            similarity = SequenceMatcher(None, word_lower, term_lower).ratio()
            
            if similarity > best_score:
                best_score = similarity
                best_match = term
        
        if best_score >= self.fuzzy_threshold:
            return best_match
        
        return None
    
    def _phonetic_match(self, word: str) -> Optional[str]:
        """
        Find match using phonetic similarity (sounds-like)
        
        Args:
            word: Word to match
            
        Returns:
            Best matching term or None
        """
        if not self.phonetic_available:
            return None
        
        try:
            word_metaphone = self.jellyfish.metaphone(word)
            
            # Check if metaphone matches any term
            if word_metaphone in self.metaphone_map:
                candidate = self.metaphone_map[word_metaphone]
                
                # Verify with fuzzy similarity (phonetic false positives)
                similarity = SequenceMatcher(
                    None,
                    word.lower(),
                    candidate.lower()
                ).ratio()
                
                if similarity >= self.phonetic_threshold:
                    return candidate
        except Exception as e:
            self.logger.debug(f"Phonetic matching error for '{word}': {e}")
        
        return None
    
    def _restore_punctuation(
        self,
        corrected: str,
        original: str,
        original_clean: str
    ) -> str:
        """
        Restore punctuation from original word to corrected word
        
        Args:
            corrected: Corrected word (clean)
            original: Original word (with punctuation)
            original_clean: Original word (cleaned)
            
        Returns:
            Corrected word with original punctuation
        """
        # Extract leading/trailing punctuation
        leading = ''
        trailing = ''
        
        # Leading punctuation
        i = 0
        while i < len(original) and not original[i].isalnum():
            leading += original[i]
            i += 1
        
        # Trailing punctuation
        i = len(original) - 1
        while i >= 0 and not original[i].isalnum():
            trailing = original[i] + trailing
            i -= 1
        
        return leading + corrected + trailing


class ContextAwareBiasCorrector(BiasCorrector):
    """
    Enhanced corrector with temporal context awareness
    
    Uses bias windows to apply scene-specific corrections
    """
    
    def __init__(
        self,
        bias_terms: List[str],
        bias_windows: Optional[List[Dict]] = None,
        **kwargs
    ):
        """
        Initialize context-aware corrector
        
        Args:
            bias_terms: Global bias terms
            bias_windows: List of temporal windows with specific terms
            **kwargs: Passed to BiasCorrector
        """
        super().__init__(bias_terms, **kwargs)
        self.bias_windows = bias_windows or []
        
        # Build temporal index
        self._build_temporal_index()
    
    def _build_temporal_index(self):
        """Build index for fast temporal lookups"""
        # Sort windows by start time
        self.windows_sorted = sorted(
            self.bias_windows,
            key=lambda w: w.get('start_time', 0)
        )
        
        self.logger.debug(f"Built temporal index with {len(self.windows_sorted)} windows")
    
    def correct_segments(
        self,
        segments: List[Dict]
    ) -> Tuple[List[Dict], Dict[str, int]]:
        """
        Apply corrections with temporal context awareness
        
        For each segment, finds applicable bias window and uses
        window-specific terms in addition to global terms.
        """
        corrected_segments = []
        stats = {
            'total_segments': len(segments),
            'corrected_segments': 0,
            'total_corrections': 0,
            'methods': {
                'exact': 0,
                'fuzzy': 0,
                'phonetic': 0,
                'context': 0
            }
        }
        
        for seg in segments:
            # Find applicable bias window
            seg_start = seg.get('start', 0)
            seg_end = seg.get('end', seg_start)
            seg_mid = (seg_start + seg_end) / 2
            
            context_terms = self._get_context_terms(seg_mid)
            
            # Temporarily extend bias terms with context
            if context_terms:
                original_terms = self.bias_terms
                self.bias_terms = list(set(self.bias_terms + context_terms))
                self._build_lookups()
            
            # Correct with context
            corrected_seg, seg_stats = self._correct_segment(seg)
            corrected_segments.append(corrected_seg)
            
            # Restore original terms
            if context_terms:
                self.bias_terms = original_terms
                self._build_lookups()
            
            # Update stats
            if seg_stats['corrections'] > 0:
                stats['corrected_segments'] += 1
                stats['total_corrections'] += seg_stats['corrections']
                for method, count in seg_stats['methods'].items():
                    stats['methods'][method] += count
        
        return corrected_segments, stats
    
    def _get_context_terms(self, timestamp: float) -> List[str]:
        """
        Get applicable bias terms for a given timestamp
        
        Args:
            timestamp: Time in seconds
            
        Returns:
            List of context-specific terms
        """
        context_terms = []
        
        for window in self.windows_sorted:
            start = window.get('start_time', 0)
            end = window.get('end_time', float('inf'))
            
            if start <= timestamp <= end:
                window_terms = window.get('bias_terms', [])
                context_terms.extend(window_terms)
        
        return context_terms
