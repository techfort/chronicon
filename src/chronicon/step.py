"""
Step abstraction: atomic units of workflow execution.

Two kinds of steps:
1. Pure: Deterministic functions (no side effects)
2. Effectful: LLM calls, API calls, IO (logged and replayable)

All steps are:
- Identified by name and version hash
- Have serializable inputs and outputs
- Logged in execution trace
"""

from typing import Callable, Any, Optional
from dataclasses import dataclass
from enum import Enum
import inspect

from chronicon.hash import hash_source
from chronicon.serialization import serialize, deserialize


class StepKind(Enum):
    """Step classification."""
    PURE = "pure"
    EFFECTFUL = "effectful"


@dataclass
class StepInvocation:
    """
    A single invocation of a step during workflow execution.
    
    Captures everything needed to replay or test this step execution.
    """
    step_id: str
    step_version: str
    kind: StepKind
    inputs: dict[str, Any]
    output: Any
    error: Optional[str] = None
    
    # For effectful steps (LLM calls)
    llm_model: Optional[str] = None
    llm_prompt: Optional[str] = None
    llm_temperature: Optional[float] = None
    llm_max_tokens: Optional[int] = None
    llm_response_raw: Optional[str] = None


class Step:
    """
    A step definition: a function with metadata for execution and replay.
    """
    
    def __init__(
        self,
        func: Callable,
        kind: StepKind,
        step_id: Optional[str] = None,
    ):
        self.func = func
        self.kind = kind
        self.step_id = step_id or func.__name__
        self.version = hash_source(func)
        
        # Validate function signature
        sig = inspect.signature(func)
        for param in sig.parameters.values():
            if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                raise ValueError(f"Step {self.step_id} cannot use *args or **kwargs")
    
    def __call__(self, *args, **kwargs) -> Any:
        """Execute the step function."""
        return self.func(*args, **kwargs)
    
    def __repr__(self) -> str:
        return f"Step({self.step_id}, {self.kind.value}, v={self.version[:8]})"


def step(func: Optional[Callable] = None, *, step_id: Optional[str] = None) -> Callable:
    """
    Decorator for pure (deterministic) steps.
    
    Pure steps have no side effects and always return the same output
    for the same inputs. They are still logged but not mocked during replay.
    
    Usage:
        @step
        def add(x: int, y: int) -> int:
            return x + y
        
        @step(step_id="custom_id")
        def process(data: str) -> str:
            return data.upper()
    """
    def decorator(f: Callable) -> Step:
        return Step(f, StepKind.PURE, step_id=step_id)
    
    if func is None:
        # Called with arguments: @step(step_id="...")
        return decorator
    else:
        # Called without arguments: @step
        return decorator(func)


# LLM call implementation

def llm_call(
    prompt: str,
    model: str = "claude-3-5-sonnet-20241022",
    temperature: float = 1.0,
    max_tokens: int = 4096,
    system: Optional[str] = None,
) -> str:
    """
    Make an LLM call (Anthropic Claude).
    
    This is an effectful operation that is:
    - Logged in execution trace
    - Replayed from logs (not re-executed)
    - Includes full request/response metadata
    
    Args:
        prompt: The user prompt
        model: Anthropic model name
        temperature: Sampling temperature (0-1)
        max_tokens: Maximum tokens in response
        system: Optional system prompt
        
    Returns:
        The text response from the LLM
        
    Note:
        This function is NOT decorated as a step. It's called directly
        from workflows and the execution engine handles the logging.
        During replay, the logged response is returned without calling the API.
    """
    import anthropic
    import os
    
    # Get API key from environment
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")
    
    client = anthropic.Anthropic(api_key=api_key)
    
    # Build messages
    messages = [{"role": "user", "content": prompt}]
    
    # Call API
    kwargs = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": messages,
    }
    
    if system:
        kwargs["system"] = system
    
    response = client.messages.create(**kwargs)
    
    # Extract text from response
    text = response.content[0].text
    
    return text


# Export step wrapper for llm_call
# The execution engine will intercept calls to llm_call and wrap them
def _create_llm_step(
    prompt: str,
    model: str,
    temperature: float,
    max_tokens: int,
    system: Optional[str],
) -> Step:
    """
    Create a step wrapper for an LLM call.
    
    This is used internally by the execution engine to treat llm_call
    as an effectful step.
    """
    def llm_func():
        return llm_call(
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            system=system,
        )
    
    # Give it a deterministic name based on inputs
    step_id = f"llm_call"
    
    return Step(llm_func, StepKind.EFFECTFUL, step_id=step_id)
