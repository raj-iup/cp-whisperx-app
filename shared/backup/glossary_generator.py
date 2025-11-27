#!/usr/bin/env python3
"""
Glossary Generator - Phase 1 Implementation

Generates glossaries from TMDB metadata for use in ASR biasing
and translation consistency.

Features:
- Auto-generates glossaries from TMDB cast/crew
- Creates source-to-target mappings
- Supports multiple output formats (JSON, YAML, CSV)
- Handles character name variations
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Set, Optional
from collections import defaultdict


class GlossaryGenerator:
    """Generate glossaries from TMDB metadata"""
    
    def __init__(
        self,
        tmdb_metadata: Optional[Dict] = None,
        logger=None
    ):
        """
        Initialize glossary generator
        
        Args:
            tmdb_metadata: TMDB metadata dict
            logger: Optional logger instance
        """
        self.tmdb_metadata = tmdb_metadata or {}
        self.logger = logger
        self.glossary = defaultdict(set)
    
    def generate(
        self,
        include_cast: bool = True,
        include_crew: bool = True,
        include_characters: bool = True,
        include_title: bool = True,
        max_cast: int = 20,
        max_crew: int = 10
    ) -> Dict[str, List[str]]:
        """
        Generate glossary from TMDB metadata
        
        Args:
            include_cast: Include cast member names
            include_crew: Include crew member names
            include_characters: Include character names
            include_title: Include movie title
            max_cast: Maximum cast members to include
            max_crew: Maximum crew members to include
        
        Returns:
            Glossary dict with source -> [targets]
        """
        glossary = defaultdict(list)
        
        if self.logger:
            self.logger.info("Generating glossary from TMDB metadata")
        
        # Add movie title
        if include_title:
            title = self.tmdb_metadata.get('title', '').strip()
            if title:
                glossary[title] = [title]
                if self.logger:
                    self.logger.debug(f"Added title: {title}")
        
        # Add cast members
        if include_cast:
            cast = self.tmdb_metadata.get('cast', [])[:max_cast]
            for member in cast:
                name = member.get('name', '').strip()
                if name:
                    # Add full name
                    glossary[name] = [name]
                    
                    # Add character name if available
                    if include_characters:
                        character = member.get('character', '').strip()
                        if character:
                            # Clean character name
                            character = self._clean_character_name(character)
                            if character:
                                glossary[character] = [character]
                                # Link character to actor
                                glossary[f"{character} (character)"] = [name]
            
            if self.logger:
                self.logger.debug(f"Added {len(cast)} cast members")
        
        # Add crew members
        if include_crew:
            crew = self.tmdb_metadata.get('crew', [])[:max_crew]
            important_roles = [
                'Director', 'Writer', 'Screenplay', 'Producer',
                'Music', 'Original Music Composer', 'Cinematography'
            ]
            
            added = 0
            for member in crew:
                if member.get('job') in important_roles:
                    name = member.get('name', '').strip()
                    if name:
                        glossary[name] = [name]
                        added += 1
            
            if self.logger:
                self.logger.debug(f"Added {added} crew members")
        
        # Convert defaultdict to regular dict
        result = {k: list(v) if isinstance(v, set) else v for k, v in glossary.items()}
        
        if self.logger:
            self.logger.info(f"Generated glossary with {len(result)} entries")
        
        return result
    
    def generate_for_asr(
        self,
        include_name_variations: bool = True
    ) -> List[str]:
        """
        Generate glossary for ASR biasing (flat list of terms)
        
        Args:
            include_name_variations: Include first/last name variations
        
        Returns:
            List of terms for ASR biasing
        """
        terms = set()
        
        # Add all names
        for member in self.tmdb_metadata.get('cast', [])[:20]:
            name = member.get('name', '').strip()
            if name:
                terms.add(name)
                
                if include_name_variations:
                    # Add name parts
                    parts = name.split()
                    if len(parts) >= 2:
                        terms.add(parts[0])  # First name
                        terms.add(parts[-1])  # Last name
            
            # Add character names
            character = member.get('character', '').strip()
            if character:
                character = self._clean_character_name(character)
                if character:
                    terms.add(character)
        
        # Add crew names
        for member in self.tmdb_metadata.get('crew', [])[:10]:
            name = member.get('name', '').strip()
            if name:
                terms.add(name)
        
        # Add title
        title = self.tmdb_metadata.get('title', '').strip()
        if title:
            terms.add(title)
        
        result = sorted(list(terms))
        
        if self.logger:
            self.logger.info(f"Generated ASR glossary with {len(result)} terms")
        
        return result
    
    def generate_for_translation(
        self,
        source_lang: str = "en",
        target_lang: str = "hi"
    ) -> Dict[str, str]:
        """
        Generate glossary for translation (1-to-1 mappings)
        
        For entity preservation, maps names to themselves.
        
        Args:
            source_lang: Source language code
            target_lang: Target language code
        
        Returns:
            Dict of source -> target mappings
        """
        mappings = {}
        
        # Add all entity names (preserve as-is in translation)
        for member in self.tmdb_metadata.get('cast', [])[:20]:
            name = member.get('name', '').strip()
            if name:
                mappings[name] = name  # Don't translate names
            
            character = member.get('character', '').strip()
            if character:
                character = self._clean_character_name(character)
                if character:
                    mappings[character] = character
        
        for member in self.tmdb_metadata.get('crew', [])[:10]:
            name = member.get('name', '').strip()
            if name:
                mappings[name] = name
        
        # Add title
        title = self.tmdb_metadata.get('title', '').strip()
        if title:
            mappings[title] = title
        
        if self.logger:
            self.logger.info(f"Generated translation glossary with {len(mappings)} mappings")
        
        return mappings
    
    def _clean_character_name(self, character: str) -> str:
        """
        Clean character name from TMDB format
        
        Removes:
        - Parentheticals like (voice), (uncredited)
        - Extra whitespace
        - Special characters
        
        Args:
            character: Raw character name
        
        Returns:
            Cleaned character name
        """
        import re
        
        # Remove parentheticals
        character = re.sub(r'\s*\([^)]*\)', '', character)
        
        # Remove bracketed info
        character = re.sub(r'\s*\[[^\]]*\]', '', character)
        
        # Remove "as Character" format
        character = re.sub(r'\s+as\s+.*$', '', character, flags=re.IGNORECASE)
        
        # Clean whitespace
        character = ' '.join(character.split())
        
        return character.strip()
    
    def save_json(self, output_path: Path, glossary: Dict = None):
        """Save glossary as JSON"""
        if glossary is None:
            glossary = self.generate()
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(glossary, f, indent=2, ensure_ascii=False)
        
        if self.logger:
            self.logger.info(f"Saved glossary to: {output_path}")
    
    def save_yaml(self, output_path: Path, glossary: Dict = None):
        """Save glossary as YAML"""
        if glossary is None:
            glossary = self.generate()
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(glossary, f, allow_unicode=True, default_flow_style=False)
        
        if self.logger:
            self.logger.info(f"Saved glossary to: {output_path}")
    
    def save_csv(self, output_path: Path, glossary: Dict = None):
        """Save glossary as CSV (source,target format)"""
        if glossary is None:
            glossary = self.generate()
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            # Write header
            f.write("source,target\n")
            
            # Write entries
            for source, targets in sorted(glossary.items()):
                if isinstance(targets, list):
                    target = targets[0] if targets else source
                else:
                    target = targets
                
                # Escape commas in names
                source_escaped = f'"{source}"' if ',' in source else source
                target_escaped = f'"{target}"' if ',' in target else target
                
                f.write(f"{source_escaped},{target_escaped}\n")
        
        if self.logger:
            self.logger.info(f"Saved glossary to: {output_path}")
