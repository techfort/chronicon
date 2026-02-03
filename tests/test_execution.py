"""
Tests for execution engine.
"""

import pytest
import tempfile
import os
from pathlib import Path

from chronicon import workflow, execute, llm_call
from chronicon.log import ExecutionLog


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        yield str(db_path)


def test_execute_simple_workflow(temp_db):
    """Test executing a simple workflow without LLM calls."""
    
    @workflow
    def add_numbers(x: int, y: int) -> int:
        return x + y
    
    log = ExecutionLog(temp_db)
    result = execute(add_numbers, x=2, y=3, log=log)
    
    assert result.success
    assert result.output == 5
    assert result.error is None
    assert len(result.execution_id) > 0
    
    # Check it was logged
    exec_record = log.get_execution(result.execution_id)
    assert exec_record is not None
    assert exec_record.workflow_id == "add_numbers"
    assert exec_record.status == "completed"


def test_execute_with_error(temp_db):
    """Test execution with error."""
    
    @workflow
    def failing_workflow(x: int) -> int:
        raise ValueError("Intentional error")
    
    log = ExecutionLog(temp_db)
    result = execute(failing_workflow, x=5, log=log)
    
    assert not result.success
    assert result.output is None
    assert "ValueError: Intentional error" in result.error
    
    # Check it was logged as failed
    exec_record = log.get_execution(result.execution_id)
    assert exec_record.status == "failed"


def test_execute_rejects_non_serializable_input(temp_db):
    """Test that non-serializable inputs are rejected."""
    
    @workflow
    def test_workflow(x) -> int:
        return 42
    
    log = ExecutionLog(temp_db)
    
    # Lambda is not serializable
    with pytest.raises(ValueError, match="serializable"):
        execute(test_workflow, x=lambda: 1, log=log)


def test_execute_rejects_non_serializable_output(temp_db):
    """Test that non-serializable outputs are rejected."""
    
    @workflow
    def test_workflow(x: int):
        return lambda: x  # Not serializable
    
    log = ExecutionLog(temp_db)
    result = execute(test_workflow, x=5, log=log)
    
    assert not result.success
    assert "serializable" in result.error


@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="Requires ANTHROPIC_API_KEY environment variable"
)
def test_execute_with_llm_call(temp_db):
    """Test execution with actual LLM call (requires API key)."""
    
    @workflow
    def llm_workflow(prompt: str) -> str:
        response = llm_call(
            prompt=prompt,
            model="claude-3-5-sonnet-20241022",
            temperature=0.0,
            max_tokens=50,
        )
        return response
    
    log = ExecutionLog(temp_db)
    result = execute(llm_workflow, prompt="Say 'test' and nothing else.", log=log)
    
    if result.success:
        assert result.output is not None
        assert len(result.steps) == 1
        assert result.steps[0].step_id == "llm_call"
        assert result.steps[0].llm_model == "claude-3-5-sonnet-20241022"
