"""
Tests for workflow decorator and Workflow class.
"""

import pytest
from chronicon.workflow import workflow, Workflow


def test_workflow_decorator():
    """Test basic workflow decorator."""
    
    @workflow
    def simple_workflow(x: int, y: int) -> int:
        return x + y
    
    assert isinstance(simple_workflow, Workflow)
    assert simple_workflow.workflow_id == "simple_workflow"
    assert len(simple_workflow.version) == 64  # SHA-256 hex
    
    # Should be callable
    result = simple_workflow(2, 3)
    assert result == 5


def test_workflow_with_id():
    """Test workflow with custom ID."""
    
    @workflow(workflow_id="custom_id")
    def my_workflow(x: int) -> int:
        return x * 2
    
    assert my_workflow.workflow_id == "custom_id"


def test_workflow_rejects_varargs():
    """Test that workflow rejects *args and **kwargs."""
    
    with pytest.raises(ValueError, match="cannot use"):
        @workflow
        def bad_workflow(*args, **kwargs):
            pass


def test_workflow_version_changes_with_code():
    """Test that version hash changes when code changes."""
    
    @workflow
    def version_test_1(x: int) -> int:
        return x + 1
    
    version_1 = version_test_1.version
    
    @workflow
    def version_test_1(x: int) -> int:
        return x + 2  # Different implementation
    
    version_2 = version_test_1.version
    
    assert version_1 != version_2


def test_workflow_metadata():
    """Test workflow metadata."""
    
    @workflow
    def metadata_test(x: int, y: str) -> dict:
        """Test docstring."""
        return {"x": x, "y": y}
    
    meta = metadata_test.metadata()
    assert meta.workflow_id == "metadata_test"
    assert meta.version == metadata_test.version
    assert len(meta.signature.parameters) == 2
