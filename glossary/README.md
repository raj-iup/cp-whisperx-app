# Hinglish Glossary System

This directory contains the Hinglish→English glossary and per-film prompt files for context-aware subtitle translation.

## Structure

```
glossary/
├── hinglish_master.tsv          # Main glossary (Hinglish → English mappings)
├── prompts/                     # Per-film context prompts
│   ├── jaane_tu_2008.txt
│   ├── dil_chahta_hai_2001.txt
│   └── ...
└── README.md                    # This file
```

## Glossary Format (TSV)

**Columns:**
- `source`: Hinglish term (e.g., "yaar", "bhai", "ji")
- `preferred_english`: Pipe-separated English options (e.g., "dude|man|buddy")
- `notes`: Usage guidance
- `context`: Context category (casual, formal, honorific, etc.)

**Example:**
```tsv
source	preferred_english	notes	context
yaar	dude|man|buddy	Use "dude" for young male; "man" neutral	casual
ji	sir|ma'am|	Honorific suffix; omit if repetitive	honorific
```

## How It Works

1. **Glossary Loader** (`shared/glossary.py`)
   - Loads TSV file
   - Creates term mapping dictionary
   - Provides `apply()` method for text substitution

2. **Subtitle Generation Integration** (`docker/subtitle-gen/subtitle_gen.py`)
   - Checks if glossary is enabled (`GLOSSARY_ENABLED=true`)
   - Loads glossary if available
   - Applies term substitution to each subtitle segment
   - Selects first option by default (can be enhanced with context awareness)

3. **Configuration** (`.env` file)
   ```bash
   GLOSSARY_ENABLED=true
   GLOSSARY_PATH=glossary/hinglish_master.tsv
   ```

## Usage Examples

### Basic Term Substitution
```python
from shared.glossary import HinglishGlossary

glossary = HinglishGlossary("glossary/hinglish_master.tsv")
text = "Hey yaar, kya scene hai?"
result = glossary.apply(text)
# Result: "Hey dude, what's up?"
```

### Context-Aware Selection
```python
# Future enhancement: pass context for term selection
text = "Yes ji, I understand"
result = glossary.apply(text, context="formal")
# Result: "Yes sir, I understand"
```

## Per-Film Prompts

Create prompt files for each film to provide:
- Character names and relationships
- Film-specific slang or catchphrases
- Location/setting context
- Tone guidance

**Example** (`prompts/jaane_tu_2008.txt`):
```
Film: Jaane Tu Ya Jaane Na (2008)
Setting: Mumbai, friend group of college students
Tone: Casual, youth-oriented, frequent Hinglish code-switching

Characters:
- Jai Rathod (male, main): Non-violent, gentle
- Aditi Wadia (female, main): Bold, outspoken
- Rotlu, Shaleen, Jiggy (friends): Casual banter

Key Terms:
- "yaar" → "dude" (very frequent among friends)
- "bhai" → "bro" (casual friend context)
- "ji" → usually omit or "sir/ma'am" (rare in friend group)

Catchphrases:
- "Rats" (Jai's nickname for Aditi)
- "Meow" (Aditi's nickname for Jai)
```

## Adding New Terms

1. Edit `hinglish_master.tsv`
2. Add row with: source, preferred translations (pipe-separated), notes, context
3. Save and test with sample text

## Context Categories

- `casual`: Informal conversation (yaar, bhai, bindaas)
- `formal`: Formal settings (ji when honorific, proper titles)
- `honorific`: Respectful terms (ji, beta, uncle/aunty)
- `discourse`: Conversation markers (acha, matlab, suno)
- `exclamation`: Reactions (arey, arre, oho)
- `slang`: Colloquialisms (jugaad, timepass, mast)
- `mumbai-slang`: Mumbai-specific terms (apun, bhidu, tapori)
- `agreement/disagreement`: Yes/no variants
- `intensifier`: Emphasis words (bilkul, ekdum, full)

## Best Practices

1. **First option is default**: Put most common/neutral translation first
2. **Context matters**: Use notes to guide when multiple options apply
3. **Preserve cultural terms**: Some terms (uncle, aunty) often kept in English
4. **Avoid over-translation**: Some exclamations better kept minimal
5. **Test iteratively**: Run on sample scenes, refine based on results

## Future Enhancements

- [ ] Context-aware term selection (analyze surrounding text)
- [ ] ML-based term selection based on character/scene
- [ ] Per-character speaking style (some use more English, some more Hindi)
- [ ] Regional variant support (Mumbai vs Delhi vs regional slang)
- [ ] Frequency-based term learning (track which mappings work best)

## Configuration Reference

### Environment Variables
```bash
# Enable/disable glossary
GLOSSARY_ENABLED=true

# Path to main glossary file
GLOSSARY_PATH=glossary/hinglish_master.tsv

# Path to per-film prompts (optional)
FILM_PROMPT_PATH=glossary/prompts/{film_title}_{year}.txt

# Term selection strategy
GLOSSARY_STRATEGY=first|context|ml  # Default: first
```

### Integration Points

1. **Subtitle Generation** (`docker/subtitle-gen/subtitle_gen.py`)
   - Applied after ASR/translation
   - Before CPS enforcement and formatting

2. **Post-NER** (`docker/post-ner/post_ner.py`)
   - Could be integrated here for entity-aware substitution

3. **Second-Pass Translation** (`docker/second-pass-translation/`)
   - Could use glossary as constraints for NLLB

## Maintenance

- Review and update glossary after each film processing
- Add new terms discovered in specific films
- Track term frequency to optimize default selections
- Collect feedback from QA reviewers on term choices

## Credits

Based on IMPROVEMENT-PLAN.md Step 8: Hinglish→English Glossary
