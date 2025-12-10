#!/usr/bin/env python3
"""
Unit tests for Context Learner module.

Tests learning capabilities:
- Character name extraction
- Cultural term learning
- Translation memory building
- Auto-glossary generation
"""

# Standard library
import json
import tempfile
from pathlib import Path
from datetime import datetime

# Third-party
import pytest

# Local
from shared.context_learner import (
    ContextLearner,
    LearnedTerm,
    TranslationMemoryEntry
)


class TestLearnedTerm:
    """Test LearnedTerm dataclass."""
    
    def test_create_learned_term(self):
        """Test creating a learned term."""
        term = LearnedTerm(
            term="Meenu",
            frequency=5,
            contexts=["Scene 1", "Scene 2"],
            category="character_name",
            confidence=0.8,
            first_seen="2025-12-09T10:00:00",
            last_seen="2025-12-09T15:00:00"
        )
        
        assert term.term == "Meenu"
        assert term.frequency == 5
        assert len(term.contexts) == 2
        assert term.category == "character_name"
        assert term.confidence == 0.8
    
    def test_to_dict(self):
        """Test converting term to dictionary."""
        term = LearnedTerm(
            term="arey yaar",
            frequency=3,
            contexts=["Context 1"],
            category="cultural_term",
            confidence=0.6,
            first_seen="2025-12-09T10:00:00",
            last_seen="2025-12-09T11:00:00"
        )
        
        data = term.to_dict()
        assert isinstance(data, dict)
        assert data["term"] == "arey yaar"
        assert data["frequency"] == 3
    
    def test_from_dict(self):
        """Test creating term from dictionary."""
        data = {
            "term": "namaste",
            "frequency": 10,
            "contexts": ["Greeting"],
            "category": "cultural_term",
            "confidence": 0.9,
            "first_seen": "2025-12-01T10:00:00",
            "last_seen": "2025-12-09T10:00:00"
        }
        
        term = LearnedTerm.from_dict(data)
        assert term.term == "namaste"
        assert term.frequency == 10
        assert term.confidence == 0.9


class TestTranslationMemoryEntry:
    """Test TranslationMemoryEntry dataclass."""
    
    def test_create_entry(self):
        """Test creating translation memory entry."""
        entry = TranslationMemoryEntry(
            source="नमस्ते",
            target="Hello",
            source_lang="hi",
            target_lang="en",
            frequency=5,
            confidence=0.95,
            contexts=["Greeting"],
            last_used="2025-12-09T10:00:00"
        )
        
        assert entry.source == "नमस्ते"
        assert entry.target == "Hello"
        assert entry.source_lang == "hi"
        assert entry.target_lang == "en"
    
    def test_to_dict(self):
        """Test converting entry to dictionary."""
        entry = TranslationMemoryEntry(
            source="शुक्रिया",
            target="Thank you",
            source_lang="hi",
            target_lang="en",
            frequency=3,
            confidence=0.8,
            contexts=["Thanks"],
            last_used="2025-12-09T10:00:00"
        )
        
        data = entry.to_dict()
        assert isinstance(data, dict)
        assert data["source"] == "शुक्रिया"
        assert data["target"] == "Thank you"


class TestContextLearner:
    """Test ContextLearner class."""
    
    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def learner(self, temp_cache_dir):
        """Create context learner with temporary cache."""
        return ContextLearner(cache_dir=temp_cache_dir)
    
    def test_create_learner(self, learner):
        """Test creating context learner."""
        assert learner is not None
        assert learner.min_frequency == 3
        assert learner.min_confidence == 0.6
    
    def test_add_learned_term(self, learner):
        """Test adding learned term."""
        learner._add_learned_term(
            lang="hi",
            term="Meenu",
            category="character_name",
            context="TMDB: Jaane Tu"
        )
        
        terms = learner.get_learned_terms("hi", min_confidence=0.0)  # Lower threshold for test
        assert len(terms) >= 1
        assert any(t.term == "Meenu" for t in terms)
    
    def test_add_learned_term_updates_frequency(self, learner):
        """Test that adding same term updates frequency."""
        # Add term multiple times
        for i in range(5):
            learner._add_learned_term(
                lang="hi",
                term="Meenu",
                category="character_name",
                context=f"Context {i}"
            )
        
        terms = learner.get_learned_terms("hi", category="character_name", min_confidence=0.0)
        meenu = next(t for t in terms if t.term == "Meenu")
        assert meenu.frequency == 5
        assert meenu.confidence > 0.1  # Should increase with frequency
    
    def test_add_translation_memory(self, learner):
        """Test adding translation memory entry."""
        learner._add_translation_memory(
            source="नमस्ते",
            target="Hello",
            src_lang="hi",
            tgt_lang="en",
            context="Greeting"
        )
        
        entries = learner.get_translation_memory("hi", "en", min_confidence=0.0)  # Lower threshold
        assert len(entries) >= 1
        assert any(e.source == "नमस्ते" for e in entries)
    
    def test_get_learned_terms_by_category(self, learner):
        """Test filtering learned terms by category."""
        # Add terms of different categories
        learner._add_learned_term("hi", "Meenu", "character_name", "Context 1")
        learner._add_learned_term("hi", "arey yaar", "cultural_term", "Context 2")
        learner._add_learned_term("hi", "Mumbai", "named_entity", "Context 3")
        
        # Get only character names
        character_names = learner.get_learned_terms("hi", category="character_name")
        assert all(t.category == "character_name" for t in character_names)
    
    def test_get_learned_terms_by_confidence(self, learner):
        """Test filtering learned terms by confidence."""
        # Add term with high frequency (high confidence)
        for i in range(10):
            learner._add_learned_term("hi", "frequent_term", "cultural_term", f"Context {i}")
        
        # Add term with low frequency (low confidence)
        learner._add_learned_term("hi", "rare_term", "cultural_term", "Context 1")
        
        # Get only high confidence terms
        high_conf_terms = learner.get_learned_terms("hi", min_confidence=0.8)
        assert any(t.term == "frequent_term" for t in high_conf_terms)
        assert not any(t.term == "rare_term" for t in high_conf_terms)
    
    def test_generate_auto_glossary(self, learner):
        """Test generating auto-glossary."""
        # Add some terms
        for i in range(5):
            learner._add_learned_term("hi", "Meenu", "character_name", f"Context {i}")
            learner._add_learned_term("hi", "arey yaar", "cultural_term", f"Context {i}")
        
        # Generate glossary
        glossary = learner.generate_auto_glossary("hi", min_confidence=0.3)
        assert len(glossary) >= 2
        assert any(e["term"] == "Meenu" for e in glossary)
        assert any(e["term"] == "arey yaar" for e in glossary)
    
    def test_save_and_load_knowledge(self, learner, temp_cache_dir):
        """Test saving and loading learned knowledge."""
        # Add some terms
        learner._add_learned_term("hi", "Meenu", "character_name", "Context 1")
        learner._add_translation_memory("नमस्ते", "Hello", "hi", "en", "Context 1")
        
        # Save
        learner._save_knowledge()
        
        # Create new learner (should load saved knowledge)
        learner2 = ContextLearner(cache_dir=temp_cache_dir)
        
        # Verify loaded
        terms = learner2.get_learned_terms("hi", min_confidence=0.0)
        assert len(terms) >= 1
        assert any(t.term == "Meenu" for t in terms)
        
        entries = learner2.get_translation_memory("hi", "en", min_confidence=0.0)
        assert len(entries) >= 1
        assert any(e.source == "नमस्ते" for e in entries)
    
    def test_learn_from_tmdb_mock(self, learner, temp_cache_dir):
        """Test learning from TMDB metadata (mock)."""
        # Create mock TMDB manifest
        job_dir = temp_cache_dir / "job-test"
        tmdb_dir = job_dir / "02_tmdb"
        tmdb_dir.mkdir(parents=True)
        
        # Create manifest
        manifest = {
            "outputs": [{
                "key": "tmdb_metadata",
                "filename": "tmdb_data.json"
            }]
        }
        with open(tmdb_dir / "stage_manifest.json", 'w') as f:
            json.dump(manifest, f)
        
        # Create TMDB data
        tmdb_data = {
            "title": "Test Movie",
            "cast": [
                {"character": "Meenu", "actor": "Actor 1"},
                {"character": "Jai", "actor": "Actor 2"}
            ]
        }
        with open(tmdb_dir / "tmdb_data.json", 'w') as f:
            json.dump(tmdb_data, f)
        
        # Learn from job
        stats = learner.learn_from_job(job_dir)
        assert stats["character_names"] >= 2
        
        # Verify learned terms
        terms = learner.get_learned_terms("hi", category="character_name", min_confidence=0.0)
        assert any(t.term == "Meenu" for t in terms)
        assert any(t.term == "Jai" for t in terms)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
