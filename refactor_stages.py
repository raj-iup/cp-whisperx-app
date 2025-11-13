#!/usr/bin/env python3
"""
Automated stage refactoring script.
Helps refactor existing stage scripts to use the new StageIO pattern.
"""
import sys
import re
from pathlib import Path
from typing import Dict, List

# Stage definitions with their primary input/output files
STAGE_CONFIG = {
    "demux": {
        "description": "Extract audio from video file",
        "inputs": [],
        "outputs": ["audio.wav"],
        "primary_output": "audio.wav"
    },
    "tmdb": {
        "description": "Fetch cast and crew metadata",
        "inputs": [],
        "outputs": ["tmdb_data.json"],
        "primary_output": "tmdb_data.json"
    },
    "pre_ner": {
        "description": "Pre-ASR named entity recognition",
        "inputs": ["tmdb_data.json"],
        "outputs": ["entities.txt", "ner_annotated.json", "entity_frequencies.json"],
        "primary_output": "ner_annotated.json"
    },
    "silero_vad": {
        "description": "Voice activity detection (Silero)",
        "inputs": ["audio.wav"],
        "outputs": ["vad_segments.json"],
        "primary_output": "vad_segments.json"
    },
    "pyannote_vad": {
        "description": "Voice activity detection (PyAnnote)",
        "inputs": ["audio.wav"],
        "outputs": ["vad_segments.json"],
        "primary_output": "vad_segments.json"
    },
    "diarization": {
        "description": "Speaker diarization",
        "inputs": ["audio.wav", "vad_segments.json"],
        "outputs": ["diarization.json", "speaker_segments.json"],
        "primary_output": "diarization.json"
    },
    "asr": {
        "description": "Automatic speech recognition",
        "inputs": ["audio.wav", "diarization.json", "tmdb_data.json"],
        "outputs": ["transcription.json", "word_timestamps.json"],
        "primary_output": "transcription.json"
    },
    "glossary_builder": {
        "description": "Build translation glossary",
        "inputs": ["transcription.json", "tmdb_data.json", "ner_annotated.json"],
        "outputs": ["glossary.json"],
        "primary_output": "glossary.json"
    },
    "second_pass_translation": {
        "description": "Second-pass translation refinement",
        "inputs": ["transcription.json", "glossary.json"],
        "outputs": ["translation.json"],
        "primary_output": "translation.json"
    },
    "lyrics_detection": {
        "description": "Detect and classify lyrics segments",
        "inputs": ["audio.wav", "transcription.json"],
        "outputs": ["lyrics_segments.json", "audio_features.json"],
        "primary_output": "lyrics_segments.json"
    },
    "post_ner": {
        "description": "Post-ASR named entity refinement",
        "inputs": ["transcription.json", "ner_annotated.json"],
        "outputs": ["entities_final.txt", "ner_final.json"],
        "primary_output": "ner_final.json"
    },
    "subtitle_gen": {
        "description": "Generate subtitle files",
        "inputs": ["transcription.json", "lyrics_segments.json"],
        "outputs": ["subtitles.srt", "subtitles.ass"],
        "primary_output": "subtitles.srt"
    },
    "mux": {
        "description": "Mux subtitles with video",
        "inputs": ["subtitles.srt"],
        "outputs": ["output.mkv"],
        "primary_output": "output.mkv"
    },
    "finalize": {
        "description": "Finalize and organize outputs",
        "inputs": [],
        "outputs": ["final_manifest.json"],
        "primary_output": "final_manifest.json"
    }
}


def print_refactoring_summary():
    """Print summary of stages that need refactoring."""
    print("=" * 80)
    print("STAGE REFACTORING STATUS")
    print("=" * 80)
    print()
    
    scripts_dir = Path("scripts")
    
    for stage_name, config in STAGE_CONFIG.items():
        script_file = scripts_dir / f"{stage_name}.py"
        
        if not script_file.exists():
            status = "❌ MISSING"
        else:
            content = script_file.read_text()
            if "from shared.stage_utils import StageIO" in content:
                status = "✅ REFACTORED"
            else:
                status = "⚠️  NEEDS REFACTORING"
        
        print(f"{status:20} {stage_name:20} - {config['description']}")
    
    print()
    print("=" * 80)


def generate_stage_template(stage_name: str) -> str:
    """Generate refactored stage code template."""
    config = STAGE_CONFIG.get(stage_name)
    if not config:
        return None
    
    inputs = config.get('inputs', [])
    outputs = config.get('outputs', [])
    description = config.get('description', '')
    
    # Generate input loading code
    input_code = []
    for input_file in inputs:
        var_name = input_file.replace('.', '_').replace('-', '_')
        if input_file.endswith('.json'):
            input_code.append(f"        {var_name}_data = stage_io.load_json('{input_file}')")
            input_code.append(f"        logger.debug(f'Loaded {input_file}: {{len({var_name}_data)}} items')")
        else:
            input_code.append(f"        {var_name}_path = stage_io.get_input_path('{input_file}')")
            input_code.append(f"        if not {var_name}_path.exists():")
            input_code.append(f"            logger.error(f'Input not found: {{{var_name}_path}}')")
            input_code.append(f"            return 1")
            input_code.append(f"        logger.info(f'Input: {{{var_name}_path}}')")
    
    input_section = "\n".join(input_code) if input_code else "        # No inputs from previous stages"
    
    # Generate output saving code
    output_code = []
    for i, output_file in enumerate(outputs):
        var_name = f"output_{i+1}"
        if output_file.endswith('.json'):
            output_code.append(f"        # Save {output_file}")
            output_code.append(f"        {var_name} = {{}}")
            output_code.append(f"        stage_io.save_json({var_name}, '{output_file}')")
        else:
            output_code.append(f"        # Save {output_file}")
            output_code.append(f"        {var_name}_path = stage_io.get_output_path('{output_file}')")
            output_code.append(f"        # Write your output to {var_name}_path")
    
    output_section = "\n".join(output_code) if output_code else "        # No specific outputs"
    
    template = f'''#!/usr/bin/env python3
"""
{stage_name.upper()} stage: {description}
"""
import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.stage_utils import StageIO, get_stage_logger
from shared.config import load_config


def main():
    """Main entry point for {stage_name} stage."""
    # Initialize stage I/O
    stage_io = StageIO("{stage_name}")
    logger = get_stage_logger("{stage_name}", log_level="DEBUG")
    
    logger.info("=" * 60)
    logger.info("{stage_name.upper()} STAGE: {description}")
    logger.info("=" * 60)
    
    # Load configuration
    config_path = os.environ.get('CONFIG_PATH', 'config/.env.pipeline')
    logger.debug(f"Loading configuration from: {{config_path}}")
    
    try:
        config = load_config(config_path)
    except Exception as e:
        logger.error(f"Failed to load configuration: {{e}}")
        return 1
    
    # Load inputs from previous stages
    try:
{input_section}
    except Exception as e:
        logger.error(f"Failed to load inputs: {{e}}", exc_info=True)
        return 1
    
    # Process stage logic
    logger.info("Processing...")
    
    try:
        # TODO: Implement stage-specific processing logic
        result = process_{stage_name}(config, logger)
        
    except Exception as e:
        logger.error(f"Processing failed: {{e}}", exc_info=True)
        return 1
    
    # Save outputs
    logger.info("Saving outputs...")
    
    try:
{output_section}
        
        # Save metadata
        metadata = {{
            'status': 'completed',
            # Add stage-specific metadata
        }}
        stage_io.save_metadata(metadata)
        logger.debug("Metadata saved")
        
    except Exception as e:
        logger.error(f"Failed to save outputs: {{e}}")
        return 1
    
    logger.info("=" * 60)
    logger.info("{stage_name.upper()} STAGE COMPLETED")
    logger.info("=" * 60)
    
    return 0


def process_{stage_name}(config, logger):
    """
    Process {stage_name} stage logic.
    
    Args:
        config: Configuration object
        logger: Logger instance
        
    Returns:
        Processed result
    """
    logger.debug("Processing {stage_name}...")
    
    # TODO: Implement stage-specific logic
    result = {{}}
    
    return result


if __name__ == "__main__":
    sys.exit(main())
'''
    
    return template


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "status":
            print_refactoring_summary()
        
        elif command == "template":
            if len(sys.argv) < 3:
                print("Usage: python refactor_stages.py template <stage_name>")
                return 1
            
            stage_name = sys.argv[2]
            template = generate_stage_template(stage_name)
            
            if template:
                print(template)
            else:
                print(f"Unknown stage: {stage_name}")
                return 1
        
        elif command == "help":
            print("Stage Refactoring Helper")
            print()
            print("Commands:")
            print("  status           - Show refactoring status of all stages")
            print("  template <stage> - Generate template code for a stage")
            print("  help             - Show this help")
            print()
            print("Examples:")
            print("  python refactor_stages.py status")
            print("  python refactor_stages.py template pre_ner")
        
        else:
            print(f"Unknown command: {command}")
            print("Run 'python refactor_stages.py help' for usage")
            return 1
    else:
        print_refactoring_summary()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
