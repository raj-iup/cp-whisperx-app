"""
canonicalization.py - NER-guided canonicalization and text polish

Handles:
- Loading canonical name mappings from YAML
- Applying canonical replacements to segments
- Punctuation and case polishing
- Final SRT generation with polished text
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Optional
import yaml

import sys
from pathlib import Path

# Add project root to path for shared imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.logger import PipelineLogger


class CanonicalProcessor:
    """Canonicalization and polish processor"""

    def __init__(
        self,
        canon_map_file: Optional[str] = None,
        logger: Optional[PipelineLogger] = None
    ):
        """
        Initialize canonical processor

        Args:
            canon_map_file: Path to canonical mapping YAML file
            logger: Logger instance
        """
        self.canon_map_file = canon_map_file
        self.logger = logger or self._create_default_logger()
        self.canon_map = {}

    def _create_default_logger(self):
        """Create default logger if none provided"""
        from shared.logger import PipelineLogger
        return PipelineLogger("canonicalization")

    def load_canon_map(self):
        """Load canonical name mapping from YAML file"""
        if not self.canon_map_file:
            self.logger.info("No canonical map file specified, skipping...")
            return

        canon_map_path = Path(self.canon_map_file)
        if not canon_map_path.exists():
            self.logger.warning(f"Canonical map file not found: {self.canon_map_file}")
            return

        try:
            with open(canon_map_path, 'r', encoding='utf-8', errors='replace') as f:
                self.canon_map = yaml.safe_load(f) or {}

            # Count mappings
            total_mappings = sum(len(mappings) for mappings in self.canon_map.values())
            self.logger.info(f"Loaded canonical map: {total_mappings} mappings")

            for label in ["PER", "ORG", "GPE", "LOC"]:
                if label in self.canon_map:
                    self.logger.info(f"  {label}: {len(self.canon_map[label])} mappings")

        except Exception as e:
            self.logger.error(f"Failed to load canonical map: {e}")
            self.canon_map = {}

    def apply_canonical_replacements(
        self,
        segments: List[Dict]
    ) -> List[Dict]:
        """
        Apply canonical name replacements to segments

        Args:
            segments: Input segments with NER annotations

        Returns:
            Segments with canonical names applied
        """
        self.logger.info("Applying canonical name replacements...")

        if not self.canon_map:
            self.logger.info("  No canonical map loaded, skipping...")
            return segments

        canonical_segments = []
        replacement_count = 0

        for segment in segments:
            text = segment.get("text", "").strip()
            entities = segment.get("entities", [])

            if not text:
                canonical_segments.append(segment)
                continue

            # Apply replacements based on entities
            new_text = text
            for entity in entities:
                entity_text = entity.get("text", "")
                entity_label = entity.get("label", "")

                # Map label to canon_map key
                label_map = {
                    "PERSON": "PER",
                    "ORG": "ORG",
                    "GPE": "GPE",
                    "LOC": "LOC"
                }
                canon_label = label_map.get(entity_label, entity_label)

                # Check if canonical mapping exists
                if canon_label in self.canon_map:
                    mappings = self.canon_map[canon_label]
                    if entity_text in mappings:
                        canonical_name = mappings[entity_text]
                        # Replace in text (case-insensitive, whole word)
                        pattern = re.compile(re.escape(entity_text), re.IGNORECASE)
                        new_text = pattern.sub(canonical_name, new_text)
                        replacement_count += 1

            # Create canonical segment
            canonical_segment = segment.copy()
            canonical_segment["text_before_canon"] = text
            canonical_segment["text"] = new_text

            canonical_segments.append(canonical_segment)

        self.logger.info(f"  Applied {replacement_count} canonical replacements")
        return canonical_segments

    def polish_punctuation_and_case(
        self,
        segments: List[Dict]
    ) -> List[Dict]:
        """
        Polish punctuation and capitalization

        Args:
            segments: Input segments

        Returns:
            Polished segments
        """
        self.logger.info("Polishing punctuation and case...")

        polished_segments = []

        for segment in segments:
            text = segment.get("text", "").strip()

            if not text:
                polished_segments.append(segment)
                continue

            # Apply polishing rules
            polished_text = self._polish_text(text)

            # Create polished segment
            polished_segment = segment.copy()
            polished_segment["text_before_polish"] = text
            polished_segment["text"] = polished_text

            polished_segments.append(polished_segment)

        self.logger.info("  Polishing complete")
        return polished_segments

    def _polish_text(self, text: str) -> str:
        """
        Apply polishing rules to text

        Args:
            text: Input text

        Returns:
            Polished text
        """
        # Ensure sentence starts with capital letter
        if text and text[0].islower():
            text = text[0].upper() + text[1:]

        # Fix spacing around punctuation
        text = re.sub(r'\s+([,.!?;:])', r'\1', text)  # Remove space before punctuation
        text = re.sub(r'([,.!?;:])([A-Za-z])', r'\1 \2', text)  # Add space after punctuation

        # Fix multiple spaces
        text = re.sub(r'\s+', ' ', text)

        # Fix common patterns
        text = re.sub(r'\bi\b', 'I', text)  # Fix lowercase I
        text = re.sub(r'\bi\'m\b', "I'm", text, flags=re.IGNORECASE)
        text = re.sub(r'\bi\'ll\b', "I'll", text, flags=re.IGNORECASE)
        text = re.sub(r'\bi\'ve\b', "I've", text, flags=re.IGNORECASE)

        # Ensure sentence ends with punctuation
        if text and text[-1] not in '.!?':
            text = text + '.'

        return text.strip()

    def generate_final_srt(
        self,
        segments: List[Dict],
        output_file: Path
    ):
        """
        Generate final polished SRT file

        Args:
            segments: Polished segments
            output_file: Output SRT file path
        """
        self.logger.info(f"Generating final SRT: {output_file}")

        with open(output_file, "w", encoding="utf-8") as f:
            for i, segment in enumerate(segments, 1):
                start = segment.get("start", 0)
                end = segment.get("end", start + 1)
                text = segment.get("text", "").strip()
                speaker = segment.get("speaker", "")

                if not text:
                    continue

                # Format timestamps as HH:MM:SS,mmm
                start_time = self._format_srt_time(start)
                end_time = self._format_srt_time(end)

                # Add speaker prefix if available
                if speaker:
                    text = f"[{speaker}] {text}"

                f.write(f"{i}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{text}\n")
                f.write("\n")

        self.logger.info("  Final SRT generated")

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

    def save_results(
        self,
        segments: List[Dict],
        output_dir: Path,
        basename: str
    ):
        """
        Save canonicalized and polished segments

        Args:
            segments: Processed segments
            output_dir: Output directory
            basename: Base filename
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save as JSON
        json_file = output_dir / f"{basename}.polished.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(segments, f, indent=2, ensure_ascii=False)
        self.logger.info(f"  Saved: {json_file}")

        # Save as plain text
        txt_file = output_dir / f"{basename}.polished.txt"
        with open(txt_file, "w", encoding="utf-8") as f:
            for segment in segments:
                text = segment.get("text", "").strip()
                speaker = segment.get("speaker", "")
                if text:
                    if speaker:
                        f.write(f"[{speaker}] {text}\n")
                    else:
                        f.write(f"{text}\n")
        self.logger.info(f"  Saved: {txt_file}")

        # Generate final SRT
        srt_file = output_dir / f"{basename}.final.srt"
        self.generate_final_srt(segments, srt_file)
        self.logger.info(f"  Saved: {srt_file}")


def run_canonicalization_pipeline(
    segments: List[Dict],
    output_dir: Path,
    basename: str,
    canon_map_file: Optional[str] = None,
    logger: Optional[PipelineLogger] = None
) -> List[Dict]:
    """
    Run complete canonicalization and polish pipeline

    Args:
        segments: Input segments with NER annotations
        output_dir: Output directory
        basename: Base filename
        canon_map_file: Canonical mapping file
        logger: Logger instance

    Returns:
        Polished segments
    """
    processor = CanonicalProcessor(
        canon_map_file=canon_map_file,
        logger=logger
    )

    # Load canonical map
    processor.load_canon_map()

    # Apply canonical replacements
    canonical_segments = processor.apply_canonical_replacements(segments)

    # Polish punctuation and case
    polished_segments = processor.polish_punctuation_and_case(canonical_segments)

    # Save results
    processor.save_results(polished_segments, output_dir, basename)

    return polished_segments
