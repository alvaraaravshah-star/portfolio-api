#!/bin/bash

# Quick Start Script for Refactored Macro Engine API
# This script sets up and runs the refactored FastAPI server

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  Macro Engine API - Refactored Version                        ║"
echo "║  Multi-Stage Pipeline Setup & Launch                          ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_CMD=${PYTHON_CMD:-python3}
PORT=${PORT:-10000}

echo -e "${BLUE}[1/5]${NC} Checking Python installation..."
if ! command -v $PYTHON_CMD &> /dev/null; then
    echo -e "${RED}Error: Python not found${NC}"
    echo "Please install Python 3.7+ or set PYTHON_CMD environment variable"
    exit 1
fi
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"
echo ""

echo -e "${BLUE}[2/5]${NC} Checking dependencies..."
echo "   Checking for required packages..."

# Check for required packages
required_packages=("fastapi" "uvicorn" "pydantic")
missing_packages=()

for package in "${required_packages[@]}"; do
    if ! $PYTHON_CMD -c "import $package" 2>/dev/null; then
        missing_packages+=("$package")
    fi
done

if [ ${#missing_packages[@]} -gt 0 ]; then
    echo -e "${YELLOW}   Missing packages: ${missing_packages[*]}${NC}"
    echo -e "   Installing from requirements.txt..."
    
    if [ -f "$PROJECT_DIR/requirements.txt" ]; then
        $PYTHON_CMD -m pip install -q -r "$PROJECT_DIR/requirements.txt"
        echo -e "${GREEN}✓ Dependencies installed${NC}"
    else
        echo -e "${RED}Error: requirements.txt not found${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ All dependencies installed${NC}"
fi
echo ""

echo -e "${BLUE}[3/5]${NC} Checking project structure..."

# Check for required directories and files
required_dirs=(
    "Pass 4 - Regime Mapping/outputs"
    "Pass 5 - Portfolio Scoring"
    "Pass 6 - Portfolio Construction"
)

required_files=(
    "api_server_refactored.py"
    "services/pipeline.py"
    "services/validation.py"
    "routers/recommendations.py"
)

all_exist=true
for dir in "${required_dirs[@]}"; do
    if [ ! -d "$PROJECT_DIR/$dir" ]; then
        echo -e "${YELLOW}   Warning: Missing directory: $dir${NC}"
        all_exist=false
    fi
done

for file in "${required_files[@]}"; do
    if [ ! -f "$PROJECT_DIR/$file" ]; then
        echo -e "${RED}   Error: Missing file: $file${NC}"
        exit 1
    fi
done

if [ "$all_exist" = true ]; then
    echo -e "${GREEN}✓ Project structure is valid${NC}"
fi
echo ""

echo -e "${BLUE}[4/5]${NC} Creating necessary directories..."
mkdir -p "$PROJECT_DIR/logs"
mkdir -p "$PROJECT_DIR/Pass 4 - Regime Mapping/outputs"
mkdir -p "$PROJECT_DIR/Pass 5 - Portfolio Scoring/outputs"
mkdir -p "$PROJECT_DIR/Pass 6 - Portfolio Construction/outputs"
echo -e "${GREEN}✓ Directories ready${NC}"
echo ""

echo -e "${BLUE}[5/5]${NC} Starting API server..."
echo ""
echo -e "${YELLOW}═════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}API Server Starting...${NC}"
echo -e "${YELLOW}═════════════════════════════════════════════════════${NC}"
echo ""
echo "URL:           http://localhost:$PORT"
echo "API Docs:      http://localhost:$PORT/docs"
echo "OpenAPI JSON:  http://localhost:$PORT/openapi.json"
echo "Health Check:  http://localhost:$PORT/health"
echo ""
echo "Endpoints:"
echo "  POST /recommend/start       - Pass 4: Regime Mapping"
echo "  POST /recommend/investor    - Pass 5: Investor Allocation"
echo "  POST /recommend/final       - Pass 6: Portfolio Construction"
echo ""
echo "To test the API:"
echo "  python test_api.py"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""
echo -e "${YELLOW}═════════════════════════════════════════════════════${NC}"
echo ""

# Start the server
cd "$PROJECT_DIR"
$PYTHON_CMD api_server_refactored.py --port $PORT
