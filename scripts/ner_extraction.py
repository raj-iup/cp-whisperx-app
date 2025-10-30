"""
ner_extraction.py - Named Entity Recognition using spaCy

Handles:
- Loading spaCy transformer models
- Extracting named entities (PER, ORG, GPE)
- Annotating segments with entity information
- Building entity frequency tables
- Saving NER results
"""

import json
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple
from collections import Counter
import spacy
from tqdm import tqdm

from .logger import PipelineLogger


class NERProcessor:
    """Named Entity Recognition processor"""

    def __init__(
        self,
        model_name: str = "en_core_web_trf",
        device: str = "cpu",
        logger: Optional[PipelineLogger] = None
    ):
        """
        Initialize NER processor

        Args:
            model_name: spaCy model name (e.g., en_core_web_trf)
            device: Device to use (cpu, cuda)
            logger: Logger instance
        """
        self.model_name = model_name
        self.device = device
        self.logger = logger or self._create_default_logger()
        self.nlp = None

    def _create_default_logger(self):
        """Create default logger if none provided"""
        from .logger import PipelineLogger
        return PipelineLogger("ner")

    def load_model(self):
        """Load spaCy NER model"""
        self.logger.info(f"Loading spaCy NER model: {self.model_name}")
        self.logger.info(f"  Device: {self.device}")

        try:
            self.nlp = spacy.load(self.model_name)

            # Configure for GPU if available
            if self.device == "cuda":
                spacy.require_gpu()
            elif self.device == "cpu":
                spacy.require_cpu()

            self.logger.info("  NER model loaded successfully")

        except OSError as e:
            self.logger.error(f"  Model not found: {self.model_name}")
            self.logger.error(f"  Install with: python -m spacy download {self.model_name}")
            raise
        except Exception as e:
            self.logger.error(f"  Failed to load NER model: {e}")
            raise

    def extract_entities_from_text(self, text: str) -> List[Dict]:
        """
        Extract named entities from text

        Args:
            text: Input text

        Returns:
            List of entity dicts with text, label, start, end
        """
        if not self.nlp:
            raise RuntimeError("NER model not loaded. Call load_model() first.")

        if not text or not text.strip():
            return []

        try:
            doc = self.nlp(text)
            entities = []

            for ent in doc.ents:
                # Filter to relevant entity types
                if ent.label_ in ["PERSON", "ORG", "GPE", "LOC", "NORP"]:
                    entities.append({
                        "text": ent.text,
                        "label": ent.label_,
                        "start_char": ent.start_char,
                        "end_char": ent.end_char
                    })

            return entities

        except Exception as e:
            self.logger.warning(f"  Entity extraction failed for text: {text[:50]}... Error: {e}")
            return []

    def annotate_segments(
        self,
        segments: List[Dict],
        batch_size: int = 32
    ) -> List[Dict]:
        """
        Annotate segments with named entity information

        Args:
            segments: Input segments
            batch_size: Batch size for processing

        Returns:
            Segments with entity annotations
        """
        self.logger.info("Annotating segments with named entities...")

        if not self.nlp:
            raise RuntimeError("NER model not loaded. Call load_model() first.")

        annotated_segments = []

        for segment in tqdm(segments, desc="NER Processing"):
            text = segment.get("text", "").strip()

            if not text:
                annotated_segments.append(segment)
                continue

            # Extract entities
            entities = self.extract_entities_from_text(text)

            # Add entities to segment
            annotated_segment = segment.copy()
            annotated_segment["entities"] = entities

            annotated_segments.append(annotated_segment)

        # Count entities
        total_entities = sum(len(seg.get("entities", [])) for seg in annotated_segments)
        self.logger.info(f"  NER annotation complete: {total_entities} entities found")

        return annotated_segments

    def build_entity_frequency_table(
        self,
        segments: List[Dict]
    ) -> Dict[str, Dict[str, int]]:
        """
        Build frequency table of named entities

        Args:
            segments: Annotated segments

        Returns:
            Dict mapping entity labels to Counter of entity texts
        """
        self.logger.info("Building entity frequency table...")

        entity_counts = {
            "PERSON": Counter(),
            "ORG": Counter(),
            "GPE": Counter(),
            "LOC": Counter(),
            "NORP": Counter()
        }

        for segment in segments:
            entities = segment.get("entities", [])
            for entity in entities:
                label = entity.get("label", "")
                text = entity.get("text", "")

                if label in entity_counts:
                    entity_counts[label][text] += 1

        # Convert Counter to dict
        frequency_table = {}
        for label, counter in entity_counts.items():
            if counter:
                frequency_table[label] = dict(counter.most_common())

        # Log summary
        for label, counts in frequency_table.items():
            unique_count = len(counts)
            total_count = sum(counts.values())
            self.logger.info(f"  {label}: {unique_count} unique, {total_count} total")

        return frequency_table

    def extract_canonical_candidates(
        self,
        frequency_table: Dict[str, Dict[str, int]],
        top_k: int = 50
    ) -> Dict[str, List[str]]:
        """
        Extract top-k entities as canonical candidates

        Args:
            frequency_table: Entity frequency table
            top_k: Number of top entities to extract per label

        Returns:
            Dict mapping labels to top-k entity texts
        """
        canonical_candidates = {}

        for label, counts in frequency_table.items():
            # Get top-k
            sorted_entities = sorted(counts.items(), key=lambda x: x[1], reverse=True)
            top_entities = [entity for entity, count in sorted_entities[:top_k]]
            canonical_candidates[label] = top_entities

        return canonical_candidates

    def save_results(
        self,
        segments: List[Dict],
        frequency_table: Dict[str, Dict[str, int]],
        output_dir: Path,
        basename: str
    ):
        """
        Save NER results to output directory

        Args:
            segments: Annotated segments
            frequency_table: Entity frequency table
            output_dir: Output directory
            basename: Base filename
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save annotated segments as JSON
        json_file = output_dir / f"{basename}.ner_annotated.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(segments, f, indent=2, ensure_ascii=False)
        self.logger.info(f"  Saved: {json_file}")

        # Save entity frequency table
        freq_file = output_dir / f"{basename}.entity_frequencies.json"
        with open(freq_file, "w", encoding="utf-8") as f:
            json.dump(frequency_table, f, indent=2, ensure_ascii=False)
        self.logger.info(f"  Saved: {freq_file}")

        # Save as human-readable text
        txt_file = output_dir / f"{basename}.entities.txt"
        with open(txt_file, "w", encoding="utf-8") as f:
            f.write("Named Entity Frequency Report\n")
            f.write("=" * 70 + "\n\n")

            for label, counts in frequency_table.items():
                f.write(f"{label}:\n")
                f.write("-" * 70 + "\n")
                for entity, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
                    f.write(f"  {entity}: {count}\n")
                f.write("\n")

        self.logger.info(f"  Saved: {txt_file}")


def run_ner_pipeline(
    segments: List[Dict],
    output_dir: Path,
    basename: str,
    model_name: str,
    device: str,
    logger: Optional[PipelineLogger] = None
) -> Tuple[List[Dict], Dict[str, Dict[str, int]]]:
    """
    Run complete NER pipeline

    Args:
        segments: Input segments
        output_dir: Output directory
        basename: Base filename
        model_name: spaCy model name
        device: Device to use
        logger: Logger instance

    Returns:
        Tuple of (annotated segments, entity frequency table)
    """
    processor = NERProcessor(
        model_name=model_name,
        device=device,
        logger=logger
    )

    # Load model
    processor.load_model()

    # Annotate segments
    annotated_segments = processor.annotate_segments(segments)

    # Build frequency table
    frequency_table = processor.build_entity_frequency_table(annotated_segments)

    # Save results
    processor.save_results(annotated_segments, frequency_table, output_dir, basename)

    return annotated_segments, frequency_table
