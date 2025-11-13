"""
Hinglish Glossary System

Provides terminology management for Hinglish→English subtitle translation.
Loads TSV glossary and applies term substitutions with context awareness.
Supports advanced strategies: context-aware, character-based, regional, ML-based.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging


class HinglishGlossary:
    """
    Hinglish→English glossary manager
    
    Loads terminology mappings from TSV and applies substitutions
    to subtitle text while preserving context.
    
    Supports multiple selection strategies:
    - first: Use first option (default, fast)
    - context: Analyze surrounding text
    - character: Use character speaking profiles
    - regional: Apply regional variants (Mumbai, Delhi, etc.)
    - frequency: Learn from previous selections
    - adaptive: Combine all strategies intelligently
    - ml: ML-based selection (future)
    """
    
    def __init__(
        self, 
        tsv_path: Path, 
        logger: Optional[logging.Logger] = None,
        strategy: str = 'first',
        prompt_path: Optional[Path] = None,
        frequency_data_path: Optional[Path] = None
    ):
        """
        Initialize glossary from TSV file
        
        Args:
            tsv_path: Path to glossary TSV file
            logger: Optional logger instance
            strategy: Selection strategy (first|context|character|regional|adaptive|ml)
            prompt_path: Path to movie-specific prompt (for character/regional)
            frequency_data_path: Path to learned frequency data
        """
        self.logger = logger or logging.getLogger(__name__)
        self.term_map: Dict[str, Dict] = {}
        self.terms_applied = 0
        self.terms_skipped = 0
        self.strategy_name = strategy
        
        # Initialize advanced strategy if needed
        self.advanced_strategy = None
        if strategy != 'first':
            try:
                from .glossary_advanced import AdvancedGlossaryStrategy
                self.advanced_strategy = AdvancedGlossaryStrategy(strategy, logger)
                
                # Initialize from prompt
                if prompt_path:
                    self.advanced_strategy.initialize_from_prompt(prompt_path)
                
                # Load frequency data
                if frequency_data_path and frequency_data_path.exists():
                    self.advanced_strategy.load_frequency_data(frequency_data_path)
                
                self.logger.info(f"Initialized advanced glossary strategy: {strategy}")
            except ImportError:
                self.logger.warning("Advanced strategies not available, using 'first' strategy")
                self.strategy_name = 'first'
        
        if not tsv_path.exists():
            self.logger.warning(f"Glossary file not found: {tsv_path}")
            return
        
        self._load_glossary(tsv_path)
    
    def _load_glossary(self, tsv_path: Path):
        """Load glossary from TSV file"""
        try:
            with open(tsv_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if not lines:
                return
            
            # Parse header
            header = lines[0].strip().split('\t')
            if len(header) < 2:
                self.logger.error("Invalid glossary format: needs at least 2 columns")
                return
            
            # Parse terms
            for i, line in enumerate(lines[1:], start=2):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split('\t')
                if len(parts) < 2:
                    continue
                
                source = parts[0].strip().lower()
                preferred = parts[1].strip()
                notes = parts[2].strip() if len(parts) > 2 else ""
                context = parts[3].strip() if len(parts) > 3 else ""
                
                if not source or not preferred:
                    continue
                
                # Parse pipe-separated options
                options = [opt.strip() for opt in preferred.split('|') if opt.strip()]
                
                self.term_map[source] = {
                    'options': options,
                    'notes': notes,
                    'context': context,
                    'line': i
                }
            
            self.logger.info(f"Loaded {len(self.term_map)} glossary terms from {tsv_path}")
            
        except Exception as e:
            self.logger.error(f"Error loading glossary: {e}")
    
    def apply(
        self, 
        text: str, 
        context: Optional[Dict[str, Any]] = None,
        preserve_case: bool = True
    ) -> str:
        """
        Apply glossary substitutions to text with advanced strategy support
        
        Args:
            text: Input text to process
            context: Context dict with keys:
                - window: Surrounding text (previous + next segments)
                - speaker: Speaker name (if available)
                - term_context: Term context type (from TSV)
                - segment_index: Segment index in subtitle
            preserve_case: Maintain original case when substituting
        
        Returns:
            Text with glossary terms substituted
        """
        if not self.term_map:
            return text
        
        result = text
        applied_count = 0
        
        # Build context dict if not provided
        if context is None:
            context = {}
        
        # Sort terms by length (longest first) to handle multi-word terms
        sorted_terms = sorted(self.term_map.keys(), key=len, reverse=True)
        
        for source_term in sorted_terms:
            term_data = self.term_map[source_term]
            options = term_data['options']
            
            if not options:
                continue
            
            # Create case-insensitive pattern with word boundaries
            pattern = re.compile(r'\b' + re.escape(source_term) + r'\b', re.IGNORECASE)
            
            # Find all matches
            matches = list(pattern.finditer(result))
            
            if matches:
                # Select best option based on strategy
                if self.advanced_strategy and self.strategy_name != 'first':
                    # Build context for advanced selection
                    selection_context = {
                        'text': result,
                        'window': context.get('window', ''),
                        'speaker': context.get('speaker'),
                        'term_context': term_data['context']
                    }
                    
                    replacement = self.advanced_strategy.select_best_option(
                        source_term, options, selection_context
                    )
                else:
                    # Simple: use first option
                    replacement = options[0]
                
                # Skip empty replacements (like "ji" → "")
                if not replacement:
                    continue
                
                # Replace from end to start to preserve positions
                for match in reversed(matches):
                    original = match.group()
                    
                    # Preserve case if requested
                    if preserve_case:
                        if original.isupper():
                            replacement_final = replacement.upper()
                        elif original[0].isupper():
                            replacement_final = replacement.capitalize()
                        else:
                            replacement_final = replacement
                    else:
                        replacement_final = replacement
                    
                    # Perform replacement
                    result = result[:match.start()] + replacement_final + result[match.end():]
                    applied_count += 1
        
        self.terms_applied += applied_count
        return result
    
    def apply_batch(self, texts: List[str], context: str = "") -> List[str]:
        """
        Apply glossary to multiple texts
        
        Args:
            texts: List of text strings
            context: Optional context
        
        Returns:
            List of processed texts
        """
        return [self.apply(text, context) for text in texts]
    
    def get_term_info(self, source_term: str) -> Optional[Dict]:
        """
        Get information about a specific term
        
        Args:
            source_term: Source Hinglish term
        
        Returns:
            Term data dict or None
        """
        return self.term_map.get(source_term.lower())
    
    def search_terms(self, query: str) -> List[Tuple[str, Dict]]:
        """
        Search for terms matching query
        
        Args:
            query: Search string
        
        Returns:
            List of (term, data) tuples
        """
        query_lower = query.lower()
        results = []
        
        for term, data in self.term_map.items():
            if query_lower in term or query_lower in ' '.join(data['options']).lower():
                results.append((term, data))
        
        return results
    
    def get_stats(self) -> Dict:
        """
        Get glossary usage statistics including advanced strategy stats
        
        Returns:
            Stats dictionary
        """
        stats = {
            'total_terms': len(self.term_map),
            'terms_applied': self.terms_applied,
            'terms_skipped': self.terms_skipped,
            'strategy': self.strategy_name,
            'contexts': list(set(d['context'] for d in self.term_map.values() if d['context']))
        }
        
        # Add advanced strategy stats if available
        if self.advanced_strategy:
            stats['advanced_stats'] = self.advanced_strategy.get_statistics()
        
        return stats
    
    def save_learned_data(self, output_dir: Path):
        """
        Save learned data from advanced strategies
        
        Args:
            output_dir: Directory to save learned data
        """
        if self.advanced_strategy:
            self.advanced_strategy.save_learned_data(output_dir)
            self.logger.info(f"Saved learned data to {output_dir}")
        else:
            self.logger.debug("No advanced strategy, nothing to save")
    
    def validate(self) -> List[Dict]:
        """
        Validate glossary entries
        
        Returns:
            List of validation issues
        """
        issues = []
        
        for term, data in self.term_map.items():
            # Check for empty options
            if not data['options']:
                issues.append({
                    'term': term,
                    'type': 'empty_options',
                    'message': 'No translation options provided'
                })
            
            # Check for very long terms (likely errors)
            if len(term) > 50:
                issues.append({
                    'term': term,
                    'type': 'long_term',
                    'message': f'Term unusually long ({len(term)} chars)'
                })
            
            # Check for duplicate options
            if len(data['options']) != len(set(data['options'])):
                issues.append({
                    'term': term,
                    'type': 'duplicate_options',
                    'message': 'Duplicate translation options'
                })
        
        return issues


def load_film_prompt(prompt_path: Path, logger: Optional[logging.Logger] = None) -> Optional[str]:
    """
    Load per-film context prompt
    
    Args:
        prompt_path: Path to prompt file
        logger: Optional logger
    
    Returns:
        Prompt text or None
    """
    logger = logger or logging.getLogger(__name__)
    
    if not prompt_path.exists():
        logger.debug(f"Prompt file not found: {prompt_path}")
        return None
    
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        logger.info(f"Loaded film prompt from {prompt_path.name}")
        return content
        
    except Exception as e:
        logger.error(f"Error loading prompt: {e}")
        return None


# Example usage
if __name__ == "__main__":
    # Test glossary
    glossary_path = Path(__file__).parent.parent / "glossary" / "hinglish_master.tsv"
    glossary = HinglishGlossary(glossary_path)
    
    # Test substitutions
    test_texts = [
        "Hey yaar, kya scene hai?",
        "Ji, I understand what you mean.",
        "Arre bhai, this is pakka nonsense!",
        "Listen yaar, we need to do some jugaad here."
    ]
    
    print("Glossary Test:")
    print("=" * 60)
    for text in test_texts:
        result = glossary.apply(text)
        print(f"Input:  {text}")
        print(f"Output: {result}")
        print()
    
    # Show stats
    stats = glossary.get_stats()
    print(f"Stats: {stats}")
