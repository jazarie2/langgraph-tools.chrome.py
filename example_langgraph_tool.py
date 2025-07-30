#!/usr/bin/env python3
"""
LangGraph Tools Example - Demonstrates best practices for building LangGraph applications.

This example shows how to:
1. Define proper state structures
2. Create custom tools with error handling
3. Build graph workflows with nodes and edges
4. Implement parallel tool execution
5. Handle interrupts and human-in-the-loop scenarios
6. Add comprehensive testing and validation

Follow the patterns shown here for robust LangGraph applications.
"""

import asyncio
import uuid
from datetime import datetime
from typing import Annotated, Any, Dict, List, TypedDict

# LangGraph and LangChain imports
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver


# ============================================================================
# STATE DEFINITIONS - Using TypedDict for type safety
# ============================================================================

class WorkflowState(TypedDict):
    """Main state structure for the workflow.
    
    Attributes:
        messages: Conversation history with proper message typing
        pending_tools: List of tools awaiting execution
        results: Mapping of tool IDs to execution results
        errors: Mapping of tool IDs to error messages
        user_input: Latest user input for processing
        validation_results: Results from state validation checks
        execution_metadata: Metadata about execution (timing, etc.)
    """
    messages: Annotated[list[BaseMessage], add_messages]
    pending_tools: list[dict[str, Any]]
    results: dict[str, Any]
    errors: dict[str, str]
    user_input: str
    validation_results: dict[str, bool]
    execution_metadata: dict[str, Any]


# ============================================================================
# CUSTOM TOOLS - Following best practices for tool implementation
# ============================================================================

@tool
async def search_tool(query: str) -> str:
    """Simulate a search tool with realistic behavior.
    
    Args:
        query: Search query string
        
    Returns:
        str: Formatted search results
        
    Raises:
        ValueError: If query is empty or invalid
    """
    try:
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        # Simulate API call delay
        await asyncio.sleep(0.5)
        
        # Simulate search results
        results = [
            f"Result 1 for '{query}': Relevant information found",
            f"Result 2 for '{query}': Additional context available",
            f"Result 3 for '{query}': Related documentation exists"
        ]
        
        return f"Search results for '{query}':\n" + "\n".join(results)
    
    except Exception as e:
        return f"Search error: {e!s}"


@tool
async def analysis_tool(data: str) -> str:
    """Analyze data and provide insights.
    
    Args:
        data: Data to analyze
        
    Returns:
        str: Analysis results
    """
    try:
        if not data:
            return "Error: No data provided for analysis"
        
        # Simulate analysis processing
        await asyncio.sleep(0.3)
        
        word_count = len(data.split())
        char_count = len(data)
        
        analysis = {
            "word_count": word_count,
            "character_count": char_count,
            "complexity": "high" if word_count > 50 else "medium" if word_count > 20 else "low",
            "timestamp": datetime.now().isoformat()
        }
        
        return f"Analysis complete: {analysis}"
    
    except Exception as e:
        return f"Analysis error: {e!s}"


@tool
def validation_tool(content: str) -> str:
    """Validate content according to specified criteria.
    
    Args:
        content: Content to validate
        
    Returns:
        str: Validation results
    """
    try:
        if not content:
            return "Validation failed: Empty content"
        
        checks = {
            "min_length": len(content) >= 10,
            "has_letters": any(c.isalpha() for c in content),
            "has_numbers": any(c.isdigit() for c in content),
            "safe_characters": all(c.isprintable() for c in content)
        }
        
        passed = sum(checks.values())
        total = len(checks)
        
        return f"Validation results: {passed}/{total} checks passed - {checks}"
    
    except Exception as e:
        return f"Validation error: {e!s}"


# ============================================================================
# NODE FUNCTIONS - Core processing logic
# ============================================================================

def input_processor_node(state: WorkflowState) -> dict:
    """Process user input and prepare for tool execution.
    
    Args:
        state: Current workflow state
        
    Returns:
        dict: State updates including prepared tools
    """
    try:
        user_input = state.get("user_input", "")
        if not user_input:
            return {"errors": {"input_processor": "No user input provided"}}
        
        # Determine which tools to use based on input
        pending_tools = []
        
        if "search" in user_input.lower():
            pending_tools.append({
                "id": f"search_{uuid.uuid4().hex[:8]}",
                "tool_name": "search_tool",
                "args": {"query": user_input}
            })
        
        if "analyze" in user_input.lower():
            pending_tools.append({
                "id": f"analysis_{uuid.uuid4().hex[:8]}",
                "tool_name": "analysis_tool", 
                "args": {"data": user_input}
            })
        
        if "validate" in user_input.lower():
            pending_tools.append({
                "id": f"validation_{uuid.uuid4().hex[:8]}",
                "tool_name": "validation_tool",
                "args": {"content": user_input}
            })
        
        return {
            "pending_tools": pending_tools,
            "execution_metadata": {
                "processing_time": datetime.now().isoformat(),
                "tools_prepared": len(pending_tools)
            }
        }
    
    except Exception as e:
        return {"errors": {"input_processor": str(e)}}


async def parallel_tool_executor_node(state: WorkflowState) -> dict:
    """Execute multiple tools in parallel for efficiency.
    
    Args:
        state: Current workflow state
        
    Returns:
        dict: State updates with tool execution results
    """
    try:
        pending_tools = state.get("pending_tools", [])
        if not pending_tools:
            return {"results": {}, "errors": {}}
        
        # Map tool names to actual tool functions
        available_tools = {
            "search_tool": search_tool,
            "analysis_tool": analysis_tool,
            "validation_tool": validation_tool
        }
        
        # Execute tools in parallel
        start_time = datetime.now()
        
        async def execute_single_tool(tool_call: dict) -> tuple[str, Any]:
            """Execute a single tool and return results."""
            tool_id = tool_call["id"]
            tool_name = tool_call["tool_name"]
            tool_args = tool_call["args"]
            
            try:
                tool_func = available_tools.get(tool_name)
                if not tool_func:
                    return tool_id, f"Error: Unknown tool '{tool_name}'"
                
                # Execute tool (handle both sync and async)
                if asyncio.iscoroutinefunction(tool_func.func):
                    result = await tool_func.ainvoke(list(tool_args.values())[0])
                else:
                    result = tool_func.invoke(list(tool_args.values())[0])
                
                return tool_id, result
            
            except Exception as e:
                return tool_id, f"Error: {e!s}"
        
        # Execute all tools concurrently
        tasks = [execute_single_tool(tool_call) for tool_call in pending_tools]
        execution_results = await asyncio.gather(*tasks)
        
        # Separate results and errors
        results = {}
        errors = {}
        
        for tool_id, result in execution_results:
            if isinstance(result, str) and result.startswith("Error:"):
                errors[tool_id] = result
            else:
                results[tool_id] = result
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "results": results,
            "errors": errors,
            "pending_tools": [],  # Clear pending tools
            "execution_metadata": {
                **state.get("execution_metadata", {}),
                "execution_time_seconds": execution_time,
                "tools_executed": len(pending_tools)
            }
        }
    
    except Exception as e:
        return {"errors": {"parallel_executor": str(e)}}


def validation_node(state: WorkflowState) -> dict:
    """Validate the current state and execution results.
    
    Args:
        state: Current workflow state
        
    Returns:
        dict: State updates with validation results
    """
    try:
        validations = {
            "has_user_input": bool(state.get("user_input")),
            "has_execution_metadata": bool(state.get("execution_metadata")),
            "results_present": bool(state.get("results")),
            "no_critical_errors": not any(
                "critical" in error.lower() 
                for error in state.get("errors", {}).values()
            ),
            "state_consistency": isinstance(state.get("results", {}), dict)
        }
        
        overall_valid = all(validations.values())
        
        return {
            "validation_results": {
                **validations,
                "overall_valid": overall_valid,
                "validation_timestamp": datetime.now().isoformat()
            }
        }
    
    except Exception as e:
        return {
            "validation_results": {"validation_error": str(e)},
            "errors": {"validation_node": str(e)}
        }


def response_formatter_node(state: WorkflowState) -> dict:
    """Format the final response based on execution results.
    
    Args:
        state: Current workflow state
        
    Returns:
        dict: State updates with formatted response
    """
    try:
        results = state.get("results", {})
        errors = state.get("errors", {})
        validation_results = state.get("validation_results", {})
        
        # Build response summary
        response_parts = []
        
        if results:
            response_parts.append("✅ **Execution Results:**")
            for tool_id, result in results.items():
                response_parts.append(f"- {tool_id}: {result}")
        
        if errors:
            response_parts.append("\n❌ **Errors Encountered:**")
            for tool_id, error in errors.items():
                response_parts.append(f"- {tool_id}: {error}")
        
        if validation_results:
            overall_valid = validation_results.get("overall_valid", False)
            status = "✅ Valid" if overall_valid else "⚠️ Issues Detected"
            response_parts.append(f"\n🔍 **Validation Status:** {status}")
        
        execution_metadata = state.get("execution_metadata", {})
        if execution_metadata:
            response_parts.append(f"\n📊 **Execution Info:**")
            for key, value in execution_metadata.items():
                response_parts.append(f"- {key}: {value}")
        
        formatted_response = "\n".join(response_parts)
        
        # Create final AI message
        final_message = AIMessage(content=formatted_response)
        
        return {
            "messages": [final_message],
            "execution_metadata": {
                **execution_metadata,
                "response_formatted": True,
                "completion_time": datetime.now().isoformat()
            }
        }
    
    except Exception as e:
        error_message = AIMessage(content=f"Error formatting response: {e}")
        return {
            "messages": [error_message],
            "errors": {"response_formatter": str(e)}
        }


# ============================================================================
# CONDITIONAL LOGIC - Graph routing decisions
# ============================================================================

def should_execute_tools(state: WorkflowState) -> str:
    """Determine if tools should be executed based on state.
    
    Args:
        state: Current workflow state
        
    Returns:
        str: Next node name
    """
    pending_tools = state.get("pending_tools", [])
    
    if pending_tools:
        return "parallel_executor"
    else:
        return "validator"


def should_continue_processing(state: WorkflowState) -> str:
    """Determine if processing should continue or end.
    
    Args:
        state: Current workflow state
        
    Returns:
        str: Next node name or END
    """
    validation_results = state.get("validation_results", {})
    
    if validation_results.get("overall_valid", False):
        return "response_formatter"
    else:
        # Could add retry logic here
        return "response_formatter"


# ============================================================================
# GRAPH CONSTRUCTION - Building the workflow
# ============================================================================

def create_langgraph_workflow() -> StateGraph:
    """Create and configure the LangGraph workflow.
    
    Returns:
        StateGraph: Configured workflow graph
    """
    # Initialize the graph with our state schema
    workflow = StateGraph(WorkflowState)
    
    # Add nodes
    workflow.add_node("input_processor", input_processor_node)
    workflow.add_node("parallel_executor", parallel_tool_executor_node)
    workflow.add_node("validator", validation_node)
    workflow.add_node("response_formatter", response_formatter_node)
    
    # Define the flow
    workflow.add_edge(START, "input_processor")
    
    # Conditional routing based on available tools
    workflow.add_conditional_edges(
        "input_processor",
        should_execute_tools,
        {
            "parallel_executor": "parallel_executor",
            "validator": "validator"
        }
    )
    
    workflow.add_edge("parallel_executor", "validator")
    
    # Conditional routing for validation results
    workflow.add_conditional_edges(
        "validator",
        should_continue_processing,
        {
            "response_formatter": "response_formatter"
        }
    )
    
    workflow.add_edge("response_formatter", END)
    
    return workflow


# ============================================================================
# EXAMPLE USAGE AND TESTING
# ============================================================================

async def run_example_workflow(user_input: str) -> dict:
    """Run the example workflow with given input.
    
    Args:
        user_input: User input to process
        
    Returns:
        dict: Final workflow state
    """
    # Create and compile the workflow
    workflow = create_langgraph_workflow()
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)
    
    # Configure execution
    config = {"configurable": {"thread_id": f"example_{uuid.uuid4().hex[:8]}"}}
    
    # Initial state
    initial_state = {
        "messages": [HumanMessage(content=user_input)],
        "pending_tools": [],
        "results": {},
        "errors": {},
        "user_input": user_input,
        "validation_results": {},
        "execution_metadata": {"start_time": datetime.now().isoformat()}
    }
    
    try:
        # Execute the workflow
        result = await app.ainvoke(initial_state, config=config)
        return result
    
    except Exception as e:
        print(f"Workflow execution error: {e}")
        return {"errors": {"workflow": str(e)}}


async def demonstrate_langgraph_tools():
    """Demonstrate various LangGraph tool patterns."""
    print("🚀 LangGraph Tools Demonstration")
    print("=" * 50)
    
    # Test cases demonstrating different scenarios
    test_cases = [
        "Please search for Python best practices",
        "Analyze this text and validate the results",
        "Search for machine learning tutorials and analyze the content",
        "Validate this simple text content",
        ""  # Edge case: empty input
    ]
    
    for i, test_input in enumerate(test_cases, 1):
        print(f"\n📝 Test Case {i}: '{test_input}'")
        print("-" * 30)
        
        result = await run_example_workflow(test_input)
        
        # Display results
        if "messages" in result and result["messages"]:
            final_message = result["messages"][-1]
            if hasattr(final_message, 'content'):
                print(final_message.content)
        
        # Show execution metadata
        metadata = result.get("execution_metadata", {})
        if metadata:
            print(f"\n⏱️ Execution took: {metadata.get('execution_time_seconds', 'N/A')} seconds")
            print(f"🔧 Tools executed: {metadata.get('tools_executed', 0)}")
        
        print("\n" + "="*50)


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    # Run the demonstration
    try:
        asyncio.run(demonstrate_langgraph_tools())
    except KeyboardInterrupt:
        print("\n👋 Demonstration interrupted by user")
    except Exception as e:
        print(f"❌ Demonstration failed: {e}")