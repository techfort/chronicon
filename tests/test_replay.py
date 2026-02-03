"""
Tests for replay engine.
"""

import pytest
import tempfile
from pathlib import Path

from chronicon import workflow, execute, replay
from chronicon.log import ExecutionLog


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        yield str(db_path)


def test_replay_simple_workflow(temp_db):
    """Test replaying a simple workflow."""
    
    @workflow
    def simple(x: int, y: int) -> int:
        return x + y
    
    log = ExecutionLog(temp_db)
    
    # Execute
    result = execute(simple, x=2, y=3, log=log)
    assert result.success
    
    # Replay
    replay_result = replay(simple, execution_id=result.execution_id, log=log)
    
    assert replay_result.success
    assert replay_result.output == result.output
    assert len(replay_result.divergences) == 0


def test_replay_detects_code_change(temp_db):
    """Test that replay detects when code has changed."""
    
    @workflow
    def version_1(x: int) -> int:
        return x + 1
    
    log = ExecutionLog(temp_db)
    
    # Execute original
    result = execute(version_1, x=5, log=log)
    assert result.output == 6
    
    # Change implementation
    @workflow
    def version_1(x: int) -> int:
        return x + 2  # Changed!
    
    # Replay should detect divergence
    replay_result = replay(
        version_1,
        execution_id=result.execution_id,
        log=log,
        allow_divergence=True,
    )
    
    assert len(replay_result.divergences) > 0
    assert any(
        "version" in d.message.lower()
        for d in replay_result.divergences
    )


def test_replay_nonexistent_execution(temp_db):
    """Test replaying a non-existent execution."""
    
    @workflow
    def test_workflow(x: int) -> int:
        return x
    
    log = ExecutionLog(temp_db)
    
    with pytest.raises(ValueError, match="not found"):
        replay(test_workflow, execution_id="nonexistent", log=log)


def test_replay_wrong_workflow(temp_db):
    """Test replaying with wrong workflow."""
    
    @workflow
    def workflow_a(x: int) -> int:
        return x + 1
    
    @workflow
    def workflow_b(x: int) -> int:
        return x + 2
    
    log = ExecutionLog(temp_db)
    
    # Execute workflow_a
    result = execute(workflow_a, x=5, log=log)
    
    # Try to replay with workflow_b
    with pytest.raises(ValueError, match="Workflow ID mismatch"):
        replay(workflow_b, execution_id=result.execution_id, log=log)
