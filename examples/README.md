# Example Test Scripts

This directory contains example scripts demonstrating different ways to use the ordering workflow agent.

## Available Examples

### 1. Simple Test (`simple_test.py`)

Basic end-to-end test for a single manufacturer.

**Usage:**
```bash
python examples/simple_test.py
```

**Features:**
- Tests complete workflow for Shalom manufacturer
- Reviews guide content
- Downloads order file
- Generates summary

### 2. Multi-Manufacturer Test (`multi_manufacturer_test.py`)

Tests multiple manufacturers in sequence.

**Usage:**
```bash
python examples/multi_manufacturer_test.py
```

**Features:**
- Tests multiple manufacturers
- Runs workflows in sequence
- Provides overall pass/fail summary
- Measures total execution time
- Skips guide review for faster execution

**Customization:**
Edit the `manufacturers` list in the script:
```python
manufacturers = [
    "Shalom",
    "Manufacturer2",
    "Manufacturer3",
]
```

### 3. Custom Workflow Test (`custom_workflow_test.py`)

Demonstrates step-by-step control over the workflow.

**Usage:**
```bash
python examples/custom_workflow_test.py
```

**Features:**
- Manual control over each step
- Guide content validation
- Preview of guide content
- Session data inspection
- Useful for debugging or custom logic

## Running the Examples

### Prerequisites

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set environment variables (optional):
   ```bash
   export TOOL1_BASE_URL="https://ags-tools-1-extract.onrender.com"
   export TOOL2_BASE_URL="https://ags-tools-2-finalize.onrender.com"
   ```

### Run All Examples

```bash
# Simple test
python examples/simple_test.py

# Multi-manufacturer test
python examples/multi_manufacturer_test.py

# Custom workflow test
python examples/custom_workflow_test.py
```

## Output

All examples generate files in the `./output/` directory:
- `{job_id}_{timestamp}.xlsx` - Order files
- `{job_id}_guide.md` - Guide files
- `{job_id}_summary.json` - Workflow summaries (simple test only)

## Creating Your Own Tests

Use these examples as templates for your own tests:

```python
import asyncio
from test_agent import OrderingAgent

async def my_custom_test():
    # Create agent
    agent = OrderingAgent(
        tool1_url="...",
        tool2_url="...",
        output_dir="./output"
    )

    # Your custom logic here
    result = await agent.run_complete_workflow(
        manufacturer_id="YourManufacturer",
        job_id="your-test-001"
    )

    return result

asyncio.run(my_custom_test())
```

## Troubleshooting

If examples fail:

1. Check Tool URLs are accessible:
   ```bash
   curl https://ags-tools-1-extract.onrender.com/health
   curl https://ags-tools-2-finalize.onrender.com/health
   ```

2. Review logs:
   ```bash
   cat test_agent.log
   ```

3. Check output directory permissions:
   ```bash
   ls -la ./output
   ```

## Integration Testing

These examples can be integrated into CI/CD pipelines:

```yaml
# GitHub Actions example
- name: Run ordering tests
  run: |
    python examples/simple_test.py
    python examples/multi_manufacturer_test.py
```

## Advanced Usage

### Parallel Testing

Run multiple tests concurrently:

```python
async def parallel_tests():
    agent = OrderingAgent(...)

    tasks = [
        agent.run_complete_workflow("Shalom", "job-1"),
        agent.run_complete_workflow("Mfr2", "job-2"),
        agent.run_complete_workflow("Mfr3", "job-3"),
    ]

    results = await asyncio.gather(*tasks)
    return results
```

### Custom Validation

Add your own validation logic:

```python
async def validated_workflow(agent, manufacturer):
    result = await agent.run_complete_workflow(manufacturer, "job-001")

    # Custom validation
    if result["success"]:
        file_path = result["steps"]["download"]["file_path"]
        # Validate Excel file structure
        validate_excel_file(file_path)

    return result
```
