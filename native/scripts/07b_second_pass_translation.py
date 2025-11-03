#!/usr/bin/env python3
"""Stage 7b: Second Pass Translation - Refine WhisperX translations with specialized models"""
import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Optional
import time

sys.path.insert(0, 'native/utils')
from device_manager import get_device
from native_logger import NativePipelineLogger
from manifest import StageManifest


def load_env_config() -> dict:
    """Load configuration from environment variables."""
    return {
        'enabled': os.getenv('SECOND_PASS_ENABLED', 'false').lower() == 'true',
        'backend': os.getenv('SECOND_PASS_BACKEND', 'nllb'),
        'source_language': os.getenv('WHISPER_LANGUAGE', 'hi'),
        'target_language': os.getenv('TARGET_LANGUAGE', 'en'),
        'device': os.getenv('WHISPERX_DEVICE', 'cpu'),
        'batch_size': int(os.getenv('WHISPER_BATCH_SIZE', '16')),
        'task': os.getenv('WHISPER_TASK', 'translate')
    }


def run_second_pass_translation(
    asr_result: Dict,
    source_lang: str,
    target_lang: str,
    backend: str,
    device: str,
    logger,
    batch_size: int = 16
) -> Dict:
    """
    Run second-pass translation on WhisperX output.
    
    Strategy:
    1. If task was 'translate': Re-run specialized translation model on original audio
    2. If task was 'transcribe': Translate the source language transcript
    
    Args:
        asr_result: WhisperX ASR result with segments
        source_lang: Source language code
        target_lang: Target language code
        backend: Translation backend ('nllb', 'opus-mt', 'mbart')
        device: Device to run on
        logger: Logger instance
        batch_size: Batch size for translation
        
    Returns:
        Enhanced result with better translations
    """
    logger.info(f"Running second-pass translation: {source_lang} -> {target_lang}")
    logger.info(f"Backend: {backend}")
    
    segments = asr_result.get('segments', [])
    if not segments:
        logger.warning("No segments to translate")
        return asr_result
    
    # Extract text from segments
    texts = [seg.get('text', '').strip() for seg in segments if seg.get('text', '').strip()]
    if not texts:
        logger.warning("No text found in segments")
        return asr_result
    
    logger.info(f"Translating {len(texts)} segments...")
    
    try:
        if backend == 'nllb':
            translated_texts = _translate_nllb(texts, source_lang, target_lang, device, logger, batch_size)
        elif backend == 'opus-mt':
            translated_texts = _translate_opus_mt(texts, source_lang, target_lang, device, logger, batch_size)
        elif backend == 'mbart':
            translated_texts = _translate_mbart(texts, source_lang, target_lang, device, logger, batch_size)
        else:
            logger.error(f"Unknown backend: {backend}")
            return asr_result
        
        # Update segments with refined translations
        text_idx = 0
        for seg in segments:
            if seg.get('text', '').strip():
                seg['text_original'] = seg['text']  # Save original
                seg['text'] = translated_texts[text_idx]
                seg['translation_method'] = f'second_pass_{backend}'
                text_idx += 1
        
        asr_result['segments'] = segments
        asr_result['second_pass_enabled'] = True
        asr_result['second_pass_backend'] = backend
        
        logger.info(f"✓ Second-pass translation complete: {len(translated_texts)} segments refined")
        
        return asr_result
        
    except Exception as e:
        logger.error(f"Second-pass translation failed: {e}")
        logger.warning("Falling back to original WhisperX translations")
        return asr_result


def _translate_nllb(texts: List[str], src_lang: str, tgt_lang: str, device: str, logger, batch_size: int) -> List[str]:
    """Translate using NLLB-200 model."""
    logger.info("Loading NLLB-200 model...")
    
    try:
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
        
        model_name = "facebook/nllb-200-distilled-600M"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        
        # Map language codes to NLLB format
        lang_map = {
            'hi': 'hin_Deva',
            'en': 'eng_Latn',
            'es': 'spa_Latn',
            'fr': 'fra_Latn',
            'de': 'deu_Latn',
            'zh': 'zho_Hans',
            'ja': 'jpn_Jpan',
            'ko': 'kor_Hang'
        }
        
        src_lang_code = lang_map.get(src_lang, 'hin_Deva')
        tgt_lang_code = lang_map.get(tgt_lang, 'eng_Latn')
        
        # Move model to device
        if device == 'cuda':
            model = model.cuda()
        elif device == 'mps':
            model = model.to('mps')
        
        logger.info(f"✓ NLLB model loaded on {device}")
        
        # Translate in batches
        translated = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            
            inputs = tokenizer(batch, return_tensors="pt", padding=True, truncation=True, max_length=512)
            
            if device == 'cuda':
                inputs = {k: v.cuda() for k, v in inputs.items()}
            elif device == 'mps':
                inputs = {k: v.to('mps') for k, v in inputs.items()}
            
            tokenizer.src_lang = src_lang_code
            forced_bos_token_id = tokenizer.convert_tokens_to_ids(tgt_lang_code)
            
            outputs = model.generate(
                **inputs,
                forced_bos_token_id=forced_bos_token_id,
                max_length=512,
                num_beams=5,
                early_stopping=True
            )
            
            batch_translations = tokenizer.batch_decode(outputs, skip_special_tokens=True)
            translated.extend(batch_translations)
            
            if (i + batch_size) % (batch_size * 5) == 0:
                logger.debug(f"Translated {len(translated)}/{len(texts)} segments")
        
        return translated
        
    except Exception as e:
        logger.error(f"NLLB translation failed: {e}")
        raise


def _translate_opus_mt(texts: List[str], src_lang: str, tgt_lang: str, device: str, logger, batch_size: int) -> List[str]:
    """Translate using Helsinki-NLP Opus-MT model."""
    logger.info("Loading Opus-MT model...")
    
    try:
        from transformers import MarianMTModel, MarianTokenizer
        
        # Find appropriate Opus-MT model
        model_name = f"Helsinki-NLP/opus-mt-{src_lang}-{tgt_lang}"
        
        try:
            tokenizer = MarianTokenizer.from_pretrained(model_name)
            model = MarianMTModel.from_pretrained(model_name)
        except:
            # Try reverse direction or fallback
            logger.warning(f"Model {model_name} not found, trying alternatives...")
            model_name = "Helsinki-NLP/opus-mt-mul-en"  # Multilingual to English
            tokenizer = MarianTokenizer.from_pretrained(model_name)
            model = MarianMTModel.from_pretrained(model_name)
        
        # Move model to device
        if device == 'cuda':
            model = model.cuda()
        elif device == 'mps':
            model = model.to('mps')
        
        logger.info(f"✓ Opus-MT model loaded on {device}")
        
        # Translate in batches
        translated = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            
            inputs = tokenizer(batch, return_tensors="pt", padding=True, truncation=True, max_length=512)
            
            if device == 'cuda':
                inputs = {k: v.cuda() for k, v in inputs.items()}
            elif device == 'mps':
                inputs = {k: v.to('mps') for k, v in inputs.items()}
            
            outputs = model.generate(**inputs, max_length=512, num_beams=5)
            batch_translations = tokenizer.batch_decode(outputs, skip_special_tokens=True)
            translated.extend(batch_translations)
            
            if (i + batch_size) % (batch_size * 5) == 0:
                logger.debug(f"Translated {len(translated)}/{len(texts)} segments")
        
        return translated
        
    except Exception as e:
        logger.error(f"Opus-MT translation failed: {e}")
        raise


def _translate_mbart(texts: List[str], src_lang: str, tgt_lang: str, device: str, logger, batch_size: int) -> List[str]:
    """Translate using mBART model."""
    logger.info("Loading mBART model...")
    
    try:
        from transformers import MBartForConditionalGeneration, MBart50TokenizerFast
        
        model_name = "facebook/mbart-large-50-many-to-many-mmt"
        tokenizer = MBart50TokenizerFast.from_pretrained(model_name)
        model = MBartForConditionalGeneration.from_pretrained(model_name)
        
        # Map language codes
        lang_map = {
            'hi': 'hi_IN',
            'en': 'en_XX',
            'es': 'es_XX',
            'fr': 'fr_XX',
            'de': 'de_DE'
        }
        
        src_lang_code = lang_map.get(src_lang, 'hi_IN')
        tgt_lang_code = lang_map.get(tgt_lang, 'en_XX')
        
        # Move model to device
        if device == 'cuda':
            model = model.cuda()
        elif device == 'mps':
            model = model.to('mps')
        
        logger.info(f"✓ mBART model loaded on {device}")
        
        # Translate in batches
        tokenizer.src_lang = src_lang_code
        translated = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            
            inputs = tokenizer(batch, return_tensors="pt", padding=True, truncation=True, max_length=512)
            
            if device == 'cuda':
                inputs = {k: v.cuda() for k, v in inputs.items()}
            elif device == 'mps':
                inputs = {k: v.to('mps') for k, v in inputs.items()}
            
            forced_bos_token_id = tokenizer.lang_code_to_id[tgt_lang_code]
            outputs = model.generate(
                **inputs,
                forced_bos_token_id=forced_bos_token_id,
                max_length=512,
                num_beams=5
            )
            
            batch_translations = tokenizer.batch_decode(outputs, skip_special_tokens=True)
            translated.extend(batch_translations)
            
            if (i + batch_size) % (batch_size * 5) == 0:
                logger.debug(f"Translated {len(translated)}/{len(texts)} segments")
        
        return translated
        
    except Exception as e:
        logger.error(f"mBART translation failed: {e}")
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, help='Input video file')
    parser.add_argument('--movie-dir', required=True, help='Movie output directory')
    args = parser.parse_args()
    
    movie_dir = Path(args.movie_dir)
    movie_name = movie_dir.name
    logger = NativePipelineLogger('second_pass_translation', movie_name)
    
    try:
        logger.log_stage_start("Second Pass Translation - Refining translations")
        
        # Load configuration
        env_config = load_env_config()
        
        # Check if enabled
        if not env_config['enabled']:
            logger.info("Second pass translation disabled in config")
            logger.log_stage_success("Skipped (disabled)")
            return 0
        
        # Check if translation task (not transcription)
        if env_config['task'] != 'translate':
            logger.info(f"Task is '{env_config['task']}', second pass only works with 'translate'")
            logger.log_stage_success("Skipped (not translation task)")
            return 0
        
        logger.info(f"Backend: {env_config['backend']}")
        logger.info(f"Languages: {env_config['source_language']} -> {env_config['target_language']}")
        
        # Get device
        if env_config['device'].upper() not in ['CPU', 'MPS', 'CUDA']:
            device = get_device(prefer_mps=True, stage_name='second_pass_translation')
        else:
            device = env_config['device'].lower()
        
        logger.log_model_load(f"Translation model ({env_config['backend']})", device)
        
        start = time.time()
        
        with StageManifest('second_pass_translation', movie_dir, logger.logger) as manifest:
            # Load ASR result from stage 7
            asr_file = movie_dir / "asr" / f"{movie_name}.asr.json"
            if not asr_file.exists():
                logger.error(f"ASR file not found: {asr_file}")
                raise FileNotFoundError(f"ASR file not found: {asr_file}")
            
            with open(asr_file, 'r') as f:
                asr_result = json.load(f)
            
            logger.info(f"Loaded ASR result: {len(asr_result.get('segments', []))} segments")
            
            # Run second pass translation
            enhanced_result = run_second_pass_translation(
                asr_result=asr_result,
                source_lang=env_config['source_language'],
                target_lang=env_config['target_language'],
                backend=env_config['backend'],
                device=device,
                logger=logger,
                batch_size=env_config['batch_size']
            )
            
            # Save enhanced result (overwrite original)
            output_file = asr_file
            with open(output_file, 'w') as f:
                json.dump(enhanced_result, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved enhanced result: {output_file}")
            
            duration = time.time() - start
            
            # Update manifest
            manifest.add_output_file(output_file, "Enhanced ASR with second-pass translation")
            manifest.add_stat('duration', duration)
            manifest.add_stat('num_segments', len(enhanced_result.get('segments', [])))
            manifest.add_stat('backend', env_config['backend'])
            manifest.add_stat('source_language', env_config['source_language'])
            manifest.add_stat('target_language', env_config['target_language'])
        
        logger.log_stage_success(f"Enhanced {len(enhanced_result.get('segments', []))} segments in {duration:.1f}s")
        return 0
        
    except Exception as e:
        logger.log_stage_error(f"Second pass translation failed: {e}")
        import traceback
        logger.logger.error(traceback.format_exc())
        return 1


if __name__ == '__main__':
    sys.exit(main())
