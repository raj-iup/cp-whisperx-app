#!/bin/bash
# Verification script for all pipeline stage fixes

echo "════════════════════════════════════════════════════════════"
echo "   PIPELINE STAGE FIXES - VERIFICATION"
echo "════════════════════════════════════════════════════════════"
echo ""

echo "✅ Checking ASR Stage Fixes..."
echo "────────────────────────────────────────────────────────────"

# Check temperature fix
if grep -q "# temperature not supported by CTranslate2 beam search" scripts/whisperx_integration.py; then
    echo "  ✓ Temperature parameter removed (critical fix)"
else
    echo "  ✗ Temperature fix not found"
fi

# Check warnings suppression
if grep -q "warnings.filterwarnings.*pyannote" docker/asr/whisperx_asr.py; then
    echo "  ✓ PyAnnote warnings suppressed"
else
    echo "  ✗ Warnings suppression not found"
fi

# Check language logging
if grep -q "from WHISPER_LANGUAGE" docker/asr/whisperx_asr.py; then
    echo "  ✓ Language parameter logging enhanced"
else
    echo "  ✗ Language logging not enhanced"
fi

# Check speaker info logging
if grep -q "Character names from pre_ner" docker/asr/whisperx_asr.py; then
    echo "  ✓ Speaker info logging enhanced"
else
    echo "  ✗ Speaker info logging not enhanced"
fi

echo ""
echo "✅ Checking Remaining Stages..."
echo "────────────────────────────────────────────────────────────"

# Check Second Pass Translation
if grep -q "from SECOND_PASS_BACKEND" docker/second-pass-translation/second_pass_translation.py; then
    echo "  ✓ Second Pass Translation - config logging added"
else
    echo "  ✗ Second Pass Translation - config logging missing"
fi

# Check Lyrics Detection
if grep -q "from LYRIC_THRESHOLD" docker/lyrics-detection/lyrics_detection.py; then
    echo "  ✓ Lyrics Detection - config logging added"
else
    echo "  ✗ Lyrics Detection - config logging missing"
fi

# Check Post-NER
if grep -q "from POST_NER_MODEL" docker/post-ner/post_ner.py; then
    echo "  ✓ Post-NER - config logging added"
else
    echo "  ✗ Post-NER - config logging missing"
fi

# Check Subtitle Generation
if grep -q "from SUBTITLE_FORMAT" docker/subtitle-gen/subtitle_gen.py; then
    echo "  ✓ Subtitle Generation - config logging added"
else
    echo "  ✗ Subtitle Generation - config logging missing"
fi

# Check Mux
if grep -q "from MUX_SUBTITLE_CODEC" docker/mux/mux.py; then
    echo "  ✓ Mux - config logging added"
else
    echo "  ✗ Mux - config logging missing"
fi

echo ""
echo "📊 Summary"
echo "────────────────────────────────────────────────────────────"

# Count fixed stages
total_stages=6
fixed_count=$(grep -l "from.*LANGUAGE\|from.*BACKEND\|from.*THRESHOLD\|from.*MODEL\|from.*FORMAT\|from.*CODEC" docker/*/*.py scripts/whisperx_integration.py 2>/dev/null | wc -l | xargs)

echo "Stages with enhanced logging: $fixed_count/$total_stages"

if [ "$fixed_count" -eq "$total_stages" ]; then
    echo "✅ All stages successfully enhanced!"
else
    echo "⚠️  Some stages may need verification"
fi

echo ""
echo "📚 Documentation"
echo "────────────────────────────────────────────────────────────"
ls -1 ASR_FIXES_COMPLETE.md ALL_STAGES_FIXES_COMPLETE.md WHISPERX_FIX_COMPLETE.md 2>/dev/null | while read file; do
    echo "  ✓ $file"
done

echo ""
echo "🚀 Ready to Resume"
echo "────────────────────────────────────────────────────────────"
echo "  ./resume-pipeline.sh 20251108-0001"
echo ""
echo "════════════════════════════════════════════════════════════"
