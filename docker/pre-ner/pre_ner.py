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


def extract_entities_from_text(text: str, nlp, logger) -> List[Dict]:
    """
    Extract named entities from text using spaCy.
    
    Args:
        text: Text to analyze
        nlp: spaCy NLP model
        logger: Logger instance
    
    Returns:
        List of entity dicts with text, label, start, end
    """
    if not text or not text.strip():
        return []
    
    try:
        doc = nlp(text)
        entities = []
        
        for ent in doc.ents:
            entities.append({
                "text": ent.text,
                "label": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char,
                "confidence": 1.0  # spaCy doesn't provide confidence for base models
            })
        
        return entities
        
    except Exception as e:
        logger.error(f"Error extracting entities: {e}")
        return []


def extract_from_tmdb_metadata(metadata: Dict, nlp, logger) -> Dict[str, List[str]]:
    """
    Extract all entities from TMDB metadata.
    
    Args:
        metadata: TMDB metadata dict
        nlp: spaCy NLP model
        logger: Logger instance
    
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
        overview_entities = extract_entities_from_text(metadata['overview'], nlp, logger)
        for ent in overview_entities:
            entities_by_type[ent['label']].add(ent['text'])
    
    # Extract from tagline using NER
    if metadata.get('tagline'):
        tagline_entities = extract_entities_from_text(metadata['tagline'], nlp, logger)
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
            keyword_entities = extract_entities_from_text(keyword, nlp, logger)
            for ent in keyword_entities:
                entities_by_type[ent['label']].add(ent['text'])
    
    # Convert sets to sorted lists
    result = {}
    for entity_type, entity_set in entities_by_type.items():
        result[entity_type] = sorted(list(entity_set))
    
    return result


def generate_ner_enhanced_prompt(entities: Dict[str, List[str]], metadata: Dict, logger) -> str:
    """
    Generate NER-enhanced prompt for WhisperX.
    
    Args:
        entities: Extracted entities by type
        metadata: Original TMDB metadata
        logger: Logger instance
    
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
    
    # Named Entities
    if entities.get('PERSON'):
        # Top 15 person names
        people = entities['PERSON'][:15]
        prompt_parts.append(f"Characters & Cast: {', '.join(people)}")
    
    if entities.get('GPE'):
        # Locations (countries, cities)
        locations = entities['GPE'][:5]
        prompt_parts.append(f"Locations: {', '.join(locations)}")
    
    if entities.get('LOC'):
        # Specific places
        places = entities['LOC'][:5]
        prompt_parts.append(f"Places: {', '.join(places)}")
    
    if entities.get('ORG'):
        # Organizations
        orgs = entities['ORG'][:5]
        prompt_parts.append(f"Organizations: {', '.join(orgs)}")
    
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
        # Movie title provided
        title = sys.argv[1]
        year = sys.argv[2] if len(sys.argv) >= 3 else None
        temp_filename = f"{title} {year}.mp4" if year else f"{title}.mp4"
        movie_dir = get_movie_dir(Path(temp_filename), Path(config.output_root))
    elif config.input_file:
        input_path = Path(config.input_file)
        movie_dir = get_movie_dir(input_path, Path(config.output_root))
    else:
        logger.error("No movie specified. Usage: pre_ner.py <title> [year]")
        sys.exit(1)
    
    logger.info(f"Movie directory: {movie_dir}")
    
    # Load TMDB metadata
    metadata_file = movie_dir / "metadata" / "tmdb_data.json"
    if not metadata_file.exists():
        logger.warning(f"TMDB metadata not found: {metadata_file}")
        logger.warning("Pre-NER will run with empty entity list")
        
        # Create empty entities output
        pre_ner_dir = movie_dir / "pre_ner"
        pre_ner_dir.mkdir(exist_ok=True, parents=True)
        
        entities_file = pre_ner_dir / "entities.json"
        empty_data = {
            "entities": [],
            "entities_by_type": {},
            "total_entities": 0,
            "source": "none - TMDB metadata unavailable"
        }
        
        with open(entities_file, 'w', encoding='utf-8') as f:
            import json
            json.dump(empty_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Empty entity file created: {entities_file}")
        sys.exit(0)
    
    metadata = load_json(metadata_file)
    logger.info(f"Loaded metadata for: {metadata.get('title', 'Unknown')}")
    
    # Load spaCy model
    logger.info("Loading spaCy model...")
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        logger.info("spaCy model loaded")
    except Exception as e:
        logger.error(f"Failed to load spaCy model: {e}")
        sys.exit(1)
    
    # Extract entities
    logger.info("Extracting named entities...")
    entities = extract_from_tmdb_metadata(metadata, nlp, logger)
    
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
    
    # Generate enhanced prompt
    enhanced_prompt = generate_ner_enhanced_prompt(entities, metadata, logger)
    
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
