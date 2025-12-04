#!/usr/bin/env bash

# Titus Simulator Web UI Startup Script

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Titus Simulator - Web UI${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

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
pip install -q streamlit pandas httpx

echo ""
echo -e "${GREEN}Starting Web UI...${NC}"
echo -e "${BLUE}UI will be available at: http://localhost:8088${NC}"
echo -e "${YELLOW}Make sure the API server is running on port 8087${NC}"
echo ""

# Default port (can be overridden by .env)
UI_PORT=${TITUS_UI_PORT:-8088}

# Start Streamlit
streamlit run streamlit_ui.py --server.port $UI_PORT
