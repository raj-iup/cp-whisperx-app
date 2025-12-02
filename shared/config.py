"""
Shared configuration loader for all pipeline containers.
Reads configuration from .env file and provides typed access.
"""
import os
import json
from pathlib import Path
from typing import Optional, Any

# Try to import pydantic_settings, fall back to simple implementation if not available
try:
    from pydantic_settings import BaseSettings
    from pydantic import Field, field_validator
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    # Provide dummy implementations
    class BaseSettings:
        pass
    def Field(*args, **kwargs):
        return None
    def field_validator(*args, **kwargs):
        def decorator(func):
            return func
        return decorator


class PipelineConfig(BaseSettings):
    """Pipeline configuration with validation."""
    
    # Job Configuration
    job_id: str = Field(default="", env="JOB_ID")
    user_id: int = Field(default=1, env="USER_ID")
    title: Optional[str] = Field(default=None, env="TITLE")
    year: Optional[int] = Field(default=None, env="YEAR")
    
    # Workflow Configuration
    workflow_mode: str = Field(default="subtitle-gen", env="WORKFLOW_MODE")
    source_language: Optional[str] = Field(default=None, env="SOURCE_LANGUAGE")
    target_language: Optional[str] = Field(default=None, env="TARGET_LANGUAGE")
    
    # Media Processing Configuration
    media_processing_mode: str = Field(default="full", env="MEDIA_PROCESSING_MODE")
    media_start_time: Optional[str] = Field(default=None, env="MEDIA_START_TIME")
    media_end_time: Optional[str] = Field(default=None, env="MEDIA_END_TIME")
    
    @field_validator('title', mode='before')
    @classmethod
    def empty_str_to_none_title(cls, v):
        """Convert empty string to None for optional title."""
        if v == '' or v is None:
            return None
        return v
    
    @field_validator('year', mode='before')
    @classmethod
    def empty_str_to_none_year(cls, v):
        """Convert empty string to None for optional year."""
        if v == '' or v is None:
            return None
        return int(v)
    
    @field_validator('media_start_time', 'media_end_time', mode='before')
    @classmethod
    def empty_str_to_none_time(cls, v):
        """Convert empty string to None for optional time values."""
        if v == '' or v is None:
            return None
        return v
    
    # Docker Registry
    docker_registry: str = Field(default="rajiup", env="DOCKER_REGISTRY")
    docker_tag: str = Field(default="latest", env="DOCKER_TAG")
    
    # Paths
    in_root: str = Field(default="", env="IN_ROOT")  # Path to input media in job directory
    output_root: str = Field(default="./out", env="OUTPUT_ROOT")
    log_root: str = Field(default="./logs", env="LOG_ROOT")
    temp_root: str = Field(default="./temp", env="TEMP_ROOT")
    
    # Logging
    log_level: str = Field(default="info", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    log_to_console: bool = Field(default=True, env="LOG_TO_CONSOLE")
    log_to_file: bool = Field(default=True, env="LOG_TO_FILE")
    
    # Secrets
    secrets_path: str = Field(default="./config/secrets.json", env="SECRETS_PATH")
    tmdb_api_key: str = Field(default="", env="TMDB_API_KEY")
    hf_token: str = Field(default="", env="HF_TOKEN")
    
    # Pipeline Steps
    step_demux: bool = Field(default=True, env="STEP_DEMUX")
    step_tmdb_metadata: bool = Field(default=True, env="STEP_TMDB_METADATA")
    step_pre_asr_ner: bool = Field(default=True, env="STEP_PRE_ASR_NER")
    step_vad_silero: bool = Field(default=True, env="STEP_VAD_SILERO")
    step_silero_vad: bool = Field(default=True, env="STEP_SILERO_VAD")
    step_vad_pyannote: bool = Field(default=True, env="STEP_VAD_PYANNOTE")
    step_pyannote_vad: bool = Field(default=True, env="STEP_PYANNOTE_VAD")
    step_diarization: bool = Field(default=True, env="STEP_DIARIZATION")
    step_whisperx: bool = Field(default=True, env="STEP_WHISPERX")
    step_post_asr_ner: bool = Field(default=True, env="STEP_POST_ASR_NER")
    step_subtitle_gen: bool = Field(default=True, env="STEP_SUBTITLE_GEN")
    step_mux: bool = Field(default=True, env="STEP_MUX")
    
    # FFmpeg Demux
    audio_sample_rate: int = Field(default=16000, env="AUDIO_SAMPLE_RATE")
    audio_channels: int = Field(default=1, env="AUDIO_CHANNELS")
    audio_format: str = Field(default="wav", env="AUDIO_FORMAT")
    audio_codec: str = Field(default="pcm_s16le", env="AUDIO_CODEC")
    
    # TMDB
    tmdb_enabled: bool = Field(default=True, env="TMDB_ENABLED")
    tmdb_language: str = Field(default="en-US", env="TMDB_LANGUAGE")
    tmdb_infer_from_filename: bool = Field(default=True, env="TMDB_INFER_FROM_FILENAME")
    
    # Pre-ASR NER
    pre_ner_enabled: bool = Field(default=True, env="PRE_NER_ENABLED")
    pre_ner_model: str = Field(default="en_core_web_trf", env="PRE_NER_MODEL")
    pre_ner_confidence_threshold: float = Field(default=0.0, env="PRE_NER_CONFIDENCE")
    pre_ner_entity_types: str = Field(default="PERSON,ORG,GPE,LOC,FAC", env="PRE_NER_ENTITY_TYPES")
    
    # Bias Injection
    bias_enabled: bool = Field(default=True, env="BIAS_ENABLED")
    bias_window_seconds: int = Field(default=45, env="BIAS_WINDOW_SECONDS")
    bias_stride_seconds: int = Field(default=15, env="BIAS_STRIDE_SECONDS")
    bias_topk: int = Field(default=10, env="BIAS_TOPK")
    bias_min_confidence: float = Field(default=0.6, env="BIAS_MIN_CONFIDENCE")
    
    # Song Bias Injection (Stage 7)
    song_bias_enabled: bool = Field(default=True, env="SONG_BIAS_ENABLED")
    song_bias_fuzzy_threshold: float = Field(default=0.80, env="SONG_BIAS_FUZZY_THRESHOLD")
    
    # Soundtrack Enrichment (Stage 2 - TMDB)
    use_musicbrainz: bool = Field(default=True, env="USE_MUSICBRAINZ")
    cache_musicbrainz: bool = Field(default=True, env="CACHE_MUSICBRAINZ")
    
    # Whisper/WhisperX - Basic parameters
    whisper_model: str = Field(default="large-v3", env="WHISPER_MODEL")
    whisper_compute_type: str = Field(default="int8", env="WHISPER_COMPUTE_TYPE")
    whisper_batch_size: int = Field(default=16, env="WHISPER_BATCH_SIZE")
    whisper_language: str = Field(default="hi", env="WHISPER_LANGUAGE")
    whisper_task: str = Field(default="translate", env="WHISPER_TASK")
    
    # Whisper/WhisperX - Advanced transcription parameters
    whisper_temperature: str = Field(default="0.0,0.2,0.4,0.6,0.8,1.0", env="WHISPER_TEMPERATURE")
    whisper_beam_size: int = Field(default=5, env="WHISPER_BEAM_SIZE")
    whisper_best_of: int = Field(default=5, env="WHISPER_BEST_OF")
    whisper_patience: float = Field(default=1.0, env="WHISPER_PATIENCE")
    whisper_length_penalty: float = Field(default=1.0, env="WHISPER_LENGTH_PENALTY")
    whisper_no_speech_threshold: float = Field(default=0.6, env="WHISPER_NO_SPEECH_THRESHOLD")
    whisper_logprob_threshold: float = Field(default=-1.0, env="WHISPER_LOGPROB_THRESHOLD")
    whisper_compression_ratio_threshold: float = Field(default=2.4, env="WHISPER_COMPRESSION_RATIO_THRESHOLD")
    whisper_condition_on_previous_text: bool = Field(default=True, env="WHISPER_CONDITION_ON_PREVIOUS_TEXT")
    whisper_initial_prompt: str = Field(default="", env="WHISPER_INITIAL_PROMPT")
    
    # WhisperX specific
    whisperx_device: str = Field(default="auto", env="WHISPERX_DEVICE")  # auto, cpu, cuda, mps
    whisperx_backend: str = Field(default="auto", env="WHISPERX_BACKEND")  # auto, whisperx, mlx, ctranslate2
    whisperx_align_extend: float = Field(default=2.0, env="WHISPERX_ALIGN_EXTEND")
    whisperx_align_from_prev: bool = Field(default=True, env="WHISPERX_ALIGN_FROM_PREV")
    
    # Languages (support both naming conventions)
    src_lang: str = Field(default="hi", env="SRC_LANG")
    tgt_lang: str = Field(default="en", env="TGT_LANG")
    source_lang: str = Field(default="hi", env="SOURCE_LANG")
    target_lang: str = Field(default="en", env="TARGET_LANG")
    
    # Silero VAD
    silero_threshold: float = Field(default=0.6, env="SILERO_THRESHOLD")
    silero_min_speech_duration_ms: int = Field(default=250, env="SILERO_MIN_SPEECH_DURATION_MS")
    silero_min_silence_duration_ms: int = Field(default=300, env="SILERO_MIN_SILENCE_DURATION_MS")
    silero_merge_gap_sec: float = Field(default=0.35, env="SILERO_MERGE_GAP_SEC")
    
    # PyAnnote VAD
    pyannote_onset: float = Field(default=0.5, env="PYANNOTE_ONSET")
    pyannote_offset: float = Field(default=0.5, env="PYANNOTE_OFFSET")
    pyannote_min_duration_on: float = Field(default=0.0, env="PYANNOTE_MIN_DURATION_ON")
    pyannote_min_duration_off: float = Field(default=0.0, env="PYANNOTE_MIN_DURATION_OFF")
    pyannote_device: str = Field(default="auto", env="PYANNOTE_DEVICE")  # auto, cpu, cuda, mps
    pyannote_window_pad: float = Field(default=0.25, env="PYANNOTE_WINDOW_PAD")
    pyannote_merge_gap: float = Field(default=0.2, env="PYANNOTE_MERGE_GAP")
    
    # Diarization
    diarization_min_speakers: int = Field(default=1, env="DIARIZATION_MIN_SPEAKERS")
    diarization_max_speakers: int = Field(default=10, env="DIARIZATION_MAX_SPEAKERS")
    diarization_model: str = Field(default="pyannote/speaker-diarization-3.1", env="DIARIZATION_MODEL")
    diarization_device: str = Field(default="auto", env="DIARIZATION_DEVICE")  # auto, cpu, cuda, mps
    diarization_method: str = Field(default="pyannote", env="DIARIZATION_METHOD")
    speaker_map: str = Field(default="", env="SPEAKER_MAP")
    
    # Subtitle generation
    subtitle_format: str = Field(default="srt", env="SUBTITLE_FORMAT")
    subtitle_max_line_length: int = Field(default=42, env="SUBTITLE_MAX_LINE_LENGTH")
    subtitle_max_lines: int = Field(default=2, env="SUBTITLE_MAX_LINES")
    subtitle_include_speaker_labels: bool = Field(default=True, env="SUBTITLE_INCLUDE_SPEAKER_LABELS")
    subtitle_speaker_format: str = Field(default="[{speaker}]", env="SUBTITLE_SPEAKER_FORMAT")
    subtitle_word_level_timestamps: bool = Field(default=False, env="SUBTITLE_WORD_LEVEL_TIMESTAMPS")
    subtitle_max_duration: float = Field(default=7.0, env="SUBTITLE_MAX_DURATION")
    subtitle_min_duration: float = Field(default=1.0, env="SUBTITLE_MIN_DURATION")
    subtitle_merge_short: bool = Field(default=True, env="SUBTITLE_MERGE_SHORT")
    
    # ========================================================================
    # Glossary System Configuration
    # ========================================================================
    
    # Glossary Builder Configuration (Stage 3)
    glossary_enable: bool = Field(default=True, env="GLOSSARY_ENABLE")
    glossary_seed_sources: str = Field(default="asr,tmdb,master", env="GLOSSARY_SEED_SOURCES")
    glossary_min_conf: float = Field(default=0.55, env="GLOSSARY_MIN_CONF")
    glossary_master: str = Field(default="glossary/hinglish_master.tsv", env="GLOSSARY_MASTER")
    glossary_prompts_dir: str = Field(default="glossary/prompts", env="GLOSSARY_PROMPTS_DIR")
    glossary_cache_dir: str = Field(default="glossary/cache", env="GLOSSARY_CACHE_DIR")
    glossary_cache_enabled: bool = Field(default=True, env="GLOSSARY_CACHE_ENABLED")
    glossary_cache_ttl_days: int = Field(default=30, env="GLOSSARY_CACHE_TTL_DAYS")
    glossary_learning_enabled: bool = Field(default=False, env="GLOSSARY_LEARNING_ENABLED")
    glossary_auto_learn: bool = Field(default=True, env="GLOSSARY_AUTO_LEARN")
    glossary_min_occurrences: int = Field(default=2, env="GLOSSARY_MIN_OCCURRENCES")
    glossary_confidence_threshold: int = Field(default=3, env="GLOSSARY_CONFIDENCE_THRESHOLD")
    
    # Legacy Glossary Configuration (for subtitle-gen stage)
    glossary_enabled: bool = Field(default=True, env="GLOSSARY_ENABLED")
    glossary_path: str = Field(default="glossary/hinglish_master.tsv", env="GLOSSARY_PATH")
    glossary_strategy: str = Field(default="adaptive", env="GLOSSARY_STRATEGY")
    film_prompt_path: str = Field(default="", env="FILM_PROMPT_PATH")
    frequency_data_path: str = Field(default="glossary/learned/term_frequency.json", env="FREQUENCY_DATA_PATH")
    
    # CPS (Characters Per Second) enforcement
    cps_target: float = Field(default=15.0, env="CPS_TARGET")
    cps_hard_cap: float = Field(default=17.0, env="CPS_HARD_CAP")
    cps_enforcement: bool = Field(default=True, env="CPS_ENFORCEMENT")
    
    # Bollywood Enhancements
    second_pass_enabled: bool = Field(default=True, env="SECOND_PASS_ENABLED")
    second_pass_backend: str = Field(default="nllb", env="SECOND_PASS_BACKEND")
    lyric_detect_enabled: bool = Field(default=True, env="LYRIC_DETECT_ENABLED")
    lyric_threshold: float = Field(default=0.5, env="LYRIC_THRESHOLD")
    lyric_style: str = Field(default="lyric", env="LYRIC_STYLE")
    lyric_min_duration: float = Field(default=30.0, env="LYRIC_MIN_DURATION")
    
    # Post-ASR NER
    post_ner_model: str = Field(default="en_core_web_trf", env="POST_NER_MODEL")
    post_ner_entity_correction: bool = Field(default=True, env="POST_NER_ENTITY_CORRECTION")
    post_ner_tmdb_matching: bool = Field(default=True, env="POST_NER_TMDB_MATCHING")
    post_ner_confidence_threshold: float = Field(default=0.8, env="POST_NER_CONFIDENCE_THRESHOLD")
    post_ner_device: str = Field(default="cpu", env="POST_NER_DEVICE")
    
    # FFmpeg Mux
    mux_subtitle_codec: str = Field(default="mov_text", env="MUX_SUBTITLE_CODEC")
    mux_subtitle_language: str = Field(default="eng", env="MUX_SUBTITLE_LANGUAGE")
    mux_subtitle_title: str = Field(default="English", env="MUX_SUBTITLE_TITLE")
    mux_copy_video: bool = Field(default=True, env="MUX_COPY_VIDEO")
    mux_copy_audio: bool = Field(default=True, env="MUX_COPY_AUDIO")
    mux_container_format: str = Field(default="mp4", env="MUX_CONTAINER_FORMAT")
    
    # Devices
    device: str = Field(default="cpu", env="DEVICE")  # Global device setting
    device_whisperx: str = Field(default="cpu", env="DEVICE_WHISPERX")
    device_diarization: str = Field(default="cpu", env="DEVICE_DIARIZATION")
    device_vad: str = Field(default="cpu", env="DEVICE_VAD")
    device_ner: str = Field(default="cpu", env="DEVICE_NER")
    
    # Docker
    docker_memory_limit: str = Field(default="10g", env="DOCKER_MEMORY_LIMIT")
    docker_cpu_limit: int = Field(default=4, env="DOCKER_CPU_LIMIT")
    
    # Advanced
    enable_chunking: bool = Field(default=False, env="ENABLE_CHUNKING")
    chunk_duration_minutes: int = Field(default=30, env="CHUNK_DURATION_MINUTES")
    cleanup_temp_files: bool = Field(default=True, env="CLEANUP_TEMP_FILES")
    keep_intermediate_files: bool = Field(default=False, env="KEEP_INTERMEDIATE_FILES")
    max_retries: int = Field(default=3, env="MAX_RETRIES")
    
    class Config:
        env_file = "/app/config/.env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env
    
    def load_secrets(self) -> dict:
        """Load secrets from JSON file."""
        secrets_file = Path(self.secrets_path)
        if secrets_file.exists():
            with open(secrets_file, 'r') as f:
                return json.load(f)
        return {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get config value by key."""
        return getattr(self, key.lower(), default)


def load_config(env_file: Optional[str] = None):
    """
    Load pipeline configuration.
    Returns PipelineConfig if pydantic_settings is available, otherwise returns simple Config.
    """
    if not PYDANTIC_AVAILABLE:
        # Fallback to simple Config when pydantic_settings not available
        # Path is already imported at module level (line 7)
        project_root = Path(__file__).parent.parent
        return Config(project_root)
    
    # Check for CONFIG_PATH environment variable first
    if env_file is None:
        env_file = os.getenv('CONFIG_PATH')
    
    if env_file and Path(env_file).exists():
        config = PipelineConfig(_env_file=env_file)
    else:
        config = PipelineConfig()
    
    # Load secrets and merge into config
    secrets = config.load_secrets()
    if secrets:
        # Merge secrets into config object
        if 'hf_token' in secrets and not config.hf_token:
            config.hf_token = secrets['hf_token']
        if 'HF_TOKEN' in secrets and not config.hf_token:
            config.hf_token = secrets['HF_TOKEN']
        if 'tmdb_api_key' in secrets and not config.tmdb_api_key:
            config.tmdb_api_key = secrets['tmdb_api_key']
        if 'TMDB_API_KEY' in secrets and not config.tmdb_api_key:
            config.tmdb_api_key = secrets['TMDB_API_KEY']
    
    return config


class Config:
    """
    Simple configuration loader for reading from config/.env.pipeline
    Used by prepare-job.py to read configuration values.
    
    Best practice: Use this class instead of os.environ.get()
    """
    
    def __init__(self, project_root: Path):
        """Initialize config loader with project root."""
        self.project_root = project_root
        self.config_file = project_root / "config" / ".env.pipeline"
        self._config = {}
        self._load()
    
    def _load(self):
        """Load configuration from .env.pipeline file."""
        if not self.config_file.exists():
            return
        
        with open(self.config_file, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                # Parse KEY=value
                if '=' in line:
                    key, value = line.split('=', 1)
                    # Remove inline comments
                    if '#' in value:
                        value = value.split('#')[0]
                    self._config[key.strip()] = value.strip()
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.
        
        Args:
            key: Configuration key (e.g., 'SOURCE_SEPARATION_ENABLED')
            default: Default value if key not found
        
        Returns:
            Configuration value or default
        """
        return self._config.get(key, default)
    
    def get_secret(self, key: str) -> Optional[str]:
        """
        Get secret value from secrets.json.
        
        Args:
            key: Secret key (e.g., 'HUGGINGFACE_TOKEN')
        
        Returns:
            Secret value or None
        """
        secrets_file = self.project_root / "config" / "secrets.json"
        if not secrets_file.exists():
            return None
        
        try:
            with open(secrets_file, 'r') as f:
                secrets = json.load(f)
                return secrets.get(key)
        except Exception:
            return None
    
    def __getattr__(self, name: str) -> Any:
        """
        Allow attribute-style access to config values.
        
        Args:
            name: Attribute name (converted to uppercase for env var lookup)
        
        Returns:
            Configuration value or None
        """
        # Convert snake_case to UPPERCASE for env var lookup
        env_key = name.upper()
        
        # Check environment variables first (for runtime overrides)
        env_value = os.getenv(env_key)
        if env_value is not None:
            return self._parse_value(env_value)
        
        # Check loaded config
        if env_key in self._config:
            return self._parse_value(self._config[env_key])
        
        # Return None for missing attributes (compatible with getattr(config, 'key', default))
        return None
    
    def _parse_value(self, value: str) -> Any:
        """Parse string value to appropriate type."""
        if value.lower() in ('true', 'yes', '1', 'on'):
            return True
        if value.lower() in ('false', 'no', '0', 'off'):
            return False
        
        # Try to parse as number
        try:
            if '.' in value:
                return float(value)
            return int(value)
        except ValueError:
            pass
        
        # Return as string, removing quotes if present
        return value.strip('"').strip("'")
    
    def load_secrets(self) -> dict:
        """Load secrets from JSON file (for compatibility with PipelineConfig)."""
        secrets_file = self.project_root / "config" / "secrets.json"
        if not secrets_file.exists():
            return {}
        
        try:
            with open(secrets_file, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
