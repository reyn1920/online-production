import os
import requests
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import logging
import base64

from .base_api import BaseAPI, APIError, RateLimitError

logger = logging.getLogger(__name__)


class HuggingFaceAPI(BaseAPI):
    """Hugging Face API integration for free AI models"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Hugging Face API client

        Args:
            api_key: Hugging Face API token. If not provided, will try to get from environment
        """
        super().__init__()
        self.api_key = api_key or os.getenv("HUGGINGFACE_API_KEY")
        self.base_url = "https://api - inference.huggingface.co"
        self.name = "Hugging Face"
        self.category = "AI / ML"

        if not self.api_key:
            logger.warning(
                "Hugging Face API key not provided. Rate limits will be more restrictive."
            )

    def get_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        headers = {"Content - Type": "application / json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def text_generation(
        self, text: str, model: str = "microsoft / DialoGPT - medium", **kwargs
    ) -> Dict[str, Any]:
        """
        Generate text using Hugging Face models

        Args:
            text: Input text prompt
            model: Model to use
            **kwargs: Additional parameters

        Returns:
            Dict containing the generated text
        """
        url = f"{self.base_url}/models/{model}"

        payload = {"inputs": text, "parameters": kwargs}

        try:
            response = requests.post(url, json=payload, headers=self.get_headers())

            if response.status_code == 429:
                raise RateLimitError("Hugging Face API rate limit exceeded")
            elif response.status_code == 503:
                raise APIError("Model is currently loading. Please try again in a few minutes.")
            elif response.status_code != 200:
                raise APIError(f"Hugging Face API error: {response.status_code} - {response.text}")

            return response.json()

        except requests.RequestException as e:
            raise APIError(f"Request failed: {str(e)}")

    def text_classification(
        self,
        text: str,
        model: str = "cardiffnlp / twitter - roberta - base - sentiment - latest",
    ) -> Dict[str, Any]:
        """
        Classify text using Hugging Face models

        Args:
            text: Text to classify
            model: Classification model to use

        Returns:
            Dict containing classification results
        """
        url = f"{self.base_url}/models/{model}"

        payload = {"inputs": text}

        try:
            response = requests.post(url, json=payload, headers=self.get_headers())

            if response.status_code == 429:
                raise RateLimitError("Hugging Face API rate limit exceeded")
            elif response.status_code == 503:
                raise APIError("Model is currently loading. Please try again in a few minutes.")
            elif response.status_code != 200:
                raise APIError(f"Hugging Face API error: {response.status_code} - {response.text}")

            return response.json()

        except requests.RequestException as e:
            raise APIError(f"Request failed: {str(e)}")

    def summarization(
        self, text: str, model: str = "facebook / bart - large - cnn", **kwargs
    ) -> Dict[str, Any]:
        """
        Summarize text using Hugging Face models

        Args:
            text: Text to summarize
            model: Summarization model to use
            **kwargs: Additional parameters

        Returns:
            Dict containing summarization results
        """
        url = f"{self.base_url}/models/{model}"

        payload = {"inputs": text, "parameters": kwargs}

        try:
            response = requests.post(url, json=payload, headers=self.get_headers())

            if response.status_code == 429:
                raise RateLimitError("Hugging Face API rate limit exceeded")
            elif response.status_code == 503:
                raise APIError("Model is currently loading. Please try again in a few minutes.")
            elif response.status_code != 200:
                raise APIError(f"Hugging Face API error: {response.status_code} - {response.text}")

            return response.json()

        except requests.RequestException as e:
            raise APIError(f"Request failed: {str(e)}")

    def image_classification(
        self,
        image_data: Union[str, bytes],
        model: str = "google / vit - base - patch16 - 224",
    ) -> Dict[str, Any]:
        """
        Classify images using Hugging Face models

        Args:
            image_data: Image data (base64 string or bytes)
            model: Image classification model to use

        Returns:
            Dict containing classification results
        """
        url = f"{self.base_url}/models/{model}"

        # Handle different image data formats
        if isinstance(image_data, str):
            # Assume base64 encoded
            image_bytes = base64.b64decode(image_data)
        else:
            image_bytes = image_data

        headers = self.get_headers()
        headers["Content - Type"] = "application / octet - stream"

        try:
            response = requests.post(url, data=image_bytes, headers=headers)

            if response.status_code == 429:
                raise RateLimitError("Hugging Face API rate limit exceeded")
            elif response.status_code == 503:
                raise APIError("Model is currently loading. Please try again in a few minutes.")
            elif response.status_code != 200:
                raise APIError(f"Hugging Face API error: {response.status_code} - {response.text}")

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
            "available_tasks": [
                "text - generation",
                "text - classification",
                "summarization",
                "image - classification",
                "question - answering",
                "translation",
            ],
            "rate_limits": "Free tier: 1000 requests / month, Paid: Higher limits",
            "last_checked": datetime.now().isoformat(),
        }

    def test_connection(self) -> Dict[str, Any]:
        """
        Test the API connection

        Returns:
            Dict containing test results
        """
        try:
            # Test with a simple sentiment analysis
            result = self.text_classification("This is a test message")

            return {
                "success": True,
                "message": "Connection successful",
                "test_result": result,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
