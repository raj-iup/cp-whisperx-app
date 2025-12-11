#!/usr/bin/env python3
"""
Integration tests for ASR module extraction (Phase 7)

Tests all 6 extracted modules working together:
- model_manager.py
- bias_prompting.py  
- postprocessing.py
- transcription.py
- alignment.py
- (chunking.py - stub)

Per AD-002 + AD-009: Quality-first testing of modular architecture
"""

# Standard library
import sys
import json
import tempfile
from pathlib import Path
from typing import Dict, Any

# Add scripts to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

# Third-party
import pytest

# Local modules under test
from whisperx_module.model_manager import ModelManager
from whisperx_module.bias_prompting import BiasPromptingStrategy
from whisperx_module.postprocessing import ResultProcessor
from whisperx_module.transcription import TranscriptionEngine
from whisperx_module.alignment import AlignmentEngine
from shared.logger import get_logger


class TestModuleIntegration:
    """Integration tests for ASR module architecture"""
    
    @pytest.fixture
    def logger(self):
        """Test logger"""
        return get_logger("test_integration")
    
    @pytest.fixture
    def test_audio(self):
        """Path to test audio file"""
        test_file = PROJECT_ROOT / "in" / "Energy Demand in AI.mp4"
        if not test_file.exists():
            pytest.skip(f"Test file not found: {test_file}")
        return str(test_file)
    
    @pytest.fixture
    def mock_segments(self):
        """Mock transcription segments"""
        return [
            {
                "start": 0.0,
                "end": 2.5,
                "text": "This is a test segment",
                "confidence": 0.95
            },
            {
                "start": 2.5,
                "end": 5.0,
                "text": "Another test segment",
                "confidence": 0.88
            }
        ]
    
    def test_model_manager_creation(self, logger):
        """Test ModelManager can create backends"""
        manager = ModelManager(
            backend_type="auto",
            model_name="base",  # Smallest model for testing
            device="cpu",
            compute_type="int8",
            logger=logger
        )
        
        # Should select appropriate backend
        assert manager.backend_type in ["whisperx", "mlx", "ctranslate2"]
        logger.info(f"✓ ModelManager created with backend: {manager.backend_type}")
    
    def test_bias_prompting_strategies(self, logger, mock_segments):
        """Test BiasPrompting strategies work"""
        strategy = BiasPromptingStrategy(
            mode="simple",
            bias_words=["test", "segment"],
            logger=logger
        )
        
        # Generate bias windows
        windows = strategy.generate_windows(
            segments=mock_segments,
            mode="simple"
        )
        
        assert isinstance(windows, list)
        logger.info(f"✓ BiasPrompting generated {len(windows)} windows")
    
    def test_result_processor_filtering(self, logger, mock_segments):
        """Test ResultProcessor filters low confidence"""
        processor = ResultProcessor(logger=logger)
        
        # Add low confidence segment
        test_segments = mock_segments + [
            {"start": 5.0, "end": 7.0, "text": "Low confidence", "confidence": 0.5}
        ]
        
        # Filter (threshold 0.6)
        filtered = processor.filter_low_confidence_segments(
            test_segments,
            confidence_threshold=0.6
        )
        
        # Should remove low confidence
        assert len(filtered) == 2  # Only 2 high-confidence segments
        logger.info(f"✓ ResultProcessor filtered {len(test_segments) - len(filtered)} low-confidence segments")
    
    def test_result_processor_save_formats(self, logger, mock_segments):
        """Test ResultProcessor saves multiple formats"""
        processor = ResultProcessor(logger=logger)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            
            # Save results
            result = {"segments": mock_segments}
            processor.save_results(
                result=result,
                output_dir=output_dir,
                basename="test",
                language="en"
            )
            
            # Check files created
            json_file = output_dir / "test_english_whisperx.json"
            txt_file = output_dir / "test_english_transcript.txt"
            srt_file = output_dir / "test_english_subtitles.srt"
            
            assert json_file.exists(), "JSON file not created"
            assert txt_file.exists(), "TXT file not created"
            assert srt_file.exists(), "SRT file not created"
            
            logger.info("✓ ResultProcessor saved all 3 formats (JSON, TXT, SRT)")
    
    def test_alignment_engine_dispatcher(self, logger, mock_segments):
        """Test AlignmentEngine routing (no actual alignment)"""
        # Mock backend
        class MockBackend:
            name = "whisperx"
            def align_segments(self, segments, audio_file, language):
                return {"segments": segments}
        
        engine = AlignmentEngine(
            backend=MockBackend(),
            device="cpu",
            logger=logger
        )
        
        result = {"segments": mock_segments}
        aligned = engine.align(
            result=result,
            audio_file="dummy.mp4",
            target_lang="en"
        )
        
        assert "segments" in aligned
        logger.info("✓ AlignmentEngine dispatcher works")
    
    def test_transcription_engine_workflow_detection(self, logger):
        """Test TranscriptionEngine workflow logic"""
        # Mock processor
        class MockProcessor:
            def __init__(self):
                self.backend = type('obj', (object,), {'name': 'whisperx'})()
                self.model_name = "base"
                self.device = "cpu"
                self.batch_size = 8
        
        engine = TranscriptionEngine(
            processor=MockProcessor(),
            logger=logger,
            get_indictrans2_fn=None
        )
        
        # Test workflow detection
        needs_two_step = engine._needs_two_step_processing(
            source_language="hi",
            target_language="en"
        )
        
        assert needs_two_step is True
        logger.info("✓ TranscriptionEngine detects two-step workflow")
        
        # Test same-language workflow
        needs_two_step = engine._needs_two_step_processing(
            source_language="en",
            target_language="en"
        )
        
        assert needs_two_step is False
        logger.info("✓ TranscriptionEngine detects single-step workflow")
    
    def test_module_imports(self):
        """Test all modules can be imported"""
        try:
            from whisperx_module import ModelManager
            from whisperx_module import BiasPromptingStrategy
            from whisperx_module import ResultProcessor
            from whisperx_module import TranscriptionEngine
            from whisperx_module import AlignmentEngine
            
            # Check exports
            from whisperx_module import __all__
            assert "ModelManager" in __all__
            assert "BiasPromptingStrategy" in __all__
            assert "ResultProcessor" in __all__
            assert "TranscriptionEngine" in __all__
            assert "AlignmentEngine" in __all__
            
            print("✓ All modules import successfully")
            print(f"✓ Module exports: {', '.join(__all__)}")
            
        except ImportError as e:
            pytest.fail(f"Module import failed: {e}")
    
    def test_backward_compatibility(self):
        """Test original WhisperXProcessor still works"""
        try:
            from whisperx_integration import WhisperXProcessor
            
            # Should be able to create processor
            processor = WhisperXProcessor(
                model_name="base",
                device="cpu",
                compute_type="int8"
            )
            
            assert processor is not None
            print("✓ Original WhisperXProcessor still functional")
            
        except ImportError as e:
            pytest.fail(f"Backward compatibility broken: {e}")


class TestEndToEndIntegration:
    """End-to-end integration tests"""
    
    @pytest.fixture
    def logger(self):
        return get_logger("test_e2e")
    
    @pytest.mark.slow
    def test_full_pipeline_with_modules(self, logger):
        """Test complete pipeline using extracted modules"""
        # This would be a full E2E test
        # Skipped in CI, run manually with real audio
        pytest.skip("Full E2E test - run manually")


def test_compliance_checks():
    """Test all modules follow compliance standards"""
    import ast
    
    modules = [
        "model_manager.py",
        "bias_prompting.py",
        "postprocessing.py",
        "transcription.py",
        "alignment.py"
    ]
    
    for module_name in modules:
        module_path = PROJECT_ROOT / "scripts" / "whisperx_module" / module_name
        
        if not module_path.exists():
            pytest.fail(f"Module not found: {module_path}")
        
        # Check file has proper structure
        with open(module_path) as f:
            content = f.read()
            
            # Should have docstring
            assert '"""' in content, f"{module_name} missing docstring"
            
            # Should import logger from shared
            assert "from shared.logger import" in content or "logger" in content
            
            # Should have __all__ export
            tree = ast.parse(content)
            has_all = any(
                isinstance(node, ast.Assign) and 
                any(t.id == '__all__' for t in node.targets if isinstance(t, ast.Name))
                for node in ast.walk(tree)
            )
            assert has_all, f"{module_name} missing __all__ export"
        
        print(f"✓ {module_name} follows compliance standards")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
