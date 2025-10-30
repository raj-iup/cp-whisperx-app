"""
prompt_assembly.py - Assemble combined prompt from multiple sources

Combines:
- Filename-inferred title/year
- Era lexicon
- TMDB cast/crew
- User prompt (optional)
"""

from pathlib import Path
from typing import Optional
from dataclasses import dataclass
import yaml

from .filename_parser import ParsedFilename
from .era_lexicon import EraLexicon, format_era_context
from .tmdb_enrichment import TMDBMetadata, format_tmdb_context


@dataclass
class AssembledPrompt:
    """Complete assembled prompt with all sources"""
    title: str
    year: Optional[int]
    era_context: str
    tmdb_context: str
    user_prompt: str
    combined_text: str
    combined_yaml: dict


def assemble_prompt(
    parsed_filename: ParsedFilename,
    era_lexicon: Optional[EraLexicon],
    tmdb_metadata: Optional[TMDBMetadata],
    user_prompt: str = ""
) -> AssembledPrompt:
    """
    Assemble combined prompt from all sources

    Args:
        parsed_filename: Parsed filename info
        era_lexicon: Era-specific lexicon
        tmdb_metadata: TMDB metadata
        user_prompt: Optional user-provided prompt

    Returns:
        AssembledPrompt with combined text and YAML
    """
    title = parsed_filename.title
    year = parsed_filename.year

    # Format era context
    era_context = ""
    if era_lexicon:
        era_context = format_era_context(year)

    # Format TMDB context
    tmdb_context = ""
    if tmdb_metadata and tmdb_metadata.found:
        tmdb_context = format_tmdb_context(tmdb_metadata)

    # Build combined text
    sections = []

    sections.append(f"Title: {title}")
    if year:
        sections.append(f"Year: {year}")

    if era_context:
        sections.append(f"\n{era_context}")

    if tmdb_context:
        sections.append(f"\n{tmdb_context}")

    if user_prompt:
        sections.append(f"\nUser context:\n{user_prompt}")

    combined_text = "\n".join(sections)

    # Build YAML representation
    combined_yaml = {
        "title": title,
        "year": year,
        "era": era_lexicon.era_name if era_lexicon else None,
        "tmdb_found": tmdb_metadata.found if tmdb_metadata else False,
        "cast_count": len(tmdb_metadata.cast) if tmdb_metadata else 0,
        "crew_count": len(tmdb_metadata.crew) if tmdb_metadata else 0
    }

    return AssembledPrompt(
        title=title,
        year=year,
        era_context=era_context,
        tmdb_context=tmdb_context,
        user_prompt=user_prompt,
        combined_text=combined_text,
        combined_yaml=combined_yaml
    )


def write_prompt_files(
    output_dir: Path,
    basename: str,
    assembled_prompt: AssembledPrompt
):
    """
    Write prompt files to output directory

    Creates:
    - <basename>.initial_prompt.txt (just title/year)
    - <basename>.combined.initial_prompt.txt (full text)
    - <basename>.combined.initial_prompt.md (YAML + prompt)

    Args:
        output_dir: Output directory
        basename: Base filename
        assembled_prompt: Assembled prompt
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initial prompt (just title/year)
    initial_prompt = f"Title: {assembled_prompt.title}"
    if assembled_prompt.year:
        initial_prompt += f"\nYear: {assembled_prompt.year}"

    initial_file = output_dir / f"{basename}.initial_prompt.txt"
    with open(initial_file, "w") as f:
        f.write(initial_prompt)

    # Combined prompt (full text)
    combined_file = output_dir / f"{basename}.combined.initial_prompt.txt"
    with open(combined_file, "w") as f:
        f.write(assembled_prompt.combined_text)

    # Combined prompt with YAML metadata
    md_file = output_dir / f"{basename}.combined.initial_prompt.md"
    with open(md_file, "w") as f:
        f.write("---\n")
        f.write(yaml.dump(assembled_prompt.combined_yaml, default_flow_style=False))
        f.write("---\n\n")
        f.write(assembled_prompt.combined_text)
