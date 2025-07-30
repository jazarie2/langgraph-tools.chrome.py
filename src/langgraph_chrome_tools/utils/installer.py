"""Playwright installation utilities for LangGraph Chrome Tools."""

import subprocess
import sys
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from ..core.exceptions import PlaywrightInstallationError

logger = logging.getLogger(__name__)


def check_playwright_installation() -> Dict[str, Any]:
    """Check if Playwright and Chrome are properly installed.
    
    Returns:
        Dict[str, Any]: Installation status report
    """
    status = {
        "playwright_installed": False,
        "chromium_installed": False,
        "python_package_installed": False,
        "issues": [],
        "suggestions": [],
    }
    
    try:
        # Check if playwright Python package is installed
        import playwright
        status["python_package_installed"] = True
        status["playwright_version"] = getattr(playwright, "__version__", "unknown")
    except ImportError:
        status["issues"].append("Playwright Python package not installed")
        status["suggestions"].append("Run: pip install playwright")
        return status
    
    try:
        # Check if playwright CLI is available
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        
        if result.returncode == 0:
            status["playwright_installed"] = True
            status["cli_version"] = result.stdout.strip()
        else:
            status["issues"].append("Playwright CLI not working properly")
            status["suggestions"].append("Reinstall playwright: pip install --force-reinstall playwright")
    
    except subprocess.TimeoutExpired:
        status["issues"].append("Playwright CLI check timed out")
        status["suggestions"].append("Check system performance and try again")
    except Exception as e:
        status["issues"].append(f"Error checking Playwright CLI: {e}")
        status["suggestions"].append("Reinstall playwright: pip install --force-reinstall playwright")
    
    try:
        # Check if Chromium browser is installed
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "--dry-run", "chromium"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        if "chromium" in result.stdout.lower() and "already installed" in result.stdout.lower():
            status["chromium_installed"] = True
        elif result.returncode == 0:
            # Dry run successful, but browser may not be installed
            status["issues"].append("Chromium browser may not be installed")
            status["suggestions"].append("Run: playwright install chromium")
        else:
            status["issues"].append("Unable to check Chromium installation")
            status["suggestions"].append("Run: playwright install chromium")
    
    except subprocess.TimeoutExpired:
        status["issues"].append("Chromium check timed out")
        status["suggestions"].append("Run: playwright install chromium")
    except Exception as e:
        status["issues"].append(f"Error checking Chromium: {e}")
        status["suggestions"].append("Run: playwright install chromium")
    
    # Overall status
    status["is_ready"] = (
        status["python_package_installed"] and
        status["playwright_installed"] and
        status["chromium_installed"]
    )
    
    return status


def install_playwright(
    force: bool = False,
    with_deps: bool = True,
    browsers: Optional[list[str]] = None,
) -> Dict[str, Any]:
    """Install Playwright and browsers.
    
    Args:
        force: Whether to force reinstallation
        with_deps: Whether to install system dependencies
        browsers: List of browsers to install (default: ["chromium"])
        
    Returns:
        Dict[str, Any]: Installation result
    """
    if browsers is None:
        browsers = ["chromium"]
    
    result = {
        "success": False,
        "steps_completed": [],
        "errors": [],
        "suggestions": [],
    }
    
    try:
        # Step 1: Install/upgrade Python package
        logger.info("Installing Playwright Python package...")
        
        pip_cmd = [sys.executable, "-m", "pip", "install"]
        if force:
            pip_cmd.append("--force-reinstall")
        pip_cmd.append("playwright")
        
        process = subprocess.run(
            pip_cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutes
        )
        
        if process.returncode == 0:
            result["steps_completed"].append("Python package installed")
            logger.info("Playwright Python package installed successfully")
        else:
            error_msg = f"Failed to install Python package: {process.stderr}"
            result["errors"].append(error_msg)
            result["suggestions"].append("Check your internet connection and pip configuration")
            logger.error(error_msg)
            return result
        
        # Step 2: Install browsers
        logger.info(f"Installing browsers: {browsers}")
        
        install_cmd = [sys.executable, "-m", "playwright", "install"]
        if with_deps:
            install_cmd.append("--with-deps")
        install_cmd.extend(browsers)
        
        process = subprocess.run(
            install_cmd,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minutes
        )
        
        if process.returncode == 0:
            result["steps_completed"].append(f"Browsers installed: {browsers}")
            logger.info("Browsers installed successfully")
            result["success"] = True
        else:
            error_msg = f"Failed to install browsers: {process.stderr}"
            result["errors"].append(error_msg)
            result["suggestions"].extend([
                "Check your internet connection",
                "Ensure you have sufficient disk space",
                "Try running with sudo/administrator privileges if on Linux/macOS",
                "Check if antivirus is blocking the installation",
            ])
            logger.error(error_msg)
        
        # Step 3: Verify installation
        if result["success"]:
            logger.info("Verifying installation...")
            status = check_playwright_installation()
            
            if status["is_ready"]:
                result["steps_completed"].append("Installation verified")
                logger.info("Installation verification successful")
            else:
                result["success"] = False
                result["errors"].append("Installation verification failed")
                result["errors"].extend(status["issues"])
                result["suggestions"].extend(status["suggestions"])
                logger.error("Installation verification failed")
    
    except subprocess.TimeoutExpired as e:
        error_msg = f"Installation timed out: {e}"
        result["errors"].append(error_msg)
        result["suggestions"].extend([
            "Check your internet connection",
            "Try again with a better network connection",
            "Consider installing manually: pip install playwright && playwright install chromium",
        ])
        logger.error(error_msg)
    
    except Exception as e:
        error_msg = f"Unexpected error during installation: {e}"
        result["errors"].append(error_msg)
        result["suggestions"].extend([
            "Check system requirements",
            "Try manual installation",
            "Report the issue if problem persists",
        ])
        logger.error(error_msg)
    
    return result


def uninstall_playwright() -> Dict[str, Any]:
    """Uninstall Playwright (but preserve profiles).
    
    Returns:
        Dict[str, Any]: Uninstallation result
    """
    result = {
        "success": False,
        "steps_completed": [],
        "errors": [],
        "suggestions": [],
        "profiles_preserved": True,
    }
    
    try:
        logger.info("Uninstalling Playwright...")
        
        # Only uninstall the Python package
        # Browser binaries and profiles are left intact
        process = subprocess.run(
            [sys.executable, "-m", "pip", "uninstall", "-y", "playwright"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        
        if process.returncode == 0:
            result["steps_completed"].append("Python package uninstalled")
            result["success"] = True
            logger.info("Playwright uninstalled successfully")
        else:
            error_msg = f"Failed to uninstall: {process.stderr}"
            result["errors"].append(error_msg)
            logger.error(error_msg)
        
        # Note about profiles
        result["suggestions"].append(
            "Chrome profiles are preserved in ~/.langgraph_chrome_profiles/"
        )
        result["suggestions"].append(
            "To remove profiles manually: rm -rf ~/.langgraph_chrome_profiles/"
        )
    
    except Exception as e:
        error_msg = f"Error during uninstallation: {e}"
        result["errors"].append(error_msg)
        logger.error(error_msg)
    
    return result


def get_installation_info() -> Dict[str, Any]:
    """Get detailed installation information.
    
    Returns:
        Dict[str, Any]: Detailed installation info
    """
    info = {
        "system": {},
        "python": {},
        "playwright": {},
        "browsers": {},
    }
    
    # System info
    import platform
    info["system"] = {
        "platform": platform.platform(),
        "machine": platform.machine(),
        "python_version": platform.python_version(),
    }
    
    # Python info
    info["python"] = {
        "executable": sys.executable,
        "version": sys.version,
        "prefix": sys.prefix,
    }
    
    # Playwright info
    try:
        import playwright
        info["playwright"]["package_installed"] = True
        info["playwright"]["version"] = getattr(playwright, "__version__", "unknown")
        
        # Try to get browser paths
        try:
            from playwright._impl._driver import compute_driver_executable
            driver_path = compute_driver_executable()
            info["playwright"]["driver_path"] = str(driver_path)
        except Exception:
            info["playwright"]["driver_path"] = "unknown"
    
    except ImportError:
        info["playwright"]["package_installed"] = False
    
    # Browser info
    try:
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "--dry-run"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        if result.returncode == 0:
            info["browsers"]["status"] = "available"
            info["browsers"]["output"] = result.stdout
        else:
            info["browsers"]["status"] = "error"
            info["browsers"]["error"] = result.stderr
    
    except Exception as e:
        info["browsers"]["status"] = "unknown"
        info["browsers"]["error"] = str(e)
    
    return info