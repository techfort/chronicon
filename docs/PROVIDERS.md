# LLM Provider Configuration

Chronicon uses a factory pattern for LLM providers, making it easy to use different LLM services (Anthropic, Ollama, OpenAI, custom endpoints) without monkey-patching.

**Key Feature**: Use multiple providers in a single workflow - route different tasks to different models.

## Quick Start

### Single Provider (Simple)

```python
from chronicon import workflow, execute, anthropic_llm_call

llm_call = anthropic_llm_call()  # Uses ANTHROPIC_API_KEY env var
result = execute(my_workflow, inputs, llm_call=llm_call)
```

### Multiple Providers (Advanced)

```python
from chronicon import workflow, execute, anthropic_llm_call, ollama_llm_call

# Set up providers
providers = {
    "anthropic": anthropic_llm_call(),
    "ollama": ollama_llm_call(),
}

@workflow
def smart_workflow(text: str) -> dict:
    from chronicon import llm_call
    
    # Use Ollama for quick classification (free, local)
    category = llm_call(
        f"Classify: {text}",
        model="llama2",
        provider="ollama"
    )
    
    # Use Claude for detailed analysis (paid, sophisticated)
    analysis = llm_call(
        f"Analyze: {text}",
        model="claude-3-5-sonnet-20241022",
        provider="anthropic"
    )
    
    return {"category": category, "analysis": analysis}

# Execute with multiple providers
result = execute(smart_workflow, "sample text", providers=providers)
```

## Factory Function

For more control, use the `create_llm_call` factory:

```python
from chronicon import create_llm_call, execute

# Anthropic
llm_call = create_llm_call(
    provider="anthropic",
    api_key="sk-ant-..."
)

# Ollama
llm_call = create_llm_call(
    provider="ollama",
    endpoint="http://localhost:11434"
)

# OpenAI
llm_call = create_llm_call(
    provider="openai",
    api_key="sk-..."
)

# Custom endpoint (OpenAI-compatible API)
llm_call = create_llm_call(
    provider="custom",
    endpoint="https://my-llm.com/v1/chat",
    api_key="my-key",
    headers={"X-Custom-Header": "value"}
)

# Use it
result = execute(my_workflow, inputs, llm_call=llm_call)
```

## Writing Workflows

Inside your workflow, use `llm_call` as usual. Specify the provider per call when using multiple providers:

```python
from chronicon import workflow

@workflow
def my_workflow(topic: str) -> str:
    from chronicon import llm_call
    
    # Simple case: use default provider
    response = llm_call(
        f"Write about {topic}",
        model="claude-3-5-sonnet-20241022",
        temperature=0.7,
        max_tokens=1000,
    )
    
    # Advanced: specify provider (when using providers dict)
    response = llm_call(
        f"Write about {topic}",
        model="llama2",
        provider="ollama"  # Route to specific provider
    )
    
    return response
```

## Use Cases for Multiple Providers

### Cost Optimization

Use cheap/free models for simple tasks, expensive models only when needed:

```python
@workflow
def cost_optimized_analysis(query: str) -> dict:
    from chronicon import llm_call
    
    # Step 1: Classify complexity with free Ollama
    complexity = llm_call(
        f"Is this query simple or complex? {query}",
        model="llama2",
        provider="ollama"  # Free, local
    )
    
    # Step 2: Route based on complexity
    if "simple" in complexity.lower():
        answer = llm_call(query, model="llama2", provider="ollama")
    else:
        answer = llm_call(query, model="claude-3-5-sonnet-20241022", provider="anthropic")
    
    return {"complexity": complexity, "answer": answer}
```

### Multi-Model Consensus

Get diverse perspectives by asking multiple models:

```python
@workflow
def consensus_analysis(question: str) -> dict:
    from chronicon import llm_call
    
    # Ask multiple models
    ollama_view = llm_call(question, provider="ollama")
    claude_view = llm_call(question, provider="anthropic")
    gpt_view = llm_call(question, provider="openai")
    
    # Synthesize
    synthesis = llm_call(
        f"Synthesize these views: {ollama_view}, {claude_view}, {gpt_view}",
        provider="anthropic"
    )
    
    return {"views": [ollama_view, claude_view, gpt_view], "synthesis": synthesis}
```

### Task-Specific Routing

Route different tasks to models that excel at them:

```python
@workflow
def specialized_pipeline(code: str, docs: str) -> dict:
    from chronicon import llm_call
    
    # Use code-specialized model for code review
    code_review = llm_call(
        f"Review this code: {code}",
        model="deepseek-coder:6.7b",
        provider="ollama"
    )
    
    # Use general model for documentation
    doc_summary = llm_call(
        f"Summarize: {docs}",
        model="claude-3-5-sonnet-20241022",
        provider="anthropic"
    )
    
    return {"code_review": code_review, "doc_summary": doc_summary}
```

## Provider-Specific Details

### Anthropic

- **Models**: `claude-3-5-sonnet-20241022`, `claude-3-opus-20240229`, etc.
- **API Key**: Pass `api_key` or set `ANTHROPIC_API_KEY` environment variable
- **Endpoint**: Uses official Anthropic API

```python
llm_call = anthropic_llm_call(api_key="sk-ant-...")
```

### Ollama

- **Models**: `llama2`, `mistral`, `deepseek-coder:6.7b`, `codellama`, etc.
- **Endpoint**: Defaults to `http://localhost:11434`
- **No API key required** - runs locally
- **Prerequisites**: Install Ollama and pull a model

```python
llm_call = ollama_llm_call(endpoint="http://localhost:11434")
```

### OpenAI

- **Models**: `gpt-4`, `gpt-3.5-turbo`, etc.
- **API Key**: Pass `api_key` or set `OPENAI_API_KEY` environment variable
- **Endpoint**: Defaults to `https://api.openai.com/v1` (can override for Azure OpenAI)

```python
# Standard OpenAI
llm_call = openai_llm_call(api_key="sk-...")

# Azure OpenAI
llm_call = openai_llm_call(
    api_key="...",
    endpoint="https://your-resource.openai.azure.com"
)
```

### Custom Endpoints

For any OpenAI-compatible API:

```python
llm_call = create_llm_call(
    provider="custom",
    endpoint="https://api.example.com/v1/chat/completions",
    api_key="your-key",
    headers={"Authorization": "Bearer your-key"}  # Optional custom headers
)
```

## Testing with Different Providers

The factory pattern makes it easy to test workflows with different providers:

```python
import pytest
from chronicon import workflow, execute, create_llm_call

@workflow
def sentiment_analysis(text: str) -> str:
    from chronicon import llm_call
    return llm_call(f"Classify sentiment: {text}", max_tokens=10)

def test_with_ollama():
    """Test with local Ollama model."""
    llm_call = create_llm_call("ollama")
    result = execute(sentiment_analysis, "Great!", llm_call=llm_call)
    assert result.success

def test_with_anthropic():
    """Test with Anthropic Claude."""
    llm_call = create_llm_call("anthropic")
    result = execute(sentiment_analysis, "Great!", llm_call=llm_call)
    assert result.success
```

## Design Principles

1. **Explicit over implicit** - Provider is configured at execution time
2. **No monkey-patching** - Pass `llm_call` as parameter to `execute()`
3. **Easy to swap** - Change provider by changing one line
4. **Built-in helpers** - Convenience functions for common cases
5. **Extensible** - Support for custom endpoints

## Migration from Old Pattern

If you were using monkey-patching:

```python
# OLD (monkey-patching)
import chronicon.step
from chronicon.integrations.ollama import llm_call
chronicon.step.llm_call = llm_call

result = execute(my_workflow, inputs)
```

New pattern:

```python
# NEW (factory pattern)
from chronicon import ollama_llm_call, execute

llm_call = ollama_llm_call()
result = execute(my_workflow, inputs, llm_call=llm_call)
```

## Examples

See these examples for complete demonstrations:

- `examples/provider_factory.py` - All provider types
- `examples/ollama_example.py` - Local Ollama usage
- `examples/simple.py` - Basic Anthropic usage
