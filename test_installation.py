#!/usr/bin/env python3
"""
Installation test for LangGraph Chrome Tools.

This script verifies that the package is correctly installed and
all basic functionality works as expected.
"""

import asyncio
import sys
import traceback


def test_imports():
    """Test that all main imports work correctly."""
    print("🔍 Testing imports...")
    
    try:
        # Test core imports
        from langgraph_chrome_tools import (
            ChromeBrowser,
            ProfileManager,
            ProfileMode,
            get_all_chrome_tools,
        )
        print("  ✅ Core imports successful")
        
        # Test tool imports
        from langgraph_chrome_tools import (
            chrome_navigate_tool,
            chrome_click_tool,
            chrome_type_tool,
            chrome_extract_text_tool,
            chrome_screenshot_tool,
            chrome_wait_for_element_tool,
            chrome_evaluate_js_tool,
            chrome_scroll_tool,
        )
        print("  ✅ Tool imports successful")
        
        # Test utility imports
        from langgraph_chrome_tools.utils import (
            health_check,
            check_playwright_installation,
            install_playwright,
        )
        print("  ✅ Utility imports successful")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Unexpected error during imports: {e}")
        return False


def test_profile_management():
    """Test profile management functionality."""
    print("\n👤 Testing profile management...")
    
    try:
        from langgraph_chrome_tools import ProfileManager, ProfileMode
        
        # Create profile manager
        manager = ProfileManager()
        print("  ✅ ProfileManager created")
        
        # Test scratch profile creation
        scratch_profile = manager.create_profile(ProfileMode.SCRATCH)
        print(f"  ✅ Scratch profile created: {scratch_profile.name}")
        
        # Test profile listing
        profiles = manager.list_profiles()
        print(f"  ✅ Listed {len(profiles)} active profiles")
        
        # Test persistent profiles listing
        persistent = manager.list_persistent_profiles()
        print(f"  ✅ Found {len(persistent)} persistent profiles")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Profile management test failed: {e}")
        traceback.print_exc()
        return False


def test_health_check():
    """Test health check functionality."""
    print("\n🔍 Testing health check...")
    
    try:
        from langgraph_chrome_tools.utils import health_check, check_playwright_installation
        
        # Test Playwright installation check
        pw_status = check_playwright_installation()
        print(f"  ℹ️ Playwright ready: {pw_status.get('is_ready', False)}")
        
        # Test comprehensive health check
        health = health_check()
        print(f"  ℹ️ Overall status: {health['overall_status']}")
        
        if health['issues']:
            print(f"  ⚠️ Issues found: {len(health['issues'])}")
            for issue in health['issues'][:3]:  # Show first 3 issues
                print(f"    - {issue}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Health check test failed: {e}")
        traceback.print_exc()
        return False


def test_tool_availability():
    """Test that all tools are available and properly configured."""
    print("\n🔧 Testing tool availability...")
    
    try:
        from langgraph_chrome_tools import get_all_chrome_tools
        
        tools = get_all_chrome_tools()
        print(f"  ✅ Found {len(tools)} available tools")
        
        for tool in tools:
            print(f"    - {tool.name}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Tool availability test failed: {e}")
        traceback.print_exc()
        return False


async def test_basic_browser_creation():
    """Test basic browser instance creation (without starting)."""
    print("\n🌐 Testing browser creation...")
    
    try:
        from langgraph_chrome_tools import ChromeBrowser, ProfileManager, ProfileMode
        
        # Create profile for testing
        profile_manager = ProfileManager()
        profile_config = profile_manager.create_profile(ProfileMode.SCRATCH)
        print("  ✅ Test profile created")
        
        # Create browser instance (don't start it to avoid requiring Playwright setup)
        browser = ChromeBrowser(profile_config=profile_config)
        print("  ✅ Browser instance created")
        
        # Test properties
        print(f"  ✅ Browser started: {browser.is_started}")
        print(f"  ✅ Profile mode: {browser.profile_config.mode.value}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Browser creation test failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all installation tests."""
    print("🚀 LangGraph Chrome Tools - Installation Test")
    print("=" * 50)
    
    test_results = []
    
    # Run synchronous tests
    test_results.append(("Imports", test_imports()))
    test_results.append(("Profile Management", test_profile_management()))
    test_results.append(("Health Check", test_health_check()))
    test_results.append(("Tool Availability", test_tool_availability()))
    
    # Run asynchronous tests
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        browser_test_result = loop.run_until_complete(test_basic_browser_creation())
        test_results.append(("Browser Creation", browser_test_result))
        loop.close()
    except Exception as e:
        print(f"  ❌ Async test setup failed: {e}")
        test_results.append(("Browser Creation", False))
    
    # Summary
    print("\n📊 Test Results Summary")
    print("-" * 30)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1
    
    print("-" * 30)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! LangGraph Chrome Tools is ready to use.")
        print("\nNext steps:")
        print("  1. Run 'langgraph-chrome-setup' to install Playwright")
        print("  2. Check out examples/ for usage examples")
        print("  3. Read the README.md for full documentation")
        return 0
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Please check the errors above.")
        print("\nTroubleshooting:")
        print("  1. Ensure you installed with: pip install langgraph-chrome-tools")
        print("  2. Check Python version is 3.9+")
        print("  3. Try reinstalling: pip install --force-reinstall langgraph-chrome-tools")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)