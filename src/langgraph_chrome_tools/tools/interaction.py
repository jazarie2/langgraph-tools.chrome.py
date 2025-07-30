"""Interaction tools for Chrome automation in LangGraph."""

import logging
from typing import Optional

from langchain_core.tools import tool

from ..core.exceptions import ChromeToolsError, ElementNotFoundError
from ..utils.browser_manager import get_browser_instance

logger = logging.getLogger(__name__)


@tool
async def chrome_click_tool(
    selector: str,
    browser_id: Optional[str] = None,
    timeout: Optional[float] = None,
) -> str:
    """Click on an element using CSS selector.
    
    This tool finds an element using a CSS selector and clicks on it.
    It waits for the element to be clickable before attempting the click.
    
    Args:
        selector: CSS selector for the element to click (e.g., "#button-id", ".class-name", "button")
        browser_id: Optional browser instance ID (uses default if not provided)
        timeout: Optional timeout in seconds for finding the element
        
    Returns:
        str: JSON string with click results
        
    Examples:
        >>> result = await chrome_click_tool("#submit-button")
        >>> result = await chrome_click_tool("button[type='submit']")
        >>> result = await chrome_click_tool(".menu-item", timeout=10)
    """
    try:
        # Get browser instance
        browser = await get_browser_instance(browser_id)
        
        # Perform click
        result = await browser.click(selector, timeout=timeout)
        
        response = {
            "success": True,
            "selector": selector,
            "action": "click",
            "page_url": result["page_url"],
            "message": f"Successfully clicked element: {selector}",
        }
        
        logger.info(f"Click successful: {selector}")
        
        import json
        return json.dumps(response, indent=2)
    
    except ElementNotFoundError as e:
        error_response = {
            "success": False,
            "selector": selector,
            "error": "element_not_found",
            "message": str(e),
            "suggestions": e.suggestions,
        }
        logger.error(f"Element not found for click: {selector}")
        import json
        return json.dumps(error_response, indent=2)
    
    except ChromeToolsError as e:
        error_response = {
            "success": False,
            "selector": selector,
            "error": "chrome_error",
            "message": str(e),
            "suggestions": e.suggestions,
        }
        logger.error(f"Chrome error clicking {selector}: {e}")
        import json
        return json.dumps(error_response, indent=2)
    
    except Exception as e:
        error_response = {
            "success": False,
            "selector": selector,
            "error": "unexpected_error",
            "message": f"Unexpected error: {str(e)}",
            "suggestions": [
                "Verify the CSS selector is correct",
                "Check if the element is visible on the page",
                "Try waiting for the page to load completely",
            ],
        }
        logger.error(f"Unexpected error clicking {selector}: {e}")
        import json
        return json.dumps(error_response, indent=2)


@tool
async def chrome_type_tool(
    selector: str,
    text: str,
    browser_id: Optional[str] = None,
    delay: float = 0,
    timeout: Optional[float] = None,
) -> str:
    """Type text into an input element.
    
    This tool finds an input element using a CSS selector and types the specified text.
    It clears any existing text before typing the new text.
    
    Args:
        selector: CSS selector for the input element (e.g., "#email", "input[name='username']")
        text: Text to type into the element
        browser_id: Optional browser instance ID (uses default if not provided)
        delay: Delay between keystrokes in seconds (default: 0)
        timeout: Optional timeout in seconds for finding the element
        
    Returns:
        str: JSON string with typing results
        
    Examples:
        >>> result = await chrome_type_tool("#email", "user@example.com")
        >>> result = await chrome_type_tool("input[name='password']", "secret123", delay=0.1)
    """
    try:
        # Get browser instance
        browser = await get_browser_instance(browser_id)
        
        # Perform typing
        result = await browser.type_text(selector, text, delay=delay, timeout=timeout)
        
        response = {
            "success": True,
            "selector": selector,
            "text_length": len(text),
            "action": "type",
            "page_url": result["page_url"],
            "message": f"Successfully typed text into element: {selector}",
        }
        
        logger.info(f"Type successful: {selector} ({len(text)} characters)")
        
        import json
        return json.dumps(response, indent=2)
    
    except ElementNotFoundError as e:
        error_response = {
            "success": False,
            "selector": selector,
            "error": "element_not_found",
            "message": str(e),
            "suggestions": e.suggestions,
        }
        logger.error(f"Element not found for typing: {selector}")
        import json
        return json.dumps(error_response, indent=2)
    
    except ChromeToolsError as e:
        error_response = {
            "success": False,
            "selector": selector,
            "error": "chrome_error",
            "message": str(e),
            "suggestions": e.suggestions,
        }
        logger.error(f"Chrome error typing into {selector}: {e}")
        import json
        return json.dumps(error_response, indent=2)
    
    except Exception as e:
        error_response = {
            "success": False,
            "selector": selector,
            "error": "unexpected_error",
            "message": f"Unexpected error: {str(e)}",
            "suggestions": [
                "Verify the CSS selector points to an input element",
                "Check if the element is enabled and editable",
                "Try using a different selector",
            ],
        }
        logger.error(f"Unexpected error typing into {selector}: {e}")
        import json
        return json.dumps(error_response, indent=2)


@tool
async def chrome_scroll_tool(
    x: int = 0,
    y: int = 0,
    browser_id: Optional[str] = None,
) -> str:
    """Scroll the page by specified amounts.
    
    This tool scrolls the current page by the specified horizontal and vertical amounts.
    Positive values scroll down/right, negative values scroll up/left.
    
    Args:
        x: Horizontal scroll amount in pixels (positive = right, negative = left)
        y: Vertical scroll amount in pixels (positive = down, negative = up)
        browser_id: Optional browser instance ID (uses default if not provided)
        
    Returns:
        str: JSON string with scroll results
        
    Examples:
        >>> result = await chrome_scroll_tool(y=500)  # Scroll down 500px
        >>> result = await chrome_scroll_tool(x=-200, y=300)  # Scroll left 200px, down 300px
        >>> result = await chrome_scroll_tool(y=-1000)  # Scroll up 1000px
    """
    try:
        # Get browser instance
        browser = await get_browser_instance(browser_id)
        
        # Perform scroll
        result = await browser.scroll(x=x, y=y)
        
        response = {
            "success": True,
            "scroll_x": x,
            "scroll_y": y,
            "action": "scroll",
            "page_url": result["page_url"],
            "message": f"Successfully scrolled by ({x}, {y}) pixels",
        }
        
        logger.info(f"Scroll successful: ({x}, {y})")
        
        import json
        return json.dumps(response, indent=2)
    
    except ChromeToolsError as e:
        error_response = {
            "success": False,
            "scroll_x": x,
            "scroll_y": y,
            "error": "chrome_error",
            "message": str(e),
            "suggestions": e.suggestions,
        }
        logger.error(f"Chrome error scrolling: {e}")
        import json
        return json.dumps(error_response, indent=2)
    
    except Exception as e:
        error_response = {
            "success": False,
            "scroll_x": x,
            "scroll_y": y,
            "error": "unexpected_error",
            "message": f"Unexpected error: {str(e)}",
            "suggestions": [
                "Check if the browser is properly started",
                "Verify the page is loaded",
                "Try smaller scroll amounts",
            ],
        }
        logger.error(f"Unexpected error scrolling: {e}")
        import json
        return json.dumps(error_response, indent=2)