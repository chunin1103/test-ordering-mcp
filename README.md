# MCP Ordering System - Testing Agent

Automated testing system for the AGS Ordering workflow using Model Context Protocol (MCP).

## Overview

This repository contains:
- **MCP Server** (`mcp_server.py`) - Exposes ordering workflow tools via MCP
- **Testing Agent** (`test_agent.py`) - Automated agent to test the complete ordering workflow
- **Example Scripts** - Various test scenarios

## Workflow

The ordering system follows this workflow:

```
1. Extract Manufacturer Data (Tool #1)
   ↓
2. Review Generated Guide (optional)
   ↓
3. Finalize Order (Tool #2)
   ↓
4. Download Excel File
```

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd test-ordering-mcp

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Tool URLs if different from defaults
```

### 2. Run the Testing Agent

**Basic usage** (tests Shalom manufacturer):
```bash
python test_agent.py
```

**Custom manufacturer**:
```bash
python test_agent.py --manufacturer "Shalom"
```

**Custom job ID**:
```bash
python test_agent.py --manufacturer "Shalom" --job-id "order-001"
```

**All options**:
```bash
python test_agent.py \
  --manufacturer "Shalom" \
  --job-id "order-001" \
  --tool1-url "https://ags-tools-1-extract.onrender.com" \
  --tool2-url "https://ags-tools-2-finalize.onrender.com" \
  --output-dir "./output"
```

### 3. Check Results

After running the agent, check the `./output` directory:
- `{job_id}_{timestamp}.xlsx` - The generated order file
- `{job_id}_guide.md` - The generated guide
- `{job_id}_summary.json` - Workflow execution summary
- `test_agent.log` - Detailed logs

## MCP Server Setup

### For Claude Desktop (macOS)

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ags-orchestration": {
      "command": "python",
      "args": [
        "/path/to/test-ordering-mcp/mcp_server.py"
      ],
      "env": {
        "TOOL1_BASE_URL": "https://ags-tools-1-extract.onrender.com",
        "TOOL2_BASE_URL": "https://ags-tools-2-finalize.onrender.com"
      }
    }
  }
}
```

### For Cursor IDE

Edit `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "ags-orchestration": {
      "command": "python",
      "args": [
        "/path/to/test-ordering-mcp/mcp_server.py"
      ],
      "env": {
        "TOOL1_BASE_URL": "https://ags-tools-1-extract.onrender.com",
        "TOOL2_BASE_URL": "https://ags-tools-2-finalize.onrender.com"
      }
    }
  }
}
```

### For Windows (Claude Desktop)

Edit `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ags-orchestration": {
      "command": "python",
      "args": [
        "C:\\path\\to\\test-ordering-mcp\\mcp_server.py"
      ],
      "env": {
        "TOOL1_BASE_URL": "https://ags-tools-1-extract.onrender.com",
        "TOOL2_BASE_URL": "https://ags-tools-2-finalize.onrender.com"
      }
    }
  }
}
```

## Using MCP Tools in Claude/ChatGPT

Once the MCP server is configured, you can use these commands:

### Example 1: Complete Workflow

```
Use extract_manufacturer_data to create an order for Shalom manufacturer with job_id "order-001"
```

Then:
```
Use finalize_order with the guide_uri from the previous step
```

Finally:
```
Download the order file using get_order_file
```

### Example 2: With Guide Review

```
Extract data for Shalom (job_id: order-002), then show me the guide content before finalizing
```

## Available MCP Tools

### 1. extract_manufacturer_data

Extracts manufacturer data and generates an ordering guide.

**Parameters:**
- `manufacturer_id` (string, required): Manufacturer name (e.g., "Shalom")
- `job_id` (string, required): Unique job identifier

**Returns:**
- `guide_uri`: URL to the generated guide
- `schema_info`: Schema information

### 2. finalize_order

Processes the guide and generates an Excel order file.

**Parameters:**
- `guide_uri` (string, required): URI from extract_manufacturer_data
- `job_id` (string, required): Job identifier

**Returns:**
- `order_uri`: URL to download the order file
- `order_file`: Filename of the generated Excel

### 3. get_order_file

Downloads the generated Excel file.

**Parameters:**
- `job_id` (string, required): Job identifier
- `output_path` (string, optional): Local path to save file

**Returns:**
- `file_path`: Path to downloaded file
- `file_size`: Size in bytes

### 4. get_guide_content

Views the content of a guide file.

**Parameters:**
- `guide_uri` (string, required): URI of the guide

**Returns:**
- `content`: Guide markdown content

## Testing Agent API

You can also use the agent programmatically:

```python
import asyncio
from test_agent import OrderingAgent

async def main():
    agent = OrderingAgent(
        tool1_url="https://ags-tools-1-extract.onrender.com",
        tool2_url="https://ags-tools-2-finalize.onrender.com",
        output_dir="./output"
    )

    # Run complete workflow
    result = await agent.run_complete_workflow(
        manufacturer_id="Shalom",
        job_id="order-001",
        review_guide=True
    )

    if result["success"]:
        print(f"Order file: {result['steps']['download']['file_path']}")
    else:
        print("Workflow failed")

asyncio.run(main())
```

## Project Structure

```
test-ordering-mcp/
├── mcp_server.py          # MCP server implementation
├── test_agent.py          # Automated testing agent
├── requirements.txt       # Python dependencies
├── .env.example          # Environment configuration template
├── .gitignore            # Git ignore rules
├── README.md             # This file
└── output/               # Generated files (created automatically)
    ├── *.xlsx            # Order files
    ├── *_guide.md        # Guide files
    ├── *_summary.json    # Workflow summaries
    └── *.log             # Log files
```

## Troubleshooting

### MCP Server Not Starting

1. Check Python version (requires 3.8+):
   ```bash
   python --version
   ```

2. Verify dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Test manually:
   ```bash
   python mcp_server.py
   ```

### Tool URLs Not Reachable

1. Verify URLs in `.env` or command line:
   ```bash
   curl https://ags-tools-1-extract.onrender.com/health
   curl https://ags-tools-2-finalize.onrender.com/health
   ```

2. Check firewall/proxy settings

### Files Not Downloading

1. Check output directory permissions:
   ```bash
   mkdir -p ./output
   ls -la ./output
   ```

2. Verify Tool #2 URL is correct

### Workflow Fails

Check the logs for detailed error information:
- Console output (stdout)
- `test_agent.log` file
- `{job_id}_summary.json` for step-by-step results

## Advanced Usage

### Custom Test Scenarios

Create a custom test script:

```python
# my_test.py
import asyncio
from test_agent import OrderingAgent

async def test_multiple_manufacturers():
    agent = OrderingAgent(
        tool1_url="...",
        tool2_url="..."
    )

    manufacturers = ["Shalom", "Manufacturer2", "Manufacturer3"]

    for mfr in manufacturers:
        job_id = f"order-{mfr.lower()}-001"
        result = await agent.run_complete_workflow(mfr, job_id)
        print(f"{mfr}: {'✓' if result['success'] else '✗'}")

asyncio.run(test_multiple_manufacturers())
```

### Integration with CI/CD

Add to your CI pipeline:

```yaml
# .github/workflows/test-ordering.yml
name: Test Ordering Workflow

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run test agent
        env:
          TOOL1_BASE_URL: ${{ secrets.TOOL1_BASE_URL }}
          TOOL2_BASE_URL: ${{ secrets.TOOL2_BASE_URL }}
        run: python test_agent.py --manufacturer Shalom
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TOOL1_BASE_URL` | Base URL for Tool #1 (Extract) | `https://ags-tools-1-extract.onrender.com` |
| `TOOL2_BASE_URL` | Base URL for Tool #2 (Finalize) | `https://ags-tools-2-finalize.onrender.com` |
| `OUTPUT_DIR` | Directory for output files | `./output` |

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with the agent
5. Submit a pull request

## License

[Your License Here]

## Support

For issues or questions:
- Check the logs in `test_agent.log`
- Review the workflow summary in `output/{job_id}_summary.json`
- Open an issue in the repository
