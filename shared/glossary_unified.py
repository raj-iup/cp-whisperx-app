#!/usr/bin/env python3
"""
Unified Glossary Manager - DEPRECATED

⚠️ DEPRECATION NOTICE:
This module is deprecated and will be removed in v2.0.0.
Use UnifiedGlossaryManager from shared.glossary_manager instead.

Migration Guide:
    Old:
        from shared.glossary_unified import UnifiedGlossary
        glossary = UnifiedGlossary(glossary_path=path, film_name=name)
    
    New:
        from shared.glossary_manager import UnifiedGlossaryManager
        manager = UnifiedGlossaryManager(
            project_root=project_root,
            film_title=title,
            film_year=year
        )
        manager.load_all_sources()

See shared/GLOSSARY_ARCHITECTURE.md for complete migration guide.

Combines:
- Master glossary (manual, authoritative)
- Film-specific terms (from prompts)
- Learned terms (from ASR/corrections)
- Cached terms (per-film optimizations)

Priority: Manual > Film-specific > Learned > Cached
"""

import warnings
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging
from collections import defaultdict
import pandas as pd

# Local
from shared.logger import get_logger
logger = get_logger(__name__)

# Issue deprecation warning when module is imported
warnings.warn(
    "shared.glossary_unified is deprecated and will be removed in v2.0.0. "
    "Use UnifiedGlossaryManager from shared.glossary_manager instead. "
    "See shared/GLOSSARY_ARCHITECTURE.md for migration guide.",
    DeprecationWarning,
    stacklevel=2
)


class UnifiedGlossary:
    """
    DEPRECATED: Single source of truth for glossary management
    
    ⚠️ This class is deprecated. Use UnifiedGlossaryManager from
    shared.glossary_manager instead.
    
    Manages all glossary sources with priority cascade:
    1. Film-specific overrides (highest priority)
    2. Master glossary (manual, authoritative)
    3. Learned terms (from usage)
    4. Cached terms (per-film)
    """
    
    def __init__(
        self,
        glossary_path: Optional[Path] = None,
        film_name: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
        enable_learning: bool = True
    ):
        """
        Initialize unified glossary
        
        DEPRECATED: Use UnifiedGlossaryManager instead.
        
        Args:
            glossary_path: Path to unified glossary TSV
            film_name: Film name for film-specific overrides
            logger: Optional logger
            enable_learning: Enable frequency-based learning
        """
        warnings.warn(
            "UnifiedGlossary is deprecated. Use UnifiedGlossaryManager from "
            "shared.glossary_manager instead.",
            DeprecationWarning,
            stacklevel=2
        )
        
        self.logger = logger or logging.getLogger(__name__)
        self.film_name = film_name
        self.enable_learning = enable_learning
        
        # Glossary storage
        self.master: Dict[str, Dict] = {}  # Main glossary
        self.film_terms: Dict[str, Dict] = {}  # Film-specific overrides
        self.learned: Dict[str, Dict] = {}  # Learned terms
        
        # Usage tracking
        self.usage_stats = defaultdict(lambda: defaultdict(int))
        self.context_stats = defaultdict(lambda: defaultdict(int))
        self.terms_applied = 0
        self.terms_skipped = 0
        
        # Load glossaries
        if glossary_path and glossary_path.exists():
            self._load_unified_glossary(glossary_path)
        
        # Load film-specific terms if available
        if film_name:
            self._load_film_specific(film_name)
        
        # Load learned terms if available
        if enable_learning:
            self._load_learned_terms()
    
    def _load_unified_glossary(self, path: Path):
        """Load unified glossary from TSV"""
        try:
            df = pd.read_csv(path, sep='\t')
            
            # Verify required columns
            required_cols = ['term', 'english']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                self.logger.error(f"Glossary missing required columns: {missing_cols}")
                return
            
            for idx, row in df.iterrows():
                try:
                    term = str(row['term']).lower().strip()
                    
                    # Skip empty terms
                    if not term or term == 'nan':
                        continue
                    
                    entry = {
                        'term': term,
                        'english': str(row['english']),
                        'alternatives': str(row.get('alternatives', '')).split('|') if pd.notna(row.get('alternatives')) else [],
                        'context': str(row.get('context', 'general')),
                        'confidence': float(row.get('confidence', 0.8)),
                        'source': str(row.get('source', 'unknown')),
                        'frequency': int(row.get('frequency', 0)),
                        'notes': str(row.get('notes', ''))
                    }
                    
                    # Store in master
                    self.master[term] = entry
                    
                except Exception as e:
                    self.logger.warning(f"Failed to load glossary row {idx}: {e}")
                    continue
            
            self.logger.info(f"Loaded unified glossary: {len(self.master)} terms from {path}")
            
        except Exception as e:
            self.logger.error(f"Failed to load unified glossary: {e}")
            import traceback
            self.logger.debug(f"Traceback: {traceback.format_exc()}")
    
    def _load_film_specific(self, film_name: str):
        """Load film-specific terms from prompt file"""
        # Try to find prompt file
        prompts_dir = Path(__file__).parent.parent / "glossary" / "prompts"
        
        # Try various name formats
        possible_names = [
            f"{film_name.lower().replace(' ', '_')}.txt",
            f"{film_name.lower().replace(' ', '-')}.txt",
        ]
        
        for name in possible_names:
            prompt_file = prompts_dir / name
            if prompt_file.exists():
                self._parse_prompt_file(prompt_file)
                return
        
        self.logger.debug(f"No film-specific prompt found for: {film_name}")
    
    def _parse_prompt_file(self, path: Path):
        """Parse film-specific prompt file for special terms"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for sacred terms (NEVER translate)
            sacred_pattern = r'"([^"]+)"\s*\(.*?NEVER\s+translate.*?\)'
            for match in re.finditer(sacred_pattern, content, re.IGNORECASE):
                term = match.group(1).lower()
                self.film_terms[term] = {
                    'term': term,
                    'english': match.group(1),  # Keep original
                    'alternatives': [],
                    'context': 'sacred',
                    'confidence': 1.0,
                    'source': f'film:{self.film_name}',
                    'notes': 'NEVER translate - signature phrase'
                }
            
            # Look for key terms with specific translations
            key_term_pattern = r'"([^"]+)"\s*→\s*"([^"]+)"'
            for match in re.finditer(key_term_pattern, content):
                term = match.group(1).lower()
                translation = match.group(2)
                self.film_terms[term] = {
                    'term': term,
                    'english': translation,
                    'alternatives': [],
                    'context': 'film-specific',
                    'confidence': 1.0,
                    'source': f'film:{self.film_name}',
                    'notes': f'Film-specific translation for {self.film_name}'
                }
            
            if self.film_terms:
                self.logger.info(f"Loaded {len(self.film_terms)} film-specific terms from {path}")
        
        except Exception as e:
            self.logger.error(f"Failed to parse prompt file: {e}")
    
    def _load_learned_terms(self):
        """Load learned terms from previous runs"""
        if not self.film_name:
            return
        
        learned_dir = Path(__file__).parent.parent / "glossary" / "glossary_learned"
        learned_file = learned_dir / f"{self.film_name}_learned.tsv"
        
        if not learned_file.exists():
            return
        
        try:
            df = pd.read_csv(learned_file, sep='\t')
            
            for _, row in df.iterrows():
                term = str(row['term']).lower().strip()
                
                entry = {
                    'term': term,
                    'english': str(row['english']),
                    'alternatives': str(row.get('alternatives', '')).split('|') if pd.notna(row.get('alternatives')) else [],
                    'context': str(row.get('context', 'learned')),
                    'confidence': float(row.get('confidence', 0.7)),
                    'source': str(row.get('source', 'learned')),
                    'frequency': int(row.get('frequency', 0)),
                    'notes': str(row.get('notes', ''))
                }
                
                # Store in learned
                self.learned[term] = entry
            
            self.logger.info(f"Loaded {len(self.learned)} learned terms from {learned_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to load learned terms: {e}")
    
    def get_translation(
        self,
        term: str,
        context: Optional[str] = None,
        alternatives: bool = False
    ) -> Optional[str]:
        """
        Get best translation for a term
        
        Args:
            term: Term to translate
            context: Optional context (formal/casual/emotional)
            alternatives: Return all alternatives
        
        Returns:
            Translation string or None if not found
        """
        term_lower = term.lower().strip()
        
        # Priority 1: Film-specific overrides
        if term_lower in self.film_terms:
            entry = self.film_terms[term_lower]
            self._track_usage(term_lower, entry['english'], 'film-specific')
            return entry['english']
        
        # Priority 2: Master glossary
        if term_lower in self.master:
            entry = self.master[term_lower]
            translation = self._select_by_context(entry, context) if context else entry['english']
            self._track_usage(term_lower, translation, 'master')
            return translation
        
        # Priority 3: Learned terms
        if term_lower in self.learned:
            entry = self.learned[term_lower]
            self._track_usage(term_lower, entry['english'], 'learned')
            return entry['english']
        
        # Not found
        return None
    
    def _select_by_context(self, entry: Dict, context: str) -> str:
        """Select best translation based on context"""
        # Get alternatives list
        alternatives_str = entry.get('alternatives', '')
        
        if not alternatives_str or pd.isna(alternatives_str):
            return entry['english']
        
        # Parse alternatives (pipe-separated)
        alternatives = str(alternatives_str).split('|') if alternatives_str else []
        
        if not alternatives:
            return entry['english']
        
        # Filter out empty alternatives
        alternatives = [alt.strip() for alt in alternatives if alt.strip()]
        
        if not alternatives:
            return entry['english']
        
        # Context-based selection
        entry_context = entry.get('context', '').lower()
        
        if context == 'formal':
            # For formal context, prefer:
            # - "sir/ma'am" over "hey"
            # - "brother" over "bro"
            # - Last option often more formal
            formal_keywords = ['sir', 'ma\'am', 'brother', 'formal']
            
            for alt in alternatives:
                if any(keyword in alt.lower() for keyword in formal_keywords):
                    return alt
            
            # Fallback to last alternative (often more formal)
            return alternatives[-1]
        
        elif context == 'casual':
            # For casual context, prefer:
            # - "dude" over "sir"
            # - "bro" over "brother"
            # - First option often more casual
            casual_keywords = ['dude', 'bro', 'man', 'hey', 'buddy']
            
            for alt in alternatives:
                if any(keyword in alt.lower() for keyword in casual_keywords):
                    return alt
            
            # Fallback to first alternative (often more casual)
            return alternatives[0]
        
        elif context == 'emotional':
            # For emotional context, prefer softer variants
            emotional_keywords = ['dear', 'love', 'heart', 'friend']
            
            for alt in alternatives:
                if any(keyword in alt.lower() for keyword in emotional_keywords):
                    return alt
        
        # Default to primary translation (first alternative or english field)
        return alternatives[0] if alternatives else entry['english']
    
    def _track_usage(self, term: str, translation: str, source: str):
        """Track term usage for learning"""
        self.usage_stats[term][translation] += 1
        self.terms_applied += 1
        
        # Update master glossary frequency if learning enabled
        if self.enable_learning and term in self.master:
            self.master[term]['frequency'] = self.master[term].get('frequency', 0) + 1
    
    def _track_context_usage(self, term: str, context: str, translation: str):
        """Track context-specific usage for adaptive learning"""
        if self.enable_learning:
            self.context_stats[term][f"{context}:{translation}"] += 1
    
    def apply(
        self,
        text: str,
        context: Optional[str] = None,
        case_sensitive: bool = False
    ) -> str:
        """
        Apply glossary to text
        
        Args:
            text: Input text
            context: Optional context hint
            case_sensitive: Whether to preserve case
        
        Returns:
            Text with glossary applied
        """
        result = text
        applied_count = 0
        
        # Sort terms by length (longest first to avoid partial matches)
        terms = sorted(self.master.keys(), key=len, reverse=True)
        
        for term in terms:
            # Check if term exists in text
            if case_sensitive:
                pattern = re.escape(term)
            else:
                pattern = re.escape(term)
                flags = re.IGNORECASE
            
            if re.search(pattern, result, flags=0 if case_sensitive else re.IGNORECASE):
                translation = self.get_translation(term, context)
                
                if translation:
                    # Replace with translation
                    if case_sensitive:
                        result = result.replace(term, translation)
                    else:
                        result = re.sub(
                            pattern,
                            translation,
                            result,
                            flags=re.IGNORECASE
                        )
                    applied_count += 1
        
        self.terms_applied += applied_count
        return result
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return {
            'total_terms': len(self.master),
            'film_specific': len(self.film_terms),
            'learned': len(self.learned),
            'terms_applied': self.terms_applied,
            'terms_skipped': self.terms_skipped,
            'most_used': dict(sorted(
                [(term, sum(translations.values()))
                 for term, translations in self.usage_stats.items()],
                key=lambda x: x[1],
                reverse=True
            )[:10])
        }
    
    def save_learned(self, output_path: Path):
        """Save learned terms for future use"""
        if not self.usage_stats:
            return
        
        # Convert usage stats to learned terms
        learned_data = []
        
        for term, translations in self.usage_stats.items():
            if term not in self.master and term not in self.film_terms:
                # Find most used translation
                best_translation = max(translations.items(), key=lambda x: x[1])
                
                learned_data.append({
                    'term': term,
                    'english': best_translation[0],
                    'alternatives': '|'.join(translations.keys()),
                    'context': 'learned',
                    'confidence': min(best_translation[1] / 10.0, 1.0),  # Normalize
                    'source': 'learned:usage',
                    'frequency': best_translation[1],
                    'notes': 'Auto-learned from usage'
                })
        
        if learned_data:
            df = pd.DataFrame(learned_data)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(output_path, sep='\t', index=False)
            self.logger.info(f"Saved {len(learned_data)} learned terms to {output_path}")


# Convenience function
def load_glossary(
    glossary_path: Optional[Path] = None,
    film_name: Optional[str] = None,
    logger: Optional[logging.Logger] = None
) -> UnifiedGlossary:
    """
    Load unified glossary
    
    Args:
        glossary_path: Path to unified glossary (default: glossary/unified_glossary.tsv)
        film_name: Film name for film-specific terms
        logger: Optional logger
    
    Returns:
        UnifiedGlossary instance
    """
    if glossary_path is None:
        # Default path
        glossary_path = Path(__file__).parent.parent / "glossary" / "unified_glossary.tsv"
    
    return UnifiedGlossary(glossary_path, film_name, logger)
