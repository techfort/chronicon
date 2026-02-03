"""
Workflow decorator and Workflow class.

A workflow is a Python function decorated with @workflow.
Workflows are:
- Versioned by source code hash
- Explicit about inputs and outputs (via type hints)
- Executed by the execution engine
- Replayable from execution logs
"""

from typing import Callable, Any, Optional, TypeVar, ParamSpec
from dataclasses import dataclass
import inspect

from chronicon.hash import hash_source


P = ParamSpec('P')
R = TypeVar('R')


@dataclass
class WorkflowMetadata:
    """Metadata about a workflow definition."""
    workflow_id: str
    version: str
    func: Callable
    signature: inspect.Signature


class Workflow:
    """
    A workflow definition.
    
    Wraps a Python function with metadata for execution and replay.
    """
    
    def __init__(
        self,
        func: Callable[P, R],
        workflow_id: Optional[str] = None,
    ):
        """
        Create a workflow from a function.
        
        Args:
            func: The workflow function
            workflow_id: Optional custom ID (defaults to function name)
        """
        self.func = func
        self.workflow_id = workflow_id or func.__name__
        self.version = hash_source(func)
        self.signature = inspect.signature(func)
        
        # Validate signature
        self._validate_signature()
        
        # Preserve function metadata
        self.__name__ = func.__name__
        self.__doc__ = func.__doc__
        self.__module__ = func.__module__
        self.__annotations__ = func.__annotations__
    
    def _validate_signature(self) -> None:
        """Validate workflow function signature."""
        # Check for *args, **kwargs
        for param in self.signature.parameters.values():
            if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                raise ValueError(
                    f"Workflow {self.workflow_id} cannot use *args or **kwargs. "
                    "All inputs must be explicit for deterministic replay."
                )
        
        # Recommend type hints (but don't enforce for now)
        params_without_annotations = [
            name for name, param in self.signature.parameters.items()
            if param.annotation == inspect.Parameter.empty
        ]
        if params_without_annotations:
            import warnings
            warnings.warn(
                f"Workflow {self.workflow_id} has parameters without type hints: "
                f"{params_without_annotations}. Type hints improve clarity."
            )
    
    def metadata(self) -> WorkflowMetadata:
        """Get workflow metadata."""
        return WorkflowMetadata(
            workflow_id=self.workflow_id,
            version=self.version,
            func=self.func,
            signature=self.signature,
        )
    
    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        """
        Call the workflow function directly (without execution engine).
        
        This is useful for testing or debugging, but does not log execution.
        For normal execution with logging, use the execute() function.
        """
        return self.func(*args, **kwargs)
    
    def __repr__(self) -> str:
        return f"Workflow({self.workflow_id}, v={self.version[:8]})"


def workflow(
    func: Optional[Callable[P, R]] = None,
    *,
    workflow_id: Optional[str] = None,
) -> Callable[[Callable[P, R]], Workflow]:
    """
    Decorator to define a workflow.
    
    A workflow is a Python function that can be:
    - Executed with full logging
    - Replayed deterministically
    - Tested against past executions
    
    Usage:
        @workflow
        def my_workflow(x: int, y: int) -> int:
            result = step_1(x)
            result = step_2(result, y)
            return result
        
        @workflow(workflow_id="custom_id")
        def other_workflow(data: str) -> str:
            return process(data)
    
    Args:
        func: The workflow function (when used without arguments)
        workflow_id: Optional custom workflow ID (defaults to function name)
        
    Returns:
        Workflow instance wrapping the function
    """
    def decorator(f: Callable[P, R]) -> Workflow:
        return Workflow(f, workflow_id=workflow_id)
    
    if func is None:
        # Called with arguments: @workflow(workflow_id="...")
        return decorator
    else:
        # Called without arguments: @workflow
        return decorator(func)
