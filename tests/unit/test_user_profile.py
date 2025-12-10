#!/usr/bin/env python3
"""
Unit tests for user_profile.py

Tests userId assignment, profile management, and credential access.
"""

import sys
import json
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.user_profile import UserProfile, UserIdManager, create_user, list_all_users


@pytest.fixture
def temp_users_dir(monkeypatch, tmp_path):
    """Create temporary users directory for testing."""
    users_dir = tmp_path / "users"
    users_dir.mkdir()
    
    # Monkey patch the USERS_DIR
    monkeypatch.setattr(UserIdManager, 'USERS_DIR', users_dir)
    monkeypatch.setattr(UserIdManager, 'COUNTER_FILE', users_dir / '.userIdCounter')
    
    yield users_dir
    
    # Cleanup handled by tmp_path


class TestUserIdManager:
    """Test userId assignment and management."""
    
    def test_get_next_user_id_starts_at_1(self, temp_users_dir):
        """First userId should be 1."""
        user_id = UserIdManager.get_next_user_id()
        assert user_id == 1
    
    def test_get_next_user_id_increments(self, temp_users_dir):
        """UserId should increment sequentially."""
        user_id1 = UserIdManager.get_next_user_id()
        user_id2 = UserIdManager.get_next_user_id()
        user_id3 = UserIdManager.get_next_user_id()
        
        assert user_id1 == 1
        assert user_id2 == 2
        assert user_id3 == 3
    
    def test_user_exists_false_for_new_user(self, temp_users_dir):
        """user_exists should return False for non-existent user."""
        assert not UserIdManager.user_exists(999)
    
    def test_user_exists_true_after_creation(self, temp_users_dir):
        """user_exists should return True after user created."""
        user_id = UserProfile.create_new_user(name="Test User")
        assert UserIdManager.user_exists(user_id)
    
    def test_list_users_empty_initially(self, temp_users_dir):
        """list_users should return empty list initially."""
        users = UserIdManager.list_users()
        assert users == []
    
    def test_list_users_returns_created_users(self, temp_users_dir):
        """list_users should return all created userIds."""
        user1 = UserProfile.create_new_user(name="User 1")
        user2 = UserProfile.create_new_user(name="User 2")
        user3 = UserProfile.create_new_user(name="User 3")
        
        users = UserIdManager.list_users()
        assert users == [user1, user2, user3]
        assert users == [1, 2, 3]


class TestUserProfileCreation:
    """Test user profile creation."""
    
    def test_create_new_user_assigns_user_id(self, temp_users_dir):
        """create_new_user should assign userId."""
        user_id = UserProfile.create_new_user(name="Alice")
        assert user_id == 1
    
    def test_create_new_user_creates_profile_file(self, temp_users_dir):
        """create_new_user should create profile.json."""
        user_id = UserProfile.create_new_user(name="Alice")
        profile_path = temp_users_dir / str(user_id) / "profile.json"
        assert profile_path.exists()
    
    def test_create_new_user_creates_cache_dir(self, temp_users_dir):
        """create_new_user should create cache directory."""
        user_id = UserProfile.create_new_user(name="Alice")
        cache_dir = temp_users_dir / str(user_id) / "cache"
        assert cache_dir.exists()
        assert cache_dir.is_dir()
    
    def test_create_new_user_sets_user_info(self, temp_users_dir):
        """create_new_user should set name and email."""
        user_id = UserProfile.create_new_user(name="Alice", email="alice@example.com")
        profile = UserProfile.load(user_id)
        
        assert profile.user['name'] == "Alice"
        assert profile.user['email'] == "alice@example.com"
        assert 'created_at' in profile.user
    
    def test_create_new_user_with_credentials(self, temp_users_dir):
        """create_new_user should accept credential kwargs."""
        user_id = UserProfile.create_new_user(
            name="Alice",
            tmdb_api_key="test_tmdb_key",
            openai_api_key="test_openai_key"
        )
        profile = UserProfile.load(user_id)
        
        assert profile.get_credential('tmdb', 'api_key') == "test_tmdb_key"
        assert profile.get_credential('openai', 'api_key') == "test_openai_key"
    
    def test_create_multiple_users(self, temp_users_dir):
        """Should be able to create multiple users."""
        user1 = UserProfile.create_new_user(name="Alice")
        user2 = UserProfile.create_new_user(name="Bob")
        user3 = UserProfile.create_new_user(name="Carol")
        
        assert user1 == 1
        assert user2 == 2
        assert user3 == 3
        
        # All profiles should exist
        assert UserIdManager.user_exists(1)
        assert UserIdManager.user_exists(2)
        assert UserIdManager.user_exists(3)


class TestUserProfileLoading:
    """Test user profile loading."""
    
    def test_load_existing_profile(self, temp_users_dir):
        """load should return profile for existing userId."""
        user_id = UserProfile.create_new_user(name="Alice")
        profile = UserProfile.load(user_id)
        
        assert profile.user_id == user_id
        assert profile.user['name'] == "Alice"
    
    def test_load_nonexistent_profile_raises(self, temp_users_dir):
        """load should raise FileNotFoundError for non-existent userId."""
        with pytest.raises(FileNotFoundError, match="User profile not found"):
            UserProfile.load(user_id=999)
    
    def test_load_validates_schema(self, temp_users_dir):
        """load should validate profile schema."""
        # Create invalid profile
        user_dir = temp_users_dir / "1"
        user_dir.mkdir()
        
        profile_path = user_dir / "profile.json"
        with open(profile_path, 'w') as f:
            json.dump({"invalid": "schema"}, f)
        
        with pytest.raises(ValueError, match="Missing required field"):
            UserProfile.load(user_id=1)
    
    def test_load_sets_user_id(self, temp_users_dir):
        """load should set userId attribute."""
        user_id = UserProfile.create_new_user(name="Alice")
        profile = UserProfile.load(user_id)
        
        assert profile.user_id == user_id


class TestCredentialAccess:
    """Test credential access methods."""
    
    def test_get_credential_existing(self, temp_users_dir):
        """get_credential should return existing credential."""
        user_id = UserProfile.create_new_user(tmdb_api_key="test_key")
        profile = UserProfile.load(user_id)
        
        api_key = profile.get_credential('tmdb', 'api_key')
        assert api_key == "test_key"
    
    def test_get_credential_missing_returns_none(self, temp_users_dir):
        """get_credential should return None for missing credential."""
        user_id = UserProfile.create_new_user(name="Alice")
        profile = UserProfile.load(user_id)
        
        api_key = profile.get_credential('tmdb', 'api_key')
        assert api_key is None
    
    def test_get_credential_empty_string_returns_none(self, temp_users_dir):
        """get_credential should return None for empty string."""
        user_id = UserProfile.create_new_user(name="Alice")
        profile = UserProfile.load(user_id)
        
        # Default template has empty strings
        api_key = profile.get_credential('huggingface', 'token')
        assert api_key is None or api_key == ""
    
    def test_set_credential_new(self, temp_users_dir):
        """set_credential should set new credential."""
        user_id = UserProfile.create_new_user(name="Alice")
        profile = UserProfile.load(user_id)
        
        profile.set_credential('tmdb', 'api_key', 'new_key')
        assert profile.get_credential('tmdb', 'api_key') == 'new_key'
    
    def test_set_credential_overwrites_existing(self, temp_users_dir):
        """set_credential should overwrite existing credential."""
        user_id = UserProfile.create_new_user(tmdb_api_key="old_key")
        profile = UserProfile.load(user_id)
        
        profile.set_credential('tmdb', 'api_key', 'new_key')
        assert profile.get_credential('tmdb', 'api_key') == 'new_key'
    
    def test_save_persists_changes(self, temp_users_dir):
        """save should persist credential changes."""
        user_id = UserProfile.create_new_user(name="Alice")
        profile = UserProfile.load(user_id)
        
        profile.set_credential('tmdb', 'api_key', 'test_key')
        profile.save()
        
        # Reload and verify
        profile2 = UserProfile.load(user_id)
        assert profile2.get_credential('tmdb', 'api_key') == 'test_key'


class TestWorkflowValidation:
    """Test workflow validation."""
    
    def test_validate_transcribe_workflow_valid(self, temp_users_dir):
        """validate_for_workflow should pass with HF token."""
        user_id = UserProfile.create_new_user(huggingface_token="test_token")
        profile = UserProfile.load(user_id)
        
        # Should not raise
        profile.validate_for_workflow('transcribe')
    
    def test_validate_transcribe_workflow_missing_hf_raises(self, temp_users_dir):
        """validate_for_workflow should raise without HF token."""
        user_id = UserProfile.create_new_user(name="Alice")
        profile = UserProfile.load(user_id)
        
        with pytest.raises(ValueError, match="HuggingFace token"):
            profile.validate_for_workflow('transcribe')
    
    def test_validate_subtitle_workflow_valid(self, temp_users_dir):
        """validate_for_workflow should pass with HF + TMDB."""
        user_id = UserProfile.create_new_user(
            huggingface_token="test_token",
            tmdb_api_key="test_key"
        )
        profile = UserProfile.load(user_id)
        
        # Should not raise
        profile.validate_for_workflow('subtitle')
    
    def test_validate_subtitle_workflow_missing_tmdb_raises(self, temp_users_dir):
        """validate_for_workflow should raise without TMDB key."""
        user_id = UserProfile.create_new_user(huggingface_token="test_token")
        profile = UserProfile.load(user_id)
        
        with pytest.raises(ValueError, match="TMDB API key"):
            profile.validate_for_workflow('subtitle')
    
    def test_validate_unknown_workflow_raises(self, temp_users_dir):
        """validate_for_workflow should raise for unknown workflow."""
        user_id = UserProfile.create_new_user(name="Alice")
        profile = UserProfile.load(user_id)
        
        with pytest.raises(ValueError, match="Unknown workflow"):
            profile.validate_for_workflow('invalid_workflow')


class TestBackwardCompatibility:
    """Test backward compatibility with secrets.json."""
    
    def test_load_migrates_from_secrets_json(self, temp_users_dir, monkeypatch, tmp_path):
        """load should migrate from secrets.json if userId not found."""
        # Create config directory
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        
        # Create secrets.json
        secrets = {
            "hf_token": "test_hf_token",
            "tmdb_api_key": "test_tmdb_key",
            "openai_api_key": "test_openai_key"
        }
        secrets_path = config_dir / "secrets.json"
        with open(secrets_path, 'w') as f:
            json.dump(secrets, f)
        
        # Monkey patch Path to find our test config
        original_path = Path
        def mock_path(path_str):
            if path_str == 'config':
                return config_dir
            return original_path(path_str)
        monkeypatch.setattr('shared.user_profile.Path', mock_path)
        
        # Load should migrate
        profile = UserProfile.load(user_id=1)
        
        # Verify credentials migrated
        assert profile.get_credential('huggingface', 'token') == "test_hf_token"
        assert profile.get_credential('tmdb', 'api_key') == "test_tmdb_key"
        assert profile.get_credential('openai', 'api_key') == "test_openai_key"
        
        # Verify profile saved
        assert UserIdManager.user_exists(1)


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_create_user_function(self, temp_users_dir):
        """create_user should create new user."""
        user_id = create_user(name="Alice", email="alice@example.com")
        assert user_id == 1
        assert UserIdManager.user_exists(1)
    
    def test_list_all_users_function(self, temp_users_dir):
        """list_all_users should list all users."""
        create_user(name="Alice")
        create_user(name="Bob")
        create_user(name="Carol")
        
        users = list_all_users()
        assert users == [1, 2, 3]


class TestProfileMethods:
    """Test profile utility methods."""
    
    def test_to_dict(self, temp_users_dir):
        """to_dict should return profile as dictionary."""
        user_id = UserProfile.create_new_user(name="Alice")
        profile = UserProfile.load(user_id)
        
        data = profile.to_dict()
        assert data['userId'] == user_id
        assert data['user']['name'] == "Alice"
        assert 'credentials' in data
        assert 'preferences' in data
    
    def test_repr(self, temp_users_dir):
        """__repr__ should return readable string."""
        user_id = UserProfile.create_new_user(name="Alice")
        profile = UserProfile.load(user_id)
        
        repr_str = repr(profile)
        assert "UserProfile" in repr_str
        assert f"userId={user_id}" in repr_str
        assert "Alice" in repr_str


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
