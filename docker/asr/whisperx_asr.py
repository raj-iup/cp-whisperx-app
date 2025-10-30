#!/usr/bin/env python3
"""
WhisperX ASR container - Transcription + Translation + Forced Alignment

Workflow: Stage 7 (per workflow-arch.txt)
Input: audio/audio.wav, vad/*.json, pre_ner prompts
Output: asr/*.asr.json with word-level timestamps
"""
import sys
import json
import os
from pathlib import Path
from typing import List, Dict, Optional

# Setup paths
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/shared')

from scripts.whisperx_integration import WhisperXProcessor
from logger import PipelineLogger


def load_initial_prompt(movie_dir: Path, logger: PipelineLogger) -> str:
    """Load initial prompt from Pre-NER output"""
    prompt = ""
    
    # Try combined prompt first
    combined_prompt = movie_dir / f"{movie_dir.name}.combined.initial_prompt.txt"
    if combined_prompt.exists():
        with open(combined_prompt) as f:
            prompt = f.read().strip()
        logger.info(f"Loaded combined prompt: {len(prompt)} chars")
        return prompt
    
    # Try initial prompt
    initial_prompt = movie_dir / f"{movie_dir.name}.initial_prompt.txt"
    if initial_prompt.exists():
        with open(initial_prompt) as f:
            prompt = f.read().strip()
        logger.info(f"Loaded initial prompt: {len(prompt)} chars")
        return prompt
    
    # Try Pre-NER entities
    pre_ner_file = movie_dir / "pre_ner" / "entities.json"
    if pre_ner_file.exists():
        with open(pre_ner_file) as f:
            data = json.load(f)
        entities = data.get("entities", [])
        if entities:
            prompt = ", ".join(entities[:50])
            logger.info(f"Built prompt from {len(entities)} Pre-NER entities")
            return prompt
    
    logger.warning("No initial prompt found")
    return ""


def load_vad_segments(movie_dir: Path, logger: PipelineLogger) -> Optional[List[Dict]]:
    """Load VAD segments if available"""
    
    # Try PyAnnote VAD first
    pyannote_vad = movie_dir / "vad" / "pyannote_refined_segments.json"
    if pyannote_vad.exists():
        with open(pyannote_vad) as f:
            segments = json.load(f)
        logger.info(f"Loaded PyAnnote VAD: {len(segments)} segments")
        return segments
    
    # Try Silero VAD
    silero_vad = movie_dir / "vad" / "silero_segments.json"
    if silero_vad.exists():
        with open(silero_vad) as f:
            segments = json.load(f)
        logger.info(f"Loaded Silero VAD: {len(segments)} segments")
        return segments
    
    logger.warning("No VAD segments found - will process entire audio")
    return None


def main():
    if len(sys.argv) < 2:
        print("Usage: whisperx_asr.py <movie_dir>")
        sys.exit(1)
    
    movie_dir = Path(sys.argv[1])
    
    # Setup logger
    logger = PipelineLogger("asr")
    logger.info(f"Starting WhisperX ASR for: {movie_dir}")
    
    # Find audio file
    audio_file = movie_dir / "audio" / "audio.wav"
    if not audio_file.exists():
        logger.error(f"Audio file not found: {audio_file}")
        sys.exit(1)
    
    logger.info(f"Audio file: {audio_file}")
    
    # Load initial prompt
    initial_prompt = load_initial_prompt(movie_dir, logger)
    
    # Load VAD segments (optional)
    vad_segments = load_vad_segments(movie_dir, logger)
    
    # Get config
    model_name = os.getenv("WHISPER_MODEL", "large-v2")
    device = os.getenv("DEVICE", "cpu")
    compute_type = os.getenv("COMPUTE_TYPE", "int8")
    source_lang = os.getenv("SOURCE_LANG", "hi")
    target_lang = os.getenv("TARGET_LANG", "en")
    batch_size = int(os.getenv("BATCH_SIZE", "16"))
    hf_token = os.getenv("HF_TOKEN", "")
    
    logger.info(f"Model: {model_name}")
    logger.info(f"Device: {device}")
    logger.info(f"Compute type: {compute_type}")
    logger.info(f"Source language: {source_lang}")
    logger.info(f"Target language: {target_lang}")
    
    # Initialize WhisperX processor
    processor = WhisperXProcessor(
        model_name=model_name,
        device=device,
        compute_type=compute_type,
        hf_token=hf_token,
        logger=logger
    )
    
    # Load model
    logger.info("Loading WhisperX model...")
    processor.load_model()
    
    # Load alignment model for target language
    logger.info(f"Loading alignment model for {target_lang}...")
    processor.load_align_model(target_lang)
    
    # Load diarization speaker segments (from Stage 6)
    speaker_segments = None
    diar_file = movie_dir / "diarization" / f"{movie_dir.name}.speaker_segments.json"
    if diar_file.exists():
        logger.info(f"Loading speaker segments from Stage 6...")
        with open(diar_file) as f:
            diar_data = json.load(f)
        speaker_segments = diar_data.get("speaker_segments", [])
        logger.info(f"✓ Loaded {len(speaker_segments)} speaker segments")
        logger.info(f"✓ {diar_data.get('num_speakers', 0)} unique speakers identified")
    else:
        logger.warning("No diarization segments found - ASR will run without speaker info")
    
    # Transcribe and translate
    try:
        logger.info("Starting transcription and translation...")
        
        result = processor.transcribe_with_bias(
            audio_file=str(audio_file),
            source_lang=source_lang,
            target_lang=target_lang,
            bias_windows=None,  # Bias windows loaded internally if available
            batch_size=batch_size
        )
        
        segments = result.get("segments", [])
        logger.info(f"✓ Transcription complete: {len(segments)} segments")
        
        # Align words
        if processor.align_model:
            logger.info("Aligning words to audio...")
            audio = __import__("whisperx").load_audio(str(audio_file))
            result = __import__("whisperx").align(
                segments,
                processor.align_model,
                processor.align_metadata,
                audio,
                device=device,
                return_char_alignments=False
            )
            logger.info("✓ Word alignment complete")
        
        # Assign speakers to segments if diarization available
        if speaker_segments:
            logger.info("Assigning speakers to transcript segments...")
            segments = result.get("segments", [])
            for segment in segments:
                seg_start = segment.get("start", 0)
                seg_end = segment.get("end", 0)
                seg_mid = (seg_start + seg_end) / 2
                
                # Find speaker for this segment's midpoint
                for spk_seg in speaker_segments:
                    if spk_seg["start"] <= seg_mid <= spk_seg["end"]:
                        segment["speaker"] = spk_seg["speaker"]
                        break
            
            speakers_assigned = sum(1 for seg in segments if "speaker" in seg)
            logger.info(f"✓ Assigned speakers to {speakers_assigned}/{len(segments)} segments")
            result["segments"] = segments
        
        # Save results
        output_dir = movie_dir / "asr"
        output_dir.mkdir(exist_ok=True, parents=True)
        
        output_file = output_dir / f"{movie_dir.name}.asr.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✓ ASR output saved: {output_file}")
        
        # Also save as text
        txt_file = output_dir / f"{movie_dir.name}.asr.txt"
        with open(txt_file, "w", encoding="utf-8") as f:
            for seg in result.get("segments", []):
                text = seg.get("text", "").strip()
                if text:
                    f.write(f"{text}\n")
        
        logger.info(f"✓ Text transcript saved: {txt_file}")
        
        # Save metadata
        metadata = {
            "model": model_name,
            "device": device,
            "compute_type": compute_type,
            "source_language": source_lang,
            "target_language": target_lang,
            "segments_count": len(segments),
            "has_word_timestamps": processor.align_model is not None
        }
        
        meta_file = output_dir / f"{movie_dir.name}.asr.meta.json"
        with open(meta_file, "w") as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"✓ Metadata saved: {meta_file}")
        logger.info("✓ WhisperX ASR complete")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"ASR failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
