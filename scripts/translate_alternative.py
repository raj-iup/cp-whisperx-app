#!/usr/bin/env python3
"""
Alternative Translation Script
Translates Hindi segments to English using IndicTrans2 as alternative to NLLB
"""
import sys
import json
import os
from pathlib import Path
import logging

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def setup_logging():
    """Setup logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='[%(levelname)s] %(message)s'
    )
    return logging.getLogger(__name__)

def load_segments(segments_file: Path):
    """Load original Hindi segments"""
    with open(segments_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['segments']

def translate_with_indictrans2(segments, logger):
    """Translate segments using IndicTrans2"""
    from IndicTransToolkit import IndicProcessor
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    
    logger.info("Loading IndicTrans2 model (Indic→English)...")
    
    model_name = "ai4bharat/indictrans2-indic-en-1B"
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name, trust_remote_code=True)
    
    # Move to device - IndicTrans2 works better on CPU for now
    import torch
    device = torch.device("cpu")
    logger.info("Using CPU (IndicTrans2 optimized for CPU)")
    
    model.to(device)
    
    ip = IndicProcessor(inference=True)
    
    logger.info(f"Translating {len(segments)} segments from Hindi to English...")
    
    translated_segments = []
    for i, segment in enumerate(segments):
        text = segment['text'].strip()
        
        if not text:
            translated_segments.append({
                **segment,
                'translation': ''
            })
            continue
        
        # Prepare for IndicTrans2
        batch = ip.preprocess_batch([text], src_lang="hin_Deva", tgt_lang="eng_Latn")
        
        # Tokenize
        inputs = tokenizer(
            batch,
            truncation=True,
            padding="longest",
            return_tensors="pt",
            return_attention_mask=True,
        ).to(device)
        
        # Generate translation
        with torch.no_grad():
            generated_tokens = model.generate(
                **inputs,
                use_cache=False,  # Disable cache to avoid issues
                min_length=0,
                max_length=256,
                num_beams=5,
                num_return_sequences=1,
            )
        
        # Decode
        with tokenizer.as_target_tokenizer():
            generated_tokens = tokenizer.batch_decode(
                generated_tokens.detach().cpu().tolist(),
                skip_special_tokens=True,
                clean_up_tokenization_spaces=True,
            )
        
        # Postprocess
        translations = ip.postprocess_batch(generated_tokens, lang="eng_Latn")
        translation = translations[0] if translations else text
        
        translated_segments.append({
            **segment,
            'translation': translation
        })
        
        if (i + 1) % 10 == 0:
            logger.info(f"  Translated {i + 1}/{len(segments)} segments")
    
    logger.info(f"✓ Translation complete: {len(translated_segments)} segments")
    return translated_segments

def create_srt(segments, output_file: Path, logger):
    """Create SRT subtitle file"""
    import srt
    from datetime import timedelta
    
    subtitles = []
    for i, segment in enumerate(segments, 1):
        translation = segment.get('translation', segment.get('text', ''))
        if not translation.strip():
            continue
        
        start_time = timedelta(seconds=segment['start'])
        end_time = timedelta(seconds=segment['end'])
        
        subtitle = srt.Subtitle(
            index=i,
            start=start_time,
            end=end_time,
            content=translation
        )
        subtitles.append(subtitle)
    
    # Write SRT file
    srt_content = srt.compose(subtitles)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(srt_content)
    
    logger.info(f"✓ Created SRT file: {output_file}")
    logger.info(f"  Total subtitles: {len(subtitles)}")

def main():
    logger = setup_logging()
    
    # Get job directory from argument or use latest
    if len(sys.argv) > 1:
        job_dir = Path(sys.argv[1])
    else:
        logger.error("Usage: python translate_alternative.py <job_directory>")
        logger.error("Example: python translate_alternative.py out/2025/11/23/rpatel/4")
        sys.exit(1)
    
    if not job_dir.exists():
        logger.error(f"Job directory not found: {job_dir}")
        sys.exit(1)
    
    logger.info("=" * 70)
    logger.info("ALTERNATIVE TRANSLATION: Hindi → English (IndicTrans2)")
    logger.info("=" * 70)
    logger.info(f"Job directory: {job_dir}")
    
    # Load original segments
    segments_file = job_dir / "transcripts" / "segments.json"
    if not segments_file.exists():
        logger.error(f"Segments file not found: {segments_file}")
        sys.exit(1)
    
    logger.info(f"Loading segments from: {segments_file}")
    segments = load_segments(segments_file)
    logger.info(f"Loaded {len(segments)} segments")
    
    # Translate using IndicTrans2
    translated_segments = translate_with_indictrans2(segments, logger)
    
    # Save translated segments
    output_json = job_dir / "transcripts" / "segments_translated_en_indictrans2.json"
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump({'segments': translated_segments}, f, indent=2, ensure_ascii=False)
    logger.info(f"✓ Saved translated segments: {output_json}")
    
    # Create SRT file
    subtitles_dir = job_dir / "subtitles"
    subtitles_dir.mkdir(exist_ok=True)
    
    # Get original movie name
    srt_files = list(subtitles_dir.glob("*.hi.srt"))
    if srt_files:
        base_name = srt_files[0].stem.replace('.hi', '')
        output_srt = subtitles_dir / f"{base_name}.en.indictrans2.srt"
    else:
        output_srt = subtitles_dir / "movie.en.indictrans2.srt"
    
    create_srt(translated_segments, output_srt, logger)
    
    logger.info("")
    logger.info("=" * 70)
    logger.info("✅ ALTERNATIVE TRANSLATION COMPLETE")
    logger.info("=" * 70)
    logger.info("")
    logger.info("Output files:")
    logger.info(f"  JSON: {output_json}")
    logger.info(f"  SRT:  {output_srt}")
    logger.info("")
    logger.info("Compare with NLLB translation:")
    existing_srt = subtitles_dir / f"{base_name}.en.srt" if srt_files else None
    if existing_srt and existing_srt.exists():
        logger.info(f"  NLLB:        {existing_srt}")
        logger.info(f"  IndicTrans2: {output_srt}")

if __name__ == "__main__":
    main()
