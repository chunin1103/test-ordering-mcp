#!/usr/bin/env python3
"""
Multi-Manufacturer Test - Test multiple manufacturers in sequence

Usage:
    python examples/multi_manufacturer_test.py
"""

import asyncio
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_agent import OrderingAgent


async def test_manufacturer(agent, manufacturer_id, test_num):
    """Test a single manufacturer"""
    job_id = f"multi-test-{test_num:03d}-{manufacturer_id.lower()}"

    print(f"\n{'=' * 80}")
    print(f"Test {test_num}: {manufacturer_id}")
    print(f"Job ID: {job_id}")
    print(f"{'=' * 80}")

    result = await agent.run_complete_workflow(
        manufacturer_id=manufacturer_id,
        job_id=job_id,
        review_guide=False  # Skip review for speed
    )

    return {
        "manufacturer": manufacturer_id,
        "job_id": job_id,
        "success": result.get("success", False),
        "result": result
    }


async def main():
    """Test multiple manufacturers"""

    print("=" * 80)
    print("Multi-Manufacturer Ordering Workflow Test")
    print("=" * 80)

    # List of manufacturers to test
    manufacturers = [
        "Shalom",
        # Add more manufacturers as needed
        # "Manufacturer2",
        # "Manufacturer3",
    ]

    # Create agent
    agent = OrderingAgent(
        tool1_url=os.getenv("TOOL1_BASE_URL", "https://ags-tools-1-extract.onrender.com"),
        tool2_url=os.getenv("TOOL2_BASE_URL", "https://ags-tools-2-finalize.onrender.com"),
        output_dir="./output"
    )

    # Run tests
    start_time = datetime.now()
    results = []

    for idx, manufacturer in enumerate(manufacturers, 1):
        result = await test_manufacturer(agent, manufacturer, idx)
        results.append(result)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    # Print summary
    print("\n" + "=" * 80)
    print("Overall Test Summary")
    print("=" * 80)

    passed = sum(1 for r in results if r["success"])
    failed = len(results) - passed

    print(f"\nTotal tests: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Duration: {duration:.2f} seconds")

    print("\nDetailed Results:")
    for result in results:
        status = "✓ PASS" if result["success"] else "✗ FAIL"
        print(f"  {status} - {result['manufacturer']} ({result['job_id']})")

    print("\nGenerated files in ./output/")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
