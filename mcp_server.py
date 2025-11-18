#!/usr/bin/env python3
"""
MCP Server for AGS Orchestration Tools
Exposes ordering workflow tools via Model Context Protocol
"""

import os
import sys
import json
import asyncio
import logging
from typing import Any, Dict, Optional
import httpx
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)

# Environment variables
TOOL1_BASE_URL = os.getenv("TOOL1_BASE_URL", "https://ags-tools-1-extract.onrender.com")
TOOL2_BASE_URL = os.getenv("TOOL2_BASE_URL", "https://ags-tools-2-finalize.onrender.com")

# Create MCP server instance
app = Server("ags-orchestration")


@app.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List all available tools"""
    return [
        types.Tool(
            name="extract_manufacturer_data",
            description="Extract manufacturer data and generate ordering guide (Tool #1). "
                       "This is the first step in the ordering workflow.",
            inputSchema={
                "type": "object",
                "properties": {
                    "manufacturer_id": {
                        "type": "string",
                        "description": "Manufacturer name or ID (e.g., 'Shalom')"
                    },
                    "job_id": {
                        "type": "string",
                        "description": "Unique job identifier (e.g., 'order-001')"
                    }
                },
                "required": ["manufacturer_id", "job_id"]
            }
        ),
        types.Tool(
            name="finalize_order",
            description="Process the guide and generate Excel order file (Tool #2). "
                       "This is the second step, using the guide_uri from extract_manufacturer_data.",
            inputSchema={
                "type": "object",
                "properties": {
                    "guide_uri": {
                        "type": "string",
                        "description": "URI of the guide.md file from extract_manufacturer_data"
                    },
                    "job_id": {
                        "type": "string",
                        "description": "Job identifier (should match the one used in extract_manufacturer_data)"
                    }
                },
                "required": ["guide_uri", "job_id"]
            }
        ),
        types.Tool(
            name="get_order_file",
            description="Download the generated Excel order file",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_id": {
                        "type": "string",
                        "description": "Job identifier"
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Optional local path to save the file (defaults to ./output/{job_id}.xlsx)"
                    }
                },
                "required": ["job_id"]
            }
        ),
        types.Tool(
            name="get_guide_content",
            description="View the content of a guide.md file",
            inputSchema={
                "type": "object",
                "properties": {
                    "guide_uri": {
                        "type": "string",
                        "description": "URI of the guide.md file"
                    }
                },
                "required": ["guide_uri"]
            }
        )
    ]


@app.call_tool()
async def handle_call_tool(
    name: str,
    arguments: dict
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool execution requests"""

    try:
        if name == "extract_manufacturer_data":
            return await extract_manufacturer_data(
                arguments["manufacturer_id"],
                arguments["job_id"]
            )

        elif name == "finalize_order":
            return await finalize_order(
                arguments["guide_uri"],
                arguments["job_id"]
            )

        elif name == "get_order_file":
            return await get_order_file(
                arguments["job_id"],
                arguments.get("output_path")
            )

        elif name == "get_guide_content":
            return await get_guide_content(
                arguments["guide_uri"]
            )

        else:
            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        logger.error(f"Error executing tool {name}: {str(e)}", exc_info=True)
        error_result = {
            "status": "error",
            "error": str(e),
            "tool": name
        }
        return [types.TextContent(
            type="text",
            text=json.dumps(error_result, indent=2)
        )]


async def extract_manufacturer_data(manufacturer_id: str, job_id: str) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Call Tool #1: Extract manufacturer data"""
    logger.info(f"Extracting data for manufacturer: {manufacturer_id}, job: {job_id}")

    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{TOOL1_BASE_URL}/extract",
                json={
                    "manufacturer_id": manufacturer_id,
                    "job_id": job_id
                }
            )

            # Check HTTP status
            if response.status_code != 200:
                error_text = response.text[:500] if response.text else "No response body"
                raise httpx.HTTPStatusError(
                    f"HTTP {response.status_code}: {error_text}",
                    request=response.request,
                    response=response
                )

            # Try to parse JSON response
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                logger.error(f"External API returned invalid JSON: {response.text[:500]}")
                raise ValueError(f"External API returned invalid JSON: {e}")

    except httpx.ConnectError as e:
        raise ConnectionError(f"Failed to connect to {TOOL1_BASE_URL}: {e}")
    except httpx.TimeoutException as e:
        raise TimeoutError(f"Request to {TOOL1_BASE_URL} timed out: {e}")

    result = {
        "status": "success",
        "manufacturer_id": manufacturer_id,
        "job_id": job_id,
        "guide_uri": data.get("guide_uri"),
        "schema_info": data.get("schema_info", {}),
        "message": f"Successfully extracted data for {manufacturer_id}. Guide available at: {data.get('guide_uri')}"
    }

    logger.info(f"Extract completed: {result}")

    return [types.TextContent(
        type="text",
        text=json.dumps(result, indent=2)
    )]


async def finalize_order(guide_uri: str, job_id: str) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Call Tool #2: Finalize order and generate Excel"""
    # Handle relative paths by prepending the base URL
    if guide_uri.startswith('/'):
        full_guide_uri = f"{TOOL1_BASE_URL}{guide_uri}"
    else:
        full_guide_uri = guide_uri

    logger.info(f"Finalizing order for job: {job_id}, guide: {full_guide_uri}")

    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{TOOL2_BASE_URL}/finalize",
                json={
                    "guide_uri": full_guide_uri,
                    "job_id": job_id
                }
            )

            if response.status_code != 200:
                error_text = response.text[:500] if response.text else "No response body"
                raise httpx.HTTPStatusError(
                    f"HTTP {response.status_code}: {error_text}",
                    request=response.request,
                    response=response
                )

            try:
                data = response.json()
            except json.JSONDecodeError as e:
                logger.error(f"External API returned invalid JSON: {response.text[:500]}")
                raise ValueError(f"External API returned invalid JSON: {e}")

    except httpx.ConnectError as e:
        raise ConnectionError(f"Failed to connect to {TOOL2_BASE_URL}: {e}")
    except httpx.TimeoutException as e:
        raise TimeoutError(f"Request to {TOOL2_BASE_URL} timed out: {e}")

    result = {
        "status": "success",
        "job_id": job_id,
        "order_uri": data.get("order_uri"),
        "order_file": data.get("order_file"),
        "message": f"Successfully generated order file. Download at: {data.get('order_uri')}"
    }

    logger.info(f"Finalize completed: {result}")

    return [types.TextContent(
        type="text",
        text=json.dumps(result, indent=2)
    )]


async def get_order_file(job_id: str, output_path: Optional[str] = None) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Download the Excel order file"""
    if output_path is None:
        output_path = f"./output/{job_id}.xlsx"

    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else "./output", exist_ok=True)

    logger.info(f"Downloading order file for job: {job_id} to {output_path}")

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(
                f"{TOOL2_BASE_URL}/orders/{job_id}"
            )

            if response.status_code != 200:
                error_text = response.text[:500] if response.text else "No response body"
                raise httpx.HTTPStatusError(
                    f"HTTP {response.status_code}: {error_text}",
                    request=response.request,
                    response=response
                )

            # Save the file
            with open(output_path, 'wb') as f:
                f.write(response.content)

    except httpx.ConnectError as e:
        raise ConnectionError(f"Failed to connect to {TOOL2_BASE_URL}: {e}")
    except httpx.TimeoutException as e:
        raise TimeoutError(f"Request to {TOOL2_BASE_URL} timed out: {e}")

    result = {
        "status": "success",
        "job_id": job_id,
        "file_path": output_path,
        "file_size": len(response.content),
        "message": f"Order file downloaded successfully to {output_path}"
    }

    logger.info(f"Download completed: {result}")

    return [types.TextContent(
        type="text",
        text=json.dumps(result, indent=2)
    )]


async def get_guide_content(guide_uri: str) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Fetch and return guide content"""
    # Handle relative paths by prepending the base URL
    if guide_uri.startswith('/'):
        full_url = f"{TOOL1_BASE_URL}{guide_uri}"
    else:
        full_url = guide_uri

    logger.info(f"Fetching guide content from: {full_url}")

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(full_url)

            if response.status_code != 200:
                error_text = response.text[:500] if response.text else "No response body"
                raise httpx.HTTPStatusError(
                    f"HTTP {response.status_code}: {error_text}",
                    request=response.request,
                    response=response
                )

            content = response.text

    except httpx.ConnectError as e:
        raise ConnectionError(f"Failed to connect to {full_url}: {e}")
    except httpx.TimeoutException as e:
        raise TimeoutError(f"Request to {full_url} timed out: {e}")

    result = {
        "status": "success",
        "guide_uri": guide_uri,
        "content": content,
        "content_length": len(content)
    }

    return [types.TextContent(
        type="text",
        text=json.dumps(result, indent=2)
    )]


async def main():
    """Main entry point for the MCP server"""
    logger.info("Starting AGS Orchestration MCP Server")
    logger.info(f"Tool #1 URL: {TOOL1_BASE_URL}")
    logger.info(f"Tool #2 URL: {TOOL2_BASE_URL}")

    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="ags-orchestration",
                server_version="1.0.0",
                capabilities=app.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
