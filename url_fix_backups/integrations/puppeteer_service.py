#!/usr / bin / env python3
""""""
Puppeteer Service for Web AI Integration
Handles browser automation for interacting with web AI platforms
""""""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

@dataclass


class BrowserSession:
    """Browser session information"""

    session_id: str
    platform: str
    url: str
    created_at: datetime
    last_used: datetime
    is_active: bool = True


class PuppeteerService:
    """Service for managing Puppeteer browser automation"""


    def __init__(self, config: Dict = None):
        """Initialize Puppeteer service"""
        self.config = config or self._get_default_config()
        self.logger = self._setup_logging()
        self.sessions = {}
        self.mcp_available = True  # Will check MCP availability


    def _get_default_config(self) -> Dict:
        """Get default configuration with macOS compatibility fixes"""
        return {
            "browser": {
                "headless": False,  # Set to False for debugging
                "width": 1280,
                    "height": 720,
                    "timeout": 30000,
                    "args": [
                    "--no - sandbox",
                        "--disable - setuid - sandbox",
                        "--disable - dev - shm - usage",
                        "--disable - accelerated - 2d - canvas",
                        "--no - first - run",
                        "--no - zygote",
                        "--disable - gpu",
                        "--disable - blink - features = AutomationControlled",
                        "--user - agent = Mozilla / 5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit / 537.36 (KHTML,"
# BRACKET_SURGEON: disabled
#     like Gecko) Chrome / 120.0.0.0 Safari / 537.36","
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         ],
                    "ignoreDefaultArgs": ["--disable - extensions"],
                    "slowMo": 100,
# BRACKET_SURGEON: disabled
#                     },
                "retry": {"max_attempts": 3, "delay": 2},
                "selectors": {
                "chatgpt": {
                    "input": 'textarea[data - id="root"]',
                        "send_button": 'button[data - testid="send - button"]',
                        "response": '[data - message - author - role="assistant"] .markdown',
                        "loading": ".result - streaming",
# BRACKET_SURGEON: disabled
#                         },
                    "gemini": {
                    "input": '.ql - editor[contenteditable="true"]',
                        "send_button": 'button[aria - label="Send message"]',
                        "response": "[data - response - index] .markdown",
                        "loading": ".loading - indicator",
# BRACKET_SURGEON: disabled
#                         },
                    "claude": {
                    "input": 'div[contenteditable="true"][data - testid="chat - input"]',
                        "send_button": 'button[aria - label="Send Message"]',
                        "response": '[data - testid="conversation"] .font - claude - message',
                        "loading": ".thinking - indicator",
# BRACKET_SURGEON: disabled
#                         },
# BRACKET_SURGEON: disabled
#                     },
# BRACKET_SURGEON: disabled
#                 }


    def _setup_logging(self) -> logging.Logger:
        """Setup logging"""
        logger = logging.getLogger("PuppeteerService")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger


    async def navigate_to_platform(self, platform: str, url: str) -> str:
        """Navigate to AI platform and return session ID"""
        session_id = f"{platform}_{int(time.time())}"

        try:
            self.logger.info(f"Navigating to {platform} at {url}")

            # Use MCP Puppeteer to navigate

            from integrations.mcp_client import MCPClient

            mcp = MCPClient()

            # Navigate to the platform with full launch options
            nav_result = await mcp.call_tool(
                "puppeteer_navigate",
                    {
                    "url": url,
                        "launchOptions": {
                        "headless": self.config["browser"]["headless"],
                            "args": self.config["browser"]["args"],
                            "ignoreDefaultArgs": self.config["browser"][
                            "ignoreDefaultArgs"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         ],
                            "slowMo": self.config["browser"]["slowMo"],
                            "timeout": self.config["browser"]["timeout"],
# BRACKET_SURGEON: disabled
#                             },
                        "allowDangerous": True,
# BRACKET_SURGEON: disabled
#                         },
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )

            if nav_result.get("success"):
                # Store session info
                self.sessions[session_id] = BrowserSession(
                    session_id = session_id,
                        platform = platform,
                        url = url,
                        created_at = datetime.now(),
                        last_used = datetime.now(),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )

                self.logger.info(f"Successfully navigated to {platform}")
                return session_id
            else:
                raise Exception(f"Navigation failed: {nav_result.get('error')}")

        except Exception as e:
            self.logger.error(f"Navigation to {platform} failed: {e}")
            raise


    async def send_message(self, session_id: str, message: str, platform: str) -> str:
        """Send message to AI platform and get response"""
        if session_id not in self.sessions:
            raise Exception(f"Session {session_id} not found")

        try:
            self.logger.info(f"Sending message to {platform}")

            from integrations.mcp_client import MCPClient

            mcp = MCPClient()

            selectors = self.config["selectors"].get(platform, {})

            # Fill the input field
            await mcp.call_tool(
                "puppeteer_fill", {"selector": selectors.get("input"), "value": message}
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

            # Click send button
            await mcp.call_tool(
                "puppeteer_click", {"selector": selectors.get("send_button")}
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

            # Wait for response
            await asyncio.sleep(3)  # Initial wait

            # Check for loading indicator and wait for completion
            loading_selector = selectors.get("loading")
            if loading_selector:
                # Wait for loading to disappear (up to 30 seconds)
                for _ in range(30):
                    try:
                        await mcp.call_tool(
                            "puppeteer_evaluate",
                                {"script": f'document.querySelector("{loading_selector}")'},
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                                 )
                        await asyncio.sleep(1)
                    except Exception:
                        break  # Loading indicator not found, response ready

            # Get the response text
            response_result = await mcp.call_tool(
                "puppeteer_evaluate",
                    {
                    "script": f""""""
                    const responseElement = document.querySelector("{selectors.get('response')}");
                    responseElement ? responseElement.innerText : "No response found";
                """"""
# BRACKET_SURGEON: disabled
#                 },
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )

            response_text = response_result.get("result", "No response received")

            # Update session last used time
            self.sessions[session_id].last_used = datetime.now()

            self.logger.info(f"Received response from {platform}")
            return response_text

        except Exception as e:
            self.logger.error(f"Failed to send message to {platform}: {e}")
            raise


    async def take_screenshot(self, session_id: str, name: str = None) -> str:
        """Take screenshot of current page"""
        try:

            from integrations.mcp_client import MCPClient

            mcp = MCPClient()

            screenshot_name = name or f"screenshot_{session_id}_{int(time.time())}"

            result = await mcp.call_tool(
                "puppeteer_screenshot",
                    {
                    "name": screenshot_name,
                        "width": self.config["browser"]["width"],
                        "height": self.config["browser"]["height"],
# BRACKET_SURGEON: disabled
#                         },
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )

            return result.get("path", "")

        except Exception as e:
            self.logger.error(f"Screenshot failed: {e}")
            raise


    async def evaluate_script(self, session_id: str, script: str) -> Any:
        """Execute JavaScript in browser context"""
        try:

            from integrations.mcp_client import MCPClient

            mcp = MCPClient()

            result = await mcp.call_tool("puppeteer_evaluate", {"script": script})

            return result.get("result")

        except Exception as e:
            self.logger.error(f"Script evaluation failed: {e}")
            raise


    async def wait_for_element(self, selector: str, timeout: int = 10000) -> bool:
        """Wait for element to appear on page"""
        try:

            from integrations.mcp_client import MCPClient

            mcp = MCPClient()

            # Use JavaScript to wait for element
            script = f""""""
                new Promise((resolve) => {{
                    const checkElement = () => {{
                        const element = document.querySelector("{selector}");
                        if (element) {{
                            resolve(true);
                        }} else {{
                            setTimeout(checkElement, 100);
# BRACKET_SURGEON: disabled
#                         }}
# BRACKET_SURGEON: disabled
#                     }};
                    checkElement();
                    setTimeout(() => resolve(false), {timeout});
# BRACKET_SURGEON: disabled
#                 }});
            """"""

            result = await mcp.call_tool("puppeteer_evaluate", {"script": script})

            return result.get("result", False)

        except Exception as e:
            self.logger.error(f"Wait for element failed: {e}")
            return False


    async def cleanup_session(self, session_id: str):
        """Cleanup browser session"""
        if session_id in self.sessions:
            self.logger.info(f"Cleaning up session {session_id}")
            del self.sessions[session_id]


    async def cleanup_all_sessions(self):
        """Cleanup all browser sessions"""
        self.logger.info("Cleaning up all sessions")
        self.sessions.clear()


    def get_session_info(self, session_id: str) -> Optional[BrowserSession]:
        """Get session information"""
        return self.sessions.get(session_id)


    def list_active_sessions(self) -> List[BrowserSession]:
        """List all active sessions"""
        return list(self.sessions.values())


    async def health_check(self) -> Dict:
        """Check service health"""
        try:
            # Test MCP connection

            from integrations.mcp_client import MCPClient

            mcp = MCPClient()

            # Simple test navigation
            test_result = await mcp.call_tool(
                "puppeteer_navigate", {"url": "https://www.google.com"}
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

            mcp_status = "healthy" if test_result.get("success") else "error"

        except Exception as e:
            mcp_status = f"error: {str(e)}"

        return {
            "status": "healthy" if mcp_status == "healthy" else "degraded",
                "mcp_puppeteer": mcp_status,
                "active_sessions": len(self.sessions),
                "timestamp": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#                 }

if __name__ == "__main__":


    async def test_puppeteer_service():
        """Test the Puppeteer service"""
        service = PuppeteerService()

        # Health check
        health = await service.health_check()
        print(f"Health: {json.dumps(health, indent = 2)}")

        # Test navigation (if MCP is available)
        try:
            session_id = await service.navigate_to_platform(
                "chatgpt", "https://chat.openai.com"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )
            print(f"Created session: {session_id}")

            # Test screenshot
            screenshot_path = await service.take_screenshot(session_id)
            print(f"Screenshot saved: {screenshot_path}")

        except Exception as e:
            print(f"Test failed: {e}")

    asyncio.run(test_puppeteer_service())