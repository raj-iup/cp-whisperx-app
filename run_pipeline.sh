#!/bin/bash
# run_pipeline.sh - Simple wrapper for Docker-based pipeline orchestrator

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Help message
show_help() {
    cat << HELP
Usage: ./run_pipeline.sh [OPTIONS] <input_video>

Docker-based pipeline orchestrator for context-aware subtitle generation.

OPTIONS:
    -u, --user-id NUM       User ID for job isolation (default: 1)
    -c, --config FILE       Configuration file (default: config/.env)
    -s, --stages "..."      Run specific stages only (e.g., "demux asr subtitle_gen mux")
    --no-resume             Start fresh, ignore previous progress
    --build                 Rebuild Docker images before running
    --list-stages           List all available stages and exit
    -h, --help              Show this help message

COMMON WORKFLOWS:
    # Production run (all stages)
    ./run_pipeline.sh in/movie.mp4

    # Test run (fast - essential stages only)
    ./run_pipeline.sh --stages "demux asr subtitle_gen mux" in/movie.mp4

    # Debug specific stage
    ./run_pipeline.sh --stages "asr" in/movie.mp4

    # Resume after failure (automatic)
    ./run_pipeline.sh in/movie.mp4

    # Start completely fresh
    ./run_pipeline.sh --no-resume in/movie.mp4

    # Rebuild and run
    ./run_pipeline.sh --build in/movie.mp4

EXAMPLES:
    # Multi-user execution
    ./run_pipeline.sh --user-id 2 in/movie.mp4

    # Custom configuration
    ./run_pipeline.sh --config config/.env.custom in/movie.mp4

    # All options
    ./run_pipeline.sh --user-id 3 --config config/.env.test --stages "demux asr mux" in/movie.mp4

OUTPUT:
    Job outputs: out/YYYY/MM/DD/[USER_ID]/[JOB_ID]/
    Logs:        logs/YYYY/MM/DD/[USER_ID]/[JOB_ID]/

DOCUMENTATION:
    Quick Start: QUICKSTART.md
    Quick Ref:   docs/PIPELINE_QUICKREF.md
    Full Guide:  docs/JOB_ORCHESTRATION.md
    Config Ref:  docs/CONFIGURATION_GUIDE.md

HELP
}

# Default values
USER_ID=1
CONFIG_FILE="config/.env"
INPUT_VIDEO=""
STAGES=""
NO_RESUME=false
BUILD_IMAGES=false
LIST_STAGES=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -u|--user-id)
            USER_ID="$2"
            shift 2
            ;;
        -c|--config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        -s|--stages)
            STAGES="$2"
            shift 2
            ;;
        --no-resume)
            NO_RESUME=true
            shift
            ;;
        --build)
            BUILD_IMAGES=true
            shift
            ;;
        --list-stages)
            LIST_STAGES=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        -*)
            echo -e "${RED}Error: Unknown option $1${NC}"
            show_help
            exit 1
            ;;
        *)
            INPUT_VIDEO="$1"
            shift
            ;;
    esac
done

# Validate input
if [ "$LIST_STAGES" = true ]; then
    # Just list stages and exit
    python3 pipeline.py --list-stages
    exit 0
fi

if [ -z "$INPUT_VIDEO" ]; then
    echo -e "${RED}Error: No input video specified${NC}"
    show_help
    exit 1
fi

if [ ! -f "$INPUT_VIDEO" ]; then
    echo -e "${RED}Error: Input video not found: $INPUT_VIDEO${NC}"
    exit 1
fi

if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}Error: Configuration file not found: $CONFIG_FILE${NC}"
    exit 1
fi

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker not found. Please install Docker.${NC}"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 not found. Please install Python 3.9+${NC}"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo -e "${RED}Error: Docker daemon not running. Please start Docker.${NC}"
    exit 1
fi

# Check if containers are built
echo -e "${BLUE}Checking Docker containers...${NC}"
if ! docker images | grep -q "cp-whisperx-app-asr"; then
    echo -e "${YELLOW}Docker containers not found. Building...${NC}"
    docker compose build
elif [ "$BUILD_IMAGES" = true ]; then
    echo -e "${YELLOW}Rebuilding Docker containers...${NC}"
    docker compose build
fi

# Display configuration
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Docker Pipeline Orchestrator${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}Configuration:${NC}"
echo "  Input Video:  $INPUT_VIDEO"
echo "  Config File:  $CONFIG_FILE"
echo "  User ID:      $USER_ID"
if [ -n "$STAGES" ]; then
    echo "  Stages:       $STAGES"
else
    echo "  Stages:       All (complete pipeline)"
fi
if [ "$NO_RESUME" = true ]; then
    echo "  Resume:       Disabled (starting fresh)"
else
    echo "  Resume:       Enabled (auto-resume if previous run exists)"
fi
echo ""

# Run pipeline
echo -e "${BLUE}Starting pipeline...${NC}"
echo ""

# Build command arguments
PIPELINE_ARGS=("$INPUT_VIDEO" "$CONFIG_FILE" "$USER_ID")

if [ -n "$STAGES" ]; then
    PIPELINE_ARGS+=("--stages" $STAGES)
fi

if [ "$NO_RESUME" = true ]; then
    PIPELINE_ARGS+=("--no-resume")
fi

python3 pipeline.py "${PIPELINE_ARGS[@]}"

# Capture exit code
EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  ✅ Pipeline completed successfully!${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    
    # Find output directory
    OUTPUT_DIR=$(find out -type d -name "202*-*" | tail -1)
    if [ -n "$OUTPUT_DIR" ]; then
        echo ""
        echo "Output Directory: $OUTPUT_DIR"
        echo "Final Video:      $OUTPUT_DIR/final_output.mp4"
        echo "Subtitles:        $OUTPUT_DIR/subtitles/subtitles.srt"
        echo "Manifest:         $OUTPUT_DIR/manifest.json"
        echo ""
        echo "View logs:        ls logs/$(basename $(dirname $OUTPUT_DIR))/$(basename $OUTPUT_DIR)/"
    fi
else
    echo -e "${RED}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${RED}  ❌ Pipeline failed!${NC}"
    echo -e "${RED}═══════════════════════════════════════════════════════════${NC}"
    
    # Find log directory
    LOG_DIR=$(find logs -type d -name "202*-*" | tail -1)
    if [ -n "$LOG_DIR" ]; then
        echo ""
        echo "Check logs:    ls $LOG_DIR/"
        echo "Orchestrator:  cat $LOG_DIR/orchestrator_*.log"
        echo "Manifest:      cat $(find out -name "manifest.json" | tail -1)"
    fi
fi

exit $EXIT_CODE
