#!/usr/bin/env python3
"""
Unified Glossary Manager - Single Source of Truth

Consolidates all glossary functionality with caching, learning,
and priority cascade resolution.

Compliance: DEVELOPMENT_STANDARDS.md
"""

# Standard library
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from collections import defaultdict
from datetime import datetime
import logging

# Local
from shared.logger import get_logger
logger = get_logger(__name__)


class UnifiedGlossaryManager:
    """
    Central glossary management system
    
    Features:
    - Priority cascade (film > TMDB > master > learned)
    - TMDB caching (per-film, configurable TTL)
    - Frequency-based learning (Phase 3)
    - Context-aware term selection
    - Multiple strategies (cascade, frequency, context, ML)
    
    Priority Cascade:
        1. Film-specific overrides (highest priority)
        2. TMDB glossary (cast/crew names)
        3. Master glossary (manual Hinglish terms)
        4. Learned terms (frequency-based)
    
    Usage:
        manager = UnifiedGlossaryManager(
            project_root=Path("/path/to/project"),
            film_title="3 Idiots",
            film_year=2009,
            tmdb_enrichment_path=Path("02_tmdb/enrichment.json"),
            enable_cache=True,
            enable_learning=True
        )
        
        # Load all sources
        stats = manager.load_all_sources()
        
        # Get term translation
        translation = manager.get_term("yaar", context="casual")
        
        # Apply to text
        result = manager.apply_to_text("Hey yaar!")
        
        # Track usage (for learning)
        manager.track_usage("yaar", "dude", success=True)
        
        # Get bias terms for ASR
        bias_terms = manager.get_bias_terms(max_terms=100)
    """
    
    def __init__(
        self,
        project_root: Path,
        film_title: Optional[str] = None,
        film_year: Optional[int] = None,
        tmdb_enrichment_path: Optional[Path] = None,
        enable_cache: bool = True,
        enable_learning: bool = False,
        strategy: str = 'cascade',
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize unified glossary manager
        
        Args:
            project_root: Project root directory
            film_title: Film title for film-specific glossaries
            film_year: Film year for cache lookup
            tmdb_enrichment_path: Path to TMDB enrichment.json
            enable_cache: Enable TMDB glossary caching
            enable_learning: Enable frequency-based learning
            strategy: Term selection strategy (cascade|frequency|context|ml)
            logger: Optional logger instance
        """
        self.project_root = Path(project_root)
        self.film_title = film_title
        self.film_year = film_year
        self.tmdb_enrichment_path = tmdb_enrichment_path
        self.enable_cache = enable_cache
        self.enable_learning = enable_learning
        self.strategy = strategy
        self.logger = logger or logging.getLogger(__name__)
        
        # Glossary sources (priority order)
        self.film_specific: Dict[str, List[str]] = {}
        self.tmdb_glossary: Dict[str, List[str]] = {}
        self.master_glossary: Dict[str, List[str]] = {}
        self.learned_terms: Dict[str, Dict[str, float]] = {}
        
        # Statistics
        self.stats = defaultdict(int)
        
        # Cache manager
        if enable_cache:
            from shared.glossary_cache import GlossaryCache
            self.cache = GlossaryCache(project_root, logger=logger)
        else:
            self.cache = None
        
        # Loaded flag
        self.loaded = False
    
    def load_all_sources(self) -> Dict[str, Any]:
        """
        Load all glossary sources with priority cascade
        
        Returns:
            Statistics dict with counts and cache info
        """
        if self.loaded:
            self.logger.warning("Glossary already loaded, skipping reload")
            return self._get_load_stats()
        
        self.logger.info("Loading unified glossary system...")
        
        stats = {
            'master_terms': 0,
            'tmdb_terms': 0,
            'film_terms': 0,
            'learned_terms': 0,
            'total_terms': 0,
            'cache_hit': False
        }
        
        # 1. Load master glossary (always)
        self._load_master_glossary()
        stats['master_terms'] = len(self.master_glossary)
        
        # 2. Load TMDB glossary (if available)
        if self.film_title and self.film_year:
            if self.enable_cache and self.cache:
                # Try cache first
                cached = self.cache.get_tmdb_glossary(self.film_title, self.film_year)
                if cached:
                    self.tmdb_glossary = cached
                    stats['cache_hit'] = True
                    self.logger.info(f"✓ Using cached TMDB glossary")
                else:
                    self._load_tmdb_glossary()
                    # Save to cache
                    if self.tmdb_glossary:
                        self.cache.save_tmdb_glossary(
                            self.film_title, 
                            self.film_year, 
                            self.tmdb_glossary
                        )
            else:
                self._load_tmdb_glossary()
            
            stats['tmdb_terms'] = len(self.tmdb_glossary)
        
        # 3. Load film-specific glossary (if exists)
        if self.film_title and self.film_year:
            self._load_film_specific_glossary()
            stats['film_terms'] = len(self.film_specific)
        
        # 4. Load learned terms (if enabled)
        if self.enable_learning:
            self._load_learned_terms()
            stats['learned_terms'] = len(self.learned_terms)
        
        # Calculate total unique terms
        all_terms = set()
        all_terms.update(self.master_glossary.keys())
        all_terms.update(self.tmdb_glossary.keys())
        all_terms.update(self.film_specific.keys())
        all_terms.update(self.learned_terms.keys())
        stats['total_terms'] = len(all_terms)
        
        # Add aliases for backwards compatibility
        stats['master_count'] = stats['master_terms']
        stats['tmdb_count'] = stats['tmdb_terms']
        stats['film_specific_count'] = stats['film_terms']
        stats['learned_count'] = stats['learned_terms']
        
        self.loaded = True
        self.logger.info(f"✓ Loaded {stats['total_terms']} unique terms")
        
        return stats
    
    def _load_master_glossary(self) -> None:
        """Load master Hinglish glossary from TSV"""
        master_path = self.project_root / "glossary" / "hinglish_master.tsv"
        
        if not master_path.exists():
            self.logger.warning(f"Master glossary not found: {master_path}")
            return
        
        try:
            # Try pandas first (preferred), fall back to manual parsing
            pandas_available = False
            try:
                import pandas as pd
                pandas_available = True
                df = pd.read_csv(master_path, sep='\t')
                
                for _, row in df.iterrows():
                    source = str(row['source']).strip()
                    translations = str(row['preferred_english']).split('|')
                    translations = [t.strip() for t in translations if t.strip()]
                    
                    if source and translations:
                        self.master_glossary[source] = translations
                        
            except ImportError:
                # Fallback: parse TSV manually without pandas
                self.logger.debug("Pandas not available, using manual TSV parsing")
                with open(master_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if len(lines) < 2:
                        return
                    
                    # Parse header to find column indices
                    header = lines[0].strip().split('\t')
                    try:
                        source_idx = header.index('source')
                        pref_idx = header.index('preferred_english')
                    except ValueError:
                        self.logger.error("Master glossary missing required columns: source, preferred_english", exc_info=True)
                        return
                    
                    # Parse data rows
                    for line in lines[1:]:
                        cols = line.strip().split('\t')
                        if len(cols) <= max(source_idx, pref_idx):
                            continue
                        
                        source = cols[source_idx].strip()
                        translations = cols[pref_idx].split('|')
                        translations = [t.strip() for t in translations if t.strip()]
                        
                        if source and translations:
                            self.master_glossary[source] = translations
            
            self.logger.debug(f"Loaded {len(self.master_glossary)} master terms")
            
        except ImportError:
            # This should not happen as we handle it above, but just in case
            self.logger.debug("Pandas not available")
        except Exception as e:
            self.logger.error(f"Error loading master glossary: {e}", exc_info=True)
    
    def _load_tmdb_glossary(self) -> None:
        """Load TMDB-generated glossary"""
        if not self.tmdb_enrichment_path or not self.tmdb_enrichment_path.exists():
            self.logger.debug("No TMDB enrichment file available")
            return
        
        try:
            with open(self.tmdb_enrichment_path, 'r', encoding='utf-8') as f:
                enrichment = json.load(f)
            
            # Extract cast names
            for cast_member in enrichment.get('cast', [])[:30]:  # Limit to top 30
                name = cast_member.get('name', '').strip()
                if name:
                    self.tmdb_glossary[name] = [name]
                
                # Character names
                character = cast_member.get('character', '').strip()
                if character:
                    # Clean character name
                    character = character.split('/')[0].strip()  # Take first if multiple
                    character = re.sub(r'\(.*?\)', '', character).strip()  # Remove parentheses
                    if character and character != name and len(character) > 1:
                        self.tmdb_glossary[character] = [character]
            
            # Extract crew names (directors, writers)
            for crew_member in enrichment.get('crew', []):
                if crew_member.get('job') in ['Director', 'Writer', 'Screenplay', 'Producer']:
                    name = crew_member.get('name', '').strip()
                    if name:
                        self.tmdb_glossary[name] = [name]
            
            self.logger.debug(f"Loaded {len(self.tmdb_glossary)} TMDB terms")
            
        except Exception as e:
            self.logger.error(f"Error loading TMDB glossary: {e}", exc_info=True)
    
    def _load_film_specific_glossary(self) -> None:
        """Load film-specific glossary overrides"""
        film_slug = self._get_film_slug()
        film_path = self.project_root / "glossary" / "films" / "popular" / f"{film_slug}.json"
        
        if not film_path.exists():
            self.logger.debug(f"No film-specific glossary for {film_slug}")
            return
        
        try:
            with open(film_path, 'r', encoding='utf-8') as f:
                film_data = json.load(f)
            
            # Handle both formats: {"terms": {...}} or direct {...}
            if 'terms' in film_data:
                terms = film_data['terms']
            else:
                terms = film_data
            
            # Convert to list format if needed
            for key, value in terms.items():
                if isinstance(value, str):
                    self.film_specific[key] = [value]
                elif isinstance(value, list):
                    self.film_specific[key] = value
            
            self.logger.debug(f"Loaded {len(self.film_specific)} film-specific terms")
            
        except Exception as e:
            self.logger.error(f"Error loading film-specific glossary: {e}", exc_info=True)
    
    def _load_learned_terms(self) -> None:
        """Load learned term frequencies"""
        if not self.film_title or not self.film_year:
            return
        
        if not self.cache:
            return
        
        try:
            self.learned_terms = self.cache.get_learned_terms(
                self.film_title,
                self.film_year
            )
            
            self.logger.debug(f"Loaded {len(self.learned_terms)} learned terms")
            
        except Exception as e:
            self.logger.error(f"Error loading learned terms: {e}", exc_info=True)
    
    def get_term(
        self,
        source_term: str,
        context: Optional[str] = None,
        strategy: Optional[str] = None
    ) -> Optional[str]:
        """
        Get best translation for term using priority cascade
        
        Args:
            source_term: Source term to translate
            context: Optional context (casual, formal, etc.)
            strategy: Override default strategy
            
        Returns:
            Best translation or None if not found
        """
        if not self.loaded:
            self.logger.warning("Glossary not loaded, call load_all_sources() first")
            return None
        
        strategy = strategy or self.strategy
        
        # Priority cascade
        if source_term in self.film_specific:
            translations = self.film_specific[source_term]
            self.stats['film_hits'] += 1
            return self._select_best_translation(
                source_term, translations, context, strategy
            )
        
        if source_term in self.tmdb_glossary:
            translations = self.tmdb_glossary[source_term]
            self.stats['tmdb_hits'] += 1
            return self._select_best_translation(
                source_term, translations, context, strategy
            )
        
        if source_term in self.master_glossary:
            translations = self.master_glossary[source_term]
            self.stats['master_hits'] += 1
            return self._select_best_translation(
                source_term, translations, context, strategy
            )
        
        # Check learned terms (lowest priority)
        if source_term in self.learned_terms:
            # Get most frequent translation
            best = max(
                self.learned_terms[source_term].items(),
                key=lambda x: x[1]
            )
            self.stats['learned_hits'] += 1
            return best[0]
        
        self.stats['misses'] += 1
        return None
    
    def _select_best_translation(
        self,
        source_term: str,
        translations: List[str],
        context: Optional[str],
        strategy: str
    ) -> str:
        """Select best translation based on strategy"""
        if not translations:
            return source_term
        
        if strategy == 'cascade' or strategy == 'first':
            # Return first option
            return translations[0]
        
        elif strategy == 'frequency' and self.enable_learning:
            # Use learned frequency
            if source_term in self.learned_terms:
                for trans in translations:
                    if trans in self.learned_terms[source_term]:
                        return trans
            return translations[0]
        
        elif strategy == 'context' and context:
            # Context-aware selection (future enhancement)
            # For now, fall back to first
            return translations[0]
        
        else:
            return translations[0]
    
    def apply_to_text(
        self,
        text: str,
        context: Optional[str] = None
    ) -> str:
        """
        Apply glossary to text
        
        Args:
            text: Input text
            context: Optional context hint
            
        Returns:
            Translated text
        """
        if not self.loaded:
            self.logger.warning("Glossary not loaded")
            return text
        
        # Simple word-by-word replacement
        words = text.split()
        result = []
        
        for word in words:
            # Strip punctuation for lookup
            clean_word = word.strip('.,!?;:"\'"()[]{}')
            translation = self.get_term(clean_word, context)
            
            if translation:
                # Preserve punctuation
                if word != clean_word:
                    prefix = word[:len(word) - len(word.lstrip('.,!?;:"\'"()[]{}'))]
                    suffix = word[len(word.rstrip('.,!?;:"\'"()[]{}')):]
                    result.append(f"{prefix}{translation}{suffix}")
                else:
                    result.append(translation)
            else:
                result.append(word)
        
        return ' '.join(result)
    
    def track_usage(
        self,
        source_term: str,
        translation: str,
        success: bool = True
    ) -> None:
        """
        Track term usage for learning (Phase 3)
        
        Args:
            source_term: Source term used
            translation: Translation chosen
            success: Whether translation was successful
        """
        if not self.enable_learning:
            return
        
        if source_term not in self.learned_terms:
            self.learned_terms[source_term] = {}
        
        if translation not in self.learned_terms[source_term]:
            self.learned_terms[source_term][translation] = 0.0
        
        # Increment frequency
        if success:
            self.learned_terms[source_term][translation] += 1.0
        else:
            # Penalize failed translations
            self.learned_terms[source_term][translation] = max(
                0.0,
                self.learned_terms[source_term][translation] - 0.5
            )
    
    def save_learned_terms(self) -> bool:
        """
        Persist learned terms to cache
        
        Returns:
            True if saved successfully
        """
        if not self.enable_learning or not self.cache:
            return False
        
        if not self.film_title or not self.film_year:
            return False
        
        try:
            self.cache.update_learned_terms(
                self.film_title,
                self.film_year,
                self.learned_terms
            )
            
            self.logger.debug(f"Saved {len(self.learned_terms)} learned terms")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving learned terms: {e}", exc_info=True)
            return False
    
    def get_bias_terms(self, max_terms: int = 100) -> List[str]:
        """
        Get terms for ASR biasing
        
        Args:
            max_terms: Maximum terms to return
            
        Returns:
            List of terms sorted by priority
        """
        if not self.loaded:
            self.logger.warning("Glossary not loaded")
            return []
        
        # Collect all unique terms
        terms = []
        
        # Priority: film-specific > TMDB > master
        terms.extend(self.film_specific.keys())
        terms.extend(self.tmdb_glossary.keys())
        terms.extend(self.master_glossary.keys())
        
        # Deduplicate while preserving order
        seen = set()
        unique_terms = []
        for term in terms:
            if term not in seen:
                seen.add(term)
                unique_terms.append(term)
        
        return unique_terms[:max_terms]
    
    def get_all_terms(self) -> Dict[str, str]:
        """
        Get all terms with their translations (first option)
        
        Returns:
            Dictionary of {source: translation}
        """
        if not self.loaded:
            return {}
        
        all_terms = {}
        
        # Priority cascade
        for source, translations in self.master_glossary.items():
            all_terms[source] = translations[0] if translations else source
        
        for source, translations in self.tmdb_glossary.items():
            all_terms[source] = translations[0] if translations else source
        
        for source, translations in self.film_specific.items():
            all_terms[source] = translations[0] if translations else source
        
        return all_terms
    
    def save_snapshot(self, output_path: Path) -> bool:
        """
        Save glossary snapshot for debugging
        
        Args:
            output_path: Path to save snapshot
            
        Returns:
            True if saved successfully
        """
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'film_title': self.film_title,
            'film_year': self.film_year,
            'loaded': self.loaded,
            'enable_cache': self.enable_cache,
            'enable_learning': self.enable_learning,
            'strategy': self.strategy,
            'statistics': {
                'master_terms': len(self.master_glossary),
                'tmdb_terms': len(self.tmdb_glossary),
                'film_specific_terms': len(self.film_specific),
                'learned_terms': len(self.learned_terms),
                'usage_stats': dict(self.stats)
            },
            'sample_terms': {
                'master': list(self.master_glossary.keys())[:10],
                'tmdb': list(self.tmdb_glossary.keys())[:10],
                'film': list(self.film_specific.keys())[:10],
            }
        }
        
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(snapshot, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            self.logger.error(f"Error saving snapshot: {e}", exc_info=True)
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get glossary statistics
        
        Returns:
            Statistics dictionary
        """
        total_hits = (
            self.stats['film_hits'] + 
            self.stats['tmdb_hits'] + 
            self.stats['master_hits'] + 
            self.stats['learned_hits']
        )
        total_requests = total_hits + self.stats['misses']
        
        hit_rate = (total_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'loaded': self.loaded,
            'sources': {
                'master': len(self.master_glossary),
                'tmdb': len(self.tmdb_glossary),
                'film_specific': len(self.film_specific),
                'learned': len(self.learned_terms)
            },
            'usage': {
                'film_hits': self.stats['film_hits'],
                'tmdb_hits': self.stats['tmdb_hits'],
                'master_hits': self.stats['master_hits'],
                'learned_hits': self.stats['learned_hits'],
                'misses': self.stats['misses'],
                'total_requests': total_requests,
                'hit_rate': round(hit_rate, 2)
            },
            'cache': self.cache.get_cache_statistics() if self.cache else None
        }
    
    def _get_film_slug(self) -> str:
        """Generate film slug for file paths"""
        if not self.film_title:
            return ""
        
        slug = self.film_title.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[\s_]+', '_', slug)
        
        if self.film_year:
            return f"{slug}_{self.film_year}"
        return slug
    
    def _get_load_stats(self) -> Dict[str, Any]:
        """Get current load statistics"""
        all_terms = set()
        all_terms.update(self.master_glossary.keys())
        all_terms.update(self.tmdb_glossary.keys())
        all_terms.update(self.film_specific.keys())
        all_terms.update(self.learned_terms.keys())
        
        return {
            'master_terms': len(self.master_glossary),
            'master_count': len(self.master_glossary),  # Alias for backwards compatibility
            'tmdb_terms': len(self.tmdb_glossary),
            'tmdb_count': len(self.tmdb_glossary),  # Alias
            'film_terms': len(self.film_specific),
            'film_specific_count': len(self.film_specific),  # Alias
            'learned_terms': len(self.learned_terms),
            'learned_count': len(self.learned_terms),  # Alias
            'total_terms': len(all_terms),
            'cache_hit': False
        }
