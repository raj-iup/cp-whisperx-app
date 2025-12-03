"""
Pytest configuration and fixtures for CP-WhisperX tests.

This module provides common test fixtures and configuration for the test suite.
Phase 2: Testing Infrastructure - Enhanced fixtures for comprehensive testing.
"""

import sys
import json
import tempfile
from pathlib import Path
from typing import Dict, Any, Generator

import pytest

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def project_root() -> Path:
    """Return the project root directory."""
    return PROJECT_ROOT


@pytest.fixture
def scripts_dir(project_root: Path) -> Path:
    """Return the scripts directory."""
    return project_root / "scripts"


@pytest.fixture
def shared_dir(project_root: Path) -> Path:
    """Return the shared directory."""
    return project_root / "shared"


@pytest.fixture
def config_dir(project_root: Path) -> Path:
    """Return the config directory."""
    return project_root / "config"


@pytest.fixture
def sample_output_dir(tmp_path: Path) -> Path:
    """Create and return a temporary output directory for tests."""
    output_dir = tmp_path / "test_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


# ============================================================================
# ENHANCED FIXTURES FOR PHASE 2
# ============================================================================

@pytest.fixture
def mock_job_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """
    Create a mock job directory with standard structure.
    
    Creates:
        - job_dir/.env.pipeline (minimal config)
        - job_dir/01_demux/ (empty stage dir)
        - job_dir/in/ (input directory)
    
    Yields:
        Path to job directory
    """
    job_dir = tmp_path / "mock_job"
    job_dir.mkdir()
    
    # Create minimal config
    config_file = job_dir / ".env.pipeline"
    config_file.write_text("""# Mock pipeline config
DEBUG=false
LOG_LEVEL=INFO
""")
    
    # Create standard directories
    (job_dir / "01_demux").mkdir()
    (job_dir / "in").mkdir()
    
    yield job_dir
    
    # Cleanup handled by tmp_path


@pytest.fixture
def mock_stage_output(tmp_path: Path) -> Generator[Path, None, None]:
    """
    Create a mock stage output directory with sample files.
    
    Creates:
        - stage_dir/manifest.json
        - stage_dir/output.txt (sample output)
    
    Yields:
        Path to stage output directory
    """
    stage_dir = tmp_path / "mock_stage_output"
    stage_dir.mkdir()
    
    # Create mock manifest
    manifest = {
        "stage_name": "mock_stage",
        "inputs": [],
        "outputs": ["output.txt"],
        "exit_code": 0,
        "duration": 1.5
    }
    manifest_file = stage_dir / "manifest.json"
    manifest_file.write_text(json.dumps(manifest, indent=2))
    
    # Create mock output file
    output_file = stage_dir / "output.txt"
    output_file.write_text("Mock stage output content")
    
    yield stage_dir


@pytest.fixture
def mock_config() -> Dict[str, Any]:
    """
    Return a mock configuration dictionary.
    
    Returns:
        Dict with common config parameters
    """
    return {
        "DEBUG": "false",
        "LOG_LEVEL": "INFO",
        "WHISPERX_MODEL": "large-v2",
        "WHISPERX_DEVICE": "cpu",
        "STAGE_01_DEMUX_ENABLED": "true",
        "STAGE_02_TMDB_ENABLED": "true",
        "STAGE_03_GLOSSARY_ENABLED": "true",
        "TARGET_LANGUAGES": "en,hi,gu",
    }


@pytest.fixture
def sample_media_path(project_root: Path) -> Path:
    """
    Return path to Sample 1 (English technical) test media.
    
    Returns:
        Path to in/Energy Demand in AI.mp4
    """
    return project_root / "in" / "Energy Demand in AI.mp4"


@pytest.fixture
def sample_media_hinglish(project_root: Path) -> Path:
    """
    Return path to Sample 2 (Hinglish Bollywood) test media.
    
    Returns:
        Path to in/test_clips/jaane_tu_test_clip.mp4
    """
    return project_root / "in" / "test_clips" / "jaane_tu_test_clip.mp4"


@pytest.fixture
def mock_audio_file(tmp_path: Path) -> Generator[Path, None, None]:
    """
    Create a mock audio file for testing.
    
    Creates a small WAV file header (not playable, but valid format).
    
    Yields:
        Path to mock audio.wav file
    """
    audio_file = tmp_path / "audio.wav"
    
    # Create minimal WAV file header
    # RIFF header + minimal WAV data
    wav_header = b'RIFF' + b'\x00' * 4 + b'WAVEfmt ' + b'\x10\x00\x00\x00'
    wav_header += b'\x01\x00\x01\x00'  # PCM, mono
    wav_header += b'\x44\xAC\x00\x00'  # 44100 Hz sample rate
    wav_header += b'\x88\x58\x01\x00'  # Byte rate
    wav_header += b'\x02\x00\x10\x00'  # Block align, bits per sample
    wav_header += b'data' + b'\x00' * 4  # Data chunk
    
    audio_file.write_bytes(wav_header)
    
    yield audio_file


@pytest.fixture
def mock_transcript_json(tmp_path: Path) -> Generator[Path, None, None]:
    """
    Create a mock transcript JSON file.
    
    Creates:
        transcript.json with sample segments
    
    Yields:
        Path to transcript.json
    """
    transcript_file = tmp_path / "transcript.json"
    
    transcript_data = {
        "segments": [
            {
                "id": 0,
                "start": 0.0,
                "end": 2.5,
                "text": "This is a test transcript.",
                "confidence": 0.95
            },
            {
                "id": 1,
                "start": 2.5,
                "end": 5.0,
                "text": "With multiple segments.",
                "confidence": 0.92
            }
        ],
        "language": "en"
    }
    
    transcript_file.write_text(json.dumps(transcript_data, indent=2))
    
    yield transcript_file


@pytest.fixture
def mock_glossary_tsv(tmp_path: Path) -> Generator[Path, None, None]:
    """
    Create a mock glossary TSV file.
    
    Creates:
        glossary.tsv with sample terms
    
    Yields:
        Path to glossary.tsv
    """
    glossary_file = tmp_path / "glossary.tsv"
    
    glossary_content = """term\tsource_lang\ttarget_lang\ttranslation\tcategory\tconfidence
AI\ten\thi\tएआई\ttechnical\t1.0
energy\ten\thi\tऊर्जा\ttechnical\t0.95
Jai\thi\ten\tJai\tcharacter_name\t1.0
beta\thi\ten\tson\tcultural\t0.9
"""
    glossary_file.write_text(glossary_content)
    
    yield glossary_file


@pytest.fixture
def test_media_samples(project_root: Path) -> Dict[str, Dict[str, Any]]:
    """
    Return metadata for standard test media samples.
    
    Returns:
        Dict with sample1 and sample2 metadata
    """
    return {
        "sample1": {
            "name": "English Technical Content",
            "path": project_root / "in" / "Energy Demand in AI.mp4",
            "language": "en",
            "type": "technical",
            "workflows": ["transcribe", "translate"],
            "quality_targets": {
                "asr_wer": 0.05,
                "translation_bleu": 0.90
            }
        },
        "sample2": {
            "name": "Hinglish Bollywood Content",
            "path": project_root / "in" / "test_clips" / "jaane_tu_test_clip.mp4",
            "language": "hi",
            "type": "entertainment",
            "workflows": ["subtitle", "transcribe", "translate"],
            "quality_targets": {
                "asr_wer": 0.15,
                "subtitle_quality": 0.88,
                "context_awareness": 0.80
            }
        }
    }


@pytest.fixture(scope="session")
def test_results_dir(project_root: Path) -> Path:
    """
    Return the test-results directory.
    
    Creates directory if it doesn't exist.
    
    Returns:
        Path to test-results/
    """
    results_dir = project_root / "test-results"
    results_dir.mkdir(exist_ok=True)
    return results_dir
