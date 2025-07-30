"""Browser instance management for LangGraph Chrome Tools.

This module provides a global browser manager that allows tools to share
browser instances and manages their lifecycle automatically.
"""

import asyncio
import logging
import weakref
from typing import Dict, Optional, Any
from contextlib import asynccontextmanager

from ..core.browser import ChromeBrowser
from ..core.exceptions import ChromeToolsError, BrowserNotStartedError
from ..profiles.manager import ProfileManager, ProfileMode, ProfileConfig

logger = logging.getLogger(__name__)

# Global browser instance registry
_browser_instances: Dict[str, ChromeBrowser] = {}
_default_browser_id = "default"


async def get_browser_instance(browser_id: Optional[str] = None) -> ChromeBrowser:
    """Get or create a browser instance.
    
    Args:
        browser_id: Browser instance ID (uses default if not provided)
        
    Returns:
        ChromeBrowser: Browser instance
        
    Raises:
        BrowserNotStartedError: If browser is not started
        ChromeToolsError: If browser creation fails
    """
    instance_id = browser_id or _default_browser_id
    
    # Check if instance exists and is started
    if instance_id in _browser_instances:
        browser = _browser_instances[instance_id]
        if browser.is_started:
            return browser
        else:
            # Browser exists but is not started - try to start it
            try:
                await browser.start()
                return browser
            except Exception as e:
                # Remove dead instance and create new one
                logger.warning(f"Failed to restart browser {instance_id}: {e}")
                del _browser_instances[instance_id]
    
    # Create new browser instance
    return await create_browser_instance(browser_id=instance_id)


async def create_browser_instance(
    browser_id: Optional[str] = None,
    profile_config: Optional[ProfileConfig] = None,
    profile_mode: ProfileMode = ProfileMode.SCRATCH,
    profile_name: Optional[str] = None,
    visible: bool = False,
    **kwargs: Any,
) -> ChromeBrowser:
    """Create a new browser instance.
    
    Args:
        browser_id: Browser instance ID (uses default if not provided)
        profile_config: Pre-configured profile (overrides other profile settings)
        profile_mode: Profile mode to use if profile_config is not provided
        profile_name: Profile name (for persistent profiles)
        visible: Whether to show browser window
        **kwargs: Additional browser options
        
    Returns:
        ChromeBrowser: Created and started browser instance
        
    Raises:
        ChromeToolsError: If browser creation fails
    """
    instance_id = browser_id or _default_browser_id
    
    try:
        # Close existing instance if it exists
        if instance_id in _browser_instances:
            await close_browser_instance(instance_id)
        
        # Set up profile configuration
        if not profile_config:
            profile_manager = ProfileManager()
            profile_config = profile_manager.create_profile(
                mode=profile_mode,
                name=profile_name,
                visible=visible,
            )
        
        # Create browser instance
        browser = ChromeBrowser(
            profile_config=profile_config,
            **kwargs,
        )
        
        # Start browser
        await browser.start()
        
        # Store in registry
        _browser_instances[instance_id] = browser
        
        logger.info(f"Created browser instance: {instance_id}")
        return browser
        
    except Exception as e:
        raise ChromeToolsError(
            f"Failed to create browser instance '{instance_id}': {e}",
            context={"browser_id": instance_id},
            suggestions=[
                "Check if Playwright is properly installed",
                "Verify profile configuration",
                "Try using a different profile mode",
            ],
        ) from e


async def close_browser_instance(browser_id: Optional[str] = None) -> bool:
    """Close a browser instance.
    
    Args:
        browser_id: Browser instance ID (uses default if not provided)
        
    Returns:
        bool: True if browser was closed, False if not found
    """
    instance_id = browser_id or _default_browser_id
    
    if instance_id not in _browser_instances:
        return False
    
    try:
        browser = _browser_instances[instance_id]
        await browser.close()
        del _browser_instances[instance_id]
        logger.info(f"Closed browser instance: {instance_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error closing browser {instance_id}: {e}")
        # Remove from registry even if close failed
        del _browser_instances[instance_id]
        return False


async def close_all_browser_instances() -> int:
    """Close all browser instances.
    
    Returns:
        int: Number of browsers closed
    """
    instance_ids = list(_browser_instances.keys())
    closed_count = 0
    
    for instance_id in instance_ids:
        if await close_browser_instance(instance_id):
            closed_count += 1
    
    logger.info(f"Closed {closed_count} browser instances")
    return closed_count


def list_browser_instances() -> Dict[str, Dict[str, Any]]:
    """List all browser instances and their status.
    
    Returns:
        Dict[str, Dict[str, Any]]: Browser instances and their info
    """
    instances = {}
    
    for instance_id, browser in _browser_instances.items():
        instances[instance_id] = {
            "instance_id": instance_id,
            "is_started": browser.is_started,
            "current_url": browser.current_url,
            "profile_name": browser.profile_config.name,
            "profile_mode": browser.profile_config.mode.value,
            "visible": browser.profile_config.visible,
        }
    
    return instances


@asynccontextmanager
async def managed_browser(
    browser_id: Optional[str] = None,
    auto_close: bool = True,
    **kwargs: Any,
):
    """Context manager for browser instances.
    
    Args:
        browser_id: Browser instance ID
        auto_close: Whether to automatically close browser on exit
        **kwargs: Arguments for browser creation
        
    Examples:
        >>> async with managed_browser() as browser:
        ...     await browser.navigate("https://example.com")
        ...     # Browser automatically closed on exit
        
        >>> async with managed_browser(auto_close=False) as browser:
        ...     await browser.navigate("https://example.com")
        ...     # Browser remains open
    """
    browser = None
    try:
        browser = await create_browser_instance(browser_id=browser_id, **kwargs)
        yield browser
    finally:
        if browser and auto_close:
            await close_browser_instance(browser_id)


# Cleanup function for when the module is unloaded
async def cleanup_all_browsers():
    """Clean up all browser instances."""
    await close_all_browser_instances()


# Register cleanup function to run on exit
import atexit
atexit.register(lambda: asyncio.create_task(cleanup_all_browsers()))