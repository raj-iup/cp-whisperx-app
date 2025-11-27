#!/bin/bash
# Quick Reference: MLX Alignment & Beam Comparison

cat << 'EOF'

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  MLX ALIGNMENT & BEAM SEARCH COMPARISON - QUICK REFERENCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 WHAT WAS FIXED
  ✅ Empty 05_alignment directory now has actual output
  ✅ MLX transcripts now get word-level timestamps
  ✅ Beam search comparison tool for quality optimization

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  COMMON TASKS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1️⃣  CHECK IF JOB HAS WORD-LEVEL TIMING
    jq '.segments[0].words | length' out/2025/11/24/1/1/04_asr/segments.json
    
    Output: 0     → No word timing (needs alignment)
    Output: > 0   → Has word timing ✓

2️⃣  MANUALLY ALIGN EXISTING JOB
    python3 scripts/mlx_alignment.py \
        out/2025/11/24/1/1/02_source_separation/audio.wav \
        out/2025/11/24/1/1/04_asr/segments.json \
        out/2025/11/24/1/1/05_alignment/segments_aligned.json \
        --language hi

3️⃣  COMPARE BEAM SEARCH QUALITY (QUICK TEST)
    ./compare-beam-search.sh out/2025/11/24/1/1 --beam-range 4,6
    
    Opens: out/2025/11/24/1/1/beam_comparison/beam_comparison_report.html

4️⃣  COMPARE ALL BEAM WIDTHS (4-10)
    ./compare-beam-search.sh out/2025/11/24/1/1
    
    Time: ~10 minutes (7 beams × 90 seconds each)

5️⃣  VIEW COMPARISON REPORT
    open out/2025/11/24/1/1/beam_comparison/beam_comparison_report.html

6️⃣  COUNT WORDS IN ALIGNED SEGMENTS
    jq '[.segments[].words | length] | add' \
        out/2025/11/24/1/1/05_alignment/segments_aligned.json

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  NEW PIPELINE BEHAVIOR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BEFORE (MLX Backend):
  05_alignment/
  └── (empty)          # Just verification, no output ✗

AFTER (MLX Backend):
  05_alignment/
  └── segments_aligned.json    # Full word-level timing ✓

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  DIRECTORY STRUCTURE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{JOB_DIR}/
├── 04_asr/
│   └── segments.json                    # Segment-level timing only
├── 05_alignment/
│   └── segments_aligned.json            # ✨ NEW: Word-level timing
└── beam_comparison/                     # ✨ NEW: Beam quality test
    ├── segments_en_beam4.json
    ├── segments_en_beam5.json
    ├── segments_en_beam6.json
    ├── segments_en_beam7.json
    ├── segments_en_beam8.json
    ├── segments_en_beam9.json
    ├── segments_en_beam10.json
    └── beam_comparison_report.html

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  WORKFLOW EXAMPLES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Example 1: Quick Beam Test (3 beams)
─────────────────────────────────────
  ./compare-beam-search.sh out/2025/11/24/1/1 --beam-range 4,6
  # Time: ~4 minutes
  # Opens report in browser

Example 2: Full Beam Analysis (7 beams)
────────────────────────────────────────
  ./compare-beam-search.sh out/2025/11/24/1/1
  # Time: ~10 minutes
  # Comprehensive quality comparison

Example 3: Re-align Existing Job
─────────────────────────────────
  # Check current state
  jq '.segments[0].words' out/2025/11/24/1/1/04_asr/segments.json
  # Output: []
  
  # Perform alignment
  python3 scripts/mlx_alignment.py \
      out/2025/11/24/1/1/02_source_separation/audio.wav \
      out/2025/11/24/1/1/04_asr/segments.json \
      out/2025/11/24/1/1/05_alignment/segments_aligned.json \
      --language hi
  
  # Verify
  jq '.segments[0].words[0:3]' out/2025/11/24/1/1/05_alignment/segments_aligned.json

Example 4: New Pipeline Run
────────────────────────────
  ./prepare-job.sh --input "movie.mp4" --source-lang hi --target-lang en
  ./run-pipeline.sh out/2025/11/25/1/1
  
  # Alignment happens automatically during pipeline!
  ls -lh out/2025/11/25/1/1/05_alignment/segments_aligned.json

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  BEAM SEARCH GUIDANCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Beam Width Recommendations:
  
  Beam 4-5:   Fast, good for dialogue/conversation
              Time: ~90s per 150 segments
              Quality: Good
  
  Beam 6-7:   Balanced, recommended for most content
              Time: ~95s per 150 segments
              Quality: Better
  
  Beam 8-10:  Best quality, ideal for songs/poetry
              Time: ~105s per 150 segments
              Quality: Best
  
  Default:    Beam 4 (fast, decent quality)
  Optimal:    Beam 7 (balance of speed/quality)
  Premium:    Beam 10 (best quality, slower)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  TROUBLESHOOTING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❓ Alignment still empty?
   → Check: grep WHISPER_BACKEND out/2025/11/24/1/1/.job-*.env
   → Should be: WHISPER_BACKEND=mlx

❓ Beam comparison fails?
   → Test: test -d .venv-indictrans2 && echo "✓" || echo "✗"
   → Install: ./bootstrap.sh --env indictrans2

❓ HTML report doesn't open?
   → Manual: open out/2025/11/24/1/1/beam_comparison/beam_comparison_report.html
   → Or copy URL from terminal output

❓ Need more help?
   → Full docs: docs/MLX_ALIGNMENT_BEAM_COMPARISON.md
   → Summary: ALIGNMENT_BEAM_ENHANCEMENT_SUMMARY.md

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  FILES CREATED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ✅ scripts/mlx_alignment.py                  (MLX alignment module)
  ✅ scripts/beam_search_comparison.py         (Beam comparison tool)
  ✅ compare-beam-search.sh                    (Wrapper script)
  ✅ docs/MLX_ALIGNMENT_BEAM_COMPARISON.md     (Full documentation)
  ✅ ALIGNMENT_BEAM_ENHANCEMENT_SUMMARY.md     (Enhancement summary)
  ✅ scripts/run-pipeline.py                   (Enhanced alignment stage)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EOF
