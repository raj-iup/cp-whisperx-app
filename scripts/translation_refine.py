"""
translation_refine.py - Second-pass translation refinement

Handles:
- Loading translation models (opus-mt, mbart50, nllb200)
- Re-translating segments that may have weak translations
- Merging original and refined translations
- Quality scoring and fallback logic
"""

import json
from pathlib import Path
from typing import List, Dict, Optional, Any
import torch
from transformers import (
    MarianMTModel, MarianTokenizer,
    MBartForConditionalGeneration, MBart50TokenizerFast,
    AutoModelForSeq2SeqLM, AutoTokenizer
)
from tqdm import tqdm

import sys
from pathlib import Path

# Add project root to path for shared imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.logger import PipelineLogger

# Local
from shared.logger import get_logger
logger = get_logger(__name__)


class TranslationRefiner:
    """Second-pass translation refiner"""

    def __init__(
        self,
        backend: str = "opus-mt",
        source_lang: str = "hi",
        target_lang: str = "en",
        device: str = "cpu",
        logger: Optional[PipelineLogger] = None
    ):
        """
        Initialize translation refiner

        Args:
            backend: Translation backend (opus-mt, mbart50, nllb200)
            source_lang: Source language code
            target_lang: Target language code
            device: Device to use (cpu, cuda, mps)
            logger: Logger instance
        """
        self.backend = backend
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.device = device
        self.logger = logger or self._create_default_logger()

        self.model = None
        self.tokenizer = None

    def _create_default_logger(self):
        """Create default logger if none provided"""
        from shared.logger import PipelineLogger
        return PipelineLogger("translation")

    def load_model(self):
        """Load translation model based on backend"""
        self.logger.info(f"Loading translation model: {self.backend}")
        self.logger.info(f"  Source: {self.source_lang}, Target: {self.target_lang}")
        self.logger.info(f"  Device: {self.device}")

        try:
            # Normalize backend name (nllb -> nllb200 for backward compatibility)
            backend = self.backend.lower()
            if backend == "nllb":
                backend = "nllb200"
                self.logger.info(f"  Using backend: nllb200 (alias for nllb)")
            
            if backend == "opus-mt":
                self._load_opus_mt()
            elif backend == "mbart50":
                self._load_mbart50()
            elif backend == "nllb200":
                self._load_nllb200()
            else:
                raise ValueError(f"Unknown backend: {self.backend}")

            self.logger.info("  Model loaded successfully")

        except Exception as e:
            self.logger.error(f"  Failed to load model: {e}", exc_info=True)
            raise

    def _load_opus_mt(self):
        """Load Helsinki-NLP OPUS-MT model"""
        # Map language codes to OPUS-MT format
        lang_map = {"hi": "hi", "en": "en"}
        src = lang_map.get(self.source_lang, self.source_lang)
        tgt = lang_map.get(self.target_lang, self.target_lang)

        model_name = f"Helsinki-NLP/opus-mt-{src}-{tgt}"
        self.logger.info(f"  Loading: {model_name}")

        self.tokenizer = MarianTokenizer.from_pretrained(model_name)
        self.model = MarianMTModel.from_pretrained(model_name)
        self.model.to(self.device)
        self.model.eval()

    def _load_mbart50(self):
        """Load Facebook mBART-50 model"""
        model_name = "facebook/mbart-large-50-many-to-many-mmt"
        self.logger.info(f"  Loading: {model_name}")

        self.tokenizer = MBart50TokenizerFast.from_pretrained(model_name)
        self.model = MBartForConditionalGeneration.from_pretrained(model_name)
        self.model.to(self.device)
        self.model.eval()

        # Set source language
        lang_code_map = {"hi": "hi_IN", "en": "en_XX"}
        self.tokenizer.src_lang = lang_code_map.get(self.source_lang, "hi_IN")

    def _load_nllb200(self):
        """Load Meta NLLB-200 model"""
        model_name = "facebook/nllb-200-distilled-600M"
        self.logger.info(f"  Loading: {model_name}")

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        self.model.to(self.device)
        self.model.eval()

    def translate_text(self, text: str) -> str:
        """
        Translate a single text string

        Args:
            text: Source text to translate

        Returns:
            Translated text
        """
        if not text or not text.strip():
            return text

        try:
            # Tokenize
            inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # Generate translation
            with torch.no_grad():
                if self.backend == "mbart50":
                    # mBART requires forced_bos_token_id for target language
                    lang_code_map = {"en": "en_XX", "hi": "hi_IN"}
                    forced_bos_token_id = self.tokenizer.lang_code_to_id.get(
                        lang_code_map.get(self.target_lang, "en_XX")
                    )
                    outputs = self.model.generate(**inputs, forced_bos_token_id=forced_bos_token_id)
                elif self.backend == "nllb200":
                    # NLLB requires forced_bos_token_id for target language
                    lang_code_map = {"en": "eng_Latn", "hi": "hin_Deva"}
                    forced_bos_token_id = self.tokenizer.lang_code_to_id.get(
                        lang_code_map.get(self.target_lang, "eng_Latn")
                    )
                    outputs = self.model.generate(**inputs, forced_bos_token_id=forced_bos_token_id)
                else:
                    # OPUS-MT
                    outputs = self.model.generate(**inputs)

            # Decode
            translated = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            return translated

        except Exception as e:
            self.logger.warning(f"  Translation failed for text: {text[:50]}... Error: {e}")
            return text

    def refine_segments(
        self,
        segments: List[Dict],
        refine_all: bool = False,
        batch_size: int = 8
    ) -> List[Dict]:
        """
        Refine translations for segments

        Args:
            segments: Segments with existing translations
            refine_all: If True, refine all segments. If False, only refine weak ones
            batch_size: Batch size for translation

        Returns:
            Segments with refined translations
        """
        self.logger.info(f"Refining translations (refine_all={refine_all})...")

        if not self.model:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        segments_to_refine = segments if refine_all else self._filter_weak_segments(segments)

        self.logger.info(f"  Refining {len(segments_to_refine)} segments out of {len(segments)} total")

        # Create a map of segment indices to refine
        refine_indices = set()
        if not refine_all:
            for seg_to_refine in segments_to_refine:
                for idx, seg in enumerate(segments):
                    if seg.get("start") == seg_to_refine.get("start") and seg.get("end") == seg_to_refine.get("end"):
                        refine_indices.add(idx)
                        break

        refined_segments = []
        for idx, segment in enumerate(tqdm(segments, desc="Processing")):
            # Check if this segment should be refined
            should_refine = refine_all or idx in refine_indices
            
            if not should_refine:
                # Keep original segment
                refined_segments.append(segment)
                continue
                
            original_text = segment.get("text", "").strip()

            if not original_text:
                refined_segments.append(segment)
                continue

            # Translate
            refined_text = self.translate_text(original_text)

            # Create refined segment
            refined_segment = segment.copy()
            refined_segment["text_original"] = original_text
            refined_segment["text"] = refined_text
            refined_segment["refined"] = True

            refined_segments.append(refined_segment)

        self.logger.info(f"  Refinement complete: {len(refined_segments)} segments total, {len(segments_to_refine)} refined")
        return refined_segments

    def _filter_weak_segments(self, segments: List[Dict]) -> List[Dict]:
        """
        Filter segments that may have weak translations

        Args:
            segments: All segments

        Returns:
            Segments that should be refined
        """
        # Simple heuristics for weak translations:
        # - Very short segments (< 3 words)
        # - Segments with many repeated words
        # - Segments with unusual character patterns

        weak_segments = []
        for segment in segments:
            text = segment.get("text", "").strip()
            if not text:
                continue

            words = text.split()

            # Check if short
            if len(words) < 3:
                weak_segments.append(segment)
                continue

            # Check for repetition
            unique_words = set(words)
            if len(unique_words) < len(words) * 0.5:  # > 50% repetition
                weak_segments.append(segment)
                continue

        return weak_segments

    def merge_with_original(
        self,
        original_segments: List[Dict],
        refined_segments: List[Dict]
    ) -> List[Dict]:
        """
        Merge refined segments with original segments

        Args:
            original_segments: Original segments
            refined_segments: Refined segments

        Returns:
            Merged segments
        """
        self.logger.info("Merging refined segments with original...")

        # Create lookup for refined segments by start time
        refined_lookup = {seg.get("start", 0): seg for seg in refined_segments if seg.get("refined")}

        merged = []
        for orig_seg in original_segments:
            start_time = orig_seg.get("start", 0)

            if start_time in refined_lookup:
                # Use refined version
                merged.append(refined_lookup[start_time])
            else:
                # Keep original
                merged.append(orig_seg)

        self.logger.info(f"  Merge complete: {len(merged)} segments")
        return merged

    def save_results(
        self,
        segments: List[Dict],
        output_dir: Path,
        basename: str
    ):
        """
        Save refined segments to output directory

        Args:
            segments: Refined segments
            output_dir: Output directory
            basename: Base filename
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save refined segments as JSON
        json_file = output_dir / f"{basename}.refined.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(segments, f, indent=2, ensure_ascii=False)
        self.logger.info(f"  Saved: {json_file}")

        # Save as plain text
        txt_file = output_dir / f"{basename}.refined.txt"
        with open(txt_file, "w", encoding="utf-8") as f:
            for segment in segments:
                text = segment.get("text", "").strip()
                if text:
                    f.write(f"{text}\n")
        self.logger.info(f"  Saved: {txt_file}")


def run_translation_refine_pipeline(
    segments: List[Dict],
    output_dir: Path,
    basename: str,
    backend: str,
    source_lang: str,
    target_lang: str,
    device: str,
    refine_all: bool = False,
    logger: Optional[PipelineLogger] = None
) -> List[Dict]:
    """
    Run complete translation refinement pipeline

    Args:
        segments: Input segments to refine
        output_dir: Output directory
        basename: Base filename
        backend: Translation backend
        source_lang: Source language
        target_lang: Target language
        device: Device to use
        refine_all: Whether to refine all segments
        logger: Logger instance

    Returns:
        Refined segments
    """
    refiner = TranslationRefiner(
        backend=backend,
        source_lang=source_lang,
        target_lang=target_lang,
        device=device,
        logger=logger
    )

    # Load model
    refiner.load_model()

    # Refine segments
    refined_segments = refiner.refine_segments(segments, refine_all=refine_all)

    # Save results
    refiner.save_results(refined_segments, output_dir, basename)

    return refined_segments


def main():
    """Main entry point for translation refinement stage."""
    import sys
    import os
    import json
    from pathlib import Path
    from shared.logger import PipelineLogger
    from shared.config import load_config
    from shared.stage_utils import StageIO
    
    # Get output directory and config from environment or command line
    output_dir_env = os.environ.get('OUTPUT_DIR')
    config_path_env = os.environ.get('CONFIG_PATH')
    
    if output_dir_env:
        output_dir = Path(output_dir_env)
    elif len(sys.argv) > 1:
        output_dir = Path(sys.argv[1])
    else:
        logger.info("ERROR: No output directory specified", file=sys.stderr)
        return 1
    
    # Load configuration
    if config_path_env:
        config = load_config(config_path_env)
    else:
        config = None
    
    # Initialize StageIO for proper directory structure
    stage_io = StageIO("second_pass_translation", output_base=output_dir)
    
    # Setup logger with proper log path
    log_file = stage_io.get_log_path()
    logger = PipelineLogger("second_pass_translation", log_file)
    
    logger.info("Running second-pass translation refinement")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Stage directory: {stage_io.stage_dir}")
    
    # Check if second pass is enabled
    second_pass_enabled = getattr(config, 'second_pass_enabled', True) if config else True
    if not second_pass_enabled:
        logger.info("Second-pass translation disabled, skipping")
        return 0
    
    # Load transcript from ASR - check multiple possible locations
    logger.info("Loading ASR transcript...")
    
    asr_file_locations = [
        output_dir / "06_asr" / "transcript.json",  # Standard stage location
        output_dir / "06_asr" / "segments.json",    # Segments file
        output_dir / "07_song_bias_injection" / "segments.json",  # After song bias
        output_dir / "asr" / "transcript.json",     # Legacy location
        output_dir / "07_asr" / "transcript.json",  # Alternate
        output_dir / "05_asr" / "transcript.json"   # Alternate
    ]
    
    segments = None
    asr_file = None
    
    for location in asr_file_locations:
        if location.exists():
            asr_file = location
            logger.info(f"Found ASR output: {asr_file}")
            try:
                with open(asr_file, 'r') as f:
                    asr_data = json.load(f)
                    segments = asr_data.get('segments', []) if isinstance(asr_data, dict) else asr_data
                    
                if segments:
                    logger.info(f"Loaded {len(segments)} segments")
                    break
            except Exception as e:
                logger.warning(f"Failed to load {location}: {e}")
                continue
    
    if not segments:
        logger.warning("ASR output not found in any expected location")
        logger.info("Expected locations:")
        for loc in asr_file_locations:
            logger.info(f"  - {loc}")
        logger.warning("Skipping second-pass translation")
        return 0
    
    # Get configuration parameters
    backend = getattr(config, 'second_pass_backend', 'nllb') if config else 'nllb'
    source_lang = getattr(config, 'whisper_language', 'hi') if config else 'hi'
    target_lang = getattr(config, 'target_language', 'en') if config else 'en'
    device = os.environ.get('DEVICE_OVERRIDE', getattr(config, 'device', 'cpu') if config else 'cpu').lower()
    refine_all = False  # Only refine segments with low confidence
    
    logger.info(f"Backend: {backend}")
    logger.info(f"Source language: {source_lang}")
    logger.info(f"Target language: {target_lang}")
    logger.info(f"Device: {device}")
    logger.info(f"Segments to process: {len(segments)}")
    
    try:
        # Run translation refinement - save to stage directory
        refined_segments = run_translation_refine_pipeline(
            segments=segments,
            output_dir=stage_io.stage_dir,
            basename="refined",
            backend=backend,
            source_lang=source_lang,
            target_lang=target_lang,
            device=device,
            refine_all=refine_all,
            logger=logger
        )
        
        # Save metadata
        metadata = {
            "status": "completed",
            "segments_total": len(segments),
            "segments_refined": len([s for s in refined_segments if s.get("refined")]),
            "backend": backend,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "device": device
        }
        stage_io.save_metadata(metadata)
        
        logger.info(f"✓ Translation refinement completed successfully")
        logger.info(f"  Refined segments: {len(refined_segments)}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Translation refinement failed: {e}", exc_info=True)
        import traceback
        logger.error(traceback.format_exc(, exc_info=True))
        logger.warning("Continuing without translation refinement")
        return 0  # Non-critical, don't fail pipeline


if __name__ == "__main__":
    import sys
    sys.exit(main())
