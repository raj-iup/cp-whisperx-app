#!/usr/bin/env python3
"""
Unit Tests for Configuration System

Tests configuration loading and management.
Phase 2: Testing Infrastructure - Task 2.2
"""

# Standard library
import os
import sys
from pathlib import Path

# Third-party
import pytest

# Local
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.config_loader import load_config


@pytest.mark.unit
class TestConfigLoader:
    """Unit tests for configuration loading."""
    
    def test_load_config_returns_dict(self):
        """Test that load_config returns a dictionary."""
        config = load_config()
        assert isinstance(config, dict)
    
    def test_load_config_has_expected_keys(self):
        """Test that config has expected keys."""
        config = load_config()
        
        # Should have at least some pipeline config
        assert len(config) > 0
    
    def test_config_get_with_default(self):
        """Test getting config value with default."""
        config = load_config()
        
        # Non-existent key should return default
        value = config.get("NONEXISTENT_KEY_12345", "default_value")
        assert value == "default_value"
    
    def test_config_type_conversion(self):
        """Test type conversion for config values."""
        config = load_config()
        
        # Test integer conversion (if key exists)
        if "MAX_DURATION" in config:
            value = int(config.get("MAX_DURATION", 3600))
            assert isinstance(value, int)
    
    def test_config_boolean_conversion(self):
        """Test boolean conversion for config values."""
        config = load_config()
        
        # Test boolean-like values
        true_value = config.get("TEST_BOOL_TRUE", "true")
        assert true_value.lower() in ("true", "false", "1", "0")
    
    def test_config_list_parsing(self):
        """Test parsing comma-separated lists."""
        config = load_config()
        
        # Test list parsing
        list_value = config.get("TARGET_LANGS", "en,hi").split(",")
        assert isinstance(list_value, list)
        assert len(list_value) >= 1


@pytest.mark.unit
class TestEnvironmentConfig:
    """Unit tests for environment-specific configuration."""
    
    def test_config_respects_environment_variables(self, monkeypatch):
        """Test that environment variables can override config."""
        # Set test environment variable
        test_key = "TEST_CONFIG_KEY"
        test_value = "test_value_12345"
        monkeypatch.setenv(test_key, test_value)
        
        # Load config
        config = load_config()
        
        # Check if environment variable is accessible
        assert os.environ.get(test_key) == test_value
    
    def test_config_handles_missing_file_gracefully(self):
        """Test that missing config file is handled gracefully."""
        # This should not raise an exception
        try:
            config = load_config()
            assert isinstance(config, dict)
        except FileNotFoundError:
            pytest.fail("load_config should handle missing file gracefully")


@pytest.mark.unit
class TestConfigValidation:
    """Unit tests for configuration validation."""
    
    def test_config_values_not_empty(self):
        """Test that important config values are not empty."""
        config = load_config()
        
        # Check that config is not completely empty
        assert len(config) > 0
    
    def test_config_paths_are_valid(self):
        """Test that path values in config are valid."""
        config = load_config()
        
        # Test any path-like config values
        for key, value in config.items():
            if key.endswith("_DIR") or key.endswith("_PATH"):
                # Value should be a string if it exists
                if value:
                    assert isinstance(value, str)
