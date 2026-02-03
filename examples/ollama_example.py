"""
Example: Using Ollama with Chronicon

This example shows how to use a local Ollama model instead of Anthropic's API.

Prerequisites:
1. Install Ollama: https://ollama.ai/
2. Pull a model: ollama pull llama2
3. Start Ollama (it runs as a service)

No API key needed - everything runs locally!
"""

from chronicon import workflow, execute, replay
from chronicon.log import ExecutionLog

# Import Ollama's llm_call and replace the default globally
import chronicon.step
from chronicon.integrations.ollama import llm_call

# Monkey-patch: Replace Anthropic's llm_call with Ollama's
chronicon.step.llm_call = llm_call


@workflow
def local_sentiment_analysis(text: str) -> dict:
    """
    Analyze sentiment using a local Ollama model.
    
    This workflow runs entirely on your machine - no API calls,
    no API keys, no cloud dependencies.
    """
    
    # Use Ollama's llama2 model (or mistral, codellama, etc.)
    result = llm_call(
        prompt=f"""Classify the sentiment of this text as positive, negative, or neutral.
Respond with ONLY the label (positive/negative/neutral) and nothing else.

Text: {text}""",
        model="deepseek-coder:6.7b",  # or "mistral", "codellama", etc.
        temperature=0.0,
        max_tokens=10,
    )
    
    sentiment = result.strip().lower()
    
    # Simple confidence calculation
    confidence = 0.95 if sentiment in ["positive", "negative", "neutral"] else 0.5
    
    return {
        "text": text,
        "sentiment": sentiment,
        "confidence": confidence,
        "model": "deepseek-coder:6.7b",
        "provider": "ollama",
    }


def main():
    print("\n" + "=" * 70)
    print("CHRONICON + OLLAMA: Local LLM Workflow")
    print("=" * 70)
    print("\nUsing local Ollama model - no API key required!")
    print("Make sure Ollama is running: ollama serve")
    print()
    
    log = ExecutionLog("ollama_example.db")
    
    # Test text
    text = "I absolutely love using local models! No API costs and total privacy."
    
    # Execute workflow
    print(f"📝 Analyzing: '{text}'")
    print()
    
    try:
        result = execute(
            local_sentiment_analysis,
            text=text,
            log=log,
        )
        
        if result.success:
            print("✅ Analysis complete!")
            print(f"   Execution ID: {result.execution_id}")
            print(f"   Sentiment: {result.output['sentiment']}")
            print(f"   Confidence: {result.output['confidence']}")
            print(f"   Model: {result.output['model']}")
            print(f"   Provider: {result.output['provider']}")
            print()
            
            # Replay
            print("🔁 Replaying from logs...")
            replay_result = replay(
                local_sentiment_analysis,
                execution_id=result.execution_id,
                log=log,
            )
            
            if replay_result.success:
                print("✅ Replay successful!")
                print(f"   Output matches: {replay_result.output == result.output}")
                print(f"   Divergences: {len(replay_result.divergences)}")
            else:
                print(f"❌ Replay failed: {replay_result.error}")
        else:
            print(f"❌ Execution failed: {result.error}")
            
    except ConnectionError as e:
        print("❌ Could not connect to Ollama!")
        print()
        print("Make sure Ollama is running:")
        print("  1. Install: https://ollama.ai/")
        print("  2. Pull model: ollama pull llama2")
        print("  3. Check status: curl http://localhost:11434/api/tags")
        print()
        print(f"Error: {e}")
    
    print()
    print("=" * 70)
    print("💾 Execution saved to: ollama_example.db")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
