"""
Example: Using the LLM provider factory pattern.

This demonstrates the new factory pattern for creating llm_call functions
configured for different providers (Anthropic, Ollama, OpenAI, custom).
"""

import os
from chronicon import workflow, execute, create_llm_call, anthropic_llm_call, ollama_llm_call


@workflow
def greet(name: str) -> str:
    """Simple greeting workflow."""
    from chronicon import llm_call
    
    response = llm_call(
        f"Say hello to {name} in a creative way.",
        model="claude-3-5-sonnet-20241022",
        max_tokens=100,
    )
    
    return response


def example_1_anthropic():
    """Example 1: Use Anthropic with factory."""
    print("\n" + "="*60)
    print("Example 1: Anthropic via factory")
    print("="*60)
    
    # Create Anthropic llm_call
    llm_call = create_llm_call(
        provider="anthropic",
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )
    
    # Execute with custom llm_call
    result = execute(greet, "Alice", llm_call=llm_call)
    print(f"Output: {result.output}")


def example_2_anthropic_convenience():
    """Example 2: Use built-in Anthropic helper."""
    print("\n" + "="*60)
    print("Example 2: Anthropic via convenience function")
    print("="*60)
    
    # Use convenience function
    llm_call = anthropic_llm_call()
    
    result = execute(greet, "Bob", llm_call=llm_call)
    print(f"Output: {result.output}")


def example_3_ollama():
    """Example 3: Use Ollama with factory."""
    print("\n" + "="*60)
    print("Example 3: Ollama via factory")
    print("="*60)
    
    # Create Ollama llm_call
    llm_call = create_llm_call(
        provider="ollama",
        endpoint="http://localhost:11434"
    )
    
    result = execute(greet, "Charlie", llm_call=llm_call)
    print(f"Output: {result.output}")


def example_4_ollama_convenience():
    """Example 4: Use built-in Ollama helper."""
    print("\n" + "="*60)
    print("Example 4: Ollama via convenience function")
    print("="*60)
    
    # Use convenience function
    llm_call = ollama_llm_call()
    
    result = execute(greet, "Diana", llm_call=llm_call)
    print(f"Output: {result.output}")


def example_5_custom_endpoint():
    """Example 5: Use custom endpoint."""
    print("\n" + "="*60)
    print("Example 5: Custom endpoint")
    print("="*60)
    
    # Create custom llm_call
    llm_call = create_llm_call(
        provider="custom",
        endpoint="https://my-llm-service.com/v1/chat",
        api_key="my-api-key",
        headers={"X-Custom-Header": "value"}
    )
    
    # This would work if you had a custom endpoint
    # result = execute(greet, "Eve", llm_call=llm_call)
    # print(f"Output: {result.output}")
    print("(Skipped - requires custom endpoint)")


def example_6_openai():
    """Example 6: Use OpenAI."""
    print("\n" + "="*60)
    print("Example 6: OpenAI")
    print("="*60)
    
    # Skip if no API key
    if not os.getenv("OPENAI_API_KEY"):
        print("(Skipped - set OPENAI_API_KEY to run)")
        return
    
    # Create OpenAI llm_call
    llm_call = create_llm_call(
        provider="openai",
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    result = execute(greet, "Frank", llm_call=llm_call)
    print(f"Output: {result.output}")


if __name__ == "__main__":
    print("\nLLM Provider Factory Examples")
    print("==============================")
    
    # Run Anthropic examples if API key is available
    if os.getenv("ANTHROPIC_API_KEY"):
        example_1_anthropic()
        example_2_anthropic_convenience()
    else:
        print("\nSkipping Anthropic examples (set ANTHROPIC_API_KEY)")
    
    # Run Ollama examples if server is available
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=1)
        if response.status_code == 200:
            example_3_ollama()
            example_4_ollama_convenience()
        else:
            print("\nSkipping Ollama examples (server not responding)")
    except:
        print("\nSkipping Ollama examples (run: ollama serve)")
    
    # Show custom endpoint example
    example_5_custom_endpoint()
    
    # Show OpenAI example
    example_6_openai()
    
    print("\n" + "="*60)
    print("Key Benefits:")
    print("="*60)
    print("✓ Explicit provider configuration")
    print("✓ No monkey-patching required")
    print("✓ Easy to swap providers")
    print("✓ Built-in helpers for common cases")
    print("✓ Support for custom endpoints")
    print()
