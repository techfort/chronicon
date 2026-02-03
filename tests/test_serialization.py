"""
Tests for serialization utilities.
"""

import pytest
from datetime import datetime
from pathlib import Path

from chronicon.serialization import serialize, deserialize, is_serializable


def test_serialize_basic_types():
    """Test serializing basic Python types."""
    
    # Primitives
    assert deserialize(serialize(42)) == 42
    assert deserialize(serialize(3.14)) == 3.14
    assert deserialize(serialize("hello")) == "hello"
    assert deserialize(serialize(True)) == True
    assert deserialize(serialize(None)) == None
    
    # Collections
    assert deserialize(serialize([1, 2, 3])) == [1, 2, 3]
    assert deserialize(serialize({"a": 1, "b": 2})) == {"a": 1, "b": 2}


def test_serialize_datetime():
    """Test serializing datetime objects."""
    
    dt = datetime(2024, 1, 15, 12, 30, 45)
    serialized = serialize(dt)
    deserialized = deserialize(serialized)
    
    assert deserialized == dt


def test_serialize_path():
    """Test serializing Path objects."""
    
    p = Path("/home/user/file.txt")
    serialized = serialize(p)
    deserialized = deserialize(serialized)
    
    assert deserialized == p


def test_serialize_set():
    """Test serializing sets."""
    
    s = {1, 2, 3}
    serialized = serialize(s)
    deserialized = deserialize(serialized)
    
    assert deserialized == s


def test_serialize_nested():
    """Test serializing nested structures."""
    
    data = {
        "name": "test",
        "count": 42,
        "items": [1, 2, 3],
        "metadata": {
            "created": datetime(2024, 1, 1),
            "path": Path("/tmp/test"),
        }
    }
    
    serialized = serialize(data)
    deserialized = deserialize(serialized)
    
    assert deserialized == data


def test_is_serializable():
    """Test checking if values are serializable."""
    
    # Serializable
    assert is_serializable(42)
    assert is_serializable("hello")
    assert is_serializable([1, 2, 3])
    assert is_serializable({"a": 1})
    assert is_serializable(datetime.now())
    assert is_serializable(Path("/tmp"))
    
    # Not serializable
    assert not is_serializable(lambda x: x)
    assert not is_serializable(open)


def test_serialize_deterministic():
    """Test that serialization is deterministic."""
    
    data = {"b": 2, "a": 1, "c": 3}
    
    # Multiple serializations should be identical
    s1 = serialize(data)
    s2 = serialize(data)
    assert s1 == s2
    
    # Order doesn't matter for dicts
    data2 = {"c": 3, "a": 1, "b": 2}
    s3 = serialize(data2)
    assert s1 == s3
