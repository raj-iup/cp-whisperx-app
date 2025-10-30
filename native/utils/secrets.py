"""
Secrets manager for native MPS pipeline.
Loads API keys and tokens from config/secrets.json with fallback to environment variables.
"""
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any


class SecretsManager:
    """Manage secrets and API keys for the pipeline."""
    
    def __init__(self, secrets_file: str = "config/secrets.json"):
        """
        Initialize secrets manager.
        
        Args:
            secrets_file: Path to secrets JSON file
        """
        self.secrets_file = Path(secrets_file)
        self.secrets: Dict[str, Any] = {}
        self._load_secrets()
    
    def _load_secrets(self):
        """Load secrets from file and environment variables."""
        # Try to load from secrets.json
        if self.secrets_file.exists():
            try:
                with open(self.secrets_file, 'r') as f:
                    file_secrets = json.load(f)
                    # Filter out empty values
                    self.secrets = {
                        k: v for k, v in file_secrets.items() 
                        if v and str(v).strip()
                    }
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load secrets file: {e}")
                self.secrets = {}
        
        # Environment variables take precedence
        env_keys = [
            'TMDB_API_KEY',
            'HF_TOKEN',
            'PYANNOTE_API_TOKEN',
            'PYANNOTE_TOKEN',
            'OPENAI_API_KEY',
        ]
        
        for key in env_keys:
            env_value = os.getenv(key)
            if env_value and env_value.strip():
                # Convert to lowercase with underscores for consistency
                normalized_key = key.lower()
                self.secrets[normalized_key] = env_value.strip()
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a secret by key.
        
        Args:
            key: Secret key (case-insensitive)
            default: Default value if not found
        
        Returns:
            Secret value or default
        """
        # Normalize key to lowercase
        key_lower = key.lower()
        
        # Try direct match
        if key_lower in self.secrets:
            return self.secrets[key_lower]
        
        # Try with underscores instead of hyphens
        key_normalized = key_lower.replace('-', '_')
        if key_normalized in self.secrets:
            return self.secrets[key_normalized]
        
        # Try environment variable
        env_value = os.getenv(key.upper())
        if env_value and env_value.strip():
            return env_value.strip()
        
        return default
    
    def get_tmdb_api_key(self) -> Optional[str]:
        """Get TMDB API key."""
        return self.get('tmdb_api_key')
    
    def get_hf_token(self) -> Optional[str]:
        """Get HuggingFace token."""
        return self.get('hf_token')
    
    def get_pyannote_token(self) -> Optional[str]:
        """Get PyAnnote token (tries multiple key names)."""
        # Try different possible key names
        for key in ['pyannote_token', 'pyannote_api_token', 'hf_token']:
            token = self.get(key)
            if token:
                return token
        return None
    
    def has_secret(self, key: str) -> bool:
        """Check if a secret exists and is non-empty."""
        value = self.get(key)
        return value is not None and value.strip() != ''
    
    def export_to_env(self):
        """Export all secrets as environment variables."""
        for key, value in self.secrets.items():
            if value:
                # Convert to uppercase with underscores
                env_key = key.upper().replace('-', '_')
                os.environ[env_key] = str(value)
    
    def get_all(self) -> Dict[str, str]:
        """Get all secrets (for debugging - be careful with logging!)."""
        return dict(self.secrets)
    
    def mask_secret(self, secret: str, show_chars: int = 4) -> str:
        """
        Mask a secret for safe logging.
        
        Args:
            secret: Secret to mask
            show_chars: Number of characters to show
        
        Returns:
            Masked secret string
        """
        if not secret or len(secret) <= show_chars:
            return "***"
        return secret[:show_chars] + "..." + "*" * (len(secret) - show_chars)
    
    def summary(self) -> Dict[str, str]:
        """Get a summary of available secrets (masked)."""
        return {
            key: self.mask_secret(value) if value else "Not set"
            for key, value in {
                'tmdb_api_key': self.get_tmdb_api_key(),
                'hf_token': self.get_hf_token(),
                'pyannote_token': self.get_pyannote_token(),
            }.items()
        }


# Global instance for easy access
_secrets_manager: Optional[SecretsManager] = None


def get_secrets_manager(secrets_file: str = "config/secrets.json") -> SecretsManager:
    """
    Get or create the global secrets manager instance.
    
    Args:
        secrets_file: Path to secrets JSON file
    
    Returns:
        SecretsManager instance
    """
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = SecretsManager(secrets_file)
    return _secrets_manager


def load_secrets_to_env(secrets_file: str = "config/secrets.json"):
    """
    Load secrets from file and export to environment variables.
    
    Args:
        secrets_file: Path to secrets JSON file
    """
    manager = get_secrets_manager(secrets_file)
    manager.export_to_env()


# Convenience functions
def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get a secret by key."""
    return get_secrets_manager().get(key, default)


def get_tmdb_api_key() -> Optional[str]:
    """Get TMDB API key."""
    return get_secrets_manager().get_tmdb_api_key()


def get_hf_token() -> Optional[str]:
    """Get HuggingFace token."""
    return get_secrets_manager().get_hf_token()


def get_pyannote_token() -> Optional[str]:
    """Get PyAnnote token."""
    return get_secrets_manager().get_pyannote_token()
