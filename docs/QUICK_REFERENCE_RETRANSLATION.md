# Quick Reference: SRT Re-translation

## Problem
WhisperX translation produces hallucinated/incomplete English subtitles with missing dialogue.

## Solution
Use Google Translate API to re-translate Hinglish SRT files to English.

## Quick Usage

```bash
# Re-translate a job's subtitles
./retranslate-subtitles.sh out/2025/11/16/1/JOBID

# Direct script usage
python scripts/retranslate_srt.py input.srt -o output-English.srt
```

## Output Files

- `{basename}-English-Retranslated.srt` - New translation
- `{basename}-English.srt.backup` - Backup of original
- Original remains unchanged

## Replace Original (if desired)

```bash
cp out/.../06_asr/file-English-Retranslated.srt \
   out/.../06_asr/file-English.srt
```

## When to Use

- ✓ Missing dialogue in English translation
- ✓ Repeated words/phrases (hallucinations)
- ✓ Segment count mismatch
- ✓ Nonsensical translations

## Performance

- ~200-400 subtitles per minute
- Typical full movie: ~5 minutes
- File size typically smaller (no hallucinations)

## Files

- **Script**: `scripts/retranslate_srt.py`
- **Wrapper**: `retranslate-subtitles.sh` or `.ps1`
- **Docs**: `docs/SRT_RETRANSLATION.md`
- **Summary**: `RETRANSLATION_FIX_SUMMARY.md`

## Installation

```bash
pip install deep-translator
```

Auto-installed when using wrapper script.
