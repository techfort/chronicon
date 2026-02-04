"""
Tests for provider factory pattern.
"""

import pytest
from chronicon import create_llm_call, anthropic_llm_call, ollama_llm_call, openai_llm_call


def test_create_llm_call_returns_callable():
    """Factory should return callable functions."""
    # Test each provider returns a callable
    providers = ["anthropic", "ollama", "openai"]
    
    for provider in providers:
        if provider == "anthropic":
            try:
                llm_call = create_llm_call(provider, api_key="test-key")
            except ImportError:
                pytest.skip("anthropic not installed")
        elif provider == "ollama":
            llm_call = create_llm_call(provider, endpoint="http://localhost:11434")
        elif provider == "openai":
            llm_call = create_llm_call(provider, api_key="test-key")
        
        assert callable(llm_call)


def test_create_llm_call_unknown_provider():
    """Factory should raise error for unknown providers."""
    with pytest.raises(ValueError, match="Unknown provider"):
        create_llm_call("unknown_provider")


def test_create_llm_call_custom_requires_endpoint():
    """Custom provider should require endpoint."""
    with pytest.raises(ValueError, match="Custom provider requires 'endpoint'"):
        create_llm_call("custom", api_key="test")


def test_anthropic_convenience_function():
    """Anthropic convenience function should return callable."""
    try:
        llm_call = anthropic_llm_call(api_key="test-key")
        assert callable(llm_call)
    except ImportError:
        pytest.skip("anthropic not installed")


def test_ollama_convenience_function():
    """Ollama convenience function should return callable."""
    llm_call = ollama_llm_call(endpoint="http://localhost:11434")
    assert callable(llm_call)


def test_openai_convenience_function():
    """OpenAI convenience function should return callable."""
    llm_call = openai_llm_call(api_key="test-key")
    assert callable(llm_call)


def test_ollama_llm_call_signature():
    """Ollama llm_call should accept standard parameters."""
    llm_call = ollama_llm_call()
    
    # Check function signature matches expected
    import inspect
    sig = inspect.signature(llm_call)
    params = list(sig.parameters.keys())
    
    assert "prompt" in params
    assert "model" in params
    assert "temperature" in params
    assert "max_tokens" in params
    assert "system" in params


def test_custom_endpoint_with_headers():
    """Custom provider should accept custom headers."""
    llm_call = create_llm_call(
        "custom",
        endpoint="https://example.com/api",
        api_key="test-key",
        headers={"X-Custom": "value"}
    )
    
    assert callable(llm_call)
