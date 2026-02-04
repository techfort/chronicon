"""
Test multi-provider execution.
"""

import pytest
from chronicon import workflow, execute, create_llm_call


def test_execute_with_multiple_providers(temp_db):
    """Test execution with multiple providers."""
    from chronicon.log import ExecutionLog
    
    # Create mock providers
    calls_made = []
    
    def mock_provider_a(prompt, **kwargs):
        calls_made.append(("a", prompt))
        return "Response from A"
    
    def mock_provider_b(prompt, **kwargs):
        calls_made.append(("b", prompt))
        return "Response from B"
    
    @workflow
    def multi_provider_workflow(x: str) -> dict:
        from chronicon import llm_call
        
        # Call provider A
        result_a = llm_call(f"Task A: {x}", provider="a")
        
        # Call provider B
        result_b = llm_call(f"Task B: {x}", provider="b")
        
        return {"a": result_a, "b": result_b}
    
    log = ExecutionLog(temp_db)
    providers = {"a": mock_provider_a, "b": mock_provider_b}
    
    result = execute(multi_provider_workflow, x="test", log=log, providers=providers)
    
    assert result.success
    assert result.output["a"] == "Response from A"
    assert result.output["b"] == "Response from B"
    
    # Verify both providers were called
    assert len(calls_made) == 2
    assert calls_made[0][0] == "a"
    assert calls_made[1][0] == "b"


def test_execute_with_default_provider(temp_db):
    """Test that default provider is used when no provider specified."""
    from chronicon.log import ExecutionLog
    
    calls_made = []
    
    def mock_default(prompt, **kwargs):
        calls_made.append(prompt)
        return "Default response"
    
    def mock_other(prompt, **kwargs):
        return "Other response"
    
    @workflow
    def mixed_workflow() -> dict:
        from chronicon import llm_call
        
        # Use default (no provider specified)
        result1 = llm_call("Task 1")
        
        # Use specific provider
        result2 = llm_call("Task 2", provider="other")
        
        return {"default": result1, "other": result2}
    
    log = ExecutionLog(temp_db)
    providers = {"default": mock_default, "other": mock_other}
    
    result = execute(mixed_workflow, log=log, providers=providers)
    
    assert result.success
    assert result.output["default"] == "Default response"
    assert result.output["other"] == "Other response"
    assert "Task 1" in calls_made


def test_execute_with_unknown_provider_raises_error(temp_db):
    """Test that unknown provider raises error."""
    from chronicon.log import ExecutionLog
    
    def mock_provider(prompt, **kwargs):
        return "Response"
    
    @workflow
    def bad_workflow() -> str:
        from chronicon import llm_call
        return llm_call("Test", provider="unknown")
    
    log = ExecutionLog(temp_db)
    providers = {"known": mock_provider}
    
    result = execute(bad_workflow, log=log, providers=providers)
    
    assert not result.success
    assert "Unknown provider" in result.error
    assert "unknown" in result.error


def test_execute_with_single_llm_call_still_works(temp_db):
    """Test backward compatibility with single llm_call parameter."""
    from chronicon.log import ExecutionLog
    
    def mock_llm_call(prompt, **kwargs):
        return "Single provider response"
    
    @workflow
    def simple_workflow() -> str:
        from chronicon import llm_call
        return llm_call("Test")
    
    log = ExecutionLog(temp_db)
    
    # Old style: single llm_call parameter
    result = execute(simple_workflow, log=log, llm_call=mock_llm_call)
    
    assert result.success
    assert result.output == "Single provider response"


def test_providers_dict_takes_precedence_over_llm_call(temp_db):
    """Test that providers dict takes precedence over llm_call parameter."""
    from chronicon.log import ExecutionLog
    
    def single_provider(prompt, **kwargs):
        return "Single"
    
    def dict_provider(prompt, **kwargs):
        return "From dict"
    
    @workflow
    def workflow_test() -> str:
        from chronicon import llm_call
        return llm_call("Test")
    
    log = ExecutionLog(temp_db)
    
    # Both provided - providers should win
    result = execute(
        workflow_test,
        log=log,
        llm_call=single_provider,
        providers={"default": dict_provider}
    )
    
    assert result.success
    assert result.output == "From dict"


@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary database."""
    db_path = tmp_path / "test.db"
    return str(db_path)
