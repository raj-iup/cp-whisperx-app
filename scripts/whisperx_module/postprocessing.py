"""
postprocessing.py - Result filtering and output formatting

Handles:
- Low confidence segment filtering
- Result saving in multiple formats
- SRT subtitle generation
- Time formatting

Extracted from whisperx_integration.py (Phase 5 - AD-002)
Status: ✅ Complete
"""

# Standard library
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Local
from shared.logger import get_logger


class ResultProcessor:
    """Process and format transcription results"""
    
    def __init__(self, logger: Any):
        """
        Initialize result processor
        
        Args:
            logger: Logger instance
        """
        self.logger = logger
    
    def filter_low_confidence_segments(
        self,
        segments: List[Dict[str, Any]],
        min_logprob: float = -0.7,
        min_duration: float = 0.1
    ) -> List[Dict[str, Any]]:
        """
        Filter out low-confidence and zero-duration segments (Phase 1 optimization).

        This implements confidence-based filtering to remove:
        - Segments with low average log probability (likely hallucinations)
        - Zero-duration or very short segments (timing errors)
        - Empty text segments

        Args:
            segments: List of transcription segments
            min_logprob: Minimum average log probability (-0.7 recommended)
            min_duration: Minimum segment duration in seconds (0.1s recommended)

        Returns:
            Filtered segments list
        """
        if not segments:
            return segments

        filtered = []
        removed_count = 0
        removed_by_confidence = 0
        removed_by_duration = 0
        removed_by_empty = 0

        for seg in segments:
            # Check for empty text
            text = seg.get('text', '').strip()
            if not text:
                removed_by_empty += 1
                removed_count += 1
                continue

            # Check confidence (avg_logprob)
            avg_logprob = seg.get('avg_logprob', 0)
            if avg_logprob < min_logprob:
                removed_by_confidence += 1
                removed_count += 1
                self.logger.debug(f"  Filtered low confidence ({avg_logprob:.2f}): {text[:50]}")
                continue

            # Check duration
            start = seg.get('start', 0)
            end = seg.get('end', 0)
            duration = end - start

            if duration < min_duration:
                removed_by_duration += 1
                removed_count += 1
                self.logger.debug(f"  Filtered short duration ({duration:.3f}s): {text[:50]}")
                continue

            # Passed all filters
            filtered.append(seg)

        # Log filtering statistics
        if removed_count > 0:
            self.logger.info(f"  📊 Confidence filtering: Removed {removed_count}/{len(segments)} segments")
            self.logger.info(f"     - By confidence: {removed_by_confidence}")
            self.logger.info(f"     - By duration: {removed_by_duration}")
            self.logger.info(f"     - By empty text: {removed_by_empty}")
        else:
            self.logger.debug(f"  Confidence filtering: All {len(segments)} segments passed")

        return filtered
    
    def save_results(
        self,
        result: Dict[str, Any],
        output_dir: Path,
        basename: str,
        target_lang: Optional[str] = None
    ) -> Dict[str, Path]:
        """
        Save WhisperX results to output directory

        Args:
            result: WhisperX result
            output_dir: Output directory (e.g., out/Movie/asr/)
            basename: Base filename
            target_lang: Target language for filename suffix (e.g., "en" -> "basename-English.srt")
            
        Returns:
            Dictionary mapping format names to file paths
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        saved_files = {}
        
        # Language code to name mapping for readable filenames
        lang_names = {
            'en': 'English', 'es': 'Spanish', 'fr': 'French', 'de': 'German',
            'it': 'Italian', 'pt': 'Portuguese', 'ru': 'Russian', 'ja': 'Japanese',
            'ko': 'Korean', 'zh': 'Chinese', 'ar': 'Arabic', 'hi': 'Hindi',
            'ta': 'Tamil', 'te': 'Telugu', 'bn': 'Bengali', 'ur': 'Urdu'
        }
        
        # Create language suffix for filenames if target_lang is provided
        lang_suffix = ""
        if target_lang and target_lang != 'auto':
            lang_name = lang_names.get(target_lang, target_lang.lower())
            lang_suffix = f"_{lang_name}"

        # Save full JSON result with basename
        # Pattern: {stage}_{lang}_whisperx.json or {stage}_whisperx.json
        json_file = output_dir / f"{basename}{lang_suffix}_whisperx.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        self.logger.info(f"  Saved: {json_file}")
        saved_files['whisperx_json'] = json_file

        # Save segments as JSON (cleaner format) with basename
        # Pattern: {stage}_{lang}_segments.json or {stage}_segments.json
        segments_file = output_dir / f"{basename}{lang_suffix}_segments.json"
        segments = result.get("segments", [])
        with open(segments_file, "w", encoding="utf-8") as f:
            json.dump(segments, f, indent=2, ensure_ascii=False)
        self.logger.info(f"  Saved: {segments_file}")
        saved_files['segments_json'] = segments_file

        # Save as plain text transcript with basename
        # Pattern: {stage}_{lang}_transcript.txt or {stage}_transcript.txt
        txt_file = output_dir / f"{basename}{lang_suffix}_transcript.txt"
        with open(txt_file, "w", encoding="utf-8") as f:
            for segment in segments:
                text = segment.get("text", "").strip()
                if text:
                    f.write(f"{text}\n")
        self.logger.info(f"  Saved: {txt_file}")
        saved_files['transcript_txt'] = txt_file

        # Save as SRT with basename
        # Pattern: {stage}_{lang}_subtitles.srt or {stage}_subtitles.srt
        srt_file = output_dir / f"{basename}{lang_suffix}_subtitles.srt"
        self._save_as_srt(segments, srt_file)
        self.logger.info(f"  Saved: {srt_file}")
        saved_files['subtitles_srt'] = srt_file
        
        # Save primary files with proper stage naming (Task #5)
        # Pattern: {stage}_transcript.json and {stage}_segments.json
        primary_json = output_dir / f"{basename}_transcript.json"
        with open(primary_json, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())  # Ensure data is written to disk
        self.logger.info(f"  Saved: {primary_json}")
        saved_files['primary_transcript_json'] = primary_json
        
        primary_segments = output_dir / f"{basename}_segments.json"
        with open(primary_segments, "w", encoding="utf-8") as f:
            json.dump(segments, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())  # Ensure data is written to disk
        self.logger.info(f"  Saved: {primary_segments}")
        saved_files['primary_segments_json'] = primary_segments
        
        # Also save with legacy names for backward compatibility
        legacy_json = output_dir / "transcript.json"
        with open(legacy_json, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        saved_files['legacy_transcript_json'] = legacy_json
        
        legacy_segments = output_dir / "segments.json"
        with open(legacy_segments, "w", encoding="utf-8") as f:
            json.dump(segments, f, indent=2, ensure_ascii=False)
        saved_files['legacy_segments_json'] = legacy_segments
        
        return saved_files

    def _save_as_srt(self, segments: List[Dict], srt_file: Path) -> None:
        """
        Save segments as SRT subtitle file

        Args:
            segments: List of WhisperX segments
            srt_file: Output SRT file path
        """
        with open(srt_file, "w", encoding="utf-8") as f:
            for i, segment in enumerate(segments, 1):
                start = segment.get("start", 0)
                end = segment.get("end", start + 1)
                text = segment.get("text", "").strip()

                if not text:
                    continue

                # Format timestamps as HH:MM:SS,mmm
                start_time = self._format_srt_time(start)
                end_time = self._format_srt_time(end)

                f.write(f"{i}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{text}\n")
                f.write("\n")

    def _format_srt_time(self, seconds: float) -> str:
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


__all__ = ['ResultProcessor']
