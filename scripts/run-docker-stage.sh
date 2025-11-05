#!/bin/bash
# Run Docker stage with GPU fallback
#
# Usage:
#   ./scripts/run-docker-stage.sh asr --movie-dir out/Movie_Name --try-gpu
#   ./scripts/run-docker-stage.sh asr --movie-dir out/Movie_Name --no-gpu

python3 scripts/run_docker_stage.py "$@"
