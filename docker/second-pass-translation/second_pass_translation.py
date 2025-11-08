#!/usr/bin/env python3
"""
Second Pass Translation container - Refine WhisperX translations

Workflow: Stage 7b (new stage)
Input: asr/*.asr.json (from Stage 7)
Output: asr/*.asr.json (enhanced with better translations)
"""
import sys
import json
import os
from pathlib import Path
from typing import List, Dict

# Setup paths - handle both Docker and native execution
execution_mode = os.getenv('EXECUTION_MODE', 'docker')
if execution_mode == 'native':
    # Native mode: add project root to path
    project_root = Path(__file__).resolve().parents[2]  # docker/second-pass-translation -> root
    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(project_root / 'shared'))
else:
    # Docker mode: use /app paths
    sys.path.insert(0, '/app')
    sys.path.insert(0, '/app/shared')

from logger import PipelineLogger


def load_asr_result(movie_dir: Path, logger: PipelineLogger) -> Dict:
    """Load ASR result from Stage 7."""
    asr_file = movie_dir / "asr" / f"{movie_dir.name}.asr.json"
    
    if not asr_file.exists():
        logger.error(f"ASR file not found: {asr_file}")
        raise FileNotFoundError(f"ASR file not found")
    
    with open(asr_file, 'r') as f:
        result = json.load(f)
    
    logger.info(f"Loaded ASR result: {len(result.get('segments', []))} segments")
    return result


def translate_with_nllb(texts: List[str], src_lang: str, tgt_lang: str, device: str, logger: PipelineLogger, batch_size: int) -> List[str]:
    """Translate using NLLB-200 model."""
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    
    logger.info("Loading NLLB-200 model...")
    model_name = "facebook/nllb-200-distilled-600M"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    
    # Map language codes
    lang_map = {
        'hi': 'hin_Deva', 'en': 'eng_Latn', 'es': 'spa_Latn',
        'fr': 'fra_Latn', 'de': 'deu_Latn', 'zh': 'zho_Hans',
        'ja': 'jpn_Jpan', 'ko': 'kor_Hang'
    }
    
    src_lang_code = lang_map.get(src_lang, 'hin_Deva')
    tgt_lang_code = lang_map.get(tgt_lang, 'eng_Latn')
    
    if device == 'cuda':
        model = model.cuda()
    
    logger.info(f"[OK] NLLB model loaded on {device}")
    
    translated = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        inputs = tokenizer(batch, return_tensors="pt", padding=True, truncation=True, max_length=512)
        
        if device == 'cuda':
            inputs = {k: v.cuda() for k, v in inputs.items()}
        
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


def translate_with_opus_mt(texts: List[str], src_lang: str, tgt_lang: str, device: str, logger: PipelineLogger, batch_size: int) -> List[str]:
    """Translate using Opus-MT model."""
    from transformers import MarianMTModel, MarianTokenizer
    
    logger.info("Loading Opus-MT model...")
    model_name = f"Helsinki-NLP/opus-mt-{src_lang}-{tgt_lang}"
    
    try:
        tokenizer = MarianTokenizer.from_pretrained(model_name)
        model = MarianMTModel.from_pretrained(model_name)
    except:
        logger.warning(f"Model {model_name} not found, using multilingual model")
        model_name = "Helsinki-NLP/opus-mt-mul-en"
        tokenizer = MarianTokenizer.from_pretrained(model_name)
        model = MarianMTModel.from_pretrained(model_name)
    
    if device == 'cuda':
        model = model.cuda()
    
    logger.info(f"[OK] Opus-MT model loaded on {device}")
    
    translated = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        inputs = tokenizer(batch, return_tensors="pt", padding=True, truncation=True, max_length=512)
        
        if device == 'cuda':
            inputs = {k: v.cuda() for k, v in inputs.items()}
        
        outputs = model.generate(**inputs, max_length=512, num_beams=5)
        batch_translations = tokenizer.batch_decode(outputs, skip_special_tokens=True)
        translated.extend(batch_translations)
        
        if (i + batch_size) % (batch_size * 5) == 0:
            logger.debug(f"Translated {len(translated)}/{len(texts)} segments")
    
    return translated


def translate_with_mbart(texts: List[str], src_lang: str, tgt_lang: str, device: str, logger: PipelineLogger, batch_size: int) -> List[str]:
    """Translate using mBART model."""
    from transformers import MBartForConditionalGeneration, MBart50TokenizerFast
    
    logger.info("Loading mBART model...")
    model_name = "facebook/mbart-large-50-many-to-many-mmt"
    tokenizer = MBart50TokenizerFast.from_pretrained(model_name)
    model = MBartForConditionalGeneration.from_pretrained(model_name)
    
    lang_map = {'hi': 'hi_IN', 'en': 'en_XX', 'es': 'es_XX', 'fr': 'fr_XX', 'de': 'de_DE'}
    src_lang_code = lang_map.get(src_lang, 'hi_IN')
    tgt_lang_code = lang_map.get(tgt_lang, 'en_XX')
    
    if device == 'cuda':
        model = model.cuda()
    
    logger.info(f"[OK] mBART model loaded on {device}")
    
    tokenizer.src_lang = src_lang_code
    translated = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        inputs = tokenizer(batch, return_tensors="pt", padding=True, truncation=True, max_length=512)
        
        if device == 'cuda':
            inputs = {k: v.cuda() for k, v in inputs.items()}
        
        forced_bos_token_id = tokenizer.lang_code_to_id[tgt_lang_code]
        outputs = model.generate(**inputs, forced_bos_token_id=forced_bos_token_id, max_length=512, num_beams=5)
        
        batch_translations = tokenizer.batch_decode(outputs, skip_special_tokens=True)
        translated.extend(batch_translations)
        
        if (i + batch_size) % (batch_size * 5) == 0:
            logger.debug(f"Translated {len(translated)}/{len(texts)} segments")
    
    return translated


def main():
    if len(sys.argv) < 2:
        print("Usage: second_pass_translation.py <movie_dir>")
        sys.exit(1)
    
    movie_dir = Path(sys.argv[1])
    
    from config import load_config
    config = load_config()
    
    log_level = config.log_level.upper() if hasattr(config, 'log_level') else "INFO"
    logger = PipelineLogger("second_pass_translation", log_level=log_level)
    logger.info(f"Starting second-pass translation for: {movie_dir}")
    
    # Check if enabled
    enabled = config.get('second_pass_enabled', False)
    if not enabled:
        logger.info("Second pass translation disabled in config")
        sys.exit(0)
    
    # Check task type
    task = config.get('whisper_task', 'translate')
    if task != 'translate':
        logger.info(f"Task is '{task}', second pass only works with 'translate'")
        sys.exit(0)
    
    # Get config
    backend = config.get('second_pass_backend', 'nllb')
    src_lang = config.get('whisper_language', 'hi')
    tgt_lang = config.get('target_language', 'en')
    device = config.get('device', 'cpu')
    batch_size = config.get('whisper_batch_size', 16)
    
    logger.info(f"Backend: {backend}")
    logger.info(f"Languages: {src_lang} -> {tgt_lang}")
    logger.info(f"Device: {device}")
    
    try:
        # Load ASR result
        asr_result = load_asr_result(movie_dir, logger)
        segments = asr_result.get('segments', [])
        
        # Extract texts
        texts = [seg.get('text', '').strip() for seg in segments if seg.get('text', '').strip()]
        
        if not texts:
            logger.warning("No text to translate")
            sys.exit(0)
        
        logger.info(f"Translating {len(texts)} segments...")
        
        # Translate based on backend
        if backend == 'nllb':
            translated = translate_with_nllb(texts, src_lang, tgt_lang, device, logger, batch_size)
        elif backend == 'opus-mt':
            translated = translate_with_opus_mt(texts, src_lang, tgt_lang, device, logger, batch_size)
        elif backend == 'mbart':
            translated = translate_with_mbart(texts, src_lang, tgt_lang, device, logger, batch_size)
        else:
            logger.error(f"Unknown backend: {backend}")
            sys.exit(1)
        
        # Update segments
        text_idx = 0
        for seg in segments:
            if seg.get('text', '').strip():
                seg['text_original'] = seg['text']
                seg['text'] = translated[text_idx]
                seg['translation_method'] = f'second_pass_{backend}'
                text_idx += 1
        
        asr_result['segments'] = segments
        asr_result['second_pass_enabled'] = True
        asr_result['second_pass_backend'] = backend
        
        # Save enhanced result
        asr_file = movie_dir / "asr" / f"{movie_dir.name}.asr.json"
        with open(asr_file, 'w') as f:
            json.dump(asr_result, f, indent=2, ensure_ascii=False)
        
        logger.info(f"[OK] Enhanced {len(translated)} segments")
        logger.info(f"Saved: {asr_file}")
        
    except Exception as e:
        logger.error(f"Second pass translation failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == '__main__':
    main()
