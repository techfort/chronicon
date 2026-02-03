"""
Tests for hashing utilities.
"""

import pytest
from chronicon.hash import hash_source, hash_value, hash_step_invocation


def test_hash_source():
    """Test hashing function source code."""
    
    def func1():
        return 42
    
    # Hash should be deterministic
    hash1 = hash_source(func1)
    hash2 = hash_source(func1)
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 hex


def test_hash_source_changes_with_code():
    """Test that hash changes when code changes."""
    
    def func_v1():
        return 1
    
    def func_v2():
        return 2
    
    hash1 = hash_source(func_v1)
    hash2 = hash_source(func_v2)
    assert hash1 != hash2


def test_hash_value():
    """Test hashing values."""
    
    # Same values should have same hash
    hash1 = hash_value({"a": 1, "b": 2})
    hash2 = hash_value({"b": 2, "a": 1})  # Different order
    assert hash1 == hash2
    
    # Different values should have different hash
    hash3 = hash_value({"a": 1, "b": 3})
    assert hash1 != hash3


def test_hash_step_invocation():
    """Test hashing step invocations."""
    
    hash1 = hash_step_invocation(
        step_id="test_step",
        step_version="v1",
        inputs={"x": 1, "y": 2}
    )
    
    # Same invocation should have same hash
    hash2 = hash_step_invocation(
        step_id="test_step",
        step_version="v1",
        inputs={"y": 2, "x": 1}  # Different order
    )
    assert hash1 == hash2
    
    # Different inputs should have different hash
    hash3 = hash_step_invocation(
        step_id="test_step",
        step_version="v1",
        inputs={"x": 1, "y": 3}
    )
    assert hash1 != hash3
