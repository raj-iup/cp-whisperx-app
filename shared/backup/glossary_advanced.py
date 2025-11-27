"""
Advanced Glossary Strategies - Context-Aware Term Selection
Implements ML-based, character-aware, and regional variant selection
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging
from collections import defaultdict, Counter

try:
    from .glossary_ml import MLTermSelector
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False


class ContextAnalyzer:
    """Analyzes surrounding text context for intelligent term selection"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        
        # Context patterns for different situations
        self.context_patterns = {
            'formal': [
                r'\b(sir|madam|please|kindly|respectfully)\b',
                r'\b(meeting|office|presentation|business)\b',
                r'\b(professor|doctor|officer|honorable)\b'
            ],
            'casual': [
                r'\b(hey|dude|bro|man|guys)\b',
                r'\b(cool|awesome|chill|fun|party)\b',
                r'\b(friend|buddy|pal)\b'
            ],
            'emotional': [
                r'\b(love|heart|feel|cry|sad|happy)\b',
                r'\b(mother|father|family|home)\b',
                r'[!]{2,}',  # Multiple exclamation marks
            ],
            'aggressive': [
                r'\b(fight|kill|beat|destroy|revenge)\b',
                r'\b(angry|mad|furious|hate)\b',
                r'[A-Z]{4,}',  # ALL CAPS WORDS
            ],
            'question': [
                r'\b(what|why|how|when|where|who)\b',
                r'\?',
            ]
        }
    
    def analyze_context(self, text: str, window: str = "") -> Dict[str, float]:
        """
        Analyze text context and return confidence scores for each context type
        
        Args:
            text: The segment text being analyzed
            window: Surrounding text (previous + next segments)
        
        Returns:
            Dict mapping context type to confidence score (0.0-1.0)
        """
        combined_text = f"{window} {text}".lower()
        scores = {}
        
        for context_type, patterns in self.context_patterns.items():
            matches = 0
            for pattern in patterns:
                matches += len(re.findall(pattern, combined_text, re.IGNORECASE))
            
            # Normalize score
            scores[context_type] = min(matches / 3.0, 1.0)
        
        return scores
    
    def select_term_by_context(
        self, 
        options: List[str], 
        context_scores: Dict[str, float],
        context_hints: Dict[str, List[str]]
    ) -> str:
        """
        Select best term option based on context analysis
        
        Args:
            options: List of possible translations
            context_scores: Context type confidence scores
            context_hints: Mapping of context types to preferred options
        
        Returns:
            Best matching option
        """
        # Score each option based on context
        option_scores = defaultdict(float)
        
        for context_type, score in context_scores.items():
            if score > 0.3:  # Significant context
                preferred = context_hints.get(context_type, [])
                for opt in options:
                    if opt in preferred:
                        option_scores[opt] += score
        
        if option_scores:
            best_option = max(option_scores.items(), key=lambda x: x[1])[0]
            return best_option
        
        # Fallback to first option
        return options[0] if options else ""


class CharacterProfiler:
    """Per-character speaking style profiles"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.profiles: Dict[str, Dict[str, Any]] = {}
    
    def load_profiles_from_prompt(self, prompt_path: Path):
        """
        Load character profiles from movie-specific prompt file
        
        Expected format in prompt:
        Characters:
        - Name (gender): Traits, speech_pattern=casual, english_ratio=0.7
        """
        if not prompt_path.exists():
            return
        
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse character sections
            lines = content.split('\n')
            in_characters = False
            
            for line in lines:
                if line.strip().startswith('Characters:'):
                    in_characters = True
                    continue
                
                if in_characters:
                    if line.strip() and not line.startswith('- '):
                        # End of character section
                        break
                    
                    if line.startswith('- '):
                        # Parse character line
                        self._parse_character_line(line)
            
            if self.profiles:
                self.logger.info(f"Loaded {len(self.profiles)} character profiles")
        
        except Exception as e:
            self.logger.warning(f"Error loading character profiles: {e}")
    
    def _parse_character_line(self, line: str):
        """Parse a character definition line"""
        # Format: - Name (gender): Description
        match = re.match(r'- ([^(]+)\s*\(([^)]+)\):\s*(.+)', line)
        if match:
            name = match.group(1).strip()
            gender = match.group(2).strip()
            description = match.group(3).strip()
            
            # Default profile
            profile = {
                'gender': gender,
                'formality': 'neutral',
                'english_ratio': 0.5,
                'preferred_terms': {}
            }
            
            # Extract hints from description
            desc_lower = description.lower()
            
            if any(w in desc_lower for w in ['formal', 'educated', 'sophisticated', 'elite']):
                profile['formality'] = 'formal'
                profile['english_ratio'] = 0.7
            elif any(w in desc_lower for w in ['casual', 'street', 'youth', 'young']):
                profile['formality'] = 'casual'
                profile['english_ratio'] = 0.6
            elif any(w in desc_lower for w in ['traditional', 'elder', 'conservative']):
                profile['formality'] = 'formal'
                profile['english_ratio'] = 0.3
            
            self.profiles[name.lower()] = profile
    
    def get_preferred_term(
        self, 
        speaker: str, 
        options: List[str], 
        term_context: str
    ) -> Optional[str]:
        """
        Get character's preferred term based on their profile
        
        Args:
            speaker: Speaker name
            options: Available term options
            term_context: Context of the term (casual, formal, etc.)
        
        Returns:
            Preferred option or None
        """
        speaker_key = speaker.lower() if speaker else None
        
        if not speaker_key or speaker_key not in self.profiles:
            return None
        
        profile = self.profiles[speaker_key]
        formality = profile['formality']
        
        # Map formality to preferred options
        if formality == 'formal' and term_context == 'honorific':
            # Formal speakers use full honorifics
            return next((opt for opt in options if opt in ['sir', 'ma\'am', 'mister']), None)
        elif formality == 'casual' and term_context == 'honorific':
            # Casual speakers might omit or shorten
            return next((opt for opt in options if opt == ''), None)
        
        return None


class RegionalVariantSelector:
    """Regional variant support (Mumbai, Delhi, Punjab, etc.)"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        
        # Regional term preferences
        self.regional_preferences = {
            'mumbai': {
                'yaar': 'dude',
                'bhai': 'bro',
                'apun': 'I',  # Mumbai-specific
                'bhidu': 'dude',  # Mumbai-specific
                'tapori': 'street hustler'
            },
            'delhi': {
                'yaar': 'man',
                'bhai': 'brother',
                'ji': 'sir/ma\'am',  # Delhi is more formal
            },
            'punjab': {
                'yaar': 'yaar',  # Keep Punjabi flavor
                'bhai': 'brother',
                'veere': 'brother',  # Punjabi-specific
                'paji': 'brother',
            },
            'haryana': {
                'bhai': 'brother',
                'bapu': 'father',
                'tau': 'uncle',
            },
            'bihar': {
                'bhai': 'brother',
                'babu': 'mister',
                'sahab': 'sir',
            }
        }
        
        self.current_region: Optional[str] = None
    
    def detect_region_from_prompt(self, prompt_path: Path):
        """Detect regional setting from movie prompt file"""
        if not prompt_path.exists():
            return
        
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                content = f.read().lower()
            
            # Check for regional keywords
            if 'mumbai' in content or 'bombay' in content:
                self.current_region = 'mumbai'
            elif 'delhi' in content:
                self.current_region = 'delhi'
            elif 'punjab' in content or 'punjabi' in content:
                self.current_region = 'punjab'
            elif 'haryana' in content or 'haryanvi' in content:
                self.current_region = 'haryana'
            elif 'bihar' in content or 'bhojpuri' in content:
                self.current_region = 'bihar'
            
            if self.current_region:
                self.logger.info(f"Detected regional variant: {self.current_region}")
        
        except Exception as e:
            self.logger.warning(f"Error detecting region: {e}")
    
    def get_regional_preference(self, term: str, options: List[str]) -> Optional[str]:
        """Get regional preference for a term"""
        if not self.current_region:
            return None
        
        regional_prefs = self.regional_preferences.get(self.current_region, {})
        preferred = regional_prefs.get(term)
        
        if preferred and preferred in options:
            return preferred
        
        return None


class FrequencyLearner:
    """Learns term frequency and selection patterns"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.term_usage: Dict[str, Counter] = defaultdict(Counter)
        self.selection_history: List[Tuple[str, str, str]] = []
    
    def record_selection(self, source_term: str, selected_option: str, context: str):
        """Record a term selection for learning"""
        self.term_usage[source_term][selected_option] += 1
        self.selection_history.append((source_term, selected_option, context))
    
    def get_most_frequent(self, source_term: str, options: List[str]) -> Optional[str]:
        """Get most frequently used option for this term"""
        if source_term not in self.term_usage:
            return None
        
        counter = self.term_usage[source_term]
        if not counter:
            return None
        
        # Get most common that's in current options
        for term, count in counter.most_common():
            if term in options:
                return term
        
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get learning statistics"""
        return {
            'total_selections': len(self.selection_history),
            'unique_terms': len(self.term_usage),
            'most_used_terms': {
                term: counter.most_common(3)
                for term, counter in list(self.term_usage.items())[:10]
            }
        }
    
    def save_to_file(self, filepath: Path):
        """Save learned patterns to file"""
        try:
            import json
            data = {
                'term_usage': {
                    term: dict(counter)
                    for term, counter in self.term_usage.items()
                },
                'statistics': self.get_statistics()
            }
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.logger.info(f"Saved frequency data to {filepath}")
        
        except Exception as e:
            self.logger.warning(f"Error saving frequency data: {e}")
    
    def load_from_file(self, filepath: Path):
        """Load learned patterns from file"""
        if not filepath.exists():
            return
        
        try:
            import json
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Restore term usage
            for term, usage_dict in data.get('term_usage', {}).items():
                self.term_usage[term] = Counter(usage_dict)
            
            self.logger.info(f"Loaded frequency data from {filepath}")
        
        except Exception as e:
            self.logger.warning(f"Error loading frequency data: {e}")


class AdvancedGlossaryStrategy:
    """
    Orchestrates all advanced glossary strategies
    Combines context analysis, character profiles, regional variants, and frequency learning
    """
    
    def __init__(
        self, 
        strategy: str = 'adaptive',
        logger: Optional[logging.Logger] = None
    ):
        """
        Args:
            strategy: 'first', 'context', 'character', 'regional', 'adaptive', 'ml'
        """
        self.strategy = strategy
        self.logger = logger or logging.getLogger(__name__)
        
        # Initialize components
        self.context_analyzer = ContextAnalyzer(logger)
        self.character_profiler = CharacterProfiler(logger)
        self.regional_selector = RegionalVariantSelector(logger)
        self.frequency_learner = FrequencyLearner(logger)
        
        # Initialize ML selector if strategy requires it
        self.ml_selector = None
        if strategy == 'ml' or strategy == 'adaptive':
            if ML_AVAILABLE:
                try:
                    self.ml_selector = MLTermSelector(logger)
                    if self.ml_selector.is_available():
                        self.logger.info(f"✓ ML selector initialized ({self.ml_selector.model_type})")
                    else:
                        self.logger.warning("ML selector initialization failed")
                        self.ml_selector = None
                except Exception as e:
                    self.logger.warning(f"Could not initialize ML selector: {e}")
                    self.ml_selector = None
            else:
                self.logger.warning("ML selector not available (install sentence-transformers)")
        
        # Context hints for term selection
        self.context_hints = {
            'formal': ['sir', 'ma\'am', 'mister', 'miss'],
            'casual': ['dude', 'man', 'bro', 'buddy'],
            'emotional': ['friend', 'dear'],
        }
    
    def initialize_from_prompt(self, prompt_path: Optional[Path]):
        """Initialize strategy components from movie prompt file"""
        if not prompt_path or not prompt_path.exists():
            return
        
        self.logger.info(f"Initializing advanced strategies from: {prompt_path.name}")
        
        # Load character profiles
        self.character_profiler.load_profiles_from_prompt(prompt_path)
        
        # Detect regional variant
        self.regional_selector.detect_region_from_prompt(prompt_path)
        
        # Load ML model if available
        if self.ml_selector:
            ml_model_path = prompt_path.parent / f"{prompt_path.stem}_ml_model.json"
            if ml_model_path.exists():
                self.ml_selector.load_model(ml_model_path)
    
    def load_frequency_data(self, frequency_file: Path):
        """Load learned frequency data"""
        self.frequency_learner.load_from_file(frequency_file)
        
        # Also try to load ML model from same directory
        if self.ml_selector:
            ml_model_path = frequency_file.parent / "ml_selection_model.json"
            if ml_model_path.exists():
                self.ml_selector.load_model(ml_model_path)
    
    def select_best_option(
        self,
        source_term: str,
        options: List[str],
        context: Dict[str, Any]
    ) -> str:
        """
        Select best translation option using configured strategy
        
        Args:
            source_term: Original Hinglish term
            options: List of possible translations
            context: Context dict with keys:
                - text: Current segment text
                - window: Surrounding text
                - speaker: Speaker name (if available)
                - term_context: Term context type (casual, formal, etc.)
        
        Returns:
            Selected translation
        """
        if not options:
            return ""
        
        if len(options) == 1:
            return options[0]
        
        # Strategy: first (simple, default)
        if self.strategy == 'first':
            selected = options[0]
        
        # Strategy: frequency-based
        elif self.strategy == 'frequency':
            selected = self._select_by_frequency(source_term, options)
        
        # Strategy: regional
        elif self.strategy == 'regional':
            selected = self._select_by_region(source_term, options)
        
        # Strategy: character-based
        elif self.strategy == 'character':
            selected = self._select_by_character(
                source_term, options, 
                context.get('speaker'), 
                context.get('term_context', '')
            )
        
        # Strategy: context-aware
        elif self.strategy == 'context':
            selected = self._select_by_context(source_term, options, context)
        
        # Strategy: adaptive (combines all)
        elif self.strategy == 'adaptive':
            selected = self._select_adaptive(source_term, options, context)
        
        # Strategy: ML-based (future)
        elif self.strategy == 'ml':
            selected = self._select_by_ml(source_term, options, context)
        
        else:
            selected = options[0]
        
        # Record selection for learning
        self.frequency_learner.record_selection(
            source_term, selected, context.get('term_context', '')
        )
        
        # Record for ML learning as well
        if self.ml_selector:
            try:
                self.ml_selector.record_selection(source_term, selected, context)
            except Exception as e:
                self.logger.debug(f"ML recording error: {e}")
        
        return selected
    
    def _select_by_frequency(self, source_term: str, options: List[str]) -> str:
        """Select based on frequency learning"""
        freq_choice = self.frequency_learner.get_most_frequent(source_term, options)
        return freq_choice if freq_choice else options[0]
    
    def _select_by_region(self, source_term: str, options: List[str]) -> str:
        """Select based on regional variant"""
        regional_choice = self.regional_selector.get_regional_preference(source_term, options)
        return regional_choice if regional_choice else options[0]
    
    def _select_by_character(
        self, 
        source_term: str, 
        options: List[str],
        speaker: Optional[str],
        term_context: str
    ) -> str:
        """Select based on character profile"""
        if speaker:
            char_choice = self.character_profiler.get_preferred_term(
                speaker, options, term_context
            )
            if char_choice:
                return char_choice
        return options[0]
    
    def _select_by_context(
        self, 
        source_term: str, 
        options: List[str],
        context: Dict[str, Any]
    ) -> str:
        """Select based on context analysis"""
        text = context.get('text', '')
        window = context.get('window', '')
        
        context_scores = self.context_analyzer.analyze_context(text, window)
        
        selected = self.context_analyzer.select_term_by_context(
            options, context_scores, self.context_hints
        )
        
        return selected
    
    def _select_adaptive(
        self, 
        source_term: str, 
        options: List[str],
        context: Dict[str, Any]
    ) -> str:
        """Adaptive selection - tries all strategies with priority"""
        
        # Priority 1: Character profile (if speaker known)
        speaker = context.get('speaker')
        if speaker:
            char_choice = self._select_by_character(
                source_term, options, speaker, context.get('term_context', '')
            )
            if char_choice != options[0]:  # Not just fallback
                return char_choice
        
        # Priority 2: Regional variant
        regional_choice = self._select_by_region(source_term, options)
        if regional_choice != options[0]:
            return regional_choice
        
        # Priority 3: Context analysis
        context_choice = self._select_by_context(source_term, options, context)
        if context_choice != options[0]:
            return context_choice
        
        # Priority 4: Frequency learning
        freq_choice = self._select_by_frequency(source_term, options)
        if freq_choice:
            return freq_choice
        
        # Fallback
        return options[0]
    
    def _select_by_ml(
        self, 
        source_term: str, 
        options: List[str],
        context: Dict[str, Any]
    ) -> str:
        """ML-based selection using semantic embeddings and similarity matching"""
        
        if not self.ml_selector or not self.ml_selector.is_available():
            self.logger.debug("ML selector not available, using adaptive")
            return self._select_adaptive(source_term, options, context)
        
        try:
            # Get ML prediction
            predicted_option, confidence = self.ml_selector.predict(
                source_term, options, context
            )
            
            # Use ML prediction if confidence is high enough
            if confidence > 0.3:  # Minimum confidence threshold
                self.logger.debug(
                    f"ML selected '{predicted_option}' for '{source_term}' "
                    f"(confidence: {confidence:.2f})"
                )
                return predicted_option
            else:
                # Low confidence, fall back to adaptive
                self.logger.debug(
                    f"ML confidence too low ({confidence:.2f}), using adaptive fallback"
                )
                return self._select_adaptive(source_term, options, context)
        
        except Exception as e:
            self.logger.warning(f"ML selection error: {e}, using adaptive fallback")
            return self._select_adaptive(source_term, options, context)
    
    def save_learned_data(self, output_dir: Path):
        """Save all learned data"""
        output_dir.mkdir(exist_ok=True, parents=True)
        
        # Save frequency data
        freq_file = output_dir / "term_frequency.json"
        self.frequency_learner.save_to_file(freq_file)
        
        # Save ML model data
        if self.ml_selector:
            ml_file = output_dir / "ml_selection_model.json"
            try:
                self.ml_selector.save_model(ml_file)
            except Exception as e:
                self.logger.warning(f"Could not save ML model: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics"""
        stats = {
            'strategy': self.strategy,
            'character_profiles': len(self.character_profiler.profiles),
            'regional_variant': self.regional_selector.current_region,
            'frequency_stats': self.frequency_learner.get_statistics()
        }
        
        # Add ML stats if available
        if self.ml_selector:
            stats['ml_stats'] = self.ml_selector.get_statistics()
        
        return stats
