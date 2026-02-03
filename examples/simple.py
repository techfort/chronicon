"""
Example: Simple workflow demonstrating core concepts

A minimal example showing:
- Workflow definition
- Pure computation
- LLM calls
- Execution and replay
"""

from chronicon import workflow, execute, replay, llm_call
from chronicon.log import ExecutionLog


@workflow
def classify_sentiment(text: str) -> dict:
    """
    Classify the sentiment of text.
    
    Returns sentiment label and confidence score.
    """
    # LLM call for classification
    result = llm_call(
        prompt=f"Classify the sentiment of this text as positive, negative, or neutral. "
                f"Respond with only the label.\n\nText: {text}",
        model="claude-3-5-sonnet-20241022",
        temperature=0.0,  # Deterministic
        max_tokens=10,
    )
    
    sentiment = result.strip().lower()
    
    # Pure computation - calculate confidence (simplified)
    confidence = 0.95 if sentiment in ["positive", "negative", "neutral"] else 0.5
    
    return {
        "text": text,
        "sentiment": sentiment,
        "confidence": confidence,
    }


if __name__ == "__main__":
    log = ExecutionLog("examples.db")
    
    # Run
    result = execute(
        classify_sentiment,
        text="I absolutely love this product! It exceeded all my expectations.",
        log=log,
    )
    
    print(f"Execution: {result.execution_id}")
    print(f"Output: {result.output}")
    print()
    
    # Replay
    replay_result = replay(
        classify_sentiment,
        execution_id=result.execution_id,
        log=log,
    )
    
    print(f"Replay: {replay_result.replayed_from}")
    print(f"Output matches: {replay_result.output == result.output}")
    print(f"Divergences: {len(replay_result.divergences)}")
