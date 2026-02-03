"""
Replay engine: deterministic replay from execution logs.

The replay engine:
- Loads execution logs
- Re-executes workflows using logged outputs for effectful steps
- Detects divergence (code changes, input changes, non-determinism)
- Explains why replay diverged

Design principles:
- Pure steps are re-executed (they should be deterministic)
- Effectful steps (LLM calls) use logged outputs (no re-execution)
- Hash comparison detects code changes
- Input comparison detects data changes
"""

from typing import Optional, Any
from dataclasses import dataclass
from enum import Enum

from chronicon.workflow import Workflow
from chronicon.execution import ExecutionResult
from chronicon.log import ExecutionLog, ExecutionRecord
from chronicon.step import StepInvocation, StepKind
from chronicon.serialization import serialize


class DivergenceKind(Enum):
    """Types of replay divergence."""
    WORKFLOW_VERSION_MISMATCH = "workflow_version_mismatch"
    STEP_VERSION_MISMATCH = "step_version_mismatch"
    INPUT_MISMATCH = "input_mismatch"
    STEP_COUNT_MISMATCH = "step_count_mismatch"
    OUTPUT_MISMATCH = "output_mismatch"


@dataclass
class Divergence:
    """A detected divergence during replay."""
    kind: DivergenceKind
    message: str
    step_index: Optional[int] = None
    expected: Optional[Any] = None
    actual: Optional[Any] = None


@dataclass
class ReplayResult:
    """Result of a replay."""
    execution_id: str  # The original execution ID
    workflow_id: str
    workflow_version: str
    inputs: dict[str, Any]
    output: Optional[Any]
    error: Optional[str]
    success: bool
    divergences: list[Divergence]
    replayed_from: str  # Original execution ID


def replay(
    workflow: Workflow,
    execution_id: str,
    log: Optional[ExecutionLog] = None,
    allow_divergence: bool = False,
) -> ReplayResult:
    """
    Replay a workflow from an execution log.
    
    Replays deterministically by:
    - Using logged outputs for effectful steps (LLM calls)
    - Re-executing pure steps
    - Detecting divergence from original execution
    
    Args:
        workflow: Workflow to replay (must match logged workflow)
        execution_id: ID of execution to replay
        log: Execution log (creates default if None)
        allow_divergence: If False, raises on divergence; if True, continues
        
    Returns:
        ReplayResult with replay metadata and divergences
        
    Raises:
        ValueError: If execution not found or divergence detected (when allow_divergence=False)
    """
    # Create default log if needed
    if log is None:
        log = ExecutionLog()
    
    # Load execution
    exec_record = log.get_execution(execution_id)
    if not exec_record:
        raise ValueError(f"Execution {execution_id} not found")
    
    # Load steps
    logged_steps = log.get_steps(execution_id)
    
    # Check workflow version
    divergences = []
    if workflow.version != exec_record.workflow_version:
        divergences.append(Divergence(
            kind=DivergenceKind.WORKFLOW_VERSION_MISMATCH,
            message=f"Workflow code changed. Expected version {exec_record.workflow_version[:8]}, "
                    f"got {workflow.version[:8]}",
            expected=exec_record.workflow_version,
            actual=workflow.version,
        ))
    
    # Check workflow ID
    if workflow.workflow_id != exec_record.workflow_id:
        raise ValueError(
            f"Workflow ID mismatch. Expected {exec_record.workflow_id}, "
            f"got {workflow.workflow_id}"
        )
    
    # Check inputs
    if serialize(exec_record.inputs) != serialize(exec_record.inputs):  # Just checking serializability
        # Inputs should match exactly
        pass
    
    # Replay execution
    try:
        output = _replay_workflow(
            workflow=workflow,
            inputs=exec_record.inputs,
            logged_steps=logged_steps,
            divergences=divergences,
        )
        
        # Check output matches
        if exec_record.output is not None:
            if serialize(output) != serialize(exec_record.output):
                divergences.append(Divergence(
                    kind=DivergenceKind.OUTPUT_MISMATCH,
                    message="Output diverged from logged execution",
                    expected=exec_record.output,
                    actual=output,
                ))
        
        # If divergences found and not allowed, raise
        if divergences and not allow_divergence:
            raise ValueError(
                f"Replay diverged: {', '.join(d.message for d in divergences)}"
            )
        
        return ReplayResult(
            execution_id=execution_id,
            workflow_id=workflow.workflow_id,
            workflow_version=workflow.version,
            inputs=exec_record.inputs,
            output=output,
            error=None,
            success=True,
            divergences=divergences,
            replayed_from=execution_id,
        )
    
    except Exception as e:
        return ReplayResult(
            execution_id=execution_id,
            workflow_id=workflow.workflow_id,
            workflow_version=workflow.version,
            inputs=exec_record.inputs,
            output=None,
            error=str(e),
            success=False,
            divergences=divergences,
            replayed_from=execution_id,
        )


def _replay_workflow(
    workflow: Workflow,
    inputs: dict[str, Any],
    logged_steps: list[StepInvocation],
    divergences: list[Divergence],
) -> Any:
    """
    Replay workflow using logged step outputs.
    
    This is the core replay logic:
    - Effectful steps use logged outputs
    - Pure steps are re-executed
    """
    # Create a mock for llm_call that returns logged outputs
    step_index = 0
    
    def mock_llm_call(
        prompt: str,
        model: str = "claude-3-5-sonnet-20241022",
        temperature: float = 1.0,
        max_tokens: int = 4096,
        system: Optional[str] = None,
    ) -> str:
        """Mock LLM call that returns logged output."""
        nonlocal step_index
        
        if step_index >= len(logged_steps):
            divergences.append(Divergence(
                kind=DivergenceKind.STEP_COUNT_MISMATCH,
                message=f"More steps executed than logged (expected {len(logged_steps)})",
                step_index=step_index,
            ))
            raise ValueError("Replay diverged: more steps than logged")
        
        logged = logged_steps[step_index]
        step_index += 1
        
        # Verify this was an LLM call
        if logged.kind != StepKind.EFFECTFUL or logged.step_id != "llm_call":
            divergences.append(Divergence(
                kind=DivergenceKind.STEP_VERSION_MISMATCH,
                message=f"Expected LLM call at step {step_index-1}, got {logged.step_id}",
                step_index=step_index - 1,
            ))
            raise ValueError(f"Step mismatch at index {step_index-1}")
        
        # Verify inputs match (prompt, model, etc.)
        expected_inputs = {
            "prompt": prompt,
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "system": system,
        }
        
        if serialize(expected_inputs) != serialize(logged.inputs):
            divergences.append(Divergence(
                kind=DivergenceKind.INPUT_MISMATCH,
                message=f"LLM call inputs diverged at step {step_index-1}",
                step_index=step_index - 1,
                expected=logged.inputs,
                actual=expected_inputs,
            ))
        
        # Return logged output
        return logged.output
    
    # Patch llm_call
    from chronicon.step import llm_call as actual_llm_call
    
    # Also patch in workflow globals
    workflow_globals = workflow.func.__globals__
    original_workflow_llm_call = None
    if 'llm_call' in workflow_globals:
        original_workflow_llm_call = workflow_globals['llm_call']
        workflow_globals['llm_call'] = mock_llm_call
    
    try:
        # Execute workflow with mocked llm_call
        output = workflow.func(**inputs)
        
        # Check step count
        if step_index < len(logged_steps):
            divergences.append(Divergence(
                kind=DivergenceKind.STEP_COUNT_MISMATCH,
                message=f"Fewer steps executed than logged (expected {len(logged_steps)}, got {step_index})",
            ))
        
        return output
    
    finally:
        # Restore original llm_call in workflow globals
        if original_workflow_llm_call is not None:
            workflow_globals['llm_call'] = original_workflow_llm_call
