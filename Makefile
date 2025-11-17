.PHONY: help setup install test clean examples

help:
	@echo "MCP Ordering System - Available Commands"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make setup      - Run full setup (create venv, install deps, etc.)"
	@echo "  make install    - Install dependencies only"
	@echo ""
	@echo "Testing:"
	@echo "  make test       - Run simple test with Shalom manufacturer"
	@echo "  make examples   - Run all example tests"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean      - Clean output files and cache"
	@echo "  make env        - Create .env from .env.example"
	@echo ""
	@echo "Development:"
	@echo "  make mcp        - Start MCP server (for testing)"
	@echo ""

setup:
	@echo "Running setup..."
	python3 setup.py

install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt

test:
	@echo "Running simple test..."
	python test_agent.py --manufacturer Shalom

examples:
	@echo "Running all examples..."
	@echo ""
	@echo "=== Simple Test ==="
	python examples/simple_test.py
	@echo ""
	@echo "=== Multi-Manufacturer Test ==="
	python examples/multi_manufacturer_test.py
	@echo ""
	@echo "=== Custom Workflow Test ==="
	python examples/custom_workflow_test.py

clean:
	@echo "Cleaning output and cache files..."
	rm -rf output/*.xlsx output/*.md output/*.json
	rm -f test_agent.log
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "✓ Cleaned"

env:
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✓ .env created from .env.example"; \
	else \
		echo ".env already exists"; \
	fi

mcp:
	@echo "Starting MCP server..."
	@echo "Press Ctrl+C to stop"
	python mcp_server.py
