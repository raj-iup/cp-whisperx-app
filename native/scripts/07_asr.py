#!/usr/bin/env python3
"""Stage 7: WhisperX ASR + Forced Alignment"""
import os
import sys
import json
import argparse
from pathlib import Path
from typing import Optional

sys.path.insert(0, 'native/utils')
from device_manager import get_device
from native_logger import NativePipelineLogger
from manifest import StageManifest


def load_env_config() -> dict:
    """Load configuration from environment variables."""
    return {
        'model_name': os.getenv('WHISPER_MODEL', 'large-v3'),
        'compute_type': os.getenv('WHISPER_COMPUTE_TYPE', 'int8'),
        'batch_size': int(os.getenv('WHISPER_BATCH_SIZE', '16')),
        'source_language': os.getenv('WHISPER_LANGUAGE', 'hi'),
        'target_language': os.getenv('TARGET_LANGUAGE', 'en'),
        'task': os.getenv('WHISPER_TASK', 'translate'),
        'device': os.getenv('WHISPERX_DEVICE', 'cpu'),
        'temperature': os.getenv('WHISPER_TEMPERATURE', '0.0,0.2,0.4,0.6,0.8,1.0'),
        'beam_size': int(os.getenv('WHISPER_BEAM_SIZE', '5')),
        'best_of': int(os.getenv('WHISPER_BEST_OF', '5')),
        'patience': float(os.getenv('WHISPER_PATIENCE', '1.0')),
        'length_penalty': float(os.getenv('WHISPER_LENGTH_PENALTY', '1.0')),
        'no_speech_threshold': float(os.getenv('WHISPER_NO_SPEECH_THRESHOLD', '0.6')),
        'logprob_threshold': float(os.getenv('WHISPER_LOGPROB_THRESHOLD', '-1.0')),
        'compression_ratio_threshold': float(os.getenv('WHISPER_COMPRESSION_RATIO_THRESHOLD', '2.4')),
        'condition_on_previous_text': os.getenv('WHISPER_CONDITION_ON_PREVIOUS_TEXT', 'true').lower() == 'true',
        'initial_prompt': os.getenv('WHISPER_INITIAL_PROMPT', '')
    }


def load_initial_prompt(movie_dir: Path, logger) -> str:
    """Load initial prompt from file."""
    # Try NER-enhanced prompt first
    ner_prompt = movie_dir / "prompts" / "ner_enhanced_prompt.txt"
    if ner_prompt.exists():
        with open(ner_prompt, 'r') as f:
            prompt = f.read().strip()
        logger.info(f"Loaded NER-enhanced prompt: {len(prompt)} chars")
        return prompt
    
    # Try other prompt files
    for prompt_file in [
        movie_dir / f"{movie_dir.name}.combined.initial_prompt.txt",
        movie_dir / f"{movie_dir.name}.initial_prompt.txt"
    ]:
        if prompt_file.exists():
            with open(prompt_file, 'r') as f:
                prompt = f.read().strip()
            logger.info(f"Loaded prompt from {prompt_file.name}: {len(prompt)} chars")
            return prompt
    
    logger.warning("No initial prompt file found")
    return ""


def run_asr(
    audio_file: Path,
    speaker_segments_file: Optional[Path],
    device: str,
    logger,
    config: dict = None
):
    """
    Run WhisperX ASR for speech-to-text transcription.
    
    Args:
        audio_file: Path to audio file
        speaker_segments_file: Path to speaker segments JSON
        device: Device to run on (cpu, mps, cuda)
        logger: Logger instance
        config: Configuration dict
        
    Returns:
        Tuple of (transcription_result, statistics)
    """
    logger.info(f"Running WhisperX ASR on {device}")
    logger.info(f"Model: {config.get('model_name', 'large-v3')}")
    logger.info(f"Source: {config.get('source_language', 'hi')} -> Target: {config.get('target_language', 'en')}")
    
    # Load speaker segments if available
    speaker_segments = None
    if speaker_segments_file and speaker_segments_file.exists():
        with open(speaker_segments_file, 'r') as f:
            speaker_data = json.load(f)
        speaker_segments = speaker_data.get('speaker_segments', [])
        logger.info(f"Loaded {len(speaker_segments)} speaker segments")
    else:
        logger.warning("No speaker segments found")
    
    import time
    start = time.time()
    
    try:
        # Import WhisperX
        import whisperx
        
        # Load model
        logger.info("Loading WhisperX model...")
        model = whisperx.load_model(
            config['model_name'],
            device=device,
            compute_type=config['compute_type']
        )
        logger.info("✓ Model loaded")
        
        # Load audio
        logger.info("Loading audio...")
        audio = whisperx.load_audio(str(audio_file))
        
        # Parse temperature
        temperature = [float(t.strip()) for t in config['temperature'].split(',')]
        
        # Transcribe
        logger.info("Transcribing...")
        logger.debug(f"  Temperature: {temperature}")
        logger.debug(f"  Beam size: {config['beam_size']}")
        
        transcribe_options = {
            "language": config['source_language'],
            "task": config['task'],
            "batch_size": config['batch_size'],
            "temperature": temperature,
            "beam_size": config['beam_size'],
            "best_of": config['best_of'],
            "patience": config['patience'],
            "length_penalty": config['length_penalty'],
            "no_speech_threshold": config['no_speech_threshold'],
            "logprob_threshold": config['logprob_threshold'],
            "compression_ratio_threshold": config['compression_ratio_threshold'],
            "condition_on_previous_text": config['condition_on_previous_text']
        }
        
        if config['initial_prompt']:
            transcribe_options['initial_prompt'] = config['initial_prompt']
            logger.info(f"  Using initial prompt: {len(config['initial_prompt'])} chars")
        
        result = model.transcribe(audio, **transcribe_options)
        segments = result.get("segments", [])
        logger.info(f"✓ Transcription complete: {len(segments)} segments")
        
        # Load alignment model
        target_lang = config['target_language']
        logger.info(f"Loading alignment model for {target_lang}...")
        try:
            align_model, align_metadata = whisperx.load_align_model(
                language_code=target_lang,
                device=device
            )
            
            # Align words
            logger.info("Aligning words...")
            result = whisperx.align(
                segments,
                align_model,
                align_metadata,
                audio,
                device=device,
                return_char_alignments=False
            )
            logger.info("✓ Word alignment complete")
        except Exception as e:
            logger.warning(f"Alignment failed: {e}")
            logger.warning("Continuing without word-level timestamps")
        
        # Assign speakers if available
        if speaker_segments:
            logger.info("Assigning speakers...")
            segments = result.get("segments", [])
            for segment in segments:
                seg_mid = (segment.get("start", 0) + segment.get("end", 0)) / 2
                for spk_seg in speaker_segments:
                    if spk_seg["start"] <= seg_mid <= spk_seg["end"]:
                        segment["speaker"] = spk_seg["speaker"]
                        break
            
            speakers_assigned = sum(1 for seg in segments if "speaker" in seg)
            logger.info(f"✓ Assigned speakers to {speakers_assigned}/{len(segments)} segments")
            result["segments"] = segments
        
        duration = time.time() - start
        
        # Calculate statistics
        total_words = sum(len(seg.get('words', [])) for seg in segments)
        stats = {
            'num_segments': len(segments),
            'total_words': total_words,
            'duration': duration,
            'language': config['source_language'],
            'target_language': target_lang,
            'device': device,
            'model': config['model_name']
        }
        
        logger.info(f"ASR complete: {len(segments)} segments, {total_words} words")
        
        return result, stats
        
    except Exception as e:
        logger.error(f"ASR failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, help='Input video file')
    parser.add_argument('--movie-dir', required=True, help='Movie output directory')
    args = parser.parse_args()
    
    movie_dir = Path(args.movie_dir)
    movie_name = movie_dir.name
    logger = NativePipelineLogger('asr', movie_name)
    
    try:
        logger.log_stage_start("WhisperX ASR - Transcription and translation")
        
        # Load configuration from environment
        env_config = load_env_config()
        
        # Load initial prompt from file (override env if file exists)
        prompt_from_file = load_initial_prompt(movie_dir, logger)
        if prompt_from_file:
            env_config['initial_prompt'] = prompt_from_file
        
        logger.info(f"Configuration: model={env_config['model_name']}, "
                   f"device={env_config['device']}, "
                   f"language={env_config['source_language']}->{env_config['target_language']}")
        
        # Get device
        if env_config['device'].upper() not in ['CPU', 'MPS', 'CUDA']:
            device = get_device(prefer_mps=True, stage_name='asr')
        else:
            device = env_config['device'].lower()
        
        logger.log_model_load(f"WhisperX {env_config['model_name']}", device)
        
        import time
        start = time.time()
        
        with StageManifest('asr', movie_dir, logger.logger) as manifest:
            # Get paths
            audio_file = movie_dir / 'audio' / 'audio.wav'
            speaker_segments_file = movie_dir / 'diarization' / 'speaker_segments.json'
            
            if not audio_file.exists():
                raise FileNotFoundError(f"Audio file not found: {audio_file}")
            
            logger.debug(f"Audio file: {audio_file}")
            
            # Run ASR with configuration
            result, stats = run_asr(
                audio_file=audio_file,
                speaker_segments_file=speaker_segments_file,
                device=device,
                logger=logger,
                config=env_config
            )
            
            duration = time.time() - start
            
            # Log results
            logger.log_processing("ASR complete", duration)
            logger.log_metric("Segments", stats['num_segments'])
            logger.log_metric("Words", stats['total_words'])
            logger.log_metric("Language", f"{stats['language']}->{stats['target_language']}")
            
            # Create output directory
            asr_dir = movie_dir / 'asr'
            asr_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"ASR directory: {asr_dir}")
            
            # Save ASR result
            output_file = asr_dir / f'{movie_name}.asr.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            logger.log_file_operation("Saved ASR result", output_file, success=True)
            
            # Save transcript text
            txt_file = asr_dir / f'{movie_name}.asr.txt'
            with open(txt_file, 'w', encoding='utf-8') as f:
                for seg in result.get('segments', []):
                    text = seg.get('text', '').strip()
                    if text:
                        f.write(f"{text}\n")
            
            logger.log_file_operation("Saved transcript", txt_file, success=True)
            
            # Save metadata
            metadata = {
                'model': env_config['model_name'],
                'device': device,
                'compute_type': env_config['compute_type'],
                'source_language': env_config['source_language'],
                'target_language': env_config['target_language'],
                'task': env_config['task'],
                'segments_count': stats['num_segments'],
                'words_count': stats['total_words'],
                'transcription_parameters': {
                    'batch_size': env_config['batch_size'],
                    'temperature': env_config['temperature'],
                    'beam_size': env_config['beam_size'],
                    'best_of': env_config['best_of'],
                    'patience': env_config['patience'],
                    'length_penalty': env_config['length_penalty'],
                    'no_speech_threshold': env_config['no_speech_threshold'],
                    'logprob_threshold': env_config['logprob_threshold'],
                    'compression_ratio_threshold': env_config['compression_ratio_threshold'],
                    'condition_on_previous_text': env_config['condition_on_previous_text'],
                    'initial_prompt_length': len(env_config['initial_prompt'])
                }
            }
            
            meta_file = asr_dir / f'{movie_name}.asr.meta.json'
            with open(meta_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            logger.log_file_operation("Saved metadata", meta_file, success=True)
            
            # Add to manifest
            manifest.add_output('transcript', output_file, 'WhisperX ASR transcript')
            manifest.add_metadata('device', device)
            manifest.add_metadata('model', env_config['model_name'])
            manifest.add_metadata('segments', stats['num_segments'])
            manifest.add_metadata('words', stats['total_words'])
        
        logger.log_stage_end(success=True)
        
    except Exception as e:
        logger.error(f"Stage failed with error: {e}")
        logger.log_stage_end(success=False)
        raise


if __name__ == '__main__':
    main()
