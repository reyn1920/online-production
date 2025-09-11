#!/usr / bin / env python3
"""
API Registration Automation Script
Automatically opens registration pages and manages API keys

Usage:
    python api_registration_automation.py --phase 1
    python api_registration_automation.py --api huggingface
    python api_registration_automation.py --batch - register
"""

import argparse
import json
import os
import subprocess
import sys
import time
import webbrowser
from datetime import datetime
from typing import Dict, List, Optional

# API Registry with all 100+ APIs
API_REGISTRY = {
    # Phase 1: Essential Free APIs
    "huggingface": {
        "name": "Hugging Face",
            "signup_url": "https://huggingface.co / join",
            "login_url": "https://huggingface.co / login",
            "env_var": "HUGGINGFACE_API_KEY",
            "cost": "FREE",
            "phase": 1,
            "priority": "high",
            "instructions": "1. Sign up → 2. Go to Settings → 3. Access Tokens → 4. Create new token",
            },
        "groq": {
        "name": "Groq",
            "signup_url": "https://console.groq.com/",
            "login_url": "https://console.groq.com/",
            "env_var": "GROQ_API_KEY",
            "cost": "FREE",
            "phase": 1,
            "priority": "high",
            "instructions": "1. Sign up → 2. Create API Key → 3. Copy key",
            },
        "google_ai": {
        "name": "Google AI (Gemini)",
            "signup_url": "https://makersuite.google.com/",
            "login_url": "https://makersuite.google.com/",
            "env_var": "GOOGLE_AI_API_KEY",
            "cost": "FREEMIUM",
            "phase": 1,
            "priority": "high",
            "instructions": "1. Sign up with Google → 2. Create API Key → 3. Copy key",
            },
        "youtube": {
        "name": "YouTube Data API",
            "signup_url": "https://console.cloud.google.com/",
            "login_url": "https://accounts.google.com/",
            "env_var": "YOUTUBE_API_KEY",
            "cost": "FREE",
            "phase": 1,
            "priority": "high",
            "instructions": "1. Google Cloud Console → 2. Enable YouTube Data API → 3. Create credentials",
            },
        "reddit": {
        "name": "Reddit API",
            "signup_url": "https://www.reddit.com / prefs / apps",
            "login_url": "https://www.reddit.com / login",
            "env_var": "REDDIT_CLIENT_ID",
            "cost": "FREE",
            "phase": 1,
            "priority": "high",
            "instructions": "1. Reddit login → 2. Create app → 3. Get client ID and secret",
            },
        "github": {
        "name": "GitHub API",
            "signup_url": "https://github.com / join",
            "login_url": "https://github.com / login",
            "env_var": "GITHUB_TOKEN",
            "cost": "FREE",
            "phase": 1,
            "priority": "high",
            "instructions": "1. GitHub login → 2. Settings → 3. Developer settings → 4. Personal access tokens",
            },
        "netlify": {
        "name": "Netlify",
            "signup_url": "https://app.netlify.com / signup",
            "login_url": "https://app.netlify.com/",
            "env_var": "NETLIFY_AUTH_TOKEN",
            "cost": "FREEMIUM",
            "phase": 1,
            "priority": "high",
            "instructions": "1. Sign up → 2. User settings → 3. Applications → 4. Personal access tokens",
            },
        "sendgrid": {
        "name": "SendGrid",
            "signup_url": "https://signup.sendgrid.com/",
            "login_url": "https://app.sendgrid.com / login",
            "env_var": "SENDGRID_API_KEY",
            "cost": "FREEMIUM",
            "phase": 1,
            "priority": "high",
            "instructions": "1. Sign up → 2. Settings → 3. API Keys → 4. Create API Key",
            },
        # Phase 2: Social Media APIs
    "twitter": {
        "name": "Twitter / X API",
            "signup_url": "https://developer.twitter.com/",
            "login_url": "https://twitter.com / login",
            "env_var": "TWITTER_API_KEY",
            "cost": "FREEMIUM",
            "phase": 2,
            "priority": "medium",
            "instructions": "1. Apply for developer account → 2. Create app → 3. Get API keys",
            },
        "linkedin": {
        "name": "LinkedIn API",
            "signup_url": "https://developer.linkedin.com/",
            "login_url": "https://www.linkedin.com / login",
            "env_var": "LI_CLIENT_ID",
            "cost": "FREE",
            "phase": 2,
            "priority": "medium",
            "instructions": "1. LinkedIn login → 2. Create app → 3. Get client credentials",
            },
        "pinterest": {
        "name": "Pinterest API",
            "signup_url": "https://developers.pinterest.com/",
            "login_url": "https://www.pinterest.com / login",
            "env_var": "PINTEREST_ACCESS_TOKEN",
            "cost": "FREE",
            "phase": 2,
            "priority": "medium",
            "instructions": "1. Pinterest login → 2. Create app → 3. Generate access token",
            },
        "tiktok": {
        "name": "TikTok API",
            "signup_url": "https://developers.tiktok.com/",
            "login_url": "https://www.tiktok.com / login",
            "env_var": "TIKTOK_CLIENT_ID",
            "cost": "FREE",
            "phase": 2,
            "priority": "medium",
            "instructions": "1. TikTok login → 2. Apply for API access → 3. Create app",
            },
        "facebook": {
        "name": "Facebook / Meta API",
            "signup_url": "https://developers.facebook.com/",
            "login_url": "https://www.facebook.com / login",
            "env_var": "FACEBOOK_APP_ID",
            "cost": "FREE",
            "phase": 2,
            "priority": "medium",
            "instructions": "1. Facebook login → 2. Create app → 3. Get app ID and secret",
            },
        "instagram": {
        "name": "Instagram API",
            "signup_url": "https://developers.facebook.com/",
            "login_url": "https://www.facebook.com / login",
            "env_var": "INSTAGRAM_ACCESS_TOKEN",
            "cost": "FREE",
            "phase": 2,
            "priority": "medium",
            "instructions": "1. Facebook developers → 2. Instagram Basic Display → 3. Create app",
            },
        # Phase 3: Specialized APIs
    "dog_api": {
        "name": "Dog API",
            "signup_url": "https://thedogapi.com / signup",
            "login_url": "https://thedogapi.com / signup",
            "env_var": "DOG_API_KEY",
            "cost": "FREE",
            "phase": 3,
            "priority": "low",
            "instructions": "1. Sign up → 2. Get API key from email",
            },
        "cat_api": {
        "name": "Cat API",
            "signup_url": "https://thecatapi.com / signup",
            "login_url": "https://thecatapi.com / signup",
            "env_var": "CAT_API_KEY",
            "cost": "FREE",
            "phase": 3,
            "priority": "low",
            "instructions": "1. Sign up → 2. Get API key from email",
            },
        "ebird": {
        "name": "eBird API",
            "signup_url": "https://ebird.org / api / keygen",
            "login_url": "https://ebird.org / login",
            "env_var": "EBIRD_API_TOKEN",
            "cost": "FREE",
            "phase": 3,
            "priority": "low",
            "instructions": "1. eBird login → 2. Request API key → 3. Get key via email",
            },
        "petfinder": {
        "name": "Petfinder API",
            "signup_url": "https://www.petfinder.com / developers/",
            "login_url": "https://www.petfinder.com / user / login/",
            "env_var": "PETFINDER_KEY",
            "cost": "FREE",
            "phase": 3,
            "priority": "low",
            "instructions": "1. Petfinder login → 2. Register app → 3. Get API key and secret",
            },
        "openweather": {
        "name": "OpenWeatherMap",
            "signup_url": "https://openweathermap.org / api",
            "login_url": "https://home.openweathermap.org / users / sign_in",
            "env_var": "OPENWEATHER_API_KEY",
            "cost": "FREEMIUM",
            "phase": 3,
            "priority": "medium",
            "instructions": "1. Sign up → 2. API keys section → 3. Generate key",
            },
        "unsplash": {
        "name": "Unsplash API",
            "signup_url": "https://unsplash.com / developers",
            "login_url": "https://unsplash.com / login",
            "env_var": "UNSPLASH_ACCESS_KEY",
            "cost": "FREE",
            "phase": 3,
            "priority": "medium",
            "instructions": "1. Unsplash login → 2. Create new app → 3. Get access key",
            },
        # Phase 4: Business APIs
    "stripe": {
        "name": "Stripe",
            "signup_url": "https://dashboard.stripe.com / register",
            "login_url": "https://dashboard.stripe.com / login",
            "env_var": "STRIPE_PUBLISHABLE_KEY",
            "cost": "FREEMIUM",
            "phase": 4,
            "priority": "medium",
            "instructions": "1. Sign up → 2. Developers → 3. API keys → 4. Get publishable and secret keys",
            },
        "calendly": {
        "name": "Calendly",
            "signup_url": "https://calendly.com/",
            "login_url": "https://calendly.com / login",
            "env_var": "CALENDLY_TOKEN",
            "cost": "FREEMIUM",
            "phase": 4,
            "priority": "low",
            "instructions": "1. Sign up → 2. Integrations → 3. API & Webhooks → 4. Generate token",
            },
        "mailchimp": {
        "name": "Mailchimp",
            "signup_url": "https://mailchimp.com/",
            "login_url": "https://login.mailchimp.com/",
            "env_var": "MAILCHIMP_API_KEY",
            "cost": "FREEMIUM",
            "phase": 4,
            "priority": "medium",
            "instructions": "1. Sign up → 2. Account → 3. Extras → 4. API keys → 5. Create key",
            },
        "hubspot": {
        "name": "HubSpot",
            "signup_url": "https://www.hubspot.com/",
            "login_url": "https://app.hubspot.com / login",
            "env_var": "HUBSPOT_API_KEY",
            "cost": "FREEMIUM",
            "phase": 4,
            "priority": "low",
            "instructions": "1. Sign up → 2. Settings → 3. Integrations → 4. API key",
            },
        "airtable": {
        "name": "Airtable",
            "signup_url": "https://airtable.com/",
            "login_url": "https://airtable.com / login",
            "env_var": "AIRTABLE_API_KEY",
            "cost": "FREEMIUM",
            "phase": 4,
            "priority": "low",
            "instructions": "1. Sign up → 2. Account → 3. Generate API key",
            },
        "notion": {
        "name": "Notion",
            "signup_url": "https://www.notion.so/",
            "login_url": "https://www.notion.so / login",
            "env_var": "NOTION_API_KEY",
            "cost": "FREEMIUM",
            "phase": 4,
            "priority": "low",
            "instructions": "1. Sign up → 2. Settings → 3. Integrations → 4. Create integration",
            },
}


class APIRegistrationManager:


    def __init__(self):
        self.env_file = ".env"
        self.progress_file = "api_registration_progress.json"
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
            json.dump(self.progress, f, indent = 2)


    def mark_registered(self, api_key: str, api_token: str = None):
        """Mark an API as registered with its key"""
        self.progress[api_key] = {
            "registered": True,
                "timestamp": datetime.now().isoformat(),
                "has_key": bool(api_token),
                }
        self.save_progress()


    def is_registered(self, api_key: str) -> bool:
        """Check if an API is already registered"""
        return self.progress.get(api_key, {}).get("registered", False)


    def open_registration_page(self, api_key: str):
        """Open the registration page for an API"""
        if api_key not in API_REGISTRY:
            print(f"❌ Unknown API: {api_key}")
            return False

        api_info = API_REGISTRY[api_key]

        if self.is_registered(api_key):
            print(f"✅ {api_info['name']} is already registered")
            return True

        print(f"\n🚀 Opening registration for {api_info['name']}")
        print(f"📋 Instructions: {api_info['instructions']}")
        print(f"💰 Cost: {api_info['cost']}")
        print(f"🔑 Environment Variable: {api_info['env_var']}")

        # Open signup page
        webbrowser.open(api_info["signup_url"])

        # Wait for user confirmation
        input(f"\n⏳ Press Enter after you've registered for {api_info['name']}...")

        # Prompt for API key
        api_token = input(
            f"🔑 Enter your {api_info['name']} API key (or press Enter to skip): "
        ).strip()

        if api_token:
            self.update_env_file(api_info["env_var"], api_token)
            print(f"✅ Added {api_info['env_var']} to .env file")

        self.mark_registered(api_key, api_token)
        print(f"✅ {api_info['name']} registration completed!")

        return True


    def update_env_file(self, env_var: str, value: str):
        """Update or add environment variable to .env file"""
        env_lines = []
        updated = False

        # Read existing .env file
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
        phase_apis = [k for k, v in API_REGISTRY.items() if v["phase"] == phase]

        if not phase_apis:
            print(f"❌ No APIs found for phase {phase}")
            return

        print(f"\n🎯 Starting Phase {phase} Registration")
        print(f"📊 Found {len(phase_apis)} APIs to register")

        for api_key in phase_apis:
            api_info = API_REGISTRY[api_key]
            print(f"\n{'='*50}")
            print(f"📋 {api_info['name']} ({api_info['cost']})")

            if self.is_registered(api_key):
                print(f"✅ Already registered, skipping...")
                continue

            proceed = input(
                f"🤔 Register for {api_info['name']}? (y / n/s = skip): "
            ).lower()

            if proceed == "y":
                self.open_registration_page(api_key)
            elif proceed == "s":
                print(f"⏭️  Skipping {api_info['name']}")
                continue
            else:
                print(f"❌ Stopping phase {phase} registration")
                break

        print(f"\n🎉 Phase {phase} registration completed!")


    def batch_register(self, api_keys: List[str]):
        """Register multiple APIs in batch"""
        print(f"\n🚀 Batch registering {len(api_keys)} APIs")

        for api_key in api_keys:
            if api_key in API_REGISTRY:
                self.open_registration_page(api_key)
                time.sleep(2)  # Brief pause between registrations
            else:
                print(f"❌ Unknown API: {api_key}")


    def show_status(self):
        """Show registration status for all APIs"""
        print("\n📊 API Registration Status")
        print("=" * 60)

        phases = {}
        for api_key, api_info in API_REGISTRY.items():
            phase = api_info["phase"]
            if phase not in phases:
                phases[phase] = []
            phases[phase].append((api_key, api_info))

        for phase in sorted(phases.keys()):
            print(f"\n🎯 Phase {phase}:")
            for api_key, api_info in phases[phase]:
                status = "✅" if self.is_registered(api_key) else "❌"
                print(f"  {status} {api_info['name']} ({api_info['cost']})")

        # Summary
        total_apis = len(API_REGISTRY)
        registered_count = len(
            [k for k in API_REGISTRY.keys() if self.is_registered(k)]
        )
        print(
            f"\n📈 Progress: {registered_count}/{total_apis} APIs registered ({registered_count / total_apis * 100:.1f}%)"
        )


    def generate_env_template(self):
        """Generate .env template with all API variables"""
        template_file = ".env.template"

        with open(template_file, "w") as f:
            f.write("# API Registration Template\n")
            f.write(f"# Generated on {datetime.now().isoformat()}\n\n")

            phases = {}
            for api_key, api_info in API_REGISTRY.items():
                phase = api_info["phase"]
                if phase not in phases:
                    phases[phase] = []
                phases[phase].append((api_key, api_info))

            for phase in sorted(phases.keys()):
                f.write(f"\n# Phase {phase} APIs\n")
                for api_key, api_info in phases[phase]:
                    f.write(f"# {api_info['name']} ({api_info['cost']})\n")
                    f.write(f"{api_info['env_var']}=\n")

        print(f"✅ Generated {template_file} with all API variables")


def main():
    parser = argparse.ArgumentParser(description="API Registration Automation")
    parser.add_argument(
        "--phase", type = int, help="Register all APIs in a specific phase (1 - 4)"
    )
    parser.add_argument("--api", type = str, help="Register a specific API")
    parser.add_argument("--batch - register", nargs="+", help="Register multiple APIs")
    parser.add_argument(
        "--status", action="store_true", help="Show registration status"
    )
    parser.add_argument(
        "--template", action="store_true", help="Generate .env template"
    )
    parser.add_argument("--list", action="store_true", help="List all available APIs")

    args = parser.parse_args()

    manager = APIRegistrationManager()

    if args.status:
        manager.show_status()
    elif args.template:
        manager.generate_env_template()
    elif args.list:
        print("\n📋 Available APIs:")
        for api_key, api_info in API_REGISTRY.items():
            print(
                f"  {api_key}: {api_info['name']} (Phase {api_info['phase']}, {api_info['cost']})"
            )
    elif args.phase:
        manager.register_phase(args.phase)
    elif args.api:
        manager.open_registration_page(args.api)
    elif args.batch_register:
        manager.batch_register(args.batch_register)
    else:
        # Interactive mode
        print("\n🚀 API Registration Automation")
        print("Choose an option:")
        print("1. Register Phase 1 APIs (Essential Free)")
        print("2. Register Phase 2 APIs (Social Media)")
        print("3. Register Phase 3 APIs (Specialized)")
        print("4. Register Phase 4 APIs (Business)")
        print("5. Show registration status")
        print("6. Register specific API")
        print("7. Generate .env template")

        choice = input("\nEnter your choice (1 - 7): ").strip()

        if choice == "1":
            manager.register_phase(1)
        elif choice == "2":
            manager.register_phase(2)
        elif choice == "3":
            manager.register_phase(3)
        elif choice == "4":
            manager.register_phase(4)
        elif choice == "5":
            manager.show_status()
        elif choice == "6":
            api_key = input("Enter API key: ").strip()
            manager.open_registration_page(api_key)
        elif choice == "7":
            manager.generate_env_template()
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    main()
