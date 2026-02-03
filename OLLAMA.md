# Using Ollama with Chronicon

Run LLM workflows entirely on your local machine - no API keys, no cloud dependencies, no costs!

## Quick Setup

### 1. Install Ollama

```bash
# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Or visit: https://ollama.ai/
```

### 2. Pull a Model

```bash
# Llama 2 (7B) - good balance
ollama pull llama2

# Or other models:
ollama pull mistral      # Mistral 7B - fast and good
ollama pull codellama    # Code-focused
ollama pull llama2:13b   # Larger, more capable
```

### 3. Verify It's Running

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# List installed models
ollama list
```

## Using Ollama in Your Workflows

### Option 1: Import Ollama's llm_call

```python
from chronicon import workflow, execute
# Use Ollama's llm_call instead of the default
from chronicon.integrations.ollama import llm_call

@workflow
def my_workflow(text: str) -> str:
    # This uses Ollama, not Anthropic
    result = llm_call(
        prompt=f"Analyze: {text}",
        model="llama2",  # or "mistral", "codellama", etc.
        temperature=0.7,
    )
    return result

result = execute(my_workflow, text="Hello!")
```

### Option 2: Monkey-Patch Globally

```python
from chronicon import workflow, execute
import chronicon.step
from chronicon.integrations.ollama import llm_call

# Replace the default llm_call globally
chronicon.step.llm_call = llm_call

@workflow  
def my_workflow(text: str) -> str:
    # Now all workflows use Ollama
    from chronicon import llm_call
    result = llm_call(prompt=f"Analyze: {text}", model="llama2")
    return result
```

## Complete Example

Run the included example:

```bash
# Make sure Ollama is running
ollama serve  # (usually runs automatically)

# Install requests dependency
pip install requests

# Run the example
python examples/ollama_example.py
```

The example shows:
- Local sentiment analysis
- No API key needed
- Full replay capability
- Execution logging

## Available Models

```bash
# List all available models
ollama list

# Popular choices:
llama2        # 7B - balanced
llama2:13b    # 13B - more capable
mistral       # 7B - fast
codellama     # 7B - code-focused
gemma         # Google's model
phi           # Microsoft's small model
```

## Model Parameters

```python
llm_call(
    prompt="Your prompt here",
    model="llama2",           # Model name from 'ollama list'
    temperature=0.7,          # 0.0-1.0, lower = more deterministic
    max_tokens=4096,          # Max response length
    system="You are...",      # Optional system prompt
)
```

## Advantages of Local Models

✅ **No API costs** - run unlimited workflows  
✅ **Complete privacy** - data never leaves your machine  
✅ **No rate limits** - run as many workflows as you want  
✅ **Offline capable** - works without internet  
✅ **Full control** - choose any model you want  

## Disadvantages

❌ **Requires GPU** - slower on CPU (but still works)  
❌ **Model quality** - not as capable as GPT-4 or Claude  
❌ **Resource usage** - uses RAM and disk space  
❌ **Setup required** - need to install and manage Ollama  

## Performance Tips

### 1. Use Appropriate Models

```python
# For simple tasks (sentiment, classification)
model="llama2"  # 7B, fast

# For complex reasoning
model="llama2:13b"  # 13B, slower but better

# For code
model="codellama"  # Optimized for programming
```

### 2. Lower Temperature for Determinism

```python
llm_call(
    prompt="Classify sentiment",
    model="llama2",
    temperature=0.0,  # More deterministic
)
```

### 3. Use Smaller max_tokens

```python
llm_call(
    prompt="Answer with yes or no",
    max_tokens=10,  # Faster for short responses
)
```

## Mixing Ollama and Anthropic

You can use both in the same project:

```python
from chronicon import workflow, execute
from chronicon.integrations.ollama import llm_call as ollama_call
from chronicon.step import llm_call as anthropic_call

@workflow
def hybrid_workflow(text: str) -> dict:
    # Use Ollama for simple classification (free)
    sentiment = ollama_call(
        prompt=f"Classify: {text}",
        model="llama2",
    )
    
    # Use Anthropic for complex analysis (paid but better)
    analysis = anthropic_call(
        prompt=f"Deep analysis: {text}",
        model="claude-3-5-sonnet-20241022",
    )
    
    return {"sentiment": sentiment, "analysis": analysis}
```

## Troubleshooting

### Problem: "Could not connect to Ollama"

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if needed
ollama serve

# On Linux, it usually runs as a service:
systemctl status ollama
```

### Problem: "Model not found"

```bash
# List installed models
ollama list

# Pull the model you need
ollama pull llama2
```

### Problem: Slow responses

```bash
# Use a smaller model
ollama pull phi  # Microsoft's 2.7B model

# Or use GPU acceleration (if you have NVIDIA GPU)
# Ollama automatically uses GPU if available
```

### Problem: Out of memory

```bash
# Use a smaller model
ollama pull phi

# Or increase system swap space
# Or close other applications
```

## Testing with Ollama

Works exactly the same as with Anthropic:

```python
def test_local_workflow():
    from chronicon import replay
    from chronicon.log import ExecutionLog
    
    log = ExecutionLog("ollama_example.db")
    
    # Replay a past execution
    result = replay(
        my_workflow,
        execution_id="known-execution-id",
        log=log,
    )
    
    # No LLM call made - uses logged output
    assert result.success
    assert result.output is not None
```

## Resources

- **Ollama Website**: https://ollama.ai/
- **Model Library**: https://ollama.ai/library
- **Ollama GitHub**: https://github.com/ollama/ollama
- **Ollama Discord**: https://discord.gg/ollama

## Next Steps

1. Install Ollama: `curl -fsSL https://ollama.ai/install.sh | sh`
2. Pull a model: `ollama pull llama2`
3. Run the example: `python examples/ollama_example.py`
4. Create your own local workflows!

---

**The best of both worlds**: Use Ollama for development and testing (free), then switch to Anthropic for production (better quality) - all with the same Chronicon workflow code!
