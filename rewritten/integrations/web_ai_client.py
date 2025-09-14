#!/usr/bin/env python3
"""
Web AI Platform Client
Integrates with web versions of AI platforms using Puppeteer for browser automation
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class WebAIPlatform(Enum):
    """Supported web AI platforms"""

    CHATGPT = "chatgpt"
    GEMINI = "gemini"
    CLAUDE = "claude"
    ABACUS = "abacus"
    PERPLEXITY = "perplexity"


@dataclass
class WebAIResponse:
    """Response from web AI platform"""

    success: bool
    content: Optional[str]
    error: Optional[str]
    platform: str
    model: Optional[str]
    response_time: float
    timestamp: datetime
    session_id: Optional[str] = None
    usage: Optional[Dict] = None


class WebAIClient:
    """Client for interacting with web AI platforms via browser automation"""

    def __init__(self, config_path: str = None):
        """Initialize web AI client"""
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        self.active_sessions = {}
        self.platform_configs = {
            WebAIPlatform.CHATGPT: {
                "url": "https://chat.openai.com",
                "selectors": {
                    "input": 'textarea[data-id="root"]',
                    "send_button": 'button[data-testid="send-button"]',
                    "response": '[data-message-author-role="assistant"] .markdown',
                    "new_chat": 'a[href="/"]',
                },
                "wait_for_response": 3000,
            },
            WebAIPlatform.GEMINI: {
                "url": "https://gemini.google.com",
                "selectors": {
                    "input": '.ql-editor[contenteditable="true"]',
                    "send_button": 'button[aria-label="Send message"]',
                    "response": "[data-response-index] .markdown",
                    "new_chat": 'button[aria-label="New chat"]',
                },
                "wait_for_response": 4000,
            },
            WebAIPlatform.CLAUDE: {
                "url": "https://claude.ai",
                "selectors": {
                    "input": 'div[contenteditable="true"][data-testid="chat-input"]',
                    "send_button": 'button[aria-label="Send Message"]',
                    "response": '[data-testid="conversation"] .font-claude-message',
                    "new_chat": 'button[title="Start new conversation"]',
                },
                "wait_for_response": 3500,
            },
            WebAIPlatform.ABACUS: {
                "url": "https://apps.abacus.ai/chatllm/?appId = 1024a18ebe",
                "selectors": {
                    "input": "textarea[placeholder*='Type your message'], .chat-input, textarea.message-input",
                    "send_button": "button[type='submit'], .send-button, .submit-btn",
                    "response": ".message-content, .response-text, .assistant-message",
                    "new_chat": ".new-chat-btn, button[aria-label*='New']",
                },
                "wait_for_response": 5000,
            },
        }

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from file"""
        default_config = {
            "browser_settings": {
                "headless": True,
                "timeout": 30000,
                "viewport": {"width": 1280, "height": 720},
            },
            "retry_settings": {"max_retries": 3, "retry_delay": 2},
            "rate_limits": {"requests_per_minute": 10, "concurrent_sessions": 3},
            "logging": {"level": "INFO", "file": "web_ai_client.log"},
        }

        if config_path:
            try:
                with open(config_path, "r") as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                print(f"Warning: Could not load config from {config_path}: {e}")

        return default_config

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger("WebAIClient")
        logger.setLevel(getattr(logging, self.config["logging"]["level"]))

        if not logger.handlers:
            handler = logging.FileHandler(self.config["logging"]["file"])
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    async def chat_completion(
        self, messages: List[Dict], platform: WebAIPlatform, model: str = None, **kwargs
    ) -> WebAIResponse:
        """Send chat completion request to web AI platform"""
        start_time = time.time()

        try:
            self.logger.info(f"Starting chat completion with {platform.value}")

            # Get or create session for platform
            session_id = await self._get_session(platform)

            # Format messages for web interface
            prompt = self._format_messages(messages)

            # Send request via browser automation
            response_content = await self._send_web_request(platform, prompt, session_id)

            response_time = time.time() - start_time

            return WebAIResponse(
                success=True,
                content=response_content,
                error=None,
                platform=platform.value,
                model=model or "default",
                response_time=response_time,
                timestamp=datetime.now(),
                session_id=session_id,
            )

        except Exception as e:
            self.logger.error(f"Chat completion failed: {e}")
            response_time = time.time() - start_time

            return WebAIResponse(
                success=False,
                content=None,
                error=str(e),
                platform=platform.value,
                model=model or "default",
                response_time=response_time,
                timestamp=datetime.now(),
            )

    async def _get_session(self, platform: WebAIPlatform) -> str:
        """Get or create browser session for platform"""
        session_id = f"{platform.value}_{int(time.time())}"

        if platform not in self.active_sessions:
            self.logger.info(f"Creating new session for {platform.value}")
            # Session will be created when first request is made
            self.active_sessions[platform] = {
                "session_id": session_id,
                "created_at": datetime.now(),
                "request_count": 0,
            }

        return self.active_sessions[platform]["session_id"]

    def _format_messages(self, messages: List[Dict]) -> str:
        """Format message list into a single prompt for web interface"""
        formatted_parts = []

        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")

            if role == "system":
                formatted_parts.append(f"System: {content}")
            elif role == "user":
                formatted_parts.append(content)
            elif role == "assistant":
                formatted_parts.append(f"Assistant: {content}")

        return "\\n\\n".join(formatted_parts)

    async def _send_web_request(self, platform: WebAIPlatform, prompt: str, session_id: str) -> str:
        """Send request via browser automation using MCP Puppeteer"""
        config = self.platform_configs[platform]

        try:
            from .puppeteer_service import PuppeteerService

            self.logger.info(f"Sending web request to {platform.value}")

            # Initialize Puppeteer service
            puppeteer = PuppeteerService()

            # Navigate to platform if session doesn't exist
            if session_id not in puppeteer.sessions:
                await puppeteer.navigate_to_platform(platform.value, config["url"])

            # Send message and get response
            response = await puppeteer.send_message(session_id, prompt, platform.value)

            return response

        except Exception as e:
            self.logger.error(f"Web request failed: {e}")
            # Fallback to simulated response for development
            return f"Simulated response from {platform.value}: {prompt[:100]}... [Error: {str(e)}]"

    async def get_available_platforms(self) -> List[str]:
        """Get list of available web AI platforms"""
        return [platform.value for platform in WebAIPlatform]

    async def health_check(self) -> Dict:
        """Check health of web AI client"""
        return {
            "status": "healthy",
            "active_sessions": len(self.active_sessions),
            "supported_platforms": await self.get_available_platforms(),
            "timestamp": datetime.now().isoformat(),
        }

    async def cleanup_sessions(self):
        """Cleanup old or inactive sessions"""
        current_time = datetime.now()

        for platform, session_info in list(self.active_sessions.items()):
            session_age = (current_time - session_info["created_at"]).seconds

            # Clean up sessions older than 1 hour
            if session_age > 3600:
                self.logger.info(f"Cleaning up old session for {platform.value}")
                del self.active_sessions[platform]


if __name__ == "__main__":

    async def test_web_ai_client():
        """Test the web AI client"""
        client = WebAIClient()

        # Test health check
        health = await client.health_check()
        print(f"Health check: {json.dumps(health, indent = 2)}")

        # Test chat completion
        messages = [{"role": "user", "content": "Hello, how are you today?"}]

        response = await client.chat_completion(messages=messages, platform=WebAIPlatform.CHATGPT)

        print(f"Response: {response}")

    asyncio.run(test_web_ai_client())
