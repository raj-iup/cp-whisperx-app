#!/bin/bash
# Resume pipeline from a specific stage

if [ $# -lt 2 ]; then
    echo "Usage: ./resume-pipeline.sh <job_id> <stage_number>"
    echo ""
    echo "Stages:"
    echo "  1 - demux"
    echo "  2 - tmdb"
    echo "  3 - pre_ner"
    echo "  4 - silero_vad"
    echo "  5 - pyannote_vad"
    echo "  6 - diarization"
    echo "  7 - asr"
    echo "  8 - post_ner"
    echo "  9 - subtitle_gen"
    echo "  10 - mux"
    echo ""
    echo "Example: ./resume-pipeline.sh 20251102-0002 7"
    exit 1
fi

JOB_ID=$1
STAGE_NUM=$2

# Extract date components from job ID
YEAR=${JOB_ID:0:4}
MONTH=${JOB_ID:4:2}
DAY=${JOB_ID:6:2}

# Paths
MOVIE_DIR="/app/out/${YEAR}/${MONTH}/${DAY}/${JOB_ID}"
CONFIG_PATH="/app/jobs/${YEAR}/${MONTH}/${DAY}/${JOB_ID}/.${JOB_ID}.env"
OUTPUT_DIR="out/${YEAR}/${MONTH}/${DAY}/${JOB_ID}"
LOG_DIR="out/${YEAR}/${MONTH}/${DAY}/${JOB_ID}/logs"

# Stage mapping
case $STAGE_NUM in
    1) STAGE="demux"; ARGS="${MOVIE_DIR%/*}/../jobs/${YEAR}/${MONTH}/${DAY}/${JOB_ID}/*.mp4 ${MOVIE_DIR}" ;;
    2) STAGE="tmdb"; ARGS="${MOVIE_DIR}" ;;
    3) STAGE="pre-ner"; ARGS="${MOVIE_DIR}" ;;
    4) STAGE="silero-vad"; ARGS="${MOVIE_DIR}" ;;
    5) STAGE="pyannote-vad"; ARGS="${MOVIE_DIR}" ;;
    6) STAGE="diarization"; ARGS="${MOVIE_DIR}" ;;
    7) STAGE="asr"; ARGS="${MOVIE_DIR}" ;;
    8) STAGE="post-ner"; ARGS="${MOVIE_DIR}" ;;
    9) STAGE="subtitle-gen"; ARGS="${MOVIE_DIR}" ;;
    10) STAGE="mux"; ARGS="<video> <subs> <output>" ;;
    *) echo "Invalid stage number: $STAGE_NUM"; exit 1 ;;
esac

echo "Resuming pipeline for job: $JOB_ID"
echo "Starting from stage $STAGE_NUM: $STAGE"
echo ""

docker compose -f docker-compose.yml run --rm \
    -e "CONFIG_PATH=${CONFIG_PATH}" \
    -e "OUTPUT_DIR=${OUTPUT_DIR}" \
    -e "LOG_ROOT=${LOG_DIR}" \
    ${STAGE} ${ARGS}
