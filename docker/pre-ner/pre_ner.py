#!/usr/bin/env python3
"""
Pre-ASR NER Step
Extracts named entities from TMDB metadata to enrich ASR prompts.
Outputs to: out/{movie}/entities/
"""
import sys
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict

sys.path.insert(0, '/app/shared')
from config import load_config
from logger import setup_logger
from utils import save_json, load_json, get_movie_dir


def extract_entities_from_text(text: str, nlp, logger, confidence_threshold: float = 0.0) -> List[Dict]:
    """
    Extract named entities from text using spaCy.
    
    Args:
        text: Text to analyze
        nlp: spaCy NLP model
        logger: Logger instance
        confidence_threshold: Minimum confidence score (0.0-1.0)
    
    Returns:
        List of entity dicts with text, label, start, end
    """
    if not text or not text.strip():
        return []
    
    try:
        doc = nlp(text)
        entities = []
        
        for ent in doc.ents:
            # Get confidence score if available (transformer models)
            if hasattr(ent, '_') and hasattr(ent._, 'score'):
                confidence = float(ent._.score)
            else:
                confidence = 1.0  # Base models don't provide confidence
            
            # Filter by confidence threshold
            if confidence >= confidence_threshold:
                entities.append({
                    "text": ent.text,
                    "label": ent.label_,
                    "start": ent.start_char,
                    "end": ent.end_char,
                    "confidence": confidence
                })
        
        return entities
        
    except Exception as e:
        logger.error(f"Error extracting entities: {e}")
        return []


def extract_from_tmdb_metadata(metadata: Dict, nlp, logger, confidence_threshold: float = 0.0) -> Dict[str, List[str]]:
    """
    Extract all entities from TMDB metadata.
    
    Args:
        metadata: TMDB metadata dict
        nlp: spaCy NLP model
        logger: Logger instance
        confidence_threshold: Minimum confidence score for NER entities
    
    Returns:
        Dict mapping entity types to lists of entity texts
    """
    entities_by_type = defaultdict(set)
    
    # Extract from cast (PERSON entities)
    if metadata.get('cast'):
        for person in metadata['cast'][:20]:  # Top 20 cast
            if person.get('name'):
                entities_by_type['PERSON'].add(person['name'])
                # Also add character names
                if person.get('character'):
                    char_name = person['character'].split('/')[0].strip()  # Handle multiple characters
                    if char_name and not char_name.startswith('['):
                        entities_by_type['PERSON'].add(char_name)
    
    # Extract from crew (PERSON entities)
    if metadata.get('crew'):
        for person in metadata['crew']:
            if person.get('name'):
                entities_by_type['PERSON'].add(person['name'])
    
    # Extract from overview using NER
    if metadata.get('overview'):
        overview_entities = extract_entities_from_text(metadata['overview'], nlp, logger, confidence_threshold)
        for ent in overview_entities:
            entities_by_type[ent['label']].add(ent['text'])
    
    # Extract from tagline using NER
    if metadata.get('tagline'):
        tagline_entities = extract_entities_from_text(metadata['tagline'], nlp, logger, confidence_threshold)
        for ent in tagline_entities:
            entities_by_type[ent['label']].add(ent['text'])
    
    # Extract production countries (GPE entities)
    if metadata.get('production_countries'):
        for country in metadata['production_countries']:
            entities_by_type['GPE'].add(country)
    
    # Extract keywords (potential entities)
    if metadata.get('keywords'):
        for keyword in metadata['keywords']:
            # Keywords might contain locations or organizations
            keyword_entities = extract_entities_from_text(keyword, nlp, logger, confidence_threshold)
            for ent in keyword_entities:
                entities_by_type[ent['label']].add(ent['text'])
    
    # Convert sets to sorted lists
    result = {}
    for entity_type, entity_set in entities_by_type.items():
        result[entity_type] = sorted(list(entity_set))
    
    return result


def generate_ner_enhanced_prompt(entities: Dict[str, List[str]], metadata: Dict, logger, entity_types: List[str]) -> str:
    """
    Generate NER-enhanced prompt for WhisperX.
    
    Args:
        entities: Extracted entities by type
        metadata: Original TMDB metadata
        logger: Logger instance
        entity_types: List of entity types to include
    
    Returns:
        Enhanced prompt string
    """
    prompt_parts = []
    
    # Title and basic info
    if metadata.get('title'):
        year = metadata.get('release_date', '')[:4] if metadata.get('release_date') else ''
        prompt_parts.append(f"Title: {metadata['title']}")
        if year:
            prompt_parts.append(f"Year: {year}")
    
    # Genres
    if metadata.get('genres'):
        prompt_parts.append(f"Genres: {', '.join(metadata['genres'][:3])}")
    
    # Named Entities - use configured entity types
    entity_labels = {
        'PERSON': 'Characters & Cast',
        'GPE': 'Locations',
        'LOC': 'Places',
        'ORG': 'Organizations',
        'FAC': 'Facilities',
        'NORP': 'Nationalities',
        'EVENT': 'Events',
        'WORK_OF_ART': 'Works'
    }
    
    for entity_type in entity_types:
        if entities.get(entity_type):
            entity_list = entities[entity_type][:15 if entity_type == 'PERSON' else 5]
            label = entity_labels.get(entity_type, entity_type)
            prompt_parts.append(f"{label}: {', '.join(entity_list)}")
    
    # Keywords/themes
    if metadata.get('keywords'):
        prompt_parts.append(f"Themes: {', '.join(metadata['keywords'][:5])}")
    
    # Context from overview (first sentence)
    if metadata.get('overview'):
        first_sentence = metadata['overview'].split('.')[0].strip()
        if len(first_sentence) < 150:
            prompt_parts.append(f"Context: {first_sentence}")
    
    prompt = "\n".join(prompt_parts)
    
    logger.info(f"Generated enhanced prompt with {len(prompt)} characters")
    
    return prompt


def main():
    """Main entry point."""
    # Validate arguments BEFORE setting up logger (though it's optional here)
    # Still validate early to avoid unnecessary config loading
    if len(sys.argv) < 2:
        # For pre-ner, argument is somewhat optional but let's be explicit
        # Load config to check if we have output_root
        try:
            config = load_config()
            if not config.output_root:
                print("ERROR: Usage: pre_ner.py <movie_dir>", file=sys.stderr)
                sys.exit(1)
        except:
            print("ERROR: Usage: pre_ner.py <movie_dir>", file=sys.stderr)
            sys.exit(1)
    else:
        config = load_config()
    
    logger = setup_logger(
        "pre-ner",
        log_level=config.log_level,
        log_format=config.log_format,
        log_to_console=config.log_to_console,
        log_to_file=config.log_to_file,
        log_dir=config.log_root
    )
    
    logger.info("Starting Pre-ASR NER")
    
    # Get movie directory from command line or config
    if len(sys.argv) >= 2:
        movie_dir = Path(sys.argv[1])
        logger.info(f"Using movie directory from argument: {movie_dir}")
    else:
        # Always use output_root directly when it's set (should be job-specific)
        movie_dir = Path(config.output_root)
        logger.info(f"Using output_root as movie directory: {movie_dir}")
    
    logger.info(f"Movie directory: {movie_dir}")
    
    # Load TMDB metadata
    metadata_file = movie_dir / "metadata" / "tmdb_data.json"
    
    # Helper function to create empty entities
    def create_empty_entities(reason: str):
        logger.warning(reason)
        logger.warning("Pre-NER will run with empty entity list")
        
        # Create empty entities output
        pre_ner_dir = movie_dir / "pre_ner"
        pre_ner_dir.mkdir(exist_ok=True, parents=True)
        
        entities_file = pre_ner_dir / "entities.json"
        empty_data = {
            "entities": [],
            "entities_by_type": {},
            "total_entities": 0,
            "source": f"none - {reason}"
        }
        
        with open(entities_file, 'w', encoding='utf-8') as f:
            import json
            json.dump(empty_data, f, indent=2, ensure_ascii=False)
            f.flush()
            import os
            os.fsync(f.fileno())
        
        logger.info(f"Empty entity file created: {entities_file}")
        sys.exit(0)
    
    if not metadata_file.exists():
        create_empty_entities(f"TMDB metadata not found: {metadata_file}")
    
    metadata = load_json(metadata_file)
    if not metadata:
        create_empty_entities(f"TMDB metadata file is empty or invalid: {metadata_file}")
    
    logger.info(f"Loaded metadata for: {metadata.get('title', 'Unknown')}")
    
    # Get configuration parameters
    model_name = getattr(config, 'pre_ner_model', 'en_core_web_sm')
    confidence_threshold = float(getattr(config, 'pre_ner_confidence_threshold', 0.0))
    entity_types_str = getattr(config, 'pre_ner_entity_types', 'PERSON,ORG,GPE,LOC,FAC')
    entity_types = [t.strip() for t in entity_types_str.split(',')]
    
    logger.info(f"Configuration:")
    logger.info(f"  Model: {model_name}")
    logger.info(f"  Confidence threshold: {confidence_threshold}")
    logger.info(f"  Entity types: {entity_types}")
    
    # Load spaCy model
    logger.info(f"Loading spaCy model: {model_name}...")
    try:
        import spacy
        nlp = spacy.load(model_name)
        logger.info(f"spaCy model loaded: {model_name}")
    except Exception as e:
        logger.error(f"Failed to load spaCy model '{model_name}': {e}")
        logger.error(f"Make sure the model is installed: python -m spacy download {model_name}")
        sys.exit(1)
    
    # Extract entities
    logger.info("Extracting named entities...")
    entities = extract_from_tmdb_metadata(metadata, nlp, logger, confidence_threshold)
    
    # Log statistics
    total_entities = sum(len(ents) for ents in entities.values())
    logger.info(f"Extracted {total_entities} entities across {len(entities)} types")
    for entity_type, entity_list in entities.items():
        logger.info(f"  {entity_type}: {len(entity_list)} entities")
    
    # Save entities
    entities_dir = movie_dir / "entities"
    entities_dir.mkdir(parents=True, exist_ok=True)
    
    entities_file = entities_dir / "pre_ner.json"
    
    output_data = {
        "source": "pre_asr_ner",
        "tmdb_id": metadata.get('tmdb_id'),
        "movie_title": metadata.get('title'),
        "entities_by_type": entities,
        "total_entities": total_entities,
        "entity_counts": {k: len(v) for k, v in entities.items()}
    }
    
    save_json(output_data, entities_file)
    logger.info(f"Entities saved: {entities_file}")
    
    # Generate enhanced prompt using configured entity types
    enhanced_prompt = generate_ner_enhanced_prompt(entities, metadata, logger, entity_types)
    
    prompt_dir = movie_dir / "prompts"
    prompt_dir.mkdir(parents=True, exist_ok=True)
    
    prompt_file = prompt_dir / "ner_enhanced_prompt.txt"
    with open(prompt_file, 'w', encoding='utf-8') as f:
        f.write(enhanced_prompt)
    
    logger.info(f"Enhanced prompt saved: {prompt_file}")
    logger.debug(f"Prompt preview:\n{enhanced_prompt[:300]}...")
    
    logger.info("Pre-ASR NER completed successfully")
    sys.exit(0)


if __name__ == "__main__":
    main()
