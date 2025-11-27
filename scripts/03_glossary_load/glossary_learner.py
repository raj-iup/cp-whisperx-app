#!/usr/bin/env python3
"""
Glossary Learner for CP-WhisperX-App

Purpose: Auto-detect character names and terms from transcripts
Input: ASR transcripts, TMDB cast data
Output: Job-specific glossary additions
"""

import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional
from collections import Counter

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.logger import PipelineLogger


class GlossaryLearner:
    """Auto-learn glossary terms from transcripts."""
    
    def __init__(self, logger: Optional[PipelineLogger] = None):
        """Initialize glossary learner.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or PipelineLogger("glossary_learner")
        
        # Common Hindi name patterns
        self.name_patterns = [
            r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b',  # Full names
            r'\b[A-Z][a-z]{2,}\b',  # Single names (min 3 chars)
        ]
        
        # Words to exclude (not names)
        self.exclude_words = {
            'Okay', 'Yeah', 'Yes', 'The', 'But', 'And', 'What',
            'When', 'Where', 'Why', 'How', 'Who', 'This', 'That',
            'Very', 'Much', 'More', 'Most', 'Some', 'All', 'Any',
            'May', 'Can', 'Will', 'Could', 'Would', 'Should',
            'Please', 'Thank', 'Thanks', 'Sorry', 'Hello', 'Bye',
        }
    
    def extract_potential_names(
        self, 
        transcript_text: str,
        min_occurrences: int = 2
    ) -> Dict[str, int]:
        """Extract potential character names from transcript.
        
        Args:
            transcript_text: Transcript text to analyze
            min_occurrences: Minimum times a name must appear
            
        Returns:
            Dictionary of {name: count}
        """
        potential_names = []
        
        # Extract capitalized words (likely names)
        for pattern in self.name_patterns:
            matches = re.findall(pattern, transcript_text)
            potential_names.extend(matches)
        
        # Count occurrences
        name_counts = Counter(potential_names)
        
        # Filter by minimum occurrences and exclude common words
        filtered_names = {
            name: count 
            for name, count in name_counts.items()
            if count >= min_occurrences and name not in self.exclude_words
        }
        
        self.logger.info(f"Found {len(filtered_names)} potential names")
        
        return filtered_names
    
    def compare_with_tmdb(
        self,
        potential_names: Dict[str, int],
        tmdb_cast: List[Dict[str, Any]]
    ) -> Tuple[List[str], List[str]]:
        """Compare extracted names with TMDB cast.
        
        Args:
            potential_names: Extracted name candidates
            tmdb_cast: TMDB cast information
            
        Returns:
            Tuple of (matched_names, new_names)
        """
        if not tmdb_cast:
            self.logger.warning("No TMDB cast data available")
            return [], list(potential_names.keys())
        
        # Extract TMDB character names
        tmdb_characters = set()
        for cast_member in tmdb_cast:
            char_name = cast_member.get('character', '')
            if char_name and char_name != 'N/A':
                # Handle multiple characters (e.g., "Character 1 / Character 2")
                for name in char_name.split('/'):
                    clean_name = name.strip()
                    if clean_name:
                        tmdb_characters.add(clean_name)
        
        # Compare
        matched = []
        new_names = []
        
        for name in potential_names.keys():
            # Check exact match
            if name in tmdb_characters:
                matched.append(name)
            # Check partial match (first name only)
            elif any(name in char or char in name for char in tmdb_characters):
                matched.append(name)
            else:
                new_names.append(name)
        
        self.logger.info(f"Matched: {len(matched)}, New: {len(new_names)}")
        
        return matched, new_names
    
    def extract_from_segments(
        self,
        segments: List[Dict[str, Any]],
        min_occurrences: int = 2
    ) -> Dict[str, int]:
        """Extract names from segment list.
        
        Args:
            segments: List of transcript segments
            min_occurrences: Minimum occurrences threshold
            
        Returns:
            Dictionary of potential names
        """
        # Combine all segment text
        all_text = " ".join(seg.get('text', '') for seg in segments)
        
        return self.extract_potential_names(all_text, min_occurrences)
    
    def generate_job_glossary(
        self,
        potential_names: Dict[str, int],
        confidence_threshold: int = 3
    ) -> Dict[str, str]:
        """Generate job-specific glossary from potential names.
        
        Args:
            potential_names: Extracted names with counts
            confidence_threshold: Minimum count to include
            
        Returns:
            Glossary dictionary {source: target}
        """
        # Filter by confidence
        confident_names = {
            name: count
            for name, count in potential_names.items()
            if count >= confidence_threshold
        }
        
        # For now, identity mapping (no translation)
        # In future, could use transliteration or translation APIs
        glossary = {name: name for name in confident_names.keys()}
        
        self.logger.info(f"Generated glossary with {len(glossary)} terms")
        
        return glossary
    
    def merge_glossaries(
        self,
        base_glossary: Dict[str, str],
        new_glossary: Dict[str, str],
        prefer_base: bool = True
    ) -> Dict[str, str]:
        """Merge two glossaries.
        
        Args:
            base_glossary: Existing glossary
            new_glossary: New terms to add
            prefer_base: If True, keep base values on conflict
            
        Returns:
            Merged glossary
        """
        merged = base_glossary.copy()
        
        for source, target in new_glossary.items():
            if source not in merged:
                merged[source] = target
            elif not prefer_base:
                merged[source] = target
        
        self.logger.info(
            f"Merged: {len(base_glossary)} base + {len(new_glossary)} new "
            f"= {len(merged)} total"
        )
        
        return merged
    
    def save_glossary(
        self,
        glossary: Dict[str, str],
        output_path: Path,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Save glossary to JSON file.
        
        Args:
            glossary: Glossary dictionary
            output_path: Output file path
            metadata: Optional metadata to include
        """
        output_data = {
            'glossary': glossary,
            'metadata': metadata or {},
            'term_count': len(glossary),
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"✓ Saved glossary: {output_path}")
    
    def learn_from_job(
        self,
        job_dir: Path,
        base_glossary: Optional[Dict[str, str]] = None,
        min_occurrences: int = 2,
        confidence_threshold: int = 3
    ) -> Dict[str, str]:
        """Learn glossary from job transcripts.
        
        Args:
            job_dir: Job output directory
            base_glossary: Existing glossary to extend
            min_occurrences: Minimum name occurrences
            confidence_threshold: Confidence threshold for inclusion
            
        Returns:
            Enhanced glossary
        """
        job_dir = Path(job_dir)
        
        # Load transcript segments
        segments_file = job_dir / "06_asr" / "segments.json"
        if not segments_file.exists():
            self.logger.warning(f"No segments file found: {segments_file}")
            return base_glossary or {}
        
        with open(segments_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            segments = data.get('segments', [])
        
        self.logger.info(f"Analyzing {len(segments)} segments")
        
        # Extract potential names
        potential_names = self.extract_from_segments(segments, min_occurrences)
        
        # Load TMDB data if available
        tmdb_file = job_dir / "02_tmdb_query" / "tmdb_metadata.json"
        tmdb_cast = []
        
        if tmdb_file.exists():
            with open(tmdb_file, 'r', encoding='utf-8') as f:
                tmdb_data = json.load(f)
                tmdb_cast = tmdb_data.get('cast', [])
            
            self.logger.info(f"Found {len(tmdb_cast)} TMDB cast members")
            
            # Compare with TMDB
            matched, new_names = self.compare_with_tmdb(potential_names, tmdb_cast)
            self.logger.info(
                f"Matched {len(matched)} known characters, "
                f"found {len(new_names)} new names"
            )
        
        # Generate job glossary
        job_glossary = self.generate_job_glossary(
            potential_names,
            confidence_threshold
        )
        
        # Merge with base glossary
        if base_glossary:
            enhanced_glossary = self.merge_glossaries(
                base_glossary,
                job_glossary
            )
        else:
            enhanced_glossary = job_glossary
        
        # Save enhanced glossary
        output_path = job_dir / "03_glossary_load" / "glossary_enhanced.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.save_glossary(
            enhanced_glossary,
            output_path,
            metadata={
                'job_dir': str(job_dir),
                'base_terms': len(base_glossary) if base_glossary else 0,
                'learned_terms': len(job_glossary),
                'total_terms': len(enhanced_glossary),
            }
        )
        
        return enhanced_glossary


def main():
    """Command-line interface for glossary learner."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Learn glossary from transcripts")
    parser.add_argument("job_dir", type=Path, help="Job directory path")
    parser.add_argument(
        "--base-glossary",
        type=Path,
        help="Base glossary JSON file"
    )
    parser.add_argument(
        "--min-occurrences",
        type=int,
        default=2,
        help="Minimum name occurrences (default: 2)"
    )
    parser.add_argument(
        "--confidence-threshold",
        type=int,
        default=3,
        help="Confidence threshold for inclusion (default: 3)"
    )
    
    args = parser.parse_args()
    
    # Initialize learner
    learner = GlossaryLearner()
    
    # Load base glossary
    base_glossary = None
    if args.base_glossary and args.base_glossary.exists():
        with open(args.base_glossary, 'r', encoding='utf-8') as f:
            data = json.load(f)
            base_glossary = data.get('glossary', data)
        print(f"✓ Loaded base glossary: {len(base_glossary)} terms")
    
    # Learn from job
    enhanced_glossary = learner.learn_from_job(
        args.job_dir,
        base_glossary,
        args.min_occurrences,
        args.confidence_threshold
    )
    
    print(f"\n✅ Glossary learning complete!")
    print(f"   Base terms: {len(base_glossary) if base_glossary else 0}")
    print(f"   Total terms: {len(enhanced_glossary)}")
    print(f"   New terms: {len(enhanced_glossary) - (len(base_glossary) if base_glossary else 0)}")


if __name__ == "__main__":
    main()
