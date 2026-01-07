#!/bin/bash

# Start NAT Agent Server Script
# This script starts the NeMo Agent Toolkit server for the RunAI agent

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Starting RunAI NAT Agent Server${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if in correct directory
if [ ! -d "runai-agent" ]; then
    echo -e "${YELLOW}Error: runai-agent directory not found${NC}"
    echo "Please run this script from the project root directory"
    exit 1
fi

cd runai-agent

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Error: Virtual environment not found${NC}"
    echo "Please run the setup first: cd runai-agent && uv venv .venv && uv sync"
    exit 1
fi

# Activate virtual environment
echo -e "${GREEN}✓${NC} Activating virtual environment..."
source .venv/bin/activate

# Set OpenMP workaround for macOS
# This prevents crashes due to multiple OpenMP library copies
export KMP_DUPLICATE_LIB_OK=TRUE

# Check environment variables
echo -e "${GREEN}✓${NC} Checking environment variables..."

if [ -z "$NVIDIA_API_KEY" ]; then
    echo -e "${YELLOW}Warning: NVIDIA_API_KEY not set${NC}"
    echo "Please export NVIDIA_API_KEY before running this script"
    exit 1
fi

if [ -z "$RUNAI_CLIENT_ID" ]; then
    echo -e "${YELLOW}Warning: RUNAI_CLIENT_ID not set, using default 'test'${NC}"
    export RUNAI_CLIENT_ID="test"
fi

if [ -z "$RUNAI_CLIENT_SECRET" ]; then
    echo -e "${YELLOW}Warning: RUNAI_CLIENT_SECRET not set, using default 'test'${NC}"
    export RUNAI_CLIENT_SECRET="test"
fi

if [ -z "$RUNAI_BASE_URL" ]; then
    echo -e "${YELLOW}Warning: RUNAI_BASE_URL not set, using default 'https://test.run.ai'${NC}"
    export RUNAI_BASE_URL="https://test.run.ai"
fi

echo ""
echo -e "${GREEN}Environment Configuration:${NC}"
echo "  NVIDIA_API_KEY: ${NVIDIA_API_KEY:0:20}..."
echo "  RUNAI_CLIENT_ID: $RUNAI_CLIENT_ID"
echo "  RUNAI_BASE_URL: $RUNAI_BASE_URL"
echo ""

# Auto-construct ROOT_PATH from Run:ai environment variables if available
if [ -n "$RUNAI_PROJECT" ] && [ -n "$RUNAI_JOB_NAME" ]; then
    ROOT_PATH="/${RUNAI_PROJECT}/${RUNAI_JOB_NAME}"
    echo -e "${GREEN}✓${NC} Auto-detected Run:ai deployment"
    echo -e "${BLUE}RUNAI_PROJECT: $RUNAI_PROJECT${NC}"
    echo -e "${BLUE}RUNAI_JOB_NAME: $RUNAI_JOB_NAME${NC}"
    echo -e "${BLUE}ROOT_PATH: $ROOT_PATH (auto-constructed)${NC}"
elif [ -n "$ROOT_PATH" ]; then
    echo -e "${BLUE}ROOT_PATH: $ROOT_PATH (manually set)${NC}"
else
    ROOT_PATH=""
    echo -e "${BLUE}ROOT_PATH not set - running without path prefix (local development mode)${NC}"
    echo -e "${BLUE}To set a root path manually: export ROOT_PATH='/project-01/your-app'${NC}"
    echo -e "${BLUE}Or let Run:ai set it automatically via RUNAI_PROJECT and RUNAI_JOB_NAME${NC}"
fi

# Start the server
echo ""
echo -e "${GREEN}✓${NC} Starting NAT agent server on port 8000..."
echo -e "${BLUE}Server will be accessible at: http://0.0.0.0:8000${NC}"
if [ -z "$ROOT_PATH" ]; then
    echo -e "${BLUE}API Documentation: http://localhost:8000/docs${NC}"
    echo -e "${BLUE}Endpoint: http://localhost:8000/generate${NC}"
else
    echo -e "${BLUE}API Documentation: http://localhost:8000${ROOT_PATH}/docs${NC}"
    echo -e "${BLUE}Endpoint: http://localhost:8000${ROOT_PATH}/generate${NC}"
fi
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

# Only add --root_path flag if ROOT_PATH is set
if [ -z "$ROOT_PATH" ]; then
    nat serve --config_file configs/workflow.yaml --host 0.0.0.0 --port 8000
else
    nat serve --config_file configs/workflow.yaml --host 0.0.0.0 --port 8000 --root_path "$ROOT_PATH"
fi
