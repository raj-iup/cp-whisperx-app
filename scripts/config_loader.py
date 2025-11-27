"""
config_loader.py - Configuration loader for whisperx-app

Loads configuration from:
- ./config/.env (all tunables)
- ./config/secrets.json (tokens/keys)

NEVER reads from shell environment (os.environ) directly.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import dotenv_values


class Config:
    """Configuration container for whisperx-app"""

    def __init__(self, project_root: Optional[Path] = None):
        if project_root is None:
            # Default: go up one level from scripts/ to project root
            project_root = Path(__file__).parent.parent

        self.project_root = Path(project_root)
        # Use .env.pipeline as the main config file
        self.env_file = self.project_root / "config" / ".env.pipeline"
        self.secrets_file = self.project_root / "config" / "secrets.json"

        self._env: Dict[str, Any] = {}
        self._secrets: Dict[str, str] = {}

        self._load_env()
        self._load_secrets()

    def _load_env(self):
        """Load .env file"""
        if not self.env_file.exists():
            raise FileNotFoundError(f"Config file not found: {self.env_file}")

        # Load all values as strings first
        raw_env = dotenv_values(str(self.env_file))

        # Convert types
        for key, value in raw_env.items():
            if value is None or value == "":
                self._env[key] = None
            elif value.lower() in ("true", "false"):
                self._env[key] = value.lower() == "true"
            elif value.isdigit():
                self._env[key] = int(value)
            else:
                try:
                    self._env[key] = float(value)
                except ValueError:
                    self._env[key] = value

    def _load_secrets(self):
        """Load secrets.json"""
        if not self.secrets_file.exists():
            raise FileNotFoundError(f"Secrets file not found: {self.secrets_file}")

        with open(self.secrets_file, 'r', encoding='utf-8', errors='replace') as f:
            self._secrets = json.load(f)

    def get(self, key: str, default: Any = None) -> Any:
        """Get config value from .env"""
        return self._env.get(key, default)

    def get_secret(self, key: str) -> str:
        """Get secret value from secrets.json"""
        if key not in self._secrets:
            raise KeyError(f"Secret '{key}' not found in {self.secrets_file}")
        return self._secrets[key]

    # Convenience properties for common config values
    @property
    def input_file(self) -> Optional[str]:
        return self.get("INPUT_FILE")

    @property
    def input_url(self) -> Optional[str]:
        return self.get("INPUT_URL")

    @property
    def output_root(self) -> Path:
        path = self.get("OUTPUT_ROOT", "./out")
        return self.project_root / path if not Path(path).is_absolute() else Path(path)

    @property
    def log_root(self) -> Path:
        path = self.get("LOG_ROOT", "./logs")
        return self.project_root / path if not Path(path).is_absolute() else Path(path)

    @property
    def window_seconds(self) -> int:
        return self.get("WINDOW_SECONDS", 45)

    @property
    def stride_seconds(self) -> int:
        return self.get("STRIDE_SECONDS", 15)

    @property
    def bias_topk(self) -> int:
        return self.get("BIAS_TOPK", 10)

    @property
    def bias_decay(self) -> float:
        return self.get("BIAS_DECAY", 0.9)

    @property
    def infer_tmdb(self) -> bool:
        return self.get("INFER_TMDB", True)

    @property
    def second_pass_enabled(self) -> bool:
        return self.get("SECOND_PASS_ENABLED", True)

    @property
    def second_pass_backend(self) -> str:
        return self.get("SECOND_PASS_BACKEND", "opus-mt")

    @property
    def ner_enabled(self) -> bool:
        return self.get("NER_ENABLED", True)

    @property
    def ner_preset(self) -> str:
        return self.get("NER_PRESET", "en_core_web_trf")

    @property
    def whisperx_model(self) -> str:
        # Support both WHISPER_MODEL and WHISPERX_MODEL for backwards compatibility
        return self.get("WHISPER_MODEL", self.get("WHISPERX_MODEL", "large-v3"))
    
    @property
    def whisper_compute_type(self) -> str:
        return self.get("WHISPER_COMPUTE_TYPE", "int8")
    
    @property
    def batch_size(self) -> int:
        return self.get("BATCH_SIZE", 16)
    
    @property
    def whisper_backend(self) -> str:
        return self.get("WHISPER_BACKEND", "whisperx")
    
    @property
    def indictrans2_device(self) -> str:
        return self.get("INDICTRANS2_DEVICE", "cpu")

    @property
    def device_whisperx(self) -> str:
        return self.get("DEVICE_WHISPERX", "cpu")

    @property
    def device_diarization(self) -> str:
        return self.get("DEVICE_DIARIZATION", "cpu")

    @property
    def device_second_pass(self) -> str:
        return self.get("DEVICE_SECOND_PASS", "cpu")

    @property
    def device_spacy(self) -> str:
        return self.get("DEVICE_SPACY", "cpu")

    @property
    def src_lang(self) -> str:
        return self.get("SRC_LANG", "hi")

    @property
    def tgt_lang(self) -> str:
        return self.get("TGT_LANG", "en")

    @property
    def hf_token(self) -> str:
        return self.get_secret("hf_token")

    @property
    def tmdb_api_key(self) -> str:
        return self.get_secret("tmdb_api_key")

    @property
    def pyannote_token(self) -> str:
        return self.get_secret("pyannote_token")

    def __repr__(self):
        return f"Config(env_file={self.env_file}, secrets_file={self.secrets_file})"


def load_config(project_root: Optional[Path] = None) -> Config:
    """
    Load configuration from ./config/.env and ./config/secrets.json

    Args:
        project_root: Path to project root (default: auto-detect)

    Returns:
        Config object with all settings

    Example:
        >>> config = load_config()
        >>> print(config.window_seconds)
        45
        >>> print(config.hf_token)
        'hf_...'
    """
    return Config(project_root)
