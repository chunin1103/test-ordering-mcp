#!/usr/bin/env python3
"""
Simple Test - Basic workflow test for a single manufacturer

Usage:
    python examples/simple_test.py
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_agent import OrderingAgent


async def main():
    """Simple test of the ordering workflow"""

    print("=" * 80)
    print("Simple Ordering Workflow Test")
    print("=" * 80)

    # Create agent with default URLs
    agent = OrderingAgent(
        tool1_url=os.getenv("TOOL1_BASE_URL", "https://ags-tools-1-extract.onrender.com"),
        tool2_url=os.getenv("TOOL2_BASE_URL", "https://ags-tools-2-finalize.onrender.com"),
        output_dir="./output"
    )

    # Test with Shalom manufacturer
    manufacturer = "Shalom"
    job_id = "simple-test-001"

    print(f"\nTesting manufacturer: {manufacturer}")
    print(f"Job ID: {job_id}\n")

    result = await agent.run_complete_workflow(
        manufacturer_id=manufacturer,
        job_id=job_id,
        review_guide=True
    )

    # Print summary
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)

    if result.get("success"):
        print("✓ Test PASSED")
        print(f"\nGenerated files:")
        if "download" in result["steps"]:
            print(f"  - Order file: {result['steps']['download']['file_path']}")
        print(f"  - Guide: ./output/{job_id}_guide.md")
        print(f"  - Summary: ./output/{job_id}_summary.json")
    else:
        print("✗ Test FAILED")
        print("\nErrors:")
        for step, data in result.get("steps", {}).items():
            if not data.get("success"):
                print(f"  - {step}: {data.get('error', 'Unknown error')}")

    return 0 if result.get("success") else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
