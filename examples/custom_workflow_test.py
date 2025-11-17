#!/usr/bin/env python3
"""
Custom Workflow Test - Demonstrates step-by-step control

This example shows how to use the agent's individual methods
for fine-grained control over the workflow.

Usage:
    python examples/custom_workflow_test.py
"""

import asyncio
import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_agent import OrderingAgent


async def main():
    """Custom workflow with manual control"""

    print("=" * 80)
    print("Custom Workflow Test - Step-by-Step Control")
    print("=" * 80)

    # Setup
    agent = OrderingAgent(
        tool1_url=os.getenv("TOOL1_BASE_URL", "https://ags-tools-1-extract.onrender.com"),
        tool2_url=os.getenv("TOOL2_BASE_URL", "https://ags-tools-2-finalize.onrender.com"),
        output_dir="./output"
    )

    manufacturer = "Shalom"
    job_id = "custom-workflow-001"

    # Step 1: Extract manufacturer data
    print(f"\n[Step 1] Extracting data for {manufacturer}...")
    extract_result = await agent.extract_manufacturer_data(manufacturer, job_id)

    if not extract_result["success"]:
        print(f"✗ Extract failed: {extract_result['error']}")
        return 1

    print(f"✓ Extract successful")
    print(f"Guide URI: {extract_result['guide_uri']}")

    # Step 2: Review the guide
    print(f"\n[Step 2] Fetching guide content...")
    guide_result = await agent.get_guide_content(extract_result["guide_uri"])

    if not guide_result["success"]:
        print(f"✗ Guide fetch failed: {guide_result['error']}")
        return 1

    print(f"✓ Guide fetched: {guide_result['length']} characters")

    # Display guide preview
    guide_content = guide_result["content"]
    lines = guide_content.split('\n')
    print(f"\nGuide Preview (first 10 lines):")
    print("-" * 80)
    for line in lines[:10]:
        print(line)
    print("-" * 80)
    print(f"... ({len(lines)} total lines)")

    # Save guide locally
    guide_path = f"./output/{job_id}_guide.md"
    with open(guide_path, 'w') as f:
        f.write(guide_content)
    print(f"\nGuide saved to: {guide_path}")

    # Optional: Validate guide content
    print(f"\n[Validation] Checking guide content...")
    if "manufacturer" in guide_content.lower():
        print("✓ Guide contains manufacturer information")
    if "order" in guide_content.lower():
        print("✓ Guide contains ordering information")

    # Step 3: User confirmation (in real scenario, you might want to review)
    print(f"\n[Confirmation] Proceeding to finalize order...")

    # Step 4: Finalize the order
    print(f"\n[Step 3] Finalizing order...")
    finalize_result = await agent.finalize_order(extract_result["guide_uri"], job_id)

    if not finalize_result["success"]:
        print(f"✗ Finalize failed: {finalize_result['error']}")
        return 1

    print(f"✓ Order finalized")
    print(f"Order URI: {finalize_result['order_uri']}")

    # Step 5: Download the order file
    print(f"\n[Step 4] Downloading order file...")
    download_result = await agent.download_order_file(job_id)

    if not download_result["success"]:
        print(f"✗ Download failed: {download_result['error']}")
        return 1

    print(f"✓ Order file downloaded")
    print(f"File path: {download_result['file_path']}")
    print(f"File size: {download_result['file_size']} bytes")

    # Final summary
    print("\n" + "=" * 80)
    print("Workflow Summary")
    print("=" * 80)

    session_data = agent.get_session_data(job_id)
    print(json.dumps(session_data, indent=2))

    print("\n✓ Custom workflow completed successfully!")
    print(f"\nGenerated files:")
    print(f"  - Order: {download_result['file_path']}")
    print(f"  - Guide: {guide_path}")

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
