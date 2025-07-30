"""Data extraction tools for Chrome automation in LangGraph."""

import logging
from typing import Optional
from pathlib import Path

from langchain_core.tools import tool

from ..core.exceptions import ChromeToolsError
from ..utils.browser_manager import get_browser_instance

logger = logging.getLogger(__name__)


@tool
async def chrome_extract_text_tool(
    selector: Optional[str] = None,
    browser_id: Optional[str] = None,
) -> str:
    """Extract text content from the current page or a specific element.
    
    This tool extracts visible text from the current page. If a selector is provided,
    it extracts text from that specific element. Otherwise, it extracts all visible text.
    
    Args:
        selector: Optional CSS selector for specific element (extracts from body if not provided)
        browser_id: Optional browser instance ID (uses default if not provided)
        
    Returns:
        str: JSON string with extracted text content
        
    Examples:
        >>> result = await chrome_extract_text_tool()  # Extract all page text
        >>> result = await chrome_extract_text_tool("#main-content")  # Extract from specific element
        >>> result = await chrome_extract_text_tool(".article-body")  # Extract article text
    """
    try:
        # Get browser instance
        browser = await get_browser_instance(browser_id)
        
        if selector:
            # Extract text from specific element
            try:
                text_content = await browser._page.inner_text(selector)
                source = f"element '{selector}'"
            except Exception as e:
                if "timeout" in str(e).lower() or "not found" in str(e).lower():
                    error_response = {
                        "success": False,
                        "selector": selector,
                        "error": "element_not_found",
                        "message": f"Element not found: {selector}",
                        "page_url": browser.current_url,
                        "suggestions": [
                            "Verify the CSS selector is correct",
                            "Check if the element exists on the page",
                            "Wait for the page to load completely",
                        ],
                    }
                    import json
                    return json.dumps(error_response, indent=2)
                else:
                    raise
        else:
            # Extract all visible text from page
            text_content = await browser.get_page_text()
            source = "entire page"
        
        response = {
            "success": True,
            "text_content": text_content,
            "text_length": len(text_content),
            "word_count": len(text_content.split()) if text_content else 0,
            "source": source,
            "page_url": browser.current_url,
            "message": f"Successfully extracted text from {source}",
        }
        
        logger.info(f"Text extraction successful: {len(text_content)} characters from {source}")
        
        import json
        return json.dumps(response, indent=2)
    
    except ChromeToolsError as e:
        error_response = {
            "success": False,
            "selector": selector,
            "error": "chrome_error",
            "message": str(e),
            "suggestions": e.suggestions,
        }
        logger.error(f"Chrome error extracting text: {e}")
        import json
        return json.dumps(error_response, indent=2)
    
    except Exception as e:
        error_response = {
            "success": False,
            "selector": selector,
            "error": "unexpected_error",
            "message": f"Unexpected error: {str(e)}",
            "suggestions": [
                "Check if the browser is properly started",
                "Verify the page has loaded",
                "Try extracting from a different element",
            ],
        }
        logger.error(f"Unexpected error extracting text: {e}")
        import json
        return json.dumps(error_response, indent=2)


@tool
async def chrome_screenshot_tool(
    path: Optional[str] = None,
    full_page: bool = False,
    browser_id: Optional[str] = None,
) -> str:
    """Take a screenshot of the current page.
    
    This tool captures a screenshot of the current page. You can save it to a file
    or get the screenshot data as base64.
    
    Args:
        path: Optional file path to save screenshot (returns base64 if not provided)
        full_page: Whether to capture the entire page or just the visible area
        browser_id: Optional browser instance ID (uses default if not provided)
        
    Returns:
        str: JSON string with screenshot results
        
    Examples:
        >>> result = await chrome_screenshot_tool()  # Get base64 screenshot
        >>> result = await chrome_screenshot_tool("/tmp/page.png")  # Save to file
        >>> result = await chrome_screenshot_tool(full_page=True)  # Full page screenshot
    """
    try:
        # Get browser instance
        browser = await get_browser_instance(browser_id)
        
        # Take screenshot
        if path:
            # Save to file
            screenshot_path = Path(path)
            screenshot_path.parent.mkdir(parents=True, exist_ok=True)
            
            result = await browser.screenshot(path=screenshot_path, full_page=full_page)
            
            response = {
                "success": True,
                "screenshot_path": str(result),
                "full_page": full_page,
                "format": "file",
                "page_url": browser.current_url,
                "message": f"Screenshot saved to {result}",
            }
        else:
            # Return as base64
            screenshot_bytes = await browser.screenshot(full_page=full_page)
            
            import base64
            screenshot_b64 = base64.b64encode(screenshot_bytes).decode()
            
            response = {
                "success": True,
                "screenshot_base64": screenshot_b64,
                "screenshot_size": len(screenshot_bytes),
                "full_page": full_page,
                "format": "base64",
                "page_url": browser.current_url,
                "message": f"Screenshot captured ({len(screenshot_bytes)} bytes)",
            }
        
        logger.info(f"Screenshot successful: full_page={full_page}, format={'file' if path else 'base64'}")
        
        import json
        return json.dumps(response, indent=2)
    
    except ChromeToolsError as e:
        error_response = {
            "success": False,
            "path": path,
            "error": "chrome_error",
            "message": str(e),
            "suggestions": e.suggestions,
        }
        logger.error(f"Chrome error taking screenshot: {e}")
        import json
        return json.dumps(error_response, indent=2)
    
    except Exception as e:
        error_response = {
            "success": False,
            "path": path,
            "error": "unexpected_error",
            "message": f"Unexpected error: {str(e)}",
            "suggestions": [
                "Check if the browser is properly started",
                "Verify the save path is writable",
                "Ensure the page has loaded",
            ],
        }
        logger.error(f"Unexpected error taking screenshot: {e}")
        import json
        return json.dumps(error_response, indent=2)