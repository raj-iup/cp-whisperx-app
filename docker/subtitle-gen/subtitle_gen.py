#!/usr/bin/env python3
"""
Subtitle Generation container - Create .srt files

Workflow: Stage 9 (per workflow-arch.txt)
Input: post_ner/*.corrected.json
Output: en_merged/*.srt with speaker-prefixed subtitles
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
    project_root = Path(__file__).resolve().parents[2]  # docker/subtitle-gen -> root
    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(project_root / 'shared'))
else:
    # Docker mode: use /app paths
    sys.path.insert(0, '/app')
    sys.path.insert(0, '/app/shared')

from logger import PipelineLogger
from glossary import HinglishGlossary, load_film_prompt


def format_srt_time(seconds: float) -> str:
    """
    Format seconds as SRT timestamp (HH:MM:SS,mmm)
    
    Args:
        seconds: Time in seconds
    
    Returns:
        Formatted timestamp string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def split_long_lines(text: str, max_line_length: int, max_lines: int) -> str:
    """
    Split long text into multiple lines based on max line length and max lines.
    
    Args:
        text: Text to split
        max_line_length: Maximum characters per line
        max_lines: Maximum number of lines
    
    Returns:
        Text with line breaks inserted
    """
    if len(text) <= max_line_length:
        return text
    
    words = text.split()
    lines = []
    current_line = []
    current_length = 0
    
    for word in words:
        word_length = len(word)
        # +1 for space between words
        if current_length + word_length + (1 if current_line else 0) <= max_line_length:
            current_line.append(word)
            current_length += word_length + (1 if current_length > 0 else 0)
        else:
            # Start new line
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
            current_length = word_length
            
            # Check if we've hit max lines
            if len(lines) >= max_lines:
                break
    
    # Add remaining words to last line
    if current_line and len(lines) < max_lines:
        lines.append(" ".join(current_line))
    
    # Trim to max_lines
    return "\n".join(lines[:max_lines])


def format_speaker_label(speaker: str, speaker_format: str) -> str:
    """
    Format speaker label according to template.
    
    Args:
        speaker: Speaker identifier
        speaker_format: Format template (e.g., "[{speaker}]", "({speaker})", "{speaker}:")
    
    Returns:
        Formatted speaker label
    """
    if not speaker or not speaker_format:
        return ""
    
    return speaker_format.replace("{speaker}", speaker)


def calculate_cps(text: str, duration: float) -> float:
    """
    Calculate characters per second (CPS)
    
    Args:
        text: Subtitle text
        duration: Duration in seconds
    
    Returns:
        CPS value
    """
    char_count = len(text.replace('\n', '').replace('\r', ''))
    return char_count / max(duration, 0.001)


def check_cps_compliance(
    segments: List[Dict],
    cps_target: float = 15.0,
    cps_hard_cap: float = 17.0,
    include_speaker: bool = True,
    speaker_format: str = "[{speaker}]",
    logger=None
) -> Dict:
    """
    Check CPS (Characters Per Second) compliance for all segments
    
    Args:
        segments: List of subtitle segments
        cps_target: Target CPS (warning threshold)
        cps_hard_cap: Hard cap CPS (violation threshold)
        include_speaker: Whether speaker labels are included
        speaker_format: Format for speaker labels
        logger: Logger instance
    
    Returns:
        Dict with violations, warnings, and statistics
    """
    violations = []
    warnings = []
    cps_values = []
    
    for i, seg in enumerate(segments, 1):
        duration = seg.get('end', 0) - seg.get('start', 0)
        if duration <= 0:
            continue
        
        # Build final text as it will appear
        text = seg.get('text', '').strip()
        if not text:
            continue
        
        if seg.get('is_lyric'):
            text = f"♪ {text} ♪"
        elif include_speaker and seg.get('speaker'):
            speaker_label = format_speaker_label(seg['speaker'], speaker_format)
            text = f"{speaker_label} {text}"
        
        cps = calculate_cps(text, duration)
        cps_values.append(cps)
        
        if cps > cps_hard_cap:
            violations.append({
                'index': i,
                'cps': round(cps, 2),
                'duration': round(duration, 2),
                'chars': len(text.replace('\n', '')),
                'text_preview': text[:60] + '...' if len(text) > 60 else text
            })
        elif cps > cps_target:
            warnings.append({
                'index': i,
                'cps': round(cps, 2),
                'duration': round(duration, 2),
                'chars': len(text.replace('\n', ''))
            })
    
    # Calculate statistics
    avg_cps = sum(cps_values) / len(cps_values) if cps_values else 0
    max_cps = max(cps_values) if cps_values else 0
    min_cps = min(cps_values) if cps_values else 0
    
    # Log results
    if logger:
        total = len([s for s in segments if s.get('text')])
        logger.info(f"CPS Analysis:")
        logger.info(f"  Average CPS: {avg_cps:.2f}")
        logger.info(f"  Range: {min_cps:.2f} - {max_cps:.2f}")
        logger.info(f"  Target: {cps_target}, Hard cap: {cps_hard_cap}")
        
        if violations:
            logger.warning(f"⚠ CPS violations (>{cps_hard_cap}): {len(violations)}/{total}")
            for v in violations[:5]:
                logger.warning(f"  #{v['index']}: {v['cps']} CPS ({v['chars']} chars / {v['duration']}s)")
                logger.warning(f"    \"{v['text_preview']}\"")
            if len(violations) > 5:
                logger.warning(f"  ... and {len(violations) - 5} more violations")
        
        if warnings:
            logger.info(f"ℹ CPS warnings (>{cps_target}): {len(warnings)}/{total}")
        
        if not violations and not warnings:
            logger.info(f"✓ All subtitles within CPS limits")
    
    return {
        'violations': violations,
        'warnings': warnings,
        'total': len([s for s in segments if s.get('text')]),
        'avg_cps': round(avg_cps, 2),
        'max_cps': round(max_cps, 2),
        'min_cps': round(min_cps, 2)
    }


def merge_short_subtitles(
    segments: List[Dict],
    max_duration: float = 7.0,
    max_chars: int = 84
) -> List[Dict]:
    """
    Merge consecutive short subtitles from same speaker
    
    Args:
        segments: List of subtitle segments
        max_duration: Maximum duration for merged subtitle (seconds)
        max_chars: Maximum characters per subtitle
    
    Returns:
        Merged segments
    """
    if not segments:
        return []
    
    merged = []
    current = None
    
    for segment in segments:
        text = segment.get("text", "").strip()
        if not text:
            continue
        
        speaker = segment.get("speaker", "")
        start = segment.get("start", 0)
        end = segment.get("end", start + 1)
        
        if current is None:
            # Start new subtitle
            current = {
                "speaker": speaker,
                "start": start,
                "end": end,
                "text": text
            }
        elif (current["speaker"] == speaker and
              end - current["start"] <= max_duration and
              len(current["text"]) + len(text) + 1 <= max_chars):
            # Merge with current
            current["text"] += " " + text
            current["end"] = end
        else:
            # Save current and start new
            merged.append(current)
            current = {
                "speaker": speaker,
                "start": start,
                "end": end,
                "text": text
            }
    
    # Add final subtitle
    if current:
        merged.append(current)
    
    return merged


def generate_srt(
    segments: List[Dict],
    output_file: Path,
    include_speaker: bool = True,
    speaker_format: str = "[{speaker}]",
    max_line_length: int = 42,
    max_lines: int = 2,
    logger: PipelineLogger = None
):
    """
    Generate SRT subtitle file from segments
    
    Args:
        segments: List of subtitle segments
        output_file: Output SRT file path
        include_speaker: Include speaker labels in subtitles
        speaker_format: Format template for speaker labels
        max_line_length: Maximum characters per line
        max_lines: Maximum number of lines per subtitle
        logger: Logger instance
    """
    if logger:
        logger.info(f"Generating SRT with {len(segments)} subtitles...")
    
    with open(output_file, "w", encoding="utf-8") as f:
        lyric_count = 0
        for i, segment in enumerate(segments, 1):
            start = segment.get("start", 0)
            end = segment.get("end", start + 1)
            text = segment.get("text", "").strip()
            speaker = segment.get("speaker", "")
            is_lyric = segment.get("is_lyric", False)
            
            if not text:
                continue
            
            if is_lyric:
                lyric_count += 1
            
            # Format timestamps
            start_time = format_srt_time(start)
            end_time = format_srt_time(end)
            
            # Format text based on content type
            if is_lyric:
                # Special formatting for lyrics
                text = f"♪ {text} ♪"
            elif include_speaker and speaker:
                # Add speaker prefix for dialogue
                speaker_label = format_speaker_label(speaker, speaker_format)
                text = f"{speaker_label} {text}"
            
            # Split long lines
            text = split_long_lines(text, max_line_length, max_lines)
            
            # Write SRT entry
            f.write(f"{i}\n")
            f.write(f"{start_time} --> {end_time}\n")
            f.write(f"{text}\n")
            f.write("\n")
    
    if logger:
        logger.info(f"[OK] SRT file generated: {output_file}")
        if lyric_count > 0:
            logger.info(f"  {lyric_count} lyric subtitles with special formatting")


def main():
    if len(sys.argv) < 2:
        print("Usage: subtitle_gen.py <movie_dir>")
        sys.exit(1)
    
    movie_dir = Path(sys.argv[1])
    
    # Load config to get log level
    try:
        from config import load_config
        config = load_config()
        log_level = config.log_level.upper() if hasattr(config, 'log_level') else "INFO"
    except:
        log_level = "INFO"
    
    # Setup logger
    logger = PipelineLogger("subtitle-gen", log_level=log_level)
    logger.info(f"Starting subtitle generation for: {movie_dir}")
    
    # Log config source
    config_path = os.getenv('CONFIG_PATH', '/app/config/.env')
    logger.info(f"Using config: {config_path}")
    
    # Find corrected transcript (Post-NER output - preferred)
    corrected_files = list(movie_dir.glob("post_ner/*.corrected.json"))
    
    # Fallback to ASR if post-ner not available
    # (ASR already has speaker labels from diarization per workflow-arch.txt)
    if not corrected_files:
        # Check if post-ner stage exists (might be running or not yet run)
        post_ner_dir = movie_dir / "post_ner"
        if post_ner_dir.exists():
            logger.info("Post-NER directory exists but no corrected output found - stage may have failed or be in progress")
            logger.info("Checking for ASR transcript as fallback...")
        else:
            logger.info("Post-NER stage not yet run, using ASR transcript")
        
        corrected_files = list(movie_dir.glob("asr/*.asr.json"))
        if corrected_files:
            logger.info(f"Using ASR transcript: {corrected_files[0].name}")
    
    if not corrected_files:
        logger.error("No transcript found")
        sys.exit(1)
    
    input_file = corrected_files[0]
    logger.info(f"Input transcript: {input_file}")
    
    # Load segments
    with open(input_file) as f:
        data = json.load(f)
    
    # Handle different formats
    if isinstance(data, dict):
        segments = data.get("segments", [])
    elif isinstance(data, list):
        segments = data
    else:
        logger.error("Unknown transcript format")
        sys.exit(1)
    
    logger.info(f"Loaded {len(segments)} segments")
    
    # Count segments with speaker labels and lyrics
    segments_with_speaker = sum(1 for seg in segments if seg.get('speaker'))
    segments_with_lyrics = sum(1 for seg in segments if seg.get('is_lyric'))
    
    logger.info(f"  Segments with speaker labels: {segments_with_speaker}")
    logger.info(f"  Segments marked as lyrics: {segments_with_lyrics}")
    
    # Apply glossary if enabled
    glossary_enabled = config.get('glossary_enabled', True)
    if glossary_enabled:
        glossary_path = Path(config.get('glossary_path', 'glossary/hinglish_master.tsv'))
        glossary_strategy = config.get('glossary_strategy', 'adaptive')
        film_prompt_path_str = config.get('film_prompt_path', '')
        frequency_data_path_str = config.get('frequency_data_path', 'glossary/learned/term_frequency.json')
        
        # Handle both Docker and native paths
        if not glossary_path.is_absolute():
            if execution_mode == 'native':
                glossary_path = project_root / glossary_path
            else:
                glossary_path = Path('/app') / glossary_path
        
        # Resolve prompt path
        film_prompt_path = None
        if film_prompt_path_str:
            film_prompt_path = Path(film_prompt_path_str)
            if not film_prompt_path.is_absolute():
                if execution_mode == 'native':
                    film_prompt_path = project_root / film_prompt_path
                else:
                    film_prompt_path = Path('/app') / film_prompt_path
        
        # Resolve frequency data path
        frequency_data_path = None
        if frequency_data_path_str:
            frequency_data_path = Path(frequency_data_path_str)
            if not frequency_data_path.is_absolute():
                if execution_mode == 'native':
                    frequency_data_path = project_root / frequency_data_path
                else:
                    frequency_data_path = Path('/app') / frequency_data_path
        
        if glossary_path.exists():
            logger.info(f"Loading glossary from: {glossary_path}")
            logger.info(f"  Strategy: {glossary_strategy}")
            if film_prompt_path and film_prompt_path.exists():
                logger.info(f"  Movie prompt: {film_prompt_path.name}")
            
            # Initialize glossary with advanced strategies
            glossary = HinglishGlossary(
                glossary_path, 
                logger=logger,
                strategy=glossary_strategy,
                prompt_path=film_prompt_path,
                frequency_data_path=frequency_data_path
            )
            
            # Build context window for each segment
            window_size = 2  # segments before and after
            
            # Apply glossary to all segment texts
            for i, seg in enumerate(segments):
                if 'text' in seg and seg['text']:
                    # Build context window
                    window_texts = []
                    for j in range(max(0, i - window_size), min(len(segments), i + window_size + 1)):
                        if j != i and 'text' in segments[j]:
                            window_texts.append(segments[j]['text'])
                    
                    context = {
                        'window': ' '.join(window_texts),
                        'speaker': seg.get('speaker', ''),
                        'segment_index': i
                    }
                    
                    original_text = seg['text']
                    seg['text'] = glossary.apply(original_text, context=context)
            
            # Log stats
            stats = glossary.get_stats()
            logger.info(f"Glossary applied: {stats['terms_applied']} substitutions")
            logger.info(f"  Total terms in glossary: {stats['total_terms']}")
            logger.info(f"  Strategy used: {stats['strategy']}")
            
            if 'advanced_stats' in stats:
                adv = stats['advanced_stats']
                if adv.get('character_profiles'):
                    logger.info(f"  Character profiles loaded: {adv['character_profiles']}")
                if adv.get('regional_variant'):
                    logger.info(f"  Regional variant: {adv['regional_variant']}")
                if adv.get('frequency_stats'):
                    freq = adv['frequency_stats']
                    logger.info(f"  Frequency learning: {freq.get('total_selections', 0)} selections")
            
            # Save learned data
            if glossary_strategy in ['frequency', 'adaptive', 'ml']:
                learned_dir = movie_dir / "glossary_learned"
                glossary.save_learned_data(learned_dir)
                logger.info(f"  Saved learned data to: {learned_dir}")
        else:
            logger.warning(f"Glossary file not found: {glossary_path}")
            logger.info("Continuing without glossary")
    else:
        logger.info("Glossary disabled (GLOSSARY_ENABLED=false)")
    
    # Get configuration parameters with detailed logging
    subtitle_format = config.get('subtitle_format', 'srt')
    max_line_length = config.get('subtitle_max_line_length', 42)
    max_lines = config.get('subtitle_max_lines', 2)
    include_speaker = config.get('subtitle_include_speaker_labels', True)
    speaker_format = config.get('subtitle_speaker_format', '[{speaker}]')
    word_level = config.get('subtitle_word_level_timestamps', False)
    max_duration = config.get('subtitle_max_duration', 7.0)
    min_duration = config.get('subtitle_min_duration', 1.0)
    merge_subtitles = config.get('subtitle_merge_short', True)
    
    # Calculate max chars (max_line_length * max_lines)
    max_chars = max_line_length * max_lines
    
    logger.info(f"Configuration:")
    logger.info(f"  Format: {subtitle_format} (from SUBTITLE_FORMAT)")
    logger.info(f"  Max line length: {max_line_length} chars (from SUBTITLE_MAX_LINE_LENGTH)")
    logger.info(f"  Max lines: {max_lines} (from SUBTITLE_MAX_LINES)")
    logger.info(f"  Max chars total: {max_chars}")
    logger.info(f"  Include speaker: {include_speaker}")
    logger.info(f"  Speaker format: {speaker_format}")
    logger.info(f"  Word-level timestamps: {word_level}")
    logger.info(f"  Duration limits: {min_duration}s - {max_duration}s")
    logger.info(f"  Merge short subtitles: {merge_subtitles}")
    
    if word_level:
        logger.warning("Word-level timestamps requested but not yet implemented")
    
    # Merge if requested
    if merge_subtitles:
        logger.info("Merging consecutive short subtitles...")
        segments = merge_short_subtitles(
            segments,
            max_duration=max_duration,
            max_chars=max_chars
        )
        logger.info(f"After merging: {len(segments)} subtitles")
    
    # Setup output
    output_dir = movie_dir / "en_merged"
    output_dir.mkdir(exist_ok=True, parents=True)
    
    output_file = output_dir / f"{movie_dir.name}.merged.{subtitle_format}"
    
    # Check CPS compliance before generation
    cps_enforcement = config.get('cps_enforcement', True)
    cps_target = config.get('cps_target', 15.0)
    cps_hard_cap = config.get('cps_hard_cap', 17.0)
    
    if cps_enforcement:
        logger.info(f"Checking CPS compliance (target: {cps_target}, cap: {cps_hard_cap})...")
        cps_stats = check_cps_compliance(
            segments,
            cps_target=cps_target,
            cps_hard_cap=cps_hard_cap,
            include_speaker=include_speaker,
            speaker_format=speaker_format,
            logger=logger
        )
    
    # Generate subtitle file
    try:
        if subtitle_format.lower() == 'srt':
            generate_srt(
                segments,
                output_file,
                include_speaker=include_speaker,
                speaker_format=speaker_format,
                max_line_length=max_line_length,
                max_lines=max_lines,
                logger=logger
            )
        else:
            logger.error(f"Unsupported subtitle format: {subtitle_format}")
            logger.error("Only 'srt' format is currently supported")
            sys.exit(1)
        
        logger.info(f"[OK] Subtitle generation complete")
        logger.info(f"Output: {output_file}")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Subtitle generation failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
