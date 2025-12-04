#!/usr/bin/env bash

# Titus Simulator startup script

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Titus Simulator Startup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Warning: .env file not found${NC}"
    echo -e "${YELLOW}Creating .env from .env.example...${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}.env file created. Please update with your configuration.${NC}"
    else
        echo -e "${YELLOW}No .env.example found. Please create .env manually.${NC}"
    fi
    echo ""
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}Virtual environment created.${NC}"
    echo ""
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source venv/bin/activate

# Install/upgrade dependencies
echo -e "${BLUE}Installing dependencies...${NC}"
pip install -q --upgrade pip
pip install -q -e .

echo ""
echo -e "${GREEN}Starting Titus Simulator...${NC}"
echo -e "${BLUE}Server will be available at: http://localhost:8085${NC}"
echo -e "${BLUE}API docs at: http://localhost:8085/docs${NC}"
echo ""

# Start the server
uvicorn titus_simulator.api:app --host 0.0.0.0 --port 8085 --reload
