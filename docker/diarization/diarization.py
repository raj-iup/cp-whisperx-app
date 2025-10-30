#!/usr/bin/env python3
"""
Diarization container - Speaker labeling using PyAnnote

Workflow: Stage 6 (MANDATORY per workflow-arch.txt)
Input: audio/audio.wav (+ optional VAD segments)
Output: diarization/speaker_segments.json (speaker timestamps BEFORE ASR)

NOTE: Per workflow-arch.txt, diarization runs BEFORE ASR to provide
      speaker boundaries for transcription.
"""
import sys
import json
import os
from pathlib import Path

# Setup paths
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/shared')

from scripts.diarization import DiarizationProcessor
from logger import PipelineLogger


def main():
    if len(sys.argv) < 2:
        print("Usage: diarization.py <movie_dir>")
        sys.exit(1)
    
    movie_dir = Path(sys.argv[1])
    
    # Setup logger
    logger = PipelineLogger("diarization")
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
    
    # Get config - Try environment first, then secrets.json
    hf_token = os.getenv("HF_TOKEN", "")
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
        logger.error("HF_TOKEN not found in environment or config/secrets.json")
        logger.error("Required for pyannote diarization model")
        sys.exit(1)
    
    device = os.getenv("DEVICE", "cpu")
    min_speakers = os.getenv("MIN_SPEAKERS")
    max_speakers = os.getenv("MAX_SPEAKERS")
    
    if min_speakers:
        min_speakers = int(min_speakers)
    if max_speakers:
        max_speakers = int(max_speakers)
    
    logger.info(f"Device: {device}")
    logger.info(f"Min speakers: {min_speakers or 'auto'}")
    logger.info(f"Max speakers: {max_speakers or 'auto'}")
    
    # Initialize diarization processor
    processor = DiarizationProcessor(
        hf_token=hf_token,
        device=device,
        logger=logger
    )
    
    # Load diarization model
    try:
        logger.info("Loading PyAnnote diarization model...")
        processor.load_model()
        
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
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump({
                "speaker_segments": speaker_segments,
                "num_speakers": len(set(seg["speaker"] for seg in speaker_segments)),
                "total_segments": len(speaker_segments)
            }, f, indent=2, ensure_ascii=False)
        
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
