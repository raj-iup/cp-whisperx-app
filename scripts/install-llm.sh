#!/bin/bash
# Install LLM Translation Environment
# For Hybrid Translation: LLM + IndicTrans2

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv/llm"

echo "========================================"
echo "Installing LLM Translation Environment"
echo "========================================"
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Create virtual environment
if [ -d "$VENV_DIR" ]; then
    echo "Virtual environment already exists at: $VENV_DIR"
    read -p "Remove and reinstall? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$VENV_DIR"
    else
        echo "Skipping installation"
        exit 0
    fi
fi

echo "Creating virtual environment..."
python3 -m venv "$VENV_DIR"

# Activate
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing LLM dependencies..."
pip install -r "$SCRIPT_DIR/requirements-llm.txt"

echo ""
echo "========================================"
echo "✓ LLM Translation environment installed"
echo "========================================"
echo ""
echo "To use this environment:"
echo "  source venv/llm/bin/activate"
echo ""
echo "Required API Keys (add to config/secrets.json):"
echo "  - anthropic_api_key (for Claude)"
echo "  - openai_api_key (for GPT-4)"
echo ""
echo "Get API keys:"
echo "  Anthropic: https://console.anthropic.com/"
echo "  OpenAI: https://platform.openai.com/api-keys"
echo ""
