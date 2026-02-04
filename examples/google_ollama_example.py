"""
Example: Google AI Studio + Ollama DeepSeek-Coder

This demonstrates using:
- Google AI Studio (Gemini) - Hosted, powerful general-purpose model
- Ollama DeepSeek-Coder - Local, specialized code model

Use cases:
- Google Gemini for general reasoning and analysis
- DeepSeek-Coder for code-specific tasks (review, explanation, generation)
"""

import os
from chronicon import workflow, execute, google_llm_call, ollama_llm_call
from chronicon.log import ExecutionLog


@workflow
def code_analysis_pipeline(code: str, description: str) -> dict:
    """
    Analyze code using specialized models for different tasks.
    
    - DeepSeek-Coder (local) reviews the code technically
    - Google Gemini (cloud) provides high-level insights
    """
    from chronicon import llm_call
    
    # Step 1: Technical code review with DeepSeek-Coder (local specialist)
    print("  → DeepSeek-Coder reviewing code...")
    code_review = llm_call(
        f"""Review this code for quality, bugs, and best practices.

{code}

Provide:
1. Quality assessment (1-5 stars)
2. Potential bugs or issues
3. Improvement suggestions

Keep it concise (3-4 sentences).""",
        model="deepseek-coder:6.7b",
        temperature=0.3,
        max_tokens=300,
        provider="deepseek"
    )
    
    # Step 2: Business/architectural analysis with Gemini (cloud generalist)
    print("  → Google Gemini analyzing architecture...")
    gemini_analysis = llm_call(
        f"""Analyze this code from a high-level perspective.

Code: {code}

Description: {description}

Provide:
1. Architectural assessment
2. Scalability considerations
3. Business logic clarity

Keep it concise (3-4 sentences).""",
        model="gemini-2.0-flash",
        temperature=0.7,
        max_tokens=300,
        provider="google"
    )
    
    return {
        "code": code,
        "technical_review": code_review,
        "architectural_analysis": gemini_analysis,
        "reviewers": {
            "technical": "DeepSeek-Coder 6.7B (local)",
            "architectural": "Google Gemini Pro (cloud)"
        }
    }


@workflow
def code_generation_with_review(task: str) -> dict:
    """
    Generate code with Google Gemini, review with DeepSeek-Coder.
    
    This workflow shows how to combine:
    - Gemini's strong generation capabilities
    - DeepSeek-Coder's code expertise for validation
    """
    from chronicon import llm_call
    
    # Step 1: Generate code with Gemini
    print("  → Google Gemini generating code...")
    generated_code = llm_call(
        f"""Generate Python code for this task: {task}

Provide clean, working code with comments. Return ONLY the code, no explanation.""",
        model="gemini-2.0-flash",
        temperature=0.8,
        max_tokens=500,
        provider="google"
    )
    
    # Step 2: Review with DeepSeek-Coder
    print("  → DeepSeek-Coder reviewing generated code...")
    review = llm_call(
        f"""Review this generated code:

{generated_code}

Is it correct? Any issues? Rate quality 1-5 stars. Be concise (2-3 sentences).""",
        model="deepseek-coder:6.7b",
        temperature=0.2,
        max_tokens=200,
        provider="deepseek"
    )
    
    return {
        "task": task,
        "generated_code": generated_code,
        "code_review": review,
        "generator": "Google Gemini Pro",
        "reviewer": "DeepSeek-Coder 6.7B"
    }


@workflow
def documentation_and_code_together(feature_request: str) -> dict:
    """
    Use both models in parallel for comprehensive output.
    
    - Gemini writes user documentation
    - DeepSeek-Coder implements the feature
    """
    from chronicon import llm_call
    
    # Generate user documentation with Gemini
    print("  → Google Gemini writing documentation...")
    documentation = llm_call(
        f"""Write user documentation for this feature: {feature_request}

Include:
- Overview
- How to use
- Example

Keep it brief (100 words).""",
        model="gemini-2.0-flash",
        temperature=0.7,
        max_tokens=300,
        provider="google"
    )
    
    # Generate implementation with DeepSeek-Coder
    print("  → DeepSeek-Coder implementing feature...")
    implementation = llm_call(
        f"""Implement this feature in Python: {feature_request}

Provide a complete, working implementation with type hints.
Keep it simple but functional.""",
        model="deepseek-coder:6.7b",
        temperature=0.5,
        max_tokens=400,
        provider="deepseek"
    )
    
    return {
        "feature": feature_request,
        "documentation": documentation,
        "implementation": implementation
    }


def example_1_code_review():
    """Example 1: Code review using both models."""
    print("\n" + "="*70)
    print("Example 1: Code Review (DeepSeek-Coder + Gemini)")
    print("="*70)
    
    sample_code = '''
def calculate_total(items):
    total = 0
    for item in items:
        total = total + item["price"] * item["quantity"]
    return total
'''
    
    result = execute(
        code_analysis_pipeline,
        code=sample_code,
        description="Calculate shopping cart total",
        providers=providers,
        log=log
    )
    
    if result.success:
        print("\n✅ Code Analysis Complete!")
        print(f"\n📝 Technical Review (DeepSeek-Coder):")
        print(result.output["technical_review"])
        print(f"\n🏗️  Architectural Analysis (Google Gemini):")
        print(result.output["architectural_analysis"])
        print(f"\nReviewers: {result.output['reviewers']}")
    else:
        print(f"❌ Error: {result.error}")


def example_2_code_generation():
    """Example 2: Generate and validate code."""
    print("\n" + "="*70)
    print("Example 2: Code Generation + Review")
    print("="*70)
    
    result = execute(
        code_generation_with_review,
        task="Create a function to validate email addresses using regex",
        providers=providers,
        log=log
    )
    
    if result.success:
        print("\n✅ Code Generated and Reviewed!")
        print(f"\n💻 Generated Code ({result.output['generator']}):")
        print(result.output["generated_code"])
        print(f"\n🔍 Review ({result.output['reviewer']}):")
        print(result.output["code_review"])
    else:
        print(f"❌ Error: {result.error}")


def example_3_parallel_work():
    """Example 3: Documentation + Implementation in parallel."""
    print("\n" + "="*70)
    print("Example 3: Parallel Documentation + Implementation")
    print("="*70)
    
    result = execute(
        documentation_and_code_together,
        feature_request="Add retry logic with exponential backoff to API calls",
        providers=providers,
        log=log
    )
    
    if result.success:
        print("\n✅ Feature Complete with Documentation!")
        print(f"\n📚 Documentation (Google Gemini):")
        print(result.output["documentation"])
        print(f"\n⚙️  Implementation (DeepSeek-Coder):")
        print(result.output["implementation"])
    else:
        print(f"❌ Error: {result.error}")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("Google AI Studio + Ollama DeepSeek-Coder Example")
    print("="*70)
    
    # Check prerequisites
    google_key = "AIzaSyDki6XzcXbCSLOea2CMqVHJiv79d0ZHR0Y"
    
    print("\n🔍 Checking prerequisites...")
    
    # Check Ollama
    has_ollama = False
    has_deepseek = False
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            has_ollama = True
            models = response.json().get("models", [])
            has_deepseek = any("deepseek-coder" in m.get("name", "") for m in models)
    except:
        pass
    
    if not has_ollama:
        print("❌ Ollama not running. Start it with: ollama serve")
        exit(1)
    
    if not has_deepseek:
        print("❌ DeepSeek-Coder not found. Pull it with: ollama pull deepseek-coder:6.7b")
        exit(1)
    
    print("✅ Ollama running")
    print("✅ DeepSeek-Coder available")
    print("✅ Google AI Studio API key configured")
    
    # Set up providers
    providers = {
        "google": google_llm_call(api_key=google_key),
        "deepseek": ollama_llm_call(),
    }
    
    log = ExecutionLog("google_ollama_example.db")
    
    print("\n" + "="*70)
    print("Running Examples")
    print("="*70)
    
    # Run examples
    example_1_code_review()
    example_2_code_generation()
    example_3_parallel_work()
    
    print("\n" + "="*70)
    print("Summary")
    print("="*70)
    print("✅ Used Google Gemini Pro for general reasoning and generation")
    print("✅ Used DeepSeek-Coder 6.7B for specialized code analysis")
    print("✅ All executions logged to google_ollama_example.db")
    print(f"✅ Can replay any execution with full provider information")
    
    print("\n💡 Key Benefits:")
    print("   • Use Gemini (cloud) when you need strong general reasoning")
    print("   • Use DeepSeek-Coder (local) for fast, specialized code tasks")
    print("   • Combine both for comprehensive analysis")
    print("   • All provider choices logged for debugging/replay")
    print()
