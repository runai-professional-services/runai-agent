#!/bin/bash

# RunAI CLI - Quick Verification Script
# This script verifies the CLI installation and basic functionality

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  RunAI CLI Verification Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check Python
echo -e "${BLUE}Checking Python...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 not found${NC}"
    echo "Please install Python >= 3.11 from https://python.org/"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}✓ Python found: ${PYTHON_VERSION}${NC}"

# Check Node.js
echo -e "${BLUE}Checking Node.js...${NC}"
if ! command -v node &> /dev/null; then
    echo -e "${RED}✗ Node.js not found${NC}"
    echo "Please install Node.js >= 18.0.0 from https://nodejs.org/"
    exit 1
fi

NODE_VERSION=$(node --version)
echo -e "${GREEN}✓ Node.js found: ${NODE_VERSION}${NC}"

# Check npm
echo -e "${BLUE}Checking npm...${NC}"
if ! command -v npm &> /dev/null; then
    echo -e "${RED}✗ npm not found${NC}"
    exit 1
fi

NPM_VERSION=$(npm --version)
echo -e "${GREEN}✓ npm found: ${NPM_VERSION}${NC}"
echo ""

# Check NAT installation
echo -e "${BLUE}Checking NAT (NeMo Agent Toolkit)...${NC}"
if ! command -v nat &> /dev/null && ! python3 -m nat --version &> /dev/null 2>&1; then
    echo -e "${YELLOW}⚠ NAT (NeMo Agent Toolkit) not found${NC}"
    echo -e "${YELLOW}The CLI requires NAT to be installed for the agent backend.${NC}"
    echo ""
    echo -e "${BLUE}To install NAT:${NC}"
    echo "1. Create virtual environment: python3 -m venv .venv"
    echo "2. Activate: source .venv/bin/activate"
    echo "3. Install: cd nemo-agent-toolkit-custom && pip install -e ."
    echo ""
    echo -e "${YELLOW}Continuing with CLI-only verification...${NC}"
    echo ""
else
    NAT_VERSION=$(nat --version 2>/dev/null || python3 -m nat --version 2>/dev/null || echo "unknown")
    echo -e "${GREEN}✓ NAT found: ${NAT_VERSION}${NC}"
    echo ""
fi

# Check environment variables
echo -e "${BLUE}Checking environment variables...${NC}"
ENV_MISSING=false

if [ -z "$RUNAI_CLIENT_ID" ]; then
    echo -e "${YELLOW}⚠ RUNAI_CLIENT_ID not set${NC}"
    ENV_MISSING=true
fi

if [ -z "$RUNAI_CLIENT_SECRET" ]; then
    echo -e "${YELLOW}⚠ RUNAI_CLIENT_SECRET not set${NC}"
    ENV_MISSING=true
fi

if [ -z "$RUNAI_BASE_URL" ]; then
    echo -e "${YELLOW}⚠ RUNAI_BASE_URL not set${NC}"
    ENV_MISSING=true
fi

if [ -z "$NVIDIA_API_KEY" ]; then
    echo -e "${YELLOW}⚠ NVIDIA_API_KEY not set${NC}"
    ENV_MISSING=true
fi

if [ "$ENV_MISSING" = true ]; then
    echo -e "${YELLOW}⚠ Some environment variables are missing${NC}"
    echo -e "${YELLOW}The agent server will need these to run.${NC}"
    echo ""
else
    echo -e "${GREEN}✓ All required environment variables are set${NC}"
    echo ""
fi

# Navigate to CLI directory
CLI_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/runai-cli"
echo -e "${BLUE}CLI Directory: ${CLI_DIR}${NC}"

if [ ! -d "$CLI_DIR" ]; then
    echo -e "${RED}✗ runai-cli directory not found${NC}"
    exit 1
fi

cd "$CLI_DIR"
echo ""

# Check if package.json exists
if [ ! -f "package.json" ]; then
    echo -e "${RED}✗ package.json not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓ CLI directory found${NC}"
echo ""

# Install dependencies
echo -e "${BLUE}Installing dependencies...${NC}"
npm install
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Build TypeScript
echo -e "${BLUE}Building TypeScript...${NC}"
npm run build
echo -e "${GREEN}✓ TypeScript compiled${NC}"
echo ""

# Link CLI globally
echo -e "${BLUE}Linking CLI globally...${NC}"
npm link
echo -e "${GREEN}✓ CLI linked (runai-cli command available)${NC}"
echo ""

# Test CLI
echo -e "${BLUE}Testing CLI...${NC}"
if ! command -v runai-cli &> /dev/null; then
    echo -e "${RED}✗ runai-cli command not found${NC}"
    echo "Try running: npm link"
    exit 1
fi

echo -e "${GREEN}✓ runai-cli command found${NC}"
echo ""

# Show help
echo -e "${BLUE}CLI Help Output:${NC}"
runai-cli --help
echo ""

# Check configuration
echo -e "${BLUE}Current Configuration:${NC}"
runai-cli config show || echo -e "${YELLOW}⚠ Config not initialized yet (normal for first run)${NC}"
echo ""

# Summary
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Verification Complete ✓${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo ""

if [ "$ENV_MISSING" = true ]; then
    echo -e "${YELLOW}1. Set environment variables:${NC}"
    echo "   export RUNAI_CLIENT_ID=\"your_client_id\""
    echo "   export RUNAI_CLIENT_SECRET=\"your_client_secret\""
    echo "   export RUNAI_BASE_URL=\"https://your-cluster.example.com\""
    echo "   export NVIDIA_API_KEY=\"your_api_key\""
    echo ""
fi

if ! command -v nat &> /dev/null && ! python3 -m nat --version &> /dev/null 2>&1; then
    echo -e "${YELLOW}2. Install NAT (required for agent backend):${NC}"
    echo "   cd ../nemo-agent-toolkit-custom"
    echo "   python3 -m venv ../.venv"
    echo "   source ../.venv/bin/activate"
    echo "   pip install -e ."
    echo ""
    NEXT_STEP=3
else
    NEXT_STEP=2
fi

echo -e "${GREEN}${NEXT_STEP}. Start the agent server:${NC}"
echo "   runai-cli server start --background"
echo ""

echo -e "${GREEN}$((NEXT_STEP + 1)). Test a query:${NC}"
echo -e "${GREEN}$((NEXT_STEP + 1)). Test a query:${NC}"
echo "   runai-cli ask \"Show me all projects\""
echo ""
echo -e "${GREEN}$((NEXT_STEP + 2)). Or start interactive mode:${NC}"
echo "   runai-cli chat"
echo ""
echo -e "${GREEN}✓ CLI is ready to use!${NC}"

