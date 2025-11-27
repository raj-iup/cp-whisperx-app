#!/usr/bin/env python3
"""
Hinglish Word Detector
Analyzes mixed Hindi-English text and marks each word with its detected language.
Creates enhanced SRT with word-level language detection for better Hinglish handling.
"""
import sys
import re
import json
from pathlib import Path
from typing import List, Dict, Tuple
import srt
from datetime import timedelta


def detect_script(text: str) -> str:
    """
    Detect script type of text (Devanagari/Latin/Mixed)
    
    Returns:
        'devanagari': Hindi/Devanagari script
        'latin': English/Latin script
        'mixed': Contains both
        'other': Other scripts
    """
    # Unicode ranges
    devanagari_pattern = re.compile(r'[\u0900-\u097F]+')
    latin_pattern = re.compile(r'[a-zA-Z]+')
    
    has_devanagari = bool(devanagari_pattern.search(text))
    has_latin = bool(latin_pattern.search(text))
    
    if has_devanagari and has_latin:
        return 'mixed'
    elif has_devanagari:
        return 'devanagari'
    elif has_latin:
        return 'latin'
    else:
        return 'other'


def detect_word_language(word: str) -> str:
    """
    Detect language of a single word
    
    Returns:
        'hi': Hindi (Devanagari)
        'en': English (Latin)
        'mixed': Contains both scripts
        'punct': Punctuation/symbols
    """
    word = word.strip()
    if not word:
        return 'punct'
    
    # Check if only punctuation
    if re.match(r'^[\W_]+$', word):
        return 'punct'
    
    script = detect_script(word)
    if script == 'devanagari':
        return 'hi'
    elif script == 'latin':
        return 'en'
    elif script == 'mixed':
        return 'mixed'
    else:
        return 'punct'


def tokenize_hinglish(text: str) -> List[Dict[str, str]]:
    """
    Tokenize Hinglish text into words with language tags
    
    Returns:
        List of dicts with 'word' and 'lang' keys
    """
    # Split by whitespace while preserving punctuation
    words = []
    
    # More sophisticated tokenization that handles punctuation
    tokens = re.findall(r'\S+', text)
    
    for token in tokens:
        # Separate trailing punctuation
        match = re.match(r'^(.+?)([,\.!?;:]+)$', token)
        if match:
            word_part = match.group(1)
            punct_part = match.group(2)
            
            words.append({
                'word': word_part,
                'lang': detect_word_language(word_part)
            })
            words.append({
                'word': punct_part,
                'lang': 'punct'
            })
        else:
            words.append({
                'word': token,
                'lang': detect_word_language(token)
            })
    
    return words


def format_word_with_tag(word_info: Dict[str, str]) -> str:
    """Format word with language tag for display"""
    word = word_info['word']
    lang = word_info['lang']
    
    if lang == 'punct':
        return word
    elif lang == 'hi':
        return f"[HI]{word}[/HI]"
    elif lang == 'en':
        return f"[EN]{word}[/EN]"
    elif lang == 'mixed':
        return f"[MIX]{word}[/MIX]"
    else:
        return word


def create_tagged_srt(input_srt: Path, output_srt: Path, logger):
    """
    Create SRT with word-level language tags
    """
    logger.info(f"Reading SRT file: {input_srt}")
    
    with open(input_srt, 'r', encoding='utf-8') as f:
        subtitles = list(srt.parse(f.read()))
    
    logger.info(f"Processing {len(subtitles)} subtitle entries...")
    
    tagged_subtitles = []
    stats = {'hi': 0, 'en': 0, 'mixed': 0, 'punct': 0, 'total': 0}
    
    for sub in subtitles:
        # Tokenize and detect language for each word
        words = tokenize_hinglish(sub.content)
        
        # Update statistics
        for w in words:
            stats[w['lang']] += 1
            stats['total'] += 1
        
        # Format with tags
        tagged_content = ' '.join([format_word_with_tag(w) for w in words])
        
        # Create new subtitle with tagged content
        tagged_sub = srt.Subtitle(
            index=sub.index,
            start=sub.start,
            end=sub.end,
            content=tagged_content
        )
        tagged_subtitles.append(tagged_sub)
    
    # Write tagged SRT
    logger.info(f"Writing tagged SRT to: {output_srt}")
    with open(output_srt, 'w', encoding='utf-8') as f:
        f.write(srt.compose(tagged_subtitles))
    
    # Report statistics
    logger.info("")
    logger.info("=" * 70)
    logger.info("WORD-LEVEL LANGUAGE DETECTION STATISTICS")
    logger.info("=" * 70)
    logger.info(f"Total words:     {stats['total']}")
    logger.info(f"Hindi words:     {stats['hi']} ({stats['hi']*100/max(stats['total'],1):.1f}%)")
    logger.info(f"English words:   {stats['en']} ({stats['en']*100/max(stats['total'],1):.1f}%)")
    logger.info(f"Mixed words:     {stats['mixed']} ({stats['mixed']*100/max(stats['total'],1):.1f}%)")
    logger.info(f"Punctuation:     {stats['punct']} ({stats['punct']*100/max(stats['total'],1):.1f}%)")
    logger.info("=" * 70)
    
    return stats


def create_analysis_json(input_srt: Path, output_json: Path, logger):
    """
    Create detailed JSON analysis of Hinglish content
    """
    logger.info(f"Creating detailed analysis JSON...")
    
    with open(input_srt, 'r', encoding='utf-8') as f:
        subtitles = list(srt.parse(f.read()))
    
    analysis = {
        'file': str(input_srt),
        'total_subtitles': len(subtitles),
        'subtitles': []
    }
    
    for sub in subtitles:
        words = tokenize_hinglish(sub.content)
        
        subtitle_analysis = {
            'index': sub.index,
            'start': str(sub.start),
            'end': str(sub.end),
            'original_text': sub.content,
            'words': words,
            'languages_detected': list(set([w['lang'] for w in words if w['lang'] != 'punct'])),
            'is_hinglish': any(w['lang'] == 'hi' for w in words) and any(w['lang'] == 'en' for w in words)
        }
        
        analysis['subtitles'].append(subtitle_analysis)
    
    # Write JSON
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved detailed analysis to: {output_json}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Detect and tag word-level languages in Hinglish SRT files'
    )
    parser.add_argument('input_srt', type=Path, help='Input Hindi/Hinglish SRT file')
    parser.add_argument('-o', '--output', type=Path, help='Output tagged SRT file')
    parser.add_argument('-j', '--json', type=Path, help='Output detailed JSON analysis')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Setup logger
    import logging
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format='[%(levelname)s] %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # Add simple info/error methods for compatibility
    if not hasattr(logger, 'info'):
        logger.info = logger.info
    if not hasattr(logger, 'error'):
        logger.error = logger.error
    
    logger.info("=" * 70)
    logger.info("HINGLISH WORD-LEVEL LANGUAGE DETECTOR")
    logger.info("=" * 70)
    logger.info(f"Input SRT: {args.input_srt}")
    
    if not args.input_srt.exists():
        logger.error(f"Input file not found: {args.input_srt}")
        sys.exit(1)
    
    # Determine output paths
    if args.output:
        output_srt = args.output
    else:
        output_srt = args.input_srt.parent / f"{args.input_srt.stem}.tagged.srt"
    
    if args.json:
        output_json = args.json
    else:
        output_json = args.input_srt.parent / f"{args.input_srt.stem}.analysis.json"
    
    logger.info(f"Output tagged SRT: {output_srt}")
    logger.info(f"Output analysis JSON: {output_json}")
    logger.info("")
    
    # Create tagged SRT
    stats = create_tagged_srt(args.input_srt, output_srt, logger)
    
    # Create detailed JSON analysis
    create_analysis_json(args.input_srt, output_json, logger)
    
    logger.info("")
    logger.info("=" * 70)
    logger.info("✅ HINGLISH DETECTION COMPLETE")
    logger.info("=" * 70)
    logger.info(f"Tagged SRT:  {output_srt}")
    logger.info(f"Analysis JSON: {output_json}")
    logger.info("")
    
    # Show sample
    logger.info("Sample output (first 3 entries):")
    logger.info("-" * 70)
    with open(output_srt, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        sample = ''.join(lines[:20])  # First ~3 entries
        print(sample)


if __name__ == "__main__":
    main()
