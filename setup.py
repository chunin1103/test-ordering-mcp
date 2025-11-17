#!/usr/bin/env python3
"""
Setup script for MCP Ordering System

This script helps set up the project and verify the installation.
"""

import os
import sys
import subprocess
from pathlib import Path


def check_python_version():
    """Check Python version"""
    print("Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ required, found {version.major}.{version.minor}")
        return False
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    return True


def install_dependencies():
    """Install Python dependencies"""
    print("\nInstalling dependencies...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-q", "--upgrade", "pip"
        ])
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-q", "-r", "requirements.txt"
        ])
        print("✓ Dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def setup_env_file():
    """Setup .env file"""
    print("\nSetting up environment...")
    env_file = Path(".env")
    env_example = Path(".env.example")

    if env_file.exists():
        print("✓ .env file already exists")
        return True

    if not env_example.exists():
        print("❌ .env.example not found")
        return False

    # Copy example to .env
    env_file.write_text(env_example.read_text())
    print("✓ .env file created from .env.example")
    print("  Edit .env to customize Tool URLs if needed")
    return True


def create_output_dir():
    """Create output directory"""
    print("\nCreating output directory...")
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    print(f"✓ Output directory ready: {output_dir.absolute()}")
    return True


def verify_imports():
    """Verify that required modules can be imported"""
    print("\nVerifying imports...")
    required_modules = [
        "mcp",
        "httpx",
        "pydantic",
    ]

    all_ok = True
    for module in required_modules:
        try:
            __import__(module)
            print(f"✓ {module}")
        except ImportError:
            print(f"❌ {module} - not found")
            all_ok = False

    return all_ok


def print_next_steps():
    """Print next steps for the user"""
    print("\n" + "=" * 80)
    print("Setup Complete!")
    print("=" * 80)
    print("\nNext steps:")
    print("\n1. Test the agent:")
    print("   python test_agent.py --manufacturer Shalom")
    print("\n2. Run examples:")
    print("   python examples/simple_test.py")
    print("   python examples/multi_manufacturer_test.py")
    print("   python examples/custom_workflow_test.py")
    print("\n3. Configure MCP server:")
    print("   - For Claude Desktop: ~/Library/Application Support/Claude/claude_desktop_config.json")
    print("   - For Cursor: ~/.cursor/mcp.json")
    print("   See README.md for detailed instructions")
    print("\n4. Check generated files:")
    print("   ls -l output/")
    print("")


def main():
    """Main setup function"""
    print("=" * 80)
    print("MCP Ordering System - Setup")
    print("=" * 80)
    print("")

    steps = [
        ("Check Python version", check_python_version),
        ("Install dependencies", install_dependencies),
        ("Setup environment", setup_env_file),
        ("Create directories", create_output_dir),
        ("Verify imports", verify_imports),
    ]

    for step_name, step_func in steps:
        if not step_func():
            print(f"\n❌ Setup failed at: {step_name}")
            return 1

    print_next_steps()
    return 0


if __name__ == "__main__":
    sys.exit(main())
