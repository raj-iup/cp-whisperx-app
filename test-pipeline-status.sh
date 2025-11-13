#!/bin/bash
# Test script to verify all pipeline stages are implemented

echo "=========================================="
echo "CP-WhisperX-App Pipeline Status Check"
echo "=========================================="
echo ""

# Check job output
JOB_DIR="out/2025/11/12/1/20251112-0001"

if [ ! -d "$JOB_DIR" ]; then
    echo "❌ Job directory not found: $JOB_DIR"
    exit 1
fi

echo "✅ Job directory exists: $JOB_DIR"
echo ""

# Check critical outputs
echo "Checking stage outputs..."
echo ""

# DEMUX
if [ -f "$JOB_DIR/audio.wav" ]; then
    size=$(du -h "$JOB_DIR/audio.wav" | cut -f1)
    echo "✅ DEMUX: audio.wav ($size)"
else
    echo "❌ DEMUX: audio.wav missing"
fi

# TMDB
if [ -f "$JOB_DIR/tmdb/metadata.json" ]; then
    echo "✅ TMDB: metadata.json"
else
    echo "⚠️  TMDB: metadata.json missing (optional)"
fi

# VAD
if [ -f "$JOB_DIR/vad_segments.json" ]; then
    echo "✅ VAD: vad_segments.json"
else
    echo "⚠️  VAD: vad_segments.json missing"
fi

# ASR
if [ -f "$JOB_DIR/asr/transcript.json" ]; then
    segments=$(jq '.segments | length' "$JOB_DIR/asr/transcript.json" 2>/dev/null || echo "0")
    echo "✅ ASR: transcript.json ($segments segments)"
else
    echo "❌ ASR: transcript.json missing"
fi

# NER
if [ -f "$JOB_DIR/ner/entities.json" ]; then
    echo "✅ NER: entities.json"
else
    echo "⚠️  NER: entities.json missing (optional)"
fi

# GLOSSARY
if [ -f "$JOB_DIR/glossary/terms.json" ]; then
    terms=$(jq '.terms | length' "$JOB_DIR/glossary/terms.json" 2>/dev/null || echo "0")
    echo "✅ GLOSSARY: terms.json ($terms terms)"
else
    echo "⚠️  GLOSSARY: terms.json missing (optional)"
fi

# SUBTITLES
if [ -f "$JOB_DIR/subtitles/subtitles.srt" ]; then
    lines=$(wc -l < "$JOB_DIR/subtitles/subtitles.srt")
    echo "✅ SUBTITLES: subtitles.srt ($lines lines)"
else
    echo "❌ SUBTITLES: subtitles.srt missing"
fi

# MUX
if [ -f "$JOB_DIR/output.mkv" ]; then
    size=$(du -h "$JOB_DIR/output.mkv" | cut -f1)
    echo "✅ MUX: output.mkv ($size)"
else
    echo "❌ MUX: output.mkv missing"
fi

echo ""
echo "=========================================="
echo "Pipeline Implementation Status"
echo "=========================================="

# Count stages
total=0
completed=0

for stage in demux tmdb pre_ner silero_vad pyannote_vad diarization asr glossary_builder second_pass_translation lyrics_detection post_ner subtitle_gen mux finalize; do
    total=$((total + 1))
    if grep -q "\"$stage\"" "$JOB_DIR/manifest.json" 2>/dev/null; then
        completed=$((completed + 1))
    fi
done

echo "Stages implemented: $completed/$total"
echo ""

# Check manifest
if [ -f "$JOB_DIR/manifest.json" ]; then
    pipeline_status=$(jq -r '.pipeline.status' "$JOB_DIR/manifest.json" 2>/dev/null || echo "unknown")
    echo "Pipeline status: $pipeline_status"
    
    if [ "$pipeline_status" = "completed" ] || [ "$pipeline_status" = "success" ]; then
        echo ""
        echo "🎉 Pipeline completed successfully!"
        exit 0
    fi
fi

echo ""
echo "ℹ️  Pipeline execution complete with placeholder data"
echo "   To run real transcription, update ASR stage with actual WhisperX call"
