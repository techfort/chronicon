# Chronicon Development

## Setup

1. Install dependencies:
```bash
pip install -e ".[dev]"
```

2. Set your Anthropic API key:
```bash
export ANTHROPIC_API_KEY="your-key-here"
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=chronicon --cov-report=html

# Run specific test file
pytest tests/test_workflow.py
```

## Running Examples

```bash
# Simple example
python examples/simple.py

# Full summarization example
python examples/summarize.py
```

## Project Structure

```
chronicon/
├── src/chronicon/
│   ├── __init__.py          # Public API
│   ├── workflow.py          # @workflow decorator
│   ├── step.py              # Step abstraction + llm_call
│   ├── execution.py         # Execution engine
│   ├── replay.py            # Replay engine
│   ├── log.py               # SQLite execution log
│   ├── hash.py              # Versioning utilities
│   └── serialization.py     # JSON serialization
├── tests/
│   ├── test_workflow.py
│   ├── test_execution.py
│   ├── test_replay.py
│   ├── test_hash.py
│   ├── test_serialization.py
│   └── test_log.py
└── examples/
    ├── simple.py            # Minimal example
    └── summarize.py         # Full example
```

## Core Design

**Determinism First**: Every workflow execution is:
1. Logged to SQLite (append-only)
2. Replayable from logs
3. Version-tracked (source code hashing)

**Explicit State**: No hidden globals, no magic context. Everything is:
- Passed as arguments
- Returned as results
- Logged in the database

**Two Kinds of Steps**:
- **Pure**: Re-executed during replay (deterministic)
- **Effectful**: Replayed from logs (LLM calls, API calls, IO)

## Testing Philosophy

Tests should work against **real past executions**, not mocks:

```python
# Bad (mocked)
mock_llm.return_value = "test"

# Good (replayed)
result = replay(workflow, execution_id="abc123")
assert result.output == expected
```

## Future Work (Not in MVP)

- [ ] Parallel step execution
- [ ] Multiple LLM providers
- [ ] Cloud deployment
- [ ] Web UI
- [ ] Agent patterns
- [ ] Distributed execution

The MVP is intentionally minimal. We're building the boring, correct core first.
