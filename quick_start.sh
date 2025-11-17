#!/bin/bash
# Quick Start Script for MCP Ordering System

set -e

echo "=========================================="
echo "MCP Ordering System - Quick Start"
echo "=========================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

echo "✓ Python found: $(python3 --version)"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "✓ Dependencies installed"

# Setup .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "✓ .env file created"
    echo "  Edit .env if you need to change Tool URLs"
fi

# Create output directory
mkdir -p output
echo ""
echo "✓ Output directory ready"

# Run simple test
echo ""
echo "=========================================="
echo "Running Simple Test"
echo "=========================================="
echo ""
python test_agent.py --manufacturer Shalom

echo ""
echo "=========================================="
echo "Quick Start Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Check ./output/ for generated files"
echo "  2. Run more examples:"
echo "     - python examples/simple_test.py"
echo "     - python examples/multi_manufacturer_test.py"
echo "     - python examples/custom_workflow_test.py"
echo "  3. Configure MCP server for Claude/Cursor (see README.md)"
echo ""
