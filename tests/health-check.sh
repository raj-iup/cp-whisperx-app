#!/usr/bin/env bash
# health-check.sh - Comprehensive system health check

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "════════════════════════════════════════════════════════════"
echo "CP-WHISPERX-APP HEALTH CHECK"
echo "════════════════════════════════════════════════════════════"
echo ""

# 1. Check virtual environments
echo "1. Checking Virtual Environments..."
echo "────────────────────────────────────────────────────────────"

REQUIRED_ENVS=("common" "whisperx" "indictrans2" "mlx")
ALL_ENVS_EXIST=true

for env in "${REQUIRED_ENVS[@]}"; do
    venv_path=".venv-${env}"
    if [[ -d "$venv_path" ]] && [[ -f "${venv_path}/bin/python" ]]; then
        python_version=$("${venv_path}/bin/python" --version 2>&1)
        echo -e "${GREEN}✓${NC} ${env}: ${python_version}"
    else
        echo -e "${RED}✗${NC} ${env}: NOT FOUND"
        ALL_ENVS_EXIST=false
    fi
done

echo ""

if $ALL_ENVS_EXIST; then
    echo -e "${GREEN}✓${NC} All environments exist"
else
    echo -e "${YELLOW}⚠${NC}  Some environments missing - run: ./bootstrap.sh"
fi

echo ""

# 2. Check hardware cache
echo "2. Checking Hardware Cache..."
echo "────────────────────────────────────────────────────────────"

if [[ -f "config/hardware_cache.json" ]]; then
    echo -e "${GREEN}✓${NC} Hardware cache exists"
    
    if command -v jq &> /dev/null; then
        echo ""
        echo "Platform: $(jq -r '.hardware.platform // "unknown"' config/hardware_cache.json)"
        echo "CUDA: $(jq -r '.hardware.has_cuda // false' config/hardware_cache.json)"
        echo "MPS: $(jq -r '.hardware.has_mps // false' config/hardware_cache.json)"
        echo "MLX: $(jq -r '.hardware.has_mlx // false' config/hardware_cache.json)"
    else
        echo -e "${YELLOW}⚠${NC}  jq not installed - cannot parse hardware cache details"
    fi
else
    echo -e "${RED}✗${NC} Hardware cache not found"
    echo "   Run: ./bootstrap.sh"
fi

echo ""

# 3. Check key packages
echo "3. Checking Key Packages..."
echo "────────────────────────────────────────────────────────────"

# Check MLX (if on macOS Apple Silicon)
if [[ -d ".venv-mlx" ]] && [[ "$(uname)" == "Darwin" ]] && [[ "$(uname -m)" == "arm64" ]]; then
    if .venv-mlx/bin/python -c "import mlx.core as mx" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} MLX installed (.venv-mlx)"
    else
        echo -e "${RED}✗${NC} MLX not working (.venv-mlx)"
    fi
fi

# Check WhisperX
if [[ -d ".venv-whisperx" ]]; then
    if .venv-whisperx/bin/python -c "import whisperx" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} WhisperX installed (.venv-whisperx)"
    else
        echo -e "${RED}✗${NC} WhisperX not installed (.venv-whisperx)"
    fi
fi

# Check IndicTrans2
if [[ -d ".venv-indictrans2" ]]; then
    if .venv-indictrans2/bin/python -c "from transformers import AutoTokenizer" 2>/dev/null; then
        transformers_ver=$(.venv-indictrans2/bin/python -c "import transformers; print(transformers.__version__)" 2>/dev/null)
        echo -e "${GREEN}✓${NC} Transformers ${transformers_ver} installed (.venv-indictrans2)"
    else
        echo -e "${RED}✗${NC} Transformers not installed (.venv-indictrans2)"
    fi
fi

# Check common
if [[ -d ".venv-common" ]]; then
    if .venv-common/bin/python -c "import ffmpeg" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} ffmpeg-python installed (.venv-common)"
    else
        echo -e "${RED}✗${NC} ffmpeg-python not installed (.venv-common)"
    fi
fi

echo ""

# 4. Check FFmpeg
echo "4. Checking System Dependencies..."
echo "────────────────────────────────────────────────────────────"

if command -v ffmpeg &> /dev/null; then
    ffmpeg_version=$(ffmpeg -version 2>&1 | head -n 1 | awk '{print $3}')
    echo -e "${GREEN}✓${NC} FFmpeg ${ffmpeg_version}"
else
    echo -e "${RED}✗${NC} FFmpeg not found"
    echo "   Install: brew install ffmpeg (macOS) or sudo apt install ffmpeg (Linux)"
fi

if command -v jq &> /dev/null; then
    jq_version=$(jq --version 2>&1)
    echo -e "${GREEN}✓${NC} jq ${jq_version}"
else
    echo -e "${YELLOW}⚠${NC}  jq not installed (recommended)"
    echo "   Install: brew install jq (macOS) or sudo apt install jq (Linux)"
fi

echo ""

# 5. Check scripts
echo "5. Checking Scripts..."
echo "────────────────────────────────────────────────────────────"

SCRIPTS=("bootstrap.sh" "prepare-job.sh" "run-pipeline.sh" "scripts/bootstrap.sh" "scripts/common-logging.sh")

for script in "${SCRIPTS[@]}"; do
    if [[ -f "$script" ]] && [[ -x "$script" ]]; then
        echo -e "${GREEN}✓${NC} ${script}"
    elif [[ -f "$script" ]]; then
        echo -e "${YELLOW}⚠${NC}  ${script} (not executable - run: chmod +x ${script})"
    else
        echo -e "${RED}✗${NC} ${script} NOT FOUND"
    fi
done

echo ""

# 6. Check PowerShell scripts (if applicable)
if [[ -f "bootstrap.ps1" ]]; then
    echo "6. Checking PowerShell Scripts..."
    echo "────────────────────────────────────────────────────────────"
    
    PS_SCRIPTS=("bootstrap.ps1" "prepare-job.ps1" "run-pipeline.ps1" "scripts/bootstrap.ps1" "scripts/common-logging.ps1")
    
    for script in "${PS_SCRIPTS[@]}"; do
        if [[ -f "$script" ]]; then
            echo -e "${GREEN}✓${NC} ${script}"
        else
            echo -e "${RED}✗${NC} ${script} NOT FOUND"
        fi
    done
    
    echo ""
fi

# 7. Check recent logs
echo "7. Checking Recent Logs..."
echo "────────────────────────────────────────────────────────────"

if [[ -d "logs" ]]; then
    log_count=$(find logs -name "*.log" -type f 2>/dev/null | wc -l | tr -d ' ')
    if [[ $log_count -gt 0 ]]; then
        echo -e "${GREEN}✓${NC} ${log_count} log files found"
        echo ""
        echo "Latest logs:"
        ls -lt logs/*.log 2>/dev/null | head -5 | while read -r line; do
            echo "  ${line}"
        done
    else
        echo -e "${YELLOW}⚠${NC}  No log files yet"
    fi
else
    echo -e "${YELLOW}⚠${NC}  logs/ directory does not exist"
fi

echo ""

# 8. Check documentation
echo "8. Checking Documentation..."
echo "────────────────────────────────────────────────────────────"

DOCS=("README.md" "TROUBLESHOOTING.md" "QUICK_REFERENCE.md" "IMPLEMENTATION_STATUS.md" "COMPLETE_SUMMARY.md")

for doc in "${DOCS[@]}"; do
    if [[ -f "$doc" ]]; then
        size=$(wc -c < "$doc" | tr -d ' ')
        echo -e "${GREEN}✓${NC} ${doc} (${size} bytes)"
    else
        echo -e "${RED}✗${NC} ${doc} NOT FOUND"
    fi
done

echo ""

# Summary
echo "════════════════════════════════════════════════════════════"
echo "HEALTH CHECK SUMMARY"
echo "════════════════════════════════════════════════════════════"
echo ""

if $ALL_ENVS_EXIST && [[ -f "config/hardware_cache.json" ]] && command -v ffmpeg &> /dev/null; then
    echo -e "${GREEN}✅ SYSTEM READY${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Transcribe: ./prepare-job.sh movie.mp4 --transcribe -s hi"
    echo "  2. Run: ./run-pipeline.sh -j <job-id>"
else
    echo -e "${YELLOW}⚠️  SYSTEM NOT READY${NC}"
    echo ""
    
    if ! $ALL_ENVS_EXIST; then
        echo "❌ Missing virtual environments"
        echo "   Fix: ./bootstrap.sh"
        echo ""
    fi
    
    if [[ ! -f "config/hardware_cache.json" ]]; then
        echo "❌ Hardware cache not generated"
        echo "   Fix: ./bootstrap.sh"
        echo ""
    fi
    
    if ! command -v ffmpeg &> /dev/null; then
        echo "❌ FFmpeg not installed"
        echo "   Fix: brew install ffmpeg (macOS) or sudo apt install ffmpeg (Linux)"
        echo ""
    fi
fi

echo "════════════════════════════════════════════════════════════"
echo ""

exit 0
