#!/usr / bin / env python3
"""
Avatar API Configuration for Production - Ready Linly - Talker

This module provides configuration and utilities for integrating with
major avatar generation APIs for production deployment.
"""

import os
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class AvatarPlatform(Enum):
    """Supported avatar generation platforms"""

    HEYGEN = "heygen"
    DID = "did"
    SYNTHESIA = "synthesia"
    READY_PLAYER_ME = "ready_player_me"


@dataclass
class AvatarAPIConfig:
    """Configuration for avatar API integration"""

    platform: AvatarPlatform
    api_key: str
    base_url: str
    default_avatar_id: Optional[str] = None
    max_retries: int = 3
    timeout_seconds: int = 120


class ProductionAvatarConfig:
    """Production configuration for avatar APIs"""

    def __init__(self):
        self.configs = self._load_configurations()

    def _load_configurations(self) -> Dict[AvatarPlatform, AvatarAPIConfig]:
        """Load API configurations from environment variables"""
        configs = {}

        # HeyGen Configuration
        heygen_key = os.getenv("HEYGEN_API_KEY")
        if heygen_key:
            configs[AvatarPlatform.HEYGEN] = AvatarAPIConfig(
                platform=AvatarPlatform.HEYGEN,
                api_key=heygen_key,
                base_url="https://api.heygen.com / v2",
                default_avatar_id="Josh_public_2_20230714",
                timeout_seconds=180,
            )

        # D - ID Configuration
        did_key = os.getenv("DID_API_KEY")
        if did_key:
            configs[AvatarPlatform.DID] = AvatarAPIConfig(
                platform=AvatarPlatform.DID,
                api_key=did_key,
                base_url="https://api.d - id.com",
                default_avatar_id="alice",
                timeout_seconds=150,
            )

        # Synthesia Configuration
        synthesia_key = os.getenv("SYNTHESIA_API_KEY")
        if synthesia_key:
            configs[AvatarPlatform.SYNTHESIA] = AvatarAPIConfig(
                platform=AvatarPlatform.SYNTHESIA,
                api_key=synthesia_key,
                base_url="https://api.synthesia.io / v2",
                default_avatar_id="anna_costume1_cameraA",
                timeout_seconds=200,
            )

        return configs

    def get_config(self, platform: AvatarPlatform) -> Optional[AvatarAPIConfig]:
        """Get configuration for specific platform"""
        return self.configs.get(platform)

    def is_platform_available(self, platform: AvatarPlatform) -> bool:
        """Check if platform is configured and available"""
        return platform in self.configs

    def get_available_platforms(self) -> list[AvatarPlatform]:
        """Get list of available configured platforms"""
        return list(self.configs.keys())

    def get_demo_config(self) -> Dict[str, Any]:
        """Get demo configuration when no real APIs are available"""
        return {
            "demo_mode": True,
            "platforms": [
                {
                    "name": "HeyGen",
                    "description": "Streaming Avatar Technology",
                    "features": [
                        "Real - time streaming",
                        "Professional presenters",
                        "Multi - language support",
                    ],
                    "quality": "HD 1280x720",
                    "avg_generation_time": "15 - 20 seconds",
                },
                {
                    "name": "D - ID",
                    "description": "Photorealistic Talking Heads",
                    "features": [
                        "Photorealistic avatars",
                        "Custom face upload",
                        "Natural expressions",
                    ],
                    "quality": "HD with advanced lip - sync",
                    "avg_generation_time": "10 - 15 seconds",
                },
                {
                    "name": "Synthesia",
                    "description": "Professional AI Presenters",
                    "features": ["4K quality", "100+ avatars", "Enterprise features"],
                    "quality": "4K Ultra HD",
                    "avg_generation_time": "15 - 25 seconds",
                },
            ],
        }


# Avatar quality presets
AVATAR_QUALITY_PRESETS = {
    "low": {
        "resolution": "640x480",
        "fps": 15,
        "bitrate": "500k",
        "description": "Fast generation, lower quality",
    },
    "medium": {
        "resolution": "1280x720",
        "fps": 25,
        "bitrate": "2M",
        "description": "Balanced quality and speed",
    },
    "high": {
        "resolution": "1920x1080",
        "fps": 30,
        "bitrate": "5M",
        "description": "High quality, slower generation",
    },
    "ultra": {
        "resolution": "3840x2160",
        "fps": 30,
        "bitrate": "15M",
        "description": "4K quality, longest generation time",
    },
}

# Voice configuration options
VOICE_PRESETS = {
    "professional_female": {
        "heygen_voice_id": "1bd001e7e50f421d891986aad5158bc8",
        "did_voice": "Sara",
        "synthesia_voice": "anna",
        "description": "Professional female presenter voice",
    },
    "professional_male": {
        "heygen_voice_id": "2d5b0e8c4a1f3d9e7b6c8a5f2e9d1c4b",
        "did_voice": "Adam",
        "synthesia_voice": "james",
        "description": "Professional male presenter voice",
    },
    "friendly_female": {
        "heygen_voice_id": "3e6c1f9d8b2a5e7c4f1d9b6e3a8c5f2e",
        "did_voice": "Emma",
        "synthesia_voice": "lily",
        "description": "Friendly, approachable female voice",
    },
    "authoritative_male": {
        "heygen_voice_id": "4f7d2e0a9c3b6f8e5a2f0d7b4e1a9c6f",
        "did_voice": "Brian",
        "synthesia_voice": "david",
        "description": "Authoritative, confident male voice",
    },
}


def get_production_config() -> ProductionAvatarConfig:
    """Get production avatar configuration instance"""
    return ProductionAvatarConfig()


def validate_api_keys() -> Dict[str, bool]:
    """Validate which API keys are properly configured"""
    validation_results = {
        "heygen": bool(os.getenv("HEYGEN_API_KEY")),
        "did": bool(os.getenv("DID_API_KEY")),
        "synthesia": bool(os.getenv("SYNTHESIA_API_KEY")),
    }

    return validation_results


def get_setup_instructions() -> str:
    """Get setup instructions for avatar APIs"""
    return """
🔧 AVATAR API SETUP INSTRUCTIONS

1. HeyGen API Setup:
   - Visit: https://app.heygen.com/
       - Sign up for an account
   - Go to API section and generate API key
   - Set environment variable: export HEYGEN_API_KEY="your_key_here"

2. D - ID API Setup:
   - Visit: https://www.d - id.com/
       - Create account and verify email
   - Navigate to API section
   - Generate API key
   - Set environment variable: export DID_API_KEY="your_key_here"

3. Synthesia API Setup:
   - Visit: https://www.synthesia.io/
       - Sign up for business account
   - Access API documentation
   - Generate Bearer token
   - Set environment variable: export SYNTHESIA_API_KEY="your_key_here"

💡 PRICING NOTES:
- HeyGen: Pay - per - minute, starting at $0.006 / minute
- D - ID: Credit - based system, ~$0.05 - 0.20 per video
- Synthesia: Subscription - based, starting at $30 / month

🚀 PRODUCTION DEPLOYMENT:
For production use, consider:
- Rate limiting and quota management
- Caching generated videos
- Fallback mechanisms
- Cost monitoring and alerts
"""


if __name__ == "__main__":
    # Test configuration
    config = get_production_config()
    validation = validate_api_keys()

    print("Avatar API Configuration Status:")
    print(f"Available platforms: {len(config.get_available_platforms())}")

    for platform_name, is_valid in validation.items():
        status = "✅ Configured" if is_valid else "❌ Not configured"
        print(f"{platform_name.upper()}: {status}")

    if not any(validation.values()):
        print("\\n⚠️ No API keys configured. Running in demo mode.")
        print("\\nSetup instructions:")
        print(get_setup_instructions())
