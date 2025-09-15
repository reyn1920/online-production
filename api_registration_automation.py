#!/usr/bin/env python3
""""""
API Registration Automation Script
Automatically opens registration pages and manages API keys

Usage:
    python api_registration_automation.py --phase 1
    python api_registration_automation.py --api huggingface
    python api_registration_automation.py --batch-register
""""""

import argparse
import json
import os
import sys
import time
import webbrowser
from datetime import datetime
from typing import List

# API Registry with all 100+ APIs
API_REGISTRY = {
    # Phase 1: Essential Free APIs
    "huggingface": {
        "name": "Hugging Face",
        "url": "https://huggingface.co/join",
        "login_url": "https://huggingface.co/login",
        "env_var": "HUGGINGFACE_API_KEY",
        "cost": "FREE",
        "phase": 1,
        "priority": "HIGH",
        "notes": "1. Sign up → 2. Go to Settings → 3. Access Tokens → 4. Create new token",
# BRACKET_SURGEON: disabled
#     },
    "groq": {
        "name": "Groq",
        "url": "https://console.groq.com/",
        "login_url": "https://console.groq.com/",
        "env_var": "GROQ_API_KEY",
        "cost": "FREE",
        "phase": 1,
        "priority": "HIGH",
        "notes": "1. Sign up → 2. Create API Key → 3. Copy key",
# BRACKET_SURGEON: disabled
#     },
    "google_ai": {
        "name": "Google AI (Gemini)",
        "url": "https://makersuite.google.com/",
        "login_url": "https://makersuite.google.com/",
        "env_var": "GOOGLE_AI_API_KEY",
        "cost": "FREEMIUM",
        "phase": 1,
        "priority": "HIGH",
        "notes": "1. Sign up with Google → 2. Create API Key → 3. Copy key",
# BRACKET_SURGEON: disabled
#     },
    "youtube": {
        "name": "YouTube Data API",
        "url": "https://console.cloud.google.com/",
        "login_url": "https://accounts.google.com/",
        "env_var": "YOUTUBE_API_KEY",
        "cost": "FREE",
        "phase": 1,
        "priority": "HIGH",
        "notes": "1. Google Cloud Console → 2. Enable YouTube Data API → 3. Create credentials",
# BRACKET_SURGEON: disabled
#     },
    "reddit": {
        "name": "Reddit API",
        "url": "https://www.reddit.com/prefs/apps",
        "login_url": "https://www.reddit.com/login",
        "env_var": "REDDIT_CLIENT_ID",
        "cost": "FREE",
        "phase": 1,
        "priority": "HIGH",
        "notes": "1. Reddit login → 2. Create app → 3. Get client ID and secret",
# BRACKET_SURGEON: disabled
#     },
    "github": {
        "name": "GitHub API",
        "url": "https://github.com/join",
        "login_url": "https://github.com/login",
        "env_var": "GITHUB_TOKEN",
        "cost": "FREE",
        "phase": 1,
        "priority": "HIGH",
        "notes": "1. GitHub login → 2. Settings → 3. Developer settings → 4. Personal access tokens",
# BRACKET_SURGEON: disabled
#     },
    "netlify": {
        "name": "Netlify",
        "url": "https://app.netlify.com/signup",
        "login_url": "https://app.netlify.com/",
        "env_var": "NETLIFY_AUTH_TOKEN",
        "cost": "FREEMIUM",
        "phase": 1,
        "priority": "HIGH",
        "notes": "1. Sign up → 2. User settings → 3. Applications → 4. Personal access tokens",
# BRACKET_SURGEON: disabled
#     },
    "sendgrid": {
        "name": "SendGrid",
        "url": "https://signup.sendgrid.com/",
        "login_url": "https://app.sendgrid.com/login",
        "env_var": "SENDGRID_API_KEY",
        "cost": "FREEMIUM",
        "phase": 1,
        "priority": "HIGH",
        "notes": "1. Sign up → 2. Settings → 3. API Keys → 4. Create API Key",
# BRACKET_SURGEON: disabled
#     },
    # Phase 2: Social Media APIs
    "twitter": {
        "name": "Twitter/X API",
        "url": "https://developer.twitter.com/",
        "login_url": "https://twitter.com/login",
        "env_var": "TWITTER_API_KEY",
        "cost": "FREEMIUM",
        "phase": 2,
        "priority": "MEDIUM",
        "notes": "1. Apply for developer account → 2. Create app → 3. Get API keys",
# BRACKET_SURGEON: disabled
#     },
    "linkedin": {
        "name": "LinkedIn API",
        "url": "https://developer.linkedin.com/",
        "login_url": "https://www.linkedin.com/login",
        "env_var": "LI_CLIENT_ID",
        "cost": "FREE",
        "phase": 2,
        "priority": "MEDIUM",
        "notes": "1. LinkedIn login → 2. Create app → 3. Get client credentials",
# BRACKET_SURGEON: disabled
#     },
    "pinterest": {
        "name": "Pinterest API",
        "url": "https://developers.pinterest.com/",
        "login_url": "https://www.pinterest.com/login",
        "env_var": "PINTEREST_ACCESS_TOKEN",
        "cost": "FREE",
        "phase": 2,
        "priority": "MEDIUM",
        "notes": "1. Pinterest login → 2. Create app → 3. Generate access token",
# BRACKET_SURGEON: disabled
#     },
    "tiktok": {
        "name": "TikTok API",
        "url": "https://developers.tiktok.com/",
        "login_url": "https://www.tiktok.com/login",
        "env_var": "TIKTOK_CLIENT_ID",
        "cost": "FREE",
        "phase": 2,
        "priority": "MEDIUM",
        "notes": "1. TikTok login → 2. Apply for API access → 3. Create app",
# BRACKET_SURGEON: disabled
#     },
    "facebook": {
        "name": "Facebook/Meta API",
        "url": "https://developers.facebook.com/",
        "login_url": "https://www.facebook.com/login",
        "env_var": "FACEBOOK_APP_ID",
        "cost": "FREE",
        "phase": 2,
        "priority": "MEDIUM",
        "notes": "1. Facebook login → 2. Create app → 3. Get app ID and secret",
# BRACKET_SURGEON: disabled
#     },
    "instagram": {
        "name": "Instagram API",
        "url": "https://developers.facebook.com/",
        "login_url": "https://www.facebook.com/login",
        "env_var": "INSTAGRAM_ACCESS_TOKEN",
        "cost": "FREE",
        "phase": 2,
        "priority": "MEDIUM",
        "notes": "1. Facebook developers → 2. Instagram Basic Display → 3. Create app",
# BRACKET_SURGEON: disabled
#     },
    # Phase 3: Specialized APIs
    "dog_api": {
        "name": "Dog API",
        "url": "https://thedogapi.com/signup",
        "login_url": "https://thedogapi.com/signup",
        "env_var": "DOG_API_KEY",
        "cost": "FREE",
        "phase": 3,
        "priority": "LOW",
        "notes": "1. Sign up → 2. Get API key from email",
# BRACKET_SURGEON: disabled
#     },
    "cat_api": {
        "name": "Cat API",
        "url": "https://thecatapi.com/signup",
        "login_url": "https://thecatapi.com/signup",
        "env_var": "CAT_API_KEY",
        "cost": "FREE",
        "phase": 3,
        "priority": "LOW",
        "notes": "1. Sign up → 2. Get API key from email",
# BRACKET_SURGEON: disabled
#     },
    "ebird": {
        "name": "eBird API",
        "url": "https://ebird.org/api/keygen",
        "login_url": "https://ebird.org/login",
        "env_var": "EBIRD_API_TOKEN",
        "cost": "FREE",
        "phase": 3,
        "priority": "LOW",
        "notes": "1. eBird login → 2. Request API key → 3. Get key via email",
# BRACKET_SURGEON: disabled
#     },
    "petfinder": {
        "name": "Petfinder API",
        "url": "https://www.petfinder.com/developers/",
        "login_url": "https://www.petfinder.com/user/login/",
        "env_var": "PETFINDER_KEY",
        "cost": "FREE",
        "phase": 3,
        "priority": "LOW",
        "notes": "1. Petfinder login → 2. Register app → 3. Get API key and secret",
# BRACKET_SURGEON: disabled
#     },
    "openweather": {
        "name": "OpenWeatherMap",
        "url": "https://openweathermap.org/api",
        "login_url": "https://home.openweathermap.org/users/sign_in",
        "env_var": "OPENWEATHER_API_KEY",
        "cost": "FREEMIUM",
        "phase": 3,
        "priority": "MEDIUM",
        "notes": "1. Sign up → 2. API keys section → 3. Generate key",
# BRACKET_SURGEON: disabled
#     },
    "unsplash": {
        "name": "Unsplash API",
        "url": "https://unsplash.com/developers",
        "login_url": "https://unsplash.com/login",
        "env_var": "UNSPLASH_ACCESS_KEY",
        "cost": "FREE",
        "phase": 3,
        "priority": "MEDIUM",
        "notes": "1. Unsplash login → 2. Create new app → 3. Get access key",
# BRACKET_SURGEON: disabled
#     },
    # Phase 4: Business APIs
    "stripe": {
        "name": "Stripe",
        "url": "https://dashboard.stripe.com/register",
        "login_url": "https://dashboard.stripe.com/login",
        "env_var": "STRIPE_PUBLISHABLE_KEY",
        "cost": "FREEMIUM",
        "phase": 4,
        "priority": "MEDIUM",
        "notes": "1. Sign up → 2. Developers → 3. API keys → 4. Get publishable and secret keys",
# BRACKET_SURGEON: disabled
#     },
    "calendly": {
        "name": "Calendly",
        "url": "https://calendly.com/",
        "login_url": "https://calendly.com/login",
        "env_var": "CALENDLY_TOKEN",
        "cost": "FREEMIUM",
        "phase": 4,
        "priority": "LOW",
        "notes": "1. Sign up → 2. Integrations → 3. API & Webhooks → 4. Generate token",
# BRACKET_SURGEON: disabled
#     },
    "mailchimp": {
        "name": "Mailchimp",
        "url": "https://mailchimp.com/",
        "login_url": "https://login.mailchimp.com/",
        "env_var": "MAILCHIMP_API_KEY",
        "cost": "FREEMIUM",
        "phase": 4,
        "priority": "MEDIUM",
        "notes": "1. Sign up → 2. Account → 3. Extras → 4. API keys → 5. Create key",
# BRACKET_SURGEON: disabled
#     },
    "hubspot": {
        "name": "HubSpot",
        "url": "https://www.hubspot.com/",
        "login_url": "https://app.hubspot.com/login",
        "env_var": "HUBSPOT_API_KEY",
        "cost": "FREEMIUM",
        "phase": 4,
        "priority": "LOW",
        "notes": "1. Sign up → 2. Settings → 3. Integrations → 4. API key",
# BRACKET_SURGEON: disabled
#     },
    "airtable": {
        "name": "Airtable",
        "url": "https://airtable.com/",
        "login_url": "https://airtable.com/login",
        "env_var": "AIRTABLE_API_KEY",
        "cost": "FREEMIUM",
        "phase": 4,
        "priority": "LOW",
        "notes": "1. Sign up → 2. Account → 3. Generate API key",
# BRACKET_SURGEON: disabled
#     },
    "notion": {
        "name": "Notion",
        "url": "https://www.notion.so/",
        "login_url": "https://www.notion.so/login",
        "env_var": "NOTION_API_KEY",
        "cost": "FREEMIUM",
        "phase": 4,
        "priority": "LOW",
        "notes": "1. Sign up → 2. Settings → 3. Integrations → 4. Create integration",
# BRACKET_SURGEON: disabled
#     },
# BRACKET_SURGEON: disabled
# }


class APIRegistrationManager:
    """Manages API registration process and tracks progress"""

    def __init__(self):
        self.progress_file = "api_registration_progress.json"
        self.env_file = ".env"
        self.load_progress()

    def load_progress(self):
        """Load registration progress from file"""
        try:
            with open(self.progress_file, "r") as f:
                self.progress = json.load(f)
        except FileNotFoundError:
            self.progress = {}

    def save_progress(self):
        """Save registration progress to file"""
        with open(self.progress_file, "w") as f:
            json.dump(self.progress, f, indent=2)

    def mark_registered(self, api_key: str, api_token: str = None):
        """Mark an API as registered"""
        self.progress[api_key] = {
            "registered": True,
            "timestamp": datetime.now().isoformat(),
            "has_token": bool(api_token),
# BRACKET_SURGEON: disabled
#         }
        self.save_progress()

    def is_registered(self, api_key: str) -> bool:
        """Check if an API is already registered"""
        return self.progress.get(api_key, {}).get("registered", False)

    def open_registration_page(self, api_key: str):
        """Open registration page for an API"""
        if api_key not in API_REGISTRY:
            print(f"❌ Unknown API: {api_key}")
            return False

        api_info = API_REGISTRY[api_key]
        print(f"\n🚀 Opening registration for {api_info['name']}")
        print(f"URL: {api_info['url']}")
        print(f"Instructions: {api_info['notes']}")
        print(f"Environment Variable: {api_info['env_var']}")

        try:
            webbrowser.open(api_info["url"])
            print("\n✅ Registration page opened in browser")

            # Wait for user confirmation
            input("\nPress Enter after completing registration...")

            # Ask for API key
            api_token = input(
                f"Enter your {api_info['name']} API key (or press Enter to skip): "
            ).strip()

            if api_token:
                self.update_env_file(api_info["env_var"], api_token)
                print(f"✅ API key saved to {self.env_file}")

            self.mark_registered(api_key, api_token)
            print(f"✅ {api_info['name']} marked as registered")
            return True

        except Exception as e:
            print(f"❌ Error opening registration page: {e}")
            return False

    def update_env_file(self, env_var: str, value: str):
        """Update or add environment variable to .env file"""
        env_lines = []
        updated = False

        # Read existing .env file if it exists
        if os.path.exists(self.env_file):
            with open(self.env_file, "r") as f:
                env_lines = f.readlines()

        # Update existing variable or add new one
        for i, line in enumerate(env_lines):
            if line.startswith(f"{env_var}="):
                env_lines[i] = f"{env_var}={value}\n"
                updated = True
                break

        if not updated:
            env_lines.append(f"{env_var}={value}\n")

        # Write back to file
        with open(self.env_file, "w") as f:
            f.writelines(env_lines)

    def register_phase(self, phase: int):
        """Register all APIs in a specific phase"""
        phase_apis = [(k, v) for k, v in API_REGISTRY.items() if v["phase"] == phase]

        if not phase_apis:
            print(f"❌ No APIs found for phase {phase}")
            return

        print(f"\n🎯 Registering Phase {phase} APIs ({len(phase_apis)} APIs)")
        print("=" * 50)

        for api_key, api_info in phase_apis:
            if self.is_registered(api_key):
                print(f"✅ {api_info['name']} - Already registered")
                continue

            print(f"\n📋 {api_info['name']} ({api_info['cost']})")
            proceed = input("Register this API? (y/n/q): ").lower()

            if proceed == "q":
                print("🛑 Registration stopped")
                break
            elif proceed == "y":
                self.open_registration_page(api_key)
            else:
                print("⏭️  Skipped")

        print(f"\n✅ Phase {phase} registration complete")

    def batch_register(self, api_keys: List[str]):
        """Register multiple APIs in batch"""
        print(f"\n🚀 Batch registering {len(api_keys)} APIs")
        print("=" * 40)

        for api_key in api_keys:
            if api_key not in API_REGISTRY:
                print(f"❌ Unknown API: {api_key}")
                continue

            self.open_registration_page(api_key)
            time.sleep(1)  # Brief pause between registrations

    def show_status(self):
        """Show registration status for all APIs"""
        print("\n📊 API Registration Status")
        print("=" * 60)

        # Group by phase
        for phase in [1, 2, 3, 4]:
            phase_apis = [(k, v) for k, v in API_REGISTRY.items() if v["phase"] == phase]

            if phase_apis:
                print(f"\n🎯 Phase {phase}:")
                for api_key, api_info in phase_apis:
                    status_icon = "✅" if self.is_registered(api_key) else "❌"
                    env_var = api_info["env_var"]
                    has_key = "🔑" if os.getenv(env_var) else "🚫"
                    cost_icon = {"FREE": "🆓", "FREEMIUM": "💰", "PAID": "💳"}.get(
                        api_info["cost"], "❓"
# BRACKET_SURGEON: disabled
#                     )

                    print(f"  {status_icon} {has_key} {cost_icon} {api_info['name']}")

        # Summary
        total_apis = len(API_REGISTRY)
        registered_count = sum(1 for k in API_REGISTRY.keys() if self.is_registered(k))
        has_key_count = sum(1 for v in API_REGISTRY.values() if os.getenv(v["env_var"]))

        print("\n📈 Summary:")
        print(f"Total APIs: {total_apis}")
        print(f"Registered: {registered_count} ({registered_count/total_apis*100:.1f}%)")
        print(f"Have Keys: {has_key_count} ({has_key_count/total_apis*100:.1f}%)")

    def generate_env_template(self):
        """Generate .env template file"""
        template_file = ".env.template"

        print(f"\n📄 Generating environment template: {template_file}")

        with open(template_file, "w") as f:
            f.write("# API Registration Environment Variables\n")"
            f.write(f"# Generated on {datetime.now().isoformat()}\n\n")"

            # Group by phase
            for phase in [1, 2, 3, 4]:
                phase_apis = [(k, v) for k, v in API_REGISTRY.items() if v["phase"] == phase]

                if phase_apis:
                    f.write(f"# Phase {phase} APIs\n")"
                    for api_key, api_info in sorted(phase_apis):
                        f.write(f"# {api_info['name']} ({api_info['cost']})\n")"
                        f.write(f"# Registration: {api_info['url']}\n")"
                        f.write(f"{api_info['env_var']}=your_api_key_here\n\n")

        print(f"✅ Template saved to {template_file}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="API Registration Automation Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=""""""
Examples:
  python api_registration_automation.py --phase 1
  python api_registration_automation.py --api huggingface
  python api_registration_automation.py --batch-register
  python api_registration_automation.py --status
        ""","""
# BRACKET_SURGEON: disabled
#     )

    parser.add_argument(
        "--phase",
        type=int,
        choices=[1, 2, 3, 4],
        help="Register all APIs in a specific phase",
# BRACKET_SURGEON: disabled
#     )

    parser.add_argument("--api", type=str, help="Register a specific API by key")

    parser.add_argument(
        "--batch-register",
        action="store_true",
        help="Register multiple APIs interactively",
# BRACKET_SURGEON: disabled
#     )

    parser.add_argument(
        "--status", action="store_true", help="Show registration status for all APIs"
# BRACKET_SURGEON: disabled
#     )

    parser.add_argument("--template", action="store_true", help="Generate .env template file")

    parser.add_argument("--list", action="store_true", help="List all available APIs")

    args = parser.parse_args()

    # If no arguments provided, show help
    if len(sys.argv) == 1:
        parser.print_help()
        return

    manager = APIRegistrationManager()

    try:
        if args.phase:
            manager.register_phase(args.phase)
        elif args.api:
            if args.api in API_REGISTRY:
                manager.open_registration_page(args.api)
            else:
                print(f"❌ Unknown API: {args.api}")
                print("Available APIs:")
                for key, info in API_REGISTRY.items():
                    print(f"  {key}: {info['name']}")
        elif args.batch_register:
            print("\n🚀 Batch Registration Mode")
            print("Enter API keys to register (one per line, empty line to finish):")
            api_keys = []
            while True:
                api_key = input("> ").strip()
                if not api_key:
                    break
                if api_key in API_REGISTRY:
                    api_keys.append(api_key)
                else:
                    print(f"❌ Unknown API: {api_key}")

            if api_keys:
                manager.batch_register(api_keys)
            else:
                print("No valid APIs provided")
        elif args.status:
            manager.show_status()
        elif args.template:
            manager.generate_env_template()
        elif args.list:
            print("\n📋 Available APIs:")
            print("=" * 50)
            for phase in [1, 2, 3, 4]:
                phase_apis = [(k, v) for k, v in API_REGISTRY.items() if v["phase"] == phase]
                if phase_apis:
                    print(f"\n🎯 Phase {phase}:")
                    for api_key, api_info in phase_apis:
                        cost_icon = {"FREE": "🆓", "FREEMIUM": "💰", "PAID": "💳"}.get(
                            api_info["cost"], "❓"
# BRACKET_SURGEON: disabled
#                         )
                        print(f"  {cost_icon} {api_key}: {api_info['name']}")

    except KeyboardInterrupt:
        print("\n\n👋 Registration cancelled")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()