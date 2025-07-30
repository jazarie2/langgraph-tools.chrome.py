"""LangGraph Chrome Tools - Chrome automation using Playwright for LangGraph applications.

This package provides easy-to-use LangGraph tools for automating Google Chrome
using Playwright, with support for profile management and robust error handling.

Example:
    >>> from langgraph_chrome_tools import ChromeBrowser, chrome_navigate_tool
    >>> from langgraph_chrome_tools.profiles import ProfileManager
    
    >>> # Initialize with profile management
    >>> profile_manager = ProfileManager()
    >>> browser = ChromeBrowser(profile_manager=profile_manager)
    
    >>> # Use in LangGraph workflows
    >>> tools = [chrome_navigate_tool, chrome_click_tool, chrome_extract_text_tool]
"""

from typing import List

from .core.browser import ChromeBrowser
from .core.exceptions import (
    ChromeToolsError,
    BrowserNotStartedError,
    ProfileError,
    PlaywrightInstallationError,
)
from .tools.navigation import chrome_navigate_tool
from .tools.interaction import chrome_click_tool, chrome_type_tool, chrome_scroll_tool
from .tools.extraction import chrome_extract_text_tool, chrome_screenshot_tool
from .tools.page_actions import chrome_wait_for_element_tool, chrome_evaluate_js_tool
from .profiles.manager import ProfileManager, ProfileMode
from .utils.installer import install_playwright, check_playwright_installation
from .utils.health import health_check, suggest_reinstall

__version__ = "0.1.0"
__author__ = "LangGraph Chrome Tools Team"
__email__ = "support@langgraph-chrome-tools.com"

# Main exports for easy import
__all__ = [
    # Core classes
    "ChromeBrowser",
    "ProfileManager",
    "ProfileMode",
    
    # Navigation tools
    "chrome_navigate_tool",
    
    # Interaction tools
    "chrome_click_tool",
    "chrome_type_tool",
    "chrome_scroll_tool",
    
    # Extraction tools
    "chrome_extract_text_tool",
    "chrome_screenshot_tool",
    
    # Page action tools
    "chrome_wait_for_element_tool",
    "chrome_evaluate_js_tool",
    
    # Utility functions
    "install_playwright",
    "check_playwright_installation",
    "health_check",
    "suggest_reinstall",
    
    # Exceptions
    "ChromeToolsError",
    "BrowserNotStartedError", 
    "ProfileError",
    "PlaywrightInstallationError",
    
    # Version info
    "__version__",
]

def get_all_chrome_tools() -> List:
    """Get all available Chrome tools for LangGraph.
    
    Returns:
        List: All available Chrome automation tools
    """
    return [
        chrome_navigate_tool,
        chrome_click_tool,
        chrome_type_tool,
        chrome_scroll_tool,
        chrome_extract_text_tool,
        chrome_screenshot_tool,
        chrome_wait_for_element_tool,
        chrome_evaluate_js_tool,
    ]