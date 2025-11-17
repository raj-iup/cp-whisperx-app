# Quick Reference: Two-Step Transcription

## TL;DR

When you specify a target language with `--transcribe`, you now get **BOTH** language files:

```bash
./prepare-job.sh movie.mp4 --transcribe -s hi -t en
```

**Output**:
- ✅ Hindi files (original)
- ✅ English files (translated)

---

## File Naming

| File Type | Source (Hindi) | Target (English) |
|-----------|----------------|------------------|
| Subtitles | `job.srt` | `job-English.srt` |
| Transcript | `job.transcript.txt` | `job.transcript-English.txt` |
| Segments | `job.segments.json` | `job-English.segments.json` |
| Full Result | `job.whisperx.json` | `job-English.whisperx.json` |

---

## Quick Commands

### Generate Both Languages
```bash
./prepare-job.sh "in/movie.mp4" -s hi -t en --transcribe
```

### Source Only (No Translation)
```bash
./prepare-job.sh "in/movie.mp4" -s hi --transcribe
```

### With Dual VAD + Clip
```bash
./prepare-job.sh "in/movie.mp4" \
  --transcribe \
  --enable-silero-vad \
  --enable-pyannote-vad \
  -s hi -t en \
  --start-time 00:10:00 \
  --end-time 00:15:00
```

---

## Verify Output

```bash
# Check both sets exist
ls -lh out/.../06_asr/*.srt
ls -lh out/.../06_asr/*.transcript.txt

# Compare source vs target
diff out/.../06_asr/job.transcript.txt \
     out/.../06_asr/job.transcript-English.txt
```

---

## Performance

- **With translation**: ~5-6 minutes (5-min clip)
- **Without translation**: ~4 minutes (5-min clip)
- **Trade-off**: 20-30% longer, but get both languages

---

## When to Use

✅ **Use Two-Step When**:
- Need both original and translated subtitles
- Quality verification required
- Professional localization workflow
- Multi-language distribution planned

❌ **Skip Translation When**:
- Only need source language
- Fast testing
- No international distribution

---

## Files You Get

### Source Language Files
```
job.srt                    # For original language viewers
job.transcript.txt         # Original dialogue text
job.segments.json          # Original segments with timing
job.whisperx.json          # Full original result
```

### Target Language Files
```
job-English.srt            # For international viewers
job.transcript-English.txt # Translated dialogue text
job-English.segments.json  # Translated segments with timing
job-English.whisperx.json  # Full translated result
```

---

## Common Questions

**Q: Do I need both files?**  
A: Depends. For professional work: yes. For quick tests: probably not.

**Q: Can I skip the source files?**  
A: No, they're generated first automatically.

**Q: How much longer does it take?**  
A: ~20-30% longer, but you get twice the output.

**Q: Can I add more languages later?**  
A: Yes! Reuse the source files with `--translate-only` mode (future feature).

---

