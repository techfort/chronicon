# Chronicon Project Structure

```
chronicon/
│
├── README.md                    # Project overview and philosophy
├── QUICKSTART.md                # Get started in 5 minutes
├── DEVELOPMENT.md               # Developer guide and patterns
├── PROJECT_SUMMARY.md           # Complete implementation summary
├── LICENSE                      # MIT License
├── pyproject.toml               # Modern Python packaging
├── .gitignore                   # Git ignore rules
│
├── src/chronicon/               # Core implementation (~1,438 lines)
│   ├── __init__.py             # Public API exports
│   ├── workflow.py             # @workflow decorator (119 lines)
│   ├── step.py                 # Step abstraction + llm_call (184 lines)
│   ├── execution.py            # Execution engine (236 lines)
│   ├── replay.py               # Replay engine with divergence detection (268 lines)
│   ├── log.py                  # SQLite append-only execution log (376 lines)
│   ├── hash.py                 # Source code and value hashing (80 lines)
│   ├── serialization.py        # JSON serialization with type preservation (108 lines)
│   └── cli.py                  # CLI placeholder (future)
│
├── tests/                       # Comprehensive test suite (32 tests)
│   ├── __init__.py
│   ├── test_workflow.py        # Workflow decorator tests (5 tests)
│   ├── test_execution.py       # Execution engine tests (5 tests)
│   ├── test_replay.py          # Replay and divergence tests (4 tests)
│   ├── test_log.py             # SQLite persistence tests (7 tests)
│   ├── test_hash.py            # Hashing utilities tests (4 tests)
│   └── test_serialization.py   # Serialization tests (7 tests)
│
├── examples/                    # Working examples
│   ├── simple.py               # Minimal sentiment classification example
│   └── summarize.py            # Full text summarization with quality scoring
│
└── venv/                        # Virtual environment (gitignored)
```

## Core Abstractions

### 1. Workflow (`workflow.py`)
```python
@workflow
def my_workflow(x: int) -> int:
    return process(x)
```
- Decorated Python function
- Source code versioned (SHA-256)
- Explicit inputs/outputs
- Type hints encouraged

### 2. Execution (`execution.py`)
```python
result = execute(my_workflow, x=42, log=log)
```
- Runs workflow with full logging
- Intercepts LLM calls
- Validates serialization
- Returns ExecutionResult

### 3. Execution Log (`log.py`)
```sql
-- executions table
execution_id, workflow_id, workflow_version, inputs, output, status, timestamps

-- steps table
step_record_id, execution_id, step_id, step_version, kind, inputs, output

-- llm_calls table
llm_call_id, step_record_id, model, prompt, temperature, response_raw
```
- SQLite database
- Append-only (immutable)
- Explicit schema versioning
- Queryable execution history

### 4. Replay (`replay.py`)
```python
replay_result = replay(my_workflow, execution_id=exec_id, log=log)
```
- Deterministic replay from logs
- Effectful steps use logged outputs
- Detects 5 types of divergence
- Returns ReplayResult with divergences

### 5. Hashing (`hash.py`)
```python
workflow_version = hash_source(workflow_func)
value_hash = hash_value({"x": 1, "y": 2})
```
- SHA-256 of function source code
- Content-based value hashing
- Deterministic (sorted keys)

### 6. Serialization (`serialization.py`)
```python
json_str = serialize({"dt": datetime.now(), "path": Path("/tmp")})
obj = deserialize(json_str)
```
- JSON with custom type support
- datetime, Path, bytes, set
- Deterministic (sorted keys)
- Validation helpers

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                          EXECUTION                              │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  @workflow                                                      │
│  def my_workflow(x: int) -> str:                                │
│      result = llm_call(prompt=f"Process {x}")  ◄─── Intercepted│
│      return result                                              │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      EXECUTION LOG (SQLite)                     │
│                                                                 │
│  ┌─────────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   executions    │    │    steps     │    │  llm_calls   │  │
│  │                 │    │              │    │              │  │
│  │ - exec_id       │◄───│ - exec_id    │◄───│ - step_id    │  │
│  │ - workflow_id   │    │ - step_id    │    │ - model      │  │
│  │ - version       │    │ - inputs     │    │ - prompt     │  │
│  │ - inputs        │    │ - output     │    │ - response   │  │
│  │ - output        │    │ - kind       │    │              │  │
│  └─────────────────┘    └──────────────┘    └──────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                           REPLAY                                │
│                                                                 │
│  Load logged execution                                          │
│  ├─ Workflow version matches? ◄─── Check hash                  │
│  ├─ Re-run workflow                                             │
│  │  ├─ llm_call() → Return logged output ◄─── No API call      │
│  │  └─ Pure steps → Re-execute                                 │
│  └─ Compare output → Detect divergence                          │
└─────────────────────────────────────────────────────────────────┘
```

## Design Principles

1. **Determinism First**
   - If it ran once, it can replay exactly
   - Source code versioning catches changes
   - Logged outputs ensure repeatability

2. **Explicit State**
   - No hidden globals (except execution context)
   - All inputs passed as arguments
   - All outputs returned explicitly

3. **Minimal Surface Area**
   - 5 core functions in public API
   - 3 main classes (Workflow, ExecutionResult, ReplayResult)
   - Opinionated choices (SQLite, Anthropic, JSON)

4. **Local First**
   - Single process runtime
   - SQLite for persistence
   - No distributed coordination

5. **Testing as First-Class**
   - Test against real past executions
   - No mocks needed (use replay)
   - Divergence detection helps debug

## File Sizes

```
Source Code:
  workflow.py           119 lines
  step.py               184 lines
  execution.py          236 lines
  replay.py             268 lines
  log.py                376 lines
  hash.py                80 lines
  serialization.py      108 lines
  ────────────────────────────
  Total                1438 lines

Tests:
  All test files       ~600 lines
  32 tests (31 pass, 1 skip)

Documentation:
  README.md             ~200 lines
  QUICKSTART.md         ~300 lines
  DEVELOPMENT.md        ~150 lines
  PROJECT_SUMMARY.md    ~350 lines
```

## Dependencies

**Runtime:**
- `anthropic>=0.39.0` (LLM API)
- Python 3.10+ standard library (sqlite3, json, inspect, hashlib)

**Development:**
- `pytest>=8.0.0`
- `pytest-asyncio>=0.23.0`
- `black>=24.0.0`
- `ruff>=0.6.0`

No other dependencies. No complex frameworks.

## What Makes This Different?

Most LLM frameworks focus on:
- Agent loops and planning
- Prompt engineering and templates
- Multi-provider abstractions
- Distributed execution

Chronicon focuses on:
- ✅ Deterministic replay
- ✅ Testing real executions
- ✅ Explicit state tracking
- ✅ Code versioning
- ✅ Boring correctness

## Status

**MVP Complete** ✅

- Core abstractions: Done
- Execution engine: Done
- Replay engine: Done
- SQLite persistence: Done
- Test suite: 31/32 passing
- Documentation: Complete
- Examples: Working

Ready for:
- Real-world usage
- Feedback and iteration
- Production hardening
