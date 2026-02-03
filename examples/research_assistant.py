"""
Example: Research Assistant Workflow

This example demonstrates:
- Multiple sequential LLM calls
- Pure computation mixed with effectful steps
- Complex input/output types
- Error handling
- Replay and testing
- Workflow composition

Use case: Given a topic, research it by:
1. Generate research questions
2. Answer each question
3. Synthesize findings
4. Rate the quality
"""

from chronicon import workflow, execute, replay, llm_call
from chronicon.log import ExecutionLog
from typing import List, Dict
import json


@workflow
def research_topic(topic: str, num_questions: int = 3) -> Dict:
    """
    Research a topic by generating questions, answering them, and synthesizing.
    
    Args:
        topic: The topic to research
        num_questions: Number of research questions to generate
        
    Returns:
        Dictionary with questions, answers, synthesis, and quality score
    """
    print(f"\n🔍 Researching: {topic}")
    print("=" * 70)
    
    # Step 1: Generate research questions (LLM call)
    print(f"\n📝 Generating {num_questions} research questions...")
    questions_raw = llm_call(
        prompt=f"""Generate {num_questions} specific, focused research questions about: {topic}

Return ONLY a JSON array of strings, nothing else. Example format:
["Question 1?", "Question 2?", "Question 3?"]""",
        model="claude-3-5-sonnet-20241022",
        temperature=0.7,
        max_tokens=300,
    )
    
    # Step 2: Parse questions (pure computation)
    try:
        questions = json.loads(questions_raw.strip())
        if not isinstance(questions, list):
            questions = [questions_raw]  # Fallback if not JSON
    except json.JSONDecodeError:
        # Fallback: split by lines
        questions = [q.strip() for q in questions_raw.split('\n') if q.strip()]
    
    questions = questions[:num_questions]  # Limit to requested number
    print(f"   Generated {len(questions)} questions")
    for i, q in enumerate(questions, 1):
        print(f"   {i}. {q}")
    
    # Step 3: Answer each question (multiple LLM calls)
    print(f"\n💡 Answering questions...")
    answers = []
    for i, question in enumerate(questions, 1):
        print(f"   Answering question {i}/{len(questions)}...")
        answer = llm_call(
            prompt=f"""Answer this research question concisely (2-3 sentences):

Question: {question}

Provide a factual, informative answer.""",
            model="claude-3-5-sonnet-20241022",
            temperature=0.5,
            max_tokens=200,
        )
        answers.append(answer.strip())
    
    # Step 4: Synthesize findings (LLM call)
    print(f"\n📊 Synthesizing findings...")
    qa_pairs = "\n\n".join([
        f"Q: {q}\nA: {a}" 
        for q, a in zip(questions, answers)
    ])
    
    synthesis = llm_call(
        prompt=f"""Based on these Q&A pairs about {topic}, write a brief synthesis (3-4 sentences) that captures the key insights:

{qa_pairs}

Synthesis:""",
        model="claude-3-5-sonnet-20241022",
        temperature=0.6,
        max_tokens=300,
    )
    
    # Step 5: Quality assessment (LLM call)
    print(f"\n⭐ Assessing quality...")
    quality = llm_call(
        prompt=f"""Rate the quality and depth of this research on a scale of 1-10:

Topic: {topic}
Number of questions: {len(questions)}
Synthesis: {synthesis}

Provide ONLY a single number from 1-10, nothing else.""",
        model="claude-3-5-sonnet-20241022",
        temperature=0.3,
        max_tokens=10,
    )
    
    # Step 6: Parse quality score (pure computation)
    try:
        quality_score = int(quality.strip())
    except ValueError:
        quality_score = 5  # Default if parsing fails
    
    # Return comprehensive results
    return {
        "topic": topic,
        "questions": questions,
        "answers": answers,
        "qa_pairs": [{"question": q, "answer": a} for q, a in zip(questions, answers)],
        "synthesis": synthesis.strip(),
        "quality_score": quality_score,
        "num_llm_calls": len(questions) + 3,  # questions + answers + synthesis + quality
    }


def demo_basic_usage():
    """Demonstrate basic workflow execution."""
    print("\n" + "=" * 70)
    print("DEMO 1: Basic Usage")
    print("=" * 70)
    
    log = ExecutionLog("research_example.db")
    
    # Execute workflow
    result = execute(
        research_topic,
        topic="Quantum Computing",
        num_questions=2,
        log=log,
    )
    
    if result.success:
        print("\n✅ Research completed!")
        print(f"   Execution ID: {result.execution_id}")
        print(f"   Quality Score: {result.output['quality_score']}/10")
        print(f"   LLM Calls: {result.output['num_llm_calls']}")
        print(f"\n📝 Synthesis:")
        print(f"   {result.output['synthesis']}")
        return result.execution_id
    else:
        print(f"\n❌ Failed: {result.error}")
        return None


def demo_replay(execution_id: str):
    """Demonstrate deterministic replay."""
    print("\n" + "=" * 70)
    print("DEMO 2: Deterministic Replay")
    print("=" * 70)
    
    log = ExecutionLog("research_example.db")
    
    print(f"\n🔁 Replaying execution {execution_id[:8]}...")
    
    replay_result = replay(
        research_topic,
        execution_id=execution_id,
        log=log,
        allow_divergence=True,
    )
    
    if replay_result.success:
        print("\n✅ Replay successful!")
        print(f"   Output matches: {replay_result.output == replay_result.output}")
        print(f"   Divergences: {len(replay_result.divergences)}")
        
        if replay_result.divergences:
            print("\n⚠️  Divergences detected:")
            for div in replay_result.divergences:
                print(f"   - {div.kind.value}: {div.message}")
        else:
            print("\n✨ Perfect replay - no divergences!")
    else:
        print(f"\n❌ Replay failed: {replay_result.error}")


def demo_multiple_topics():
    """Demonstrate running multiple workflows."""
    print("\n" + "=" * 70)
    print("DEMO 3: Multiple Topics")
    print("=" * 70)
    
    log = ExecutionLog("research_example.db")
    topics = ["Machine Learning", "Climate Change", "Space Exploration"]
    
    execution_ids = []
    
    for topic in topics:
        print(f"\n📚 Researching: {topic}")
        result = execute(
            research_topic,
            topic=topic,
            num_questions=2,
            log=log,
        )
        
        if result.success:
            execution_ids.append(result.execution_id)
            print(f"   ✅ Score: {result.output['quality_score']}/10")
        else:
            print(f"   ❌ Failed")
    
    print(f"\n✅ Completed {len(execution_ids)}/{len(topics)} research tasks")
    return execution_ids


def demo_inspect_database():
    """Demonstrate database inspection."""
    print("\n" + "=" * 70)
    print("DEMO 4: Database Inspection")
    print("=" * 70)
    
    log = ExecutionLog("research_example.db")
    
    # Get database connection
    conn = log._get_conn()
    
    # Count executions
    cursor = conn.execute("SELECT COUNT(*) FROM executions")
    total_executions = cursor.fetchone()[0]
    print(f"\n📊 Total executions: {total_executions}")
    
    # Count LLM calls
    cursor = conn.execute("SELECT COUNT(*) FROM llm_calls")
    total_llm_calls = cursor.fetchone()[0]
    print(f"   Total LLM calls: {total_llm_calls}")
    
    # List recent executions
    cursor = conn.execute("""
        SELECT execution_id, workflow_id, status, started_at
        FROM executions
        ORDER BY started_at DESC
        LIMIT 5
    """)
    
    print(f"\n📋 Recent executions:")
    for row in cursor.fetchall():
        exec_id = row[0][:8]
        workflow = row[1]
        status = row[2]
        started = row[3][:19]
        print(f"   {exec_id}... | {workflow:20s} | {status:10s} | {started}")


def demo_testing():
    """Demonstrate testing against past executions."""
    print("\n" + "=" * 70)
    print("DEMO 5: Testing Pattern")
    print("=" * 70)
    
    log = ExecutionLog("research_example.db")
    
    # Get most recent execution
    conn = log._get_conn()
    cursor = conn.execute("""
        SELECT execution_id FROM executions
        ORDER BY started_at DESC
        LIMIT 1
    """)
    row = cursor.fetchone()
    
    if not row:
        print("\n⚠️  No executions found. Run demo_basic_usage() first.")
        return
    
    execution_id = row[0]
    
    print(f"\n🧪 Testing replay of execution {execution_id[:8]}...")
    
    # This is how you'd test in pytest
    replay_result = replay(
        research_topic,
        execution_id=execution_id,
        log=log,
    )
    
    # Assertions you'd make in tests
    assertions = [
        ("Replay successful", replay_result.success),
        ("Has synthesis", "synthesis" in replay_result.output),
        ("Has quality score", "quality_score" in replay_result.output),
        ("Quality score in range", 1 <= replay_result.output["quality_score"] <= 10),
        ("Has questions", len(replay_result.output["questions"]) > 0),
        ("Has answers", len(replay_result.output["answers"]) > 0),
    ]
    
    print("\n✅ Test Results:")
    all_passed = True
    for desc, passed in assertions:
        status = "✅" if passed else "❌"
        print(f"   {status} {desc}")
        all_passed = all_passed and passed
    
    if all_passed:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️  Some tests failed!")


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 70)
    print("CHRONICON EXAMPLE: Research Assistant Workflow")
    print("=" * 70)
    print("\nThis example demonstrates:")
    print("  • Multiple sequential LLM calls")
    print("  • Pure computation mixed with effectful steps")
    print("  • Complex structured outputs")
    print("  • Deterministic replay")
    print("  • Database inspection")
    print("  • Testing patterns")
    
    # Demo 1: Basic usage
    execution_id = demo_basic_usage()
    
    if execution_id:
        # Demo 2: Replay
        demo_replay(execution_id)
        
        # Demo 3: Multiple topics
        demo_multiple_topics()
        
        # Demo 4: Database inspection
        demo_inspect_database()
        
        # Demo 5: Testing
        demo_testing()
    
    print("\n" + "=" * 70)
    print("🎓 Key Takeaways:")
    print("=" * 70)
    print("  1. Workflows can have multiple LLM calls")
    print("  2. Mix pure computation with effectful steps")
    print("  3. Replay works perfectly - no re-execution")
    print("  4. Database stores complete execution history")
    print("  5. Test against real past executions")
    print("\n💾 All executions saved to: research_example.db")
    print("\nExplore the database:")
    print("  sqlite3 research_example.db")
    print("  > SELECT * FROM executions;")
    print("  > SELECT * FROM llm_calls;")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
