#!/bin/bash
# ============================================================
#  african-ai-kg — Full Setup Script
#  Run: bash setup.sh
# ============================================================

set -e  # stop on any error

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  African AI Knowledge Graph Setup      ${NC}"
echo -e "${BLUE}========================================${NC}"

# ── 1. Create folder structure ───────────────────────────────
echo -e "\n${YELLOW}[1/5] Creating project folders...${NC}"
mkdir -p data/policies
mkdir -p data/extracted
mkdir -p src
mkdir -p logs
echo -e "${GREEN}✓ Folders created${NC}"

# ── 2. Create virtual environment ───────────────────────────
echo -e "\n${YELLOW}[2/5] Creating virtual environment...${NC}"
python3 -m venv venv
echo -e "${GREEN}✓ Virtual environment created${NC}"

# ── 3. Activate venv ────────────────────────────────────────
echo -e "\n${YELLOW}[3/5] Activating virtual environment...${NC}"
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"

# ── 4. Upgrade pip and install dependencies ─────────────────
echo -e "\n${YELLOW}[4/5] Installing dependencies...${NC}"
pip install --upgrade pip --quiet
pip install -r requirements.txt
echo -e "${GREEN}✓ All dependencies installed${NC}"

# ── 5. Check Ollama & Neo4j ─────────────────────────────────
echo -e "\n${YELLOW}[5/5] Checking services...${NC}"

# Check Ollama
if curl -s http://localhost:11434 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Ollama is running${NC}"
else
    echo -e "${YELLOW}⚠  Ollama not detected. Start it with: ollama serve${NC}"
fi

# Check Neo4j
if curl -s http://localhost:7474 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Neo4j is running${NC}"
else
    echo -e "${YELLOW}⚠  Neo4j not detected. Start Neo4j Desktop or run:${NC}"
    echo -e "   docker run -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j"
fi

echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}  Setup complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "\nNext steps:"
echo -e "  1. Activate venv:  ${YELLOW}source venv/bin/activate${NC}"
echo -e "  2. Edit .env with your Neo4j password"
echo -e "  3. Run pipeline:   ${YELLOW}python main.py${NC}"