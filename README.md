# Chronicon

**Deterministic, replayable LLM workflows with first-class testing.**

Chronicon is a workflow engine for building LLM applications that can be:
- **Replayed** exactly from execution logs
- **Tested** against real past executions (no mocks)
- **Debugged** with full visibility into every step

## What This Is NOT

- ❌ An agent framework
- ❌ A prompt library
- ❌ A distributed system
- ❌ A flexible DSL

## Core Principles

- **Determinism first**: If a workflow ran once, it must be replayable from logs
- **Explicit state**: No hidden globals or magic context
- **Side effects are explicit**: LLM calls, API calls, and IO are logged
- **Minimal surface area**: Opinionated over flexible
- **Local-first**: Single-process runtime

## Quick Start

```python
from chronicon import workflow, step, llm_call

@workflow
def summarize(url: str) -> tuple[str, int]:
    # Fetch text (effectful)
    text = fetch(url)
    
    # LLM summarization (effectful, logged)
    summary = llm_call(
        prompt=f"Summarize this text:\n\n{text}",
        model="claude-3-5-sonnet-20241022",
    )
    
    # Score quality (effectful, logged)
    score = llm_call(
        prompt=f"Rate this summary 1-10:\n\n{summary}",
        model="claude-3-5-sonnet-20241022",
    )
    
    return summary, int(score)

# Run it
execution = summarize.run(url="https://example.com")

# Replay it exactly
execution = summarize.replay(execution_id=execution.id)

# Test against past execution
assert summarize.replay(execution_id="abc123").output == expected_output
```

## Core Abstractions

### Workflow
A Python function decorated with `@workflow`. Workflows are:
- Versioned by source code hash
- Explicit about inputs and outputs
- Replayable from execution logs

### Step
Atomic unit of execution. Two kinds:
- **Pure**: Deterministic functions
- **Effectful**: LLM calls, API calls, IO

All steps are:
- Hashable and identifiable
- Inputs and outputs are serializable
- Logged in execution trace

### Execution Log
Append-only SQLite database recording:
- Workflow version hash
- Step ID + version hash
- Inputs and outputs (serialized)
- LLM request parameters
- Timestamps and errors

### Replay Engine
Can:
- Replay an execution deterministically
- Resume from step N
- Detect divergence (hash mismatch, input change, code change)
- Explain why a replay diverged

## Documentation

- **[Quick Start Guide](QUICKSTART.md)** - Get running in 5 minutes
- **[Project Structure](STRUCTURE.md)** - Architecture and design
- **[Development Guide](DEVELOPMENT.md)** - Contributing and testing
- **[Project Summary](PROJECT_SUMMARY.md)** - Complete implementation details

## Installation

```bash
# Clone and install
git clone <repo-url>
cd chronicon
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

# Set API key
export ANTHROPIC_API_KEY="your-key-here"
```

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black .
ruff check .
```

## Status

**MVP in progress.** Chronicon is v0: local-only, single-process, sequential execution.

What's working:
- ✅ Workflow definition and versioning
- ✅ Execution logging (SQLite)
- ✅ Deterministic replay
- ✅ LLM call tracking (Anthropic)

What's not (and won't be in v0):
- ❌ Parallelism
- ❌ Agents
- ❌ Multiple LLM providers
- ❌ Cloud deployment
- ❌ UI

## License

MIT
