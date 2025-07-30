# LangGraph Tools for Python

This repository contains comprehensive rules and examples for building robust LangGraph tools in Python. It demonstrates best practices, patterns, and architectural decisions for creating stateful, multi-actor applications with Large Language Models.

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- pip or conda for package management

### Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd langgraph-tools.chrome.py
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the example:
```bash
python example_langgraph_tool.py
```

## 📋 Cursor Rules

The `.cursorrules` file contains comprehensive guidelines for writing LangGraph tools, including:

### Core Principles
- **State Management**: Type-safe state definitions using TypedDict
- **Tool Implementation**: Robust error handling and consistent interfaces
- **Graph Construction**: Clear workflow definitions with proper checkpointing
- **Node Functions**: Single-responsibility functions with proper state handling

### Best Practices
- **Error Handling**: Graceful degradation and comprehensive error reporting
- **Performance**: Async/await patterns and parallel execution
- **Testing**: Mock tools and state validation
- **Security**: Input sanitization and credential management

### Code Structure
```
project/
├── tools/           # Custom tool implementations
├── graphs/          # Graph definitions and workflows
├── state/           # State type definitions
├── nodes/           # Node function implementations
├── tests/           # Test suites
└── config/          # Configuration management
```

## 🛠️ Example Implementation

The `example_langgraph_tool.py` demonstrates:

1. **State Definition**: Type-safe state structure with proper annotations
2. **Custom Tools**: Search, analysis, and validation tools with error handling
3. **Graph Workflow**: Multi-node processing pipeline with conditional routing
4. **Parallel Execution**: Concurrent tool execution for performance
5. **Validation**: State validation and result verification
6. **Response Formatting**: Structured output generation

### Key Features

#### State Management
```python
class WorkflowState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    pending_tools: list[dict[str, Any]]
    results: dict[str, Any]
    errors: dict[str, str]
    # ... additional fields
```

#### Tool Implementation
```python
@tool
async def search_tool(query: str) -> str:
    """Simulate a search tool with realistic behavior."""
    try:
        # Tool logic with proper error handling
        return f"Search results for '{query}'"
    except Exception as e:
        return f"Search error: {e!s}"
```

#### Graph Construction
```python
workflow = StateGraph(WorkflowState)
workflow.add_node("input_processor", input_processor_node)
workflow.add_node("parallel_executor", parallel_tool_executor_node)
# ... additional nodes and edges
```

## 🎯 Patterns and Use Cases

### Parallel Tool Execution
The example demonstrates executing multiple tools concurrently using `asyncio.gather()`, significantly improving performance for I/O-bound operations.

### Conditional Routing
Smart routing based on state conditions, allowing dynamic workflow paths based on validation results and available tools.

### Error Recovery
Comprehensive error handling that maintains system stability while providing meaningful feedback to users.

### Human-in-the-Loop
Support for interrupts and checkpointing, enabling human oversight and intervention when needed.

## 🧪 Testing

The codebase includes patterns for:
- Mock tool creation for consistent testing
- State validation functions
- Scenario-based testing (success, error, edge cases)
- Async test execution with pytest-asyncio

## 🔧 Configuration

### Environment Variables
- Use `.env` files for configuration
- Implement validation for required settings
- Support multiple environments (dev, staging, prod)

### Dependencies
See `requirements.txt` for complete dependency list:
- Core: `langgraph`, `langchain-core`
- Configuration: `pydantic`, `python-dotenv`
- Testing: `pytest`, `pytest-asyncio`
- Development: `black`, `flake8`, `mypy`

## 📚 Advanced Features

### Message Management
- Proper message types (HumanMessage, AIMessage, ToolMessage)
- Message filtering and pruning strategies
- Conversation summarization for long contexts

### Performance Optimization
- Async/await for I/O operations
- Lazy loading for expensive resources
- Execution timing and monitoring

### Security
- Input sanitization
- Credential management
- Rate limiting for API calls

## 🤝 Contributing

1. Follow the patterns in `.cursorrules`
2. Maintain type safety with TypedDict and proper annotations
3. Include comprehensive error handling
4. Add tests for new functionality
5. Document public APIs and complex logic

## 📖 Documentation

- `.cursorrules`: Comprehensive development guidelines
- `example_langgraph_tool.py`: Complete working example
- This README: Setup and usage instructions

## 🔗 References

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangChain Core](https://python.langchain.com/docs/langchain_core/)
- [Python AsyncIO](https://docs.python.org/3/library/asyncio.html)

## 📄 License

This project is provided as an educational resource. Refer to your organization's licensing requirements for production use.

---

**Happy coding with LangGraph! 🎉**