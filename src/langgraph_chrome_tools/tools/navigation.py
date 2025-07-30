"""Navigation tools for Chrome automation in LangGraph."""

import logging
from typing import Dict, Any, Optional

from langchain_core.tools import tool

from ..core.browser import ChromeBrowser
from ..core.exceptions import ChromeToolsError, NetworkError
from ..utils.browser_manager import get_browser_instance

logger = logging.getLogger(__name__)


@tool
async def chrome_navigate_tool(
    url: str,
    wait_until: str = "load",
    browser_id: Optional[str] = None,
    timeout: Optional[float] = None,
) -> str:
    """Navigate to a URL using Chrome.
    
    This tool navigates to a specified URL and waits for the page to load.
    It handles various loading states and provides detailed feedback.
    
    Args:
        url: The URL to navigate to (must include protocol, e.g., https://)
        wait_until: When to consider navigation complete. Options:
                   - "load": Wait for the load event (default)
                   - "domcontentloaded": Wait for DOMContentLoaded event
                   - "networkidle": Wait for network to be idle
                   - "commit": Wait for navigation to commit
        browser_id: Optional browser instance ID (uses default if not provided)
        timeout: Optional timeout in seconds (uses browser default if not provided)
        
    Returns:
        str: JSON string with navigation results including status, title, and final URL
        
    Examples:
        >>> result = await chrome_navigate_tool("https://example.com")
        >>> result = await chrome_navigate_tool("https://example.com", wait_until="networkidle")
    """
    try:
        # Get browser instance
        browser = await get_browser_instance(browser_id)
        
        # Validate URL
        if not url.startswith(("http://", "https://", "file://")):
            url = "https://" + url
        
        # Navigate with custom timeout if provided
        if timeout:
            original_timeout = browser.timeout
            browser.timeout = timeout
        
        try:
            result = await browser.navigate(url, wait_until=wait_until)
            
            # Format response
            response = {
                "success": True,
                "url": result["url"],
                "final_url": result["final_url"],
                "status": result["status"],
                "title": result["title"],
                "message": f"Successfully navigated to {result['final_url']}",
            }
            
            logger.info(f"Navigation successful: {url} -> {result['final_url']}")
            
            import json
            return json.dumps(response, indent=2)
            
        finally:
            # Restore original timeout
            if timeout:
                browser.timeout = original_timeout
    
    except NetworkError as e:
        error_response = {
            "success": False,
            "url": url,
            "error": "network_error",
            "message": str(e),
            "suggestions": e.suggestions,
        }
        logger.error(f"Network error navigating to {url}: {e}")
        import json
        return json.dumps(error_response, indent=2)
    
    except ChromeToolsError as e:
        error_response = {
            "success": False,
            "url": url,
            "error": "chrome_error",
            "message": str(e),
            "suggestions": e.suggestions,
        }
        logger.error(f"Chrome error navigating to {url}: {e}")
        import json
        return json.dumps(error_response, indent=2)
    
    except Exception as e:
        error_response = {
            "success": False,
            "url": url,
            "error": "unexpected_error",
            "message": f"Unexpected error: {str(e)}",
            "suggestions": [
                "Check if the URL is valid",
                "Ensure the browser is properly started",
                "Try again with a different URL",
            ],
        }
        logger.error(f"Unexpected error navigating to {url}: {e}")
        import json
        return json.dumps(error_response, indent=2)