"""
Ollama integration for Chronicon.

This module provides an alternative llm_call implementation that uses
Ollama instead of Anthropic's API.

Usage:
    # In your workflow file, import this instead:
    from chronicon.integrations.ollama import llm_call
    
    # Or monkey-patch it globally:
    import chronicon.step
    from chronicon.integrations.ollama import llm_call
    chronicon.step.llm_call = llm_call
"""

import requests
from typing import Optional


def llm_call(
    prompt: str,
    model: str = "llama2",
    temperature: float = 1.0,
    max_tokens: int = 4096,
    system: Optional[str] = None,
) -> str:
    """
    Make an LLM call using Ollama.
    
    This is a drop-in replacement for the Anthropic llm_call.
    Works with any model available in Ollama (llama2, mistral, codellama, etc.)
    
    Args:
        prompt: The user prompt
        model: Ollama model name (e.g., "llama2", "mistral", "codellama")
        temperature: Sampling temperature (0-1)
        max_tokens: Maximum tokens in response
        system: Optional system prompt
        
    Returns:
        The text response from the LLM
        
    Raises:
        ConnectionError: If Ollama is not running
        requests.RequestException: If the API call fails
        
    Note:
        Requires Ollama to be running locally (http://localhost:11434)
        Install: https://ollama.ai/
        Run: ollama run llama2
    """
    url = "http://localhost:11434/api/generate"
    
    # Build the full prompt
    full_prompt = prompt
    if system:
        full_prompt = f"{system}\n\n{prompt}"
    
    # Make request to Ollama
    payload = {
        "model": model,
        "prompt": full_prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        }
    }
    
    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        
        result = response.json()
        return result.get("response", "")
        
    except requests.exceptions.ConnectionError:
        raise ConnectionError(
            "Could not connect to Ollama. Make sure it's running:\n"
            "  1. Install: https://ollama.ai/\n"
            "  2. Pull model: ollama pull llama2\n"
            "  3. Verify: curl http://localhost:11434/api/tags"
        )
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Ollama API error: {e}")
