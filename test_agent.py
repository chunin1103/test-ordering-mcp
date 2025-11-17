#!/usr/bin/env python3
"""
Automated Testing Agent for MCP Ordering Workflow

This agent tests the complete ordering workflow:
1. Extract manufacturer data (Tool #1)
2. Review the generated guide
3. Finalize the order (Tool #2)
4. Download the Excel file
"""

import os
import sys
import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
import httpx
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('test_agent.log')
    ]
)
logger = logging.getLogger(__name__)


class OrderingAgent:
    """Agent to orchestrate the complete ordering workflow"""

    def __init__(
        self,
        tool1_url: str,
        tool2_url: str,
        output_dir: str = "./output"
    ):
        self.tool1_url = tool1_url
        self.tool2_url = tool2_url
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Session storage for workflow state
        self.session_data = {}

    async def extract_manufacturer_data(
        self,
        manufacturer_id: str,
        job_id: str
    ) -> Dict[str, Any]:
        """
        Step 1: Extract manufacturer data and generate guide
        """
        logger.info(f"[STEP 1] Extracting data for manufacturer: {manufacturer_id}")

        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    f"{self.tool1_url}/extract",
                    json={
                        "manufacturer_id": manufacturer_id,
                        "job_id": job_id
                    }
                )
                response.raise_for_status()
                data = response.json()

            logger.info(f"✓ Extract successful: {data.get('guide_uri')}")

            # Store in session
            self.session_data[job_id] = {
                "manufacturer_id": manufacturer_id,
                "guide_uri": data.get("guide_uri"),
                "schema_info": data.get("schema_info", {}),
                "extract_time": datetime.now().isoformat()
            }

            return {
                "success": True,
                "guide_uri": data.get("guide_uri"),
                "schema_info": data.get("schema_info", {}),
                "data": data
            }

        except Exception as e:
            logger.error(f"✗ Extract failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_guide_content(self, guide_uri: str) -> Dict[str, Any]:
        """
        Step 2: Fetch and review the guide content
        """
        logger.info(f"[STEP 2] Fetching guide content from: {guide_uri}")

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(guide_uri)
                response.raise_for_status()
                content = response.text

            logger.info(f"✓ Guide fetched: {len(content)} characters")

            return {
                "success": True,
                "content": content,
                "length": len(content)
            }

        except Exception as e:
            logger.error(f"✗ Guide fetch failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def finalize_order(
        self,
        guide_uri: str,
        job_id: str
    ) -> Dict[str, Any]:
        """
        Step 3: Process guide and generate Excel order file
        """
        logger.info(f"[STEP 3] Finalizing order for job: {job_id}")

        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    f"{self.tool2_url}/finalize",
                    json={
                        "guide_uri": guide_uri,
                        "job_id": job_id
                    }
                )
                response.raise_for_status()
                data = response.json()

            logger.info(f"✓ Order finalized: {data.get('order_uri')}")

            # Update session
            if job_id in self.session_data:
                self.session_data[job_id].update({
                    "order_uri": data.get("order_uri"),
                    "order_file": data.get("order_file"),
                    "finalize_time": datetime.now().isoformat()
                })

            return {
                "success": True,
                "order_uri": data.get("order_uri"),
                "order_file": data.get("order_file"),
                "data": data
            }

        except Exception as e:
            logger.error(f"✗ Finalize failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def download_order_file(
        self,
        job_id: str,
        output_filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Step 4: Download the generated Excel file
        """
        logger.info(f"[STEP 4] Downloading order file for job: {job_id}")

        if output_filename is None:
            output_filename = f"{job_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        output_path = self.output_dir / output_filename

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(
                    f"{self.tool2_url}/orders/{job_id}"
                )
                response.raise_for_status()

                # Save file
                with open(output_path, 'wb') as f:
                    f.write(response.content)

            file_size = output_path.stat().st_size
            logger.info(f"✓ File downloaded: {output_path} ({file_size} bytes)")

            # Update session
            if job_id in self.session_data:
                self.session_data[job_id].update({
                    "output_file": str(output_path),
                    "file_size": file_size,
                    "download_time": datetime.now().isoformat()
                })

            return {
                "success": True,
                "file_path": str(output_path),
                "file_size": file_size
            }

        except Exception as e:
            logger.error(f"✗ Download failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def run_complete_workflow(
        self,
        manufacturer_id: str,
        job_id: Optional[str] = None,
        review_guide: bool = True
    ) -> Dict[str, Any]:
        """
        Execute the complete ordering workflow end-to-end
        """
        if job_id is None:
            job_id = f"order-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        logger.info("=" * 80)
        logger.info(f"Starting Complete Workflow")
        logger.info(f"Manufacturer: {manufacturer_id}")
        logger.info(f"Job ID: {job_id}")
        logger.info("=" * 80)

        workflow_result = {
            "manufacturer_id": manufacturer_id,
            "job_id": job_id,
            "steps": {}
        }

        # Step 1: Extract manufacturer data
        extract_result = await self.extract_manufacturer_data(manufacturer_id, job_id)
        workflow_result["steps"]["extract"] = extract_result

        if not extract_result["success"]:
            logger.error("Workflow failed at Step 1: Extract")
            return workflow_result

        guide_uri = extract_result["guide_uri"]

        # Step 2: Review guide (optional)
        if review_guide:
            guide_result = await self.get_guide_content(guide_uri)
            workflow_result["steps"]["guide_review"] = guide_result

            if guide_result["success"]:
                # Save guide content locally
                guide_path = self.output_dir / f"{job_id}_guide.md"
                with open(guide_path, 'w') as f:
                    f.write(guide_result["content"])
                logger.info(f"Guide saved to: {guide_path}")

        # Step 3: Finalize order
        finalize_result = await self.finalize_order(guide_uri, job_id)
        workflow_result["steps"]["finalize"] = finalize_result

        if not finalize_result["success"]:
            logger.error("Workflow failed at Step 3: Finalize")
            return workflow_result

        # Step 4: Download order file
        download_result = await self.download_order_file(job_id)
        workflow_result["steps"]["download"] = download_result

        # Final summary
        workflow_result["success"] = all([
            extract_result["success"],
            finalize_result["success"],
            download_result["success"]
        ])

        logger.info("=" * 80)
        if workflow_result["success"]:
            logger.info("✓ Workflow completed successfully!")
            logger.info(f"Order file: {download_result['file_path']}")
        else:
            logger.error("✗ Workflow completed with errors")
        logger.info("=" * 80)

        # Save workflow summary
        summary_path = self.output_dir / f"{job_id}_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(workflow_result, f, indent=2)
        logger.info(f"Workflow summary saved to: {summary_path}")

        return workflow_result

    def get_session_data(self, job_id: Optional[str] = None) -> Dict[str, Any]:
        """Get session data for a specific job or all jobs"""
        if job_id:
            return self.session_data.get(job_id, {})
        return self.session_data


async def main():
    """Main entry point for testing"""
    import argparse

    parser = argparse.ArgumentParser(description='Test MCP Ordering Workflow')
    parser.add_argument(
        '--manufacturer',
        type=str,
        default='Shalom',
        help='Manufacturer name (default: Shalom)'
    )
    parser.add_argument(
        '--job-id',
        type=str,
        help='Job ID (default: auto-generated)'
    )
    parser.add_argument(
        '--tool1-url',
        type=str,
        default=os.getenv('TOOL1_BASE_URL', 'https://ags-tools-1-extract.onrender.com'),
        help='Tool #1 base URL'
    )
    parser.add_argument(
        '--tool2-url',
        type=str,
        default=os.getenv('TOOL2_BASE_URL', 'https://ags-tools-2-finalize.onrender.com'),
        help='Tool #2 base URL'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='./output',
        help='Output directory (default: ./output)'
    )
    parser.add_argument(
        '--no-review',
        action='store_true',
        help='Skip guide review step'
    )

    args = parser.parse_args()

    # Create agent
    agent = OrderingAgent(
        tool1_url=args.tool1_url,
        tool2_url=args.tool2_url,
        output_dir=args.output_dir
    )

    # Run workflow
    result = await agent.run_complete_workflow(
        manufacturer_id=args.manufacturer,
        job_id=args.job_id,
        review_guide=not args.no_review
    )

    # Exit with appropriate code
    sys.exit(0 if result.get("success") else 1)


if __name__ == "__main__":
    asyncio.run(main())
