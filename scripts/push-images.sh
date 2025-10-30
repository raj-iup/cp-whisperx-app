#!/bin/bash
# Push all Docker images to registry

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Load configuration
if [ -f "config/.env" ]; then
    export $(cat config/.env | grep -v '^#' | xargs)
fi

REGISTRY=${DOCKER_REGISTRY:-rajiup}
TAG=${DOCKER_TAG:-latest}

echo -e "${BLUE}======================================================${NC}"
echo -e "${BLUE}  PUSHING IMAGES TO REGISTRY${NC}"
echo -e "${BLUE}======================================================${NC}"
echo -e "${BLUE}Registry: ${REGISTRY}${NC}"
echo -e "${BLUE}Tag: ${TAG}${NC}"
echo ""

# Login to Docker Hub
echo -e "${YELLOW}Logging in to Docker Hub...${NC}"
docker login

# Push all images
IMAGES=("base" "demux" "tmdb" "pre-ner" "silero-vad" "pyannote-vad" "diarization" "whisperx" "post-ner" "subtitle-gen" "mux")

counter=1
total=${#IMAGES[@]}

for image in "${IMAGES[@]}"; do
    echo -e "${YELLOW}[${counter}/${total}] Pushing ${image}...${NC}"
    docker push ${REGISTRY}/cp-whisperx-app-${image}:${TAG}
    echo -e "${GREEN}✓ ${image} pushed${NC}\n"
    ((counter++))
done

echo -e "${GREEN}======================================================${NC}"
echo -e "${GREEN}  ALL IMAGES PUSHED SUCCESSFULLY${NC}"
echo -e "${GREEN}======================================================${NC}"
echo ""
echo -e "${BLUE}Images available at:${NC}"
for image in "${IMAGES[@]}"; do
    echo -e "  ${REGISTRY}/cp-whisperx-app-${image}:${TAG}"
done
