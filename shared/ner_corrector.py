#!/usr/bin/env python3
"""
NER-based Entity Correction - Phase 1 Implementation

Uses spaCy NER and TMDB metadata to correct entity recognition
errors in transcripts and translations.

Key features:
- Detects PERSON, ORG, GPE, LOC entities
- Corrects against TMDB character/cast/crew names
- Preserves entity casing and formatting
- Provides entity consistency across transcript
"""

# Standard library
import re
import logging
from typing import Dict, List, Set, Tuple, Optional
from pathlib import Path
from collections import Counter

# Third-party
import spacy

# Local
from shared.logger import get_logger
logger = get_logger(__name__)


class NERCorrector:
    """NER-based entity corrector"""
    
    def __init__(
        self,
        tmdb_metadata: Optional[Dict] = None,
        model_name: str = "en_core_web_sm",
        logger: logging.Logger=None
    ):
        """
        Initialize NER corrector
        
        Args:
            tmdb_metadata: Optional TMDB metadata dict
            model_name: spaCy model name
            logger: Optional logger instance
        """
        self.tmdb_metadata = tmdb_metadata or {}
        self.model_name = model_name
        self.logger = logger
        self.nlp = None
        
        # Build entity reference database from TMDB
        self.reference_entities = self._build_reference_entities()
        
        # Entity mapping cache
        self._entity_cache = {}
    
    def load_model(self) -> None:
        """Load spaCy NER model"""
        if self.nlp is not None:
            return
        
        try:
            if self.logger:
                self.logger.info(f"Loading spaCy model: {self.model_name}")
            
            self.nlp = spacy.load(self.model_name)
            
            if self.logger:
                self.logger.info("NER model loaded successfully")
                
        except OSError:
            if self.logger:
                self.logger.error(f"spaCy model not found: {self.model_name}", exc_info=True)
                self.logger.info(f"Install with: python -m spacy download {self.model_name}")
            raise
    
    def _build_reference_entities(self) -> Dict[str, Set[str]]:
        """
        Build reference entity database from TMDB
        
        Returns:
            Dict of entity_type -> set of names
        """
        entities = {
            'PERSON': set(),
            'CHARACTER': set(),
            'ORG': set(),
            'WORK_OF_ART': set()
        }
        
        if not self.tmdb_metadata:
            return entities
        
        # Add cast member names (real people)
        for cast_member in self.tmdb_metadata.get('cast', []):
            name = cast_member.get('name', '').strip()
            if name:
                entities['PERSON'].add(name)
                # Also add first/last name components
                parts = name.split()
                if len(parts) >= 2:
                    entities['PERSON'].add(parts[0])  # First name
                    entities['PERSON'].add(parts[-1])  # Last name
            
            # Add character names
            character = cast_member.get('character', '').strip()
            if character:
                # Clean character name (remove parentheticals)
                character = re.sub(r'\s*\([^)]*\)', '', character).strip()
                if character:
                    entities['CHARACTER'].add(character)
        
        # Add crew names
        for crew_member in self.tmdb_metadata.get('crew', []):
            name = crew_member.get('name', '').strip()
            if name:
                entities['PERSON'].add(name)
        
        # Add movie title
        title = self.tmdb_metadata.get('title', '').strip()
        if title:
            entities['WORK_OF_ART'].add(title)
        
        if self.logger:
            self.logger.debug(f"Built reference entities:")
            self.logger.debug(f"  PERSON: {len(entities['PERSON'])}")
            self.logger.debug(f"  CHARACTER: {len(entities['CHARACTER'])}")
            self.logger.debug(f"  WORK_OF_ART: {len(entities['WORK_OF_ART'])}")
        
        return entities
    
    def extract_entities(self, text: str) -> List[Dict]:
        """
        Extract named entities from text using spaCy
        
        Args:
            text: Input text
        
        Returns:
            List of entity dicts with text, label, start, end
        """
        if self.nlp is None:
            self.load_model()
        
        doc = self.nlp(text)
        
        entities = []
        for ent in doc.ents:
            # Filter to relevant entity types
            if ent.label_ in ['PERSON', 'ORG', 'GPE', 'LOC', 'WORK_OF_ART', 'FAC']:
                entities.append({
                    'text': ent.text,
                    'label': ent.label_,
                    'start': ent.start_char,
                    'end': ent.end_char,
                    'confidence': 1.0  # spaCy doesn't provide confidence
                })
        
        return entities
    
    def correct_entity(
        self,
        entity_text: str,
        entity_type: str,
        context: str = ""
    ) -> str:
        """
        Correct entity text against TMDB reference
        
        Args:
            entity_text: Entity text to correct
            entity_type: Entity type (PERSON, ORG, etc.)
            context: Optional surrounding context
        
        Returns:
            Corrected entity text
        """
        # Check cache
        cache_key = f"{entity_text}_{entity_type}"
        if cache_key in self._entity_cache:
            return self._entity_cache[cache_key]
        
        corrected = entity_text
        
        # Map entity types
        lookup_types = []
        if entity_type in ['PERSON']:
            lookup_types = ['PERSON', 'CHARACTER']
        elif entity_type in ['ORG', 'GPE', 'LOC']:
            lookup_types = ['ORG']
        elif entity_type in ['WORK_OF_ART']:
            lookup_types = ['WORK_OF_ART']
        
        # Try exact match first
        for lookup_type in lookup_types:
            if entity_text in self.reference_entities.get(lookup_type, set()):
                corrected = entity_text
                self._entity_cache[cache_key] = corrected
                return corrected
        
        # Try case-insensitive match
        entity_lower = entity_text.lower()
        for lookup_type in lookup_types:
            for ref_entity in self.reference_entities.get(lookup_type, set()):
                if ref_entity.lower() == entity_lower:
                    corrected = ref_entity  # Use reference casing
                    self._entity_cache[cache_key] = corrected
                    return corrected
        
        # Try fuzzy match (contains or is contained)
        best_match = None
        best_score = 0
        
        for lookup_type in lookup_types:
            for ref_entity in self.reference_entities.get(lookup_type, set()):
                ref_lower = ref_entity.lower()
                
                # Check if entity is part of reference
                if entity_lower in ref_lower:
                    score = len(entity_lower) / len(ref_lower)
                    if score > best_score and score > 0.5:
                        best_score = score
                        best_match = ref_entity
                
                # Check if reference is part of entity
                elif ref_lower in entity_lower:
                    score = len(ref_lower) / len(entity_lower)
                    if score > best_score and score > 0.5:
                        best_score = score
                        best_match = ref_entity
        
        if best_match:
            corrected = best_match
        
        self._entity_cache[cache_key] = corrected
        return corrected
    
    def correct_text(self, text: str, preserve_case: bool = True) -> str:
        """
        Correct all entities in text
        
        Args:
            text: Input text
            preserve_case: Preserve original casing where possible
        
        Returns:
            Corrected text
        """
        entities = self.extract_entities(text)
        
        if not entities:
            return text
        
        # Sort entities by position (reverse to maintain offsets)
        entities.sort(key=lambda e: e['start'], reverse=True)
        
        corrected_text = text
        corrections_made = 0
        
        for entity in entities:
            original = entity['text']
            corrected = self.correct_entity(
                original,
                entity['label'],
                context=text[max(0, entity['start']-50):entity['end']+50]
            )
            
            if corrected != original:
                # Replace in text
                before = corrected_text[:entity['start']]
                after = corrected_text[entity['end']:]
                corrected_text = before + corrected + after
                corrections_made += 1
                
                if self.logger:
                    self.logger.debug(f"Corrected: '{original}' -> '{corrected}'")
        
        if self.logger and corrections_made > 0:
            self.logger.info(f"Made {corrections_made} entity corrections")
        
        return corrected_text
    
    def get_entity_statistics(self, text: str) -> Dict[str, int]:
        """
        Get entity statistics for text
        
        Args:
            text: Input text
        
        Returns:
            Dict with entity counts by type
        """
        entities = self.extract_entities(text)
        
        stats = Counter()
        for entity in entities:
            stats[entity['label']] += 1
        
        return dict(stats)
    
    def validate_entities(self, text: str) -> List[Dict]:
        """
        Validate entities against TMDB reference
        
        Args:
            text: Input text
        
        Returns:
            List of validation results with original, suggested, confidence
        """
        entities = self.extract_entities(text)
        
        validations = []
        for entity in entities:
            original = entity['text']
            corrected = self.correct_entity(original, entity['label'])
            
            validation = {
                'original': original,
                'suggested': corrected,
                'type': entity['label'],
                'needs_correction': corrected != original,
                'confidence': 1.0 if corrected == original else 0.8
            }
            validations.append(validation)
        
        return validations
