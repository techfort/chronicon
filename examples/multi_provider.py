"""
Example: Using multiple LLM providers in a single workflow.

This demonstrates the power of the provider registry - you can use
different LLM providers for different tasks within the same workflow.

For example:
- Use Ollama (local, free) for simple tasks like classification
- Use Claude (cloud, paid) for complex reasoning
- Use GPT-4 for specific tasks it excels at
"""

import os
from chronicon import workflow, execute, anthropic_llm_call, ollama_llm_call


@workflow
def content_analysis(text: str) -> dict:
    """
    Analyze content using multiple LLM providers.
    
    Uses local Ollama for simple classification,
    then Claude for detailed analysis.
    """
    from chronicon import llm_call
    
    # Step 1: Quick sentiment check with local Ollama (fast, free)
    sentiment = llm_call(
        f"Classify sentiment as positive/negative/neutral. Answer with ONE WORD only.\n\nText: {text}",
        model="llama2",
        max_tokens=10,
        temperature=0.0,
        provider="ollama"  # Use local Ollama
    ).strip().lower()
    
    # Step 2: Detailed analysis with Claude (slower, paid, more sophisticated)
    analysis = llm_call(
        f"""Provide a detailed analysis of this text.
        
Text: {text}

Provide:
1. Main themes
2. Tone and style
3. Key insights

Keep response concise (2-3 sentences per section).""",
        model="claude-3-5-sonnet-20241022",
        max_tokens=500,
        temperature=0.7,
        provider="anthropic"  # Use Anthropic Claude
    )
    
    return {
        "text": text,
        "sentiment": sentiment,
        "detailed_analysis": analysis,
        "providers_used": ["ollama", "anthropic"]
    }


@workflow
def multi_model_consensus(question: str) -> dict:
    """
    Get answers from multiple models and compare them.
    
    Uses different models for diverse perspectives.
    """
    from chronicon import llm_call
    
    # Ask Ollama (local llama2)
    ollama_answer = llm_call(
        f"Answer this question concisely: {question}",
        model="llama2",
        max_tokens=200,
        provider="ollama"
    )
    
    # Ask Claude
    claude_answer = llm_call(
        f"Answer this question concisely: {question}",
        model="claude-3-5-sonnet-20241022",
        max_tokens=200,
        provider="anthropic"
    )
    
    # Synthesize with Claude
    synthesis = llm_call(
        f"""Compare these two answers and provide a synthesis:

Question: {question}

Answer 1 (Llama2): {ollama_answer}

Answer 2 (Claude): {claude_answer}

Provide a brief synthesis (2-3 sentences).""",
        model="claude-3-5-sonnet-20241022",
        max_tokens=300,
        provider="anthropic"
    )
    
    return {
        "question": question,
        "ollama": ollama_answer,
        "claude": claude_answer,
        "synthesis": synthesis
    }


def example_1_content_analysis():
    """Example 1: Use Ollama + Anthropic in one workflow."""
    print("\n" + "="*70)
    print("Example 1: Content Analysis (Ollama + Anthropic)")
    print("="*70)
    print("\nThis workflow uses:")
    print("  - Ollama (llama2) for quick sentiment classification")
    print("  - Anthropic (Claude) for detailed analysis")
    print()
    
    # Set up providers
    providers = {
        "ollama": ollama_llm_call(),
        "anthropic": anthropic_llm_call(),
    }
    
    text = """
    The new framework is incredibly powerful and easy to use. 
    The documentation is comprehensive and the examples are clear.
    It saved me hours of debugging and made my workflow much smoother.
    """
    
    result = execute(
        content_analysis,
        text=text.strip(),
        providers=providers
    )
    
    if result.success:
        print(f"✅ Analysis complete!")
        print(f"   Sentiment (Ollama): {result.output['sentiment']}")
        print(f"   Detailed Analysis (Claude):")
        print(f"   {result.output['detailed_analysis']}")
        print(f"   Providers used: {result.output['providers_used']}")
    else:
        print(f"❌ Error: {result.error}")


def example_2_multi_model_consensus():
    """Example 2: Compare answers from multiple models."""
    print("\n" + "="*70)
    print("Example 2: Multi-Model Consensus")
    print("="*70)
    print("\nThis workflow:")
    print("  - Asks the same question to Ollama and Claude")
    print("  - Compares their answers")
    print("  - Synthesizes a consensus view")
    print()
    
    providers = {
        "ollama": ollama_llm_call(),
        "anthropic": anthropic_llm_call(),
    }
    
    question = "What are the key benefits of deterministic workflow engines?"
    
    result = execute(
        multi_model_consensus,
        question=question,
        providers=providers
    )
    
    if result.success:
        print(f"✅ Consensus complete!")
        print(f"\nOllama says:")
        print(f"{result.output['ollama']}")
        print(f"\nClaude says:")
        print(f"{result.output['claude']}")
        print(f"\nSynthesis:")
        print(f"{result.output['synthesis']}")
    else:
        print(f"❌ Error: {result.error}")


def example_3_cost_optimization():
    """Example 3: Use cheap model for routing, expensive for execution."""
    print("\n" + "="*70)
    print("Example 3: Cost Optimization Strategy")
    print("="*70)
    print("\nThis demonstrates using:")
    print("  - Ollama (free) for classification/routing")
    print("  - Claude (paid) only when needed")
    print()
    
    @workflow
    def smart_routing(user_query: str) -> dict:
        """Route to appropriate model based on complexity."""
        from chronicon import llm_call
        
        # Step 1: Classify complexity with free Ollama
        complexity = llm_call(
            f"""Classify this query as 'simple' or 'complex'. Answer with ONE WORD only.

Query: {user_query}""",
            model="llama2",
            max_tokens=5,
            temperature=0.0,
            provider="ollama"
        ).strip().lower()
        
        # Step 2: Route based on complexity
        if "simple" in complexity:
            # Use Ollama for simple queries (free)
            answer = llm_call(
                user_query,
                model="llama2",
                max_tokens=200,
                provider="ollama"
            )
            provider_used = "ollama (free)"
        else:
            # Use Claude for complex queries (paid but better)
            answer = llm_call(
                user_query,
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                provider="anthropic"
            )
            provider_used = "anthropic (paid)"
        
        return {
            "query": user_query,
            "complexity": complexity,
            "answer": answer,
            "provider_used": provider_used
        }
    
    providers = {
        "ollama": ollama_llm_call(),
        "anthropic": anthropic_llm_call(),
    }
    
    # Test with simple query
    result1 = execute(
        smart_routing,
        user_query="What is 2+2?",
        providers=providers
    )
    
    print(f"Query: 'What is 2+2?'")
    if result1.success:
        print(f"  Routed to: {result1.output['provider_used']}")
        print(f"  Answer: {result1.output['answer'][:100]}...")
    
    # Test with complex query
    result2 = execute(
        smart_routing,
        user_query="Explain the philosophical implications of deterministic systems on free will.",
        providers=providers
    )
    
    print(f"\nQuery: 'Explain philosophical implications...'")
    if result2.success:
        print(f"  Routed to: {result2.output['provider_used']}")
        print(f"  Answer: {result2.output['answer'][:100]}...")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("Multi-Provider Workflow Examples")
    print("="*70)
    print("\nThese examples show how to use different LLM providers")
    print("within a single workflow execution.")
    
    # Check prerequisites
    has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))
    has_ollama = False
    
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=1)
        has_ollama = response.status_code == 200
    except:
        pass
    
    if not has_anthropic:
        print("\n⚠️  Set ANTHROPIC_API_KEY to run Anthropic examples")
    
    if not has_ollama:
        print("⚠️  Start Ollama (ollama serve) to run Ollama examples")
    
    if not (has_anthropic and has_ollama):
        print("\nSkipping examples - prerequisites not met")
        print("\nTo run these examples:")
        print("  1. Set ANTHROPIC_API_KEY environment variable")
        print("  2. Install and start Ollama (ollama serve)")
        print("  3. Pull a model (ollama pull llama2)")
        exit(0)
    
    # Run examples
    example_1_content_analysis()
    example_2_multi_model_consensus()
    example_3_cost_optimization()
    
    print("\n" + "="*70)
    print("Key Takeaways:")
    print("="*70)
    print("✓ Use multiple providers in one workflow")
    print("✓ Choose provider per LLM call (provider='name')")
    print("✓ Optimize costs by routing to appropriate models")
    print("✓ Combine strengths of different models")
    print()
