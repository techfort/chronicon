"""
Serialization utilities for step inputs/outputs.

All data flowing through workflows must be serializable to enable:
- Execution logging
- Replay from logs
- Testing against past executions

Uses JSON with type preservation where possible.
"""

import json
from typing import Any
from datetime import datetime
from pathlib import Path


class ChronicleEncoder(json.JSONEncoder):
    """
    JSON encoder with support for common Python types.
    
    Handles:
    - datetime -> ISO format string
    - Path -> string
    - bytes -> base64 string
    - set -> list
    
    Raises TypeError for non-serializable types (by design).
    """
    
    def default(self, obj: Any) -> Any:
        if isinstance(obj, datetime):
            return {"__type__": "datetime", "value": obj.isoformat()}
        elif isinstance(obj, Path):
            return {"__type__": "path", "value": str(obj)}
        elif isinstance(obj, bytes):
            import base64
            return {"__type__": "bytes", "value": base64.b64encode(obj).decode("ascii")}
        elif isinstance(obj, set):
            return {"__type__": "set", "value": list(obj)}
        return super().default(obj)


def _decode_object(dct: dict) -> Any:
    """Decode custom types from JSON."""
    if "__type__" not in dct:
        return dct
        
    type_name = dct["__type__"]
    value = dct["value"]
    
    if type_name == "datetime":
        return datetime.fromisoformat(value)
    elif type_name == "path":
        return Path(value)
    elif type_name == "bytes":
        import base64
        return base64.b64decode(value.encode("ascii"))
    elif type_name == "set":
        return set(value)
    
    return dct


def serialize(value: Any) -> str:
    """
    Serialize a value to JSON string.
    
    Args:
        value: Any serializable Python value
        
    Returns:
        JSON string
        
    Raises:
        TypeError: If value contains non-serializable types
    """
    return json.dumps(value, cls=ChronicleEncoder, sort_keys=True, ensure_ascii=True)


def deserialize(data: str) -> Any:
    """
    Deserialize a JSON string to Python value.
    
    Args:
        data: JSON string
        
    Returns:
        Deserialized Python value
    """
    return json.loads(data, object_hook=_decode_object)


def is_serializable(value: Any) -> bool:
    """
    Check if a value can be serialized.
    
    Args:
        value: Any Python value
        
    Returns:
        True if serializable, False otherwise
    """
    try:
        serialize(value)
        return True
    except (TypeError, ValueError):
        return False
