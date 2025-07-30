"""Health check and diagnosis utilities for LangGraph Chrome Tools."""

import logging
import subprocess
import sys
import psutil
from typing import Dict, Any, List, Optional

from ..core.exceptions import ChromeToolsError, PlaywrightInstallationError
from .installer import check_playwright_installation, install_playwright

logger = logging.getLogger(__name__)


def health_check() -> Dict[str, Any]:
    """Perform comprehensive health check of the Chrome tools system.
    
    Returns:
        Dict[str, Any]: Health check report with status and recommendations
    """
    report = {
        "overall_status": "unknown",
        "checks": {},
        "issues": [],
        "recommendations": [],
        "system_info": {},
    }
    
    # System information
    report["system_info"] = _get_system_info()
    
    # Check 1: Playwright installation
    playwright_status = check_playwright_installation()
    report["checks"]["playwright_installation"] = playwright_status
    
    if not playwright_status["is_ready"]:
        report["issues"].extend(playwright_status["issues"])
        report["recommendations"].extend(playwright_status["suggestions"])
    
    # Check 2: System resources
    resource_status = _check_system_resources()
    report["checks"]["system_resources"] = resource_status
    
    if not resource_status["sufficient"]:
        report["issues"].extend(resource_status["issues"])
        report["recommendations"].extend(resource_status["suggestions"])
    
    # Check 3: Chrome processes
    chrome_status = _check_chrome_processes()
    report["checks"]["chrome_processes"] = chrome_status
    
    if chrome_status["issues"]:
        report["issues"].extend(chrome_status["issues"])
        report["recommendations"].extend(chrome_status["suggestions"])
    
    # Check 4: Network connectivity
    network_status = _check_network_connectivity()
    report["checks"]["network_connectivity"] = network_status
    
    if not network_status["ok"]:
        report["issues"].extend(network_status["issues"])
        report["recommendations"].extend(network_status["suggestions"])
    
    # Check 5: File permissions
    permissions_status = _check_file_permissions()
    report["checks"]["file_permissions"] = permissions_status
    
    if not permissions_status["ok"]:
        report["issues"].extend(permissions_status["issues"])
        report["recommendations"].extend(permissions_status["suggestions"])
    
    # Determine overall status
    critical_issues = [
        not playwright_status["is_ready"],
        not resource_status["sufficient"],
        not permissions_status["ok"],
    ]
    
    if any(critical_issues):
        report["overall_status"] = "critical"
    elif report["issues"]:
        report["overall_status"] = "warning"
    else:
        report["overall_status"] = "healthy"
    
    return report


def suggest_reinstall(error: Optional[Exception] = None) -> Dict[str, Any]:
    """Suggest reinstall actions based on error context.
    
    Args:
        error: Optional exception that triggered the suggestion
        
    Returns:
        Dict[str, Any]: Reinstall suggestions and commands
    """
    suggestions = {
        "should_reinstall": False,
        "urgency": "low",
        "steps": [],
        "commands": [],
        "preserve_profiles": True,
        "estimated_time": "5-10 minutes",
    }
    
    # Analyze error if provided
    if error:
        error_str = str(error).lower()
        
        if any(keyword in error_str for keyword in [
            "executable doesn't exist",
            "browser not found",
            "chromium",
            "installation",
        ]):
            suggestions["should_reinstall"] = True
            suggestions["urgency"] = "high"
            suggestions["reason"] = "Browser executable missing or corrupted"
        
        elif any(keyword in error_str for keyword in [
            "timeout",
            "connection",
            "network",
        ]):
            suggestions["urgency"] = "medium"
            suggestions["reason"] = "Network-related issues detected"
        
        elif any(keyword in error_str for keyword in [
            "permission",
            "access denied",
            "cannot write",
        ]):
            suggestions["urgency"] = "medium"
            suggestions["reason"] = "Permission issues detected"
    
    # Check current installation status
    health_report = health_check()
    
    if health_report["overall_status"] == "critical":
        suggestions["should_reinstall"] = True
        suggestions["urgency"] = "high"
        if not suggestions.get("reason"):
            suggestions["reason"] = "Critical system issues detected"
    
    # Generate reinstall steps
    if suggestions["should_reinstall"] or suggestions["urgency"] == "high":
        suggestions["steps"] = [
            "Stop all running Chrome processes",
            "Uninstall current Playwright installation",
            "Clear temporary files and caches",
            "Reinstall Playwright with fresh browser binaries",
            "Verify installation",
            "Test basic functionality",
        ]
        
        suggestions["commands"] = [
            "# Stop Chrome processes (if any)",
            "pkill -f chrome || true",
            "",
            "# Uninstall current installation",
            "pip uninstall -y playwright",
            "",
            "# Reinstall Playwright",
            "pip install playwright",
            "playwright install chromium",
            "",
            "# Verify installation",
            "python -c 'import playwright; print(\"OK\")'",
            "playwright --version",
        ]
    
    else:
        suggestions["steps"] = [
            "Check system resources",
            "Verify network connectivity", 
            "Review error logs",
            "Try basic troubleshooting first",
        ]
        
        suggestions["commands"] = [
            "# Check Playwright status",
            "python -c 'from langgraph_chrome_tools.utils import health_check; print(health_check())'",
            "",
            "# Test basic functionality",
            "python -c 'from playwright.async_api import async_playwright; print(\"Playwright import OK\")'",
        ]
    
    return suggestions


def auto_fix_issues() -> Dict[str, Any]:
    """Attempt to automatically fix common issues.
    
    Returns:
        Dict[str, Any]: Auto-fix results
    """
    results = {
        "success": False,
        "fixes_applied": [],
        "errors": [],
        "manual_steps_required": [],
    }
    
    try:
        # Run health check first
        health_report = health_check()
        
        # Auto-fix 1: Reinstall if critically broken
        playwright_status = health_report["checks"].get("playwright_installation", {})
        
        if not playwright_status.get("is_ready", False):
            logger.info("Attempting to fix Playwright installation...")
            
            install_result = install_playwright(force=True)
            
            if install_result["success"]:
                results["fixes_applied"].append("Reinstalled Playwright and browsers")
            else:
                results["errors"].extend(install_result["errors"])
                results["manual_steps_required"].extend([
                    "Manual Playwright installation required",
                    "Check system requirements and dependencies",
                ])
        
        # Auto-fix 2: Kill hanging Chrome processes
        chrome_status = health_report["checks"].get("chrome_processes", {})
        
        if chrome_status.get("hanging_processes"):
            logger.info("Attempting to clean up hanging Chrome processes...")
            
            try:
                cleanup_result = _cleanup_chrome_processes()
                if cleanup_result["cleaned"]:
                    results["fixes_applied"].append(f"Cleaned up {cleanup_result['count']} Chrome processes")
            except Exception as e:
                results["errors"].append(f"Failed to cleanup Chrome processes: {e}")
                results["manual_steps_required"].append("Manually kill Chrome processes")
        
        # Auto-fix 3: Clear temporary files
        try:
            logger.info("Clearing temporary files...")
            cleared_count = _clear_temp_files()
            if cleared_count > 0:
                results["fixes_applied"].append(f"Cleared {cleared_count} temporary files")
        except Exception as e:
            results["errors"].append(f"Failed to clear temp files: {e}")
        
        # Check if fixes were successful
        if results["fixes_applied"] and not results["errors"]:
            results["success"] = True
        
    except Exception as e:
        results["errors"].append(f"Auto-fix failed: {e}")
        logger.error(f"Auto-fix error: {e}")
    
    return results


def _get_system_info() -> Dict[str, Any]:
    """Get system information."""
    import platform
    
    return {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "architecture": platform.architecture(),
        "cpu_count": psutil.cpu_count(),
        "memory_total": psutil.virtual_memory().total,
        "disk_free": psutil.disk_usage("/").free,
    }


def _check_system_resources() -> Dict[str, Any]:
    """Check if system has sufficient resources."""
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    
    status = {
        "sufficient": True,
        "memory_available": memory.available,
        "disk_free": disk.free,
        "issues": [],
        "suggestions": [],
    }
    
    # Check memory (need at least 1GB available)
    if memory.available < 1024 * 1024 * 1024:  # 1GB
        status["sufficient"] = False
        status["issues"].append("Insufficient memory available")
        status["suggestions"].append("Close other applications to free memory")
    
    # Check disk space (need at least 2GB free)
    if disk.free < 2 * 1024 * 1024 * 1024:  # 2GB
        status["sufficient"] = False
        status["issues"].append("Insufficient disk space")
        status["suggestions"].append("Free up disk space")
    
    return status


def _check_chrome_processes() -> Dict[str, Any]:
    """Check for Chrome processes that might interfere."""
    status = {
        "running_processes": [],
        "hanging_processes": [],
        "issues": [],
        "suggestions": [],
    }
    
    chrome_processes = []
    
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            if proc.info['name'] and 'chrom' in proc.info['name'].lower():
                chrome_processes.append({
                    "pid": proc.info['pid'],
                    "name": proc.info['name'],
                    "cmdline": ' '.join(proc.info['cmdline'] or []),
                })
        
        status["running_processes"] = chrome_processes
        
        # Check for potentially hanging processes
        if len(chrome_processes) > 5:
            status["hanging_processes"] = chrome_processes
            status["issues"].append(f"Many Chrome processes running ({len(chrome_processes)})")
            status["suggestions"].append("Consider restarting Chrome or killing hanging processes")
    
    except Exception as e:
        status["issues"].append(f"Error checking Chrome processes: {e}")
    
    return status


def _check_network_connectivity() -> Dict[str, Any]:
    """Check network connectivity for browser downloads."""
    status = {
        "ok": True,
        "issues": [],
        "suggestions": [],
    }
    
    try:
        # Simple connectivity check
        import socket
        socket.create_connection(("8.8.8.8", 53), timeout=5)
    except Exception:
        status["ok"] = False
        status["issues"].append("Network connectivity issues")
        status["suggestions"].extend([
            "Check internet connection",
            "Check firewall settings",
            "Try using a VPN if behind corporate firewall",
        ])
    
    return status


def _check_file_permissions() -> Dict[str, Any]:
    """Check file system permissions."""
    status = {
        "ok": True,
        "issues": [],
        "suggestions": [],
    }
    
    try:
        # Check if we can write to home directory
        from pathlib import Path
        home_dir = Path.home()
        test_file = home_dir / ".langgraph_test"
        
        test_file.write_text("test")
        test_file.unlink()
        
    except Exception as e:
        status["ok"] = False
        status["issues"].append(f"File permission issues: {e}")
        status["suggestions"].extend([
            "Check file system permissions",
            "Ensure user has write access to home directory",
            "Try running with appropriate permissions",
        ])
    
    return status


def _cleanup_chrome_processes() -> Dict[str, Any]:
    """Clean up hanging Chrome processes."""
    result = {
        "cleaned": False,
        "count": 0,
        "errors": [],
    }
    
    try:
        killed_count = 0
        
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] and 'chrom' in proc.info['name'].lower():
                try:
                    proc.terminate()
                    proc.wait(timeout=5)
                    killed_count += 1
                except Exception:
                    # Try force kill
                    try:
                        proc.kill()
                        killed_count += 1
                    except Exception as e:
                        result["errors"].append(f"Failed to kill process {proc.info['pid']}: {e}")
        
        result["count"] = killed_count
        result["cleaned"] = killed_count > 0
        
    except Exception as e:
        result["errors"].append(f"Error during cleanup: {e}")
    
    return result


def _clear_temp_files() -> int:
    """Clear temporary files related to Chrome/Playwright."""
    import tempfile
    import shutil
    from pathlib import Path
    
    cleared_count = 0
    temp_dir = Path(tempfile.gettempdir())
    
    # Look for Chrome/Playwright temp files
    patterns = ["chrome_profile_*", "playwright-*", "tmp*chrome*"]
    
    for pattern in patterns:
        for temp_path in temp_dir.glob(pattern):
            try:
                if temp_path.is_file():
                    temp_path.unlink()
                    cleared_count += 1
                elif temp_path.is_dir():
                    shutil.rmtree(temp_path)
                    cleared_count += 1
            except Exception:
                # Ignore cleanup errors
                pass
    
    return cleared_count