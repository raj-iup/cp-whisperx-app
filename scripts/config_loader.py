"""
logger = get_logger(__name__)

config_loader.py - Configuration loader for whisperx-app

Loads configuration from:
- ./config/.env (all tunables)
- ./config/secrets.json (tokens/keys)

NEVER reads from shell environment (os.environ) directly.

Implements config caching to reduce disk I/O (Phase 3 Optimization).
"""

# Standard library
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Third-party
from dotenv import dotenv_values

# Local
from shared.logger import get_logger


# Config cache for performance optimization (Phase 3)
_CONFIG_CACHE: Dict[str, 'Config'] = {}


class Config:
    """Configuration container for whisperx-app"""

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize configuration.
        
        Args:
            project_root: Path to project root directory. If None, auto-detects.
        """
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

    def _load_env(self) -> None:
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

    def _load_secrets(self) -> None:
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
        """Get input_file configuration value."""
        return self.get("INPUT_FILE")

    @property
    def input_url(self) -> Optional[str]:
        """Get input_url configuration value."""
        return self.get("INPUT_URL")

    @property
    def output_root(self) -> Path:
        """Get output_root configuration value."""
        path = self.get("OUTPUT_ROOT", "./out")
        return self.project_root / path if not Path(path).is_absolute() else Path(path)

    @property
    def log_root(self) -> Path:
        """Get log_root configuration value."""
        path = self.get("LOG_ROOT", "./logs")
        return self.project_root / path if not Path(path).is_absolute() else Path(path)

    @property
    def window_seconds(self) -> int:
        """Get window_seconds configuration value."""
        return self.get("WINDOW_SECONDS", 45)

    @property
    def stride_seconds(self) -> int:
        """Get stride_seconds configuration value."""
        return self.get("STRIDE_SECONDS", 15)

    @property
    def bias_topk(self) -> int:
        """Get bias_topk configuration value."""
        return self.get("BIAS_TOPK", 10)

    @property
    def bias_decay(self) -> float:
        """Get bias_decay configuration value."""
        return self.get("BIAS_DECAY", 0.9)

    @property
    def infer_tmdb(self) -> bool:
        """Get infer_tmdb configuration value."""
        return self.get("INFER_TMDB", True)

    @property
    def second_pass_enabled(self) -> bool:
        """Get second_pass_enabled configuration value."""
        return self.get("SECOND_PASS_ENABLED", True)

    @property
    def second_pass_backend(self) -> str:
        """Get second_pass_backend configuration value."""
        return self.get("SECOND_PASS_BACKEND", "opus-mt")

    @property
    def ner_enabled(self) -> bool:
        """Get ner_enabled configuration value."""
        return self.get("NER_ENABLED", True)

    @property
    def ner_preset(self) -> str:
        """Get ner_preset configuration value."""
        return self.get("NER_PRESET", "en_core_web_trf")

    @property
    def whisperx_model(self) -> str:
        """Get whisperx_model configuration value."""
        # Support both WHISPER_MODEL and WHISPERX_MODEL for backwards compatibility
        return self.get("WHISPER_MODEL", self.get("WHISPERX_MODEL", "large-v3"))
    
    @property
    def whisper_compute_type(self) -> str:
        """Get whisper_compute_type configuration value."""
        return self.get("WHISPER_COMPUTE_TYPE", "int8")
    
    @property
    def batch_size(self) -> int:
        """Get batch_size configuration value."""
        return self.get("BATCH_SIZE", 16)
    
    @property
    def whisper_backend(self) -> str:
        """Get whisper_backend configuration value."""
        return self.get("WHISPER_BACKEND", "whisperx")
    
    @property
    def indictrans2_device(self) -> str:
        """Get indictrans2_device configuration value."""
        return self.get("INDICTRANS2_DEVICE", "cpu")

    @property
    def device_whisperx(self) -> str:
        """Get device_whisperx configuration value."""
        return self.get("DEVICE_WHISPERX", "cpu")

    @property
    def device_diarization(self) -> str:
        """Get device_diarization configuration value."""
        return self.get("DEVICE_DIARIZATION", "cpu")

    @property
    def device_second_pass(self) -> str:
        """Get device_second_pass configuration value."""
        return self.get("DEVICE_SECOND_PASS", "cpu")

    @property
    def device_spacy(self) -> str:
        """Get device_spacy configuration value."""
        return self.get("DEVICE_SPACY", "cpu")

    @property
    def src_lang(self) -> str:
        """Get src_lang configuration value."""
        return self.get("SRC_LANG", "hi")

    @property
    def tgt_lang(self) -> str:
        """Get tgt_lang configuration value."""
        return self.get("TGT_LANG", "en")

    @property
    def hf_token(self) -> str:
        """Get hf_token configuration value."""
        return self.get_secret("hf_token")

    @property
    def tmdb_api_key(self) -> str:
        """Get tmdb_api_key configuration value."""
        return self.get_secret("tmdb_api_key")

    @property
    def pyannote_token(self) -> str:
        """Get pyannote_token configuration value."""
        return self.get_secret("pyannote_token")

    # Phase 3: Segment Merging Configuration
    @property
    def segment_merging_enabled(self) -> bool:
        """Get segment_merging_enabled configuration value."""
        return self.get("SEGMENT_MERGING_ENABLED", True)

    @property
    def segment_merge_max_gap(self) -> float:
        """Get segment_merge_max_gap configuration value."""
        return self.get("SEGMENT_MERGE_MAX_GAP", 1.5)

    @property
    def segment_merge_max_chars(self) -> int:
        """Get segment_merge_max_chars configuration value."""
        return self.get("SEGMENT_MERGE_MAX_CHARS", 84)

    @property
    def segment_merge_max_duration(self) -> float:
        """Get segment_merge_max_duration configuration value."""
        return self.get("SEGMENT_MERGE_MAX_DURATION", 7.0)

    @property
    def segment_merge_min_cps(self) -> float:
        """Get segment_merge_min_cps configuration value."""
        return self.get("SEGMENT_MERGE_MIN_CPS", 17.0)

    @property
    def segment_merge_max_cps(self) -> float:
        """Get segment_merge_max_cps configuration value."""
        return self.get("SEGMENT_MERGE_MAX_CPS", 20.0)

    @property
    def subtitle_max_line_length(self) -> int:
        """Get subtitle_max_line_length configuration value."""
        return self.get("SUBTITLE_MAX_LINE_LENGTH", 42)

    @property
    def subtitle_max_lines(self) -> int:
        """Get subtitle_max_lines configuration value."""
        return self.get("SUBTITLE_MAX_LINES", 2)

    @property
    def subtitle_min_duration(self) -> float:
        """Get subtitle_min_duration configuration value."""
        return self.get("SUBTITLE_MIN_DURATION", 1.0)

    # Phase 4: Translation Protection and Validation
    @property
    def translation_glossary_protection(self) -> bool:
        """Get translation_glossary_protection configuration value."""
        return self.get("TRANSLATION_GLOSSARY_PROTECTION", True)

    @property
    def translation_validation_enabled(self) -> bool:
        """Get translation_validation_enabled configuration value."""
        return self.get("TRANSLATION_VALIDATION_ENABLED", True)

    @property
    def translation_max_length_ratio(self) -> float:
        """Get translation_max_length_ratio configuration value."""
        return self.get("TRANSLATION_MAX_LENGTH_RATIO", 3.0)

    @property
    def translation_min_length_ratio(self) -> float:
        """Get translation_min_length_ratio configuration value."""
        return self.get("TRANSLATION_MIN_LENGTH_RATIO", 0.3)

    def validate_whisperx_config(self) -> tuple[bool, list[str]]:
        """
        Validate WhisperX configuration for optimal subtitle accuracy (Phase 1).

        Returns:
            Tuple of (is_valid, list of issues/warnings)
        """
        issues = []

        # Check critical anti-hallucination settings
        condition_on_previous = self.get('WHISPER_CONDITION_ON_PREVIOUS_TEXT', True)
        if condition_on_previous:
            issues.append(
                "CRITICAL: WHISPER_CONDITION_ON_PREVIOUS_TEXT=true may cause hallucinations. "
                "Recommended: false"
            )

        # Check logprob threshold
        logprob = self.get('WHISPER_LOGPROB_THRESHOLD', -1.0)
        if logprob < -0.8:
            issues.append(
                f"WARNING: WHISPER_LOGPROB_THRESHOLD={logprob} is too permissive. "
                f"Recommended: -0.7 for better quality"
            )

        # Check no_speech threshold
        no_speech = self.get('WHISPER_NO_SPEECH_THRESHOLD', 0.6)
        if no_speech < 0.6:
            issues.append(
                f"WARNING: WHISPER_NO_SPEECH_THRESHOLD={no_speech} is too low. "
                f"Recommended: 0.65 to reduce false speech detection"
            )

        # Check compression ratio
        compression = self.get('WHISPER_COMPRESSION_RATIO_THRESHOLD', 2.4)
        if compression > 2.4:
            issues.append(
                f"WARNING: WHISPER_COMPRESSION_RATIO_THRESHOLD={compression} is too permissive. "
                f"Recommended: 2.2 to catch repetitive hallucinations sooner"
            )

        # Check temperature count (Phase 1 optimization)
        temperature = self.get('WHISPER_TEMPERATURE', '0.0,0.2,0.4,0.6,0.8,1.0')
        if isinstance(temperature, str):
            temp_count = len(temperature.split(','))
            if temp_count > 3:
                issues.append(
                    f"OPTIMIZATION: WHISPER_TEMPERATURE has {temp_count} values. "
                    f"Recommended: 3 values (0.0,0.2,0.4) for 20-30% speed improvement"
                )

        # Check minimum duration setting
        min_duration = self.get('WHISPER_MIN_DURATION')
        if min_duration is None:
            issues.append(
                "INFO: WHISPER_MIN_DURATION not set. "
                "Recommended: 0.1 to filter zero-duration segments"
            )

        is_valid = not any('CRITICAL' in issue for issue in issues)
        return is_valid, issues

    def print_validation_report(self) -> None:
        """Print validation report with color-coded issues"""
        is_valid, issues = self.validate_whisperx_config()

        if not issues:
            logger.info("✅ Configuration validation passed - all settings optimal")
            return

        logger.info("📊 Configuration Validation Report:")
        logger.info("=" * 80)

        for issue in issues:
            if 'CRITICAL' in issue:
                logger.info(f"🔴 {issue}")
            elif 'WARNING' in issue:
                logger.info(f"🟡 {issue}")
            else:
                logger.info(f"ℹ️  {issue}")

        logger.info("=" * 80)

        if not is_valid:
            logger.info("❌ Validation failed - critical issues found")
        else:
            logger.warning(" Validation passed with warnings - consider optimizing")

    def __repr__(self) -> str:
        """Return string representation of Config."""
        return f"Config(env_file={self.env_file}, secrets_file={self.secrets_file})"


def load_config(project_root: Optional[Path] = None, force_reload: bool = False) -> Config:
    """
    Load configuration from ./config/.env and ./config/secrets.json with caching.
    
    Config is cached in memory after first load to reduce disk I/O.
    Phase 3 Optimization: Expected 5-10% faster stage initialization.

    Args:
        project_root: Path to project root (default: auto-detect)
        force_reload: Force reload from disk, bypass cache (default: False)

    Returns:
        Config object with all settings

    Example:
        >>> config = load_config()
        >>> logger.info(config.window_seconds)
        45
        >>> logger.info(config.hf_token)
        'hf_...'
    """
    # Generate cache key
    cache_key = str(project_root) if project_root else 'default'
    
    # Return cached config if available and not forcing reload
    if not force_reload and cache_key in _CONFIG_CACHE:
        return _CONFIG_CACHE[cache_key]
    
    # Load from disk
    config = Config(project_root)
    
    # Cache for future use
    _CONFIG_CACHE[cache_key] = config
    
    return config


def clear_config_cache() -> None:
    """
    Clear the config cache.
    
    Useful for testing or when config files are modified at runtime.
    """
    global _CONFIG_CACHE
    _CONFIG_CACHE.clear()
