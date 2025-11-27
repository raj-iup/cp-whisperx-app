#!/bin/bash
# verify-refactor.sh - Quick verification of pipeline refactor

set -e

echo "================================================================"
echo "Pipeline Refactor Verification"
echo "================================================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if in correct directory
if [ ! -f "scripts/pipeline.py" ]; then
    echo -e "${RED}✗ Error: Run this from the project root directory${NC}"
    exit 1
fi

echo "1. Checking new files exist..."
FILES=(
    "scripts/song_bias_injection.py"
    "PIPELINE_REFACTOR_2025-11-14.md"
    "REFACTOR_QUICK_REF.md"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "   ${GREEN}✓${NC} $file"
    else
        echo -e "   ${RED}✗${NC} $file - MISSING"
        exit 1
    fi
done

echo ""
echo "2. Checking stage number mappings..."
python3 << 'EOF'
import sys
sys.path.insert(0, '.')
sys.path.insert(0, 'scripts')

from shared.stage_utils import StageIO

stages = {
    "asr": 6,
    "song_bias_injection": 7,
    "lyrics_detection": 8,
    "bias_correction": 9,
    "subtitle_gen": 14,
    "mux": 15
}

all_ok = True
for name, expected in stages.items():
    stage_io = StageIO(name)
    actual = stage_io.stage_number
    if actual == expected:
        print(f"   ✓ {name:25} → Stage {actual:2}")
    else:
        print(f"   ✗ {name:25} → Stage {actual:2} (expected {expected})")
        all_ok = False

sys.exit(0 if all_ok else 1)
EOF

if [ $? -ne 0 ]; then
    echo -e "${RED}Stage mapping verification failed${NC}"
    exit 1
fi

echo ""
echo "3. Checking script executability..."
SCRIPTS=(
    "scripts/song_bias_injection.py"
    "scripts/lyrics_detection.py"
)

for script in "${SCRIPTS[@]}"; do
    if [ -x "$script" ]; then
        echo -e "   ${GREEN}✓${NC} $script is executable"
    else
        echo -e "   ${YELLOW}⚠${NC}  $script not executable (fixing...)"
        chmod +x "$script"
    fi
done

echo ""
echo "4. Testing script imports..."
python3 << 'EOF'
import sys
sys.path.insert(0, '.')
sys.path.insert(0, 'scripts')

scripts = [
    "song_bias_injection",
    "lyrics_detection",
    "bias_injection",
    "lyrics_detection_core"
]

all_ok = True
for script in scripts:
    try:
        __import__(script)
        print(f"   ✓ {script}")
    except Exception as e:
        print(f"   ✗ {script}: {e}")
        all_ok = False

sys.exit(0 if all_ok else 1)
EOF

if [ $? -ne 0 ]; then
    echo -e "${RED}Script import verification failed${NC}"
    exit 1
fi

echo ""
echo "5. Verifying pipeline definitions..."
python3 << 'EOF'
import sys
sys.path.insert(0, 'scripts')
from pipeline import STAGE_DEFINITIONS, STAGE_SCRIPTS

required = ["song_bias_injection", "lyrics_detection", "bias_correction"]
stage_names = [s[0] for s in STAGE_DEFINITIONS]

all_ok = True
for stage in required:
    if stage in stage_names and stage in STAGE_SCRIPTS:
        print(f"   ✓ {stage} in pipeline")
    else:
        print(f"   ✗ {stage} missing from pipeline")
        all_ok = False

sys.exit(0 if all_ok else 1)
EOF

if [ $? -ne 0 ]; then
    echo -e "${RED}Pipeline definition verification failed${NC}"
    exit 1
fi

echo ""
echo "================================================================"
echo -e "${GREEN}✅ All verification checks passed!${NC}"
echo "================================================================"
echo ""
echo "Pipeline refactor is ready for testing."
echo ""
echo "Next steps:"
echo "  1. Test with a movie: ./prepare-job.sh /path/to/movie.mp4"
echo "  2. Run pipeline: ./run_pipeline.sh -j <job-id>"
echo "  3. Check new stages: ls out/<job>/07_song_bias_injection/"
echo "  4. Verify lyrics: jq '.total_lyric_segments' out/<job>/08_lyrics_detection/segments.json"
echo ""
echo "Documentation:"
echo "  • PIPELINE_REFACTOR_2025-11-14.md - Full details"
echo "  • REFACTOR_QUICK_REF.md - Quick reference"
echo ""

exit 0
