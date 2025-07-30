#!/usr/bin/env python3
"""
Basic usage example for LangGraph Chrome Tools.

This example demonstrates how to use the Chrome automation tools with LangGraph
for web scraping and automation tasks.
"""

import asyncio
import logging
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from typing import TypedDict, Annotated

# Import LangGraph Chrome Tools
from langgraph_chrome_tools import (
    chrome_navigate_tool,
    chrome_click_tool,
    chrome_type_tool,
    chrome_extract_text_tool,
    chrome_screenshot_tool,
    ProfileManager,
    ProfileMode,
    get_all_chrome_tools,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Define the workflow state
class WebScrapingState(TypedDict):
    """State for web scraping workflow."""
    messages: Annotated[list[BaseMessage], add_messages]
    target_url: str
    search_query: str
    extracted_data: str
    screenshot_path: str
    errors: list[str]


async def navigate_to_site(state: WebScrapingState) -> dict:
    """Navigate to the target website."""
    logger.info(f"Navigating to: {state['target_url']}")
    
    try:
        # Navigate to the website
        result = await chrome_navigate_tool.ainvoke({
            "url": state["target_url"],
            "wait_until": "networkidle"
        })
        
        import json
        nav_result = json.loads(result)
        
        if nav_result["success"]:
            message = AIMessage(content=f"Successfully navigated to {nav_result['final_url']}")
            return {"messages": [message]}
        else:
            error_msg = f"Navigation failed: {nav_result['message']}"
            return {
                "messages": [AIMessage(content=error_msg)],
                "errors": [error_msg]
            }
    
    except Exception as e:
        error_msg = f"Error during navigation: {e}"
        logger.error(error_msg)
        return {
            "messages": [AIMessage(content=error_msg)],
            "errors": [error_msg]
        }


async def search_content(state: WebScrapingState) -> dict:
    """Search for content on the page."""
    search_query = state.get("search_query", "")
    if not search_query:
        return {"messages": [AIMessage(content="No search query provided")]}
    
    logger.info(f"Searching for: {search_query}")
    
    try:
        # Look for a search box (try common selectors)
        search_selectors = [
            "input[type='search']",
            "input[name='q']", 
            "input[name='search']",
            "#search",
            ".search-input"
        ]
        
        search_success = False
        for selector in search_selectors:
            try:
                # Try to type in the search box
                type_result = await chrome_type_tool.ainvoke({
                    "selector": selector,
                    "text": search_query,
                    "timeout": 5
                })
                
                import json
                type_data = json.loads(type_result)
                
                if type_data["success"]:
                    logger.info(f"Successfully typed in search box: {selector}")
                    
                    # Try to click search button or press Enter
                    search_buttons = [
                        "button[type='submit']",
                        "input[type='submit']",
                        "button:contains('Search')",
                        ".search-button"
                    ]
                    
                    for button_selector in search_buttons:
                        try:
                            click_result = await chrome_click_tool.ainvoke({
                                "selector": button_selector,
                                "timeout": 2
                            })
                            
                            click_data = json.loads(click_result)
                            if click_data["success"]:
                                search_success = True
                                break
                        except Exception:
                            continue
                    
                    if search_success:
                        break
                        
            except Exception:
                continue
        
        if search_success:
            message = AIMessage(content=f"Search performed for: {search_query}")
            return {"messages": [message]}
        else:
            message = AIMessage(content="No search box found, will extract page content directly")
            return {"messages": [message]}
    
    except Exception as e:
        error_msg = f"Error during search: {e}"
        logger.error(error_msg)
        return {
            "messages": [AIMessage(content=error_msg)],
            "errors": [error_msg]
        }


async def extract_data(state: WebScrapingState) -> dict:
    """Extract text content from the page."""
    logger.info("Extracting page content...")
    
    try:
        # Extract main content
        extract_result = await chrome_extract_text_tool.ainvoke({
            "selector": "main, article, .content, #content"
        })
        
        import json
        extract_data = json.loads(extract_result)
        
        if extract_data["success"]:
            extracted_text = extract_data["text_content"]
            word_count = extract_data["word_count"]
            
            message = AIMessage(
                content=f"Extracted {word_count} words from the page"
            )
            
            return {
                "messages": [message],
                "extracted_data": extracted_text
            }
        else:
            # Try extracting from entire page
            extract_result = await chrome_extract_text_tool.ainvoke({})
            extract_data = json.loads(extract_result)
            
            if extract_data["success"]:
                extracted_text = extract_data["text_content"]
                word_count = extract_data["word_count"]
                
                message = AIMessage(
                    content=f"Extracted {word_count} words from entire page"
                )
                
                return {
                    "messages": [message],
                    "extracted_data": extracted_text
                }
            else:
                error_msg = "Failed to extract any content from the page"
                return {
                    "messages": [AIMessage(content=error_msg)],
                    "errors": [error_msg]
                }
    
    except Exception as e:
        error_msg = f"Error during content extraction: {e}"
        logger.error(error_msg)
        return {
            "messages": [AIMessage(content=error_msg)],
            "errors": [error_msg]
        }


async def take_screenshot(state: WebScrapingState) -> dict:
    """Take a screenshot of the current page."""
    logger.info("Taking screenshot...")
    
    try:
        screenshot_path = "/tmp/langgraph_chrome_screenshot.png"
        
        screenshot_result = await chrome_screenshot_tool.ainvoke({
            "path": screenshot_path,
            "full_page": True
        })
        
        import json
        screenshot_data = json.loads(screenshot_result)
        
        if screenshot_data["success"]:
            message = AIMessage(
                content=f"Screenshot saved to: {screenshot_data['screenshot_path']}"
            )
            
            return {
                "messages": [message],
                "screenshot_path": screenshot_data["screenshot_path"]
            }
        else:
            error_msg = f"Screenshot failed: {screenshot_data['message']}"
            return {
                "messages": [AIMessage(content=error_msg)],
                "errors": [error_msg]
            }
    
    except Exception as e:
        error_msg = f"Error taking screenshot: {e}"
        logger.error(error_msg)
        return {
            "messages": [AIMessage(content=error_msg)],
            "errors": [error_msg]
        }


async def create_workflow() -> StateGraph:
    """Create the web scraping workflow."""
    workflow = StateGraph(WebScrapingState)
    
    # Add nodes
    workflow.add_node("navigate", navigate_to_site)
    workflow.add_node("search", search_content)
    workflow.add_node("extract", extract_data)
    workflow.add_node("screenshot", take_screenshot)
    
    # Define the flow
    workflow.add_edge(START, "navigate")
    workflow.add_edge("navigate", "search")
    workflow.add_edge("search", "extract") 
    workflow.add_edge("extract", "screenshot")
    workflow.add_edge("screenshot", END)
    
    return workflow


async def run_web_scraping_example():
    """Run the web scraping example."""
    print("🕷️ LangGraph Chrome Tools - Web Scraping Example")
    print("=" * 50)
    
    # Create workflow
    workflow = await create_workflow()
    app = workflow.compile()
    
    # Example 1: Scrape a news website
    print("\n📰 Example 1: Scraping BBC News")
    print("-" * 30)
    
    initial_state = {
        "messages": [HumanMessage(content="Scrape BBC News for technology articles")],
        "target_url": "https://www.bbc.com/news/technology",
        "search_query": "",
        "extracted_data": "",
        "screenshot_path": "",
        "errors": []
    }
    
    try:
        result = await app.ainvoke(initial_state)
        
        print(f"✅ Scraping completed!")
        print(f"📄 Extracted data length: {len(result.get('extracted_data', ''))} characters")
        print(f"📸 Screenshot: {result.get('screenshot_path', 'Not taken')}")
        
        if result.get("errors"):
            print(f"⚠️ Errors: {len(result['errors'])}")
            for error in result["errors"]:
                print(f"  - {error}")
    
    except Exception as e:
        print(f"❌ Example 1 failed: {e}")
    
    # Example 2: Search Wikipedia
    print("\n📚 Example 2: Searching Wikipedia")
    print("-" * 30)
    
    wikipedia_state = {
        "messages": [HumanMessage(content="Search Wikipedia for information about Python programming")],
        "target_url": "https://en.wikipedia.org",
        "search_query": "Python programming language",
        "extracted_data": "",
        "screenshot_path": "",
        "errors": []
    }
    
    try:
        result = await app.ainvoke(wikipedia_state)
        
        print(f"✅ Wikipedia search completed!")
        print(f"📄 Extracted data length: {len(result.get('extracted_data', ''))} characters")
        print(f"📸 Screenshot: {result.get('screenshot_path', 'Not taken')}")
        
        # Show a snippet of the extracted content
        content = result.get('extracted_data', '')
        if content:
            snippet = content[:200] + "..." if len(content) > 200 else content
            print(f"📝 Content snippet: {snippet}")
    
    except Exception as e:
        print(f"❌ Example 2 failed: {e}")
    
    print("\n🎉 Web scraping examples completed!")


async def demonstrate_profile_management():
    """Demonstrate different profile management options."""
    print("\n👤 Profile Management Demo")
    print("=" * 30)
    
    # Create profile manager
    profile_manager = ProfileManager()
    
    # Example 1: Scratch profile (temporary)
    print("🗑️ Creating scratch profile...")
    scratch_profile = profile_manager.create_profile(ProfileMode.SCRATCH)
    print(f"  Profile: {scratch_profile.name} ({scratch_profile.mode.value})")
    print(f"  Path: {scratch_profile.path}")
    
    # Example 2: Persistent profile
    print("\n💾 Creating persistent profile...")
    persistent_profile = profile_manager.create_profile(
        ProfileMode.PERSISTENT, 
        name="my_automation_profile"
    )
    print(f"  Profile: {persistent_profile.name} ({persistent_profile.mode.value})")
    print(f"  Path: {persistent_profile.path}")
    
    # Example 3: Visible profile for debugging
    print("\n👁️ Creating visible profile for debugging...")
    visible_profile = profile_manager.create_profile(
        ProfileMode.VISIBLE,
        name="debug_profile"
    )
    print(f"  Profile: {visible_profile.name} ({visible_profile.mode.value})")
    print(f"  Visible: {visible_profile.visible}")
    
    # List all profiles
    print("\n📋 All active profiles:")
    profiles = profile_manager.list_profiles()
    for profile_id, config in profiles.items():
        print(f"  - {profile_id}: {config.mode.value}")
    
    # List persistent profiles
    print("\n💾 Persistent profiles on disk:")
    persistent_profiles = profile_manager.list_persistent_profiles()
    for profile_name in persistent_profiles:
        print(f"  - {profile_name}")


async def demonstrate_tools():
    """Demonstrate individual tools."""
    print("\n🔧 Individual Tools Demo")
    print("=" * 30)
    
    # Get all available tools
    tools = get_all_chrome_tools()
    print(f"📦 Available tools: {len(tools)}")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description}")
    
    # Example navigation
    print("\n🧭 Navigation example...")
    try:
        result = await chrome_navigate_tool.ainvoke({
            "url": "https://httpbin.org/html",
            "wait_until": "load"
        })
        
        import json
        nav_data = json.loads(result)
        print(f"  Status: {'✅ Success' if nav_data['success'] else '❌ Failed'}")
        print(f"  URL: {nav_data.get('final_url', 'unknown')}")
        print(f"  Title: {nav_data.get('title', 'unknown')}")
    
    except Exception as e:
        print(f"  ❌ Navigation failed: {e}")


async def main():
    """Main example runner."""
    print("🚀 LangGraph Chrome Tools - Comprehensive Examples")
    print("=" * 60)
    
    try:
        # Demonstrate profile management
        await demonstrate_profile_management()
        
        # Demonstrate individual tools
        await demonstrate_tools()
        
        # Run web scraping workflow
        await run_web_scraping_example()
        
    except KeyboardInterrupt:
        print("\n👋 Examples interrupted by user")
    except Exception as e:
        print(f"\n❌ Examples failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✨ Thank you for trying LangGraph Chrome Tools!")


if __name__ == "__main__":
    asyncio.run(main())