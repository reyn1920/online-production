#!/usr/bin/env python3
""""""
Free API Manager
Comprehensive manager for all free API integrations in the TRAE.AI system
""""""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class FreeAPIManager:
    """Manager for all free API integrations"""

    def __init__(self):
        """Initialize the Free API Manager"""
        self.api_configs = {
            "groq": {
                "name": "Groq",
                "env_var": "GROQ_API_KEY",
                "test_url": "https://api.groq.com/openai/v1/models",
                "category": "AI/ML",
# BRACKET_SURGEON: disabled
#             },
            "huggingface": {
                "name": "Hugging Face",
                "env_var": "HUGGINGFACE_API_KEY",
                "test_url": "https://api - inference.huggingface.co/models/gpt2",
                "category": "AI/ML",
# BRACKET_SURGEON: disabled
#             },
            "pexels": {
                "name": "Pexels",
                "env_var": "PEXELS_API_KEY",
                "test_url": "https://api.pexels.com/v1/search?query = nature&per_page = 1",
                "category": "Media",
# BRACKET_SURGEON: disabled
#             },
            "guardian": {
                "name": "Guardian",
                "env_var": "GUARDIAN_API_KEY",
                "test_url": "https://content.guardianapis.com/search?q = test&page - size = 1",
                "category": "News",
# BRACKET_SURGEON: disabled
#             },
            "nytimes": {
                "name": "NY Times",
                "env_var": "NYTIMES_API_KEY",
                "test_url": "https://api.nytimes.com/svc/topstories/v2/home.json",
                "category": "News",
# BRACKET_SURGEON: disabled
#             },
            "reddit": {
                "name": "Reddit",
                "env_var": "REDDIT_CLIENT_ID",
                "test_url": "https://www.reddit.com/r/python/hot.json?limit = 1",
                "category": "Social",
# BRACKET_SURGEON: disabled
#             },
            "youtube": {
                "name": "YouTube Data API",
                "env_var": "YOUTUBE_API_KEY",
                "test_url": "https://www.googleapis.com/youtube/v3/search?part = snippet&q = test&maxResults = 1",
                "category": "Social",
# BRACKET_SURGEON: disabled
#             },
            "github": {
                "name": "GitHub",
                "env_var": "GITHUB_TOKEN",
                "test_url": "https://api.github.com/user",
                "category": "Development",
# BRACKET_SURGEON: disabled
#             },
# BRACKET_SURGEON: disabled
#         }

        logger.info(f"Initialized {len(self.api_configs)} API configurations")

    def get_api_config(self, api_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific API configuration"""
        return self.api_configs.get(api_name.lower())

    def list_apis(self) -> List[str]:
        """List all available API names"""
        return list(self.api_configs.keys())

    def get_api_status(self, api_name: str = None) -> Dict[str, Any]:
        """Get status of specific API or all APIs"""
        if api_name:
            config = self.get_api_config(api_name)
            if config:
                return self._check_api_status(api_name, config)
            else:
                return {"error": f"API '{api_name}' not found"}

        # Return status of all APIs
        status = {}
        for name, config in self.api_configs.items():
            try:
                status[name] = self._check_api_status(name, config)
            except Exception as e:
                status[name] = {"error": str(e)}

        return status

    def _check_api_status(self, api_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Check status of a single API"""
        env_var = config["env_var"]
        api_key = os.getenv(env_var)

        return {
            "name": config["name"],
            "category": config["category"],
            "env_var": env_var,
            "api_key_configured": bool(
                api_key and api_key.strip() and not api_key.startswith("your_")
# BRACKET_SURGEON: disabled
#             ),
            "api_key_present": bool(api_key),
            "timestamp": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#         }

    def check_api_keys_configured(self) -> Dict[str, Any]:
        """Check which API keys are properly configured in environment"""
        results = {}

        for name, config in self.api_configs.items():
            env_var = config["env_var"]
            api_key = os.getenv(env_var)

            results[name] = {
                "env_var": env_var,
                "configured": bool(api_key and api_key.strip() and not api_key.startswith("your_")),
                "present": bool(api_key),
                "value_preview": (
                    api_key[:10] + "..." if api_key and len(api_key) > 10 else "Not set"
# BRACKET_SURGEON: disabled
#                 ),
                "timestamp": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#             }

        return results

    def get_configured_apis(self) -> List[str]:
        """Get list of APIs that have their keys configured"""
        configured = []

        for name, config in self.api_configs.items():
            try:
                status = self._check_api_status(name, config)
                if status.get("api_key_configured", False):
                    configured.append(name)
            except Exception:
                continue

        return configured

    def get_unconfigured_apis(self) -> List[str]:
        """Get list of APIs that need configuration"""
        unconfigured = []

        for name, config in self.api_configs.items():
            try:
                status = self._check_api_status(name, config)
                if not status.get("api_key_configured", False):
                    unconfigured.append(name)
            except Exception:
                unconfigured.append(name)

        return unconfigured

    def generate_env_template(self) -> str:
        """Generate .env template with all required API keys"""
        template = []
        template.append("# Free API Keys Configuration")"
        template.append("# Get your free API keys from the respective services")"
        template.append("")

        # Group APIs by category
        categories = {}
        for api_name, config in self.api_configs.items():
            category = config["category"]
            if category not in categories:
                categories[category] = []
            categories[category].append(api_name)

        for category, api_names in categories.items():
            template.append(f"# {category} APIs")"
            for api_name in api_names:
                config = self.api_configs[api_name]
                env_var = config["env_var"]
                template.append(f"{env_var}=your_{api_name}_api_key_here")
            template.append("")

        return "\\n".join(template)

    def get_setup_instructions(self) -> Dict[str, Dict[str, str]]:
        """Get setup instructions for all APIs"""
        instructions = {
            "groq": {
                "url": "https://console.groq.com/",
                "description": "Fast AI inference with generous free tier",
                "free_tier": "Generous free usage limits",
# BRACKET_SURGEON: disabled
#             },
            "huggingface": {
                "url": "https://huggingface.co/settings/tokens",
                "description": "Access to thousands of AI models",
                "free_tier": "1000 requests/month free",
# BRACKET_SURGEON: disabled
#             },
            "pexels": {
                "url": "https://www.pexels.com/api/",
                "description": "Free stock photos and videos",
                "free_tier": "200 requests/hour",
# BRACKET_SURGEON: disabled
#             },
            "guardian": {
                "url": "https://open - platform.theguardian.com/",
                "description": "Guardian newspaper content",
                "free_tier": "5,000 calls/day",
# BRACKET_SURGEON: disabled
#             },
            "nytimes": {
                "url": "https://developer.nytimes.com/",
                "description": "NY Times articles and reviews",
                "free_tier": "4,000 requests/day",
# BRACKET_SURGEON: disabled
#             },
            "reddit": {
                "url": "https://www.reddit.com/prefs/apps",
                "description": "Reddit posts and comments",
                "free_tier": "60 requests/minute",
# BRACKET_SURGEON: disabled
#             },
            "youtube": {
                "url": "https://console.developers.google.com/",
                "description": "YouTube video data",
                "free_tier": "10,000 units/day",
# BRACKET_SURGEON: disabled
#             },
            "arxiv": {
                "url": "https://arxiv.org/help/api",
                "description": "Academic papers (no key required)",
                "free_tier": "Unlimited with rate limits",
# BRACKET_SURGEON: disabled
#             },
            "github": {
                "url": "https://github.com/settings/tokens",
                "description": "GitHub repositories and data",
                "free_tier": "5,000 requests/hour",
# BRACKET_SURGEON: disabled
#             },
            "google_trends": {
                "url": "https://trends.google.com/",
                "description": "Google search trends (no key required)",
                "free_tier": "Unlimited with rate limits",
# BRACKET_SURGEON: disabled
#             },
# BRACKET_SURGEON: disabled
#         }

        return instructions

    def generate_integration_report(self) -> Dict[str, Any]:
        """Generate comprehensive integration report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_apis": len(self.api_configs),
            "configured_apis": self.get_configured_apis(),
            "unconfigured_apis": self.get_unconfigured_apis(),
            "api_status": self.get_api_status(),
            "key_configuration_check": self.check_api_keys_configured(),
            "setup_instructions": self.get_setup_instructions(),
# BRACKET_SURGEON: disabled
#         }

        # Add summary statistics
        report["summary"] = {
            "configured_count": len(report["configured_apis"]),
            "unconfigured_count": len(report["unconfigured_apis"]),
            "success_rate": 0,
# BRACKET_SURGEON: disabled
#         }

        # Calculate configuration rate from key checks
        configured_keys = sum(
            1
            for check in report["key_configuration_check"].values()
            if check.get("configured", False)
# BRACKET_SURGEON: disabled
#         )
        if report["total_apis"] > 0:
            report["summary"]["success_rate"] = (configured_keys / report["total_apis"]) * 100

        return report

    def save_report(self, filename: str = None) -> str:
        """Save integration report to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y % m%d_ % H%M % S")
            filename = f"free_api_integration_report_{timestamp}.json"

        report = self.generate_integration_report()

        try:
            with open(filename, "w") as f:
                json.dump(report, f, indent=2)

            logger.info(f"Integration report saved to {filename}")
            return filename

        except Exception as e:
            logger.error(f"Error saving report: {str(e)}")
            raise


def main():
    """Main function for testing the API manager"""
    logging.basicConfig(level=logging.INFO)

    manager = FreeAPIManager()

    print("Free API Manager - Integration Status")
    print("=" * 50)

    # Show configured APIs
    configured = manager.get_configured_apis()
    print(f"\\nConfigured APIs ({len(configured)}):")
    for api in configured:
        print(f"  ✓ {api}")

    # Show unconfigured APIs
    unconfigured = manager.get_unconfigured_apis()
    print(f"\\nUnconfigured APIs ({len(unconfigured)}):")
    for api in unconfigured:
        print(f"  ✗ {api}")

    # Check API key configuration
    print("\\nChecking API key configuration...")
    results = manager.check_api_keys_configured()

    for api_name, result in results.items():
        status = "✓" if result.get("configured", False) else "✗"
        print(f"  {status} {api_name}: {result.get('value_preview', 'Not configured')}")

    # Generate and save report
    report_file = manager.save_report()
    print(f"\\nDetailed report saved to: {report_file}")

    # Show setup instructions
    print("\\nSetup Instructions:")
    print("Visit the following URLs to get your free API keys:")

    instructions = manager.get_setup_instructions()
    for api_name, info in instructions.items():
        if api_name in unconfigured:
            print(f"\\n{api_name.upper()}:")
            print(f"  URL: {info['url']}")
            print(f"  Description: {info['description']}")
            print(f"  Free Tier: {info['free_tier']}")


if __name__ == "__main__":
    main()