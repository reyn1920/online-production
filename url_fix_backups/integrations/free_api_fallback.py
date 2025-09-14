#!/usr / bin / env python3
"""
Free API Fallback System for RouteLL Integration
Provides fallback options when RouteLL credits are exhausted
"""

import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union

import requests


class FallbackProvider(Enum):
    HUGGINGFACE_FREE = "huggingface_free"
    OLLAMA_LOCAL = "ollama_local"
    OPENAI_FREE_TIER = "openai_free_tier"
    GROQ_FREE = "groq_free"
    TOGETHER_FREE = "together_free"


@dataclass
class FallbackResponse:
    """Response structure for fallback APIs"""

    success: bool
    data: Optional[Dict]
    error: Optional[str]
    provider: str
    model_used: str
    response_time_ms: int
    timestamp: datetime
    is_fallback: bool = True


class FreeAPIFallback:
    """
    Manages fallback to free AI APIs when RouteLL credits are exhausted
    """

    def __init__(self, config_path: str = None):
        self.config_path = (
            config_path
            or "/Users / thomasbrianreynolds / online production / config / fallback_config.json"
        )
        self.config = self._load_config()

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Available providers and their configurations
        self.providers = {
            FallbackProvider.HUGGINGFACE_FREE: {
                "name": "Hugging Face Free",
                "base_url": "https://api - inference.huggingface.co / models",
                "models": [
                    "microsoft / DialoGPT - medium",
                    "facebook / blenderbot - 400M - distill",
                    "microsoft / DialoGPT - small",
                ],
                "rate_limit": 1000,  # requests per hour
                "requires_key": True,
            },
            FallbackProvider.GROQ_FREE: {
                "name": "Groq Free Tier",
                "base_url": "https://api.groq.com / openai / v1",
                "models": [
                    "llama3 - 8b - 8192",
                    "llama3 - 70b - 8192",
                    "mixtral - 8x7b - 32768",
                ],
                "rate_limit": 30,  # requests per minute
                "requires_key": True,
            },
            FallbackProvider.TOGETHER_FREE: {
                "name": "Together AI Free",
                "base_url": "https://api.together.xyz / v1",
                "models": [
                    "meta - llama / Llama - 2 - 7b - chat - hf",
                    "mistralai / Mistral - 7B - Instruct - v0.1",
                ],
                "rate_limit": 60,  # requests per hour
                "requires_key": True,
            },
            FallbackProvider.OLLAMA_LOCAL: {
                "name": "Ollama Local",
                "base_url": "http://localhost:11434 / api",
                "models": ["llama2", "mistral", "codellama"],
                "rate_limit": float("inf"),  # No limit for local
                "requires_key": False,
            },
        }

        # Track usage for rate limiting
        self.usage_tracker = {}

    def _load_config(self) -> Dict:
        """Load fallback configuration"""
        try:
            with open(self.config_path, "r") as f:
                return json.load(f)
        except Exception as e:
            self.logger.warning(f"Failed to load fallback config: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict:
        """Get default fallback configuration"""
        return {
            "enabled": True,
            "preferred_providers": [
                "groq_free",
                "together_free",
                "huggingface_free",
                "ollama_local",
            ],
            "fallback_models": {
                "text_generation": "llama3 - 8b - 8192",
                "chat": "llama3 - 8b - 8192",
                "code": "codellama",
            },
            "max_retries": 3,
            "timeout_seconds": 30,
        }

    def is_available(self) -> bool:
        """Check if fallback system is available"""
        return self.config.get("enabled", True)

    def get_available_providers(self) -> List[str]:
        """Get list of available fallback providers"""
        available = []
        for provider_enum in FallbackProvider:
            provider = self.providers[provider_enum]
            if self._check_provider_availability(provider_enum):
                available.append(provider_enum.value)
        return available

    def _check_provider_availability(self, provider: FallbackProvider) -> bool:
        """Check if a specific provider is available"""
        provider_config = self.providers[provider]

        # Check if API key is required and available
        if provider_config["requires_key"]:
            key_name = f"{provider.value.upper()}_API_KEY"
            if not os.getenv(key_name):
                return False

        # Check rate limits
        if not self._check_rate_limit(provider):
            return False

        # For local providers, check if service is running
        if provider == FallbackProvider.OLLAMA_LOCAL:
            return self._check_ollama_availability()

        return True

    def _check_rate_limit(self, provider: FallbackProvider) -> bool:
        """Check if provider is within rate limits"""
        now = time.time()
        provider_key = provider.value

        if provider_key not in self.usage_tracker:
            self.usage_tracker[provider_key] = []

        # Clean old entries (older than 1 hour)
        self.usage_tracker[provider_key] = [
            timestamp for timestamp in self.usage_tracker[provider_key] if now - timestamp < 3600
        ]

        rate_limit = self.providers[provider]["rate_limit"]
        current_usage = len(self.usage_tracker[provider_key])

        return current_usage < rate_limit

    def _check_ollama_availability(self) -> bool:
        """Check if Ollama is running locally"""
        try:
            response = requests.get("http://localhost:11434 / api / tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def chat_completion(self, messages: List[Dict], task_type: str = "chat") -> FallbackResponse:
        """Make a chat completion request using fallback providers"""
        start_time = time.time()

        if not self.is_available():
            return FallbackResponse(
                success=False,
                data=None,
                error="Fallback system is disabled",
                provider="none",
                model_used="none",
                response_time_ms=0,
                timestamp=datetime.now(),
            )

        # Try providers in order of preference
        preferred_providers = self.config.get("preferred_providers", [])

        for provider_name in preferred_providers:
            try:
                provider_enum = FallbackProvider(provider_name)
                if self._check_provider_availability(provider_enum):
                    response = self._make_request(provider_enum, messages, task_type)
                    if response.success:
                        # Record usage
                        self.usage_tracker[provider_name].append(time.time())
                        return response
            except Exception as e:
                self.logger.warning(f"Provider {provider_name} failed: {e}")
                continue

        # If all providers failed
        return FallbackResponse(
            success=False,
            data=None,
            error="All fallback providers failed or unavailable",
            provider="none",
            model_used="none",
            response_time_ms=int((time.time() - start_time) * 1000),
            timestamp=datetime.now(),
        )

    def _make_request(
        self, provider: FallbackProvider, messages: List[Dict], task_type: str
    ) -> FallbackResponse:
        """Make request to specific provider"""
        start_time = time.time()
        provider_config = self.providers[provider]

        try:
            if provider == FallbackProvider.GROQ_FREE:
                return self._make_groq_request(messages, start_time)
            elif provider == FallbackProvider.HUGGINGFACE_FREE:
                return self._make_huggingface_request(messages, start_time)
            elif provider == FallbackProvider.TOGETHER_FREE:
                return self._make_together_request(messages, start_time)
            elif provider == FallbackProvider.OLLAMA_LOCAL:
                return self._make_ollama_request(messages, start_time)
            else:
                raise ValueError(f"Unsupported provider: {provider}")

        except Exception as e:
            return FallbackResponse(
                success=False,
                data=None,
                error=str(e),
                provider=provider.value,
                model_used="unknown",
                response_time_ms=int((time.time() - start_time) * 1000),
                timestamp=datetime.now(),
            )

    def _make_groq_request(self, messages: List[Dict], start_time: float) -> FallbackResponse:
        """Make request to Groq API"""
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content - Type": "application / json",
        }

        payload = {
            "model": "llama3 - 8b - 8192",
            "messages": messages,
            "max_tokens": 1000,
            "temperature": 0.7,
        }

        response = requests.post(
            "https://api.groq.com / openai / v1 / chat / completions",
            headers=headers,
            json=payload,
            timeout=30,
        )

        if response.status_code == 200:
            data = response.json()
            return FallbackResponse(
                success=True,
                data=data,
                error=None,
                provider="groq_free",
                model_used="llama3 - 8b - 8192",
                response_time_ms=int((time.time() - start_time) * 1000),
                timestamp=datetime.now(),
            )
        else:
            raise Exception(f"Groq API error: {response.status_code} - {response.text}")

    def _make_huggingface_request(
        self, messages: List[Dict], start_time: float
    ) -> FallbackResponse:
        """Make request to Hugging Face API"""
        api_key = os.getenv("HUGGINGFACE_API_KEY")
        if not api_key:
            raise ValueError("HUGGINGFACE_API_KEY not found")

        # Convert messages to single prompt for HF models
        prompt = "\\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content - Type": "application / json",
        }

        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 500,
                "temperature": 0.7,
                "return_full_text": False,
            },
        }

        response = requests.post(
            "https://api - inference.huggingface.co / models / microsoft / DialoGPT - medium",
            headers=headers,
            json=payload,
            timeout=30,
        )

        if response.status_code == 200:
            data = response.json()
            return FallbackResponse(
                success=True,
                data={"choices": [{"message": {"content": data[0]["generated_text"]}}]},
                error=None,
                provider="huggingface_free",
                model_used="DialoGPT - medium",
                response_time_ms=int((time.time() - start_time) * 1000),
                timestamp=datetime.now(),
            )
        else:
            raise Exception(f"HuggingFace API error: {response.status_code} - {response.text}")

    def _make_together_request(self, messages: List[Dict], start_time: float) -> FallbackResponse:
        """Make request to Together AI API"""
        api_key = os.getenv("TOGETHER_API_KEY")
        if not api_key:
            raise ValueError("TOGETHER_API_KEY not found")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content - Type": "application / json",
        }

        payload = {
            "model": "meta - llama / Llama - 2 - 7b - chat - hf",
            "messages": messages,
            "max_tokens": 1000,
            "temperature": 0.7,
        }

        response = requests.post(
            "https://api.together.xyz / v1 / chat / completions",
            headers=headers,
            json=payload,
            timeout=30,
        )

        if response.status_code == 200:
            data = response.json()
            return FallbackResponse(
                success=True,
                data=data,
                error=None,
                provider="together_free",
                model_used="Llama - 2 - 7b - chat - hf",
                response_time_ms=int((time.time() - start_time) * 1000),
                timestamp=datetime.now(),
            )
        else:
            raise Exception(f"Together API error: {response.status_code} - {response.text}")

    def _make_ollama_request(self, messages: List[Dict], start_time: float) -> FallbackResponse:
        """Make request to local Ollama API"""
        # Convert messages to prompt format for Ollama
        prompt = "\\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])

        payload = {"model": "llama2", "prompt": prompt, "stream": False}

        response = requests.post(
            "http://localhost:11434 / api / generate", json=payload, timeout=60
        )

        if response.status_code == 200:
            data = response.json()
            return FallbackResponse(
                success=True,
                data={"choices": [{"message": {"content": data["response"]}}]},
                error=None,
                provider="ollama_local",
                model_used="llama2",
                response_time_ms=int((time.time() - start_time) * 1000),
                timestamp=datetime.now(),
            )
        else:
            raise Exception(f"Ollama API error: {response.status_code} - {response.text}")

    def get_status(self) -> Dict:
        """Get fallback system status"""
        available_providers = self.get_available_providers()

        return {
            "enabled": self.is_available(),
            "available_providers": available_providers,
            "total_providers": len(self.providers),
            "usage_stats": {provider: len(usage) for provider, usage in self.usage_tracker.items()},
            "config": self.config,
        }


if __name__ == "__main__":
    # Test the fallback system
    fallback = FreeAPIFallback()

    print("🔄 Free API Fallback System")
    print(f"Status: {fallback.get_status()}")

    # Test message
    messages = [{"role": "user", "content": "Hello, how are you?"}]

    response = fallback.chat_completion(messages)
    print(f"\\nTest Response: {response}")
