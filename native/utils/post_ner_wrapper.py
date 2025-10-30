"""
Post-ASR NER wrapper for native MPS pipeline.
Corrects and enriches named entities in transcription using pre-extracted entities.
"""
import json
from pathlib import Path
from typing import List, Dict, Tuple, Set
import re
from difflib import SequenceMatcher


class PostNER:
    """
    Post-ASR Named Entity Recognition and Correction.
    
    Uses pre-extracted entities (from TMDB) to correct entity mentions
    in the ASR transcription output.
    """
    
    def __init__(self, logger=None):
        """
        Initialize Post-NER.
        
        Args:
            logger: Logger instance
        """
        self.logger = logger
        self.known_entities = {
            'persons': [],
            'locations': [],
            'titles': []
        }
        
    def load_pre_ner_entities(self, pre_ner_file: Path) -> Dict:
        """
        Load pre-extracted entities from Pre-NER stage.
        
        Args:
            pre_ner_file: Path to pre_ner.json
            
        Returns:
            Dictionary of known entities
        """
        if self.logger:
            self.logger.info(f"Loading pre-NER entities from: {pre_ner_file}")
        
        with open(pre_ner_file, 'r', encoding='utf-8') as f:
            entities = json.load(f)
        
        self.known_entities = entities
        
        if self.logger:
            total = sum(len(v) for v in entities.values())
            self.logger.info(f"Loaded {total} known entities")
            self.logger.debug(f"  Persons: {len(entities.get('persons', []))}")
            self.logger.debug(f"  Locations: {len(entities.get('locations', []))}")
            self.logger.debug(f"  Titles: {len(entities.get('titles', []))}")
        
        return entities
    
    def similarity(self, a: str, b: str) -> float:
        """
        Calculate similarity between two strings.
        
        Args:
            a: First string
            b: Second string
            
        Returns:
            Similarity ratio (0-1)
        """
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()
    
    def fuzzy_match(
        self,
        text: str,
        candidates: List[str],
        threshold: float = 0.75
    ) -> Tuple[str, float]:
        """
        Find best fuzzy match for text in candidates.
        
        Args:
            text: Text to match
            candidates: List of candidate strings
            threshold: Minimum similarity threshold
            
        Returns:
            Tuple of (best_match, similarity_score) or (None, 0.0)
        """
        if not text or not candidates:
            return None, 0.0
        
        best_match = None
        best_score = 0.0
        
        for candidate in candidates:
            score = self.similarity(text, candidate)
            if score > best_score:
                best_score = score
                best_match = candidate
        
        if best_score >= threshold:
            return best_match, best_score
        
        return None, 0.0
    
    def extract_potential_entities(self, text: str) -> List[str]:
        """
        Extract potential entity mentions from text.
        
        Uses simple heuristics:
        - Capitalized words
        - Sequences of capitalized words
        - Common patterns
        
        Args:
            text: Input text
            
        Returns:
            List of potential entity strings
        """
        # Find sequences of capitalized words (potential proper nouns)
        # Pattern: word starting with capital, followed by optional lowercase
        pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        matches = re.findall(pattern, text)
        
        # Also look for all-caps words (acronyms, etc.)
        all_caps_pattern = r'\b[A-Z]{2,}\b'
        all_caps = re.findall(all_caps_pattern, text)
        
        potential = matches + all_caps
        
        # Remove common words that aren't entities
        stop_words = {'The', 'A', 'An', 'This', 'That', 'These', 'Those', 
                     'My', 'Your', 'His', 'Her', 'Their', 'Our', 'Its'}
        potential = [p for p in potential if p not in stop_words]
        
        return list(set(potential))  # Remove duplicates
    
    def correct_entities_in_segment(
        self,
        segment: Dict,
        min_threshold: float = 0.70
    ) -> Tuple[Dict, List[Dict]]:
        """
        Correct entity mentions in a single transcript segment.
        
        Args:
            segment: Transcript segment with 'text' field
            min_threshold: Minimum similarity for correction
            
        Returns:
            Tuple of (corrected_segment, corrections_made)
        """
        text = segment.get('text', '')
        if not text:
            return segment, []
        
        corrections = []
        corrected_text = text
        
        # Extract potential entities from text
        potential_entities = self.extract_potential_entities(text)
        
        # Try to match each potential entity with known entities
        for entity_text in potential_entities:
            # Try persons first (most common in movies)
            best_match, score = self.fuzzy_match(
                entity_text,
                self.known_entities.get('persons', []),
                threshold=min_threshold
            )
            
            entity_type = 'person'
            
            # Try locations if no person match
            if not best_match:
                best_match, score = self.fuzzy_match(
                    entity_text,
                    self.known_entities.get('locations', []),
                    threshold=min_threshold
                )
                entity_type = 'location'
            
            # Try titles if no location match
            if not best_match:
                best_match, score = self.fuzzy_match(
                    entity_text,
                    self.known_entities.get('titles', []),
                    threshold=min_threshold
                )
                entity_type = 'title'
            
            # If we found a match, apply correction
            if best_match and best_match != entity_text:
                # Replace in text (case-sensitive)
                corrected_text = corrected_text.replace(entity_text, best_match)
                
                corrections.append({
                    'original': entity_text,
                    'corrected': best_match,
                    'type': entity_type,
                    'confidence': round(score, 3)
                })
        
        # Update segment with corrected text
        corrected_segment = segment.copy()
        if corrected_text != text:
            corrected_segment['text'] = corrected_text
            corrected_segment['entities_corrected'] = True
        
        return corrected_segment, corrections
    
    def process_transcript(
        self,
        transcript: Dict,
        min_threshold: float = 0.70
    ) -> Tuple[Dict, Dict]:
        """
        Process entire transcript to correct entities.
        
        Args:
            transcript: Transcript dictionary with segments
            min_threshold: Minimum similarity for correction
            
        Returns:
            Tuple of (corrected_transcript, statistics)
        """
        if self.logger:
            self.logger.info("Processing transcript for entity correction...")
        
        segments = transcript.get('segments', [])
        corrected_segments = []
        all_corrections = []
        
        for i, segment in enumerate(segments):
            corrected_seg, corrections = self.correct_entities_in_segment(
                segment,
                min_threshold=min_threshold
            )
            
            if corrections:
                # Add segment reference to corrections
                for corr in corrections:
                    corr['segment_id'] = i
                    corr['segment_start'] = segment.get('start', 0)
                
                all_corrections.extend(corrections)
            
            corrected_segments.append(corrected_seg)
        
        # Calculate statistics
        unique_corrections = {}
        for corr in all_corrections:
            key = f"{corr['original']} → {corr['corrected']}"
            if key not in unique_corrections:
                unique_corrections[key] = {
                    'original': corr['original'],
                    'corrected': corr['corrected'],
                    'type': corr['type'],
                    'occurrences': 0,
                    'avg_confidence': 0.0
                }
            unique_corrections[key]['occurrences'] += 1
            unique_corrections[key]['avg_confidence'] += corr['confidence']
        
        # Average confidences
        for key in unique_corrections:
            count = unique_corrections[key]['occurrences']
            unique_corrections[key]['avg_confidence'] /= count
            unique_corrections[key]['avg_confidence'] = round(
                unique_corrections[key]['avg_confidence'], 3
            )
        
        stats = {
            'segments_processed': len(segments),
            'segments_with_corrections': sum(1 for s in corrected_segments 
                                            if s.get('entities_corrected', False)),
            'total_corrections': len(all_corrections),
            'unique_corrections': len(unique_corrections),
            'corrections_by_type': self._count_by_type(all_corrections),
            'threshold_used': min_threshold
        }
        
        if self.logger:
            self.logger.info(f"Processed {stats['segments_processed']} segments")
            self.logger.info(f"Made {stats['total_corrections']} corrections "
                           f"({stats['unique_corrections']} unique)")
            self.logger.info(f"  Persons: {stats['corrections_by_type'].get('person', 0)}")
            self.logger.info(f"  Locations: {stats['corrections_by_type'].get('location', 0)}")
            self.logger.info(f"  Titles: {stats['corrections_by_type'].get('title', 0)}")
        
        # Create corrected transcript
        corrected_transcript = transcript.copy()
        corrected_transcript['segments'] = corrected_segments
        
        result = {
            'transcript': corrected_transcript,
            'corrections': list(unique_corrections.values()),
            'statistics': stats
        }
        
        return result, stats
    
    def _count_by_type(self, corrections: List[Dict]) -> Dict[str, int]:
        """Count corrections by entity type."""
        counts = {}
        for corr in corrections:
            entity_type = corr.get('type', 'unknown')
            counts[entity_type] = counts.get(entity_type, 0) + 1
        return counts
    
    def generate_entity_report(
        self,
        corrections: List[Dict]
    ) -> str:
        """
        Generate human-readable report of corrections.
        
        Args:
            corrections: List of unique corrections
            
        Returns:
            Report string
        """
        if not corrections:
            return "No entity corrections made."
        
        report = []
        report.append("=== Entity Corrections Report ===\n")
        
        # Group by type
        by_type = {}
        for corr in corrections:
            entity_type = corr.get('type', 'unknown')
            if entity_type not in by_type:
                by_type[entity_type] = []
            by_type[entity_type].append(corr)
        
        for entity_type, items in sorted(by_type.items()):
            report.append(f"\n{entity_type.upper()}S:")
            for item in sorted(items, key=lambda x: -x['occurrences']):
                report.append(
                    f"  {item['original']:20s} → {item['corrected']:20s} "
                    f"({item['occurrences']:2d}x, conf: {item['avg_confidence']:.2f})"
                )
        
        return '\n'.join(report)


def load_secrets(secrets_path: Path = None) -> Dict:
    """Load secrets from config/secrets.json."""
    if secrets_path is None:
        secrets_path = Path("config/secrets.json")
    
    if not secrets_path.exists():
        raise FileNotFoundError(f"Secrets file not found: {secrets_path}")
    
    with open(secrets_path, 'r') as f:
        secrets = json.load(f)
    
    return secrets
