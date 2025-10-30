#!/bin/bash
# Build all Docker images for cp-whisperx-app pipeline

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Load configuration
if [ -f "config/.env" ]; then
    export $(cat config/.env | grep -v '^#' | xargs)
fi

REGISTRY=${DOCKER_REGISTRY:-rajiup}
TAG=${DOCKER_TAG:-latest}

echo -e "${BLUE}======================================================${NC}"
echo -e "${BLUE}  CP-WHISPERX-APP DOCKER IMAGE BUILD${NC}"
echo -e "${BLUE}======================================================${NC}"
echo -e "${BLUE}Registry: ${REGISTRY}${NC}"
echo -e "${BLUE}Tag: ${TAG}${NC}"
echo ""

# Build base image first
echo -e "${YELLOW}[1/11] Building base image...${NC}"
docker build -t ${REGISTRY}/cp-whisperx-app-base:${TAG} -f docker/base/Dockerfile .
echo -e "${GREEN}✓ Base image built${NC}\n"

# Build all service images
SERVICES=("demux" "tmdb" "pre-ner" "silero-vad" "pyannote-vad" "diarization" "whisperx" "post-ner" "subtitle-gen" "mux")

counter=2
for service in "${SERVICES[@]}"; do
    echo -e "${YELLOW}[${counter}/11] Building ${service} image...${NC}"
    docker build -t ${REGISTRY}/cp-whisperx-app-${service}:${TAG} -f docker/${service}/Dockerfile .
    echo -e "${GREEN}✓ ${service} image built${NC}\n"
    ((counter++))
done

echo -e "${GREEN}======================================================${NC}"
echo -e "${GREEN}  BUILD COMPLETE${NC}"
echo -e "${GREEN}======================================================${NC}"
echo ""

# Show image sizes
echo -e "${BLUE}Docker images:${NC}"
docker images | grep "cp-whisperx-app" | sort

echo ""
echo -e "${YELLOW}To push images to registry, run:${NC}"
echo -e "${YELLOW}  ./scripts/push-images.sh${NC}"
