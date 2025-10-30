#!/bin/bash
# Quick Start - CP-WhisperX-App Dockerized Pipeline

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                          ║${NC}"
echo -e "${BLUE}║  CP-WHISPERX-APP DOCKERIZED PIPELINE                     ║${NC}"
echo -e "${BLUE}║  Quick Start Setup                                       ║${NC}"
echo -e "${BLUE}║                                                          ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Step 1: Create directories
echo -e "${BLUE}[1/5] Creating directory structure...${NC}"
mkdir -p in out logs temp config shared
echo -e "${GREEN}✓ Directories created${NC}\n"

# Step 2: Copy configuration template
echo -e "${BLUE}[2/5] Setting up configuration...${NC}"
if [ ! -f "config/.env" ]; then
    if [ -f "config/.env.template" ]; then
        cp config/.env.template config/.env
        echo -e "${GREEN}✓ Configuration template copied to config/.env${NC}"
        echo -e "${YELLOW}  Edit config/.env with your settings${NC}"
    else
        echo -e "${YELLOW}  No template found - create config/.env manually${NC}"
    fi
else
    echo -e "${GREEN}✓ Configuration file already exists${NC}"
fi
echo ""

# Step 3: Setup secrets (optional)
echo -e "${BLUE}[3/5] Setting up secrets...${NC}"
if [ ! -f "config/secrets.json" ]; then
    cat > config/secrets.json << 'EOF'
{
  "TMDB_API_KEY": "",
  "HF_TOKEN": ""
}
EOF
    echo -e "${GREEN}✓ Secrets template created${NC}"
    echo -e "${YELLOW}  Edit config/secrets.json with your API keys${NC}"
else
    echo -e "${GREEN}✓ Secrets file already exists${NC}"
fi
echo ""

# Step 4: Run preflight checks
echo -e "${BLUE}[4/5] Running preflight validation...${NC}"
if python3 preflight.py; then
    echo -e "\n${GREEN}✓ Preflight checks passed!${NC}\n"
else
    echo -e "\n${YELLOW}⚠ Some preflight checks failed${NC}"
    echo -e "${YELLOW}  Review the issues above before proceeding${NC}\n"
fi

# Step 5: Next steps
echo -e "${BLUE}[5/5] Next Steps:${NC}\n"
echo -e "  1. ${YELLOW}Configure pipeline:${NC}"
echo -e "     nano config/.env"
echo -e ""
echo -e "  2. ${YELLOW}Add API keys (optional):${NC}"
echo -e "     nano config/secrets.json"
echo -e ""
echo -e "  3. ${YELLOW}Place input video:${NC}"
echo -e "     cp your-movie.mp4 in/"
echo -e ""
echo -e "  4. ${YELLOW}Build Docker images:${NC}"
echo -e "     ./scripts/build-images.sh"
echo -e ""
echo -e "  5. ${YELLOW}Run pipeline:${NC}"
echo -e "     python3 pipeline.py in/your-movie.mp4"
echo -e ""

echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  Setup Complete!                                         ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
