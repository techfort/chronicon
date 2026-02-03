# Examples

This directory contains working examples demonstrating Chronicon's capabilities.

## Quick Start

```bash
# Activate virtual environment
cd /home/joe/10h/chronicon
source venv/bin/activate

# Set API key
export ANTHROPIC_API_KEY="your-key-here"

# Run any example
python examples/simple.py
```

## Available Examples

### 1. `simple.py` - Minimal Example
**What it demonstrates:**
- Basic workflow definition
- Single LLM call
- Execute and replay
- Perfect for getting started

**Use case:** Sentiment classification

```bash
python examples/simple.py
```

**Output:** Classifies text sentiment and demonstrates replay.

---

### 2. `summarize.py` - Text Summarization
**What it demonstrates:**
- Multiple LLM calls in sequence
- Mixed effectful and pure computation
- Quality scoring
- Pretty printed output

**Use case:** Summarize text and rate the quality

```bash
python examples/summarize.py
```

**Output:** Full demonstration with execution metadata.

---

### 3. `research_assistant.py` - Complex Workflow ⭐
**What it demonstrates:**
- Multi-step research pipeline
- Question generation and answering
- Synthesis of findings
- Multiple demonstrations:
  - Basic usage
  - Deterministic replay
  - Multiple topic processing
  - Database inspection
  - Testing patterns

**Use case:** Research a topic by generating questions, answering them, and synthesizing findings

```bash
python examples/research_assistant.py
```

**Output:** Comprehensive demo showing all 5 patterns with detailed output.

**Features:**
- Generates research questions about any topic
- Answers each question using LLM
- Synthesizes findings into coherent summary
- Rates research quality
- Shows how to inspect the database
- Demonstrates testing against past executions

---

### 4. `content_pipeline.py` - Processing Pipeline
**What it demonstrates:**
- Sequential processing stages
- Content analysis and improvement
- Conditional logic (auto-improve)
- SEO metadata generation
- Structured data transformation

**Use case:** Process blog post drafts through analysis, improvement, and SEO optimization

```bash
python examples/content_pipeline.py
```

**Output:** Shows 4-stage pipeline with analysis, suggestions, improvements, and SEO.

**Pipeline stages:**
1. Analyze tone and clarity
2. Generate improvement suggestions
3. Apply improvements (conditional)
4. Generate SEO metadata

---

## What Each Example Teaches

| Example | Complexity | LLM Calls | Key Learning |
|---------|-----------|-----------|--------------|
| `simple.py` | ⭐ Basic | 1 | Workflow basics |
| `summarize.py` | ⭐⭐ Intermediate | 2 | Sequential calls |
| `research_assistant.py` | ⭐⭐⭐ Advanced | 5+ | Complex workflows |
| `content_pipeline.py` | ⭐⭐⭐ Advanced | 4 | Processing pipelines |

## Common Patterns

### Pattern 1: Basic Workflow
```python
@workflow
def my_workflow(input: str) -> str:
    result = llm_call(prompt=f"Process: {input}")
    return result

result = execute(my_workflow, input="test", log=log)
```

### Pattern 2: Multiple LLM Calls
```python
@workflow
def multi_step(text: str) -> dict:
    summary = llm_call(prompt=f"Summarize: {text}")
    score = llm_call(prompt=f"Rate: {summary}")
    return {"summary": summary, "score": score}
```

### Pattern 3: Mixed Pure + Effectful
```python
@workflow
def mixed_workflow(data: str) -> dict:
    # Effectful: LLM call
    result = llm_call(prompt=f"Analyze: {data}")
    
    # Pure: computation
    word_count = len(result.split())
    
    return {"result": result, "words": word_count}
```

### Pattern 4: Conditional Logic
```python
@workflow
def conditional(text: str, improve: bool) -> str:
    analysis = llm_call(prompt=f"Analyze: {text}")
    
    if improve:
        return llm_call(prompt=f"Improve: {text}")
    else:
        return text
```

## Database Exploration

Each example creates its own database file:
- `examples.db` - simple.py, summarize.py
- `research_example.db` - research_assistant.py
- `content_example.db` - content_pipeline.py

Explore them:
```bash
sqlite3 research_example.db

# See all executions
SELECT execution_id, workflow_id, status FROM executions;

# See LLM calls
SELECT model, prompt, response_raw FROM llm_calls LIMIT 5;

# See steps for specific execution
SELECT step_id, kind, inputs FROM steps 
WHERE execution_id = 'your-id-here';
```

## Testing Pattern

All examples can be tested using replay:

```python
# In your test file
def test_workflow_replay():
    log = ExecutionLog("research_example.db")
    
    # Replay a known execution
    result = replay(
        research_topic,
        execution_id="known-good-execution-id",
        log=log,
    )
    
    assert result.success
    assert "synthesis" in result.output
    assert result.output["quality_score"] >= 7
```

## Troubleshooting

**Problem:** `ANTHROPIC_API_KEY not set`
```bash
export ANTHROPIC_API_KEY="your-key-here"
```

**Problem:** ModuleNotFoundError
```bash
# Make sure you're in the virtual environment
source venv/bin/activate
pip install -e .
```

**Problem:** Database locked
```bash
# Close any open SQLite connections
# Or use a different database file name
```

## Next Steps

1. **Run the examples** to see Chronicon in action
2. **Read the code** to understand patterns
3. **Modify examples** to fit your use case
4. **Create your own** workflow based on these templates

## Learn More

- [Quick Start Guide](../QUICKSTART.md)
- [Project Structure](../STRUCTURE.md)
- [Development Guide](../DEVELOPMENT.md)
