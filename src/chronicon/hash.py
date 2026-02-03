"""
Hashing utilities for deterministic versioning of workflows and steps.

Workflows and steps are versioned by hashing their source code.
This enables replay divergence detection when code changes.
"""

import hashlib
import inspect
from typing import Callable, Any


def hash_source(func: Callable) -> str:
    """
    Hash the source code of a function for versioning.
    
    Returns a deterministic SHA-256 hash of the function's source code.
    This is used to version workflows and steps.
    
    Args:
        func: The function to hash
        
    Returns:
        Hex string of the SHA-256 hash (64 characters)
        
    Raises:
        ValueError: If source code cannot be retrieved
    """
    try:
        source = inspect.getsource(func)
        # Normalize whitespace to avoid spurious changes
        normalized = source.strip()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    except (OSError, TypeError) as e:
        raise ValueError(f"Cannot retrieve source for {func.__name__}: {e}") from e


def hash_value(value: Any) -> str:
    """
    Hash a serialized value for content-based identification.
    
    Used to hash step inputs/outputs for cache keys and divergence detection.
    
    Args:
        value: Any JSON-serializable value
        
    Returns:
        Hex string of the SHA-256 hash
    """
    import json
    
    # Serialize with sorted keys for determinism
    serialized = json.dumps(value, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def hash_step_invocation(
    step_id: str,
    step_version: str,
    inputs: dict[str, Any]
) -> str:
    """
    Hash a specific step invocation for deduplication and caching.
    
    Combines step identity (id + version) with inputs to create
    a unique hash for this specific execution.
    
    Args:
        step_id: Unique identifier for the step
        step_version: Version hash of the step code
        inputs: Dictionary of input parameters
        
    Returns:
        Hex string of the SHA-256 hash
    """
    import json
    
    data = {
        "step_id": step_id,
        "step_version": step_version,
        "inputs": inputs,
    }
    serialized = json.dumps(data, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
