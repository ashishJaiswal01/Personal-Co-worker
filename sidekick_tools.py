from playwright.async_api import async_playwright
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from dotenv import load_dotenv
import os
import requests
from langchain_core.tools import Tool
from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_experimental.tools import PythonREPLTool
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper



load_dotenv(override=True)
pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_user = os.getenv("PUSHOVER_USER")
pushover_url = "https://api.pushover.net/1/messages.json"

# Initialize serper only if API key is available
serper = None
if os.getenv("SERPER_API_KEY"):
    serper = GoogleSerperAPIWrapper()
else:
    print("Warning: SERPER_API_KEY not set. Google search tool will not be available.")

async def playwright_tools():
    import asyncio
    try:
        # Add a timeout to prevent hanging in headless environments
        playwright = await asyncio.wait_for(async_playwright().start(), timeout=30)
        browser = await asyncio.wait_for(
            playwright.chromium.launch(headless=True),
            timeout=30
        )
        toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
        return toolkit.get_tools(), browser, playwright
    except asyncio.TimeoutError:
        print("Warning: Playwright initialization timed out. Browser tools will not be available.")
        # Return empty tools list so app can continue without browser
        return [], None, None
    except Exception as e:
        print(f"Warning: Failed to initialize Playwright: {e}. Browser tools will not be available.")
        return [], None, None


def push(text: str):
    """Send a push notification to the user"""
    requests.post(pushover_url, data = {"token": pushover_token, "user": pushover_user, "message": text})
    return "success"


def get_file_tools():
    toolkit = FileManagementToolkit(root_dir="sandbox")
    return toolkit.get_tools()


async def other_tools():
    push_tool = Tool(name="send_push_notification", func=push, description="Use this tool when you want to send a push notification")
    file_tools = get_file_tools()

    tools_list = file_tools + [push_tool]
    
    if serper:
        tool_search = Tool(
            name="search",
            func=serper.run,
            description="Use this tool when you want to get the results of an online web search"
        )
        tools_list.append(tool_search)

    wikipedia = WikipediaAPIWrapper()
    wiki_tool = WikipediaQueryRun(api_wrapper=wikipedia)

    python_repl = PythonREPLTool()
    
    return tools_list + [python_repl, wiki_tool]

