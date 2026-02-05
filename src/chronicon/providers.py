"""
LLM provider abstraction using LiteLLM.

This module wraps LiteLLM to provide a consistent interface for Chronicon.
LiteLLM supports 100+ providers with a unified API.

Usage:
    # Create a configured llm_call for your provider
    llm_call = create_llm_call(
        provider="anthropic",
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )
    
    # Or use built-in convenience functions
    from chronicon.providers import anthropic_llm_call, ollama_llm_call
"""

import os
from typing import Optional, Callable
import litellm


def create_llm_call(
    provider: str,
    endpoint: Optional[str] = None,
    api_key: Optional[str] = None,
    **provider_kwargs
) -> Callable:
    """
    Factory function that creates a configured llm_call function using LiteLLM.
    
    Args:
        provider: Provider name (anthropic, ollama, openai, google, etc.)
        endpoint: Optional endpoint URL (for ollama, custom providers)
        api_key: Optional API key
        **provider_kwargs: Additional provider-specific configuration
        
    Returns:
        A configured llm_call function with Chronicon's signature:
        llm_call(prompt, model, temperature, max_tokens, system) -> str
        
    Examples:
        # Anthropic
        llm_call = create_llm_call("anthropic", api_key="sk-...")
        
        # Ollama
        llm_call = create_llm_call("ollama", endpoint="http://localhost:11434")
        
        # Google AI Studio
        llm_call = create_llm_call("google", api_key="...")
    """
    
    # Map Chronicon provider names to LiteLLM model prefixes
    provider_map = {
        "anthropic": "anthropic",
        "openai": "openai",
        "google": "gemini",
        "ollama": "ollama",
        "openrouter": "openrouter",
        "custom": None,  # Handle custom separately
    }
    
    litellm_prefix = provider_map.get(provider)
    if litellm_prefix is None and provider != "custom":
        raise ValueError(
            f"Unknown provider: {provider}. "
            f"Supported: {list(provider_map.keys())}"
        )
    
    # Custom provider requires endpoint
    if provider == "custom" and not endpoint:
        raise ValueError("Custom provider requires 'endpoint' parameter")
    
    # Store configuration
    config = {
        "provider": provider,
        "endpoint": endpoint,
        "api_key": api_key,
        **provider_kwargs
    }
    
    def llm_call(
        prompt: str,
        model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        system: Optional[str] = None,
    ) -> str:
        """
        Call LLM with the given prompt.
        
        Uses LiteLLM's completion() function which handles all provider differences.
        """
        # Build messages
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        # Build model identifier for LiteLLM
        if provider == "ollama":
            # For ollama: "ollama/model_name"
            model_id = f"ollama/{model}"
            if endpoint:
                # LiteLLM uses OLLAMA_API_BASE env var
                os.environ["OLLAMA_API_BASE"] = endpoint
        elif provider == "google":
            # For Google: "gemini/model_name"
            model_id = f"gemini/{model}"
            if api_key:
                os.environ["GEMINI_API_KEY"] = api_key
        elif provider == "anthropic":
            # For Anthropic: "anthropic/model_name" or just "model_name"
            model_id = f"anthropic/{model}" if not model.startswith("anthropic/") else model
            if api_key:
                os.environ["ANTHROPIC_API_KEY"] = api_key
        elif provider == "openai":
            # For OpenAI: just model name
            model_id = model
            if api_key:
                os.environ["OPENAI_API_KEY"] = api_key
        elif provider == "custom":
            # Custom endpoint
            model_id = model
            if endpoint:
                litellm.api_base = endpoint
        else:
            # Default: use provider prefix
            model_id = f"{litellm_prefix}/{model}"
        
        try:
            # Call LiteLLM's unified completion function
            response = litellm.completion(
                model=model_id,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                api_key=api_key or os.getenv(f"{provider.upper()}_API_KEY"),
                base_url=endpoint,
                **provider_kwargs
            )
            
            # Extract text from response
            return response.choices[0].message.content
            
        except Exception as e:
            raise ValueError(
                f"LiteLLM error for provider '{provider}', model '{model}': {str(e)}"
            )
    
    return llm_call


# Convenience functions for common providers
def anthropic_llm_call(api_key: Optional[str] = None) -> Callable:
    """Create Anthropic llm_call function."""
    return create_llm_call("anthropic", api_key=api_key)


def ollama_llm_call(endpoint: str = "http://localhost:11434") -> Callable:
    """Create Ollama llm_call function."""
    return create_llm_call("ollama", endpoint=endpoint)


def openai_llm_call(api_key: Optional[str] = None) -> Callable:
    """Create OpenAI llm_call function."""
    return create_llm_call("openai", api_key=api_key)


def google_llm_call(api_key: Optional[str] = None) -> Callable:
    """Create Google AI Studio llm_call function."""
    return create_llm_call("google", api_key=api_key)


def openrouter_llm_call(api_key: Optional[str] = None) -> Callable:
    """Create OpenRouter llm_call function."""
    return create_llm_call("openrouter", api_key=api_key)
