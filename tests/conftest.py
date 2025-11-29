"""
Pytest configuration and fixtures for CP-WhisperX tests.

This module provides common test fixtures and configuration for the test suite.
"""

import sys
from pathlib import Path

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
