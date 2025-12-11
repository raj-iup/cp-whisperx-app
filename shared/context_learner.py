#!/usr/bin/env python3
"""
Context Learning Module - Learn from Historical Jobs

This module implements context learning capabilities that improve over time by
analyzing patterns from historical jobs.

Key Features:
- Character name extraction and learning
- Cultural term pattern detection
- Translation memory building
- Consistency scoring
- Auto-glossary generation

Architecture Decision: AD-015 (ML-Based Adaptive Optimization) - Task #17
"""

# Standard library
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any

# Local
from shared.logger import get_logger

logger = get_logger(__name__)


@dataclass
class LearnedTerm:
    """
    A term learned from historical jobs.
    
    Attributes:
        term: The term itself (e.g., "Meenu", "arey yaar")
        frequency: Number of times seen
        contexts: Example contexts where term appeared
        category: Type of term (character_name, cultural_term, technical_term)
        confidence: Confidence score (0-1)
        first_seen: ISO timestamp when first encountered
        last_seen: ISO timestamp when last encountered
    """
    term: str
    frequency: int
    contexts: List[str]
    category: str
    confidence: float
    first_seen: str
    last_seen: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LearnedTerm':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class TranslationMemoryEntry:
    """
    A translation pair learned from historical jobs.
    
    Attributes:
        source: Source text
        target: Target text
        source_lang: Source language code
        target_lang: Target language code
        frequency: Number of times this translation was used
        confidence: Confidence score (0-1)
        contexts: Example contexts where this appeared
        last_used: ISO timestamp when last used
    """
    source: str
    target: str
    source_lang: str
    target_lang: str
    frequency: int
    confidence: float
    contexts: List[str]
    last_used: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TranslationMemoryEntry':
        """Create from dictionary."""
        return cls(**data)


class ContextLearner:
    """
    Learn patterns from historical jobs to improve future processing.
    
    This class analyzes completed jobs to extract:
    - Character names from TMDB metadata and subtitles
    - Cultural terms that appear frequently
    - Translation patterns for consistency
    - Named entities (people, places, organizations)
    
    Example:
        learner = ContextLearner()
        
        # Analyze all historical jobs
        learner.learn_from_history()
        
        # Get learned terms for a language
        terms = learner.get_learned_terms("hi")
        
        # Get translation memory
        memory = learner.get_translation_memory("hi", "en")
    """
    
    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        min_frequency: int = 3,
        min_confidence: float = 0.6
    ):
        """
        Initialize context learner.
        
        Args:
            cache_dir: Directory to store learned knowledge
            min_frequency: Minimum times term must appear to be learned
            min_confidence: Minimum confidence to include term
        """
        self.cache_dir = cache_dir or Path.home() / ".cp-whisperx" / "context"
        self.min_frequency = min_frequency
        self.min_confidence = min_confidence
        
        # Storage
        self.learned_terms: Dict[str, Dict[str, LearnedTerm]] = defaultdict(dict)  # lang -> term -> LearnedTerm
        self.translation_memory: Dict[Tuple[str, str], Dict[str, TranslationMemoryEntry]] = {}  # (src_lang, tgt_lang) -> source -> Entry
        
        # Load existing knowledge
        self._load_knowledge()
    
    def _load_knowledge(self) -> None:
        """Load previously learned knowledge from disk."""
        try:
            # Load learned terms
            terms_file = self.cache_dir / "learned_terms.json"
            if terms_file.exists():
                with open(terms_file) as f:
                    data = json.load(f)
                    for lang, terms in data.items():
                        for term_str, term_data in terms.items():
                            self.learned_terms[lang][term_str] = LearnedTerm.from_dict(term_data)
                
                logger.info(f"📚 Loaded {sum(len(t) for t in self.learned_terms.values())} learned terms")
            
            # Load translation memory
            tm_file = self.cache_dir / "translation_memory.json"
            if tm_file.exists():
                with open(tm_file) as f:
                    data = json.load(f)
                    for lang_pair_str, translations in data.items():
                        src_lang, tgt_lang = lang_pair_str.split("→")
                        self.translation_memory[(src_lang, tgt_lang)] = {}
                        for source, entry_data in translations.items():
                            self.translation_memory[(src_lang, tgt_lang)][source] = \
                                TranslationMemoryEntry.from_dict(entry_data)
                
                logger.info(f"📚 Loaded {sum(len(t) for t in self.translation_memory.values())} translation pairs")
        
        except Exception as e:
            logger.warning(f"Failed to load previous knowledge: {e}")
    
    def _save_knowledge(self) -> None:
        """Save learned knowledge to disk."""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            
            # Save learned terms
            terms_file = self.cache_dir / "learned_terms.json"
            terms_data = {
                lang: {term: learned.to_dict() for term, learned in terms.items()}
                for lang, terms in self.learned_terms.items()
            }
            with open(terms_file, 'w') as f:
                json.dump(terms_data, f, indent=2)
            
            # Save translation memory
            tm_file = self.cache_dir / "translation_memory.json"
            tm_data = {
                f"{src_lang}→{tgt_lang}": {
                    source: entry.to_dict()
                    for source, entry in translations.items()
                }
                for (src_lang, tgt_lang), translations in self.translation_memory.items()
            }
            with open(tm_file, 'w') as f:
                json.dump(tm_data, f, indent=2)
            
            logger.info("✅ Saved learned knowledge to disk")
        
        except Exception as e:
            logger.error(f"Failed to save knowledge: {e}", exc_info=True)
    
    def learn_from_job(self, job_dir: Path) -> Dict[str, int]:
        """
        Learn from a single completed job.
        
        Args:
            job_dir: Path to job directory
        
        Returns:
            Dictionary with counts of learned items
        """
        stats = {
            "character_names": 0,
            "cultural_terms": 0,
            "translations": 0,
            "named_entities": 0
        }
        
        try:
            # Learn from TMDB metadata (character names)
            tmdb_manifest = job_dir / "02_tmdb" / "stage_manifest.json"
            if tmdb_manifest.exists():
                stats["character_names"] += self._learn_from_tmdb(tmdb_manifest)
            
            # Learn from glossary (cultural terms, names)
            glossary_file = job_dir / "03_glossary_load" / "glossary.json"
            if glossary_file.exists():
                stats["cultural_terms"] += self._learn_from_glossary(glossary_file)
            
            # Learn from translations (translation memory)
            translation_dir = job_dir / "10_translation"
            if translation_dir.exists():
                stats["translations"] += self._learn_from_translations(translation_dir)
            
            # Learn from subtitles (named entities, patterns)
            subtitle_dir = job_dir / "11_subtitle_generation"
            if subtitle_dir.exists():
                stats["named_entities"] += self._learn_from_subtitles(subtitle_dir)
            
            logger.debug(f"Learned from {job_dir.name}: {stats}")
            return stats
        
        except Exception as e:
            logger.debug(f"Failed to learn from {job_dir.name}: {e}")
            return stats
    
    def _learn_from_tmdb(self, manifest_path: Path) -> int:
        """Learn character names from TMDB metadata."""
        count = 0
        try:
            with open(manifest_path) as f:
                manifest = json.load(f)
            
            # Extract character names from metadata
            for output in manifest.get("outputs", []):
                if output.get("key") == "tmdb_metadata":
                    metadata_file = manifest_path.parent / output["filename"]
                    if metadata_file.exists():
                        with open(metadata_file) as f:
                            tmdb_data = json.load(f)
                        
                        # Extract character names from cast
                        for cast_member in tmdb_data.get("cast", []):
                            character = cast_member.get("character", "")
                            if character and len(character) > 1:
                                # Detect language (simplified - assume Hindi for Bollywood)
                                lang = "hi"
                                self._add_learned_term(
                                    lang=lang,
                                    term=character,
                                    category="character_name",
                                    context=f"TMDB: {tmdb_data.get('title', 'Unknown')}"
                                )
                                count += 1
        
        except Exception as e:
            logger.debug(f"Failed to learn from TMDB: {e}")
        
        return count
    
    def _learn_from_glossary(self, glossary_path: Path) -> int:
        """Learn cultural terms from glossary."""
        count = 0
        try:
            with open(glossary_path) as f:
                glossary = json.load(f)
            
            # Extract terms from glossary
            for entry in glossary.get("entries", []):
                term = entry.get("term", "")
                category = entry.get("category", "cultural_term")
                lang = entry.get("language", "hi")
                
                if term and len(term) > 1:
                    self._add_learned_term(
                        lang=lang,
                        term=term,
                        category=category,
                        context=f"Glossary: {entry.get('meaning', '')}"
                    )
                    count += 1
        
        except Exception as e:
            logger.debug(f"Failed to learn from glossary: {e}")
        
        return count
    
    def _learn_from_translations(self, translation_dir: Path) -> int:
        """Learn translation pairs from translation stage."""
        count = 0
        try:
            # Find translation manifest
            manifest_path = translation_dir / "stage_manifest.json"
            if not manifest_path.exists():
                return 0
            
            with open(manifest_path) as f:
                manifest = json.load(f)
            
            # Get source and target languages
            config = manifest.get("config", {})
            src_lang = config.get("source_language", "hi")
            tgt_lang = config.get("target_language", "en")
            
            # Find translated segments
            for output in manifest.get("outputs", []):
                if "segments" in output.get("key", ""):
                    segments_file = translation_dir / output["filename"]
                    if segments_file.exists():
                        with open(segments_file) as f:
                            segments = json.load(f)
                        
                        # Extract translation pairs
                        for segment in segments.get("segments", []):
                            source_text = segment.get("text", "")
                            translated_text = segment.get("translated_text", "")
                            
                            if source_text and translated_text:
                                self._add_translation_memory(
                                    source=source_text,
                                    target=translated_text,
                                    src_lang=src_lang,
                                    tgt_lang=tgt_lang,
                                    context=f"Segment {segment.get('id', 0)}"
                                )
                                count += 1
        
        except Exception as e:
            logger.debug(f"Failed to learn from translations: {e}")
        
        return count
    
    def _learn_from_subtitles(self, subtitle_dir: Path) -> int:
        """Learn named entities from subtitles."""
        count = 0
        try:
            # Find subtitle files
            for srt_file in subtitle_dir.glob("*.srt"):
                # Extract proper nouns (capitalized words)
                with open(srt_file, encoding='utf-8') as f:
                    content = f.read()
                
                # Simple named entity extraction (capitalized words)
                proper_nouns = re.findall(r'\b[A-Z][a-z]+\b', content)
                
                # Count frequency
                noun_counts = Counter(proper_nouns)
                
                # Learn frequent proper nouns
                for noun, freq in noun_counts.items():
                    if freq >= self.min_frequency:
                        lang = "en"  # Assume English subtitle file
                        self._add_learned_term(
                            lang=lang,
                            term=noun,
                            category="named_entity",
                            context=f"Subtitle: {srt_file.name}"
                        )
                        count += 1
        
        except Exception as e:
            logger.debug(f"Failed to learn from subtitles: {e}")
        
        return count
    
    def _add_learned_term(
        self,
        lang: str,
        term: str,
        category: str,
        context: str
    ) -> None:
        """Add or update a learned term."""
        term_clean = term.strip()
        if not term_clean:
            return
        
        now = datetime.now().isoformat()
        
        if term_clean in self.learned_terms[lang]:
            # Update existing
            learned = self.learned_terms[lang][term_clean]
            learned.frequency += 1
            learned.last_seen = now
            if context not in learned.contexts:
                learned.contexts.append(context)
                if len(learned.contexts) > 10:  # Keep last 10
                    learned.contexts = learned.contexts[-10:]
            
            # Update confidence based on frequency
            learned.confidence = min(1.0, learned.frequency / 10.0)
        else:
            # Create new
            self.learned_terms[lang][term_clean] = LearnedTerm(
                term=term_clean,
                frequency=1,
                contexts=[context],
                category=category,
                confidence=0.1,
                first_seen=now,
                last_seen=now
            )
    
    def _add_translation_memory(
        self,
        source: str,
        target: str,
        src_lang: str,
        tgt_lang: str,
        context: str
    ) -> None:
        """Add or update translation memory entry."""
        source_clean = source.strip()
        target_clean = target.strip()
        
        if not source_clean or not target_clean:
            return
        
        lang_pair = (src_lang, tgt_lang)
        if lang_pair not in self.translation_memory:
            self.translation_memory[lang_pair] = {}
        
        now = datetime.now().isoformat()
        
        if source_clean in self.translation_memory[lang_pair]:
            # Update existing
            entry = self.translation_memory[lang_pair][source_clean]
            entry.frequency += 1
            entry.last_used = now
            if context not in entry.contexts:
                entry.contexts.append(context)
                if len(entry.contexts) > 5:
                    entry.contexts = entry.contexts[-5:]
            
            # Update confidence
            entry.confidence = min(1.0, entry.frequency / 5.0)
        else:
            # Create new
            self.translation_memory[lang_pair][source_clean] = TranslationMemoryEntry(
                source=source_clean,
                target=target_clean,
                source_lang=src_lang,
                target_lang=tgt_lang,
                frequency=1,
                confidence=0.2,
                contexts=[context],
                last_used=now
            )
    
    def learn_from_history(self, jobs_dir: Path = None) -> Dict[str, int]:
        """
        Learn from all historical jobs.
        
        Args:
            jobs_dir: Root directory containing job subdirectories
        
        Returns:
            Dictionary with total counts
        """
        if jobs_dir is None:
            # Default to project out/ directory
            import sys
            project_root = Path(__file__).parent.parent
            jobs_dir = project_root / "out"
        
        if not jobs_dir.exists():
            logger.warning(f"Jobs directory not found: {jobs_dir}")
            return {}
        
        total_stats = defaultdict(int)
        jobs_processed = 0
        
        logger.info(f"📚 Learning from historical jobs in {jobs_dir}...")
        
        # Scan all job directories
        for date_dir in jobs_dir.iterdir():
            if not date_dir.is_dir():
                continue
            
            for user_dir in date_dir.iterdir():
                if not user_dir.is_dir():
                    continue
                
                for job_dir in user_dir.iterdir():
                    if not job_dir.is_dir() or not job_dir.name.startswith("job-"):
                        continue
                    
                    # Learn from this job
                    stats = self.learn_from_job(job_dir)
                    for key, count in stats.items():
                        total_stats[key] += count
                    jobs_processed += 1
        
        # Save learned knowledge
        self._save_knowledge()
        
        logger.info(f"✅ Learned from {jobs_processed} jobs:")
        logger.info(f"  • Character names: {total_stats['character_names']}")
        logger.info(f"  • Cultural terms: {total_stats['cultural_terms']}")
        logger.info(f"  • Translation pairs: {total_stats['translations']}")
        logger.info(f"  • Named entities: {total_stats['named_entities']}")
        
        return dict(total_stats)
    
    def get_learned_terms(
        self,
        lang: str,
        category: Optional[str] = None,
        min_confidence: Optional[float] = None
    ) -> List[LearnedTerm]:
        """
        Get learned terms for a language.
        
        Args:
            lang: Language code
            category: Filter by category (optional)
            min_confidence: Minimum confidence threshold (optional)
        
        Returns:
            List of learned terms
        """
        terms = list(self.learned_terms.get(lang, {}).values())
        
        # Apply filters
        if category:
            terms = [t for t in terms if t.category == category]
        
        if min_confidence is None:
            min_confidence = self.min_confidence
        
        terms = [t for t in terms if t.confidence >= min_confidence]
        
        # Sort by confidence descending
        terms.sort(key=lambda t: t.confidence, reverse=True)
        
        return terms
    
    def get_translation_memory(
        self,
        src_lang: str,
        tgt_lang: str,
        min_confidence: Optional[float] = None
    ) -> List[TranslationMemoryEntry]:
        """
        Get translation memory for language pair.
        
        Args:
            src_lang: Source language
            tgt_lang: Target language
            min_confidence: Minimum confidence threshold (optional)
        
        Returns:
            List of translation memory entries
        """
        lang_pair = (src_lang, tgt_lang)
        entries = list(self.translation_memory.get(lang_pair, {}).values())
        
        if min_confidence is None:
            min_confidence = self.min_confidence
        
        entries = [e for e in entries if e.confidence >= min_confidence]
        
        # Sort by confidence descending
        entries.sort(key=lambda e: e.confidence, reverse=True)
        
        return entries
    
    def generate_auto_glossary(
        self,
        lang: str,
        min_confidence: float = 0.7
    ) -> List[Dict[str, str]]:
        """
        Generate auto-glossary from learned terms.
        
        Args:
            lang: Language code
            min_confidence: Minimum confidence for inclusion
        
        Returns:
            List of glossary entries
        """
        terms = self.get_learned_terms(lang, min_confidence=min_confidence)
        
        glossary = []
        for term in terms:
            entry = {
                "term": term.term,
                "category": term.category,
                "frequency": term.frequency,
                "confidence": term.confidence,
                "contexts": term.contexts[:3],  # Include sample contexts
            }
            glossary.append(entry)
        
        return glossary


def get_context_learner() -> ContextLearner:
    """
    Get singleton instance of context learner.
    
    Returns:
        ContextLearner instance
    """
    global _context_learner_instance
    
    if '_context_learner_instance' not in globals():
        _context_learner_instance = ContextLearner()
    
    return _context_learner_instance
