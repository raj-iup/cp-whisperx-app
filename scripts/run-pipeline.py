#!/usr/bin/env python3
"""
IndicTrans2 Pipeline Orchestrator

Simplified pipeline execution for IndicTrans2 workflows:
- Transcribe workflow: demux → asr → alignment
- Translate workflow: load_transcript → indictrans2_translation → subtitle_generation

Reuses existing infrastructure:
- shared/logger.py for logging
- shared/manifest.py for tracking
- Existing stage implementations where possible
"""

# Standard library
import sys
import os
import json
import argparse
import subprocess
import traceback
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any

# Add paths for imports
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.logger import PipelineLogger, get_logger
from shared.environment_manager import EnvironmentManager
from scripts.config_loader import Config
from shared.stage_order import get_stage_dir
from shared.stage_dependencies import (
    validate_stage_dependencies,
    get_workflow_stages,
    get_execution_order
)

# Initialize logger
logger = get_logger(__name__)


def format_timestamp_srt(seconds: float) -> str:
    """Format seconds as SRT timestamp (HH:MM:SS,mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def normalize_segments_data(data: Dict[str, Any]) -> Any:
    """
    Normalize segments data to consistent dict format.
    Handles both list [...] and dict {"segments": [...]} formats.
    
    Args:
        data: Either a list of segments or a dict containing segments
        
    Returns:
        Tuple of (data_dict, segments_list)
    """
    if isinstance(data, list):
        segments = data
        data = {"segments": segments}
    elif isinstance(data, dict):
        segments = data.get("segments", [])
    else:
        segments = []
    
    return data, segments


def generate_srt_from_segments(segments: List[Dict], output_path: Path) -> bool:
    """Generate SRT subtitle file from segments"""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, segment in enumerate(segments, 1):
                # Segment number
                f.write(f"{i}\n")
                
                # Timestamps
                start = format_timestamp_srt(segment.get('start', 0))
                end = format_timestamp_srt(segment.get('end', 0))
                f.write(f"{start} --> {end}\n")
                
                # Text
                text = segment.get('text', '').strip()
                f.write(f"{text}\n")
                
                # Blank line between segments
                f.write("\n")
        
        return True
    except Exception as e:
        return False



class IndicTrans2Pipeline:
    """Pipeline orchestrator for IndicTrans2 workflows"""
    
    def __init__(self, job_dir: Path, resume: bool = False):
        """  Init  ."""
        self.job_dir = job_dir
        self.resume = resume
        
        # Set scripts directory
        self.scripts_dir = PROJECT_ROOT / "scripts"
        
        # Load main configuration for fallback defaults
        self.main_config = Config(PROJECT_ROOT)
        
        # Load job configuration
        self.job_config = self._load_config("job.json")
        self.manifest = self._load_config("manifest.json")
        
        # Initialize environment manager
        self.env_manager = EnvironmentManager(PROJECT_ROOT)
        
        # Load job-specific environment configuration
        self.env_config = self._load_env_config()
        
        # Get debug mode from job config
        self.debug = self.job_config.get("debug", False)
        log_level = "DEBUG" if self.debug else "INFO"
        
        # Setup logging - DUAL logging architecture:
        # 1. Main pipeline log: High-level orchestration
        # 2. Stage logs: Detailed logs in each stage subdirectory
        log_dir = job_dir / "logs"
        log_dir.mkdir(exist_ok=True)
        
        # Create main pipeline log file (99_pipeline_*.log for clarity)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"99_pipeline_{timestamp}.log"
        
        self.logger = PipelineLogger(
            module_name="pipeline",
            log_file=log_file,
            log_level=log_level
        )
        
        self.logger.info("=" * 80)
        self.logger.info("PIPELINE LOGGING ARCHITECTURE")
        self.logger.info("=" * 80)
        self.logger.info(f"📋 Main pipeline log: {log_file.relative_to(job_dir)}")
        self.logger.info(f"📋 Stage logs: Each stage writes to its own subdirectory")
        self.logger.info(f"📋 Stage manifests: Track inputs/outputs/intermediate files")
        self.logger.info("")
        
        if self.debug:
            self.logger.info("🐛 DEBUG MODE ENABLED - Verbose logging active")
        
        self.workflow = self.job_config["workflow"]
        
        # Initialize glossary manager (will be loaded in stage)
        self.glossary_manager = None
        
        # Log cache configuration
        cache_config = self.env_manager.hardware_cache.get("cache", {})
        if cache_config:
            self.logger.info("📦 Model cache configuration:")
            if "hf_home" in cache_config:
                hf_cache = PROJECT_ROOT / cache_config["hf_home"]
                if hf_cache.exists():
                    # Count cached models
                    hub_dir = hf_cache / "hub"
                    if hub_dir.exists():
                        model_count = len([d for d in hub_dir.iterdir() if d.is_dir() and d.name.startswith("models--")])
                        self.logger.info(f"  HuggingFace cache: {cache_config['hf_home']} ({model_count} models cached)")
                    else:
                        self.logger.info(f"  HuggingFace cache: {cache_config['hf_home']} (empty)")
                else:
                    self.logger.warning(f"  HuggingFace cache not found: {cache_config['hf_home']}")
            if "torch_home" in cache_config:
                self.logger.info(f"  PyTorch cache: {cache_config['torch_home']}")
            if "mlx_home" in cache_config:
                self.logger.info(f"  MLX cache: {cache_config['mlx_home']}")
        
        # Log environment information
        envs = self.job_config.get("environments", {})
        if envs:
            self.logger.info(f"Multi-environment mode: {len(envs)} environment(s) configured")
            for env_name, env_path in envs.items():
                installed = "✓" if self.env_manager.is_environment_installed(env_name) else "✗"
                self.logger.info(f"  {installed} {env_name}: {env_path}")
    
    def _stage_path(self, stage_name: str) -> Path:
        """
        Get the path to a stage directory using centralized stage ordering.
        
        Args:
            stage_name: Name of the stage
            
        Returns:
            Path to stage directory
        """
        return self.job_dir / get_stage_dir(stage_name)
    
    def _load_env_config(self) -> Dict[str, str]:
        """Load job-specific .env file created by prepare-job"""
        job_id = self.job_config["job_id"]
        env_file = self.job_dir / f".{job_id}.env"
        
        if not env_file.exists():
            self.logger.warning(f"Job .env file not found: {env_file}")
            return {}
        
        config = {}
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key] = value
        
        return config
    
    def _is_indic_language(self, lang_code: str) -> bool:
        """Check if a language code is an Indic language supported by IndicTrans2"""
        indic_languages = {
            "hi", "as", "bn", "gu", "kn", "ml", "mr", "or", "pa", "ta", "te", "ur",
            "ne", "sd", "si", "sa", "ks", "doi", "mni", "kok", "mai", "sat"
        }
        return lang_code in indic_languages
        
    def _load_config(self, filename: str) -> Dict:
        """Load JSON configuration file"""
        config_file = self.job_dir / filename
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration not found: {config_file}")
        
        with open(config_file) as f:
            return json.load(f)
    
    def _save_manifest(self) -> None:
        """Save manifest to file"""
        manifest_file = self.job_dir / "manifest.json"
        self.manifest["updated_at"] = datetime.now().isoformat()
        
        with open(manifest_file, 'w') as f:
            json.dump(self.manifest, f, indent=2)
    
    def _update_stage_status(self, stage_name: str, status: str, 
                            duration: Optional[float] = None):
        """Update stage status in manifest"""
        for stage in self.manifest["stages"]:
            if stage["name"] == stage_name:
                stage["status"] = status
                if status == "running":
                    stage["start_time"] = datetime.now().isoformat()
                elif status in ["completed", "failed"]:
                    stage["end_time"] = datetime.now().isoformat()
                    if duration:
                        stage["duration_seconds"] = duration
                break
        
        self._save_manifest()
    
    def _get_stage_environment(self, stage_name: str) -> Optional[str]:
        """Get the required environment for a stage"""
        stage_envs = self.job_config.get("stage_environments", {})
        
        # Try exact match first
        if stage_name in stage_envs:
            return stage_envs[stage_name]
        
        # Handle dynamic translation stage names (e.g., indictrans2_translation_en)
        if stage_name.startswith("indictrans2_translation_"):
            # Look for generic "translation" mapping
            return stage_envs.get("translation") or "indictrans2"
        
        # Handle dynamic NLLB translation stage names
        if stage_name.startswith("nllb_translation_"):
            return stage_envs.get("nllb_translation") or "nllb"
        
        # Handle dynamic subtitle generation stage names
        if stage_name.startswith("subtitle_generation_"):
            return stage_envs.get("subtitle_gen") or stage_envs.get("subtitle_generation") or "common"
        
        # Default environment mappings for stages without explicit config
        default_envs = {
            "source_separation": "common",
            "pyannote_vad": "pyannote"
        }
        
        if stage_name in default_envs:
            return default_envs[stage_name]
        
        return None
    
    def _get_target_language(self) -> Optional[str]:
        """
        Get target language from job config, handling both singular and plural forms.
        
        Returns:
            Target language code, or None if not set
        """
        # Try singular form first (legacy)
        target_lang = self.job_config.get("target_language")
        if target_lang:
            return target_lang
        
        # Try plural form (new format)
        target_langs = self.job_config.get("target_languages", [])
        if target_langs:
            return target_langs[0]
        
        return None
    
    def _run_in_environment(self, stage_name: str, command: List[str], **kwargs) -> subprocess.CompletedProcess:
        """
        Run a command in the appropriate environment for a stage
        
        Args:
            stage_name: Name of the stage
            command: Command to run
            **kwargs: Additional arguments for subprocess.run
            
        Returns:
            CompletedProcess instance
        """
        env_name = self._get_stage_environment(stage_name)
        
        if env_name:
            self.logger.info(f"Running stage '{stage_name}' in environment '{env_name}'")
            python_exe = self.env_manager.get_python_executable(env_name)
            
            # Start with provided env if any, otherwise use os.environ
            env = kwargs.get('env', os.environ).copy()
            
            # Set up environment variables for the virtual environment
            env["VIRTUAL_ENV"] = str(self.env_manager.get_environment_path(env_name))
            env_bin = self.env_manager.get_environment_path(env_name) / "bin"
            env["PATH"] = f"{env_bin}:{env['PATH']}"
            env["DEBUG_MODE"] = 'true' if self.debug else 'false'
            env["LOG_LEVEL"] = 'DEBUG' if self.debug else 'INFO'
            
            # Replace python in command with environment-specific python
            if command[0] == "python" or command[0] == "python3":
                command[0] = str(python_exe)
            
            kwargs['env'] = env
        else:
            self.logger.warning(f"No environment specified for stage '{stage_name}', using current environment")
            
            # Set debug environment variables
            if 'env' not in kwargs:
                kwargs['env'] = os.environ.copy()
            kwargs['env']['DEBUG_MODE'] = 'true' if self.debug else 'false'
            kwargs['env']['LOG_LEVEL'] = 'DEBUG' if self.debug else 'INFO'
        
        return subprocess.run(command, **kwargs)
    
    def _check_indictrans2_available(self) -> bool:
        """Check if IndicTrans2 environment is available"""
        try:
            # Check if indictrans2 environment exists and is valid
            return self.env_manager.is_environment_installed("indictrans2")
        except Exception as e:
            self.logger.debug(f"IndicTrans2 check failed: {e}")
            return False
    
    def run_transcribe_workflow(self) -> bool:
        """
        Execute transcribe workflow stages:
        1. Demux - Extract audio
        1.5. Source Separation - Extract vocals (if enabled)
        2. PyAnnote VAD - Detect speech segments (highest quality)
        3. ASR - Transcribe using WhisperX
        4. Alignment - Word-level timestamps
        5. Export - Generate plain text transcript
        """
        self.logger.info("=" * 80)
        self.logger.info("TRANSCRIBE WORKFLOW")
        self.logger.info("=" * 80)
        
        # Build stages list
        stages = [("demux", self._stage_demux)]
        
        # Add TMDB enrichment if enabled (BEFORE ASR for metadata context)
        if self.job_config.get("tmdb_enrichment", {}).get("enabled", False):
            stages.append(("tmdb", self._stage_tmdb_enrichment))
            # Add glossary load after TMDB (to use enrichment data)
            stages.append(("glossary_load", self._stage_glossary_load))
        
        # Add source separation if enabled
        sep_config = self.job_config.get("source_separation", {})
        if sep_config.get("enabled", False):
            stages.append(("source_separation", self._stage_source_separation))
        
        # Add core ASR stages
        stages.extend([
            ("pyannote_vad", self._stage_pyannote_vad),
            ("asr", self._stage_asr),
            ("hallucination_removal", self._stage_hallucination_removal),
            ("alignment", self._stage_alignment),
        ])
        
        # Add lyrics detection AFTER ASR (optional)
        lyrics_enabled = self.env_config.get("LYRICS_DETECTION_ENABLED", "true").lower() == "true"
        if lyrics_enabled:
            stages.append(("lyrics_detection", self._stage_lyrics_detection))
        
        # Final export stage
        stages.append(("export_transcript", self._stage_export_transcript))
        
        return self._execute_stages(stages)
    
    def run_translate_workflow(self) -> bool:
        """
        Execute translate workflow stages:
        Auto-executes transcribe workflow if transcript doesn't exist
        1. Demux - Extract audio (if needed)
        2. ASR - Transcribe (if needed)
        3. Alignment - Word timestamps (if needed)
        4. Load Transcript - Load segments.json
        5. IndicTrans2 Translation - Translate text
        6. Subtitle Generation - Create SRT in target language
        """
        self.logger.info("=" * 80)
        self.logger.info("TRANSLATE WORKFLOW")
        self.logger.info("=" * 80)
        
        # Get target language
        target_lang = self._get_target_language()
        
        # Check if transcript exists, if not run transcribe stages first
        segments_file = self.job_dir / "transcripts" / "segments.json"
        
        if not segments_file.exists():
            self.logger.info("📝 Transcript not found - auto-executing transcribe workflow first")
            self.logger.info("")
            
            # Run transcribe stages
            transcribe_stages = [("demux", self._stage_demux)]
            
            # Add TMDB enrichment if enabled (BEFORE ASR for metadata context)
            if self.job_config.get("tmdb_enrichment", {}).get("enabled", False):
                transcribe_stages.append(("tmdb", self._stage_tmdb_enrichment))
                # Add glossary load after TMDB (to use enrichment data)
                transcribe_stages.append(("glossary_load", self._stage_glossary_load))
            
            # Add source separation if enabled
            sep_config = self.job_config.get("source_separation", {})
            if sep_config.get("enabled", False):
                transcribe_stages.append(("source_separation", self._stage_source_separation))
            
            # Add core ASR stages
            transcribe_stages.extend([
                ("pyannote_vad", self._stage_pyannote_vad),
                ("asr", self._stage_asr),
                ("hallucination_removal", self._stage_hallucination_removal),
                ("alignment", self._stage_alignment),
            ])
            
            # Add lyrics detection AFTER ASR (optional)
            lyrics_enabled = self.env_config.get("LYRICS_DETECTION_ENABLED", "true").lower() == "true"
            if lyrics_enabled:
                transcribe_stages.append(("lyrics_detection", self._stage_lyrics_detection))
            
            # Final export stage
            transcribe_stages.append(("export_transcript", self._stage_export_transcript))
            
            if not self._execute_stages(transcribe_stages):
                self.logger.error("Transcribe workflow failed - cannot proceed with translation")
                return False
            
            self.logger.info("")
            self.logger.info("✅ Transcribe workflow completed successfully")
            self.logger.info("=" * 80)
            self.logger.info("CONTINUING WITH TRANSLATION")
            self.logger.info("=" * 80)
        else:
            self.logger.info("✓ Transcript found - skipping transcribe stages")
        
        # Route to appropriate translator based on target language
        translate_stages = [("load_transcript", self._stage_load_transcript)]
        
        # Check if hybrid translation is enabled
        use_hybrid = self.env_config.get("USE_HYBRID_TRANSLATION", "true").lower() == "true"
        
        if use_hybrid:
            # Use hybrid translation (IndicTrans2 + LLM for songs)
            self.logger.info(f"Using hybrid translation for {target_lang}")
            translate_stages.append(("hybrid_translation", self._stage_hybrid_translation))
        elif self._is_indic_language(target_lang):
            # Use IndicTrans2 for Indic languages
            self.logger.info(f"Using IndicTrans2 for Indic language: {target_lang}")
            translate_stages.append(("indictrans2_translation", self._stage_indictrans2_translation))
        else:
            # Use NLLB for non-Indic languages
            self.logger.info(f"Using NLLB for non-Indic language: {target_lang}")
            translate_stages.append(("nllb_translation", self._stage_nllb_translation))
        
        translate_stages.append(("subtitle_generation", self._stage_subtitle_generation))
        
        return self._execute_stages(translate_stages)
    
    def run_subtitle_workflow(self) -> bool:
        """
        Execute subtitle workflow stages:
        Auto-executes transcribe + translate workflows if needed
        Generates subtitles in source and multiple target languages (up to 5)
        1. Demux - Extract audio (if needed)
        2. ASR - Transcribe (if needed)
        3. Alignment - Word timestamps (if needed)
        4. Load Transcript - Load segments.json
        5. IndicTrans2 Translation - Translate text (for each target language)
        6. Subtitle Generation (Target) - Create SRT for each target language
        7. Subtitle Generation (Source) - Create SRT in source language
        8. Mux - Embed all subtitle tracks in video
        """
        self.logger.info("=" * 80)
        self.logger.info("SUBTITLE WORKFLOW")
        self.logger.info("=" * 80)
        
        # Get target languages from config
        target_languages = self.job_config.get("target_languages", [])
        if not target_languages:
            self.logger.error("No target languages configured!")
            return False
        
        self.logger.info(f"Target languages: {', '.join(target_languages)}")
        
        # Check IndicTrans2 availability
        if not self._check_indictrans2_available():
            self.logger.error("IndicTrans2 not available!")
            self.logger.error("Please install: ./install-indictrans2.sh")
            return False
        
        # Check if transcript exists, if not run transcribe stages first
        segments_file = self.job_dir / "transcripts" / "segments.json"
        
        if not segments_file.exists():
            self.logger.info("📝 Transcript not found - auto-executing transcribe workflow first")
            self.logger.info("")
            
            # Run transcribe stages
            transcribe_stages = [("demux", self._stage_demux)]
            
            # Add TMDB enrichment if enabled (BEFORE ASR for metadata context)
            if self.job_config.get("tmdb_enrichment", {}).get("enabled", False):
                transcribe_stages.append(("tmdb", self._stage_tmdb_enrichment))
                # Add glossary load after TMDB (to use enrichment data)
                transcribe_stages.append(("glossary_load", self._stage_glossary_load))
            
            # Add source separation if enabled
            sep_config = self.job_config.get("source_separation", {})
            if sep_config.get("enabled", False):
                transcribe_stages.append(("source_separation", self._stage_source_separation))
            
            # Add core ASR stages
            transcribe_stages.extend([
                ("pyannote_vad", self._stage_pyannote_vad),
                ("asr", self._stage_asr),
                ("hallucination_removal", self._stage_hallucination_removal),
                ("alignment", self._stage_alignment),
            ])
            
            # Add lyrics detection AFTER ASR (optional)
            lyrics_enabled = self.env_config.get("LYRICS_DETECTION_ENABLED", "true").lower() == "true"
            if lyrics_enabled:
                transcribe_stages.append(("lyrics_detection", self._stage_lyrics_detection))
            
            # Final stage
            transcribe_stages.append(("export_transcript", self._stage_export_transcript))
            
            if not self._execute_stages(transcribe_stages):
                self.logger.error("Transcribe workflow failed - cannot proceed with subtitle generation")
                return False
            
            self.logger.info("")
            self.logger.info("✅ Transcribe workflow completed successfully")
            self.logger.info("=" * 80)
            self.logger.info("CONTINUING WITH TRANSLATION AND SUBTITLE GENERATION")
            self.logger.info("=" * 80)
        else:
            self.logger.info("✓ Transcript found - skipping transcribe stages")
        
        # Build subtitle stages dynamically
        subtitle_stages = [("load_transcript", self._stage_load_transcript)]
        
        # Check if hybrid translation is enabled
        use_hybrid = self.env_config.get("USE_HYBRID_TRANSLATION", "true").lower() == "true"
        
        # Add translation and subtitle generation for each target language
        for target_lang in target_languages:
            # Route to appropriate translator based on language and hybrid setting
            if use_hybrid:
                # Use hybrid translation (IndicTrans2 + LLM for songs)
                subtitle_stages.append((
                    f"hybrid_translation_{target_lang}",
                    lambda tl=target_lang: self._stage_hybrid_translation_multi(tl)
                ))
            elif self._is_indic_language(target_lang):
                # Use IndicTrans2 for Indic languages
                subtitle_stages.append((
                    f"indictrans2_translation_{target_lang}",
                    lambda tl=target_lang: self._stage_indictrans2_translation_multi(tl)
                ))
            else:
                # Use NLLB for non-Indic languages
                subtitle_stages.append((
                    f"nllb_translation_{target_lang}",
                    lambda tl=target_lang: self._stage_nllb_translation_multi(tl)
                ))
            
            subtitle_stages.append((
                f"subtitle_generation_{target_lang}",
                lambda tl=target_lang: self._stage_subtitle_generation_target_multi(tl)
            ))
        
        # Add source subtitle generation
        subtitle_stages.append(("subtitle_generation_source", self._stage_subtitle_generation_source))
        
        # Add Hinglish detection for source subtitles if source language is Hindi/Indic
        source_lang = self.job_config.get("source_language", "")
        hinglish_detection = self.job_config.get("hinglish_detection", {})
        if hinglish_detection.get("enabled", True) and source_lang in ["hi", "hin", "hin_Deva"]:
            subtitle_stages.append(("hinglish_detection", self._stage_hinglish_detection))
        
        # Add mux stage
        subtitle_stages.append(("mux", self._stage_mux))
        
        return self._execute_stages(subtitle_stages)
    
    def _execute_stages(self, stages: List[tuple]) -> bool:
        """Execute list of stages"""
        for stage_name, stage_func in stages:
            # Check if resuming and stage already completed
            if self.resume:
                stage_status = self._get_stage_status(stage_name)
                if stage_status == "completed":
                    self.logger.info(f"⏭  Stage {stage_name}: SKIPPED (already completed)")
                    continue
            
            # Execute stage
            self.logger.info(f"▶️  Stage {stage_name}: STARTING")
            self._update_stage_status(stage_name, "running")
            
            start_time = datetime.now()
            
            try:
                success = stage_func()
                
                duration = (datetime.now() - start_time).total_seconds()
                
                if success:
                    self.logger.info(f"✅ Stage {stage_name}: COMPLETED ({duration:.1f}s)")
                    self._update_stage_status(stage_name, "completed", duration)
                else:
                    self.logger.error(f"❌ Stage {stage_name}: FAILED")
                    self._update_stage_status(stage_name, "failed", duration)
                    return False
                    
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                self.logger.error(f"❌ Stage {stage_name}: EXCEPTION: {e}", exc_info=True)
                if self.debug:
                    self.logger.error(f"Traceback: {traceback.format_exc()}", exc_info=True)
                self._update_stage_status(stage_name, "failed", duration)
                return False
        
        return True
    
    def _get_stage_status(self, stage_name: str) -> Optional[str]:
        """Get current status of a stage"""
        for stage in self.manifest["stages"]:
            if stage["name"] == stage_name:
                return stage["status"]
        return None
    
    # ========================================================================
    # Stage Implementations
    # ========================================================================
    
    def _stage_demux(self) -> bool:
        """Stage 1: Extract audio from video (full or clipped)"""
        
        # Initialize stage I/O and manifest
        from shared.stage_utils import StageIO
        stage_io = StageIO("demux", self.job_dir, enable_manifest=True)
        stage_logger = stage_io.get_stage_logger("DEBUG" if self.debug else "INFO")
        
        # Input/output setup
        input_media = Path(self.job_config["input_media"])
        stage_dir = stage_io.stage_dir
        audio_output = stage_io.get_output_path("audio.wav")
        
        # Track input in manifest
        stage_io.track_input(input_media, "video", format=input_media.suffix[1:])
        
        # Log input/output (to both stage log and pipeline log)
        self.logger.info(f"📥 Input: {input_media.relative_to(PROJECT_ROOT) if input_media.is_relative_to(PROJECT_ROOT) else input_media}")
        self.logger.info(f"📤 Output: {audio_output.relative_to(self.job_dir)}")
        stage_logger.info(f"Input media: {input_media}")
        stage_logger.info(f"Output directory: {stage_dir}")
        
        # Get media processing configuration
        media_config = self.job_config.get("media_processing", {})
        processing_mode = media_config.get("mode", "full")
        start_time = media_config.get("start_time", "")
        end_time = media_config.get("end_time", "")
        
        # Add config to manifest
        stage_io.set_config({
            "processing_mode": processing_mode,
            "start_time": start_time,
            "end_time": end_time,
            "sample_rate": "16000",
            "channels": "1"
        })
        
        if processing_mode == "clip":
            self.logger.info(f"Extracting audio clip (from {start_time} to {end_time})...")
            stage_logger.info(f"Clip mode: {start_time} to {end_time}")
        else:
            self.logger.info("Extracting audio from full media...")
            stage_logger.info("Full media extraction")
        
        # Build ffmpeg command
        cmd = ["ffmpeg", "-y"]
        
        # Add log level based on debug mode
        if not self.debug:
            cmd.extend(["-loglevel", "error"])
        
        # Add start time if clipping
        if processing_mode == "clip" and start_time:
            cmd.extend(["-ss", start_time])
        
        # Add input file
        cmd.extend(["-i", str(input_media)])
        
        # Add end time if clipping
        if processing_mode == "clip" and end_time:
            cmd.extend(["-to", end_time])
        
        # Add output options
        cmd.extend([
            "-vn",  # No video
            "-acodec", "pcm_s16le",
            "-ar", "16000",  # 16kHz for Whisper
            "-ac", "1",  # Mono
            str(audio_output)
        ])
        
        try:
            # Set up environment with debug flag
            env = os.environ.copy()
            env['DEBUG_MODE'] = 'true' if self.debug else 'false'
            env['LOG_LEVEL'] = 'DEBUG' if self.debug else 'INFO'
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                env=env
            )
            
            if self.debug and result.stderr:
                self.logger.debug(f"FFmpeg output: {result.stderr}")
                stage_logger.debug(f"FFmpeg stderr:\n{result.stderr}")
            
            if audio_output.exists():
                size_mb = audio_output.stat().st_size / (1024 * 1024)
                mode_str = f"clip ({start_time} to {end_time})" if processing_mode == "clip" else "full media"
                
                # Track output in manifest
                stage_io.track_output(audio_output, "audio", 
                                     format="wav", 
                                     sample_rate=16000,
                                     channels=1,
                                     size_mb=round(size_mb, 2))
                
                # Finalize manifest with success
                stage_io.finalize(status="success", 
                                 output_size_mb=round(size_mb, 2),
                                 processing_mode=processing_mode)
                
                self.logger.info(f"✓ Audio extracted from {mode_str}: {audio_output.name} ({size_mb:.1f} MB)")
                stage_logger.info(f"Successfully extracted audio: {size_mb:.1f} MB")
                stage_logger.info(f"Stage log: {stage_io.stage_log.relative_to(self.job_dir)}")
                stage_logger.info(f"Stage manifest: {stage_io.manifest_path.relative_to(self.job_dir)}")
                return True
            else:
                stage_io.add_error("Audio extraction failed - no output file")
                stage_io.finalize(status="failed")
                self.logger.error("Audio extraction failed")
                stage_logger.error("Audio extraction failed - no output file")
                return False
                
        except subprocess.CalledProcessError as e:
            self.logger.error(f"FFmpeg failed: {e}", exc_info=True)
            stage_logger.error(f"FFmpeg command failed: {e.stderr if e.stderr else str(e, exc_info=True)}", exc_info=True)
            stage_io.add_error(f"FFmpeg command failed: {e}")
            stage_io.finalize(status="failed", error="Demux failed")
            return False
        
        except FileNotFoundError as e:
            self.logger.error(f"Input file not found: {e}", exc_info=True)
            stage_logger.error(f"Input file not found: {e}", exc_info=True)
            stage_io.add_error(f"Input file not found: {e}")
            stage_io.finalize(status="failed", error=str(e))
            return False
        
        except IOError as e:
            self.logger.error(f"I/O error: {e}", exc_info=True)
            stage_logger.error(f"I/O error during demux: {e}", exc_info=True)
            stage_io.add_error(f"I/O error: {e}")
            stage_io.finalize(status="failed", error=str(e))
            return False
        
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}", exc_info=True)
            stage_logger.error(f"Unexpected error during demux: {e}", exc_info=True)
            stage_io.add_error(f"Unexpected error: {e}")
            stage_io.finalize(status="failed", error=str(e))
            return False
    
    def _stage_tmdb_enrichment(self) -> bool:
        """Stage 3: TMDB enrichment - Fetch movie metadata and generate glossaries"""
        
        # Check if TMDB enrichment is enabled
        tmdb_config = self.job_config.get("tmdb_enrichment", {})
        enabled = tmdb_config.get("enabled", False)
        
        if not enabled:
            self.logger.info("TMDB enrichment is disabled (skipping)")
            return True
        
        title = tmdb_config.get("title") or self.job_config.get("title")
        year = tmdb_config.get("year") or self.job_config.get("year")
        
        if not title:
            self.logger.warning("No movie title provided - skipping TMDB enrichment")
            return True
        
        # Input/output setup
        output_dir = self._stage_path("tmdb")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Log input/output
        self.logger.info(f"📥 Input: Title='{title}', Year={year or 'N/A'}")
        self.logger.info(f"📤 Output: {output_dir.relative_to(self.job_dir)}/")
        self.logger.info(f"Fetching TMDB metadata for: {title}" + (f" ({year})" if year else ""))
        
        # Run the TMDB enrichment script
        script_path = self.scripts_dir / "tmdb_enrichment_stage.py"
        
        try:
            # Set up environment
            env = os.environ.copy()
            env['OUTPUT_DIR'] = str(self.job_dir)
            env['DEBUG_MODE'] = 'true' if self.debug else 'false'
            env['LOG_LEVEL'] = 'DEBUG' if self.debug else 'INFO'
            
            # Build command arguments
            cmd = [sys.executable, str(script_path), "--job-dir", str(self.job_dir)]
            if title:
                cmd.extend(["--title", title])
            if year:
                cmd.extend(["--year", str(year)])
            
            # Run in common environment (TMDB/NER tools)
            result = self._run_in_environment(
                "tmdb",  # Stage name for environment lookup
                cmd,
                capture_output=True,
                text=True,
                check=True,
                env=env
            )
            
            if self.debug:
                self.logger.debug(f"TMDB enrichment output: {result.stdout}")
            
            # Check if enrichment file was created
            enrichment_file = self._stage_path("tmdb") / "enrichment.json"
            if enrichment_file.exists():
                with open(enrichment_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Log success with details
                cast_count = len(data.get('cast', []))
                crew_count = len(data.get('crew', []))
                soundtrack_count = len(data.get('soundtrack', []))
                
                self.logger.info(f"✓ TMDB metadata fetched successfully")
                if cast_count > 0:
                    self.logger.info(f"  Cast: {cast_count} actors")
                if crew_count > 0:
                    self.logger.info(f"  Crew: {crew_count} members")
                if soundtrack_count > 0:
                    self.logger.info(f"  Soundtrack: {soundtrack_count} songs")
            else:
                self.logger.warning("TMDB enrichment completed but no output file found")
            
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"TMDB enrichment failed: {e.stderr if e.stderr else str(e, exc_info=True)}")
            self.logger.warning("Continuing without TMDB metadata")
            return True  # Non-blocking failure
    
    def _stage_glossary_load(self) -> bool:
        """Stage 3: Load glossary system using new modular stage"""
        
        try:
            # Check if glossary is enabled
            glossary_enabled = self.env_config.get("STAGE_03_GLOSSARY_ENABLED", "true").lower() == "true"
            
            if not glossary_enabled:
                self.logger.info("Glossary system is disabled (skipping)")
                return True
            
            # Import glossary load stage module (module name starts with number, use importlib)
            import importlib
            glossary_load = importlib.import_module("scripts.03_glossary_load")
            
            # Call the stage module
            self.logger.info("Running glossary load stage...")
            exit_code = glossary_load.run_stage(self.job_dir, "03_glossary_load")
            
            if exit_code != 0:
                self.logger.error("Glossary load stage failed")
                return False
            
            self.logger.info("✓ Glossary load complete")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load glossary system: {e}", exc_info=True)
            if self.debug:
                self.logger.debug(traceback.format_exc())
            self.logger.warning("Continuing without glossary system")
            return True  # Non-blocking failure
    
    def _stage_source_separation(self) -> bool:
        """Stage 2: Source separation - Extract vocals, remove background music"""
        
        # Check if source separation is enabled
        sep_config = self.job_config.get("source_separation", {})
        enabled = sep_config.get("enabled", False)
        
        if not enabled:
            self.logger.info("Source separation is disabled (skipping)")
            return True
        
        # Input/output setup
        input_audio = self.job_dir / "01_demux" / "audio.wav"
        output_dir = self._stage_path("source_separation")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Log input/output
        self.logger.info(f"📥 Input: {input_audio.relative_to(self.job_dir)}")
        self.logger.info(f"📤 Output: {output_dir.relative_to(self.job_dir)}/")
        
        quality = sep_config.get("quality", "balanced")
        self.logger.info(f"Running source separation (quality: {quality})...")
        self.logger.info("This will extract vocals and remove background music")
        
        # Run the source separation script
        script_path = self.scripts_dir / "04_source_separation.py"
        
        try:
            # Set up environment
            env = os.environ.copy()
            env['OUTPUT_DIR'] = str(self.job_dir)  # CRITICAL: Tell script where job directory is
            env['DEBUG_MODE'] = 'true' if self.debug else 'false'
            env['LOG_LEVEL'] = 'DEBUG' if self.debug else 'INFO'
            
            # Run in demucs environment
            result = self._run_in_environment(
                "source_separation",
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                check=True,
                env=env
            )
            
            if self.debug:
                self.logger.debug(f"Source separation output: {result.stdout}")
            
            self.logger.info("✓ Vocals extracted successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Source separation failed: {e.stderr}", exc_info=True)
            return False
    
    def _stage_lyrics_detection(self) -> bool:
        """Stage 6: Lyrics detection using new modular stage"""
        
        try:
            # Check if lyrics detection is enabled
            lyrics_enabled = self.env_config.get("STAGE_06_LYRICS_ENABLED", "true").lower() == "true"
            
            if not lyrics_enabled:
                self.logger.info("Lyrics detection is disabled (skipping)")
                return True
            
            # Import lyrics detection stage module (module name starts with number, use importlib)
            import importlib
            lyrics_detection = importlib.import_module("scripts.06_lyrics_detection")
            
            # Call the stage module
            self.logger.info("Running lyrics detection stage...")
            exit_code = lyrics_detection.run_stage(self.job_dir, "06_lyrics_detection")
            
            if exit_code != 0:
                self.logger.warning("Lyrics detection failed, continuing without lyrics metadata")
                return True  # Non-fatal failure
            
            self.logger.info("✓ Lyrics detection complete")
            return True
            
        except Exception as e:
            self.logger.error(f"Lyrics detection error: {e}", exc_info=True)
            if self.debug:
                self.logger.debug(traceback.format_exc())
            self.logger.warning("Continuing pipeline without lyrics metadata")
            return True  # Non-fatal, graceful degradation
    
    def _stage_pyannote_vad(self) -> bool:
        """Stage 3: PyAnnote VAD for high-quality speech detection"""
        
        # Determine input audio source (from source_separation or demux)
        sep_audio = self._stage_path("source_separation") / "audio.wav"
        demux_audio = self.job_dir / "01_demux" / "audio.wav"
        
        if sep_audio.exists():
            audio_file = sep_audio
            audio_source = "source-separated vocals (clean speech)"
        elif demux_audio.exists():
            audio_file = demux_audio
            audio_source = "original audio from demux"
        else:
            self.logger.error("No audio file found from previous stages")
            self.logger.error(f"Checked: {sep_audio}")
            self.logger.error(f"Checked: {demux_audio}")
            return False
        
        # Output directory
        output_dir = self._stage_path("pyannote_vad")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Log input/output
        self.logger.info(f"📥 Input: {audio_file.relative_to(self.job_dir)}")
        self.logger.info(f"📤 Output: {output_dir.relative_to(self.job_dir)}/")
        self.logger.info(f"Running PyAnnote VAD for voice activity detection...")
        self.logger.info(f"Using {audio_source}")
        
        # Get device configuration
        device_config = self.env_config.get("WHISPERX_DEVICE", self.main_config.device_whisperx)
        # PyAnnote works on CPU, CUDA, MPS
        device = device_config.lower()
        
        self.logger.info(f"PyAnnote VAD device: {device}")
        self.logger.info("Using PyAnnote for highest quality speech detection")
        self.logger.info("This improves transcription accuracy, especially for movies with music/noise")
        
        try:
            import subprocess
            
            # Get Python executable from PyAnnote environment (dedicated for VAD)
            python_exe = self.env_manager.get_python_executable("pyannote")
            self.logger.info(f"Using PyAnnote environment: {python_exe}")
            
            # Build path to job config file
            job_id = self.job_config["job_id"]
            job_config_file = self.job_dir / f".{job_id}.env"
            
            # Set up environment
            env = os.environ.copy()
            env['CONFIG_PATH'] = str(job_config_file)
            env['OUTPUT_DIR'] = str(self.job_dir)
            env['PYANNOTE_DEVICE'] = device
            env['DEBUG_MODE'] = 'true' if self.debug else 'false'
            env['LOG_LEVEL'] = 'DEBUG' if self.debug else 'INFO'
            env['AUDIO_INPUT'] = str(audio_file)  # Pass audio path directly
            env['VAD_OUTPUT_DIR'] = str(output_dir)  # Pass VAD output directory
            
            # Run PyAnnote VAD script
            script_path = PROJECT_ROOT / "scripts" / "05_pyannote_vad.py"
            
            result = subprocess.run(
                [str(python_exe), str(script_path)],
                capture_output=True,
                text=True,
                check=True,
                cwd=str(PROJECT_ROOT),
                env=env
            )
            
            if self.debug and result.stdout:
                self.logger.debug(f"PyAnnote VAD output: {result.stdout}")
            
            # Check for output
            segments_file = output_dir / "speech_segments.json"
            if segments_file.exists():
                # Read and log statistics
                import json
                with open(segments_file) as f:
                    vad_data = json.load(f)
                
                if 'segments' in vad_data:
                    num_segments = len(vad_data['segments'])
                    self.logger.info(f"VAD detected {num_segments} speech segments")
                    
                    # Calculate total speech duration
                    total_duration = sum(seg['end'] - seg['start'] for seg in vad_data['segments'])
                    self.logger.info(f"Total speech duration: {total_duration:.1f}s")
                else:
                    self.logger.warning("VAD output missing 'segments' key")
                
                self.logger.info(f"✓ PyAnnote VAD completed: {segments_file}")
                return True
            else:
                self.logger.error("PyAnnote VAD failed - no output file generated")
                self.logger.error("Pipeline cannot continue without VAD preprocessing")
                return False
                
        except subprocess.CalledProcessError as e:
            self.logger.error(f"PyAnnote VAD error: {e.stderr}", exc_info=True)
            self.logger.error("Pipeline cannot continue without VAD preprocessing", exc_info=True)
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error in PyAnnote VAD: {e}", exc_info=True)
            self.logger.error("Pipeline cannot continue without VAD preprocessing", exc_info=True)
            return False
    
    def _stage_asr(self) -> bool:
        """Stage 4: Transcribe audio using WhisperX or MLX-Whisper"""
        
        # Determine input audio source (from source_separation or demux)
        sep_audio = self._stage_path("source_separation") / "audio.wav"
        demux_audio = self.job_dir / "01_demux" / "audio.wav"
        
        if sep_audio.exists():
            audio_file = sep_audio
            audio_source = "source-separated vocals (clean speech)"
        elif demux_audio.exists():
            audio_file = demux_audio
            audio_source = "original audio from demux"
        else:
            self.logger.error("No audio file found from previous stages")
            self.logger.error(f"Checked: {sep_audio}")
            self.logger.error(f"Checked: {demux_audio}")
            return False
        
        # Output directory
        output_dir = self._stage_path("asr")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        source_lang = self.job_config["source_language"]
        
        # Load VAD segments if available
        vad_segments = None
        vad_file = self._stage_path("pyannote_vad") / "speech_segments.json"
        vad_info = ""
        if vad_file.exists():
            try:
                import json
                with open(vad_file) as f:
                    vad_data = json.load(f)
                if 'segments' in vad_data and vad_data['segments']:
                    vad_segments = vad_data['segments']
                    vad_info = f" + VAD segments ({len(vad_segments)})"
                else:
                    self.logger.warning("VAD file exists but has no segments, transcribing full audio")
            except Exception as e:
                self.logger.warning(f"Failed to load VAD segments: {e}")
                self.logger.warning("Proceeding with full audio transcription")
        
        # Log input/output
        self.logger.info(f"📥 Input: {audio_file.relative_to(self.job_dir)}{vad_info}")
        self.logger.info(f"📤 Output: {output_dir.relative_to(self.job_dir)}/")
        self.logger.info(f"Transcribing audio...")
        self.logger.info(f"Using {audio_source}")
        
        # Get configuration from job's .env file (set by prepare-job)
        # Fall back to main config if not set in job
        device_config = self.env_config.get("WHISPERX_DEVICE", self.main_config.device_whisperx)
        whisper_model = self.env_config.get("WHISPER_MODEL", self.main_config.whisperx_model)
        compute_type = self.env_config.get("WHISPER_COMPUTE_TYPE", self.main_config.whisper_compute_type)
        batch_size = int(self.env_config.get("BATCH_SIZE", str(self.main_config.batch_size)))
        backend = self.env_config.get("WHISPER_BACKEND", self.main_config.whisper_backend)
        
        self.logger.info(f"Configured device: {device_config} (from job config)")
        self.logger.info(f"Using model: {whisper_model} (from job config)")
        self.logger.info(f"Compute type: {compute_type} (from job config)")
        self.logger.info(f"Batch size: {batch_size} (from job config)")
        self.logger.info(f"Backend: {backend} (from job config)")
        
        # Dynamic environment selection based on backend
        asr_env = self.env_manager.get_asr_environment(backend)
        self.logger.info(f"Using ASR environment: {asr_env}")
        
        # Get Python executable from selected environment
        try:
            python_exe = self.env_manager.get_python_executable(asr_env)
            self.logger.info(f"Using WhisperX environment: {python_exe}")
        except (ValueError, FileNotFoundError) as e:
            self.logger.error(f"Failed to get Python executable for {asr_env} environment: {e}", exc_info=True)
            self.logger.error("Run bootstrap.sh to set up environments", exc_info=True)
            return False
        
        # Run 06_whisperx_asr.py stage script in the selected environment
        asr_script = self.scripts_dir / "06_whisperx_asr.py"
        if not asr_script.exists():
            self.logger.error(f"ASR script not found: {asr_script}", exc_info=True)
            return False
        
        # Run ASR stage with subprocess
        self.logger.info(f"Running stage 'asr' in environment '{asr_env}'")
        env = os.environ.copy()
        env["OUTPUT_DIR"] = str(self.job_dir)
        env["PYTHONPATH"] = f"{PROJECT_ROOT}:{env.get('PYTHONPATH', '')}"
        
        result = subprocess.run(
            [str(python_exe), str(asr_script)],
            env=env,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            self.logger.error(f"ASR stage failed with exit code {result.returncode}")
            if result.stderr:
                self.logger.error(f"Error output: {result.stderr}")
            return False
        
        # Add retry logic for file detection with exponential backoff
        import time
        segments_file = output_dir / "segments.json"
        
        # Retry up to 5 times with exponential backoff
        for attempt in range(5):
            if segments_file.exists():
                break
            if attempt < 4:
                wait_time = 0.1 * (2 ** attempt)  # 0.1, 0.2, 0.4, 0.8, 1.6 seconds
                self.logger.debug(f"segments.json not found, retrying in {wait_time}s (attempt {attempt+1}/5)")
                time.sleep(wait_time)
            else:
                self.logger.error(f"Transcription failed - segments.json not found after 5 attempts")
                self.logger.error(f"  Checked: {segments_file}")
                self.logger.error(f"  Directory contents: {list(output_dir.glob('*'))}")
                return False
        
        # File exists, proceed with verification and copy
        file_size = segments_file.stat().st_size
        self.logger.info(f"✓ Transcription completed: {segments_file.relative_to(self.job_dir)}")
        self.logger.info(f"  File size: {file_size} bytes")
        
        # Copy to transcripts/ for compatibility
        import shutil
        transcripts_dir = self.job_dir / "transcripts"
        transcripts_dir.mkdir(parents=True, exist_ok=True)
        dest_file = transcripts_dir / "segments.json"
        shutil.copy2(segments_file, dest_file)
        
        # Verify copy
        if dest_file.exists() and dest_file.stat().st_size == file_size:
            self.logger.info(f"✓ Copied to: transcripts/segments.json ({file_size} bytes)")
            return True
        else:
            self.logger.error(f"Copy verification failed")
            self.logger.error(f"  Source: {segments_file} ({file_size} bytes)")
            self.logger.error(f"  Dest exists: {dest_file.exists()}")
            if dest_file.exists():
                self.logger.error(f"  Dest size: {dest_file.stat().st_size} bytes")
            return False
    
    def _stage_asr_mlx(self, audio_file: Path, output_dir: Path, 
                       source_lang: str, model: str, vad_segments: list = None) -> bool:
        """ASR using MLX-Whisper (Apple Silicon MPS acceleration)
        
        Args:
            vad_segments: Optional list of speech segments from PyAnnote VAD
                         Format: [{"start": 0.5, "end": 3.2}, ...]
        """
        
        # Map model names to MLX format
        model_map = {
            "large-v3": "mlx-community/whisper-large-v3-mlx",
            "large-v2": "mlx-community/whisper-large-v2-mlx",
            "large": "mlx-community/whisper-large-v3-mlx",
            "medium": "mlx-community/whisper-medium-mlx",
            "small": "mlx-community/whisper-small-mlx",
            "base": "mlx-community/whisper-base-mlx",
            "tiny": "mlx-community/whisper-tiny-mlx",
        }
        mlx_model = model_map.get(model, model)
        
        self.logger.info(f"Mapping model '{model}' to MLX format: '{mlx_model}'")
        
        script_content = f"""
import mlx_whisper
import json
from pathlib import Path

# Load audio and transcribe with MLX (MPS acceleration)
audio_file = "{audio_file}"
output_dir = Path("{output_dir}")
output_dir.mkdir(exist_ok=True)

logger.info("Loading MLX-Whisper model: {mlx_model}")
logger.info("Using MPS (Apple Silicon GPU) acceleration")

# Transcribe with MLX-Whisper
# This automatically uses MPS for acceleration
result = mlx_whisper.transcribe(
    str(audio_file),
    path_or_hf_repo="{mlx_model}",
    language="{source_lang}",
    verbose={'True' if self.debug else 'False'}
)

# Convert to WhisperX-compatible format
segments = []
if "segments" in result:
    for seg in result["segments"]:
        segments.append({{
            "start": seg["start"],
            "end": seg["end"],
            "text": seg["text"],
            "words": []  # MLX-Whisper doesn't provide word-level timestamps by default
        }})

output = {{
    "segments": segments,
    "language": result.get("language", "{source_lang}"),
    "text": result.get("text", "")
}}

# Save segments
segments_file = output_dir / "segments.json"
with open(segments_file, 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

logger.info(f"Transcription completed: {{len(segments)}} segments")
"""
        
        # Write script to temp file
        temp_script = output_dir / "asr_mlx_temp.py"
        with open(temp_script, 'w') as f:
            f.write(script_content)
        
        try:
            # Run the MLX script in venv/mlx environment
            import subprocess
            
            # Get Python executable from MLX environment
            python_exe = self.env_manager.get_python_executable("mlx")
            self.logger.info(f"Using MLX environment: {python_exe}")
            
            # Set up environment with debug flag
            env = os.environ.copy()
            env['DEBUG_MODE'] = 'true' if self.debug else 'false'
            env['LOG_LEVEL'] = 'DEBUG' if self.debug else 'INFO'
            
            result = subprocess.run(
                [str(python_exe), str(temp_script)],
                capture_output=True,
                text=True,
                check=True,
                cwd=str(PROJECT_ROOT),
                env=env
            )
            
            self.logger.info(f"MLX-Whisper output: {result.stdout}")
            
            # Check for output
            segments_file = output_dir / "segments.json"
            if segments_file.exists():
                self.logger.info(f"✓ Transcription completed: {segments_file.relative_to(self.job_dir)}")
                
                # Copy to transcripts/ for compatibility
                transcripts_dir = self.job_dir / "transcripts"
                transcripts_dir.mkdir(parents=True, exist_ok=True)
                import shutil
                shutil.copy2(segments_file, transcripts_dir / "segments.json")
                self.logger.info(f"✓ Copied to: transcripts/segments.json")
                
                return True
            else:
                self.logger.error("Transcription failed - no output")
                return False
                
        except subprocess.CalledProcessError as e:
            self.logger.error(f"MLX-Whisper error: {e.stderr}", exc_info=True)
            return False
        finally:
            # Clean up temp script
            if temp_script.exists():
                temp_script.unlink()
    
    def _stage_asr_whisperx(self, audio_file: Path, output_dir: Path,
                           source_lang: str, model: str, device: str,
                           compute_type: str, batch_size: int, vad_segments: list = None) -> bool:
        """ASR using WhisperX (faster-whisper/CTranslate2)
        
        Calls the proper whisperx_asr stage script to get full functionality
        including bias term support and proper parameter handling.
        
        Args:
            vad_segments: Optional list of speech segments from PyAnnote VAD
                         Format: [{"start": 0.5, "end": 3.2}, ...]
        """
        
        import subprocess
        
        # Get Python executable from WhisperX environment
        python_exe = self.env_manager.get_python_executable("whisperx")
        self.logger.info(f"Using WhisperX environment: {python_exe}")
        
        # Use the proper 06_whisperx_asr script that supports all features
        asr_script = self.scripts_dir / "06_whisperx_asr.py"
        
        if not asr_script.exists():
            self.logger.error(f"ASR script not found: {asr_script}")
            return False
        
        # Set up environment variables for the stage
        env = os.environ.copy()
        env['DEBUG_MODE'] = 'true' if self.debug else 'false'
        env['LOG_LEVEL'] = 'DEBUG' if self.debug else 'INFO'
        env['CONFIG_PATH'] = str(self.job_dir / 'job.json')
        env['JOB_DIR'] = str(self.job_dir)
        env['OUTPUT_DIR'] = str(self.job_dir)  # StageIO uses OUTPUT_DIR
        env['DEVICE_OVERRIDE'] = device
        
        try:
            result = subprocess.run(
                [str(python_exe), str(asr_script)],
                capture_output=True,
                text=True,
                check=True,
                cwd=str(PROJECT_ROOT),
                env=env
            )
            
            self.logger.info(f"ASR output: {result.stdout}")
            
            # Check for output
            segments_file = output_dir / "segments.json"
            if segments_file.exists():
                self.logger.info(f"✓ Transcription completed: {segments_file.relative_to(self.job_dir)}")
                
                # Copy to transcripts/ for compatibility
                transcripts_dir = self.job_dir / "transcripts"
                transcripts_dir.mkdir(parents=True, exist_ok=True)
                import shutil
                shutil.copy2(segments_file, transcripts_dir / "segments.json")
                self.logger.info(f"✓ Copied to: transcripts/segments.json")
                
                return True
            else:
                self.logger.error("Transcription failed - no output")
                return False
                
        except subprocess.CalledProcessError as e:
            self.logger.error(f"ASR error: {e.stderr}", exc_info=True)
            return False
    
    def _stage_alignment(self) -> bool:
        """Stage 5: Word-level alignment"""
        
        # Read from ASR stage output
        segments_file = self._stage_path("asr") / "segments.json"
        output_dir = self._stage_path("alignment")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Log input/output
        self.logger.info(f"📥 Input: {segments_file.relative_to(self.job_dir)}")
        self.logger.info(f"📤 Output: {output_dir.relative_to(self.job_dir)}/")
        
        if not segments_file.exists():
            self.logger.error(f"Segments file not found: {segments_file}")
            return False
        
        # Load segments
        with open(segments_file) as f:
            raw_data = json.load(f)
        
        # Normalize to consistent format
        data, segments = normalize_segments_data(raw_data)
        
        if not segments:
            self.logger.error("No segments found in transcript")
            return False
        
        # Check if segments already have word-level timestamps
        has_words = segments[0].get("words", []) if segments else []
        backend = self.env_config.get("WHISPER_BACKEND", self.main_config.whisper_backend)
        
        if has_words and len(has_words) > 0:
            # Already aligned
            total_words = sum(len(seg.get("words", [])) for seg in segments)
            self.logger.info(f"✓ Segments already have word-level timestamps")
            self.logger.info(f"  Segments: {len(segments)}, Words: {total_words}")
            
            # Copy to alignment output
            output_file = output_dir / "segments_aligned.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"✓ Alignment verified and saved: {output_file.relative_to(self.job_dir)}")
            return True
        
        # Need to perform alignment
        self.logger.info(f"⚠️  Segments missing word-level timestamps")
        self.logger.info(f"Backend: {backend}")
        
        if backend == "mlx":
            # Use MLX alignment
            self.logger.info("Performing word-level alignment with MLX-Whisper...")
            return self._perform_mlx_alignment(segments_file, output_dir)
        else:
            # WhisperX should have provided word timestamps already
            self.logger.warning("WhisperX backend should provide word timestamps during transcription")
            self.logger.warning("Proceeding without word-level alignment")
            
            # Copy segments anyway
            output_file = output_dir / "segments_aligned.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
    
    def _perform_mlx_alignment(self, segments_file: Path, output_dir: Path) -> bool:
        """Perform word-level alignment using MLX-Whisper"""
        
        # Determine audio source
        sep_audio = self._stage_path("source_separation") / "audio.wav"
        demux_audio = self.job_dir / "01_demux" / "audio.wav"
        
        if sep_audio.exists():
            audio_file = sep_audio
        elif demux_audio.exists():
            audio_file = demux_audio
        else:
            self.logger.error("No audio file found for alignment")
            return False
        
        source_lang = self.job_config["source_language"]
        whisper_model = self.env_config.get("WHISPER_MODEL", self.main_config.whisperx_model)
        
        # Map model names to MLX format
        model_map = {
            "large-v3": "mlx-community/whisper-large-v3-mlx",
            "large-v2": "mlx-community/whisper-large-v2-mlx",
            "large": "mlx-community/whisper-large-v3-mlx",
            "medium": "mlx-community/whisper-medium-mlx",
            "small": "mlx-community/whisper-small-mlx",
            "base": "mlx-community/whisper-base-mlx",
            "tiny": "mlx-community/whisper-tiny-mlx",
        }
        mlx_model = model_map.get(whisper_model, whisper_model)
        
        output_file = output_dir / "segments_aligned.json"
        
        self.logger.info(f"Audio: {audio_file.relative_to(self.job_dir)}")
        self.logger.info(f"Model: {mlx_model}")
        self.logger.info(f"Language: {source_lang}")
        
        # Use mlx_alignment.py script
        alignment_script = self.scripts_dir / "mlx_alignment.py"
        
        if not alignment_script.exists():
            self.logger.error(f"MLX alignment script not found: {alignment_script}")
            return False
        
        # Get Python executable from MLX environment
        python_exe = self.env_manager.get_python_executable("mlx")
        
        try:
            import subprocess
            
            cmd = [
                str(python_exe),
                str(alignment_script),
                str(audio_file),
                str(segments_file),
                str(output_file),
                "--model", mlx_model,
                "--language", source_lang
            ]
            
            if self.debug:
                cmd.append("--debug")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                cwd=str(PROJECT_ROOT)
            )
            
            if self.debug:
                self.logger.debug(f"Alignment output: {result.stdout}")
            
            # Verify output
            if output_file.exists():
                with open(output_file) as f:
                    raw_data = json.load(f)
                
                data, segments = normalize_segments_data(raw_data)
                total_words = sum(len(seg.get("words", [])) for seg in segments)
                
                self.logger.info(f"✓ Alignment completed: {len(segments)} segments, {total_words} words")
                self.logger.info(f"✓ Output saved: {output_file.relative_to(self.job_dir)}")
                return True
            else:
                self.logger.error("Alignment output file not created")
                return False
                
        except subprocess.CalledProcessError as e:
            self.logger.error(f"MLX alignment failed: {e}", exc_info=True)
            if e.stderr:
                self.logger.error(f"Error output: {e.stderr}", exc_info=True)
            return False
    
    
    def _stage_ner(self) -> bool:
        """Stage 5: Named Entity Recognition using new modular stage"""
        
        try:
            # Check if NER is enabled
            ner_enabled = self.env_config.get("STAGE_05_NER_ENABLED", "true").lower() == "true"
            
            if not ner_enabled:
                self.logger.info("NER stage is disabled (skipping)")
                return True
            
            # Import NER stage module (module name starts with number, use importlib)
            import importlib
            ner_stage = importlib.import_module("scripts.05_ner")
            
            # Call the stage module
            self.logger.info("Running NER stage...")
            exit_code = ner_stage.run_stage(self.job_dir, "05_ner")
            
            if exit_code != 0:
                self.logger.warning("NER stage failed, continuing without NER data")
                return True  # Non-fatal failure
            
            self.logger.info("✓ NER stage complete")
            return True
            
        except Exception as e:
            self.logger.error(f"NER stage error: {e}", exc_info=True)
            if self.debug:
                self.logger.debug(traceback.format_exc())
            self.logger.warning("Continuing without NER data")
            return True  # Non-fatal, graceful degradation
    
    def _stage_subtitle_gen(self) -> bool:
        """Stage 9: Subtitle generation using new modular stage"""
        
        try:
            # Check if subtitle generation is enabled
            subtitle_enabled = self.env_config.get("STAGE_09_SUBTITLE_ENABLED", "true").lower() == "true"
            
            if not subtitle_enabled:
                self.logger.info("Subtitle generation is disabled (skipping)")
                return True
            
            # Import subtitle generation stage module (module name starts with number, use importlib)
            import importlib
            subtitle_gen = importlib.import_module("scripts.09_subtitle_gen")
            
            # Call the stage module
            self.logger.info("Running subtitle generation stage...")
            exit_code = subtitle_gen.run_stage(self.job_dir, "09_subtitle_gen")
            
            if exit_code != 0:
                self.logger.error("Subtitle generation failed")
                return False  # Fatal failure
            
            self.logger.info("✓ Subtitle generation complete")
            return True
            
        except Exception as e:
            self.logger.error(f"Subtitle generation error: {e}", exc_info=True)
            if self.debug:
                self.logger.debug(traceback.format_exc())
            return False  # Fatal failure
    
    def _stage_export_transcript(self) -> bool:
        """Stage: Export plain text transcript"""
        
        # Read from ASR stage output (already copied to transcripts/)
        segments_file = self.job_dir / "transcripts" / "segments.json"
        output_txt = self.job_dir / "transcripts" / "transcript.txt"
        
        # Log input/output
        self.logger.info(f"📥 Input: {segments_file.relative_to(self.job_dir)}")
        self.logger.info(f"📤 Output: {output_txt.relative_to(self.job_dir)}")
        self.logger.info("Exporting plain text transcript...")
        
        if not segments_file.exists():
            self.logger.error(f"Segments file not found: {segments_file}")
            return False
        
        try:
            with open(segments_file) as f:
                data = json.load(f)
            
            if "segments" not in data:
                self.logger.error("No segments in JSON file")
                return False
            
            # Extract text from all segments
            lines = []
            for segment in data["segments"]:
                text = segment.get("text", "").strip()
                if text:
                    lines.append(text)
            
            # Write to text file
            with open(output_txt, 'w', encoding='utf-8') as f:
                f.write("\n".join(lines))
            
            self.logger.info(f"✓ Plain text transcript exported: {output_txt.name}")
            self.logger.info(f"Total lines: {len(lines)}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting transcript: {e}", exc_info=True)
            return False
    
    def _stage_load_transcript(self) -> bool:
        """Stage: Load transcript from ASR stage"""
        
        # Prefer cleaned transcript from transcripts/ (after hallucination removal)
        # Fall back to raw ASR output if not available
        transcript_file = self.job_dir / "transcripts" / "segments.json"
        segments_file = self._stage_path("asr") / "segments.json"
        
        # Use cleaned transcript if available, otherwise raw ASR output
        if transcript_file.exists():
            load_file = transcript_file
            self.logger.info("Using cleaned transcript (after hallucination removal)")
        elif segments_file.exists():
            load_file = segments_file
            self.logger.info("Using raw ASR transcript")
        else:
            self.logger.error("Transcript not found in transcripts/ or asr stage!")
            self.logger.error("Run transcribe workflow first!")
            return False
        
        # Log input
        self.logger.info(f"📥 Input: {load_file.relative_to(self.job_dir)}")
        self.logger.info("Loading transcript...")
        
        with open(load_file) as f:
            raw_data = json.load(f)
        
        # Normalize data format (handles both list and dict formats)
        data, segments = normalize_segments_data(raw_data)
        
        if not segments or len(segments) == 0:
            self.logger.error("No segments in transcript")
            return False
        
        self.logger.info(f"Loaded {len(segments)} segments")
        return True
    
    def _stage_hybrid_translation(self) -> bool:
        """
        Stage: Hybrid translation - IndicTrans2 for dialogue, LLM for songs
        
        Combines:
        - IndicTrans2 for dialogue (fast, accurate, free)
        - LLM with film context for songs/poetry (creative, culturally aware)
        
        Automatically routes segments based on lyrics detection results.
        Falls back to standard IndicTrans2 if LLM unavailable or disabled.
        """
        self.logger.info("Running hybrid translation...")
        
        # Check if enabled
        use_hybrid = self.env_config.get("USE_HYBRID_TRANSLATION", "true").lower() == "true"
        if not use_hybrid:
            self.logger.info("Hybrid translation disabled, using standard IndicTrans2")
            return self._stage_indictrans2_translation()
        
        # Get configuration
        use_llm_for_songs = self.env_config.get("USE_LLM_FOR_SONGS", "true").lower() == "true"
        llm_provider = self.env_config.get("LLM_PROVIDER", "anthropic")
        source_lang = self.job_config["source_language"]
        # Handle both target_language (singular) and target_languages (plural)
        target_lang = self._get_target_language()
        if not target_lang:
            target_langs = self.job_config.get("target_languages", [])
            target_lang = target_langs[0] if target_langs else None
        
        if not target_lang:
            raise ValueError("No target language specified in job config")
        
        self.logger.info(f"Configuration:")
        self.logger.info(f"  Translation: {source_lang} → {target_lang}")
        self.logger.info(f"  LLM provider: {llm_provider}")
        self.logger.info(f"  LLM for songs: {use_llm_for_songs}")
        
        # Get film context
        film_title = self.job_config.get("title", "")
        film_year = self.job_config.get("year", "")
        film_context = None
        
        if film_title and film_year:
            prompt_file = PROJECT_ROOT / "glossary" / "prompts" / f"{film_title.lower().replace(' ', '_')}_{film_year}.txt"
            if prompt_file.exists():
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    film_context = f.read()
                self.logger.info(f"✓ Loaded film context: {prompt_file.name}")
            else:
                self.logger.info(f"No film context found: {prompt_file.name}")
        
        # Input/output files (prefer lyrics-enhanced segments if available)
        segments_file = self._stage_path("lyrics_detection") / "segments.json"
        if not segments_file.exists():
            segments_file = self.job_dir / "lyrics_detection" / "segments.json"
        if not segments_file.exists():
            segments_file = self._stage_path("asr") / "segments.json"
        
        if not segments_file.exists():
            self.logger.error(f"Segments file not found: {segments_file}")
            return False
        
        # Output to translation stage directory
        output_dir = self._stage_path("translation")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"segments_{target_lang}.json"
        
        # Log input/output
        self.logger.info(f"📥 Input: {segments_file.relative_to(self.job_dir)}")
        self.logger.info(f"📤 Output: {output_file.relative_to(self.job_dir)}")
        
        try:
            # Get Python executable from LLM environment
            python_exe = self.env_manager.get_python_executable("llm")
            self.logger.info(f"Using LLM environment: {python_exe}")
            
            # Build environment variables
            env = os.environ.copy()
            env['OUTPUT_DIR'] = str(self.job_dir)  # CRITICAL: Tell script where job directory is
            env['CONFIG_PATH'] = str(self.job_dir / f".{self.job_config['job_id']}.env")
            env['SOURCE_LANG'] = source_lang
            env['TARGET_LANG'] = target_lang
            env['USE_LLM_FOR_SONGS'] = str(use_llm_for_songs).lower()
            env['LLM_PROVIDER'] = llm_provider
            env['DEBUG_MODE'] = 'true' if self.debug else 'false'
            env['LOG_LEVEL'] = 'DEBUG' if self.debug else 'INFO'
            env['SEGMENTS_FILE'] = str(segments_file)
            env['OUTPUT_FILE'] = str(output_file)
            env['JOB_DIR'] = str(self.job_dir)
            
            if film_title:
                env['FILM_TITLE'] = film_title
            if film_year:
                env['FILM_YEAR'] = str(film_year)
            
            # Pass glossary snapshot if available
            if hasattr(self, 'glossary_manager') and self.glossary_manager:
                glossary_snapshot = self._stage_path("glossary_load") / "glossary_snapshot.json"
                if glossary_snapshot.exists():
                    env['GLOSSARY_SNAPSHOT'] = str(glossary_snapshot)
                    self.logger.info(f"Using glossary snapshot for translation")
            
            # Run hybrid translator
            script_path = PROJECT_ROOT / "scripts" / "hybrid_translator.py"
            
            self.logger.info(f"Running: {script_path}")
            
            result = subprocess.run(
                [str(python_exe), str(script_path)],
                capture_output=True,
                text=True,
                check=True,
                cwd=str(PROJECT_ROOT),
                env=env
            )
            
            if self.debug and result.stdout:
                self.logger.debug(f"Hybrid translation output:\n{result.stdout}")
            
            if output_file.exists():
                # Load and report statistics
                with open(output_file, 'r', encoding='utf-8') as f:
                    raw_data = json.load(f)
                
                data, segments = normalize_segments_data(raw_data)
                
                stats = data.get('translation_stats', {})
                if stats:
                    self.logger.info(f"Translation statistics:")
                    self.logger.info(f"  Total segments: {stats.get('total_segments', 0)}")
                    self.logger.info(f"  Dialogue segments: {stats.get('dialogue_segments', 0)}")
                    self.logger.info(f"  Song segments: {stats.get('song_segments', 0)}")
                    self.logger.info(f"  IndicTrans2 used: {stats.get('indictrans2_used', 0)}")
                    self.logger.info(f"  LLM used: {stats.get('llm_used', 0)}")
                
                # Apply glossary post-processing if available
                if hasattr(self, 'glossary_manager') and self.glossary_manager:
                    try:
                        glossary_applied_count = 0
                        for segment in segments:
                            if 'text' in segment:
                                original_text = segment['text']
                                polished_text = self.glossary_manager.apply_to_text(
                                    original_text,
                                    context="translation"
                                )
                                if polished_text != original_text:
                                    segment['text'] = polished_text
                                    glossary_applied_count += 1
                        
                        if glossary_applied_count > 0:
                            # Save the glossary-enhanced version
                            with open(output_file, 'w', encoding='utf-8') as f:
                                json.dump(data, f, indent=2, ensure_ascii=False)
                            self.logger.info(f"✓ Glossary applied to {glossary_applied_count} segments")
                    except Exception as e:
                        self.logger.warning(f"Failed to apply glossary: {e}")
                
                # Copy to transcripts/ for compatibility
                transcripts_dir = self.job_dir / "transcripts"
                transcripts_dir.mkdir(parents=True, exist_ok=True)
                import shutil
                shutil.copy2(output_file, transcripts_dir / "segments_translated.json")
                
                self.logger.info(f"✓ Hybrid translation completed: {output_file.relative_to(self.job_dir)}")
                self.logger.info(f"✓ Copied to: transcripts/segments_translated.json")
                return True
            else:
                self.logger.error("Hybrid translation failed - no output file")
                return False
                
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Hybrid translation error: {e.stderr}", exc_info=True)
            self.logger.warning("Falling back to standard IndicTrans2")
            return self._stage_indictrans2_translation()
        except Exception as e:
            self.logger.error(f"Unexpected error in hybrid translation: {e}", exc_info=True)
            if self.debug:
                import traceback
                self.logger.debug(traceback.format_exc())
            self.logger.warning("Falling back to standard IndicTrans2")
            return self._stage_indictrans2_translation()
    
    def _stage_indictrans2_translation(self) -> bool:
        """Stage 7: Translate using IndicTrans2"""
        
        # Input from lyrics detection (if available) or ASR
        segments_file = self._stage_path("lyrics_detection") / "segments.json"
        if not segments_file.exists():
            segments_file = self.job_dir / "lyrics_detection" / "segments.json"
        if not segments_file.exists():
            segments_file = self._stage_path("asr") / "segments.json"
        
        if not segments_file.exists():
            self.logger.error(f"Segments file not found")
            return False
        
        source_lang = self.job_config["source_language"]
        target_lang = self._get_target_language()
        
        # Output to translation stage directory
        output_dir = self._stage_path("translation")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"segments_{target_lang}.json"
        
        # Log input/output
        self.logger.info(f"📥 Input: {segments_file.relative_to(self.job_dir)}")
        self.logger.info(f"📤 Output: {output_file.relative_to(self.job_dir)}")
        self.logger.info("Translating with IndicTrans2...")
        
        # Get configuration from job's .env file (set by prepare-job)
        device = self.env_config.get("INDICTRANS2_DEVICE", self.main_config.indictrans2_device)
        num_beams = self.env_config.get("INDICTRANS2_NUM_BEAMS", "4")
        max_tokens = self.env_config.get("INDICTRANS2_MAX_NEW_TOKENS", "128")
        
        # Dynamically select model based on language pair (no hardcoding)
        # Model selection happens in indictrans2_translator.py based on source/target
        
        self.logger.info(f"Using IndicTrans2 device: {device} (from job config)")
        self.logger.info(f"Translation: {source_lang} → {target_lang}")
        self.logger.info(f"Num beams: {num_beams} (from job config)")
        
        # Use existing IndicTrans2 translator in venv/indictrans2
        # Get Python executable from IndicTrans2 environment
        python_exe = self.env_manager.get_python_executable("indictrans2")
        self.logger.info(f"Using IndicTrans2 environment: {python_exe}")
        
        cmd = [
            str(python_exe), "-c",
            f"""
import json
from pathlib import Path
from scripts.indictrans2_translator import translate_whisperx_result

# Load segments
with open('{segments_file}') as f:
    segments = json.load(f)

# Translate with job-configured settings
from shared.logger import PipelineLogger
log_file = Path('{self.job_dir / "logs"}') / 'indictrans2_translation.log'
logger = PipelineLogger(module_name='indictrans2', log_file=log_file, log_level='{"DEBUG" if self.debug else "INFO"}')

# Set device for IndicTrans2 (from job config)
import os
os.environ['INDICTRANS2_DEVICE'] = '{device}'
os.environ['INDICTRANS2_NUM_BEAMS'] = '{num_beams}'
os.environ['INDICTRANS2_MAX_NEW_TOKENS'] = '{max_tokens}'

# translate_whisperx_result will auto-select the right model based on language pair
translated = translate_whisperx_result(segments, '{source_lang}', '{target_lang}', logger)

# Save
with open('{output_file}', 'w') as f:
    json.dump(translated, f, indent=2)

logger.info(f"Translated {{len(translated['segments'])}} segments")
"""
        ]
        
        try:
            # Set up environment with debug flag
            env = os.environ.copy()
            env['DEBUG_MODE'] = 'true' if self.debug else 'false'
            env['LOG_LEVEL'] = 'DEBUG' if self.debug else 'INFO'
            
            # Pass glossary snapshot if available
            if hasattr(self, 'glossary_manager') and self.glossary_manager:
                glossary_snapshot = self._stage_path("glossary_load") / "glossary_snapshot.json"
                if glossary_snapshot.exists():
                    env['GLOSSARY_SNAPSHOT'] = str(glossary_snapshot)
                    self.logger.info(f"Using glossary snapshot for IndicTrans2 translation")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                env=env
            )
            
            if output_file.exists():
                # Apply glossary post-processing if available
                if hasattr(self, 'glossary_manager') and self.glossary_manager:
                    try:
                        with open(output_file, 'r', encoding='utf-8') as f:
                            raw_data = json.load(f)
                        
                        data, segments = normalize_segments_data(raw_data)
                        
                        glossary_applied_count = 0
                        for segment in segments:
                            if 'text' in segment:
                                original_text = segment['text']
                                polished_text = self.glossary_manager.apply_to_text(
                                    original_text,
                                    context="translation"
                                )
                                if polished_text != original_text:
                                    segment['text'] = polished_text
                                    glossary_applied_count += 1
                        
                        if glossary_applied_count > 0:
                            # Save the glossary-enhanced version
                            with open(output_file, 'w', encoding='utf-8') as f:
                                json.dump(data, f, indent=2, ensure_ascii=False)
                            self.logger.info(f"✓ Glossary applied to {glossary_applied_count} segments")
                    except Exception as e:
                        self.logger.warning(f"Failed to apply glossary: {e}")
                
                # Copy to transcripts/ for compatibility
                transcripts_dir = self.job_dir / "transcripts"
                transcripts_dir.mkdir(parents=True, exist_ok=True)
                import shutil
                shutil.copy2(output_file, transcripts_dir / "segments_translated.json")
                
                self.logger.info(f"✓ Translation completed: {output_file.relative_to(self.job_dir)}")
                self.logger.info(f"✓ Copied to: transcripts/segments_translated.json")
                return True
            else:
                self.logger.error("Translation failed")
                return False
                
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Translation error: {e.stderr}", exc_info=True)
            return False
    
    def _stage_subtitle_generation(self) -> bool:
        """Stage 8: Generate SRT subtitle file in target language"""
        
        target_lang = self._get_target_language()
        
        # Read from translation stage
        segments_file = self._stage_path("translation") / f"segments_{target_lang}.json"
        
        if not segments_file.exists():
            # Fallback to old location
            segments_file = self.job_dir / "transcripts" / "segments_translated.json"
        
        if not segments_file.exists():
            self.logger.error(f"Translated segments not found: {segments_file}")
            return False
        
        # Output to subtitle generation stage directory
        output_dir = self._stage_path("subtitle_generation")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        title = self.job_config.get("title", "output")
        output_srt = output_dir / f"{title}.{target_lang}.srt"
        
        # Log input/output
        self.logger.info(f"📥 Input: {segments_file.relative_to(self.job_dir)}")
        self.logger.info(f"📤 Output: {output_srt.relative_to(self.job_dir)}")
        self.logger.info("Generating subtitles...")
        
        # Load translated segments
        try:
            with open(segments_file, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
                data, segments = normalize_segments_data(raw_data)
        except Exception as e:
            self.logger.error(f"Failed to load segments: {e}", exc_info=True)
            return False
        
        # Generate SRT file
        if generate_srt_from_segments(segments, output_srt):
            # Copy to subtitles/ for compatibility
            subtitles_dir = self.job_dir / "subtitles"
            subtitles_dir.mkdir(parents=True, exist_ok=True)
            final_output = subtitles_dir / output_srt.name
            
            # Only copy if source and destination are different
            if output_srt != final_output:
                import shutil
                shutil.copy2(output_srt, final_output)
                self.logger.info(f"✓ Subtitles generated: {output_srt.relative_to(self.job_dir)}")
                self.logger.info(f"✓ Copied to: subtitles/{output_srt.name}")
            else:
                self.logger.info(f"✓ Subtitles generated: {output_srt.relative_to(self.job_dir)}")
            
            return True
        else:
            self.logger.error("Subtitle generation failed")
            return False
    
    def _stage_subtitle_generation_source(self) -> bool:
        """Stage 8: Generate SRT subtitle file in source language"""
        
        source_lang = self.job_config["source_language"]
        
        # Read from ASR stage (or transcripts copy)
        segments_file = self._stage_path("asr") / "segments.json"
        if not segments_file.exists():
            segments_file = self.job_dir / "transcripts" / "segments.json"
        
        if not segments_file.exists():
            self.logger.error(f"Segments not found: {segments_file}")
            return False
        
        # Output to subtitle generation stage directory
        output_dir = self._stage_path("subtitle_generation")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        title = self.job_config.get("title", "output")
        output_srt = output_dir / f"{title}.{source_lang}.srt"
        
        # Log input/output
        self.logger.info(f"📥 Input: {segments_file.relative_to(self.job_dir)}")
        self.logger.info(f"📤 Output: {output_srt.relative_to(self.job_dir)}")
        self.logger.info("Generating source language subtitles...")
        
        # Load segments
        try:
            with open(segments_file, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
                data, segments = normalize_segments_data(raw_data)
        except Exception as e:
            self.logger.error(f"Failed to load segments: {e}", exc_info=True)
            return False
        
        # Generate SRT file
        if generate_srt_from_segments(segments, output_srt):
            # Copy to subtitles/ for compatibility
            subtitles_dir = self.job_dir / "subtitles"
            subtitles_dir.mkdir(parents=True, exist_ok=True)
            final_output = subtitles_dir / output_srt.name
            
            # Only copy if source and destination are different
            if output_srt != final_output:
                import shutil
                shutil.copy2(output_srt, final_output)
                self.logger.info(f"✓ Source subtitles generated: {output_srt.relative_to(self.job_dir)}")
                self.logger.info(f"✓ Copied to: subtitles/{output_srt.name}")
            else:
                self.logger.info(f"✓ Source subtitles generated: {output_srt.relative_to(self.job_dir)}")
            
            return True
        else:
            self.logger.error("Source subtitle generation failed")
            return False
    
    def _stage_hybrid_translation_multi(self, target_lang: str) -> bool:
        """
        Stage: Hybrid translation for multiple target languages (subtitle workflow)
        
        Wrapper around _stage_hybrid_translation for multi-language subtitle workflow.
        Temporarily updates job_config with current target language.
        """
        # Temporarily set target language for this translation
        original_target = self._get_target_language()
        # Set both formats for compatibility
        self.job_config["target_language"] = target_lang
        if "target_languages" in self.job_config:
            self.job_config["target_languages"] = [target_lang]
        
        try:
            # Call main hybrid translation stage
            result = self._stage_hybrid_translation()
            
            # If successful, rename output file to include language code
            if result:
                generic_output = self.job_dir / "transcripts" / "segments_translated.json"
                lang_specific_output = self.job_dir / "transcripts" / f"segments_translated_{target_lang}.json"
                
                if generic_output.exists():
                    # Copy to language-specific file
                    import shutil
                    shutil.copy2(generic_output, lang_specific_output)
                    self.logger.info(f"✓ Translation saved: {lang_specific_output.name}")
            
            return result
            
        finally:
            # Restore original target language
            if original_target:
                self.job_config["target_language"] = original_target
                if "target_languages" in self.job_config:
                    self.job_config["target_languages"] = [original_target]
    
    def _stage_indictrans2_translation_multi(self, target_lang: str) -> bool:
        """Translate to specific target language (for multi-language support)"""
        self.logger.info(f"Translating to {target_lang.upper()}...")
        
        segments_file = self.job_dir / "transcripts" / "segments.json"
        output_file = self.job_dir / "transcripts" / f"segments_translated_{target_lang}.json"
        
        source_lang = self.job_config["source_language"]
        
        # Get configuration from job's .env file
        device = self.env_config.get("INDICTRANS2_DEVICE", self.main_config.indictrans2_device)
        num_beams = self.env_config.get("INDICTRANS2_NUM_BEAMS", "4")
        max_tokens = self.env_config.get("INDICTRANS2_MAX_NEW_TOKENS", "128")
        
        self.logger.info(f"Using IndicTrans2 device: {device} (from job config)")
        self.logger.info(f"Translation: {source_lang} → {target_lang}")
        
        # Use existing IndicTrans2 translator in venv/indictrans2
        # Get Python executable from IndicTrans2 environment
        python_exe = self.env_manager.get_python_executable("indictrans2")
        self.logger.info(f"Using IndicTrans2 environment: {python_exe}")
        
        cmd = [
            str(python_exe), "-c",
            f"""
import json
from pathlib import Path
from scripts.indictrans2_translator import translate_whisperx_result

# Load segments
with open('{segments_file}') as f:
    segments = json.load(f)

# Translate with job-configured settings
from shared.logger import PipelineLogger
log_file = Path('{self.job_dir / "logs"}') / 'indictrans2_translation_{target_lang}.log'
logger = PipelineLogger(module_name='indictrans2_{target_lang}', log_file=log_file, log_level='{"DEBUG" if self.debug else "INFO"}')

# Set device for IndicTrans2 (from job config)
import os
os.environ['INDICTRANS2_DEVICE'] = '{device}'
os.environ['INDICTRANS2_NUM_BEAMS'] = '{num_beams}'
os.environ['INDICTRANS2_MAX_NEW_TOKENS'] = '{max_tokens}'

# translate_whisperx_result will auto-select the right model based on language pair
translated = translate_whisperx_result(segments, '{source_lang}', '{target_lang}', logger)

# Save
with open('{output_file}', 'w') as f:
    json.dump(translated, f, indent=2)

logger.info(f"Translated {{len(translated['segments'])}} segments to {target_lang}")
"""
        ]
        
        try:
            stage_name = f"indictrans2_translation_{target_lang}"
            
            result = self._run_in_environment(
                stage_name,
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            if output_file.exists():
                self.logger.info(f"Translation to {target_lang.upper()} completed: {output_file}")
                return True
            else:
                self.logger.error(f"Translation to {target_lang} failed")
                return False
                
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Translation to {target_lang} error: {e.stderr}", exc_info=True)
            return False
    
    def _stage_nllb_translation(self) -> bool:
        """Stage 2 (translate): Translate using NLLB for non-Indic languages"""
        self.logger.info("Translating with NLLB...")
        
        segments_file = self.job_dir / "transcripts" / "segments.json"
        output_file = self.job_dir / "transcripts" / "segments_translated.json"
        
        source_lang = self.job_config["source_language"]
        target_lang = self._get_target_language()
        
        # Get configuration from job's .env file (set by prepare-job)
        device = self.env_config.get("NLLB_DEVICE", "mps")
        model_size = self.env_config.get("NLLB_MODEL_SIZE", "600M")
        
        # Model name based on size
        model_map = {
            "600M": "facebook/nllb-200-distilled-600M",
            "1.3B": "facebook/nllb-200-1.3B",
            "3.3B": "facebook/nllb-200-3.3B"
        }
        model_name = model_map.get(model_size, "facebook/nllb-200-distilled-600M")
        
        self.logger.info(f"Using NLLB model: {model_name}")
        self.logger.info(f"Device: {device} (from job config)")
        self.logger.info(f"Translation: {source_lang} → {target_lang}")
        
        # Get Python executable from NLLB environment
        python_exe = self.env_manager.get_python_executable("nllb")
        self.logger.info(f"Using NLLB environment: {python_exe}")
        
        cmd = [
            str(python_exe), "-c",
            f"""
import json
from pathlib import Path
from scripts.nllb_translator import translate_whisperx_result, NLLBConfig

# Load segments
with open('{segments_file}') as f:
    segments = json.load(f)

# Setup logging
from shared.logger import PipelineLogger
log_file = Path('{self.job_dir / "logs"}') / 'nllb_translation.log'
logger = PipelineLogger(module_name='nllb', log_file=log_file, log_level='{"DEBUG" if self.debug else "INFO"}')

# Configure NLLB
config = NLLBConfig(
    model_name='{model_name}',
    device='{device}'
)

# Translate
translated = translate_whisperx_result(segments, '{source_lang}', '{target_lang}', logger: logging.Logger, config)

# Save
with open('{output_file}', 'w') as f:
    json.dump(translated, f, indent=2, ensure_ascii=False)

logger.info(f"Translated {{len(translated['segments'])}} segments")
"""
        ]
        
        try:
            # Set up environment with debug flag
            env = os.environ.copy()
            env['DEBUG_MODE'] = 'true' if self.debug else 'false'
            env['LOG_LEVEL'] = 'DEBUG' if self.debug else 'INFO'
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                cwd=str(PROJECT_ROOT),
                env=env
            )
            
            if output_file.exists():
                self.logger.info(f"Translation completed: {output_file}")
                return True
            else:
                self.logger.error("Translation failed")
                return False
                
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Translation error: {e.stderr}", exc_info=True)
            return False
    
    def _stage_nllb_translation_multi(self, target_lang: str) -> bool:
        """Translate to specific target language using NLLB (for multi-language support)"""
        self.logger.info(f"Translating to {target_lang.upper()} with NLLB...")
        
        segments_file = self.job_dir / "transcripts" / "segments.json"
        output_file = self.job_dir / "transcripts" / f"segments_translated_{target_lang}.json"
        
        source_lang = self.job_config["source_language"]
        
        # Get configuration from job's .env file
        device = self.env_config.get("NLLB_DEVICE", "mps")
        model_size = self.env_config.get("NLLB_MODEL_SIZE", "600M")
        
        # Model name based on size
        model_map = {
            "600M": "facebook/nllb-200-distilled-600M",
            "1.3B": "facebook/nllb-200-1.3B",
            "3.3B": "facebook/nllb-200-3.3B"
        }
        model_name = model_map.get(model_size, "facebook/nllb-200-distilled-600M")
        
        self.logger.info(f"Using NLLB model: {model_name}")
        self.logger.info(f"Device: {device}")
        self.logger.info(f"Translation: {source_lang} → {target_lang}")
        
        # Get Python executable from NLLB environment
        python_exe = self.env_manager.get_python_executable("nllb")
        self.logger.info(f"Using NLLB environment: {python_exe}")
        
        cmd = [
            str(python_exe), "-c",
            f"""
import json
from pathlib import Path
from scripts.nllb_translator import translate_whisperx_result, NLLBConfig

# Load segments
with open('{segments_file}') as f:
    segments = json.load(f)

# Setup logging
from shared.logger import PipelineLogger
log_file = Path('{self.job_dir / "logs"}') / 'nllb_{target_lang}_translation.log'
logger = PipelineLogger(module_name='nllb_{target_lang}', log_file=log_file, log_level='{"DEBUG" if self.debug else "INFO"}')

# Configure NLLB
config = NLLBConfig(
    model_name='{model_name}',
    device='{device}'
)

# Translate
translated = translate_whisperx_result(segments, '{source_lang}', '{target_lang}', logger: logging.Logger, config)

# Save
with open('{output_file}', 'w') as f:
    json.dump(translated, f, indent=2, ensure_ascii=False)

logger.info(f"Translated {{len(translated['segments'])}} segments to {target_lang}")
"""
        ]
        
        try:
            # Set up environment with debug flag
            env = os.environ.copy()
            env['DEBUG_MODE'] = 'true' if self.debug else 'false'
            env['LOG_LEVEL'] = 'DEBUG' if self.debug else 'INFO'
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                cwd=str(PROJECT_ROOT),
                env=env
            )
            
            if output_file.exists():
                self.logger.info(f"Translation to {target_lang.upper()} completed: {output_file}")
                return True
            else:
                self.logger.error(f"Translation to {target_lang} failed")
                return False
                
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Translation to {target_lang} error: {e.stderr}", exc_info=True)
            return False
    
    def _stage_subtitle_generation_target_multi(self, target_lang: str) -> bool:
        """Generate subtitle file for specific target language"""
        self.logger.info(f"Generating {target_lang.upper()} subtitles...")
        
        segments_file = self.job_dir / "transcripts" / f"segments_translated_{target_lang}.json"
        
        # Generate filename
        title = self.job_config.get("title", "output")
        output_srt = self.job_dir / "subtitles" / f"{title}.{target_lang}.srt"
        
        # Load translated segments
        try:
            with open(segments_file, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
                data, segments = normalize_segments_data(raw_data)
        except Exception as e:
            self.logger.error(f"Failed to load {target_lang} segments: {e}", exc_info=True)
            return False
        
        # Generate SRT file
        if generate_srt_from_segments(segments, output_srt):
            self.logger.info(f"{target_lang.upper()} subtitles generated: {output_srt}")
            return True
        else:
            self.logger.error(f"{target_lang} subtitle generation failed", exc_info=True)
            return False
    
    def _stage_subtitle_generation_target(self) -> bool:
        """Stage 3b (subtitle workflow): Generate SRT subtitle file in target language"""
        self.logger.info("Generating target language subtitles...")
        
        segments_file = self.job_dir / "transcripts" / "segments_translated.json"
        target_lang = self._get_target_language()
        
        # Generate filename
        title = self.job_config.get("title", "output")
        output_srt = self.job_dir / "subtitles" / f"{title}.{target_lang}.srt"
        
        # Load translated segments
        try:
            with open(segments_file, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
                data, segments = normalize_segments_data(raw_data)
        except Exception as e:
            self.logger.error(f"Failed to load segments: {e}", exc_info=True)
            return False
        
        # Generate SRT file
        if generate_srt_from_segments(segments, output_srt):
            self.logger.info(f"Target subtitles generated: {output_srt}")
            return True
        else:
            self.logger.error("Target subtitle generation failed", exc_info=True)
            return False
    
    def _stage_hinglish_detection(self) -> bool:
        """Stage 3b (subtitle workflow): Detect and tag word-level languages in Hinglish subtitles"""
        self.logger.info("Running Hinglish word-level language detection...")
        
        source_lang = self.job_config["source_language"]
        title = self.job_config.get("title", "output")
        
        # Source subtitle file
        source_srt = self.job_dir / "subtitles" / f"{title}.{source_lang}.srt"
        
        if not source_srt.exists():
            self.logger.warning(f"Source subtitle not found: {source_srt}")
            self.logger.warning("Skipping Hinglish detection")
            return True  # Not a failure, just skip
        
        # Output files
        tagged_srt = self.job_dir / "subtitles" / f"{title}.{source_lang}.tagged.srt"
        analysis_json = self.job_dir / "subtitles" / f"{title}.{source_lang}.analysis.json"
        
        self.logger.info(f"Analyzing: {source_srt}")
        
        # Get Python executable from common environment
        python_exe = self.env_manager.get_python_executable("common")
        
        # Run hinglish detector
        cmd = [
            str(python_exe),
            str(self.scripts_dir / "hinglish_word_detector.py"),
            str(source_srt),
            "-o", str(tagged_srt),
            "-j", str(analysis_json)
        ]
        
        if self.debug:
            cmd.append("-v")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            self.logger.info(f"✓ Tagged SRT created: {tagged_srt}")
            self.logger.info(f"✓ Analysis JSON created: {analysis_json}")
            
            # Parse and log statistics from output
            if "Hindi words:" in result.stdout:
                for line in result.stdout.split('\n'):
                    if 'words:' in line.lower() or 'Total' in line:
                        self.logger.info(f"  {line.strip()}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Hinglish detection failed: {e.stderr}", exc_info=True)
            self.logger.warning("Continuing without Hinglish detection...")
            return True  # Don't fail the pipeline, just warn
    
    def _stage_mux(self) -> bool:
        """Stage 9: Mux video with multiple subtitle tracks (up to 5)"""
        
        # Get configuration
        input_media = Path(self.job_config["input_media"])
        title = self.job_config.get("title", "output")
        source_lang = self.job_config["source_language"]
        target_languages = self.job_config.get("target_languages", [])
        
        # Get media processing configuration for clipping
        media_config = self.job_config.get("media_processing", {})
        processing_mode = media_config.get("mode", "full")
        start_time = media_config.get("start_time", "")
        end_time = media_config.get("end_time", "")
        
        # Collect all subtitle files (target languages + source)
        # Try from 08_subtitle_generation first, fallback to subtitles/
        subtitle_files = []
        subtitle_langs = []
        
        subtitle_dir = self._stage_path("subtitle_generation")
        fallback_dir = self.job_dir / "subtitles"
        
        # Add target language subtitles
        for target_lang in target_languages:
            target_srt = subtitle_dir / f"{title}.{target_lang}.srt"
            if not target_srt.exists():
                target_srt = fallback_dir / f"{title}.{target_lang}.srt"
            
            if not target_srt.exists():
                self.logger.error(f"Target subtitle not found: {target_lang}")
                return False
            subtitle_files.append(target_srt)
            subtitle_langs.append(target_lang)
        
        # Add source language subtitle
        source_srt = subtitle_dir / f"{title}.{source_lang}.srt"
        if not source_srt.exists():
            source_srt = fallback_dir / f"{title}.{source_lang}.srt"
        
        if not source_srt.exists():
            self.logger.error(f"Source subtitle not found: {source_lang}")
            return False
        subtitle_files.append(source_srt)
        subtitle_langs.append(source_lang)
        
        # Output directory
        output_dir = self.job_dir / "10_mux"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Log input/output
        self.logger.info(f"📥 Input video: {input_media.name}")
        for i, (sub_file, lang) in enumerate(zip(subtitle_files, subtitle_langs), 1):
            self.logger.info(f"📥 Input subtitle {i}: {sub_file.relative_to(self.job_dir)} ({lang})")
        
        self.logger.info(f"Muxing video with {len(subtitle_files)} subtitle tracks: {', '.join(subtitle_langs)}")
        
        # Detect source file extension and use same format for output
        source_ext = input_media.suffix.lower()  # e.g., '.mp4', '.mkv', '.avi'
        
        # Determine output format
        if source_ext in ['.mp4', '.m4v']:
            output_ext = '.mp4'
            subtitle_codec = 'mov_text'  # MP4 subtitle format
        elif source_ext in ['.mkv', '.webm']:
            output_ext = '.mkv'
            subtitle_codec = 'srt'  # MKV subtitle format
        elif source_ext in ['.avi']:
            output_ext = '.mkv'  # AVI doesn't support subtitle tracks well, use MKV
            subtitle_codec = 'srt'
            self.logger.info(f"Source is AVI, using MKV for subtitle support")
        else:
            # Default to MKV for unknown formats (best subtitle support)
            output_ext = '.mkv'
            subtitle_codec = 'srt'
            self.logger.info(f"Unknown format {source_ext}, using MKV for subtitle support")
        
        # Output video file in 09_mux directory
        output_video = output_dir / f"{title}_subtitled{output_ext}"
        
        # Also create copy in media subdirectory for user convenience
        media_name = input_media.stem
        media_output_subdir = self.job_dir / "media" / media_name
        media_output_subdir.mkdir(parents=True, exist_ok=True)
        media_output_video = media_output_subdir / f"{title}_subtitled{output_ext}"
        
        self.logger.info(f"📤 Output: {output_video.relative_to(self.job_dir)}")
        self.logger.info(f"Output format: {output_ext} (source: {source_ext})")
        
        # Build ffmpeg command
        cmd = ["ffmpeg", "-y"]
        
        # Add log level based on debug mode
        if not self.debug:
            cmd.extend(["-loglevel", "error"])
        
        # Add clipping if configured
        if processing_mode == "clip" and start_time:
            cmd.extend(["-ss", start_time])
        
        # Add input files - video first, then all subtitles
        cmd.extend(["-i", str(input_media)])  # Video input (index 0)
        for sub_file in subtitle_files:
            cmd.extend(["-i", str(sub_file)])  # Subtitle inputs (indices 1, 2, 3...)
        
        # Add end time if clipping
        if processing_mode == "clip" and end_time:
            cmd.extend(["-to", end_time])
        
        # Map streams: video, audio, all subtitles
        cmd.extend([
            "-map", "0:v",  # Video from input 0
            "-map", "0:a",  # Audio from input 0
        ])
        
        # Map all subtitle files
        for i in range(len(subtitle_files)):
            cmd.extend(["-map", str(i + 1)])  # Subtitle from input 1, 2, 3...
        
        # Copy codecs (no re-encoding)
        cmd.extend(["-c", "copy"])
        
        # Set subtitle codec based on output format
        cmd.extend(["-c:s", subtitle_codec])
        
        # Add metadata for each subtitle track
        # Map 2-letter codes to ISO 639-2 (3-letter) for better player compatibility
        lang_map_iso639_2 = {
            "hi": "hin",  # Hindi
            "en": "eng",  # English
            "gu": "guj",  # Gujarati
            "ta": "tam",  # Tamil
            "te": "tel",  # Telugu
            "bn": "ben",  # Bengali
            "mr": "mar",  # Marathi
            "kn": "kan",  # Kannada
            "ml": "mal",  # Malayalam
            "pa": "pan",  # Punjabi
            "ur": "urd",  # Urdu
            "as": "asm",  # Assamese
            "or": "ori",  # Odia
            "ne": "nep",  # Nepali
            "sd": "snd",  # Sindhi
            "si": "sin",  # Sinhala
            "sa": "san",  # Sanskrit
        }
        
        # Map to full language names for display
        lang_names = {
            "hin": "Hindi", "hi": "Hindi",
            "eng": "English", "en": "English",
            "guj": "Gujarati", "gu": "Gujarati",
            "tam": "Tamil", "ta": "Tamil",
            "tel": "Telugu", "te": "Telugu",
            "ben": "Bengali", "bn": "Bengali",
            "mar": "Marathi", "mr": "Marathi",
            "kan": "Kannada", "kn": "Kannada",
            "mal": "Malayalam", "ml": "Malayalam",
            "pan": "Punjabi", "pa": "Punjabi",
            "urd": "Urdu", "ur": "Urdu",
            "asm": "Assamese", "as": "Assamese",
            "ori": "Odia", "or": "Odia",
            "nep": "Nepali", "ne": "Nepali",
            "snd": "Sindhi", "sd": "Sindhi",
            "sin": "Sinhala", "si": "Sinhala",
            "san": "Sanskrit", "sa": "Sanskrit",
        }
        
        for i, lang in enumerate(subtitle_langs):
            # Convert to ISO 639-2 (3-letter code)
            lang_iso = lang_map_iso639_2.get(lang, lang)
            # Get full language name
            lang_title = lang_names.get(lang, lang.upper())
            
            cmd.extend([
                "-metadata:s:s:" + str(i), f"language={lang_iso}",
                "-metadata:s:s:" + str(i), f"title={lang_title}",
            ])
        
        # Output file
        cmd.append(str(output_video))
        
        mode_str = f"clipped ({start_time} to {end_time})" if processing_mode == "clip" else "full"
        self.logger.info(f"Creating {mode_str} video with {len(subtitle_files)} subtitle tracks...")
        for i, lang in enumerate(subtitle_langs):
            lang_iso = lang_map_iso639_2.get(lang, lang)
            lang_title = lang_names.get(lang, lang.upper())
            self.logger.info(f"  • Track {i}: {lang_title} ({lang_iso})")
        
        try:
            # Set up environment with debug flag
            env = os.environ.copy()
            env['DEBUG_MODE'] = 'true' if self.debug else 'false'
            env['LOG_LEVEL'] = 'DEBUG' if self.debug else 'INFO'
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                env=env
            )
            
            if self.debug and result.stderr:
                self.logger.debug(f"FFmpeg output: {result.stderr}")
            
            if output_video.exists():
                size_mb = output_video.stat().st_size / (1024 * 1024)
                self.logger.info(f"✓ Video created: {output_video.relative_to(self.job_dir)} ({size_mb:.1f} MB)")
                self.logger.info(f"✓ Video contains {len(subtitle_files)} subtitle tracks: {', '.join([l.upper() for l in subtitle_langs])}")
                
                # Also copy to media subdirectory for user convenience
                import shutil
                shutil.copy2(output_video, media_output_video)
                self.logger.info(f"✓ Copy saved to: {media_output_video.relative_to(self.job_dir)}")
                
                return True
            else:
                self.logger.error("Video muxing failed - no output file")
                return False
                
        except subprocess.CalledProcessError as e:
            self.logger.error(f"FFmpeg muxing error: {e.stderr}", exc_info=True)
            return False
    
    # ========================================================================
    # Main Execution
    # ========================================================================
    
    def run(self) -> bool:
        """Execute pipeline based on workflow"""
        self.logger.info(f"Starting pipeline: {self.workflow}")
        self.logger.info(f"Job ID: {self.job_config['job_id']}")
        self.logger.info(f"Job directory: {self.job_dir}")
        
        self.manifest["status"] = "running"
        self._save_manifest()
        
        if self.workflow == "transcribe":
            success = self.run_transcribe_workflow()
        elif self.workflow == "translate":
            success = self.run_translate_workflow()
        elif self.workflow == "subtitle":
            success = self.run_subtitle_workflow()
        else:
            self.logger.error(f"Unknown workflow: {self.workflow}")
            success = False
        
        if success:
            self.manifest["status"] = "completed"
            self.logger.info("=" * 80)
            self.logger.info("PIPELINE COMPLETED SUCCESSFULLY")
            self.logger.info("=" * 80)
        else:
            self.manifest["status"] = "failed"
            self.logger.error("=" * 80)
            self.logger.error("PIPELINE FAILED")
            self.logger.error("=" * 80)
        
        self._save_manifest()
        return success
    
    def _stage_hallucination_removal(self) -> bool:
        """
        Stage: Remove hallucinations from ASR transcript
        
        Detects and removes looping/repetition hallucinations from WhisperX output.
        Runs after ASR, before alignment.
        
        Follows developer standards:
        - Uses Config class for configuration
        - Proper error handling with graceful degradation
        - Logging with PipelineLogger
        - Respects opt-out (HALLUCINATION_REMOVAL_ENABLED=false)
        
        Returns:
            bool: True if successful or disabled, False on error
        """
        self.logger.info("Running hallucination removal...")
        
        # Check if enabled (default: true, opt-out)
        enabled = self.env_config.get('HALLUCINATION_REMOVAL_ENABLED', 'true').lower() == 'true'
        if not enabled:
            self.logger.info("Hallucination removal is disabled (HALLUCINATION_REMOVAL_ENABLED=false)")
            self.logger.info("Skipping stage - segments will be used as-is")
            return True
        
        # Configuration with defaults (following developer standards)
        loop_threshold = int(self.env_config.get('HALLUCINATION_LOOP_THRESHOLD', '3'))
        max_repeats = int(self.env_config.get('HALLUCINATION_MAX_REPEATS', '2'))
        
        self.logger.info(f"Configuration:")
        self.logger.info(f"  Loop threshold: {loop_threshold} (min consecutive repeats to consider hallucination)")
        self.logger.info(f"  Max repeats: {max_repeats} (max occurrences to keep)")
        
        # Input/output paths
        segments_file = self.job_dir / "transcripts" / "segments.json"
        if not segments_file.exists():
            self.logger.error(f"Segments file not found: {segments_file}")
            self.logger.error("Run ASR stage first!")
            return False
        
        try:
            # Load segments
            with open(segments_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract segments and metadata
            if isinstance(data, dict):
                segments = data.get('segments', [])
                metadata = {k: v for k, v in data.items() if k != 'segments'}
            else:
                segments = data
                metadata = {}
            
            if not segments:
                self.logger.warning("No segments found - nothing to clean")
                return True
            
            original_count = len(segments)
            self.logger.info(f"Processing {original_count} segments...")
            
            # Import hallucination remover (late import to avoid issues)
            sys.path.insert(0, str(SCRIPT_DIR))
            from hallucination_removal import HallucinationRemover
            
            # Create remover instance
            remover = HallucinationRemover(
                loop_threshold=loop_threshold,
                max_repeats=max_repeats,
                logger=None  # Use pipeline logger instead
            )
            
            # Detect loops manually (for logging)
            loops = remover.detect_looping_hallucinations(segments)
            
            if loops:
                self.logger.warning(f"Detected {len(loops)} hallucination loop(s):")
                for start_idx, end_idx, text in loops:
                    count = end_idx - start_idx + 1
                    self.logger.warning(f"  • '{text}' repeated {count} times (segments {start_idx}-{end_idx})")
            else:
                self.logger.info("No hallucination loops detected - segments are clean")
            
            # Remove loops
            cleaned_segments = remover.remove_looping_hallucinations(segments, loops)
            cleaned_count = len(cleaned_segments)
            removed_count = original_count - cleaned_count
            
            # Log results
            if removed_count > 0:
                self.logger.info(f"Removed {removed_count} hallucinated segments")
                self.logger.info(f"Kept {cleaned_count}/{original_count} segments ({cleaned_count/original_count*100:.1f}%)")
                
                # Calculate repetition improvement
                before_texts = [seg.get('text', '').strip() for seg in segments if seg.get('text', '').strip()]
                after_texts = [seg.get('text', '').strip() for seg in cleaned_segments if seg.get('text', '').strip()]
                
                before_unique = len(set(before_texts))
                after_unique = len(set(after_texts))
                
                before_rep_rate = 1.0 - (before_unique / len(before_texts)) if before_texts else 0.0
                after_rep_rate = 1.0 - (after_unique / len(after_texts)) if after_texts else 0.0
                
                if before_rep_rate > 0:
                    improvement = ((before_rep_rate - after_rep_rate) / before_rep_rate) * 100
                    self.logger.info(f"Repetition rate improved: {before_rep_rate:.1%} → {after_rep_rate:.1%} ({improvement:.0f}% better)")
            else:
                self.logger.info("No hallucinations found - transcript is clean")
            
            # Save cleaned segments (backup original first)
            backup_file = segments_file.with_suffix('.json.pre-hallucination-removal')
            if not backup_file.exists():
                import shutil
                shutil.copy2(segments_file, backup_file)
                self.logger.info(f"Backed up original segments: {backup_file.name}")
            
            # Write cleaned segments
            output_data = metadata.copy()
            output_data['segments'] = cleaned_segments
            output_data['hallucination_removal'] = {
                'enabled': True,
                'original_count': original_count,
                'cleaned_count': cleaned_count,
                'removed_count': removed_count,
                'loops_detected': len(loops),
                'loop_threshold': loop_threshold,
                'max_repeats': max_repeats
            }
            
            with open(segments_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Cleaned segments saved: {segments_file}")
            self.logger.info("✅ Hallucination removal completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error in hallucination removal: {e}", exc_info=True)
            if self.main_config.debug_mode:
                import traceback
                self.logger.error(f"Traceback: {traceback.format_exc()}", exc_info=True)
            
            # Graceful degradation - continue with original segments
            self.logger.warning("Continuing with original segments (graceful degradation)")
            return True  # Don't fail pipeline, just skip cleaning


def main() -> Any:
    """Main."""
    parser = argparse.ArgumentParser(
        description="IndicTrans2 Pipeline Orchestrator"
    )
    
    parser.add_argument(
        "--job-dir",
        type=Path,
        required=True,
        help="Job directory"
    )
    
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from last completed stage"
    )
    
    args = parser.parse_args()
    
    if not args.job_dir.exists():
        logger.info(f"❌ Error: Job directory not found: {args.job_dir}")
        return 1
    
    # Create and run pipeline
    pipeline = IndicTrans2Pipeline(args.job_dir, args.resume)
    success = pipeline.run()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
