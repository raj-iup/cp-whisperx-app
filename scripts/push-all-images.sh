#!/bin/bash
# Push all Docker images to registry
# Requires Docker Hub login: docker login

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REGISTRY="${DOCKERHUB_USER:-rajiup}"
REPO_NAME="cp-whisperx-app"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}CP-WhisperX-App Docker Image Pusher${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Registry: ${GREEN}${REGISTRY}${NC}"
echo -e "Repository: ${GREEN}${REPO_NAME}${NC}"
echo ""

# Check if logged in
if ! docker info | grep -q "Username"; then
    echo -e "${RED}✗ Not logged in to Docker Hub${NC}"
    echo -e "${YELLOW}Run: docker login${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker Hub login verified${NC}"
echo ""

# Function to push image
push_image() {
    local tag=$1
    
    echo -e "${YELLOW}Pushing: ${tag}${NC}"
    
    if docker push "${tag}"; then
        echo -e "${GREEN}✓ Pushed: ${tag}${NC}"
        return 0
    else
        echo -e "${RED}✗ Failed: ${tag}${NC}"
        return 1
    fi
}

# Track failures
FAILED_PUSHES=()

echo -e "${BLUE}=== Pushing Base Images ===${NC}"
echo ""

push_image "${REGISTRY}/${REPO_NAME}-base:cpu" || FAILED_PUSHES+=("base:cpu")
push_image "${REGISTRY}/${REPO_NAME}-base:cuda" || FAILED_PUSHES+=("base:cuda")
echo ""

echo -e "${BLUE}=== Pushing Stage Images ===${NC}"
echo ""

# Get all images matching our pattern
IMAGES=$(docker images --format "{{.Repository}}:{{.Tag}}" | grep "${REGISTRY}/${REPO_NAME}" | grep -v "base:")

for image in $IMAGES; do
    push_image "${image}" || FAILED_PUSHES+=("${image}")
    echo ""
done

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Push Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if [ ${#FAILED_PUSHES[@]} -eq 0 ]; then
    echo -e "${GREEN}✓ All images pushed successfully!${NC}"
    echo ""
    
    # List pushed images
    echo -e "${GREEN}Pushed images:${NC}"
    docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" | grep "${REGISTRY}/${REPO_NAME}" | head -20
else
    echo -e "${RED}✗ Failed pushes:${NC}"
    for failed in "${FAILED_PUSHES[@]}"; do
        echo -e "${RED}  - ${failed}${NC}"
    done
    echo ""
    exit 1
fi

echo ""
echo -e "${GREEN}✓ Docker images are now available on Docker Hub${NC}"
echo -e "  Registry: ${BLUE}https://hub.docker.com/u/${REGISTRY}${NC}"
echo ""
