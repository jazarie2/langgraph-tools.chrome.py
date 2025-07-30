"""Page action tools for Chrome automation in LangGraph."""

import logging
from typing import Optional, Any

from langchain_core.tools import tool

from ..core.exceptions import ChromeToolsError, ElementNotFoundError, JavaScriptError
from ..utils.browser_manager import get_browser_instance

logger = logging.getLogger(__name__)


@tool
async def chrome_wait_for_element_tool(
    selector: str,
    state: str = "visible",
    timeout: Optional[float] = None,
    browser_id: Optional[str] = None,
) -> str:
    """Wait for an element to appear or reach a specific state.
    
    This tool waits for an element to appear on the page or reach a specific state.
    Useful for waiting for dynamic content to load.
    
    Args:
        selector: CSS selector for the element to wait for
        state: Element state to wait for. Options:
               - "visible": Element is visible and has non-zero size
               - "hidden": Element is hidden or has zero size
               - "attached": Element is attached to DOM
               - "detached": Element is detached from DOM
        timeout: Optional timeout in seconds (uses browser default if not provided)
        browser_id: Optional browser instance ID (uses default if not provided)
        
    Returns:
        str: JSON string with wait results
        
    Examples:
        >>> result = await chrome_wait_for_element_tool("#loading-spinner", state="hidden")
        >>> result = await chrome_wait_for_element_tool(".dynamic-content", timeout=15)
        >>> result = await chrome_wait_for_element_tool("button", state="visible")
    """
    try:
        # Get browser instance
        browser = await get_browser_instance(browser_id)
        
        # Wait for element
        result = await browser.wait_for_element(selector, timeout=timeout, state=state)
        
        response = {
            "success": True,
            "selector": selector,
            "state": state,
            "timeout_used": timeout or browser.timeout,
            "page_url": result["page_url"],
            "message": f"Element '{selector}' reached state '{state}'",
        }
        
        logger.info(f"Wait successful: {selector} -> {state}")
        
        import json
        return json.dumps(response, indent=2)
    
    except ElementNotFoundError as e:
        error_response = {
            "success": False,
            "selector": selector,
            "state": state,
            "error": "element_not_found",
            "message": str(e),
            "suggestions": e.suggestions,
        }
        logger.error(f"Element not found while waiting: {selector}")
        import json
        return json.dumps(error_response, indent=2)
    
    except ChromeToolsError as e:
        error_response = {
            "success": False,
            "selector": selector,
            "state": state,
            "error": "chrome_error",
            "message": str(e),
            "suggestions": e.suggestions,
        }
        logger.error(f"Chrome error waiting for element: {e}")
        import json
        return json.dumps(error_response, indent=2)
    
    except Exception as e:
        error_response = {
            "success": False,
            "selector": selector,
            "state": state,
            "error": "unexpected_error",
            "message": f"Unexpected error: {str(e)}",
            "suggestions": [
                "Check if the CSS selector is correct",
                "Try increasing the timeout value",
                "Verify the element eventually appears on the page",
            ],
        }
        logger.error(f"Unexpected error waiting for element: {e}")
        import json
        return json.dumps(error_response, indent=2)


@tool
async def chrome_evaluate_js_tool(
    script: str,
    browser_id: Optional[str] = None,
) -> str:
    """Execute JavaScript code in the browser context.
    
    This tool executes custom JavaScript code in the current page context.
    Useful for complex interactions, data extraction, or page manipulation.
    
    Args:
        script: JavaScript code to execute (should return a value)
        browser_id: Optional browser instance ID (uses default if not provided)
        
    Returns:
        str: JSON string with JavaScript execution results
        
    Examples:
        >>> result = await chrome_evaluate_js_tool("document.title")
        >>> result = await chrome_evaluate_js_tool("window.scrollY")
        >>> result = await chrome_evaluate_js_tool("document.querySelectorAll('a').length")
        >>> result = await chrome_evaluate_js_tool("localStorage.getItem('user_id')")
    """
    try:
        # Get browser instance
        browser = await get_browser_instance(browser_id)
        
        # Execute JavaScript
        js_result = await browser.evaluate_javascript(script)
        
        response = {
            "success": True,
            "script": script,
            "result": js_result,
            "result_type": type(js_result).__name__,
            "page_url": browser.current_url,
            "message": f"JavaScript executed successfully",
        }
        
        logger.info(f"JavaScript execution successful: {script[:50]}...")
        
        import json
        return json.dumps(response, indent=2, default=str)
    
    except JavaScriptError as e:
        error_response = {
            "success": False,
            "script": script,
            "error": "javascript_error",
            "message": str(e),
            "suggestions": e.suggestions,
        }
        logger.error(f"JavaScript error: {e}")
        import json
        return json.dumps(error_response, indent=2)
    
    except ChromeToolsError as e:
        error_response = {
            "success": False,
            "script": script,
            "error": "chrome_error",
            "message": str(e),
            "suggestions": e.suggestions,
        }
        logger.error(f"Chrome error executing JavaScript: {e}")
        import json
        return json.dumps(error_response, indent=2)
    
    except Exception as e:
        error_response = {
            "success": False,
            "script": script,
            "error": "unexpected_error",
            "message": f"Unexpected error: {str(e)}",
            "suggestions": [
                "Check JavaScript syntax",
                "Ensure the script returns a serializable value",
                "Test the script in browser console first",
            ],
        }
        logger.error(f"Unexpected error executing JavaScript: {e}")
        import json
        return json.dumps(error_response, indent=2)