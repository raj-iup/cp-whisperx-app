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
    
    # PRIORITY 1: Try NER-enhanced prompt from pre_ner stage (as per requirements)
    ner_enhanced_prompt = movie_dir / "prompts" / "ner_enhanced_prompt.txt"
    logger.debug(f"Checking for NER-enhanced prompt: {ner_enhanced_prompt}")
    logger.debug(f"File exists: {ner_enhanced_prompt.exists()}")
    if ner_enhanced_prompt.exists():
        with open(ner_enhanced_prompt) as f:
            prompt = f.read().strip()
        logger.info(f"Loaded NER-enhanced prompt from pre_ner: {len(prompt)} chars")
        return prompt
    
    # PRIORITY 2: Try combined prompt
    combined_prompt = movie_dir / f"{movie_dir.name}.combined.initial_prompt.txt"
    if combined_prompt.exists():
        with open(combined_prompt) as f:
            prompt = f.read().strip()
        logger.info(f"Loaded combined prompt: {len(prompt)} chars")
        return prompt
    
    # PRIORITY 3: Try initial prompt
    initial_prompt = movie_dir / f"{movie_dir.name}.initial_prompt.txt"
    if initial_prompt.exists():
        with open(initial_prompt) as f:
            prompt = f.read().strip()
        logger.info(f"Loaded initial prompt: {len(prompt)} chars")
        return prompt
    
    # PRIORITY 4: Try Pre-NER entities
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
    
    # Load config first to get all settings
    from config import load_config
    config = load_config()
    
    # Setup logger with config
    log_level = config.log_level.upper() if hasattr(config, 'log_level') else "INFO"
    logger = PipelineLogger("asr", log_level=log_level)
    logger.info(f"Starting WhisperX ASR for: {movie_dir}")
    
    # Log config source
    config_path = os.getenv('CONFIG_PATH', '/app/config/.env')
    logger.info(f"Using config: {config_path}")
    
    # Find audio file
    audio_file = movie_dir / "audio" / "audio.wav"
    if not audio_file.exists():
        logger.error(f"Audio file not found: {audio_file}")
        sys.exit(1)
    
    logger.info(f"Audio file: {audio_file}")
    
    # Load initial prompt
    # Load initial prompt from file or use env var
    initial_prompt_file = load_initial_prompt(movie_dir, logger)
    initial_prompt = config.get('whisper_initial_prompt', '') or initial_prompt_file
    
    # Load VAD segments (optional)
    vad_segments = load_vad_segments(movie_dir, logger)
    
    # Get config values with proper fallbacks
    model_name = config.get('whisper_model', 'large-v3')
    device = config.get('whisperx_device', config.get('device_whisperx', 'cpu'))
    compute_type = config.get('whisper_compute_type', 'int8')
    source_lang = config.get('whisper_language', 'hi')
    
    # Get target language - check multiple possible field names
    target_lang = config.get('target_lang') or config.get('tgt_lang', 'en')
    
    # Get transcription parameters
    batch_size = config.get('whisper_batch_size', 16)
    temperature = config.get('whisper_temperature', '0.0,0.2,0.4,0.6,0.8,1.0')
    beam_size = config.get('whisper_beam_size', 5)
    best_of = config.get('whisper_best_of', 5)
    patience = config.get('whisper_patience', 1.0)
    length_penalty = config.get('whisper_length_penalty', 1.0)
    no_speech_threshold = config.get('whisper_no_speech_threshold', 0.6)
    logprob_threshold = config.get('whisper_logprob_threshold', -1.0)
    compression_ratio_threshold = config.get('whisper_compression_ratio_threshold', 2.4)
    condition_on_previous_text = config.get('whisper_condition_on_previous_text', True)
    
    hf_token = config.get('hf_token', '')
    
    logger.info(f"Configuration:")
    logger.info(f"  Model: {model_name}")
    logger.info(f"  Device: {device}")
    logger.info(f"  Compute type: {compute_type}")
    logger.info(f"  Source language: {source_lang}")
    logger.info(f"  Target language: {target_lang}")
    logger.info(f"  Batch size: {batch_size}")
    logger.info(f"  Temperature: {temperature}")
    logger.info(f"  Beam size: {beam_size}")
    if initial_prompt:
        logger.info(f"  Initial prompt: {len(initial_prompt)} chars")
    
    # Initialize WhisperX processor with all parameters
    processor = WhisperXProcessor(
        model_name=model_name,
        device=device,
        compute_type=compute_type,
        hf_token=hf_token,
        temperature=temperature,
        beam_size=beam_size,
        best_of=best_of,
        patience=patience,
        length_penalty=length_penalty,
        no_speech_threshold=no_speech_threshold,
        logprob_threshold=logprob_threshold,
        compression_ratio_threshold=compression_ratio_threshold,
        condition_on_previous_text=condition_on_previous_text,
        initial_prompt=initial_prompt,
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
        
        # Save metadata with transcription parameters
        metadata = {
            "model": model_name,
            "device": device,
            "compute_type": compute_type,
            "source_language": source_lang,
            "target_language": target_lang,
            "segments_count": len(segments),
            "has_word_timestamps": processor.align_model is not None,
            "transcription_parameters": {
                "batch_size": batch_size,
                "temperature": temperature,
                "beam_size": beam_size,
                "best_of": best_of,
                "patience": patience,
                "length_penalty": length_penalty,
                "no_speech_threshold": no_speech_threshold,
                "logprob_threshold": logprob_threshold,
                "compression_ratio_threshold": compression_ratio_threshold,
                "condition_on_previous_text": condition_on_previous_text,
                "initial_prompt_length": len(initial_prompt) if initial_prompt else 0
            }
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
