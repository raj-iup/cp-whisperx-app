#!/bin/bash
# cleanup-duplicate-vocals.sh
# 
# Safely removes duplicate vocals.wav files to save disk space
# Keeps audio.wav (used by pipeline) and accompaniment.wav (used by lyrics detection)

set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║     Cleanup: Remove Duplicate vocals.wav Files               ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Check if out directory exists
if [ ! -d "out" ]; then
    echo "❌ Error: 'out' directory not found"
    echo "   Please run this script from the project root"
    exit 1
fi

# Find all vocals.wav files
echo "Scanning for duplicate vocals.wav files..."
echo ""

# Count files
total_count=$(find out -name "vocals.wav" -type f 2>/dev/null | wc -l | tr -d ' ')

if [ "$total_count" -eq 0 ]; then
    echo "ℹ️  No vocals.wav files found"
    echo "   Either they've already been deleted or no jobs have run with source separation"
    exit 0
fi

echo "Found $total_count vocals.wav file(s)"
echo ""

# Calculate total size
total_size=0
while IFS= read -r file; do
    if [ -f "$file" ]; then
        size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo 0)
        total_size=$((total_size + size))
    fi
done < <(find out -name "vocals.wav" -type f)

# Convert to MB
total_size_mb=$((total_size / 1024 / 1024))

echo "Total disk space used: ${total_size_mb} MB"
echo ""
echo "Files to be deleted:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# List files with sizes
find out -name "vocals.wav" -type f -exec ls -lh {} \; | awk '{print "  " $9 " (" $5 ")"}'

echo ""
echo "These files are safe to delete because:"
echo "  • vocals.wav is a duplicate of audio.wav"
echo "  • PyAnnote VAD uses audio.wav (not vocals.wav)"
echo "  • WhisperX ASR uses audio.wav (not vocals.wav)"
echo "  • Lyrics detection uses audio.wav (not vocals.wav)"
echo ""
echo "Files that will be kept:"
echo "  ✅ audio.wav - Used by PyAnnote, WhisperX, and Lyrics detection"
echo "  ✅ accompaniment.wav - Used by Lyrics detection for music analysis"
echo ""

# Ask for confirmation
read -p "Delete $total_count file(s) to save ${total_size_mb} MB? (y/N): " confirm

if [[ $confirm =~ ^[Yy]$ ]]; then
    echo ""
    echo "Deleting files..."
    
    deleted_count=0
    while IFS= read -r file; do
        if [ -f "$file" ]; then
            rm -v "$file"
            deleted_count=$((deleted_count + 1))
        fi
    done < <(find out -name "vocals.wav" -type f)
    
    echo ""
    echo "✅ Cleanup complete!"
    echo "   Deleted: $deleted_count file(s)"
    echo "   Space saved: ${total_size_mb} MB"
    echo ""
else
    echo ""
    echo "ℹ️  Cleanup cancelled - no files were deleted"
    echo ""
fi

echo "════════════════════════════════════════════════════════════════"
