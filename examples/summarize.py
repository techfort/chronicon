"""
Example: Text summarization workflow

Demonstrates:
- Workflow definition
- LLM calls
- Execution with logging
- Replay from logs
"""

from chronicon import workflow, execute, replay, llm_call
from chronicon.log import ExecutionLog


@workflow
def summarize_text(text: str) -> dict:
    """
    Summarize text and evaluate the quality of the summary.
    
    Args:
        text: Text to summarize
        
    Returns:
        Dictionary with summary and quality score
    """
    # Generate summary
    summary = llm_call(
        prompt=f"Summarize the following text in 2-3 sentences:\n\n{text}",
        model="claude-3-5-sonnet-20241022",
        temperature=0.7,
        max_tokens=200,
    )
    
    # Evaluate quality
    score_text = llm_call(
        prompt=f"Rate the quality of this summary on a scale of 1-10:\n\nOriginal: {text}\n\nSummary: {summary}\n\nProvide only the numeric score.",
        model="claude-3-5-sonnet-20241022",
        temperature=0.3,
        max_tokens=10,
    )
    
    # Parse score
    try:
        score = int(score_text.strip())
    except ValueError:
        score = 5  # Default if parsing fails
    
    return {
        "summary": summary,
        "score": score,
        "original_length": len(text),
        "summary_length": len(summary),
    }


def main():
    """Run the example."""
    
    # Sample text
    text = """
    Artificial intelligence has made remarkable progress in recent years, particularly
    in the field of natural language processing. Large language models, trained on
    vast amounts of text data, have demonstrated impressive capabilities in understanding
    and generating human-like text. These models can perform tasks such as translation,
    summarization, question answering, and even creative writing. However, they also
    present challenges related to reliability, bias, and the potential for misuse.
    As these technologies continue to evolve, it's crucial to develop them responsibly
    and ensure they benefit society as a whole.
    """
    
    # Create execution log
    log = ExecutionLog("examples.db")
    
    print("=" * 70)
    print("CHRONICON EXAMPLE: Text Summarization")
    print("=" * 70)
    print()
    
    # Execute workflow
    print("📝 Running workflow...")
    print()
    result = execute(summarize_text, text=text, log=log)
    
    if result.success:
        print(f"✅ Execution completed: {result.execution_id}")
        print()
        print("Output:")
        print(f"  Summary: {result.output['summary']}")
        print(f"  Score: {result.output['score']}/10")
        print(f"  Compression: {result.output['original_length']} → {result.output['summary_length']} chars")
        print()
        print(f"Steps executed: {len(result.steps)}")
        for i, step in enumerate(result.steps):
            print(f"  {i+1}. {step.step_id} ({step.kind.value})")
        print()
    else:
        print(f"❌ Execution failed: {result.error}")
        return
    
    # Replay workflow
    print("-" * 70)
    print("🔁 Replaying workflow from logs...")
    print()
    
    replay_result = replay(
        summarize_text,
        execution_id=result.execution_id,
        log=log,
        allow_divergence=True,
    )
    
    if replay_result.success:
        print(f"✅ Replay completed")
        print()
        
        if replay_result.divergences:
            print(f"⚠️  Divergences detected: {len(replay_result.divergences)}")
            for div in replay_result.divergences:
                print(f"  - {div.kind.value}: {div.message}")
        else:
            print("✅ Perfect replay - no divergences")
        
        print()
        print("Replay output matches:", replay_result.output == result.output)
    else:
        print(f"❌ Replay failed: {replay_result.error}")
    
    print()
    print("=" * 70)
    print(f"💾 Execution log saved to: {log.db_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
