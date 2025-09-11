#!/usr/bin/env python3
"""
AI Web Assistant for Trae AI Integration
Automatically uses external AI services for coding, debugging, research, and error fixing.
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib.parse import quote

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AIResponse:
    """Structure for AI service responses"""

    service: str
    query: str
    response: str
    timestamp: float
    success: bool
    error: Optional[str] = None


class AIWebAssistant:
    """Web-based AI assistant that integrates with external AI services"""

    def __init__(self):
        self.services = {
            "abacus": "https://apps.abacus.ai/chatllm/?appId=1024a18ebe",
            "gemini": "https://gemini.google.com/app",
            "chatgpt": "https://chatgpt.com/",
        }
        self.responses_cache = []

    async def query_ai_service(
        self, service: str, query: str, context: str = ""
    ) -> AIResponse:
        """
        Query an AI service with a coding/debugging question

        Args:
            service: The AI service to query ('abacus', 'gemini', 'chatgpt')
            query: The question or code to analyze
            context: Additional context about the error or task

        Returns:
            AIResponse object with the service response
        """
        if service not in self.services:
            return AIResponse(
                service=service,
                query=query,
                response="",
                timestamp=time.time(),
                success=False,
                error=f"Unknown service: {service}",
            )

        try:
            # Format the query for the AI service
            formatted_query = self._format_query_for_service(service, query, context)

            # Use Puppeteer to interact with the web service
            response_text = await self._interact_with_service(service, formatted_query)

            response = AIResponse(
                service=service,
                query=query,
                response=response_text,
                timestamp=time.time(),
                success=True,
            )

            self.responses_cache.append(response)
            return response

        except Exception as e:
            logger.error(f"Error querying {service}: {str(e)}")
            return AIResponse(
                service=service,
                query=query,
                response="",
                timestamp=time.time(),
                success=False,
                error=str(e),
            )

    def _format_query_for_service(self, service: str, query: str, context: str) -> str:
        """
        Format the query appropriately for each AI service
        """
        base_prompt = f"""I'm working on a coding project and need help with:

Query: {query}

Context: {context}

Please provide:
1. Analysis of the issue
2. Specific code fixes or suggestions
3. Best practices to prevent similar issues

Respond with clear, actionable advice."""

        if service == "abacus":
            return f"Code Analysis Request: {base_prompt}"
        elif service == "gemini":
            return f"Coding Assistant: {base_prompt}"
        elif service == "chatgpt":
            return f"Programming Help: {base_prompt}"

        return base_prompt

    async def _interact_with_service(self, service: str, query: str) -> str:
        """
        Use Puppeteer to interact with the AI service
        This is a placeholder - actual implementation would use the MCP Puppeteer server
        """
        # This would be implemented using the Puppeteer MCP server
        # For now, return a simulated response
        logger.info(f"Querying {service} with: {query[:100]}...")

        # Simulate different response patterns for each service
        if service == "abacus":
            return f"Abacus AI Analysis: Based on your query, I recommend checking the data pipeline and model configuration. The issue might be related to feature engineering or model validation."
        elif service == "gemini":
            return f"Gemini Response: I can help you debug this code. The error suggests a schema mismatch. Try adding proper column validation and ensure your database migrations are up to date."
        elif service == "chatgpt":
            return f"ChatGPT Analysis: This looks like a common database schema issue. Here's what I recommend: 1) Check if the column exists, 2) Run proper migrations, 3) Add error handling for missing columns."

        return "Service response not available"

    async def debug_error(
        self, error_message: str, code_context: str = ""
    ) -> Dict[str, AIResponse]:
        """
        Send an error to multiple AI services for debugging assistance

        Args:
            error_message: The error message to debug
            code_context: Relevant code context

        Returns:
            Dictionary of service responses
        """
        query = f"Debug this error: {error_message}"
        context = f"Code context: {code_context}"

        # Query all services concurrently
        tasks = [
            self.query_ai_service(service, query, context)
            for service in self.services.keys()
        ]

        responses = await asyncio.gather(*tasks)

        return {response.service: response for response in responses}

    async def research_topic(
        self, topic: str, programming_language: str = "python"
    ) -> Dict[str, AIResponse]:
        """
        Research a programming topic across multiple AI services

        Args:
            topic: The topic to research
            programming_language: The programming language context

        Returns:
            Dictionary of service responses
        """
        query = f"Explain {topic} in {programming_language}"
        context = f"I need to understand {topic} for a {programming_language} project. Please provide examples and best practices."

        # Query all services concurrently
        tasks = [
            self.query_ai_service(service, query, context)
            for service in self.services.keys()
        ]

        responses = await asyncio.gather(*tasks)

        return {response.service: response for response in responses}

    def get_cached_responses(self, limit: int = 10) -> List[AIResponse]:
        """
        Get recent cached responses

        Args:
            limit: Maximum number of responses to return

        Returns:
            List of recent AIResponse objects
        """
        return sorted(self.responses_cache, key=lambda x: x.timestamp, reverse=True)[
            :limit
        ]

    def export_responses(self, filename: str = "ai_responses.json") -> str:
        """
        Export all cached responses to a JSON file

        Args:
            filename: Output filename

        Returns:
            Path to the exported file
        """
        export_data = [
            {
                "service": r.service,
                "query": r.query,
                "response": r.response,
                "timestamp": r.timestamp,
                "success": r.success,
                "error": r.error,
            }
            for r in self.responses_cache
        ]

        with open(filename, "w") as f:
            json.dump(export_data, f, indent=2)

        return filename


# Integration functions for Trae AI
class TraeAIIntegration:
    """Integration layer for Trae AI to use the web assistant"""

    def __init__(self):
        self.assistant = AIWebAssistant()

    async def auto_debug(self, error_message: str, code_snippet: str = "") -> str:
        """
        Automatically debug an error using multiple AI services

        Args:
            error_message: The error to debug
            code_snippet: Related code snippet

        Returns:
            Consolidated debugging advice
        """
        responses = await self.assistant.debug_error(error_message, code_snippet)

        # Consolidate responses
        consolidated = "AI Debugging Results:\n\n"

        for service, response in responses.items():
            if response.success:
                consolidated += f"=== {service.upper()} ===\n"
                consolidated += f"{response.response}\n\n"
            else:
                consolidated += f"=== {service.upper()} (Error) ===\n"
                consolidated += f"Failed to get response: {response.error}\n\n"

        return consolidated

    async def research_and_implement(
        self, feature_request: str, language: str = "python"
    ) -> str:
        """
        Research a feature and get implementation guidance

        Args:
            feature_request: Description of the feature to implement
            language: Programming language

        Returns:
            Research results and implementation guidance
        """
        responses = await self.assistant.research_topic(feature_request, language)

        # Consolidate research results
        consolidated = f"Research Results for: {feature_request}\n\n"

        for service, response in responses.items():
            if response.success:
                consolidated += f"=== {service.upper()} Research ===\n"
                consolidated += f"{response.response}\n\n"

        return consolidated


# Demo usage
async def demo_ai_web_assistant():
    """Demonstrate the AI Web Assistant functionality"""
    print("🤖 AI Web Assistant Demo")
    print("=" * 50)

    # Initialize the integration
    trae_integration = TraeAIIntegration()

    # Demo 1: Debug an error
    print("\n📋 Demo 1: Debugging SQLite Error")
    error_msg = "no such column: search_keywords"
    code_context = "ALTER TABLE api_discovery_tasks ADD COLUMN search_keywords TEXT;"

    debug_result = await trae_integration.auto_debug(error_msg, code_context)
    print(debug_result)

    # Demo 2: Research a topic
    print("\n📋 Demo 2: Research Database Migrations")
    research_result = await trae_integration.research_and_implement(
        "database migration best practices", "python"
    )
    print(research_result)

    # Demo 3: Show cached responses
    print("\n📋 Demo 3: Recent AI Interactions")
    recent_responses = trae_integration.assistant.get_cached_responses(5)
    for i, response in enumerate(recent_responses, 1):
        print(
            f"{i}. {response.service}: {response.query[:50]}... -> {'✅' if response.success else '❌'}"
        )

    # Export responses
    export_file = trae_integration.assistant.export_responses()
    print(f"\n💾 Responses exported to: {export_file}")

    print("\n🎉 Demo completed!")


if __name__ == "__main__":
    asyncio.run(demo_ai_web_assistant())
