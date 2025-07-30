# LangGraph Chrome Tools

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Playwright](https://img.shields.io/badge/Playwright-enabled-green.svg)](https://playwright.dev/)
[![LangGraph](https://img.shields.io/badge/LangGraph-ready-purple.svg)](https://github.com/langchain-ai/langgraph)

**LangGraph Chrome Tools** is a comprehensive Python package that provides seamless integration between [LangGraph](https://github.com/langchain-ai/langgraph) and [Playwright](https://playwright.dev/) for Chrome automation. It offers powerful tools for web scraping, browser automation, and AI-driven web interactions with robust profile management and error handling.

## 🚀 Features

- **🔧 Easy LangGraph Integration**: Ready-to-use tools that work seamlessly with LangGraph workflows
- **🌐 Chrome Automation**: Full Chrome browser control using Playwright
- **👤 Profile Management**: Support for scratch, persistent, no-profile, and visible UI modes
- **🛡️ Robust Error Handling**: Comprehensive error management with automatic recovery suggestions
- **📦 Easy Installation**: One-command setup with automatic dependency management
- **🔍 Health Monitoring**: Built-in diagnostics and auto-repair capabilities
- **🎯 Production Ready**: Follows Python packaging standards for easy distribution

## 📋 Quick Start

### Installation

```bash
# Install the package
pip install langgraph-chrome-tools

# Set up Playwright and Chrome (one-time setup)
langgraph-chrome-setup
```

### Basic Usage

```python
import asyncio
from langgraph_chrome_tools import (
    chrome_navigate_tool,
    chrome_extract_text_tool,
    ProfileManager,
    ProfileMode
)

async def simple_scraping():
    # Navigate to a website
    result = await chrome_navigate_tool.ainvoke({
        "url": "https://example.com"
    })
    
    # Extract text content
    content = await chrome_extract_text_tool.ainvoke({})
    
    print(f"Extracted content: {content}")

# Run the example
asyncio.run(simple_scraping())
```

### LangGraph Workflow Integration

```python
from langgraph.graph import StateGraph, START, END
from langgraph_chrome_tools import chrome_navigate_tool, chrome_extract_text_tool

# Define your workflow state
class WebScrapingState(TypedDict):
    url: str
    content: str
    
# Create workflow
workflow = StateGraph(WebScrapingState)

# Add Chrome tools as nodes
workflow.add_node("navigate", lambda state: chrome_navigate_tool.ainvoke({"url": state["url"]}))
workflow.add_node("extract", lambda state: chrome_extract_text_tool.ainvoke({}))

# Define the flow
workflow.add_edge(START, "navigate")
workflow.add_edge("navigate", "extract")
workflow.add_edge("extract", END)

# Compile and run
app = workflow.compile()
result = await app.ainvoke({"url": "https://example.com", "content": ""})
```

## 🛠️ Available Tools

### Navigation Tools
- **`chrome_navigate_tool`**: Navigate to URLs with various wait conditions
- **`chrome_scroll_tool`**: Scroll pages vertically or horizontally

### Interaction Tools
- **`chrome_click_tool`**: Click on elements using CSS selectors
- **`chrome_type_tool`**: Type text into input fields
- **`chrome_wait_for_element_tool`**: Wait for elements to appear or change state

### Data Extraction Tools
- **`chrome_extract_text_tool`**: Extract text content from pages or specific elements
- **`chrome_screenshot_tool`**: Capture screenshots (full page or visible area)

### Advanced Tools
- **`chrome_evaluate_js_tool`**: Execute custom JavaScript in the browser context

## 👤 Profile Management

LangGraph Chrome Tools supports multiple profile modes for different use cases:

### Profile Modes

```python
from langgraph_chrome_tools import ProfileManager, ProfileMode

profile_manager = ProfileManager()

# Temporary profile (auto-cleanup)
scratch_profile = profile_manager.create_profile(ProfileMode.SCRATCH)

# Persistent profile (saved between sessions)
persistent_profile = profile_manager.create_profile(
    ProfileMode.PERSISTENT, 
    name="my_automation_profile"
)

# Visible browser for debugging
visible_profile = profile_manager.create_profile(
    ProfileMode.VISIBLE,
    name="debug_session"
)

# No profile (incognito-like)
no_profile = profile_manager.create_profile(ProfileMode.NO_PROFILE)
```

### Profile Features

- **🗑️ Scratch Profiles**: Temporary profiles automatically cleaned up after use
- **💾 Persistent Profiles**: Named profiles that persist between sessions  
- **👁️ Visible Mode**: Show browser window for debugging and profile creation
- **🔒 No-Profile Mode**: Incognito-like mode with no data persistence
- **🧹 Auto-Cleanup**: Automatic cleanup of temporary files and profiles

## 🔧 CLI Tools

The package includes helpful command-line tools:

```bash
# Initial setup and installation
langgraph-chrome-setup

# Check system status
langgraph-chrome-setup status

# Manage profiles
langgraph-chrome-setup profile --list-profiles
langgraph-chrome-setup profile --mode persistent --name my_profile

# Diagnose and fix issues
langgraph-chrome-setup doctor
langgraph-chrome-setup doctor --auto

# Manual Playwright installation
langgraph-chrome-install
```

## 🛡️ Error Handling & Recovery

### Automatic Error Recovery

The package includes comprehensive error handling with automatic recovery suggestions:

```python
from langgraph_chrome_tools.utils import health_check, suggest_reinstall

# Check system health
health_report = health_check()
print(f"System status: {health_report['overall_status']}")

# Get reinstall suggestions for errors
suggestions = suggest_reinstall(some_error)
if suggestions["should_reinstall"]:
    print("Reinstall recommended:")
    for step in suggestions["steps"]:
        print(f"  - {step}")
```

### Error Types

- **`ChromeToolsError`**: Base exception with context and suggestions
- **`BrowserNotStartedError`**: Browser not initialized
- **`ProfileError`**: Profile management issues
- **`PlaywrightInstallationError`**: Installation/setup problems
- **`NetworkError`**: Network connectivity issues
- **`ElementNotFoundError`**: UI element not found
- **`JavaScriptError`**: JavaScript execution failures

## 📚 Advanced Usage

### Custom Browser Configuration

```python
from langgraph_chrome_tools import ChromeBrowser
from langgraph_chrome_tools.utils import create_browser_instance

# Create browser with custom options
browser = await create_browser_instance(
    profile_mode=ProfileMode.PERSISTENT,
    profile_name="my_custom_profile",
    visible=True,
    timeout=60,
    headless=False
)

# Use browser directly
await browser.navigate("https://example.com")
content = await browser.get_page_text()
await browser.close()
```

### Context Manager Usage

```python
from langgraph_chrome_tools.utils import managed_browser

async with managed_browser(profile_mode=ProfileMode.SCRATCH) as browser:
    await browser.navigate("https://example.com")
    text = await browser.get_page_text()
    # Browser automatically closed on exit
```

## 🔍 Health Monitoring

### System Diagnostics

```python
from langgraph_chrome_tools.utils import health_check, auto_fix_issues

# Comprehensive health check
health = health_check()
print(f"Overall status: {health['overall_status']}")

# Automatic issue resolution
fix_result = auto_fix_issues()
if fix_result["success"]:
    print("Issues automatically resolved!")
```

### Manual Troubleshooting

If Chrome automation fails, the package provides helpful suggestions:

1. **Installation Issues**: Automatic Playwright reinstallation
2. **Profile Conflicts**: Profile cleanup and recreation
3. **Process Management**: Hanging Chrome process cleanup
4. **Permission Issues**: File system permission guidance
5. **Network Problems**: Connectivity troubleshooting

## 📖 Examples

Check out the [`examples/`](examples/) directory for comprehensive usage examples:

- **`basic_usage.py`**: Complete web scraping workflow
- **Profile management demonstrations**
- **Individual tool usage examples**
- **Error handling patterns**

## 🔧 Development

### Setting up Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/langgraph-chrome-tools.git
cd langgraph-chrome-tools

# Install in development mode
pip install -e ".[dev]"

# Install Playwright browsers
playwright install chromium

# Run tests
pytest tests/

# Format code
black src/
```

### Project Structure

```
langgraph-chrome-tools/
├── src/langgraph_chrome_tools/
│   ├── core/           # Core browser automation
│   ├── tools/          # LangGraph tool implementations
│   ├── profiles/       # Profile management
│   ├── utils/          # Utilities and helpers
│   └── cli/            # Command-line interface
├── examples/           # Usage examples
├── tests/             # Test suite
├── docs/              # Documentation
└── setup.py           # Package configuration
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [LangGraph](https://github.com/langchain-ai/langgraph) for the excellent workflow framework
- [Playwright](https://playwright.dev/) for robust browser automation
- [LangChain](https://github.com/langchain-ai/langchain) for the foundational tools architecture

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/langgraph-chrome-tools/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/langgraph-chrome-tools/discussions)
- **Documentation**: [Read the Docs](https://langgraph-chrome-tools.readthedocs.io/)

## 🗺️ Roadmap

- [ ] **Firefox Support**: Extend beyond Chrome to Firefox automation
- [ ] **Enhanced Screenshots**: PDF generation and element-specific screenshots
- [ ] **Performance Monitoring**: Built-in performance metrics and optimization
- [ ] **Visual Testing**: Image comparison and visual regression testing
- [ ] **Mobile Simulation**: Mobile device emulation and testing
- [ ] **Parallel Execution**: Multi-browser parallel automation

---

**Happy automating with LangGraph Chrome Tools! 🎉**