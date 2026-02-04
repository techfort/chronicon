"""
Replay Google AI Studio + Ollama example executions.

This demonstrates replaying workflows from execution logs, which:
- Uses logged LLM responses (no re-execution of API calls)
- Re-executes pure Python steps
- Detects divergences if code changed
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chronicon import replay, google_llm_call, ollama_llm_call
from chronicon.log import ExecutionLog

# Import workflows directly
import importlib.util
spec = importlib.util.spec_from_file_location(
    "google_ollama_example",
    os.path.join(os.path.dirname(__file__), "google_ollama_example.py")
)
google_ollama_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(google_ollama_module)

code_analysis_pipeline = google_ollama_module.code_analysis_pipeline
code_generation_with_review = google_ollama_module.code_generation_with_review
documentation_and_code_together = google_ollama_module.documentation_and_code_together


def main():
    # Set Google API key
    os.environ["GOOGLE_API_KEY"] = "AIzaSyDki6XzcXbCSLOea2CMqVHJiv79d0ZHR0Y"
    
    # Connect to the execution log database
    log = ExecutionLog(db_path="google_ollama_example.db")
    
    # Get the most recent failed execution for each workflow
    print("=" * 70)
    print("Replaying Google AI Studio + Ollama Executions")
    print("=" * 70)
    print()
    
    # Find the last code_analysis_pipeline execution
    print("🔍 Finding most recent executions...")
    executions = log._conn.execute(
        """
        SELECT execution_id, workflow_id, started_at, error
        FROM executions 
        WHERE workflow_id IN ('code_analysis_pipeline', 'code_generation_with_review', 'documentation_and_code_together')
        ORDER BY started_at DESC 
        LIMIT 3
        """
    ).fetchall()
    
    if not executions:
        print("❌ No executions found in database")
        return
    
    print(f"✅ Found {len(executions)} executions")
    print()
    
    # Configure providers for replay (even though they won't be called)
    providers = {
        "google": google_llm_call(
            api_key=os.environ.get("GOOGLE_API_KEY", ""),
        ),
        "deepseek": ollama_llm_call(
            endpoint="http://localhost:11434",
        ),
    }
    
    # Map workflow IDs to workflow objects
    workflows = {
        "code_analysis_pipeline": code_analysis_pipeline,
        "code_generation_with_review": code_generation_with_review,
        "documentation_and_code_together": documentation_and_code_together,
    }
    
    # Replay each execution
    for exec_id, workflow_id, started_at, error in executions:
        print("=" * 70)
        print(f"Replaying: {workflow_id}")
        print(f"Execution ID: {exec_id}")
        print(f"Started: {started_at}")
        print("=" * 70)
        print()
        
        workflow_obj = workflows.get(workflow_id)
        if not workflow_obj:
            print(f"❌ Unknown workflow: {workflow_id}")
            continue
        
        try:
            # Replay uses logged LLM outputs, doesn't make actual API calls
            print("📼 Replaying from logs (no API calls will be made)...")
            result = replay(
                workflow_obj,
                execution_id=exec_id,
                log=log,
                allow_divergence=True,  # Allow divergence for demonstration
            )
            
            print()
            print(f"Status: {'✅ Success' if result.success else '❌ Failed'}")
            
            if result.divergences:
                print(f"⚠️  Detected {len(result.divergences)} divergences:")
                for div in result.divergences:
                    print(f"  - {div.kind.value}: {div.message}")
            else:
                print("✅ No divergences - replay matched original execution exactly")
            
            if result.error:
                print(f"Error: {result.error[:200]}...")
            
            # Show the steps that were replayed
            steps = log.get_steps(exec_id)
            print()
            print(f"📝 Replayed {len(steps)} steps:")
            for i, step in enumerate(steps, 1):
                provider = step.inputs.get("provider", "unknown")
                model = step.inputs.get("model", "unknown")
                prompt_preview = step.inputs.get("prompt", "")[:60].replace("\n", " ")
                
                print(f"  {i}. {step.step_id}")
                print(f"     Provider: {provider}, Model: {model}")
                print(f"     Prompt: {prompt_preview}...")
                
                if step.output:
                    output_preview = str(step.output)[:80].replace("\n", " ")
                    print(f"     Output: {output_preview}...")
                print()
            
        except Exception as e:
            print(f"❌ Replay failed: {e}")
        
        print()
    
    print("=" * 70)
    print("💡 Key Points About Replay:")
    print("=" * 70)
    print("• Replay uses LOGGED outputs from the database")
    print("• No actual API calls are made (saves cost & quota)")
    print("• Pure Python steps ARE re-executed")
    print("• Divergences detected if code changed since original run")
    print("• Useful for debugging, testing, and analyzing past executions")


if __name__ == "__main__":
    import os
    main()
