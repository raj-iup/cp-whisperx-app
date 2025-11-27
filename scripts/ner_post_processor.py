#!/usr/bin/env python3
"""
NER Post-Processor - Phase 1 Integration

Applies Named Entity Recognition correction to transcripts and translations
using TMDB metadata as reference.

Stage: Post-processing stage (runs after ASR/translation)

Input:
  - Transcripts (JSON/SRT files)
  - TMDB enrichment data
  
Output:
  - Corrected transcripts with entity validation
  - Entity statistics and validation report

Usage:
  python scripts/ner_post_processor.py \
      --job-dir out/20250124_0001_movie \
      --input transcript.json \
      --output transcript_corrected.json
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.logger import PipelineLogger
from shared.ner_corrector import NERCorrector
from shared.tmdb_loader import TMDBLoader


class NERPostProcessor:
    """NER-based post-processing for transcripts"""
    
    def __init__(
        self,
        job_dir: Path,
        logger: Optional[PipelineLogger] = None
    ):
        """
        Initialize NER post-processor
        
        Args:
            job_dir: Job output directory
            logger: Logger instance
        """
        self.job_dir = Path(job_dir)
        self.logger = logger or self._create_logger()
        
        # Load TMDB metadata
        self.tmdb_loader = TMDBLoader(self.job_dir, logger=self.logger)
        self.tmdb_data = self.tmdb_loader.load()
        
        # Initialize NER corrector
        if self.tmdb_data.found:
            metadata = self.tmdb_loader.get_metadata()
            self.corrector = NERCorrector(
                tmdb_metadata=metadata,
                model_name="en_core_web_sm",
                logger=self.logger
            )
            try:
                self.corrector.load_model()
                self.enabled = True
            except Exception as e:
                self.logger.warning(f"Failed to load NER model: {e}")
                self.enabled = False
        else:
            self.logger.info("No TMDB metadata available - NER correction disabled")
            self.corrector = None
            self.enabled = False
    
    def _create_logger(self) -> PipelineLogger:
        """Create default logger"""
        return PipelineLogger(
            module_name="ner_post_processor",
            log_file=self.job_dir / "logs" / "ner_post_processing.log"
        )
    
    def process_transcript(
        self,
        input_file: Path,
        output_file: Path,
        format: str = "json"
    ) -> bool:
        """
        Process transcript with NER correction
        
        Args:
            input_file: Input transcript file
            output_file: Output corrected transcript file
            format: File format (json or srt)
        
        Returns:
            True if successful
        """
        self.logger.info("=" * 60)
        self.logger.info("NER Post-Processing")
        self.logger.info("=" * 60)
        self.logger.info(f"Input:  {input_file.name}")
        self.logger.info(f"Output: {output_file.name}")
        
        if not self.enabled:
            self.logger.info("NER correction disabled - copying input to output")
            if input_file != output_file:
                import shutil
                shutil.copy2(input_file, output_file)
            return True
        
        try:
            if format == "json":
                return self._process_json_transcript(input_file, output_file)
            elif format == "srt":
                return self._process_srt_transcript(input_file, output_file)
            else:
                self.logger.error(f"Unsupported format: {format}")
                return False
                
        except Exception as e:
            self.logger.error(f"NER post-processing failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _process_json_transcript(
        self,
        input_file: Path,
        output_file: Path
    ) -> bool:
        """Process JSON transcript"""
        # Load transcript
        with open(input_file, 'r', encoding='utf-8') as f:
            transcript = json.load(f)
        
        corrections_made = 0
        entities_found = 0
        
        # Process segments
        if 'segments' in transcript:
            self.logger.info(f"Processing {len(transcript['segments'])} segments...")
            
            for i, segment in enumerate(transcript['segments']):
                if 'text' not in segment:
                    continue
                
                original_text = segment['text']
                
                # Extract entities
                entities = self.corrector.extract_entities(original_text)
                entities_found += len(entities)
                
                # Apply corrections
                corrected_text = self.corrector.correct_text(original_text)
                
                if corrected_text != original_text:
                    segment['text'] = corrected_text
                    segment['ner_corrected'] = True
                    corrections_made += 1
                    
                    self.logger.debug(f"Segment {i}:")
                    self.logger.debug(f"  Original:  {original_text}")
                    self.logger.debug(f"  Corrected: {corrected_text}")
            
            # Add processing metadata
            transcript['ner_processing'] = {
                'enabled': True,
                'corrections_made': corrections_made,
                'entities_found': entities_found,
                'processed_at': datetime.now().isoformat()
            }
        
        # Save corrected transcript
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(transcript, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"✓ Processed {len(transcript.get('segments', []))} segments")
        self.logger.info(f"  Entities found: {entities_found}")
        self.logger.info(f"  Corrections made: {corrections_made}")
        
        return True
    
    def _process_srt_transcript(
        self,
        input_file: Path,
        output_file: Path
    ) -> bool:
        """Process SRT subtitle file"""
        # Read SRT file
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse SRT entries
        entries = self._parse_srt(content)
        
        self.logger.info(f"Processing {len(entries)} SRT entries...")
        
        corrections_made = 0
        entities_found = 0
        
        for entry in entries:
            if 'text' not in entry:
                continue
            
            original_text = entry['text']
            
            # Extract entities
            entities = self.corrector.extract_entities(original_text)
            entities_found += len(entities)
            
            # Apply corrections
            corrected_text = self.corrector.correct_text(original_text)
            
            if corrected_text != original_text:
                entry['text'] = corrected_text
                corrections_made += 1
        
        # Write corrected SRT
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(self._format_srt(entries))
        
        self.logger.info(f"✓ Processed {len(entries)} entries")
        self.logger.info(f"  Entities found: {entities_found}")
        self.logger.info(f"  Corrections made: {corrections_made}")
        
        return True
    
    def _parse_srt(self, content: str) -> List[Dict]:
        """Parse SRT content into entries"""
        entries = []
        blocks = content.strip().split('\n\n')
        
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) < 3:
                continue
            
            try:
                index = int(lines[0])
                timecode = lines[1]
                text = '\n'.join(lines[2:])
                
                entries.append({
                    'index': index,
                    'timecode': timecode,
                    'text': text
                })
            except (ValueError, IndexError):
                continue
        
        return entries
    
    def _format_srt(self, entries: List[Dict]) -> str:
        """Format entries back to SRT"""
        blocks = []
        
        for entry in entries:
            block = f"{entry['index']}\n{entry['timecode']}\n{entry['text']}"
            blocks.append(block)
        
        return '\n\n'.join(blocks) + '\n'
    
    def validate_entities(
        self,
        input_file: Path,
        output_file: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Validate entities in transcript
        
        Args:
            input_file: Input transcript file
            output_file: Optional output validation report file
        
        Returns:
            Validation results dict
        """
        if not self.enabled:
            return {'enabled': False}
        
        self.logger.info("Validating entities...")
        
        # Load transcript
        with open(input_file, 'r', encoding='utf-8') as f:
            if input_file.suffix == '.json':
                transcript = json.load(f)
                texts = [seg['text'] for seg in transcript.get('segments', []) if 'text' in seg]
            else:
                content = f.read()
                entries = self._parse_srt(content)
                texts = [e['text'] for e in entries]
        
        # Combine all text
        full_text = ' '.join(texts)
        
        # Validate entities
        validations = self.corrector.validate_entities(full_text)
        
        # Get statistics
        stats = self.corrector.get_entity_statistics(full_text)
        
        results = {
            'enabled': True,
            'total_entities': len(validations),
            'needs_correction': sum(1 for v in validations if v['needs_correction']),
            'entity_types': stats,
            'validations': validations,
            'validated_at': datetime.now().isoformat()
        }
        
        # Save report if requested
        if output_file:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            self.logger.info(f"✓ Validation report saved: {output_file.name}")
        
        self.logger.info(f"✓ Found {results['total_entities']} entities")
        self.logger.info(f"  Needs correction: {results['needs_correction']}")
        
        return results


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='NER Post-Processor - Apply entity corrections to transcripts'
    )
    
    parser.add_argument(
        '--job-dir',
        type=Path,
        required=True,
        help='Job output directory'
    )
    
    parser.add_argument(
        '--input',
        type=Path,
        required=True,
        help='Input transcript file (JSON or SRT)'
    )
    
    parser.add_argument(
        '--output',
        type=Path,
        required=True,
        help='Output corrected transcript file'
    )
    
    parser.add_argument(
        '--format',
        choices=['json', 'srt'],
        default='json',
        help='Transcript format (default: json)'
    )
    
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Run entity validation and generate report'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    args = parser.parse_args()
    
    # Create processor
    processor = NERPostProcessor(job_dir=args.job_dir)
    
    # Process transcript
    success = processor.process_transcript(
        input_file=args.input,
        output_file=args.output,
        format=args.format
    )
    
    # Run validation if requested
    if args.validate and success:
        validation_file = args.output.parent / f"{args.output.stem}_validation.json"
        processor.validate_entities(
            input_file=args.output,
            output_file=validation_file
        )
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
