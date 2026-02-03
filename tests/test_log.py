"""
Tests for execution log (SQLite persistence).
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from chronicon.log import ExecutionLog
from chronicon.step import StepInvocation, StepKind


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        yield str(db_path)


def test_create_database(temp_db):
    """Test creating a new database."""
    log = ExecutionLog(temp_db)
    assert Path(temp_db).exists()
    log.close()


def test_start_execution(temp_db):
    """Test starting a new execution."""
    log = ExecutionLog(temp_db)
    
    execution_id = log.start_execution(
        workflow_id="test_workflow",
        workflow_version="abc123",
        inputs={"x": 1, "y": 2},
    )
    
    assert len(execution_id) > 0
    
    # Verify it was saved
    exec_record = log.get_execution(execution_id)
    assert exec_record is not None
    assert exec_record.workflow_id == "test_workflow"
    assert exec_record.status == "running"
    assert exec_record.inputs == {"x": 1, "y": 2}


def test_complete_execution(temp_db):
    """Test completing an execution."""
    log = ExecutionLog(temp_db)
    
    execution_id = log.start_execution(
        workflow_id="test_workflow",
        workflow_version="abc123",
        inputs={"x": 1},
    )
    
    log.complete_execution(execution_id, output=42)
    
    exec_record = log.get_execution(execution_id)
    assert exec_record.status == "completed"
    assert exec_record.output == 42
    assert exec_record.completed_at is not None


def test_complete_execution_with_error(temp_db):
    """Test completing an execution with error."""
    log = ExecutionLog(temp_db)
    
    execution_id = log.start_execution(
        workflow_id="test_workflow",
        workflow_version="abc123",
        inputs={"x": 1},
    )
    
    log.complete_execution(execution_id, error="Something went wrong")
    
    exec_record = log.get_execution(execution_id)
    assert exec_record.status == "failed"
    assert exec_record.error == "Something went wrong"
    assert exec_record.output is None


def test_log_step(temp_db):
    """Test logging step invocations."""
    log = ExecutionLog(temp_db)
    
    execution_id = log.start_execution(
        workflow_id="test_workflow",
        workflow_version="abc123",
        inputs={},
    )
    
    invocation = StepInvocation(
        step_id="test_step",
        step_version="v1",
        kind=StepKind.PURE,
        inputs={"x": 1},
        output=2,
    )
    
    step_record_id = log.log_step(execution_id, step_index=0, invocation=invocation)
    assert step_record_id > 0
    
    # Verify it was saved
    steps = log.get_steps(execution_id)
    assert len(steps) == 1
    assert steps[0].step_id == "test_step"
    assert steps[0].inputs == {"x": 1}
    assert steps[0].output == 2


def test_log_llm_call(temp_db):
    """Test logging LLM call metadata."""
    log = ExecutionLog(temp_db)
    
    execution_id = log.start_execution(
        workflow_id="test_workflow",
        workflow_version="abc123",
        inputs={},
    )
    
    invocation = StepInvocation(
        step_id="llm_call",
        step_version="builtin",
        kind=StepKind.EFFECTFUL,
        inputs={"prompt": "test"},
        output="response",
        llm_model="claude-3-5-sonnet-20241022",
        llm_prompt="test",
        llm_temperature=0.7,
        llm_max_tokens=100,
        llm_response_raw="response",
    )
    
    log.log_step(execution_id, step_index=0, invocation=invocation)
    
    # Verify LLM metadata was saved
    steps = log.get_steps(execution_id)
    assert len(steps) == 1
    assert steps[0].llm_model == "claude-3-5-sonnet-20241022"
    assert steps[0].llm_prompt == "test"
    assert steps[0].llm_temperature == 0.7


def test_get_steps_ordered(temp_db):
    """Test that steps are returned in order."""
    log = ExecutionLog(temp_db)
    
    execution_id = log.start_execution(
        workflow_id="test_workflow",
        workflow_version="abc123",
        inputs={},
    )
    
    # Log multiple steps
    for i in range(3):
        invocation = StepInvocation(
            step_id=f"step_{i}",
            step_version="v1",
            kind=StepKind.PURE,
            inputs={"i": i},
            output=i * 2,
        )
        log.log_step(execution_id, step_index=i, invocation=invocation)
    
    # Verify order
    steps = log.get_steps(execution_id)
    assert len(steps) == 3
    assert steps[0].step_id == "step_0"
    assert steps[1].step_id == "step_1"
    assert steps[2].step_id == "step_2"
