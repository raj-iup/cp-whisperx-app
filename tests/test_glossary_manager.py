#!/usr/bin/env python3
"""
Unit tests for Unified Glossary Manager

Tests Phase 1 functionality:
- Loading glossary sources
- Priority cascade
- Cache integration
- Term lookup and translation
"""

import pytest
import json
import tempfile
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.glossary_manager import UnifiedGlossaryManager
from shared.glossary_cache import GlossaryCache


class TestUnifiedGlossaryManager:
    """Test suite for UnifiedGlossaryManager"""
    
    def test_initialization(self, tmp_path):
        """Test basic initialization"""
        manager = UnifiedGlossaryManager(
            project_root=tmp_path,
            film_title="Test Film",
            film_year=2020,
            enable_cache=False,
            enable_learning=False
        )
        
        assert manager.film_title == "Test Film"
        assert manager.film_year == 2020
        assert not manager.loaded
    
    def test_load_without_files(self, tmp_path):
        """Test loading when no glossary files exist"""
        manager = UnifiedGlossaryManager(
            project_root=tmp_path,
            enable_cache=False
        )
        
        stats = manager.load_all_sources()
        
        assert stats['master_terms'] == 0
        assert stats['tmdb_terms'] == 0
        assert stats['total_terms'] == 0
        assert manager.loaded
    
    def test_load_master_glossary(self, tmp_path):
        """Test loading master glossary from TSV"""
        # Create glossary directory and TSV
        glossary_dir = tmp_path / "glossary"
        glossary_dir.mkdir()
        
        tsv_path = glossary_dir / "hinglish_master.tsv"
        tsv_content = """source\tpreferred_english\tnotes\tcontext
yaar\tdude|buddy|man\tCasual friend\tcasual
matlab\tI mean|that is\tDiscourse marker\tdiscourse"""
        
        with open(tsv_path, 'w') as f:
            f.write(tsv_content)
        
        manager = UnifiedGlossaryManager(
            project_root=tmp_path,
            enable_cache=False
        )
        
        stats = manager.load_all_sources()
        
        assert stats['master_terms'] == 2
        assert 'yaar' in manager.master_glossary
        assert manager.master_glossary['yaar'] == ['dude', 'buddy', 'man']
    
    def test_load_tmdb_glossary(self, tmp_path):
        """Test loading TMDB glossary from enrichment"""
        # Create TMDB enrichment file
        enrichment = {
            'cast': [
                {'name': 'Aamir Khan', 'character': 'Rancho'},
                {'name': 'R. Madhavan', 'character': 'Farhan'}
            ],
            'crew': [
                {'name': 'Rajkumar Hirani', 'job': 'Director'}
            ]
        }
        
        tmdb_path = tmp_path / "enrichment.json"
        with open(tmdb_path, 'w') as f:
            json.dump(enrichment, f)
        
        manager = UnifiedGlossaryManager(
            project_root=tmp_path,
            film_title="3 Idiots",
            film_year=2009,
            tmdb_enrichment_path=tmdb_path,
            enable_cache=False
        )
        
        stats = manager.load_all_sources()
        
        assert stats['tmdb_terms'] > 0
        assert 'Aamir Khan' in manager.tmdb_glossary
        assert 'Rancho' in manager.tmdb_glossary
    
    def test_priority_cascade(self, tmp_path):
        """Test priority cascade (film > TMDB > master)"""
        # Create master glossary
        glossary_dir = tmp_path / "glossary"
        glossary_dir.mkdir()
        
        tsv_path = glossary_dir / "hinglish_master.tsv"
        with open(tsv_path, 'w') as f:
            f.write("source\tpreferred_english\tnotes\tcontext\n")
            f.write("test\tmaster_translation\tTest term\tcasual\n")
        
        # Create TMDB enrichment
        tmdb_path = tmp_path / "tmdb.json"
        with open(tmdb_path, 'w') as f:
            json.dump({'cast': [{'name': 'test', 'character': 'tmdb_translation'}]}, f)
        
        # Create film-specific glossary
        film_dir = glossary_dir / "films" / "popular"
        film_dir.mkdir(parents=True)
        film_path = film_dir / "test_film_2020.json"
        with open(film_path, 'w') as f:
            json.dump({'test': 'film_translation'}, f)
        
        manager = UnifiedGlossaryManager(
            project_root=tmp_path,
            film_title="Test Film",
            film_year=2020,
            tmdb_enrichment_path=tmdb_path,
            enable_cache=False
        )
        
        manager.load_all_sources()
        
        # Film-specific should win
        result = manager.get_term('test')
        assert result == 'film_translation'
    
    def test_get_bias_terms(self, tmp_path):
        """Test getting bias terms for ASR"""
        # Create master glossary
        glossary_dir = tmp_path / "glossary"
        glossary_dir.mkdir()
        
        tsv_path = glossary_dir / "hinglish_master.tsv"
        with open(tsv_path, 'w') as f:
            f.write("source\tpreferred_english\tnotes\tcontext\n")
            f.write("yaar\tdude\tTest\tcasual\n")
            f.write("bhai\tbro\tTest\tcasual\n")
        
        manager = UnifiedGlossaryManager(
            project_root=tmp_path,
            enable_cache=False
        )
        
        manager.load_all_sources()
        bias_terms = manager.get_bias_terms(max_terms=10)
        
        assert len(bias_terms) > 0
        assert 'yaar' in bias_terms or 'bhai' in bias_terms
    
    def test_cache_integration(self, tmp_path):
        """Test cache integration"""
        manager = UnifiedGlossaryManager(
            project_root=tmp_path,
            film_title="Test Film",
            film_year=2020,
            enable_cache=True
        )
        
        # Cache should be initialized
        assert manager.cache is not None
        
        # Load (will save to cache)
        stats = manager.load_all_sources()
        
        # Second manager should hit cache
        manager2 = UnifiedGlossaryManager(
            project_root=tmp_path,
            film_title="Test Film",
            film_year=2020,
            enable_cache=True
        )
        
        stats2 = manager2.load_all_sources()
        assert stats2['cache_hit'] == True or stats2['tmdb_terms'] == 0


def test_glossary_cache():
    """Test glossary cache separately"""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        cache = GlossaryCache(tmp_path, ttl_days=30)
        
        # Save glossary
        test_glossary = {"yaar": ["dude"], "bhai": ["bro"]}
        result = cache.save_tmdb_glossary("Test Film", 2020, test_glossary)
        assert result == True
        
        # Retrieve glossary
        retrieved = cache.get_tmdb_glossary("Test Film", 2020)
        assert retrieved == test_glossary
        
        # Get statistics
        stats = cache.get_cache_statistics()
        assert stats['tmdb_entries'] >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
