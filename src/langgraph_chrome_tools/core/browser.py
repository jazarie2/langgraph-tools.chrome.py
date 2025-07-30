"""Chrome browser automation using Playwright.

This module provides the core ChromeBrowser class that manages Chrome instances
using Playwright, with comprehensive profile management and error handling.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, Union, List
from pathlib import Path

try:
    from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright
except ImportError:
    raise ImportError(
        "Playwright is not installed. Please install it with: pip install playwright && playwright install chromium"
    )

from .exceptions import (
    ChromeToolsError,
    BrowserNotStartedError,
    ProfileError,
    PlaywrightInstallationError,
    NetworkError,
    ElementNotFoundError,
)
from ..profiles.manager import ProfileManager, ProfileConfig, ProfileMode


logger = logging.getLogger(__name__)


class ChromeBrowser:
    """Chrome browser automation using Playwright.
    
    This class provides a high-level interface for Chrome automation with
    comprehensive profile management, error handling, and LangGraph integration.
    
    Examples:
        >>> # Basic usage with scratch profile
        >>> browser = ChromeBrowser()
        >>> await browser.start()
        >>> await browser.navigate("https://example.com")
        >>> content = await browser.get_page_content()
        >>> await browser.close()
        
        >>> # With custom profile
        >>> profile_manager = ProfileManager()
        >>> profile = profile_manager.create_profile(ProfileMode.PERSISTENT, name="my_profile")
        >>> browser = ChromeBrowser(profile_config=profile)
        >>> await browser.start()
    """
    
    def __init__(
        self,
        profile_manager: Optional[ProfileManager] = None,
        profile_config: Optional[ProfileConfig] = None,
        timeout: float = 30.0,
        **kwargs: Any,
    ) -> None:
        """Initialize the Chrome browser.
        
        Args:
            profile_manager: Profile manager instance
            profile_config: Pre-configured profile (overrides profile_manager)
            timeout: Default timeout for operations in seconds
            **kwargs: Additional Playwright browser options
        """
        self.timeout = timeout
        self.browser_options = kwargs
        
        # Set up profile management
        if profile_config:
            self.profile_config = profile_config
            self.profile_manager = profile_manager
        elif profile_manager:
            self.profile_manager = profile_manager
            self.profile_config = profile_manager.create_profile(ProfileMode.SCRATCH)
        else:
            self.profile_manager = ProfileManager()
            self.profile_config = self.profile_manager.create_profile(ProfileMode.SCRATCH)
        
        # Playwright objects (initialized on start)
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        
        # State tracking
        self._is_started = False
        self._current_url: Optional[str] = None
    
    async def start(self) -> None:
        """Start the Chrome browser with the configured profile.
        
        Raises:
            PlaywrightInstallationError: If Playwright or Chrome is not properly installed
            ProfileError: If there are issues with the profile configuration
            ChromeToolsError: If browser startup fails
        """
        if self._is_started:
            logger.warning("Browser is already started")
            return
        
        try:
            # Start Playwright
            self._playwright = await async_playwright().start()
            
            # Prepare browser launch options
            launch_options = {
                "headless": self.profile_config.headless,
                "args": self.profile_manager.get_browser_args(self.profile_config),
                **self.browser_options,
            }
            
            logger.info(f"Starting Chrome with profile: {self.profile_config.name}")
            logger.debug(f"Launch options: {launch_options}")
            
            # Launch browser
            self._browser = await self._playwright.chromium.launch(**launch_options)
            
            # Create browser context
            context_options = {}
            if self.profile_config.user_data_dir:
                # For persistent profiles, we use the browser's built-in profile support
                pass
            
            self._context = await self._browser.new_context(**context_options)
            
            # Create initial page
            self._page = await self._context.new_page()
            
            # Set default timeout
            self._page.set_default_timeout(self.timeout * 1000)  # Convert to milliseconds
            
            self._is_started = True
            logger.info("Chrome browser started successfully")
            
        except ImportError as e:
            raise PlaywrightInstallationError(
                "Playwright not properly installed",
                missing_component="playwright",
                installation_command="pip install playwright && playwright install chromium",
            ) from e
        
        except Exception as e:
            # Clean up on failure
            await self._cleanup_on_error()
            
            if "executable doesn't exist" in str(e).lower():
                raise PlaywrightInstallationError(
                    "Chrome browser not found",
                    missing_component="chromium",
                    installation_command="playwright install chromium",
                ) from e
            elif "profile" in str(e).lower():
                raise ProfileError(
                    f"Profile setup failed: {e}",
                    profile_path=str(self.profile_config.path) if self.profile_config.path else None,
                    profile_mode=self.profile_config.mode.value,
                ) from e
            else:
                raise ChromeToolsError(
                    f"Failed to start browser: {e}",
                    context={"profile_mode": self.profile_config.mode.value},
                    suggestions=[
                        "Check if Chrome is already running",
                        "Verify profile configuration",
                        "Try running with visible=True for debugging",
                    ],
                ) from e
    
    async def _cleanup_on_error(self) -> None:
        """Clean up Playwright resources on error."""
        try:
            if self._page:
                await self._page.close()
            if self._context:
                await self._context.close()
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()
        except Exception:
            # Ignore cleanup errors
            pass
        finally:
            self._page = None
            self._context = None
            self._browser = None
            self._playwright = None
            self._is_started = False
    
    def _ensure_started(self, operation: str) -> None:
        """Ensure browser is started before performing an operation.
        
        Args:
            operation: Name of the operation being performed
            
        Raises:
            BrowserNotStartedError: If browser is not started
        """
        if not self._is_started or not self._page:
            raise BrowserNotStartedError(operation)
    
    async def navigate(self, url: str, wait_until: str = "load") -> Dict[str, Any]:
        """Navigate to a URL.
        
        Args:
            url: URL to navigate to
            wait_until: When to consider navigation finished
                       ("load", "domcontentloaded", "networkidle", "commit")
            
        Returns:
            Dict[str, Any]: Navigation result with status and timing
            
        Raises:
            BrowserNotStartedError: If browser is not started
            NetworkError: If navigation fails
        """
        self._ensure_started("navigate")
        
        try:
            logger.info(f"Navigating to: {url}")
            
            # Perform navigation
            response = await self._page.goto(url, wait_until=wait_until)
            
            if response:
                status = response.status
                self._current_url = url
                
                result = {
                    "url": url,
                    "status": status,
                    "success": status < 400,
                    "title": await self._page.title(),
                    "final_url": self._page.url,
                }
                
                logger.info(f"Navigation completed: {status}")
                return result
            else:
                # Navigation succeeded but no response (e.g., file:// URLs)
                self._current_url = url
                return {
                    "url": url,
                    "status": 200,
                    "success": True,
                    "title": await self._page.title(),
                    "final_url": self._page.url,
                }
        
        except Exception as e:
            if "timeout" in str(e).lower():
                raise NetworkError(
                    f"Navigation timeout: {url}",
                    url=url,
                    timeout=self.timeout,
                ) from e
            elif "net::" in str(e).lower() or "dns" in str(e).lower():
                raise NetworkError(
                    f"Network error navigating to {url}: {e}",
                    url=url,
                ) from e
            else:
                raise ChromeToolsError(
                    f"Navigation failed: {e}",
                    context={"url": url},
                    suggestions=[
                        "Check if the URL is correct",
                        "Verify internet connection",
                        "Try increasing timeout",
                    ],
                ) from e
    
    async def click(self, selector: str, timeout: Optional[float] = None) -> Dict[str, Any]:
        """Click on an element.
        
        Args:
            selector: CSS selector for the element
            timeout: Timeout for the operation
            
        Returns:
            Dict[str, Any]: Click result
            
        Raises:
            BrowserNotStartedError: If browser is not started
            ElementNotFoundError: If element is not found
        """
        self._ensure_started("click")
        
        operation_timeout = (timeout or self.timeout) * 1000
        
        try:
            logger.debug(f"Clicking element: {selector}")
            
            # Wait for element and click
            await self._page.click(selector, timeout=operation_timeout)
            
            return {
                "selector": selector,
                "success": True,
                "action": "click",
                "page_url": self._page.url,
            }
        
        except Exception as e:
            if "timeout" in str(e).lower() or "not found" in str(e).lower():
                raise ElementNotFoundError(
                    selector=selector,
                    page_url=self._page.url,
                    timeout=timeout or self.timeout,
                ) from e
            else:
                raise ChromeToolsError(
                    f"Click failed: {e}",
                    context={"selector": selector, "page_url": self._page.url},
                ) from e
    
    async def type_text(
        self,
        selector: str,
        text: str,
        delay: float = 0,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Type text into an element.
        
        Args:
            selector: CSS selector for the input element
            text: Text to type
            delay: Delay between keystrokes in seconds
            timeout: Timeout for the operation
            
        Returns:
            Dict[str, Any]: Type result
        """
        self._ensure_started("type_text")
        
        operation_timeout = (timeout or self.timeout) * 1000
        
        try:
            logger.debug(f"Typing text into: {selector}")
            
            # Clear existing text and type new text
            await self._page.fill(selector, "", timeout=operation_timeout)
            await self._page.type(selector, text, delay=delay * 1000)
            
            return {
                "selector": selector,
                "text": text,
                "success": True,
                "action": "type",
                "page_url": self._page.url,
            }
        
        except Exception as e:
            if "timeout" in str(e).lower() or "not found" in str(e).lower():
                raise ElementNotFoundError(
                    selector=selector,
                    page_url=self._page.url,
                    timeout=timeout or self.timeout,
                ) from e
            else:
                raise ChromeToolsError(
                    f"Type failed: {e}",
                    context={"selector": selector, "page_url": self._page.url},
                ) from e
    
    async def get_page_content(self) -> str:
        """Get the current page's text content.
        
        Returns:
            str: Page text content
        """
        self._ensure_started("get_page_content")
        
        try:
            return await self._page.content()
        except Exception as e:
            raise ChromeToolsError(f"Failed to get page content: {e}") from e
    
    async def get_page_text(self) -> str:
        """Get the current page's visible text.
        
        Returns:
            str: Page visible text
        """
        self._ensure_started("get_page_text")
        
        try:
            return await self._page.inner_text("body")
        except Exception as e:
            raise ChromeToolsError(f"Failed to get page text: {e}") from e
    
    async def screenshot(
        self,
        path: Optional[Union[str, Path]] = None,
        full_page: bool = False,
    ) -> Union[bytes, str]:
        """Take a screenshot of the current page.
        
        Args:
            path: Path to save screenshot (returns bytes if None)
            full_page: Whether to capture the full page
            
        Returns:
            Union[bytes, str]: Screenshot bytes or file path
        """
        self._ensure_started("screenshot")
        
        try:
            screenshot_options = {"full_page": full_page}
            
            if path:
                screenshot_options["path"] = str(path)
                await self._page.screenshot(**screenshot_options)
                return str(path)
            else:
                return await self._page.screenshot(**screenshot_options)
        
        except Exception as e:
            raise ChromeToolsError(f"Screenshot failed: {e}") from e
    
    async def evaluate_javascript(self, script: str) -> Any:
        """Execute JavaScript in the browser.
        
        Args:
            script: JavaScript code to execute
            
        Returns:
            Any: Result of the JavaScript execution
        """
        self._ensure_started("evaluate_javascript")
        
        try:
            return await self._page.evaluate(script)
        except Exception as e:
            from .exceptions import JavaScriptError
            raise JavaScriptError(
                script=script,
                error_message=str(e),
                page_url=self._page.url,
            ) from e
    
    async def wait_for_element(
        self,
        selector: str,
        timeout: Optional[float] = None,
        state: str = "visible",
    ) -> Dict[str, Any]:
        """Wait for an element to appear.
        
        Args:
            selector: CSS selector for the element
            timeout: Timeout for the operation
            state: Element state to wait for ("visible", "hidden", "attached", "detached")
            
        Returns:
            Dict[str, Any]: Wait result
        """
        self._ensure_started("wait_for_element")
        
        operation_timeout = (timeout or self.timeout) * 1000
        
        try:
            logger.debug(f"Waiting for element: {selector} (state: {state})")
            
            await self._page.wait_for_selector(selector, timeout=operation_timeout, state=state)
            
            return {
                "selector": selector,
                "state": state,
                "success": True,
                "page_url": self._page.url,
            }
        
        except Exception as e:
            if "timeout" in str(e).lower():
                raise ElementNotFoundError(
                    selector=selector,
                    page_url=self._page.url,
                    timeout=timeout or self.timeout,
                ) from e
            else:
                raise ChromeToolsError(
                    f"Wait for element failed: {e}",
                    context={"selector": selector, "page_url": self._page.url},
                ) from e
    
    async def scroll(self, x: int = 0, y: int = 0) -> Dict[str, Any]:
        """Scroll the page.
        
        Args:
            x: Horizontal scroll amount
            y: Vertical scroll amount
            
        Returns:
            Dict[str, Any]: Scroll result
        """
        self._ensure_started("scroll")
        
        try:
            await self._page.evaluate(f"window.scrollBy({x}, {y})")
            
            return {
                "x": x,
                "y": y,
                "success": True,
                "page_url": self._page.url,
            }
        
        except Exception as e:
            raise ChromeToolsError(f"Scroll failed: {e}") from e
    
    @property
    def current_url(self) -> Optional[str]:
        """Get the current page URL."""
        if self._page:
            return self._page.url
        return self._current_url
    
    @property
    def is_started(self) -> bool:
        """Check if the browser is started."""
        return self._is_started
    
    async def close(self) -> None:
        """Close the browser and clean up resources."""
        if not self._is_started:
            return
        
        try:
            logger.info("Closing Chrome browser")
            
            if self._page:
                await self._page.close()
            if self._context:
                await self._context.close()
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()
        
        except Exception as e:
            logger.warning(f"Error during browser cleanup: {e}")
        
        finally:
            self._page = None
            self._context = None
            self._browser = None
            self._playwright = None
            self._is_started = False
            self._current_url = None
            
            logger.info("Browser closed successfully")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()