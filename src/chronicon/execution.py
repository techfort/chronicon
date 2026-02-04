"""
Execution engine: runs workflows with full logging.

The execution engine:
- Intercepts step calls (including llm_call)
- Logs all inputs, outputs, and metadata
- Handles errors and failures
- Returns execution results

Design:
- Single-threaded, sequential execution
- No parallelism
- Explicit, synchronous
"""

from typing import Any, Optional, Callable
from dataclasses import dataclass
import inspect
import traceback

from chronicon.workflow import Workflow
from chronicon.step import Step, StepInvocation, StepKind
from chronicon.log import ExecutionLog
from chronicon.serialization import is_serializable


@dataclass
class ExecutionResult:
    """Result of a workflow execution."""
    execution_id: str
    workflow_id: str
    workflow_version: str
    inputs: dict[str, Any]
    output: Optional[Any]
    error: Optional[str]
    steps: list[StepInvocation]
    success: bool


class ExecutionContext:
    """
    Execution context for tracking workflow execution state.
    
    This is passed implicitly during execution to intercept
    step calls and log them.
    """
    
    def __init__(
        self,
        execution_id: str,
        workflow_id: str,
        workflow_version: str,
        log: ExecutionLog,
    ):
        self.execution_id = execution_id
        self.workflow_id = workflow_id
        self.workflow_version = workflow_version
        self.log = log
        self.step_index = 0
        self.steps: list[StepInvocation] = []
    
    def log_step(self, invocation: StepInvocation) -> None:
        """Log a step invocation."""
        self.log.log_step(self.execution_id, self.step_index, invocation)
        self.steps.append(invocation)
        self.step_index += 1


# Global execution context (thread-local would be better, but keeping it simple)
_current_execution: Optional[ExecutionContext] = None


def get_current_execution() -> Optional[ExecutionContext]:
    """Get the current execution context."""
    return _current_execution


def execute(
    workflow: Workflow,
    *args,
    log: Optional[ExecutionLog] = None,
    llm_call: Optional[Callable] = None,
    providers: Optional[dict[str, Callable]] = None,
    **kwargs,
) -> ExecutionResult:
    """
    Execute a workflow with full logging.
    
    This is the main entry point for running workflows.
    
    Args:
        workflow: Workflow to execute
        *args: Positional arguments to workflow
        log: Execution log (creates default if None)
        llm_call: Optional single llm_call function (for simple cases)
        providers: Optional dict of named provider functions {"anthropic": fn, "ollama": fn}
                  Allows workflows to use different providers per call
        **kwargs: Keyword arguments to workflow
        
    Returns:
        ExecutionResult with execution metadata and output
        
    Raises:
        ValueError: If inputs are not serializable
    """
    global _current_execution
    
    # Create default log if needed
    if log is None:
        log = ExecutionLog()
    
    # Bind arguments to workflow signature
    bound = workflow.signature.bind(*args, **kwargs)
    bound.apply_defaults()
    inputs = dict(bound.arguments)
    
    # Validate inputs are serializable
    if not is_serializable(inputs):
        raise ValueError(f"Workflow inputs must be serializable: {inputs}")
    
    # Start execution
    execution_id = log.start_execution(
        workflow_id=workflow.workflow_id,
        workflow_version=workflow.version,
        inputs=inputs,
    )
    
    # Create execution context
    ctx = ExecutionContext(
        execution_id=execution_id,
        workflow_id=workflow.workflow_id,
        workflow_version=workflow.version,
        log=log,
    )
    
    # Set global context
    _current_execution = ctx
    
    try:
        # Set up provider resolution
        provider_registry = {}
        default_provider = None
        
        if providers:
            # Multiple providers: use the registry
            provider_registry = providers
            default_provider = providers.get("default") or next(iter(providers.values()))
        elif llm_call:
            # Single provider: use as default
            default_provider = llm_call
        else:
            # No providers: use built-in chronicon.step.llm_call
            import sys
            step_module = sys.modules['chronicon.step']
            default_provider = step_module.llm_call
        
        def logged_llm_call(
            prompt: str,
            model: str = "claude-3-5-sonnet-20241022",
            temperature: float = 1.0,
            max_tokens: int = 4096,
            system: Optional[str] = None,
            provider: Optional[str] = None,
        ) -> str:
            """LLM call with logging."""
            # Resolve which provider to use
            if provider and provider in provider_registry:
                actual_llm_call = provider_registry[provider]
            elif provider:
                raise ValueError(
                    f"Unknown provider '{provider}'. "
                    f"Available: {list(provider_registry.keys())}"
                )
            else:
                actual_llm_call = default_provider
            
            # Call the actual LLM
            response = actual_llm_call(
                prompt=prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                system=system,
            )
            
            # Log the invocation
            invocation = StepInvocation(
                step_id="llm_call",
                step_version="builtin",
                kind=StepKind.EFFECTFUL,
                inputs={
                    "prompt": prompt,
                    "model": model,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "system": system,
                    "provider": provider,  # Track which provider was used
                },
                output=response,
                llm_model=model,
                llm_prompt=prompt,
                llm_temperature=temperature,
                llm_max_tokens=max_tokens,
                llm_response_raw=response,
            )
            
            ctx.log_step(invocation)
            
            return response
        
        # Replace llm_call globally so workflows can import it
        import sys
        step_module = sys.modules['chronicon.step']
        chronicon_module = sys.modules['chronicon']
        
        original_step_llm_call = step_module.llm_call
        original_chronicon_llm_call = chronicon_module.llm_call
        
        step_module.llm_call = logged_llm_call
        chronicon_module.llm_call = logged_llm_call
        
        # Also replace in workflow's globals if it was imported early
        workflow_globals = workflow.func.__globals__
        original_workflow_llm_call = None
        if 'llm_call' in workflow_globals:
            original_workflow_llm_call = workflow_globals['llm_call']
            workflow_globals['llm_call'] = logged_llm_call
        
        try:
            # Execute workflow
            output = workflow.func(**inputs)
            
            # Validate output is serializable
            if not is_serializable(output):
                raise ValueError(f"Workflow output must be serializable: {output}")
            
            # Complete execution
            log.complete_execution(execution_id, output=output)
            
            return ExecutionResult(
                execution_id=execution_id,
                workflow_id=workflow.workflow_id,
                workflow_version=workflow.version,
                inputs=inputs,
                output=output,
                error=None,
                steps=ctx.steps,
                success=True,
            )
            
        finally:
            # Restore original llm_call
            step_module.llm_call = original_step_llm_call
            chronicon_module.llm_call = original_chronicon_llm_call
            
            if original_workflow_llm_call is not None:
                workflow_globals['llm_call'] = original_workflow_llm_call
    
    except Exception as e:
        # Log failure
        error_msg = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"
        log.complete_execution(execution_id, error=error_msg)
        
        return ExecutionResult(
            execution_id=execution_id,
            workflow_id=workflow.workflow_id,
            workflow_version=workflow.version,
            inputs=inputs,
            output=None,
            error=error_msg,
            steps=ctx.steps,
            success=False,
        )
    
    finally:
        # Clear global context
        _current_execution = None
