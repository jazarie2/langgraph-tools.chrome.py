"""Exception classes for LangGraph Chrome Tools.

This module defines custom exceptions for various error scenarios that can occur
during Chrome automation, including installation issues, browser startup problems,
and profile management errors.
"""

from typing import Optional, Dict, Any


class ChromeToolsError(Exception):
    """Base exception for all Chrome tools related errors.
    
    This is the base class for all custom exceptions in the langgraph-chrome-tools
    package. It provides additional context and suggestions for error resolution.
    
    Attributes:
        message: The error message
        context: Additional context about the error
        suggestions: List of suggested actions to resolve the error
    """
    
    def __init__(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        suggestions: Optional[list[str]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.context = context or {}
        self.suggestions = suggestions or []
    
    def __str__(self) -> str:
        """Format error message with context and suggestions."""
        result = [f"ChromeToolsError: {self.message}"]
        
        if self.context:
            result.append("Context:")
            for key, value in self.context.items():
                result.append(f"  {key}: {value}")
        
        if self.suggestions:
            result.append("Suggestions:")
            for suggestion in self.suggestions:
                result.append(f"  - {suggestion}")
        
        return "\n".join(result)


class BrowserNotStartedError(ChromeToolsError):
    """Raised when attempting to use browser functionality before starting the browser.
    
    This error occurs when trying to perform browser operations (navigation, clicking,
    etc.) before the browser has been properly initialized and started.
    """
    
    def __init__(self, operation: str) -> None:
        super().__init__(
            f"Cannot perform '{operation}' - browser not started",
            context={"operation": operation},
            suggestions=[
                "Call browser.start() before using browser tools",
                "Ensure browser initialization completed successfully",
                "Check if there were any startup errors in the logs",
            ]
        )


class ProfileError(ChromeToolsError):
    """Raised when there are issues with Chrome profile management.
    
    This can include problems creating, loading, or switching between Chrome profiles.
    """
    
    def __init__(
        self,
        message: str,
        profile_path: Optional[str] = None,
        profile_mode: Optional[str] = None,
    ) -> None:
        context = {}
        if profile_path:
            context["profile_path"] = profile_path
        if profile_mode:
            context["profile_mode"] = profile_mode
            
        suggestions = [
            "Check if the profile directory exists and is accessible",
            "Ensure Chrome is not already running with this profile",
            "Try using a different profile mode (scratch, no-profile, visible)",
            "Manually remove corrupted profile directories if needed",
        ]
        
        super().__init__(message, context=context, suggestions=suggestions)


class PlaywrightInstallationError(ChromeToolsError):
    """Raised when Playwright or its browsers are not properly installed.
    
    This error occurs when Playwright cannot find the required browser binaries
    or when there are issues with the Playwright installation itself.
    """
    
    def __init__(
        self,
        message: str,
        missing_component: Optional[str] = None,
        installation_command: Optional[str] = None,
    ) -> None:
        context = {}
        if missing_component:
            context["missing_component"] = missing_component
        if installation_command:
            context["installation_command"] = installation_command
            
        suggestions = [
            "Run: playwright install chromium",
            "Run: langgraph-chrome-install (if using our CLI)",
            "Ensure Playwright is properly installed: pip install playwright",
            "Check system dependencies for your OS",
            "If issues persist, try: playwright install --force chromium",
        ]
        
        if installation_command:
            suggestions.insert(0, f"Run: {installation_command}")
            
        super().__init__(message, context=context, suggestions=suggestions)


class NetworkError(ChromeToolsError):
    """Raised when network-related operations fail.
    
    This includes timeouts, connection failures, and other network-related issues
    during browser automation.
    """
    
    def __init__(
        self,
        message: str,
        url: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> None:
        context = {}
        if url:
            context["url"] = url
        if timeout:
            context["timeout_seconds"] = timeout
            
        suggestions = [
            "Check your internet connection",
            "Verify the URL is accessible",
            "Try increasing the timeout value",
            "Check if the website is behind a firewall or requires authentication",
        ]
        
        super().__init__(message, context=context, suggestions=suggestions)


class ElementNotFoundError(ChromeToolsError):
    """Raised when a required page element cannot be found.
    
    This occurs during browser automation when trying to interact with elements
    that don't exist on the page or haven't loaded yet.
    """
    
    def __init__(
        self,
        selector: str,
        page_url: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> None:
        context = {
            "selector": selector,
        }
        if page_url:
            context["page_url"] = page_url
        if timeout:
            context["timeout_seconds"] = timeout
            
        suggestions = [
            "Verify the element selector is correct",
            "Wait for the page to fully load before interacting",
            "Use chrome_wait_for_element_tool to wait for dynamic content",
            "Check if the element is in an iframe",
            "Inspect the page to ensure the element exists",
        ]
        
        super().__init__(
            f"Element not found: {selector}",
            context=context,
            suggestions=suggestions,
        )


class JavaScriptError(ChromeToolsError):
    """Raised when JavaScript execution fails in the browser.
    
    This occurs when custom JavaScript code executed via chrome_evaluate_js_tool
    encounters runtime errors.
    """
    
    def __init__(
        self,
        script: str,
        error_message: str,
        page_url: Optional[str] = None,
    ) -> None:
        context = {
            "script": script,
            "javascript_error": error_message,
        }
        if page_url:
            context["page_url"] = page_url
            
        suggestions = [
            "Check the JavaScript syntax",
            "Ensure all required variables and functions are available",
            "Test the script in browser developer console first",
            "Handle potential null/undefined values in the script",
        ]
        
        super().__init__(
            f"JavaScript execution failed: {error_message}",
            context=context,
            suggestions=suggestions,
        )