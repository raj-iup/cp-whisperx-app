#!/usr/bin/env python3
"""
Unit tests for Similarity Optimizer module.

Tests similarity detection and optimization reuse:
- Media fingerprinting
- Similarity computation
- Decision reuse
- Cache persistence
"""

# Standard library
import json
import tempfile
from pathlib import Path
from datetime import datetime

# Third-party
import pytest

# Local
from shared.similarity_optimizer import (
    SimilarityOptimizer,
    MediaFingerprint,
    ProcessingDecision,
    SimilarityMatch
)


class TestMediaFingerprint:
    """Test MediaFingerprint dataclass."""
    
    def test_create_fingerprint(self):
        """Test creating a media fingerprint."""
        fp = MediaFingerprint(
            media_id="abc123",
            duration=300.0,
            audio_hash="hash123",
            spectral_features={"mean": 1500.0},
            energy_profile=[0.5, 0.6, 0.7],
            language="hi",
            created_at="2025-12-10T00:00:00"
        )
        
        assert fp.media_id == "abc123"
        assert fp.duration == 300.0
        assert fp.language == "hi"
    
    def test_to_dict(self):
        """Test converting fingerprint to dictionary."""
        fp = MediaFingerprint(
            media_id="abc123",
            duration=300.0,
            audio_hash="hash123",
            spectral_features={"mean": 1500.0},
            energy_profile=[0.5, 0.6, 0.7],
            language="hi",
            created_at="2025-12-10T00:00:00"
        )
        
        data = fp.to_dict()
        assert isinstance(data, dict)
        assert data["media_id"] == "abc123"
        assert data["duration"] == 300.0


class TestProcessingDecision:
    """Test ProcessingDecision dataclass."""
    
    def test_create_decision(self):
        """Test creating a processing decision."""
        decision = ProcessingDecision(
            media_id="abc123",
            workflow="transcribe",
            model_used="large-v3",
            batch_size=8,
            beam_size=5,
            source_separation=False,
            processing_time=300.0,
            quality_metrics={"wer": 0.05},
            created_at="2025-12-10T00:00:00"
        )
        
        assert decision.media_id == "abc123"
        assert decision.model_used == "large-v3"
        assert decision.processing_time == 300.0


class TestSimilarityOptimizer:
    """Test SimilarityOptimizer class."""
    
    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def optimizer(self, temp_cache_dir):
        """Create similarity optimizer with temporary cache."""
        return SimilarityOptimizer(cache_dir=temp_cache_dir)
    
    def test_create_optimizer(self, optimizer):
        """Test creating similarity optimizer."""
        assert optimizer is not None
        assert optimizer.similarity_threshold == 0.75
        assert optimizer.min_confidence == 0.6
    
    def test_compute_similarity_identical(self, optimizer):
        """Test similarity of identical fingerprints."""
        fp1 = MediaFingerprint(
            media_id="abc123",
            duration=300.0,
            audio_hash="hash123",
            spectral_features={"mean": 1500.0, "std": 500.0},
            energy_profile=[0.5, 0.6, 0.7, 0.8],
            language="hi",
            created_at="2025-12-10T00:00:00"
        )
        
        fp2 = MediaFingerprint(
            media_id="abc124",  # Different ID
            duration=300.0,
            audio_hash="hash123",  # Same hash
            spectral_features={"mean": 1500.0, "std": 500.0},
            energy_profile=[0.5, 0.6, 0.7, 0.8],
            language="hi",
            created_at="2025-12-10T00:00:00"
        )
        
        similarity = optimizer._compute_similarity(fp1, fp2)
        assert similarity >= 0.9  # Very high similarity
    
    def test_compute_similarity_different(self, optimizer):
        """Test similarity of different fingerprints."""
        fp1 = MediaFingerprint(
            media_id="abc123",
            duration=300.0,
            audio_hash="hash123",
            spectral_features={"mean": 1500.0},
            energy_profile=[0.5, 0.6, 0.7],
            language="hi",
            created_at="2025-12-10T00:00:00"
        )
        
        fp2 = MediaFingerprint(
            media_id="xyz789",
            duration=600.0,  # Different duration
            audio_hash="hash456",  # Different hash
            spectral_features={"mean": 3000.0},  # Different features
            energy_profile=[0.1, 0.2, 0.3],  # Different energy
            language="en",  # Different language
            created_at="2025-12-10T00:00:00"
        )
        
        similarity = optimizer._compute_similarity(fp1, fp2)
        assert similarity < 0.5  # Low similarity
    
    def test_find_similar_media(self, optimizer):
        """Test finding similar media."""
        # Add some fingerprints to cache
        fp1 = MediaFingerprint(
            media_id="media1",
            duration=300.0,
            audio_hash="hash123",
            spectral_features={"mean": 1500.0},
            energy_profile=[0.5, 0.6, 0.7],
            language="hi",
            created_at="2025-12-10T00:00:00"
        )
        optimizer.fingerprints["media1"] = fp1
        
        fp2 = MediaFingerprint(
            media_id="media2",
            duration=305.0,  # Slightly different
            audio_hash="hash123",  # Same
            spectral_features={"mean": 1520.0},  # Similar
            energy_profile=[0.5, 0.6, 0.7],  # Same
            language="hi",
            created_at="2025-12-10T00:00:00"
        )
        optimizer.fingerprints["media2"] = fp2
        
        # Find similar to fp2
        matches = optimizer.find_similar_media(fp2, threshold=0.75)
        
        assert len(matches) >= 1
        assert matches[0].reference_media_id == "media1"
        assert matches[0].similarity_score >= 0.75
    
    def test_store_and_retrieve_decision(self, optimizer):
        """Test storing and retrieving processing decision."""
        # Store decision
        optimizer.store_processing_decision(
            media_id="media1",
            workflow="transcribe",
            model_used="large-v3",
            batch_size=8,
            beam_size=5,
            source_separation=False,
            processing_time=300.0,
            quality_metrics={"wer": 0.05}
        )
        
        # Verify stored
        assert "media1" in optimizer.decisions
        assert len(optimizer.decisions["media1"]) == 1
        
        decision = optimizer.decisions["media1"][0]
        assert decision.model_used == "large-v3"
        assert decision.processing_time == 300.0
    
    def test_get_reusable_decisions(self, optimizer):
        """Test getting reusable decisions from similar media."""
        # Store decision for media1
        optimizer.store_processing_decision(
            media_id="media1",
            workflow="transcribe",
            model_used="large-v3",
            batch_size=8,
            beam_size=5,
            source_separation=False,
            processing_time=300.0,
            quality_metrics={"wer": 0.05}
        )
        
        # Create similarity match
        match = SimilarityMatch(
            reference_media_id="media1",
            target_media_id="media2",
            similarity_score=0.85,
            matching_features=["duration", "audio_hash"],
            reusable_decisions=["model", "parameters"],
            confidence=0.85
        )
        
        # Get reusable decision
        decision = optimizer.get_reusable_decisions(match)
        
        assert decision is not None
        assert decision.model_used == "large-v3"
        assert decision.batch_size == 8
    
    def test_get_reusable_decisions_low_confidence(self, optimizer):
        """Test that low confidence prevents reuse."""
        # Store decision
        optimizer.store_processing_decision(
            media_id="media1",
            workflow="transcribe",
            model_used="large-v3",
            batch_size=8,
            beam_size=5,
            source_separation=False,
            processing_time=300.0,
            quality_metrics={"wer": 0.05}
        )
        
        # Create low confidence match
        match = SimilarityMatch(
            reference_media_id="media1",
            target_media_id="media2",
            similarity_score=0.60,
            matching_features=["language"],
            reusable_decisions=[],
            confidence=0.50  # Below min_confidence (0.6)
        )
        
        # Should not return decision
        decision = optimizer.get_reusable_decisions(match)
        assert decision is None
    
    def test_save_and_load_cache(self, optimizer, temp_cache_dir):
        """Test saving and loading cache."""
        # Add fingerprint and decision
        fp = MediaFingerprint(
            media_id="media1",
            duration=300.0,
            audio_hash="hash123",
            spectral_features={"mean": 1500.0},
            energy_profile=[0.5, 0.6, 0.7],
            language="hi",
            created_at="2025-12-10T00:00:00"
        )
        optimizer.fingerprints["media1"] = fp
        
        optimizer.store_processing_decision(
            media_id="media1",
            workflow="transcribe",
            model_used="large-v3",
            batch_size=8,
            beam_size=5,
            source_separation=False,
            processing_time=300.0,
            quality_metrics={"wer": 0.05}
        )
        
        # Save
        optimizer._save_cache()
        
        # Create new optimizer (should load saved cache)
        optimizer2 = SimilarityOptimizer(cache_dir=temp_cache_dir)
        
        # Verify loaded
        assert "media1" in optimizer2.fingerprints
        assert "media1" in optimizer2.decisions
        
        fp_loaded = optimizer2.fingerprints["media1"]
        assert fp_loaded.duration == 300.0
        assert fp_loaded.audio_hash == "hash123"
    
    def test_get_optimization_stats(self, optimizer):
        """Test getting optimization statistics."""
        # Add some data
        fp1 = MediaFingerprint(
            media_id="media1",
            duration=300.0,
            audio_hash="hash123",
            spectral_features={"mean": 1500.0},
            energy_profile=[0.5, 0.6, 0.7],
            language="hi",
            created_at="2025-12-10T00:00:00"
        )
        optimizer.fingerprints["media1"] = fp1
        
        optimizer.store_processing_decision(
            media_id="media1",
            workflow="transcribe",
            model_used="large-v3",
            batch_size=8,
            beam_size=5,
            source_separation=False,
            processing_time=300.0,
            quality_metrics={"wer": 0.05}
        )
        
        # Get stats
        stats = optimizer.get_optimization_stats()
        
        assert stats["total_fingerprints"] == 1
        assert stats["total_decisions"] == 1
        assert "average_similarity" in stats
        assert "cache_size_mb" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
