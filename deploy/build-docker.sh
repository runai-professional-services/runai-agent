#!/bin/bash

# Build script for NAT Agent + UI Combined Container
# This script builds a Docker image that includes both the backend agent and frontend UI

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Building NAT Agent + UI Container${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Configuration
IMAGE_NAME="${IMAGE_NAME:-nat-agent-ui}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
REGISTRY="${REGISTRY:-}"

FULL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_TAG}"
if [ -n "$REGISTRY" ]; then
    FULL_IMAGE_NAME="${REGISTRY}/${FULL_IMAGE_NAME}"
fi

echo -e "${GREEN}Building image:${NC} ${FULL_IMAGE_NAME}"
echo ""

# Build the image from project root
echo -e "${BLUE}Step 1: Building Docker image...${NC}"
cd "$(dirname "$0")/.." || exit 1
docker build \
    --platform linux/amd64 \
    -t "${FULL_IMAGE_NAME}" \
    -f deploy/Dockerfile \
    .

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓${NC} Build successful!"
    echo ""
    echo -e "${BLUE}Image details:${NC}"
    docker images "${FULL_IMAGE_NAME}" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
    echo ""
    
    # Ask if user wants to push to registry
    if [ -n "$REGISTRY" ]; then
        echo -e "${YELLOW}Push to registry?${NC} (y/n)"
        read -r response
        if [ "$response" = "y" ] || [ "$response" = "Y" ]; then
            echo -e "${BLUE}Step 2: Pushing to registry...${NC}"
            docker push "${FULL_IMAGE_NAME}"
            echo -e "${GREEN}✓${NC} Push successful!"
        fi
    fi
    
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  Build Complete!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${BLUE}To run locally:${NC}"
    echo "  docker run -p 3000:3000 -p 8000:8000 \\"
    echo "    -e NVIDIA_API_KEY=\$NVIDIA_API_KEY \\"
    echo "    -e RUNAI_CLIENT_ID=\$RUNAI_CLIENT_ID \\"
    echo "    -e RUNAI_CLIENT_SECRET=\$RUNAI_CLIENT_SECRET \\"
    echo "    ${FULL_IMAGE_NAME}"
    echo ""
    echo -e "${BLUE}Run the container:${NC}"
    echo "  docker run -p 3000:3000 -p 8000:8000 \\"
    echo "    -e NVIDIA_API_KEY=\"\$NVIDIA_API_KEY\" \\"
    echo "    ${FULL_IMAGE_NAME}"
    echo ""
    echo -e "${BLUE}Access the UI:${NC}"
    echo "  http://localhost:3000"
    echo ""
    echo -e "${BLUE}Access the API:${NC}"
    echo "  http://localhost:8000/generate"
    echo ""
else
    echo ""
    echo -e "${RED}✗${NC} Build failed!"
    exit 1
fi

