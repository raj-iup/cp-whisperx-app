"""
Shared configuration loader for all pipeline containers.
Reads configuration from .env file and provides typed access.
"""
import os
import json
from pathlib import Path
from typing import Optional, Any
from pydantic_settings import BaseSettings
from pydantic import Field


class PipelineConfig(BaseSettings):
    """Pipeline configuration with validation."""
    
    # Docker Registry
    docker_registry: str = Field(default="rajiup", env="DOCKER_REGISTRY")
    docker_tag: str = Field(default="latest", env="DOCKER_TAG")
    
    # Paths
    input_file: str = Field(default="", env="INPUT_FILE")
    output_root: str = Field(default="./out", env="OUTPUT_ROOT")
    log_root: str = Field(default="./logs", env="LOG_ROOT")
    temp_root: str = Field(default="./temp", env="TEMP_ROOT")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
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
    step_silero_vad: bool = Field(default=True, env="STEP_SILERO_VAD")
    step_pyannote_vad: bool = Field(default=True, env="STEP_PYANNOTE_VAD")
    step_diarization: bool = Field(default=True, env="STEP_DIARIZATION")
    step_whisperx: bool = Field(default=True, env="STEP_WHISPERX")
    step_post_asr_ner: bool = Field(default=True, env="STEP_POST_ASR_NER")
    step_subtitle_gen: bool = Field(default=True, env="STEP_SUBTITLE_GEN")
    step_mux: bool = Field(default=True, env="STEP_MUX")
    auto_continue: bool = Field(default=False, env="AUTO_CONTINUE")
    
    # FFmpeg Demux
    audio_sample_rate: int = Field(default=16000, env="AUDIO_SAMPLE_RATE")
    audio_channels: int = Field(default=1, env="AUDIO_CHANNELS")
    audio_format: str = Field(default="wav", env="AUDIO_FORMAT")
    audio_codec: str = Field(default="pcm_s16le", env="AUDIO_CODEC")
    
    # TMDB
    tmdb_enabled: bool = Field(default=True, env="TMDB_ENABLED")
    tmdb_language: str = Field(default="en-US", env="TMDB_LANGUAGE")
    tmdb_infer_from_filename: bool = Field(default=True, env="TMDB_INFER_FROM_FILENAME")
    
    # Whisper
    whisper_model: str = Field(default="large-v3", env="WHISPER_MODEL")
    whisper_compute_type: str = Field(default="int8", env="WHISPER_COMPUTE_TYPE")
    whisper_batch_size: int = Field(default=16, env="WHISPER_BATCH_SIZE")
    whisper_language: str = Field(default="hi", env="WHISPER_LANGUAGE")
    whisper_task: str = Field(default="translate", env="WHISPER_TASK")
    
    # Silero VAD
    silero_threshold: float = Field(default=0.6, env="SILERO_THRESHOLD")
    silero_min_speech_duration_ms: int = Field(default=250, env="SILERO_MIN_SPEECH_DURATION_MS")
    silero_min_silence_duration_ms: int = Field(default=300, env="SILERO_MIN_SILENCE_DURATION_MS")
    silero_merge_gap_sec: float = Field(default=0.35, env="SILERO_MERGE_GAP_SEC")
    
    # PyAnnote VAD
    pyannote_window_pad: float = Field(default=0.25, env="PYANNOTE_WINDOW_PAD")
    pyannote_merge_gap: float = Field(default=0.2, env="PYANNOTE_MERGE_GAP")
    
    # Diarization
    diarization_min_speakers: int = Field(default=1, env="DIARIZATION_MIN_SPEAKERS")
    diarization_max_speakers: int = Field(default=10, env="DIARIZATION_MAX_SPEAKERS")
    
    # Subtitle
    subtitle_format: str = Field(default="srt", env="SUBTITLE_FORMAT")
    subtitle_include_speaker_labels: bool = Field(default=True, env="SUBTITLE_INCLUDE_SPEAKER_LABELS")
    
    # Devices
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


def load_config(env_file: Optional[str] = None) -> PipelineConfig:
    """Load pipeline configuration."""
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
