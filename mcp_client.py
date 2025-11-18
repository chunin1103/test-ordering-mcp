#!/usr/bin/env python3
"""
MCP Client for AGS Orchestration Tools

This client connects to the MCP server to discover and call tools
via the Model Context Protocol.
"""

import os
import sys
import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('mcp_client.log')
    ]
)
logger = logging.getLogger(__name__)


class MCPOrderingClient:
    """MCP Client for the ordering workflow"""

    def __init__(self, server_script: str = "mcp_server.py"):
        self.server_script = server_script
        self.session: Optional[ClientSession] = None
        self.output_dir = Path("./output")
        self.output_dir.mkdir(exist_ok=True)

    async def connect(self) -> None:
        """Connect to the MCP server"""
        logger.info(f"Connecting to MCP server: {self.server_script}")

        # Server parameters for stdio connection
        server_params = StdioServerParameters(
            command=sys.executable,  # Python executable
            args=[self.server_script],
            env={
                **os.environ,
                "TOOL1_BASE_URL": os.getenv("TOOL1_BASE_URL", "https://ags-tools-1-extract.onrender.com"),
                "TOOL2_BASE_URL": os.getenv("TOOL2_BASE_URL", "https://ags-tools-2-finalize.onrender.com"),
            }
        )

        # Create stdio client connection
        self._stdio_context = stdio_client(server_params)
        self._streams = await self._stdio_context.__aenter__()

        # Create and initialize session
        self.session = ClientSession(self._streams[0], self._streams[1])
        await self.session.__aenter__()

        # Initialize the connection
        result = await self.session.initialize()
        logger.info(f"Connected to server: {result.server_info.name} v{result.server_info.version}")

    async def disconnect(self) -> None:
        """Disconnect from the MCP server"""
        if self.session:
            await self.session.__aexit__(None, None, None)
        if hasattr(self, '_stdio_context'):
            await self._stdio_context.__aexit__(None, None, None)
        logger.info("Disconnected from MCP server")

    async def list_tools(self) -> list:
        """List all available tools from the MCP server"""
        if not self.session:
            raise RuntimeError("Not connected to MCP server")

        result = await self.session.list_tools()
        tools = result.tools

        logger.info(f"Available tools ({len(tools)}):")
        for tool in tools:
            logger.info(f"  - {tool.name}: {tool.description}")

        return tools

    async def get_tool_schema(self, tool_name: str) -> Dict[str, Any]:
        """Get the schema for a specific tool"""
        tools = await self.list_tools()

        for tool in tools:
            if tool.name == tool_name:
                return {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema
                }

        raise ValueError(f"Tool not found: {tool_name}")

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Call a tool on the MCP server"""
        if not self.session:
            raise RuntimeError("Not connected to MCP server")

        logger.info(f"Calling tool: {tool_name}")
        logger.info(f"Arguments: {json.dumps(arguments, indent=2)}")

        result = await self.session.call_tool(tool_name, arguments)

        # Extract text content from result
        response_text = ""
        for content in result.content:
            if hasattr(content, 'text'):
                response_text += content.text

        logger.info(f"Tool response received")
        return response_text

    async def run_workflow(
        self,
        manufacturer_id: str,
        job_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run the complete ordering workflow via MCP"""

        if job_id is None:
            job_id = f"order-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        logger.info("=" * 80)
        logger.info("Starting MCP Workflow")
        logger.info(f"Manufacturer: {manufacturer_id}")
        logger.info(f"Job ID: {job_id}")
        logger.info("=" * 80)

        workflow_result = {
            "manufacturer_id": manufacturer_id,
            "job_id": job_id,
            "steps": {}
        }

        try:
            # Step 1: Extract manufacturer data
            logger.info("[STEP 1] Extracting manufacturer data...")
            extract_response = await self.call_tool(
                "extract_manufacturer_data",
                {
                    "manufacturer_id": manufacturer_id,
                    "job_id": job_id
                }
            )
            extract_data = json.loads(extract_response)
            workflow_result["steps"]["extract"] = extract_data

            if extract_data.get("status") != "success":
                logger.error("[ERROR] Extract failed")
                return workflow_result

            guide_uri = extract_data.get("guide_uri")
            logger.info(f"[OK] Extract successful: {guide_uri}")

            # Step 2: Get guide content (optional review)
            logger.info("[STEP 2] Fetching guide content...")
            guide_response = await self.call_tool(
                "get_guide_content",
                {"guide_uri": guide_uri}
            )
            guide_data = json.loads(guide_response)
            workflow_result["steps"]["guide_review"] = {
                "success": guide_data.get("status") == "success",
                "length": guide_data.get("content_length", 0)
            }

            if guide_data.get("status") == "success":
                # Save guide locally
                guide_path = self.output_dir / f"{job_id}_guide.md"
                with open(guide_path, 'w') as f:
                    f.write(guide_data.get("content", ""))
                logger.info(f"[OK] Guide saved to: {guide_path}")

            # Step 3: Finalize order
            logger.info("[STEP 3] Finalizing order...")
            finalize_response = await self.call_tool(
                "finalize_order",
                {
                    "guide_uri": guide_uri,
                    "job_id": job_id
                }
            )
            finalize_data = json.loads(finalize_response)
            workflow_result["steps"]["finalize"] = finalize_data

            if finalize_data.get("status") != "success":
                logger.error("[ERROR] Finalize failed")
                return workflow_result

            logger.info(f"[OK] Order finalized: {finalize_data.get('order_uri')}")

            # Step 4: Download order file
            logger.info("[STEP 4] Downloading order file...")
            download_response = await self.call_tool(
                "get_order_file",
                {"job_id": job_id}
            )
            download_data = json.loads(download_response)
            workflow_result["steps"]["download"] = download_data

            if download_data.get("status") == "success":
                logger.info(f"[OK] File downloaded: {download_data.get('file_path')}")
            else:
                logger.error(f"[ERROR] Download failed: {download_data.get('message', 'Unknown error')}")

            # Final status
            workflow_result["success"] = all([
                extract_data.get("status") == "success",
                finalize_data.get("status") == "success",
                download_data.get("status") == "success"
            ])

        except Exception as e:
            logger.error(f"[ERROR] Workflow failed: {str(e)}")
            workflow_result["success"] = False
            workflow_result["error"] = str(e)

        logger.info("=" * 80)
        if workflow_result.get("success"):
            logger.info("[OK] Workflow completed successfully!")
        else:
            logger.error("[ERROR] Workflow completed with errors")
        logger.info("=" * 80)

        # Save summary
        summary_path = self.output_dir / f"{job_id}_mcp_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(workflow_result, f, indent=2)
        logger.info(f"Workflow summary saved to: {summary_path}")

        return workflow_result


async def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='MCP Client for Ordering Workflow')
    parser.add_argument(
        '--list-tools',
        action='store_true',
        help='List available tools and exit'
    )
    parser.add_argument(
        '--schema',
        type=str,
        help='Get schema for a specific tool'
    )
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
        '--server',
        type=str,
        default='mcp_server.py',
        help='Path to MCP server script'
    )

    args = parser.parse_args()

    # Create client
    client = MCPOrderingClient(server_script=args.server)

    try:
        # Connect to server
        await client.connect()

        if args.list_tools:
            # Just list tools and exit
            tools = await client.list_tools()
            print("\nTool Schemas:")
            for tool in tools:
                print(f"\n{tool.name}:")
                print(f"  Description: {tool.description}")
                print(f"  Input Schema: {json.dumps(tool.inputSchema, indent=4)}")

        elif args.schema:
            # Get specific tool schema
            schema = await client.get_tool_schema(args.schema)
            print(json.dumps(schema, indent=2))

        else:
            # Run complete workflow
            result = await client.run_workflow(
                manufacturer_id=args.manufacturer,
                job_id=args.job_id
            )
            sys.exit(0 if result.get("success") else 1)

    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
