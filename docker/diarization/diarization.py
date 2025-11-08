#!/usr/bin/env python3
"""
Diarization container - Speaker labeling using PyAnnote

Workflow: Stage 6 (MANDATORY per workflow-arch.txt)
Input: audio/audio.wav (+ optional VAD segments)
Output: diarization/speaker_segments.json (speaker timestamps BEFORE ASR)

NOTE: Per workflow-arch.txt, diarization runs BEFORE ASR to provide
      speaker boundaries for transcription.

Phase 2 Enhancement: Native PyTorch execution support
"""
import sys
import warnings

# Suppress known deprecation warnings from dependencies
warnings.filterwarnings('ignore', message='.*speechbrain.pretrained.*deprecated.*')
warnings.filterwarnings('ignore', message='.*pytorch_lightning.*ModelCheckpoint.*')
import json
import os
from pathlib import Path

# ============================================================================
# PHASE 2: Native Execution Mode Check
# ============================================================================
def verify_pytorch_availability():
    """Verify PyTorch is available in native or Docker environment.
    
    Phase 2 Enhancement: Containers no longer include PyTorch in image.
    PyTorch is provided by native .bollyenv environment for optimal performance.
    """
    execution_mode = os.getenv('EXECUTION_MODE', 'docker')
    
    try:
        import torch
        
        # Set UTF-8 encoding for Windows console output
        if sys.platform == 'win32':
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
        
        # Verify CUDA availability if expected
        cuda_available = torch.cuda.is_available()
        device_name = torch.cuda.get_device_name(0) if cuda_available else "CPU"
        
        print(f"[OK] PyTorch {torch.__version__} available")
        print(f"[OK] Execution mode: {execution_mode}")
        print(f"[OK] Device: {device_name}")
        
        return True
        
    except ImportError as e:
        print("=" * 70)
        print("ERROR: PyTorch not available")
        print("=" * 70)
        print(f"Execution mode: {execution_mode}")
        print("")
        
        if execution_mode == 'native':
            print("Native execution mode requires bootstrap:")
            print("  1. Run: ./scripts/bootstrap.ps1")
            print("  2. Ensure .bollyenv volume mounted in docker-compose.yml")
            print("  3. Check PATH includes: /app/.bollyenv/bin")
        else:
            print("Docker execution mode requires PyTorch in image:")
            print("  - This image is SLIM (no PyTorch)")
            print("  - Use native mode or rebuild with full image")
        
        print("=" * 70)
        sys.exit(1)

# Verify PyTorch before proceeding
verify_pytorch_availability()
# ============================================================================

# Setup paths - handle both Docker and native execution
execution_mode = os.getenv('EXECUTION_MODE', 'docker')
project_root = Path(__file__).resolve().parents[2]  # docker/diarization -> root

if execution_mode == 'native':
    # Native mode: add project root to path
    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(project_root / 'scripts'))
    sys.path.insert(0, str(project_root / 'shared'))
else:
    # Docker mode: use /app paths
    sys.path.insert(0, '/app')
    sys.path.insert(0, '/app/scripts')
    sys.path.insert(0, '/app/shared')

# Try importing from scripts (works for both native and docker)
try:
    from scripts.diarization import DiarizationProcessor
except ImportError:
    from diarization import DiarizationProcessor

try:
    from shared.logger import PipelineLogger
except ImportError:
    from logger import PipelineLogger


def main():
    if len(sys.argv) < 2:
        print("Usage: diarization.py <movie_dir>")
        sys.exit(1)
    
    movie_dir = Path(sys.argv[1])
    
    # Load config
    try:
        from config import load_config
        config = load_config()
        log_level = config.log_level.upper() if hasattr(config, 'log_level') else "INFO"
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        sys.exit(1)
    
    # Setup logger
    logger = PipelineLogger("diarization", log_level=log_level)
    logger.info(f"Starting diarization for: {movie_dir}")
    logger.info("Per workflow-arch.txt: Stage 6 BEFORE Stage 7 (ASR)")
    
    # Find audio file
    audio_file = movie_dir / "audio" / "audio.wav"
    if not audio_file.exists():
        logger.error(f"Audio file not found: {audio_file}")
        sys.exit(1)
    
    logger.info(f"Audio file: {audio_file}")
    
    logger.info(f"Audio file: {audio_file}")
    
    # Setup output
    diar_dir = movie_dir / "diarization"
    diar_dir.mkdir(exist_ok=True, parents=True)
    
    # Get HF token from config or environment
    hf_token = config.hf_token if hasattr(config, 'hf_token') and config.hf_token else os.getenv("HF_TOKEN", "")
    if not hf_token:
        # Try loading from secrets.json
        try:
            secrets_file = Path("/app/config/secrets.json")
            if secrets_file.exists():
                with open(secrets_file) as f:
                    secrets = json.load(f)
                    hf_token = secrets.get('hf_token') or secrets.get('HF_TOKEN') or ""
        except Exception as e:
            logger.warning(f"Could not load secrets.json: {e}")
    
    if not hf_token:
        logger.error("HF_TOKEN not found in config, environment, or config/secrets.json")
        logger.error("Required for pyannote diarization model")
        sys.exit(1)
    
    # Get diarization parameters from config
    device = config.get('diarization_device', 'cpu')
    min_speakers = config.get('diarization_min_speakers')
    max_speakers = config.get('diarization_max_speakers')
    model_name = config.get('diarization_model', 'pyannote/speaker-diarization-3.1')
    speaker_map_str = config.get('speaker_map', '')
    auto_speaker_mapping = config.get('diarization_auto_speaker_mapping', True)
    
    logger.info(f"Configuration:")
    logger.info(f"  Device: {device}")
    logger.info(f"  Model: {model_name}")
    logger.info(f"  Min speakers: {min_speakers or 'auto'}")
    logger.info(f"  Max speakers: {max_speakers or 'auto'}")
    logger.info(f"  Auto speaker mapping: {auto_speaker_mapping}")
    if speaker_map_str:
        logger.info(f"  Speaker map: {speaker_map_str}")
    
    # Initialize diarization processor
    processor = DiarizationProcessor(
        hf_token=hf_token,
        device=device,
        model_name=model_name,
        logger=logger
    )
    
    # Load diarization model
    try:
        logger.info("Loading PyAnnote diarization model...")
        processor.load_model()
        
        # Parse speaker map if provided
        speaker_map = None
        if speaker_map_str:
            try:
                speaker_map = json.loads(speaker_map_str) if speaker_map_str.startswith('{') else None
            except:
                logger.warning(f"Could not parse SPEAKER_MAP, ignoring")
        
        # Run diarization on audio (BEFORE ASR per workflow-arch.txt)
        logger.info("Running diarization on audio file...")
        diarize_result = processor.diarize_audio(
            audio_file=str(audio_file),
            min_speakers=min_speakers,
            max_speakers=max_speakers
        )
        
        # Save speaker segments for ASR to use
        output_file = diar_dir / f"{movie_dir.name}.speaker_segments.json"
        
        # Convert diarization result to serializable format
        speaker_segments = []
        if hasattr(diarize_result, 'itertracks'):
            for turn, _, speaker in diarize_result.itertracks(yield_label=True):
                speaker_segments.append({
                    "start": turn.start,
                    "end": turn.end,
                    "speaker": speaker
                })
        
        # Load TMDB character names for auto-mapping if enabled
        character_names = None
        if auto_speaker_mapping and not speaker_map_str:
            tmdb_file = movie_dir / 'metadata' / 'tmdb_data.json'
            if tmdb_file.exists():
                try:
                    with open(tmdb_file, 'r', encoding='utf-8') as f:
                        tmdb_data = json.load(f)
                    
                    cast = tmdb_data.get('cast', [])
                    if cast:
                        character_names = []
                        for actor in sorted(cast, key=lambda x: x.get('order', 999))[:max_speakers or 10]:
                            character = actor.get('character', '')
                            if character:
                                character = character.split('(')[0].strip()
                                character_names.append(character)
                        
                        logger.info(f"Loaded {len(character_names)} character names from TMDB")
                except Exception as e:
                    logger.warning(f"Could not load TMDB metadata: {e}")
        
        # Apply manual speaker map if provided
        if speaker_map:
            logger.info("Applying manual speaker name mapping...")
            for seg in speaker_segments:
                if seg["speaker"] in speaker_map:
                    seg["speaker_original"] = seg["speaker"]
                    seg["speaker"] = speaker_map[seg["speaker"]]
        # Apply auto speaker mapping from TMDB if available and no manual map
        elif character_names:
            logger.info("Applying auto speaker mapping from TMDB cast...")
            speaker_ids = sorted(set(seg['speaker'] for seg in speaker_segments))
            
            for i, speaker_id in enumerate(speaker_ids):
                if i < len(character_names):
                    character_name = character_names[i]
                    for seg in speaker_segments:
                        if seg['speaker'] == speaker_id:
                            seg['speaker_original'] = speaker_id
                            seg['speaker'] = character_name
                    logger.info(f"Mapped {speaker_id} → {character_name}")
        
        output_data = {
            "speaker_segments": speaker_segments,
            "num_speakers": len(set(seg["speaker"] for seg in speaker_segments)),
            "total_segments": len(speaker_segments),
            "config": {
                "model": model_name,
                "device": device,
                "min_speakers": min_speakers,
                "max_speakers": max_speakers,
                "speaker_map_applied": bool(speaker_map),
                "auto_speaker_mapping": auto_speaker_mapping,
                "tmdb_mapping_applied": bool(character_names) and not bool(speaker_map)
            }
        }
        
        if character_names and not speaker_map:
            output_data['character_names'] = character_names
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✓ Diarization complete: {len(speaker_segments)} speaker turns")
        logger.info(f"✓ Identified {len(set(seg['speaker'] for seg in speaker_segments))} unique speakers")
        logger.info(f"✓ Output: {output_file}")
        logger.info("→ ASR will use these speaker boundaries (Stage 7)")
        
        # Also save as text for inspection
        txt_file = diar_dir / f"{movie_dir.name}.speaker_segments.txt"
        with open(txt_file, "w", encoding="utf-8") as f:
            f.write("Speaker Segments (for ASR Stage 7)\n")
            f.write("=" * 50 + "\n\n")
            for seg in speaker_segments:
                f.write(f"[{seg['start']:.2f} - {seg['end']:.2f}] {seg['speaker']}\n")
        
        logger.info(f"✓ Text output: {txt_file}")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Diarization failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
