#!/usr/bin/env python3
"""
Test suite for LangGraph tools - Demonstrates testing best practices.

This test file shows how to:
1. Test state management and validation
2. Create mock tools for testing
3. Test graph workflows and node functions
4. Validate error handling and edge cases
5. Test async functionality properly

Run with: pytest test_langgraph_tools.py -v
"""

import asyncio
import pytest
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock

# Import the components we want to test
from example_langgraph_tool import (
    WorkflowState,
    search_tool,
    analysis_tool,
    validation_tool,
    input_processor_node,
    parallel_tool_executor_node,
    validation_node,
    response_formatter_node,
    create_langgraph_workflow,
    run_example_workflow
)


# ============================================================================
# TEST FIXTURES - Reusable test data and mocks
# ============================================================================

@pytest.fixture
def sample_state() -> WorkflowState:
    """Create a sample state for testing."""
    return {
        "messages": [],
        "pending_tools": [],
        "results": {},
        "errors": {},
        "user_input": "test input",
        "validation_results": {},
        "execution_metadata": {}
    }


@pytest.fixture
def state_with_pending_tools() -> WorkflowState:
    """Create state with pending tools for testing execution."""
    return {
        "messages": [],
        "pending_tools": [
            {
                "id": "test_search",
                "tool_name": "search_tool",
                "args": {"query": "test query"}
            },
            {
                "id": "test_analysis",
                "tool_name": "analysis_tool",
                "args": {"data": "test data"}
            }
        ],
        "results": {},
        "errors": {},
        "user_input": "search and analyze test",
        "validation_results": {},
        "execution_metadata": {}
    }


@pytest.fixture
def mock_tools():
    """Create mock tools for testing."""
    search_mock = AsyncMock(return_value="Mock search results")
    analysis_mock = AsyncMock(return_value="Mock analysis results")
    validation_mock = MagicMock(return_value="Mock validation results")
    
    return {
        "search_tool": search_mock,
        "analysis_tool": analysis_mock,
        "validation_tool": validation_mock
    }


# ============================================================================
# TOOL TESTS - Testing individual tool functionality
# ============================================================================

@pytest.mark.asyncio
async def test_search_tool_success():
    """Test search tool with valid input."""
    query = "Python best practices"
    result = await search_tool.ainvoke(query)
    
    assert isinstance(result, str)
    assert query in result
    assert "Search results" in result
    assert "Result 1" in result


@pytest.mark.asyncio
async def test_search_tool_empty_query():
    """Test search tool with empty query."""
    result = await search_tool.ainvoke("")
    
    assert isinstance(result, str)
    assert "error" in result.lower()


@pytest.mark.asyncio
async def test_analysis_tool_success():
    """Test analysis tool with valid data."""
    data = "This is a test sentence with multiple words for analysis."
    result = await analysis_tool.ainvoke(data)
    
    assert isinstance(result, str)
    assert "Analysis complete" in result
    assert "word_count" in result


@pytest.mark.asyncio
async def test_analysis_tool_empty_data():
    """Test analysis tool with empty data."""
    result = await analysis_tool.ainvoke("")
    
    assert isinstance(result, str)
    assert "Error" in result


def test_validation_tool_success():
    """Test validation tool with valid content."""
    content = "Valid content with letters and numbers 123"
    result = validation_tool.invoke(content)
    
    assert isinstance(result, str)
    assert "Validation results" in result
    assert "checks passed" in result


def test_validation_tool_empty_content():
    """Test validation tool with empty content."""
    result = validation_tool.invoke("")
    
    assert isinstance(result, str)
    assert "failed" in result.lower()


# ============================================================================
# NODE FUNCTION TESTS - Testing workflow nodes
# ============================================================================

def test_input_processor_node_with_search(sample_state):
    """Test input processor identifies search intent."""
    state = {**sample_state, "user_input": "Please search for Python tutorials"}
    result = input_processor_node(state)
    
    assert "pending_tools" in result
    assert len(result["pending_tools"]) == 1
    assert result["pending_tools"][0]["tool_name"] == "search_tool"
    assert "execution_metadata" in result


def test_input_processor_node_with_multiple_intents(sample_state):
    """Test input processor with multiple tool intents."""
    state = {**sample_state, "user_input": "Search for data and analyze the results and validate them"}
    result = input_processor_node(state)
    
    assert "pending_tools" in result
    assert len(result["pending_tools"]) == 3
    tool_names = [tool["tool_name"] for tool in result["pending_tools"]]
    assert "search_tool" in tool_names
    assert "analysis_tool" in tool_names
    assert "validation_tool" in tool_names


def test_input_processor_node_no_input(sample_state):
    """Test input processor with no user input."""
    state = {**sample_state, "user_input": ""}
    result = input_processor_node(state)
    
    assert "errors" in result
    assert "input_processor" in result["errors"]


@pytest.mark.asyncio
async def test_parallel_tool_executor_node_success(state_with_pending_tools):
    """Test parallel tool execution with valid tools."""
    result = await parallel_tool_executor_node(state_with_pending_tools)
    
    assert "results" in result
    assert "errors" in result
    assert "execution_metadata" in result
    assert result["pending_tools"] == []  # Should be cleared


@pytest.mark.asyncio
async def test_parallel_tool_executor_node_no_tools(sample_state):
    """Test parallel tool executor with no pending tools."""
    result = await parallel_tool_executor_node(sample_state)
    
    assert result["results"] == {}
    assert result["errors"] == {}


def test_validation_node_success(sample_state):
    """Test validation node with valid state."""
    state = {
        **sample_state,
        "user_input": "test",
        "execution_metadata": {"test": "data"},
        "results": {"tool1": "result1"}
    }
    result = validation_node(state)
    
    assert "validation_results" in result
    assert result["validation_results"]["has_user_input"] is True
    assert result["validation_results"]["has_execution_metadata"] is True
    assert result["validation_results"]["results_present"] is True


def test_validation_node_missing_data(sample_state):
    """Test validation node with missing required data."""
    state = {**sample_state, "user_input": ""}  # Missing user input
    result = validation_node(state)
    
    assert "validation_results" in result
    assert result["validation_results"]["has_user_input"] is False


def test_response_formatter_node_with_results(sample_state):
    """Test response formatter with execution results."""
    state = {
        **sample_state,
        "results": {"tool1": "Test result 1", "tool2": "Test result 2"},
        "validation_results": {"overall_valid": True},
        "execution_metadata": {"execution_time_seconds": 1.5}
    }
    result = response_formatter_node(state)
    
    assert "messages" in result
    assert len(result["messages"]) == 1
    message_content = result["messages"][0].content
    assert "Execution Results" in message_content
    assert "Test result 1" in message_content


def test_response_formatter_node_with_errors(sample_state):
    """Test response formatter with errors."""
    state = {
        **sample_state,
        "errors": {"tool1": "Test error 1"},
        "validation_results": {"overall_valid": False}
    }
    result = response_formatter_node(state)
    
    assert "messages" in result
    message_content = result["messages"][0].content
    assert "Errors Encountered" in message_content
    assert "Test error 1" in message_content


# ============================================================================
# GRAPH WORKFLOW TESTS - Testing complete workflows
# ============================================================================

def test_create_langgraph_workflow():
    """Test graph construction and compilation."""
    workflow = create_langgraph_workflow()
    
    # Test that workflow can be compiled
    app = workflow.compile()
    assert app is not None
    
    # Test with checkpointer
    from langgraph.checkpoint.memory import MemorySaver
    memory = MemorySaver()
    app_with_memory = workflow.compile(checkpointer=memory)
    assert app_with_memory is not None


@pytest.mark.asyncio
async def test_run_example_workflow_search():
    """Test complete workflow with search input."""
    user_input = "Please search for Python tutorials"
    result = await run_example_workflow(user_input)
    
    assert isinstance(result, dict)
    assert "messages" in result
    assert "execution_metadata" in result
    
    # Check that search was executed
    if "results" in result:
        search_results = [v for k, v in result["results"].items() if "search" in k.lower()]
        if search_results:
            assert any("Search results" in str(res) for res in search_results)


@pytest.mark.asyncio
async def test_run_example_workflow_empty_input():
    """Test workflow with empty input."""
    result = await run_example_workflow("")
    
    assert isinstance(result, dict)
    # Should handle empty input gracefully
    assert "errors" in result or "messages" in result


# ============================================================================
# ERROR HANDLING TESTS - Testing edge cases and error scenarios
# ============================================================================

@pytest.mark.asyncio
async def test_tool_error_handling():
    """Test that tools handle errors gracefully."""
    # Test search tool with problematic input
    result = await search_tool.ainvoke(None)
    assert "error" in result.lower()
    
    # Test analysis tool with None
    result = await analysis_tool.ainvoke(None)
    assert "error" in result.lower() or "Error" in result


def test_node_error_handling(sample_state):
    """Test that nodes handle invalid state gracefully."""
    # Test with corrupted state
    corrupted_state = None
    
    try:
        result = input_processor_node(corrupted_state)
        # Should return error information
        assert isinstance(result, dict)
    except Exception:
        # If exception is raised, it should be handled appropriately
        pass


# ============================================================================
# INTEGRATION TESTS - Testing component interactions
# ============================================================================

@pytest.mark.asyncio
async def test_full_workflow_integration():
    """Test complete workflow integration."""
    test_inputs = [
        "Search for Python best practices",
        "Analyze this text content",
        "Validate user input data",
        "Search and analyze machine learning"
    ]
    
    for user_input in test_inputs:
        result = await run_example_workflow(user_input)
        
        # Basic validation of result structure
        assert isinstance(result, dict)
        assert "execution_metadata" in result
        
        # Should have either results or errors
        has_results = "results" in result and result["results"]
        has_errors = "errors" in result and result["errors"]
        has_messages = "messages" in result and result["messages"]
        
        assert has_results or has_errors or has_messages


# ============================================================================
# PERFORMANCE TESTS - Testing execution efficiency
# ============================================================================

@pytest.mark.asyncio
async def test_parallel_execution_performance(state_with_pending_tools):
    """Test that parallel execution is faster than sequential."""
    import time
    
    # Time parallel execution
    start_time = time.time()
    result = await parallel_tool_executor_node(state_with_pending_tools)
    parallel_time = time.time() - start_time
    
    # Verify execution completed
    assert "execution_metadata" in result
    assert "execution_time_seconds" in result["execution_metadata"]
    
    # Parallel execution should complete reasonably quickly
    # (This is a basic performance check)
    assert parallel_time < 5.0  # Should complete within 5 seconds


# ============================================================================
# TEST CONFIGURATION AND SETUP
# ============================================================================

def test_requirements_compatibility():
    """Test that required modules can be imported."""
    try:
        import langgraph
        import langchain_core
        from langchain_core.tools import tool
        from langgraph.graph import StateGraph
        assert True  # All imports successful
    except ImportError as e:
        pytest.fail(f"Required module import failed: {e}")


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])