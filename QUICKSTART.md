# Quick Start Guide

## Installation

```bash
cd chronicon
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

## Set API Key

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

## Your First Workflow

Create `my_workflow.py`:

```python
from chronicon import workflow, execute, replay, llm_call
from chronicon.log import ExecutionLog

@workflow
def hello_world(name: str) -> dict:
    """A simple workflow that greets someone."""
    
    # LLM call (logged and replayable)
    greeting = llm_call(
        prompt=f"Generate a creative greeting for {name}",
        model="claude-3-5-sonnet-20241022",
        temperature=0.7,
        max_tokens=100,
    )
    
    return {
        "name": name,
        "greeting": greeting,
    }


if __name__ == "__main__":
    # Create execution log
    log = ExecutionLog("my_app.db")
    
    # Run workflow
    print("Running workflow...")
    result = execute(hello_world, name="Alice", log=log)
    
    if result.success:
        print(f"✅ Success!")
        print(f"   Execution ID: {result.execution_id}")
        print(f"   Output: {result.output}")
        print()
        
        # Replay it
        print("Replaying workflow...")
        replay_result = replay(
            hello_world,
            execution_id=result.execution_id,
            log=log,
        )
        
        print(f"✅ Replay successful!")
        print(f"   Output matches: {replay_result.output == result.output}")
        print(f"   Divergences: {len(replay_result.divergences)}")
    else:
        print(f"❌ Failed: {result.error}")
```

Run it:

```bash
python my_workflow.py
```

## What Just Happened?

1. **Execution**: The workflow ran, calling Claude API
2. **Logging**: Everything was logged to SQLite (`my_app.db`)
   - Workflow version (source code hash)
   - Inputs: `{"name": "Alice"}`
   - LLM call: prompt, model, temperature, response
   - Output: the greeting dict
   
3. **Replay**: The workflow ran again, but:
   - LLM call was NOT re-executed
   - Instead, logged response was used
   - Result was identical to original execution

## Inspect the Database

```bash
sqlite3 my_app.db

-- See all executions
SELECT execution_id, workflow_id, status, started_at 
FROM executions;

-- See steps for an execution
SELECT step_id, kind, inputs, output 
FROM steps 
WHERE execution_id = 'your-execution-id';

-- See LLM calls
SELECT model, prompt, response_raw 
FROM llm_calls;
```

## Test Against Past Executions

```python
import pytest
from my_workflow import hello_world
from chronicon import replay
from chronicon.log import ExecutionLog

def test_hello_world_replay():
    """Test that workflow is replayable."""
    log = ExecutionLog("my_app.db")
    
    # Replay a known good execution
    result = replay(
        hello_world,
        execution_id="your-execution-id-here",
        log=log,
    )
    
    assert result.success
    assert result.output["name"] == "Alice"
    assert "greeting" in result.output
```

## Next Steps

1. **Run examples**: `python examples/simple.py`
2. **Read tests**: See `tests/` for more patterns
3. **Build something**: Create your own workflow
4. **Test it**: Replay and verify behavior

## Key Concepts

- **Workflow**: A function decorated with `@workflow`
- **Execution**: Running a workflow with logging
- **Replay**: Re-running from logs (deterministic)
- **Divergence**: When replay differs from original (code changed, etc.)

## Common Patterns

### Pattern 1: Multi-step workflow

```python
@workflow
def analyze_text(text: str) -> dict:
    # Step 1: Extract key points
    points = llm_call(
        prompt=f"Extract 3 key points from: {text}",
        temperature=0.3,
    )
    
    # Step 2: Score each point
    scores = llm_call(
        prompt=f"Rate importance 1-10 for each: {points}",
        temperature=0.0,
    )
    
    return {"points": points, "scores": scores}
```

### Pattern 2: Error handling

```python
@workflow
def robust_workflow(data: str) -> dict:
    try:
        result = llm_call(prompt=f"Process: {data}")
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### Pattern 3: Testing divergence

```python
@workflow
def version_1(x: int) -> int:
    return x + 1

# ... run and record execution_id ...

# Later, change the code
@workflow
def version_1(x: int) -> int:
    return x + 2  # Changed!

# Replay detects the change
result = replay(version_1, execution_id=old_id, allow_divergence=True)
assert len(result.divergences) > 0
assert result.divergences[0].kind == DivergenceKind.WORKFLOW_VERSION_MISMATCH
```

## Troubleshooting

**Problem**: `ANTHROPIC_API_KEY not set`
**Solution**: `export ANTHROPIC_API_KEY="your-key"`

**Problem**: Workflow fails with "not serializable"
**Solution**: Make sure inputs/outputs are JSON-serializable (no lambdas, no open files)

**Problem**: Replay diverges unexpectedly
**Solution**: Check `result.divergences` to see what changed

## Philosophy

Chronicon is intentionally minimal. If you want:
- Multiple LLM providers → Not yet
- Async/parallel → Not yet
- Agents → Not in scope
- Complex DSL → Use Python functions

Focus on: **determinism**, **testability**, **simplicity**.
