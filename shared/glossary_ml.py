"""
ML-Based Glossary Term Selection
Uses semantic embeddings and similarity matching for intelligent term selection
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import json
from collections import defaultdict

# Local
from shared.logger import get_logger
logger = get_logger(__name__)


class MLTermSelector:
    """
    ML-based term selection using sentence embeddings and semantic similarity
    
    Uses a lightweight approach:
    1. Encode context using sentence transformers (if available)
    2. Match against historical successful selections
    3. Fall back to TF-IDF similarity if transformers unavailable
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.model = None
        self.model_type = None
        self.embedding_cache = {}
        self.training_data = []
        
        # Term selection history with context embeddings
        self.selection_memory: Dict[str, List[Dict]] = defaultdict(list)
        
        # Initialize embedding model
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the best available embedding model"""
        
        # Try 1: sentence-transformers (best quality)
        try:
            self.logger.debug("Trying sentence-transformers...")
            from sentence_transformers import SentenceTransformer
            # Use local model if available, don't hang on download
            self.model = SentenceTransformer('all-MiniLM-L6-v2', cache_folder=None)
            self.model_type = 'sentence-transformer'
            self.logger.info("✓ Initialized ML selector with sentence-transformers")
            return
        except (ImportError, OSError, Exception) as e:
            self.logger.debug(f"sentence-transformers not available: {type(e).__name__}")
        
        # Try 2: Skip transformers download (causes hangs with auth issues)
        # Falls through to TF-IDF
        
        # Fallback: TF-IDF (lightweight, no dependencies)
        self.logger.debug("Using TF-IDF fallback...")
        self.model_type = 'tfidf'
        self.logger.info("⚠ Using TF-IDF fallback for ML selector (install sentence-transformers for better results)")
    
    def encode(self, text: str) -> "np.ndarray":
        """Encode text into embedding vector"""
        import numpy as np
        
        if not text:
            return np.zeros(384)  # Default dimension
        
        # Check cache
        cache_key = text[:200]  # Limit cache key length
        if cache_key in self.embedding_cache:
            return self.embedding_cache[cache_key]
        
        embedding = None
        
        if self.model_type == 'sentence-transformer':
            embedding = self.model.encode(text, convert_to_numpy=True)
        
        elif self.model_type == 'transformers':
            import torch
            
            # Tokenize and encode
            inputs = self.tokenizer(text, return_tensors='pt', truncation=True, max_length=128)
            with torch.no_grad():
                outputs = self.model(**inputs)
            
            # Mean pooling
            embeddings = outputs.last_hidden_state
            attention_mask = inputs['attention_mask']
            mask_expanded = attention_mask.unsqueeze(-1).expand(embeddings.size()).float()
            sum_embeddings = torch.sum(embeddings * mask_expanded, 1)
            sum_mask = torch.clamp(mask_expanded.sum(1), min=1e-9)
            embedding = (sum_embeddings / sum_mask).squeeze().numpy()
        
        elif self.model_type == 'tfidf':
            # Simple TF-IDF-like feature vector
            embedding = self._simple_tfidf_encode(text)
        
        # Cache result
        if len(self.embedding_cache) < 1000:  # Limit cache size
            self.embedding_cache[cache_key] = embedding
        
        return embedding
    
    def _simple_tfidf_encode(self, text: str) -> "np.ndarray":
        """Simple TF-IDF-like encoding (fallback when ML libraries unavailable)"""
        import numpy as np
        
        # Create a fixed-size feature vector based on character n-grams
        text_lower = text.lower()
        
        # Features: word presence, bigrams, length, punctuation
        features = []
        
        # Common Hinglish words (presence features)
        keywords = [
            'yaar', 'bhai', 'ji', 'sir', 'madam', 'dude', 'man', 'brother',
            'friend', 'hey', 'please', 'formal', 'casual', 'question',
            'what', 'why', 'how', 'when', 'fight', 'love', 'family'
        ]
        
        for word in keywords:
            features.append(1.0 if word in text_lower else 0.0)
        
        # Character features
        features.append(len(text) / 100.0)  # Normalized length
        features.append(text.count('?') / 10.0)  # Question marks
        features.append(text.count('!') / 10.0)  # Exclamation marks
        features.append(sum(1 for c in text if c.isupper()) / max(len(text), 1))  # Caps ratio
        
        # Pad to 384 dimensions (match transformer output size)
        features.extend([0.0] * (384 - len(features)))
        
        return np.array(features[:384], dtype=np.float32)
    
    def cosine_similarity(self, vec1: "np.ndarray", vec2: "np.ndarray") -> float:
        """Calculate cosine similarity between two vectors"""
        import numpy as np
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def record_selection(
        self,
        source_term: str,
        selected_option: str,
        context: Dict[str, Any]
    ):
        """Record a successful term selection for learning"""
        
        # Build context text
        context_text = self._build_context_text(context)
        
        # Encode context
        embedding = self.encode(context_text)
        
        # Store selection
        selection_record = {
            'option': selected_option,
            'context': context_text,
            'embedding': embedding,
            'speaker': context.get('speaker'),
            'term_context': context.get('term_context', ''),
        }
        
        self.selection_memory[source_term].append(selection_record)
        
        # Keep only recent selections (limit memory)
        if len(self.selection_memory[source_term]) > 100:
            self.selection_memory[source_term] = self.selection_memory[source_term][-100:]
    
    def _build_context_text(self, context: Dict[str, Any]) -> str:
        """Build context text from context dict"""
        parts = []
        
        if context.get('text'):
            parts.append(context['text'])
        
        if context.get('window'):
            parts.append(context['window'])
        
        if context.get('speaker'):
            parts.append(f"Speaker: {context['speaker']}")
        
        if context.get('term_context'):
            parts.append(f"Context: {context['term_context']}")
        
        return ' '.join(parts)
    
    def predict(
        self,
        source_term: str,
        options: List[str],
        context: Dict[str, Any]
    ) -> Tuple[str, float]:
        """
        Predict best option using ML
        
        Args:
            source_term: Original term to translate
            options: Available translation options
            context: Context dictionary
        
        Returns:
            (selected_option, confidence_score)
        """
        
        # If no training data, return first option with low confidence
        if source_term not in self.selection_memory or not self.selection_memory[source_term]:
            return options[0] if options else "", 0.0
        
        # Build current context
        current_context_text = self._build_context_text(context)
        current_embedding = self.encode(current_context_text)
        
        # Find most similar historical contexts
        similarities = []
        for record in self.selection_memory[source_term]:
            similarity = self.cosine_similarity(current_embedding, record['embedding'])
            similarities.append((record['option'], similarity))
        
        # Score each option based on similarity-weighted votes
        option_scores = defaultdict(float)
        option_counts = defaultdict(int)
        
        for option, similarity in similarities:
            if option in options:
                option_scores[option] += similarity
                option_counts[option] += 1
        
        # No matching options in history
        if not option_scores:
            return options[0] if options else "", 0.0
        
        # Get best option
        best_option = max(option_scores.items(), key=lambda x: x[1])
        
        # Calculate confidence (normalized similarity score)
        total_similarity = sum(option_scores.values())
        confidence = best_option[1] / total_similarity if total_similarity > 0 else 0.0
        
        return best_option[0], confidence
    
    def save_model(self, filepath: Path):
        """Save learned selection patterns"""
        import numpy as np
        
        try:
            # Convert numpy arrays to lists for JSON serialization
            data = {
                'model_type': self.model_type,
                'selection_memory': {}
            }
            
            for term, records in self.selection_memory.items():
                data['selection_memory'][term] = [
                    {
                        'option': r['option'],
                        'context': r['context'],
                        'embedding': r['embedding'].tolist(),
                        'speaker': r['speaker'],
                        'term_context': r['term_context']
                    }
                    for r in records
                ]
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.logger.info(f"✓ Saved ML model to {filepath}")
        
        except Exception as e:
            self.logger.error(f"Error saving ML model: {e}", exc_info=True)
    
    def load_model(self, filepath: Path):
        """Load learned selection patterns"""
        import numpy as np
        
        if not filepath.exists():
            return
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Restore selection memory
            self.selection_memory.clear()
            for term, records in data.get('selection_memory', {}).items():
                self.selection_memory[term] = [
                    {
                        'option': r['option'],
                        'context': r['context'],
                        'embedding': np.array(r['embedding'], dtype=np.float32),
                        'speaker': r['speaker'],
                        'term_context': r['term_context']
                    }
                    for r in records
                ]
            
            total_records = sum(len(records) for records in self.selection_memory.values())
            self.logger.info(f"✓ Loaded ML model from {filepath} ({total_records} training examples)")
        
        except Exception as e:
            self.logger.error(f"Error loading ML model: {e}", exc_info=True)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get ML model statistics"""
        total_records = sum(len(records) for records in self.selection_memory.values())
        
        return {
            'model_type': self.model_type,
            'total_training_examples': total_records,
            'terms_learned': len(self.selection_memory),
            'cache_size': len(self.embedding_cache),
            'avg_examples_per_term': total_records / max(len(self.selection_memory), 1)
        }
    
    def is_available(self) -> bool:
        """Check if ML selector is available and initialized"""
        return self.model is not None or self.model_type == 'tfidf'


# Export for easy import
__all__ = ['MLTermSelector']
