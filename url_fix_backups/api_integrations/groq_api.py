import os
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from .base_api import BaseAPI, APIError, RateLimitError

logger = logging.getLogger(__name__)


class GroqAPI(BaseAPI):
    """Groq API integration for fast AI inference"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Groq API client

        Args:
            api_key: Groq API key. If not provided, will try to get from environment
        """
        super().__init__()
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.base_url = "https://api.groq.com / openai / v1"
        self.name = "Groq"
        self.category = "AI / ML"

        if not self.api_key:
            logger.warning("Groq API key not provided. Some features may not work.")

    def get_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content - Type": "application / json",
        }

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "mixtral - 8x7b - 32768",
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a chat completion using Groq

        Args:
            messages: List of message objects with 'role' and 'content'
            model: Model to use (default: mixtral - 8x7b - 32768)
            **kwargs: Additional parameters

        Returns:
            Dict containing the completion response
        """
        if not self.api_key:
            raise APIError("Groq API key not configured")

        url = f"{self.base_url}/chat / completions"

        payload = {"model": model, "messages": messages, **kwargs}

        try:
            response = requests.post(url, json=payload, headers=self.get_headers())

            if response.status_code == 429:
                raise RateLimitError("Groq API rate limit exceeded")
            elif response.status_code != 200:
                raise APIError(f"Groq API error: {response.status_code} - {response.text}")

            return response.json()

        except requests.RequestException as e:
            raise APIError(f"Request failed: {str(e)}")

    def list_models(self) -> Dict[str, Any]:
        """
        List available models

        Returns:
            Dict containing available models
        """
        if not self.api_key:
            raise APIError("Groq API key not configured")

        url = f"{self.base_url}/models"

        try:
            response = requests.get(url, headers=self.get_headers())

            if response.status_code == 429:
                raise RateLimitError("Groq API rate limit exceeded")
            elif response.status_code != 200:
                raise APIError(f"Groq API error: {response.status_code} - {response.text}")

            return response.json()

        except requests.RequestException as e:
            raise APIError(f"Request failed: {str(e)}")

    def get_status(self) -> Dict[str, Any]:
        """
        Get API status and configuration

        Returns:
            Dict containing status information
        """
        return {
            "name": self.name,
            "category": self.category,
            "api_key_configured": bool(self.api_key),
            "base_url": self.base_url,
            "available_models": [
                "mixtral - 8x7b - 32768",
                "llama2 - 70b - 4096",
                "gemma - 7b - it",
            ],
            "rate_limits": "Generous free tier",
            "last_checked": datetime.now().isoformat(),
        }

    def test_connection(self) -> Dict[str, Any]:
        """
        Test the API connection

        Returns:
            Dict containing test results
        """
        try:
            if not self.api_key:
                return {
                    "success": False,
                    "error": "API key not configured",
                    "timestamp": datetime.now().isoformat(),
                }

            # Test with a simple model list request
            models = self.list_models()

            return {
                "success": True,
                "message": "Connection successful",
                "models_available": len(models.get("data", [])),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
