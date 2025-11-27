# CPS Violation Fixes - Quick Reference

## What Changed?

Your subtitle generator now automatically fixes CPS (Characters Per Second) violations using **three intelligent strategies**:

1. **Merge** short consecutive subtitles from same speaker
2. **Extend** subtitle duration by using gaps between segments
3. **Split** long subtitles at natural break points (punctuation)

## Default Settings (Already Configured)

```bash
CPS_ENFORCEMENT=true        # Enable CPS fixing
CPS_TARGET=15.0            # Warning threshold
CPS_HARD_CAP=17.0          # Violation threshold (will fix)
CPS_MAX_GAP=2.0            # Max seconds to extend into gaps
CPS_ALLOW_SPLIT=true       # Allow splitting subtitles
SUBTITLE_MERGE_SHORT=true  # Merge consecutive short subtitles
```

## Quick Adjustments

### Problem: Still seeing violations?

**Solution 1: Allow more gap usage**
```bash
CPS_MAX_GAP=3.0  # or 4.0
```

**Solution 2: Increase hard cap slightly**
```bash
CPS_HARD_CAP=19.0  # or 20.0 for fast-paced dialogue
```

### Problem: Subtitles split too much?

**Solution: Disable splitting**
```bash
CPS_ALLOW_SPLIT=false
CPS_HARD_CAP=19.0  # Accept slightly higher CPS
```

### Problem: Timing feels off?

**Solution: Reduce aggressiveness**
```bash
CPS_MAX_GAP=1.0           # Less extension
SUBTITLE_GAP_TOLERANCE=1.0 # Less merging
```

## What to Expect in Logs

```
[subtitle-gen] [INFO] Merging consecutive short subtitles...
[subtitle-gen] [INFO] After merging: 1850 subtitles (merged 222 segments)
[subtitle-gen] [INFO] Fixing CPS violations with multiple strategies...
[subtitle-gen] [INFO]   Extended 145 segments to fix CPS
[subtitle-gen] [INFO]   Split 38 segments to fix CPS
[subtitle-gen] [INFO] After CPS fixes: 1888 subtitles (net change: 38)
[subtitle-gen] [INFO] Final CPS compliance check...
[subtitle-gen] [INFO] CPS Analysis:
[subtitle-gen] [INFO]   Average CPS: 13.45
[subtitle-gen] [INFO]   Range: 2.10 - 16.89
[subtitle-gen] [INFO] ✓ All subtitles within CPS limits
```

## Common Presets

### Strict (Maximum Readability)
```bash
CPS_TARGET=13.0
CPS_HARD_CAP=15.0
CPS_MAX_GAP=3.0
CPS_ALLOW_SPLIT=true
```

### Standard (Recommended - Default)
```bash
CPS_TARGET=15.0
CPS_HARD_CAP=17.0
CPS_MAX_GAP=2.0
CPS_ALLOW_SPLIT=true
```

### Lenient (Fast-Paced Content)
```bash
CPS_TARGET=17.0
CPS_HARD_CAP=21.0
CPS_MAX_GAP=1.0
CPS_ALLOW_SPLIT=false
```

### Disabled
```bash
CPS_ENFORCEMENT=false
```

## Files Modified

- `docker/subtitle-gen/subtitle_gen.py` - Core implementation
- `config/.env.template` - Configuration template
- `config/.env.pipeline` - Active configuration
- `docs/CPS_IMPROVEMENTS.md` - Full documentation (this file)

## Testing Your Changes

```bash
# Run subtitle generation
./run_pipeline.sh your_movie_dir

# Check the logs for CPS compliance report
# Look for "CPS Analysis:" section

# Review the generated .srt file
cat out/your_movie/en_merged/*.srt | less
```

## Need Help?

1. Check full docs: `docs/CPS_IMPROVEMENTS.md`
2. View current settings: `grep "^CPS_" config/.env.pipeline`
3. Edit settings: `nano config/.env.pipeline`

---

**Remember:** The default settings work well for most content. Only adjust if you see specific issues after running your first subtitle generation.
