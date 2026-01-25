# Testing and Validation Guide for VOXERA

This guide covers how to check and test the VOXERA codebase.

## Prerequisites

Make sure you have all dependencies installed:

```bash
# Using Poetry (recommended)
poetry install

# Or using pip
pip install -r requirements.txt
pip install pytest pytest-asyncio httpx
```

## 1. Syntax Check

Check for syntax errors without running the code:

```bash
# Check all Python files
python -m py_compile app/**/*.py tests/**/*.py

# Check specific files
python -m py_compile app/main.py app/services/asr.py
```

## 2. Linting

### Using Ruff (Fast Python linter)

```bash
# Check all files
ruff check app/ tests/

# Check and auto-fix issues
ruff check --fix app/ tests/

# Check specific files
ruff check app/services/asr.py
```

### Using Black (Code formatter)

```bash
# Check formatting (dry-run)
black --check app/ tests/

# Format code
black app/ tests/

# Format specific files
black app/services/asr.py
```

## 3. Type Checking

### Using MyPy

```bash
# Check types
mypy app/

# Check with strict mode
mypy app/ --strict
```

## 4. Running Tests

### Run All Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=app --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_audio_pipeline.py -v

# Run specific test function
pytest tests/test_e2e_asr.py::test_websocket_connection -v
```

### Run End-to-End Tests

```bash
# Run all E2E tests
pytest tests/test_e2e_asr.py -v

# Run specific E2E test
pytest tests/test_e2e_asr.py::test_asr_partial_transcript_emission -v

# Run with detailed output
pytest tests/test_e2e_asr.py -v -s
```

### Run Unit Tests

```bash
# Run audio pipeline unit tests
pytest tests/test_audio_pipeline.py -v
```

## 5. Test Server Startup

Check if the server starts without errors:

```bash
# Start server (development mode)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using Python
python -m uvicorn app.main:app --reload
```

If the server starts successfully, you should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

## 6. Manual API Testing

### Test Health Endpoint

```bash
# Using curl
curl http://localhost:8000/api/v1/health

# Expected response:
# {"status":"healthy","version":"0.1.0"}
```

### Test WebSocket Connection

Using Python script:

```python
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/api/v1/ws/audio?call_id=test-123"
    async with websockets.connect(uri) as websocket:
        # Receive connection acknowledgment
        message = await websocket.recv()
        print(f"Received: {json.loads(message)}")
        
        # Send audio chunk
        audio_chunk = b"\x00" * 320  # 20ms PCM chunk
        await websocket.send(audio_chunk)
        print("Sent audio chunk")

asyncio.run(test_websocket())
```

Or using `wscat` (if installed):

```bash
# Install wscat: npm install -g wscat
wscat -c ws://localhost:8000/api/v1/ws/audio?call_id=test-123
```

## 7. Comprehensive Check Script

Create a script to run all checks:

```bash
#!/bin/bash
# check_all.sh

echo "🔍 Running syntax check..."
python -m py_compile app/**/*.py tests/**/*.py && echo "✅ Syntax OK" || echo "❌ Syntax errors"

echo "🔍 Running linter..."
ruff check app/ tests/ && echo "✅ Linting OK" || echo "❌ Linting issues"

echo "🔍 Running tests..."
pytest -v && echo "✅ Tests passed" || echo "❌ Tests failed"

echo "✅ All checks complete!"
```

Make it executable:
```bash
chmod +x check_all.sh
./check_all.sh
```

## 8. Continuous Integration

If using GitHub Actions or similar, you can set up automated checks:

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install poetry
          poetry install
      - name: Lint
        run: poetry run ruff check app/ tests/
      - name: Test
        run: poetry run pytest -v --cov=app
```

## 9. Quick Validation Checklist

Before committing code:

- [ ] Syntax check passes: `python -m py_compile app/**/*.py`
- [ ] Linter passes: `ruff check app/ tests/`
- [ ] All tests pass: `pytest -v`
- [ ] Server starts: `uvicorn app.main:app --reload`
- [ ] Type hints checked: `mypy app/` (optional)

## 10. Troubleshooting

### Common Issues

**Import Errors:**
```bash
# Check if all imports are correct
python -c "from app.main import app; print('Imports OK')"
```

**Test Failures:**
```bash
# Run tests with more verbose output
pytest -v -s

# Run tests and show print statements
pytest -v -s --capture=no
```

**Server Won't Start:**
```bash
# Check for syntax errors first
python -m py_compile app/main.py

# Check imports
python -c "import app.main"

# Check configuration
python -c "from app.core.config import settings; print(settings.ENVIRONMENT)"
```

## 11. Performance Testing

Test ASR latency and performance:

```bash
# Run E2E tests with timing
pytest tests/test_e2e_asr.py::test_asr_latency_within_bounds -v -s

# Run with pytest-benchmark (if installed)
pytest tests/ --benchmark-only
```

## Summary

Quick commands for daily use:

```bash
# Quick check (syntax + lint)
python -m py_compile app/**/*.py && ruff check app/

# Run all tests
pytest -v

# Start server
uvicorn app.main:app --reload
```

For more details, see the [README.md](README.md) file.
