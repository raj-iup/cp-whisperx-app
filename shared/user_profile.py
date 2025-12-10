#!/usr/bin/env python3
"""
User Profile Management System

Manages user profiles with userId-based architecture.
Profiles stored in users/{userId}/profile.json

Features:
- userId assignment and management
- Profile creation and loading
- Credential storage and retrieval
- Workflow validation
- Backward compatibility with secrets.json

Usage:
    # Create new user
    user_id = UserProfile.create_new_user(name="Alice", email="alice@example.com")
    
    # Load user profile
    profile = UserProfile.load(user_id=1)
    
    # Get credentials
    api_key = profile.get_credential('tmdb', 'api_key')
    
    # Validate for workflow
    profile.validate_for_workflow('subtitle')
"""

# Standard library
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any
import logging

# Local
from shared.logger import get_logger

# Configure logger
logger = get_logger(__name__)


class UserIdManager:
    """Manage userId assignment and tracking."""
    
    USERS_DIR = Path("users")
    COUNTER_FILE = USERS_DIR / ".userIdCounter"
    
    @classmethod
    def get_next_user_id(cls) -> int:
        """
        Get next available userId and increment counter.
        
        Thread-safe with file locking.
        
        Returns:
            Next available userId (1, 2, 3, ...)
        """
        # Ensure users directory exists
        cls.USERS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Read current counter
        if cls.COUNTER_FILE.exists():
            with open(cls.COUNTER_FILE, 'r') as f:
                try:
                    current_id = int(f.read().strip())
                except ValueError:
                    logger.warning("Invalid .userIdCounter, resetting to 1")
                    current_id = 1
        else:
            current_id = 1
        
        # Write incremented counter
        next_id = current_id + 1
        with open(cls.COUNTER_FILE, 'w') as f:
            f.write(str(next_id))
        
        return current_id
    
    @classmethod
    def user_exists(cls, user_id: int) -> bool:
        """Check if userId exists."""
        user_dir = cls.USERS_DIR / str(user_id)
        profile_file = user_dir / "profile.json"
        return profile_file.exists()
    
    @classmethod
    def list_users(cls) -> list:
        """List all existing userIds."""
        if not cls.USERS_DIR.exists():
            return []
        
        user_ids = []
        for item in cls.USERS_DIR.iterdir():
            if item.is_dir() and item.name.isdigit():
                user_id = int(item.name)
                if cls.user_exists(user_id):
                    user_ids.append(user_id)
        
        return sorted(user_ids)


class UserProfile:
    """User profile management with userId-based architecture."""
    
    def __init__(self, data: dict, user_id: int):
        """
        Initialize UserProfile.
        
        Args:
            data: Profile data dictionary
            user_id: User ID
        """
        self.user_id: int = user_id
        self.version: str = data.get('version', '1.0')
        self.user: dict = data.get('user', {})
        self.credentials: dict = data.get('credentials', {})
        self.online_services: dict = data.get('online_services', {})
        self.preferences: dict = data.get('preferences', {})
        self._data: dict = data
    
    @property
    def profile_path(self) -> Path:
        """Get path to user's profile.json."""
        return UserIdManager.USERS_DIR / str(self.user_id) / "profile.json"
    
    @classmethod
    def create_new_user(
        cls,
        name: str = "",
        email: str = "",
        **kwargs
    ) -> int:
        """
        Create new user and return assigned userId.
        
        Args:
            name: User's name (optional)
            email: User's email (optional)
            **kwargs: Additional credentials to set
            
        Returns:
            Assigned userId
            
        Example:
            >>> user_id = UserProfile.create_new_user(
            ...     name="Alice",
            ...     email="alice@example.com",
            ...     tmdb_api_key="xxxxx"
            ... )
            >>> print(f"Created user {user_id}")
            Created user 1
        """
        # Get next available userId
        user_id = UserIdManager.get_next_user_id()
        
        # Create user directory
        user_dir = UserIdManager.USERS_DIR / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        
        # Create cache directory
        cache_dir = user_dir / "cache"
        cache_dir.mkdir(exist_ok=True)
        
        # Create profile template
        profile_data = {
            "userId": user_id,
            "version": "1.0",
            "user": {
                "name": name,
                "email": email,
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            "credentials": {
                "huggingface": {"token": ""},
                "tmdb": {"api_key": ""},
                "pyannote": {"token": ""},
                "openai": {"api_key": "", "organization_id": ""},
                "anthropic": {"api_key": ""},
                "google": {"api_key": ""}
            },
            "online_services": {
                "youtube": {"api_key": "", "enabled": False},
                "vimeo": {"access_token": "", "enabled": False}
            },
            "preferences": {
                "default_workflow": "transcribe",
                "default_source_language": "en",
                "ai_provider": "openai",
                "enable_cost_tracking": True
            }
        }
        
        # Set any provided credentials
        for key, value in kwargs.items():
            # Try to find matching credential field
            if '_' in key:
                parts = key.split('_', 1)
                service = parts[0]
                cred_key = parts[1] if len(parts) > 1 else 'api_key'
                
                if service in profile_data['credentials']:
                    profile_data['credentials'][service][cred_key] = value
                elif service in profile_data['online_services']:
                    profile_data['online_services'][service][cred_key] = value
        
        # Save profile
        profile_path = user_dir / "profile.json"
        with open(profile_path, 'w') as f:
            json.dump(profile_data, f, indent=2)
        
        logger.info(f"Created new user profile: userId={user_id}")
        return user_id
    
    @classmethod
    def load(cls, user_id: int, logger_instance: Optional[logging.Logger] = None) -> 'UserProfile':
        """
        Load user profile by userId.
        
        Args:
            user_id: User ID to load
            logger_instance: Optional logger for warnings
            
        Returns:
            UserProfile instance
            
        Raises:
            FileNotFoundError: userId does not exist
            ValueError: Invalid profile data
            
        Example:
            >>> profile = UserProfile.load(user_id=1)
            >>> api_key = profile.get_credential('tmdb', 'api_key')
        """
        if logger_instance is None:
            logger_instance = logger
        
        # Check if user exists
        if not UserIdManager.user_exists(user_id):
            # Try fallback to secrets.json for backward compatibility
            secrets_path = Path('config') / 'secrets.json'
            if secrets_path.exists():
                logger_instance.warning(
                    f"userId {user_id} not found. "
                    "Attempting migration from config/secrets.json..."
                )
                return cls._load_from_secrets_json(secrets_path, user_id, logger_instance)
            
            raise FileNotFoundError(
                f"User profile not found: userId={user_id}\n"
                f"Create user: UserProfile.create_new_user()\n"
                f"Or migrate: ./tools/migrate-to-user-profile.py"
            )
        
        # Load profile
        profile_path = UserIdManager.USERS_DIR / str(user_id) / "profile.json"
        with open(profile_path, 'r') as f:
            data = json.load(f)
        
        # Validate schema
        cls._validate_schema(data)
        
        # Ensure userId matches
        if data.get('userId') != user_id:
            logger_instance.warning(
                f"Profile userId mismatch: file has {data.get('userId')}, expected {user_id}"
            )
            data['userId'] = user_id
        
        return cls(data, user_id)
    
    @classmethod
    def _load_from_secrets_json(
        cls,
        secrets_path: Path,
        user_id: int,
        logger_instance: logging.Logger
    ) -> 'UserProfile':
        """
        Load profile from legacy secrets.json (backward compatibility).
        
        Automatically migrates to userId-based profile.
        """
        with open(secrets_path, 'r') as f:
            secrets = json.load(f)
        
        logger_instance.info(f"Migrating secrets.json to userId={user_id}")
        
        # Create profile with migrated credentials
        profile_data = {
            "userId": user_id,
            "version": "1.0",
            "user": {
                "name": "",
                "email": "",
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            "credentials": {
                "huggingface": {"token": secrets.get('hf_token', '')},
                "tmdb": {"api_key": secrets.get('tmdb_api_key', '')},
                "pyannote": {"token": secrets.get('pyannote_token', secrets.get('PYANNOTE_API_TOKEN', ''))},
                "openai": {"api_key": secrets.get('openai_api_key', ''), "organization_id": ""},
                "anthropic": {"api_key": secrets.get('anthropic_api_key', '')},
                "google": {"api_key": secrets.get('google_api_key', '')}
            },
            "online_services": {
                "youtube": {"api_key": "", "enabled": False},
                "vimeo": {"access_token": "", "enabled": False}
            },
            "preferences": {
                "default_workflow": "transcribe",
                "default_source_language": "en",
                "ai_provider": "openai",
                "enable_cost_tracking": True
            }
        }
        
        # Save to userId-based location
        user_dir = UserIdManager.USERS_DIR / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        
        profile_path = user_dir / "profile.json"
        with open(profile_path, 'w') as f:
            json.dump(profile_data, f, indent=2)
        
        logger_instance.info(f"Migrated credentials to {profile_path}")
        
        return cls(profile_data, user_id)
    
    @staticmethod
    def _validate_schema(data: dict) -> None:
        """Validate profile schema."""
        required_fields = ['userId', 'version', 'credentials']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate version format
        version = data['version']
        if not re.match(r'^\d+\.\d+$', version):
            raise ValueError(f"Invalid version format: {version}")
        
        # Validate userId is integer
        if not isinstance(data['userId'], int) or data['userId'] < 1:
            raise ValueError(f"Invalid userId: {data['userId']}")
    
    def get_credential(self, service: str, key: str) -> Optional[str]:
        """
        Get credential value.
        
        Args:
            service: Service name (e.g., 'tmdb', 'openai', 'youtube')
            key: Credential key (e.g., 'api_key', 'token')
            
        Returns:
            Credential value or None if not found
            
        Example:
            >>> profile = UserProfile.load(user_id=1)
            >>> tmdb_key = profile.get_credential('tmdb', 'api_key')
        """
        # Check credentials section
        if service in self.credentials:
            if key in self.credentials[service]:
                value = self.credentials[service][key]
                return value if value else None
        
        # Check online_services section
        if service in self.online_services:
            if key in self.online_services[service]:
                value = self.online_services[service][key]
                return value if value else None
        
        return None
    
    def set_credential(self, service: str, key: str, value: str) -> None:
        """
        Set credential value.
        
        Args:
            service: Service name
            key: Credential key
            value: Credential value
            
        Example:
            >>> profile.set_credential('youtube', 'api_key', 'AIzaSy...')
            >>> profile.save()
        """
        # Update in appropriate section
        if service in self.credentials:
            if service not in self.credentials:
                self.credentials[service] = {}
            self.credentials[service][key] = value
        elif service in self.online_services:
            if service not in self.online_services:
                self.online_services[service] = {}
            self.online_services[service][key] = value
        else:
            # Add to online_services by default
            if 'online_services' not in self._data:
                self._data['online_services'] = {}
            self._data['online_services'][service] = {key: value}
            self.online_services[service] = {key: value}
    
    def has_service(self, service: str) -> bool:
        """Check if service is configured and enabled."""
        if service in self.online_services:
            return self.online_services[service].get('enabled', False)
        return False
    
    def validate_for_workflow(self, workflow: str) -> None:
        """
        Validate required credentials for workflow.
        
        Args:
            workflow: Workflow name ('transcribe', 'translate', 'subtitle')
            
        Raises:
            ValueError: Missing required credentials with helpful message
            
        Example:
            >>> profile.validate_for_workflow('subtitle')
            # Raises if TMDB key missing
        """
        # Define required credentials per workflow
        WORKFLOW_REQUIREMENTS = {
            'transcribe': [
                ('huggingface', 'token', 'HuggingFace token (for WhisperX ASR)'),
            ],
            'translate': [
                ('huggingface', 'token', 'HuggingFace token (for WhisperX ASR)'),
            ],
            'subtitle': [
                ('huggingface', 'token', 'HuggingFace token (for WhisperX ASR)'),
                ('tmdb', 'api_key', 'TMDB API key (for character names)'),
            ],
        }
        
        if workflow not in WORKFLOW_REQUIREMENTS:
            raise ValueError(f"Unknown workflow: {workflow}")
        
        missing = []
        for service, key, description in WORKFLOW_REQUIREMENTS[workflow]:
            value = self.get_credential(service, key)
            if not value:
                missing.append((service, key, description))
        
        if missing:
            error_msg = f"❌ {workflow.capitalize()} workflow requires missing credentials:\n\n"
            for service, key, description in missing:
                error_msg += f"  • {description}\n"
                error_msg += f"    Add to: users/{self.user_id}/profile.json\n"
                error_msg += f"    Path: credentials.{service}.{key}\n\n"
            error_msg += "Fix:\n"
            error_msg += f"  1. Edit: users/{self.user_id}/profile.json\n"
            error_msg += f"  2. Add missing credentials\n"
            raise ValueError(error_msg)
    
    def save(self) -> None:
        """
        Save profile to disk.
        
        Example:
            >>> profile.set_credential('youtube', 'api_key', 'AIza...')
            >>> profile.save()
        """
        # Update internal data
        self._data['userId'] = self.user_id
        self._data['version'] = self.version
        self._data['user'] = self.user
        self._data['credentials'] = self.credentials
        self._data['online_services'] = self.online_services
        self._data['preferences'] = self.preferences
        
        # Ensure directory exists
        profile_path = self.profile_path
        profile_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write JSON
        with open(profile_path, 'w') as f:
            json.dump(self._data, f, indent=2)
        
        logger.info(f"Saved profile: userId={self.user_id}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary."""
        return {
            'userId': self.user_id,
            'version': self.version,
            'user': self.user,
            'credentials': self.credentials,
            'online_services': self.online_services,
            'preferences': self.preferences
        }
    
    def __repr__(self) -> str:
        return f"UserProfile(userId={self.user_id}, name={self.user.get('name', 'Unknown')})"


# Convenience functions
def get_user_profile(user_id: int) -> UserProfile:
    """Convenience function to load user profile."""
    return UserProfile.load(user_id=user_id)


def create_user(name: str = "", email: str = "", **credentials) -> int:
    """Convenience function to create new user."""
    return UserProfile.create_new_user(name=name, email=email, **credentials)


def list_all_users() -> list:
    """List all existing userIds."""
    return UserIdManager.list_users()
