#!/usr/bin/env python3
"""
WhisperX Direct Translation Comparator

Generates English subtitles using WhisperX large-v3 model's built-in translation
for comparison with post-transcription translation methods (NLLB, IndICTrans2).

WhisperX Translation Advantages:
- Context-aware: Sees full audio context during translation
- Timing-aware: Can use prosody and speech patterns
- Integrated: Single-pass transcription + translation
- Large-v3: Latest Whisper model with improved multilingual support

Use this to compare against:
- NLLB: Text-only translation (no audio context)
- IndICTrans2: Text-only translation (Indic language specialist)
- Google Translate: Text-only translation (general purpose)
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.logger import PipelineLogger
from shared.environment_manager import EnvironmentManager


def load_job_config(job_dir: Path) -> Dict:
    """Load job configuration"""
    config_file = job_dir / "job.json"
    if not config_file.exists():
        raise FileNotFoundError(f"Job config not found: {config_file}")
    
    with open(config_file, 'r') as f:
        return json.load(f)


def generate_whisperx_translation(
    job_dir: Path,
    audio_file: Path,
    source_lang: str,
    target_lang: str,
    logger
) -> bool:
    """
    Generate English subtitles using WhisperX direct translation
    
    Args:
        job_dir: Job directory
        audio_file: Input audio file
        source_lang: Source language (e.g., "hi")
        target_lang: Target language (e.g., "en")
        logger: Logger instance
    
    Returns:
        True if successful
    """
    logger.info("=" * 70)
    logger.info("WHISPERX DIRECT TRANSLATION (Context-Aware)")
    logger.info("=" * 70)
    logger.info(f"Job directory: {job_dir}")
    logger.info(f"Audio file: {audio_file}")
    logger.info(f"Translation: {source_lang} → {target_lang}")
    logger.info("")
    logger.info("Using WhisperX large-v3 with task='translate'")
    logger.info("This provides context-aware translation from the audio signal")
    logger.info("")
    
    # Get environment manager
    env_manager = EnvironmentManager(PROJECT_ROOT)
    python_exe = env_manager.get_python_executable("whisperx")
    
    logger.info(f"Using WhisperX environment: {python_exe}")
    
    # Output files
    output_dir = job_dir / "transcripts"
    output_dir.mkdir(exist_ok=True)
    segments_file = output_dir / "segments_whisperx_translated.json"
    
    # Create a temporary Python script to run
    temp_script = job_dir / "logs" / "_whisperx_translate_temp.py"
    temp_script.parent.mkdir(exist_ok=True, parents=True)
    
    script_content = f'''
import json
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, r"{PROJECT_ROOT}")
sys.path.insert(0, r"{PROJECT_ROOT / 'scripts'}")

from scripts.whisperx_integration import WhisperXProcessor
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

try:
    # Initialize WhisperX processor
    logger.info("Initializing WhisperX processor...")
    processor = WhisperXProcessor(
        model_name="large-v3",
        device="mps",
        compute_type="float16",
        backend="auto",
        logger=logger
    )

    # Load model
    logger.info("Loading WhisperX large-v3 model...")
    processor.load_model()

    # Load alignment model for target language
    logger.info("Loading alignment model for {target_lang}...")
    processor.load_align_model("{target_lang}")

    # Transcribe with translation task
    logger.info("Running WhisperX with task='translate'...")
    result = processor.transcribe_with_bias(
        audio_file=Path(r"{audio_file}"),
        source_lang="{source_lang}",
        target_lang="{target_lang}",
        bias_windows=None,
        batch_size=16,
        bias_strategy="global",
        workflow_mode="subtitle-gen"
    )

    # Align segments
    logger.info("Aligning translated segments...")
    result = processor.align_segments(result, Path(r"{audio_file}"), "{target_lang}")

    # Save segments
    logger.info("Saving translated segments...")
    output_file = Path(r"{segments_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({{'segments': result['segments']}}, f, indent=2, ensure_ascii=False)

    logger.info(f"✓ Saved: {{output_file}}")
    logger.info(f"✓ Total segments: {{len(result['segments'])}}")
    sys.exit(0)
    
except Exception as e:
    logger.error(f"Error: {{e}}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
'''
    
    with open(temp_script, 'w') as f:
        f.write(script_content)
    
    # Run the script
    import subprocess
    
    cmd = [str(python_exe), str(temp_script)]
    
    try:
        logger.info("Running WhisperX translation...")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=1800  # 30 minutes
        )
        
        logger.info(result.stdout)
        
        if segments_file.exists():
            logger.info(f"✓ Translation segments saved: {segments_file}")
            # Clean up temp script
            temp_script.unlink(missing_ok=True)
            return True
        else:
            logger.error("Translation failed - segments file not created")
            logger.error(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("WhisperX translation timed out (30 minutes)")
        temp_script.unlink(missing_ok=True)
        return False
    except subprocess.CalledProcessError as e:
        logger.error(f"WhisperX translation failed:")
        logger.error(e.stderr)
        temp_script.unlink(missing_ok=True)
        return False


def create_srt_from_segments(
    segments_file: Path,
    output_srt: Path,
    logger
) -> bool:
    """Create SRT file from segments"""
    import srt
    from datetime import timedelta
    
    logger.info(f"Creating SRT from segments: {segments_file}")
    
    try:
        with open(segments_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            segments = data.get('segments', [])
        
        subtitles = []
        for i, segment in enumerate(segments, 1):
            text = segment.get('text', '').strip()
            if not text:
                continue
            
            start_time = timedelta(seconds=segment.get('start', 0))
            end_time = timedelta(seconds=segment.get('end', 0))
            
            subtitle = srt.Subtitle(
                index=i,
                start=start_time,
                end=end_time,
                content=text
            )
            subtitles.append(subtitle)
        
        # Write SRT
        srt_content = srt.compose(subtitles)
        with open(output_srt, 'w', encoding='utf-8') as f:
            f.write(srt_content)
        
        logger.info(f"✓ Created SRT: {output_srt}")
        logger.info(f"  Total subtitles: {len(subtitles)}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create SRT: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Generate comparative English subtitles using WhisperX direct translation'
    )
    parser.add_argument('job_dir', type=Path, help='Job directory')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Setup simple logger
    import logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='[%(levelname)s] %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 70)
    logger.info("WHISPERX CONTEXT-AWARE TRANSLATION COMPARATOR")
    logger.info("=" * 70)
    logger.info(f"Job directory: {args.job_dir}")
    
    if not args.job_dir.exists():
        logger.error(f"Job directory not found: {args.job_dir}")
        sys.exit(1)
    
    # Load job config
    try:
        config = load_job_config(args.job_dir)
    except Exception as e:
        logger.error(f"Failed to load job config: {e}")
        sys.exit(1)
    
    source_lang = config.get("source_language")
    target_languages = config.get("target_languages", [])
    
    if not target_languages:
        logger.error("No target languages configured")
        sys.exit(1)
    
    target_lang = target_languages[0]  # Use first target language
    
    logger.info(f"Source language: {source_lang}")
    logger.info(f"Target language: {target_lang}")
    
    # Find audio file
    media_config = config.get("media_processing", {})
    mode = media_config.get("mode", "full")
    
    media_dir = args.job_dir / "media"
    
    # Look for audio files in common formats
    audio_patterns = [
        "*_clip.wav", "*_clip.mp3", "*_audio.wav", "*_audio.mp3",
        "audio.wav", "audio.mp3", "*.wav", "*.mp3"
    ]
    
    audio_file = None
    for pattern in audio_patterns:
        audio_files = list(media_dir.glob(pattern))
        if audio_files:
            audio_file = audio_files[0]
            break
    
    if not audio_file:
        logger.error(f"No audio file found in {media_dir}")
        sys.exit(1)
    logger.info(f"Audio file: {audio_file}")
    logger.info("")
    
    # Generate WhisperX translation
    success = generate_whisperx_translation(
        job_dir=args.job_dir,
        audio_file=audio_file,
        source_lang=source_lang,
        target_lang=target_lang,
        logger=logger
    )
    
    if not success:
        logger.error("WhisperX translation failed")
        sys.exit(1)
    
    # Create SRT file
    segments_file = args.job_dir / "transcripts" / "segments_whisperx_translated.json"
    
    title = config.get("title", "output")
    output_srt = args.job_dir / "subtitles" / f"{title}.{target_lang}.whisperx.srt"
    
    success = create_srt_from_segments(segments_file, output_srt, logger)
    
    if not success:
        logger.error("SRT creation failed")
        sys.exit(1)
    
    logger.info("")
    logger.info("=" * 70)
    logger.info("✅ WHISPERX TRANSLATION COMPLETE")
    logger.info("=" * 70)
    logger.info("")
    logger.info("Output files:")
    logger.info(f"  JSON: {segments_file}")
    logger.info(f"  SRT:  {output_srt}")
    logger.info("")
    logger.info("Compare with other translations:")
    
    # List other translation files
    subtitles_dir = args.job_dir / "subtitles"
    other_translations = [
        f"{title}.{target_lang}.srt",  # NLLB
        f"{title}.{target_lang}.indictrans2.srt",  # IndICTrans2
        f"{title}.{target_lang}.googletrans.srt",  # Google Translate
    ]
    
    for trans_file in other_translations:
        full_path = subtitles_dir / trans_file
        if full_path.exists():
            logger.info(f"  {trans_file}")
    
    logger.info("")
    logger.info("WhisperX translation uses audio context for improved accuracy")
    logger.info("Compare this with text-only translation methods!")


if __name__ == "__main__":
    main()
