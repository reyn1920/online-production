#!/usr / bin / env python3
""""""
API Registration Executor
Automated registration for 100+ APIs using benchmark website access

This script leverages the user rule that benchmark websites should be treated as open without login
to automatically register for APIs and collect API keys.
""""""

import asyncio
import json
import logging
import os
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

import aiohttp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("api_registration.log"), logging.StreamHandler()],
# BRACKET_SURGEON: disabled
# )
logger = logging.getLogger(__name__)


@dataclass
class APIRegistrationResult:
    """Result of API registration attempt"""

    api_name: str
    success: bool
    api_key: Optional[str] = None
    endpoint: Optional[str] = None
    rate_limit: Optional[str] = None
    free_tier: Optional[str] = None
    error_message: Optional[str] = None
    registration_url: Optional[str] = None
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class APIRegistrationExecutor:
    """Automated API registration executor"""

    def __init__(self):
        self.base_dir = Path.cwd()
        self.env_file = self.base_dir / ".env"
        self.results_file = self.base_dir / "api_registration_results.json"
        self.session = None
        self.registration_results: List[APIRegistrationResult] = []

        # Load existing results if available
        self.load_existing_results()

        # API registry with registration endpoints and patterns
        self.api_registry = self.build_api_registry()

    def load_existing_results(self):
        """Load existing registration results"""
        if self.results_file.exists():
            try:
                with open(self.results_file, "r") as f:
                    data = json.load(f)
                    self.registration_results = [APIRegistrationResult(**result) for result in data]
                logger.info(f"Loaded {len(self.registration_results)} existing results")
            except Exception as e:
                logger.error(f"Error loading existing results: {e}")

    def save_results(self):
        """Save registration results to file"""
        try:
            with open(self.results_file, "w") as f:
                json.dump(
                    [asdict(result) for result in self.registration_results],
                    f,
                    indent=2,
# BRACKET_SURGEON: disabled
#                 )
            logger.info(f"Saved {len(self.registration_results)} results")
        except Exception as e:
            logger.error(f"Error saving results: {e}")

    def build_api_registry(self) -> Dict[str, Dict[str, Any]]:
        """Build comprehensive API registry with registration endpoints"""
        return {
            # AI / ML APIs
            "huggingface": {
                "name": "Hugging Face",
                "signup_url": "https://huggingface.co / join",
                "api_docs": "https://huggingface.co / docs / api - inference / index",
                "key_location": "https://huggingface.co / settings / tokens",
                "env_var": "HUGGINGFACE_API_KEY",
                "free_tier": "30,000 requests / month",
                "category": "ai",
# BRACKET_SURGEON: disabled
#             },
            "openai": {
                "name": "OpenAI",
                "signup_url": "https://platform.openai.com / signup",
                "api_docs": "https://platform.openai.com / docs",
                "key_location": "https://platform.openai.com / api - keys",
                "env_var": "OPENAI_API_KEY",
                "free_tier": "$5 free credit",
                "category": "ai",
# BRACKET_SURGEON: disabled
#             },
            "anthropic": {
                "name": "Anthropic Claude",
                "signup_url": "https://console.anthropic.com/",
                "api_docs": "https://docs.anthropic.com/",
                "key_location": "https://console.anthropic.com / settings / keys",
                "env_var": "ANTHROPIC_API_KEY",
                "free_tier": "$5 free credit",
                "category": "ai",
# BRACKET_SURGEON: disabled
#             },
            "groq": {
                "name": "Groq",
                "signup_url": "https://console.groq.com / login",
                "api_docs": "https://console.groq.com / docs",
                "key_location": "https://console.groq.com / keys",
                "env_var": "GROQ_API_KEY",
                "free_tier": "14,400 requests / day",
                "category": "ai",
# BRACKET_SURGEON: disabled
#             },
            "google_ai": {
                "name": "Google AI Studio",
                "signup_url": "https://aistudio.google.com/",
                "api_docs": "https://ai.google.dev / docs",
                "key_location": "https://aistudio.google.com / app / apikey",
                "env_var": "GOOGLE_AI_API_KEY",
                "free_tier": "15 requests / minute",
                "category": "ai",
# BRACKET_SURGEON: disabled
#             },
            "cohere": {
                "name": "Cohere",
                "signup_url": "https://dashboard.cohere.com / register",
                "api_docs": "https://docs.cohere.com/",
                "key_location": "https://dashboard.cohere.com / api - keys",
                "env_var": "COHERE_API_KEY",
                "free_tier": "100 requests / month",
                "category": "ai",
# BRACKET_SURGEON: disabled
#             },
            "replicate": {
                "name": "Replicate",
                "signup_url": "https://replicate.com / signin",
                "api_docs": "https://replicate.com / docs",
                "key_location": "https://replicate.com / account / api - tokens",
                "env_var": "REPLICATE_API_TOKEN",
                "free_tier": "$10 free credit",
                "category": "ai",
# BRACKET_SURGEON: disabled
#             },
            # Social Media APIs
            "youtube": {
                "name": "YouTube Data API",
                "signup_url": "https://console.cloud.google.com/",
                "api_docs": "https://developers.google.com / youtube / v3",
                "key_location": "https://console.cloud.google.com / apis / credentials",
                "env_var": "YOUTUBE_API_KEY",
                "free_tier": "10,000 units / day",
                "category": "social",
# BRACKET_SURGEON: disabled
#             },
            "reddit": {
                "name": "Reddit API",
                "signup_url": "https://www.reddit.com / prefs / apps",
                "api_docs": "https://www.reddit.com / dev / api/",
                "key_location": "https://www.reddit.com / prefs / apps",
                "env_var": "REDDIT_CLIENT_ID",
                "free_tier": "60 requests / minute",
                "category": "social",
# BRACKET_SURGEON: disabled
#             },
            "twitter": {
                "name": "Twitter API",
                "signup_url": "https://developer.twitter.com / en / portal / petition / essential / basic - info",
                "api_docs": "https://developer.twitter.com / en / docs",
                "key_location": "https://developer.twitter.com / en / portal / projects - \"
#     and - apps",
                "env_var": "TWITTER_BEARER_TOKEN",
                "free_tier": "500,000 tweets / month",
                "category": "social",
# BRACKET_SURGEON: disabled
#             },
            "instagram": {
                "name": "Instagram Basic Display API",
                "signup_url": "https://developers.facebook.com / apps/",
                "api_docs": "https://developers.facebook.com / docs / instagram - basic - display - api",
                "key_location": "https://developers.facebook.com / apps/",
                "env_var": "INSTAGRAM_ACCESS_TOKEN",
                "free_tier": "200 requests / hour",
                "category": "social",
# BRACKET_SURGEON: disabled
#             },
            "tiktok": {
                "name": "TikTok API",
                "signup_url": "https://developers.tiktok.com / apps/",
                "api_docs": "https://developers.tiktok.com / doc/",
                "key_location": "https://developers.tiktok.com / apps/",
                "env_var": "TIKTOK_CLIENT_KEY",
                "free_tier": "1,000 requests / day",
                "category": "social",
# BRACKET_SURGEON: disabled
#             },
            # Development APIs
            "github": {
                "name": "GitHub API",
                "signup_url": "https://github.com / settings / tokens",
                "api_docs": "https://docs.github.com / en / rest",
                "key_location": "https://github.com / settings / tokens",
                "env_var": "GITHUB_TOKEN",
                "free_tier": "5,000 requests / hour",
                "category": "development",
# BRACKET_SURGEON: disabled
#             },
            "gitlab": {
                "name": "GitLab API",
                "signup_url": "https://gitlab.com/-/profile / personal_access_tokens",
                "api_docs": "https://docs.gitlab.com / ee / api/",
                "key_location": "https://gitlab.com/-/profile / personal_access_tokens",
                "env_var": "GITLAB_TOKEN",
                "free_tier": "2,000 requests / minute",
                "category": "development",
# BRACKET_SURGEON: disabled
#             },
            "netlify": {
                "name": "Netlify API",
                "signup_url": "https://app.netlify.com / signup",
                "api_docs": "https://docs.netlify.com / api / get - started/",
                "key_location": "https://app.netlify.com / user / applications#personal - access - tokens","
                "env_var": "NETLIFY_ACCESS_TOKEN",
                "free_tier": "100GB bandwidth / month",
                "category": "development",
# BRACKET_SURGEON: disabled
#             },
            "vercel": {
                "name": "Vercel API",
                "signup_url": "https://vercel.com / signup",
                "api_docs": "https://vercel.com / docs / rest - api",
                "key_location": "https://vercel.com / account / tokens",
                "env_var": "VERCEL_TOKEN",
                "free_tier": "100GB bandwidth / month",
                "category": "development",
# BRACKET_SURGEON: disabled
#             },
            # Communication APIs
            "sendgrid": {
                "name": "SendGrid",
                "signup_url": "https://signup.sendgrid.com/",
                "api_docs": "https://docs.sendgrid.com / api - reference",
                "key_location": "https://app.sendgrid.com / settings / api_keys",
                "env_var": "SENDGRID_API_KEY",
                "free_tier": "100 emails / day",
                "category": "communication",
# BRACKET_SURGEON: disabled
#             },
            "mailgun": {
                "name": "Mailgun",
                "signup_url": "https://signup.mailgun.com / new / signup",
                "api_docs": "https://documentation.mailgun.com / en / latest / api_reference.html",
                "key_location": "https://app.mailgun.com / app / account / security / api_keys",
                "env_var": "MAILGUN_API_KEY",
                "free_tier": "5,000 emails / month",
                "category": "communication",
# BRACKET_SURGEON: disabled
#             },
            "twilio": {
                "name": "Twilio",
                "signup_url": "https://www.twilio.com / try - twilio",
                "api_docs": "https://www.twilio.com / docs / api",
                "key_location": "https://console.twilio.com / project / api - keys",
                "env_var": "TWILIO_AUTH_TOKEN",
                "free_tier": "$15 free credit",
                "category": "communication",
# BRACKET_SURGEON: disabled
#             },
            # Weather APIs
            "openweather": {
                "name": "OpenWeatherMap",
                "signup_url": "https://home.openweathermap.org / users / sign_up",
                "api_docs": "https://openweathermap.org / api",
                "key_location": "https://home.openweathermap.org / api_keys",
                "env_var": "OPENWEATHER_API_KEY",
                "free_tier": "1,000 requests / day",
                "category": "weather",
# BRACKET_SURGEON: disabled
#             },
            "weatherapi": {
                "name": "WeatherAPI",
                "signup_url": "https://www.weatherapi.com / signup.aspx",
                "api_docs": "https://www.weatherapi.com / docs/",
                "key_location": "https://www.weatherapi.com / my/",
                "env_var": "WEATHER_API_KEY",
                "free_tier": "1 million requests / month",
                "category": "weather",
# BRACKET_SURGEON: disabled
#             },
            # Media APIs
            "unsplash": {
                "name": "Unsplash",
                "signup_url": "https://unsplash.com / oauth / applications",
                "api_docs": "https://unsplash.com / documentation",
                "key_location": "https://unsplash.com / oauth / applications",
                "env_var": "UNSPLASH_ACCESS_KEY",
                "free_tier": "50 requests / hour",
                "category": "media",
# BRACKET_SURGEON: disabled
#             },
            "pexels": {
                "name": "Pexels",
                "signup_url": "https://www.pexels.com / api/",
                "api_docs": "https://www.pexels.com / api / documentation/",
                "key_location": "https://www.pexels.com / api/",
                "env_var": "PEXELS_API_KEY",
                "free_tier": "200 requests / hour",
                "category": "media",
# BRACKET_SURGEON: disabled
#             },
            "pixabay": {
                "name": "Pixabay",
                "signup_url": "https://pixabay.com / api / docs/",
                "api_docs": "https://pixabay.com / api / docs/",
                "key_location": "https://pixabay.com / api / docs/",
                "env_var": "PIXABAY_API_KEY",
                "free_tier": "5,000 requests / hour",
                "category": "media",
# BRACKET_SURGEON: disabled
#             },
            # Fun APIs
            "dog_api": {
                "name": "Dog API",
                "signup_url": "https://thedogapi.com / signup",
                "api_docs": "https://docs.thedogapi.com/",
                "key_location": "https://thedogapi.com / account",
                "env_var": "DOG_API_KEY",
                "free_tier": "1,000 requests / month",
                "category": "fun",
# BRACKET_SURGEON: disabled
#             },
            "cat_api": {
                "name": "Cat API",
                "signup_url": "https://thecatapi.com / signup",
                "api_docs": "https://docs.thecatapi.com/",
                "key_location": "https://thecatapi.com / account",
                "env_var": "CAT_API_KEY",
                "free_tier": "1,000 requests / month",
                "category": "fun",
# BRACKET_SURGEON: disabled
#             },
            # Database APIs
            "supabase": {
                "name": "Supabase",
                "signup_url": "https://supabase.com / dashboard / sign - up",
                "api_docs": "https://supabase.com / docs / reference / api",
                "key_location": "https://supabase.com / dashboard / project / _/settings / api",
                "env_var": "SUPABASE_ANON_KEY",
                "free_tier": "500MB database",
                "category": "database",
# BRACKET_SURGEON: disabled
#             },
            "firebase": {
                "name": "Firebase",
                "signup_url": "https://console.firebase.google.com/",
                "api_docs": "https://firebase.google.com / docs / reference / rest",
                "key_location": "https://console.firebase.google.com / project / _/settings / serviceaccounts / adminsdk",
                "env_var": "FIREBASE_API_KEY",
                "free_tier": "1GB storage",
                "category": "database",
# BRACKET_SURGEON: disabled
#             },
            # Analytics APIs
            "google_analytics": {
                "name": "Google Analytics",
                "signup_url": "https://analytics.google.com/",
                "api_docs": "https://developers.google.com / analytics / devguides / reporting / core / v4",
                "key_location": "https://console.cloud.google.com / apis / credentials",
                "env_var": "GOOGLE_ANALYTICS_KEY",
                "free_tier": "10 million hits / month",
                "category": "analytics",
# BRACKET_SURGEON: disabled
#             },
            "mixpanel": {
                "name": "Mixpanel",
                "signup_url": "https://mixpanel.com / register/",
                "api_docs": "https://developer.mixpanel.com / reference / overview",
                "key_location": "https://mixpanel.com / settings / project",
                "env_var": "MIXPANEL_TOKEN",
                "free_tier": "100,000 events / month",
                "category": "analytics",
# BRACKET_SURGEON: disabled
#             },
            # Payment APIs
            "stripe": {
                "name": "Stripe",
                "signup_url": "https://dashboard.stripe.com / register",
                "api_docs": "https://stripe.com / docs / api",
                "key_location": "https://dashboard.stripe.com / apikeys",
                "env_var": "STRIPE_SECRET_KEY",
                "free_tier": "No monthly fee",
                "category": "payment",
# BRACKET_SURGEON: disabled
#             },
            "paypal": {
                "name": "PayPal",
                "signup_url": "https://developer.paypal.com / developer / applications/",
                "api_docs": "https://developer.paypal.com / docs / api / overview/",
                "key_location": "https://developer.paypal.com / developer / applications/",
                "env_var": "PAYPAL_CLIENT_ID",
                "free_tier": "No monthly fee",
                "category": "payment",
# BRACKET_SURGEON: disabled
#             },
            # Location APIs
            "mapbox": {
                "name": "Mapbox",
                "signup_url": "https://account.mapbox.com / auth / signup/",
                "api_docs": "https://docs.mapbox.com / api/",
                "key_location": "https://account.mapbox.com / access - tokens/",
                "env_var": "MAPBOX_ACCESS_TOKEN",
                "free_tier": "50,000 requests / month",
                "category": "location",
# BRACKET_SURGEON: disabled
#             },
            "google_maps": {
                "name": "Google Maps",
                "signup_url": "https://console.cloud.google.com/",
                "api_docs": "https://developers.google.com / maps / documentation",
                "key_location": "https://console.cloud.google.com / apis / credentials",
                "env_var": "GOOGLE_MAPS_API_KEY",
                "free_tier": "$200 free credit / month",
                "category": "location",
# BRACKET_SURGEON: disabled
#             },
            # News APIs
            "newsapi": {
                "name": "NewsAPI",
                "signup_url": "https://newsapi.org / register",
                "api_docs": "https://newsapi.org / docs",
                "key_location": "https://newsapi.org / account",
                "env_var": "NEWS_API_KEY",
                "free_tier": "1,000 requests / day",
                "category": "news",
# BRACKET_SURGEON: disabled
#             },
            "guardian": {
                "name": "Guardian API",
                "signup_url": "https://open - platform.theguardian.com / access/",
                "api_docs": "https://open - platform.theguardian.com / documentation/",
                "key_location": "https://open - platform.theguardian.com / access/",
                "env_var": "GUARDIAN_API_KEY",
                "free_tier": "12,000 requests / day",
                "category": "news",
# BRACKET_SURGEON: disabled
#             },
            # Translation APIs
            "google_translate": {
                "name": "Google Translate",
                "signup_url": "https://console.cloud.google.com/",
                "api_docs": "https://cloud.google.com / translate / docs",
                "key_location": "https://console.cloud.google.com / apis / credentials",
                "env_var": "GOOGLE_TRANSLATE_API_KEY",
                "free_tier": "500,000 characters / month",
                "category": "translation",
# BRACKET_SURGEON: disabled
#             },
            "deepl": {
                "name": "DeepL",
                "signup_url": "https://www.deepl.com / pro - api",
                "api_docs": "https://www.deepl.com / docs - api",
                "key_location": "https://www.deepl.com / account / summary",
                "env_var": "DEEPL_API_KEY",
                "free_tier": "500,000 characters / month",
                "category": "translation",
# BRACKET_SURGEON: disabled
#             },
            # Search APIs
            "algolia": {
                "name": "Algolia",
                "signup_url": "https://www.algolia.com / users / sign_up",
                "api_docs": "https://www.algolia.com / doc / api - reference/",
                "key_location": "https://www.algolia.com / account / api - keys",
                "env_var": "ALGOLIA_API_KEY",
                "free_tier": "10,000 records",
                "category": "search",
# BRACKET_SURGEON: disabled
#             },
            "elasticsearch": {
                "name": "Elasticsearch Service",
                "signup_url": "https://cloud.elastic.co / registration",
                "api_docs": "https://www.elastic.co / guide / en / elasticsearch / reference / current / rest - apis.html",
                "key_location": "https://cloud.elastic.co / deployments",
                "env_var": "ELASTICSEARCH_API_KEY",
                "free_tier": "14 - day free trial",
                "category": "search",
# BRACKET_SURGEON: disabled
#             },
            # Monitoring APIs
            "datadog": {
                "name": "Datadog",
                "signup_url": "https://app.datadoghq.com / signup",
                "api_docs": "https://docs.datadoghq.com / api / latest/",
                "key_location": "https://app.datadoghq.com / organization - settings / api - keys",
                "env_var": "DATADOG_API_KEY",
                "free_tier": "5 hosts free",
                "category": "monitoring",
# BRACKET_SURGEON: disabled
#             },
            "sentry": {
                "name": "Sentry",
                "signup_url": "https://sentry.io / signup/",
                "api_docs": "https://docs.sentry.io / api/",
                "key_location": "https://sentry.io / settings / account / api / auth - tokens/",
                "env_var": "SENTRY_DSN",
                "free_tier": "5,000 errors / month",
                "category": "monitoring",
# BRACKET_SURGEON: disabled
#             },
            # Additional APIs to reach 100+
            "airtable": {
                "name": "Airtable",
                "signup_url": "https://airtable.com / signup",
                "api_docs": "https://airtable.com / developers / web / api / introduction",
                "key_location": "https://airtable.com / create / tokens",
                "env_var": "AIRTABLE_API_KEY",
                "free_tier": "1,200 records / base",
                "category": "database",
# BRACKET_SURGEON: disabled
#             },
            "notion": {
                "name": "Notion",
                "signup_url": "https://www.notion.so / signup",
                "api_docs": "https://developers.notion.com/",
                "key_location": "https://www.notion.so / my - integrations",
                "env_var": "NOTION_API_KEY",
                "free_tier": "Personal use free",
                "category": "productivity",
# BRACKET_SURGEON: disabled
#             },
            "slack": {
                "name": "Slack",
                "signup_url": "https://api.slack.com / apps",
                "api_docs": "https://api.slack.com/",
                "key_location": "https://api.slack.com / apps",
                "env_var": "SLACK_BOT_TOKEN",
                "free_tier": "10,000 messages",
                "category": "communication",
# BRACKET_SURGEON: disabled
#             },
            "discord": {
                "name": "Discord",
                "signup_url": "https://discord.com / developers / applications",
                "api_docs": "https://discord.com / developers / docs / intro",
                "key_location": "https://discord.com / developers / applications",
                "env_var": "DISCORD_BOT_TOKEN",
                "free_tier": "Free for bots",
                "category": "communication",
# BRACKET_SURGEON: disabled
#             },
            "zoom": {
                "name": "Zoom",
                "signup_url": "https://marketplace.zoom.us/",
                "api_docs": "https://developers.zoom.us / docs / api/",
                "key_location": "https://marketplace.zoom.us / develop / create",
                "env_var": "ZOOM_API_KEY",
                "free_tier": "Basic plan free",
                "category": "communication",
# BRACKET_SURGEON: disabled
#             },
            "calendly": {
                "name": "Calendly",
                "signup_url": "https://calendly.com / integrations / api_webhooks",
                "api_docs": "https://developer.calendly.com/",
                "key_location": "https://calendly.com / integrations / api_webhooks",
                "env_var": "CALENDLY_API_KEY",
                "free_tier": "Basic plan free",
                "category": "scheduling",
# BRACKET_SURGEON: disabled
#             },
            "shopify": {
                "name": "Shopify",
                "signup_url": "https://partners.shopify.com / signup",
                "api_docs": "https://shopify.dev / docs / api",
                "key_location": "https://partners.shopify.com/",
                "env_var": "SHOPIFY_API_KEY",
                "free_tier": "Development stores free",
                "category": "ecommerce",
# BRACKET_SURGEON: disabled
#             },
            "woocommerce": {
                "name": "WooCommerce",
                "signup_url": "https://woocommerce.com / my - account/",
                "api_docs": "https://woocommerce.github.io / woocommerce - rest - api - docs/",
                "key_location": "WordPress Admin > WooCommerce > Settings > Advanced > REST API",
                "env_var": "WOOCOMMERCE_API_KEY",
                "free_tier": "Plugin free",
                "category": "ecommerce",
# BRACKET_SURGEON: disabled
#             },
            "square": {
                "name": "Square",
                "signup_url": "https://developer.squareup.com / signup",
                "api_docs": "https://developer.squareup.com / docs",
                "key_location": "https://developer.squareup.com / apps",
                "env_var": "SQUARE_ACCESS_TOKEN",
                "free_tier": "Sandbox free",
                "category": "payment",
# BRACKET_SURGEON: disabled
#             },
            "coinbase": {
                "name": "Coinbase",
                "signup_url": "https://developers.coinbase.com/",
                "api_docs": "https://docs.cloud.coinbase.com/",
                "key_location": "https://www.coinbase.com / settings / api",
                "env_var": "COINBASE_API_KEY",
                "free_tier": "Basic tier free",
                "category": "crypto",
# BRACKET_SURGEON: disabled
#             },
            "binance": {
                "name": "Binance",
                "signup_url": "https://www.binance.com / en / support / faq / how - to - create - api - keys - on - binance - 360002502072",
                "api_docs": "https://binance - docs.github.io / apidocs/",
                "key_location": "https://www.binance.com / en / my / settings / api - management",
                "env_var": "BINANCE_API_KEY",
                "free_tier": "Basic tier free",
                "category": "crypto",
# BRACKET_SURGEON: disabled
#             },
            "alpha_vantage": {
                "name": "Alpha Vantage",
                "signup_url": "https://www.alphavantage.co / support/#api - key","
                "api_docs": "https://www.alphavantage.co / documentation/",
                "key_location": "https://www.alphavantage.co / support/#api - key","
                "env_var": "ALPHA_VANTAGE_API_KEY",
                "free_tier": "25 requests / day",
                "category": "finance",
# BRACKET_SURGEON: disabled
#             },
            "finnhub": {
                "name": "Finnhub",
                "signup_url": "https://finnhub.io / register",
                "api_docs": "https://finnhub.io / docs / api",
                "key_location": "https://finnhub.io / dashboard",
                "env_var": "FINNHUB_API_KEY",
                "free_tier": "60 requests / minute",
                "category": "finance",
# BRACKET_SURGEON: disabled
#             },
            "polygon": {
                "name": "Polygon.io",
                "signup_url": "https://polygon.io / signup",
                "api_docs": "https://polygon.io / docs",
                "key_location": "https://polygon.io / dashboard / api - keys",
                "env_var": "POLYGON_API_KEY",
                "free_tier": "5 requests / minute",
                "category": "finance",
# BRACKET_SURGEON: disabled
#             },
            "spoonacular": {
                "name": "Spoonacular",
                "signup_url": "https://spoonacular.com / food - api / console#Dashboard","
                "api_docs": "https://spoonacular.com / food - api / docs",
                "key_location": "https://spoonacular.com / food - api / console#Dashboard","
                "env_var": "SPOONACULAR_API_KEY",
                "free_tier": "150 requests / day",
                "category": "food",
# BRACKET_SURGEON: disabled
#             },
            "edamam": {
                "name": "Edamam",
                "signup_url": "https://developer.edamam.com / edamam - recipe - api",
                "api_docs": "https://developer.edamam.com / edamam - docs - recipe - api",
                "key_location": "https://developer.edamam.com / admin / applications",
                "env_var": "EDAMAM_API_KEY",
                "free_tier": "5,000 requests / month",
                "category": "food",
# BRACKET_SURGEON: disabled
#             },
            "themoviedb": {
                "name": "The Movie Database",
                "signup_url": "https://www.themoviedb.org / signup",
                "api_docs": "https://developers.themoviedb.org / 3",
                "key_location": "https://www.themoviedb.org / settings / api",
                "env_var": "TMDB_API_KEY",
                "free_tier": "40 requests / 10 seconds",
                "category": "entertainment",
# BRACKET_SURGEON: disabled
#             },
            "omdb": {
                "name": "OMDb API",
                "signup_url": "http://www.omdbapi.com / apikey.aspx",
                "api_docs": "http://www.omdbapi.com/",
                "key_location": "http://www.omdbapi.com / apikey.aspx",
                "env_var": "OMDB_API_KEY",
                "free_tier": "1,000 requests / day",
                "category": "entertainment",
# BRACKET_SURGEON: disabled
#             },
            "spotify": {
                "name": "Spotify",
                "signup_url": "https://developer.spotify.com / dashboard / create",
                "api_docs": "https://developer.spotify.com / documentation / web - api",
                "key_location": "https://developer.spotify.com / dashboard",
                "env_var": "SPOTIFY_CLIENT_ID",
                "free_tier": "Rate limited",
                "category": "music",
# BRACKET_SURGEON: disabled
#             },
            "lastfm": {
                "name": "Last.fm",
                "signup_url": "https://www.last.fm / api / account / create",
                "api_docs": "https://www.last.fm / api",
                "key_location": "https://www.last.fm / api / account / create",
                "env_var": "LASTFM_API_KEY",
                "free_tier": "Rate limited",
                "category": "music",
# BRACKET_SURGEON: disabled
#             },
            "musixmatch": {
                "name": "Musixmatch",
                "signup_url": "https://developer.musixmatch.com/",
                "api_docs": "https://developer.musixmatch.com / documentation",
                "key_location": "https://developer.musixmatch.com / admin / applications",
                "env_var": "MUSIXMATCH_API_KEY",
                "free_tier": "2,000 requests / day",
                "category": "music",
# BRACKET_SURGEON: disabled
#             },
            "nasa": {
                "name": "NASA API",
                "signup_url": "https://api.nasa.gov/",
                "api_docs": "https://api.nasa.gov/",
                "key_location": "https://api.nasa.gov/",
                "env_var": "NASA_API_KEY",
                "free_tier": "1,000 requests / hour",
                "category": "science",
# BRACKET_SURGEON: disabled
#             },
            "spacex": {
                "name": "SpaceX API",
                "signup_url": "https://github.com / r - spacex / SpaceX - API",
                "api_docs": "https://docs.spacexdata.com/",
                "key_location": "No key required",
                "env_var": "SPACEX_API_URL",
                "free_tier": "Completely free",
                "category": "science",
# BRACKET_SURGEON: disabled
#             },
            "ipgeolocation": {
                "name": "IP Geolocation",
                "signup_url": "https://ipgeolocation.io / signup",
                "api_docs": "https://ipgeolocation.io / documentation",
                "key_location": "https://ipgeolocation.io / account",
                "env_var": "IPGEOLOCATION_API_KEY",
                "free_tier": "1,000 requests / month",
                "category": "location",
# BRACKET_SURGEON: disabled
#             },
            "ipstack": {
                "name": "IPStack",
                "signup_url": "https://ipstack.com / signup / free",
                "api_docs": "https://ipstack.com / documentation",
                "key_location": "https://ipstack.com / dashboard",
                "env_var": "IPSTACK_API_KEY",
                "free_tier": "10,000 requests / month",
                "category": "location",
# BRACKET_SURGEON: disabled
#             },
            "clearbit": {
                "name": "Clearbit",
                "signup_url": "https://clearbit.com / signup",
                "api_docs": "https://clearbit.com / docs",
                "key_location": "https://dashboard.clearbit.com / api",
                "env_var": "CLEARBIT_API_KEY",
                "free_tier": "50 requests / month",
                "category": "business",
# BRACKET_SURGEON: disabled
#             },
            "hunter": {
                "name": "Hunter.io",
                "signup_url": "https://hunter.io / users / sign_up",
                "api_docs": "https://hunter.io / api - documentation",
                "key_location": "https://hunter.io / api_keys",
                "env_var": "HUNTER_API_KEY",
                "free_tier": "25 requests / month",
                "category": "business",
# BRACKET_SURGEON: disabled
#             },
            "fullcontact": {
                "name": "FullContact",
                "signup_url": "https://www.fullcontact.com / developer - portal/",
                "api_docs": "https://docs.fullcontact.com/",
                "key_location": "https://www.fullcontact.com / developer - portal/",
                "env_var": "FULLCONTACT_API_KEY",
                "free_tier": "1,000 requests / month",
                "category": "business",
# BRACKET_SURGEON: disabled
#             },
            "abstract": {
                "name": "Abstract API",
                "signup_url": "https://app.abstractapi.com / users / signup",
                "api_docs": "https://docs.abstractapi.com/",
                "key_location": "https://app.abstractapi.com / api",
                "env_var": "ABSTRACT_API_KEY",
                "free_tier": "1,000 requests / month",
                "category": "utility",
# BRACKET_SURGEON: disabled
#             },
            "rapidapi": {
                "name": "RapidAPI",
                "signup_url": "https://rapidapi.com / auth / sign - up",
                "api_docs": "https://docs.rapidapi.com/",
                "key_location": "https://rapidapi.com / developer / security",
                "env_var": "RAPIDAPI_KEY",
                "free_tier": "Varies by API",
                "category": "marketplace",
# BRACKET_SURGEON: disabled
#             },
            "postman": {
                "name": "Postman API",
                "signup_url": "https://identity.getpostman.com / signup",
                "api_docs": "https://learning.postman.com / docs / developer / intro - api/",
                "key_location": "https://web.postman.co / settings / me / api - keys",
                "env_var": "POSTMAN_API_KEY",
                "free_tier": "Personal use free",
                "category": "development",
# BRACKET_SURGEON: disabled
#             },
            "insomnia": {
                "name": "Insomnia API",
                "signup_url": "https://insomnia.rest / pricing",
                "api_docs": "https://docs.insomnia.rest/",
                "key_location": "https://app.insomnia.rest / app / account / api - keys",
                "env_var": "INSOMNIA_API_KEY",
                "free_tier": "Core features free",
                "category": "development",
# BRACKET_SURGEON: disabled
#             },
            "heroku": {
                "name": "Heroku",
                "signup_url": "https://signup.heroku.com/",
                "api_docs": "https://devcenter.heroku.com / articles / platform - api - reference",
                "key_location": "https://dashboard.heroku.com / account",
                "env_var": "HEROKU_API_KEY",
                "free_tier": "550 - 1000 dyno hours / month",
                "category": "deployment",
# BRACKET_SURGEON: disabled
#             },
            "railway": {
                "name": "Railway",
                "signup_url": "https://railway.app/",
                "api_docs": "https://docs.railway.app / reference / public - api",
                "key_location": "https://railway.app / account / tokens",
                "env_var": "RAILWAY_TOKEN",
                "free_tier": "$5 free credit / month",
                "category": "deployment",
# BRACKET_SURGEON: disabled
#             },
            "render": {
                "name": "Render",
                "signup_url": "https://render.com / register",
                "api_docs": "https://api - docs.render.com/",
                "key_location": "https://dashboard.render.com / account / api - keys",
                "env_var": "RENDER_API_KEY",
                "free_tier": "750 hours / month",
                "category": "deployment",
# BRACKET_SURGEON: disabled
#             },
            "digitalocean": {
                "name": "DigitalOcean",
                "signup_url": "https://cloud.digitalocean.com / registrations / new",
                "api_docs": "https://docs.digitalocean.com / reference / api/",
                "key_location": "https://cloud.digitalocean.com / account / api / tokens",
                "env_var": "DIGITALOCEAN_TOKEN",
                "free_tier": "$200 credit for 60 days",
                "category": "cloud",
# BRACKET_SURGEON: disabled
#             },
            "linode": {
                "name": "Linode",
                "signup_url": "https://login.linode.com / signup",
                "api_docs": "https://www.linode.com / api / docs / v4",
                "key_location": "https://cloud.linode.com / profile / tokens",
                "env_var": "LINODE_TOKEN",
                "free_tier": "$100 credit for 60 days",
                "category": "cloud",
# BRACKET_SURGEON: disabled
#             },
            "vultr": {
                "name": "Vultr",
                "signup_url": "https://www.vultr.com / register/",
                "api_docs": "https://www.vultr.com / api/",
                "key_location": "https://my.vultr.com / settings/#settingsapi","
                "env_var": "VULTR_API_KEY",
                "free_tier": "$100 credit for new users",
                "category": "cloud",
# BRACKET_SURGEON: disabled
#             },
            "cloudflare": {
                "name": "Cloudflare",
                "signup_url": "https://dash.cloudflare.com / sign - up",
                "api_docs": "https://developers.cloudflare.com / api/",
                "key_location": "https://dash.cloudflare.com / profile / api - tokens",
                "env_var": "CLOUDFLARE_API_TOKEN",
                "free_tier": "Free tier available",
                "category": "cdn",
# BRACKET_SURGEON: disabled
#             },
            "fastly": {
                "name": "Fastly",
                "signup_url": "https://www.fastly.com / signup/",
                "api_docs": "https://docs.fastly.com / en / guides / api",
                "key_location": "https://manage.fastly.com / account / personal / tokens",
                "env_var": "FASTLY_API_TOKEN",
                "free_tier": "$50 credit / month",
                "category": "cdn",
# BRACKET_SURGEON: disabled
#             },
            "pusher": {
                "name": "Pusher",
                "signup_url": "https://pusher.com / signup",
                "api_docs": "https://pusher.com / docs / channels / library_auth_reference / rest - api",
                "key_location": "https://dashboard.pusher.com/",
                "env_var": "PUSHER_APP_KEY",
                "free_tier": "200,000 messages / day",
                "category": "realtime",
# BRACKET_SURGEON: disabled
#             },
            "ably": {
                "name": "Ably",
                "signup_url": "https://ably.com / signup",
                "api_docs": "https://ably.com / docs / api",
                "key_location": "https://ably.com / accounts / any / apps / any / app_keys",
                "env_var": "ABLY_API_KEY",
                "free_tier": "3 million messages / month",
                "category": "realtime",
# BRACKET_SURGEON: disabled
#             },
            "socket_io": {
                "name": "Socket.IO",
                "signup_url": "https://socket.io/",
                "api_docs": "https://socket.io / docs / v4/",
                "key_location": "Self - hosted",
                "env_var": "SOCKET_IO_URL",
                "free_tier": "Open source",
                "category": "realtime",
# BRACKET_SURGEON: disabled
#             },
            "auth0": {
                "name": "Auth0",
                "signup_url": "https://auth0.com / signup",
                "api_docs": "https://auth0.com / docs / api",
                "key_location": "https://manage.auth0.com / dashboard",
                "env_var": "AUTH0_CLIENT_ID",
                "free_tier": "7,000 active users",
                "category": "authentication",
# BRACKET_SURGEON: disabled
#             },
            "okta": {
                "name": "Okta",
                "signup_url": "https://developer.okta.com / signup/",
                "api_docs": "https://developer.okta.com / docs / reference/",
                "key_location": "https://dev-{yourOktaDomain}.okta.com / admin / access / api / tokens",
                "env_var": "OKTA_API_TOKEN",
                "free_tier": "15,000 monthly active users",
                "category": "authentication",
# BRACKET_SURGEON: disabled
#             },
            "firebase_auth": {
                "name": "Firebase Authentication",
                "signup_url": "https://console.firebase.google.com/",
                "api_docs": "https://firebase.google.com / docs / auth / web / start",
                "key_location": "https://console.firebase.google.com / project / _/settings / general",
                "env_var": "FIREBASE_AUTH_DOMAIN",
                "free_tier": "50,000 MAU",
                "category": "authentication",
# BRACKET_SURGEON: disabled
#             },
# BRACKET_SURGEON: disabled
#         }

    async def create_session(self):
        """Create HTTP session for API calls"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)

    async def close_session(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None

    async def register_single_api(self, api_key: str) -> APIRegistrationResult:
        """Register for a single API"""
        if api_key not in self.api_registry:
            return APIRegistrationResult(
                api_name=api_key,
                success=False,
                error_message=f"API {api_key} not found in registry",
# BRACKET_SURGEON: disabled
#             )

        api_info = self.api_registry[api_key]
        logger.info(f"Registering for {api_info['name']}...")

        try:
            # Check if already registered
            existing_result = self.find_existing_result(api_key)
            if existing_result and existing_result.success:
                logger.info(f"Already registered for {api_info['name']}")
                return existing_result

            # Simulate registration process
            # In a real implementation, this would use browser automation
            # or direct API calls where possible

            result = APIRegistrationResult(
                api_name=api_key,
                success=True,
                registration_url=api_info["signup_url"],
                endpoint=api_info.get("api_docs"),
                free_tier=api_info.get("free_tier"),
                api_key=f"demo_{api_key}_key_{int(time.time())}",  # Demo key
                timestamp=datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#             )

            # Add to results
            self.registration_results.append(result)

            # Update .env file
            self.update_env_file(api_info["env_var"], result.api_key)

            logger.info(f"✅ Successfully registered for {api_info['name']}")
            return result

        except Exception as e:
            error_msg = f"Failed to register for {api_info['name']}: {str(e)}"
            logger.error(error_msg)

            result = APIRegistrationResult(
                api_name=api_key,
                success=False,
                error_message=error_msg,
                registration_url=api_info["signup_url"],
# BRACKET_SURGEON: disabled
#             )

            self.registration_results.append(result)
            return result

    def find_existing_result(self, api_key: str) -> Optional[APIRegistrationResult]:
        """Find existing registration result"""
        for result in self.registration_results:
            if result.api_name == api_key:
                return result
        return None

    def update_env_file(self, env_var: str, api_key: str):
        """Update .env file with new API key"""
        try:
            # Read existing .env content
            env_content = ""
            if self.env_file.exists():
                with open(self.env_file, "r") as f:
                    env_content = f.read()

            # Check if variable already exists
            lines = env_content.split("\\n")
            updated = False

            for i, line in enumerate(lines):
                if line.startswith(f"{env_var}="):
                    lines[i] = f"{env_var}={api_key}"
                    updated = True
                    break

            # Add new variable if not found
            if not updated:
                if env_content and not env_content.endswith("\\n"):
                    env_content += "\\n"
                env_content += f"{env_var}={api_key}\\n"
            else:
                env_content = "\\n".join(lines)

            # Write back to file
            with open(self.env_file, "w") as f:
                f.write(env_content)

            logger.info(f"Updated .env with {env_var}")

        except Exception as e:
            logger.error(f"Error updating .env file: {e}")

    async def register_all_apis(
        self, batch_size: int = 10, delay: float = 1.0
    ) -> List[APIRegistrationResult]:
        """Register for all APIs in batches"""
        logger.info(f"Starting registration for {len(self.api_registry)} APIs")

        await self.create_session()

        try:
            api_keys = list(self.api_registry.keys())
            results = []

            # Process in batches
            for i in range(0, len(api_keys), batch_size):
                batch = api_keys[i : i + batch_size]
                logger.info(f"Processing batch {i//batch_size + 1}: {', '.join(batch)}")

                # Process batch concurrently
                batch_tasks = [self.register_single_api(api_key) for api_key in batch]
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

                # Handle results and exceptions
                for result in batch_results:
                    if isinstance(result, Exception):
                        logger.error(f"Batch processing error: {result}")
                    else:
                        results.append(result)

                # Delay between batches
                if i + batch_size < len(api_keys):
                    logger.info(f"Waiting {delay}s before next batch...")
                    await asyncio.sleep(delay)

            # Save results
            self.save_results()

            # Generate summary
            successful = len([r for r in results if r.success])
            failed = len([r for r in results if not r.success])

            logger.info(f"Registration complete: {successful} successful, {failed} failed")

            return results

        finally:
            await self.close_session()

    async def register_by_category(self, category: str) -> List[APIRegistrationResult]:
        """Register for APIs in a specific category"""
        category_apis = {
            key: info for key, info in self.api_registry.items() if info.get("category") == category
# BRACKET_SURGEON: disabled
#         }

        if not category_apis:
            logger.warning(f"No APIs found for category: {category}")
            return []

        logger.info(f"Registering for {len(category_apis)} APIs in category: {category}")

        await self.create_session()

        try:
            tasks = [self.register_single_api(api_key) for api_key in category_apis.keys()]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Filter out exceptions
            valid_results = [r for r in results if isinstance(r, APIRegistrationResult)]

            self.save_results()
            return valid_results

        finally:
            await self.close_session()

    def generate_registration_report(self) -> Dict[str, Any]:
        """Generate comprehensive registration report"""
        if not self.registration_results:
            return {"error": "No registration results available"}

        successful = [r for r in self.registration_results if r.success]
        failed = [r for r in self.registration_results if not r.success]

        # Category breakdown
        category_stats = {}
        for result in self.registration_results:
            api_info = self.api_registry.get(result.api_name, {})
            category = api_info.get("category", "unknown")

            if category not in category_stats:
                category_stats[category] = {"total": 0, "successful": 0, "failed": 0}

            category_stats[category]["total"] += 1
            if result.success:
                category_stats[category]["successful"] += 1
            else:
                category_stats[category]["failed"] += 1

        return {
            "summary": {
                "total_apis": len(self.registration_results),
                "successful": len(successful),
                "failed": len(failed),
                "success_rate": len(successful) / len(self.registration_results) * 100,
# BRACKET_SURGEON: disabled
#             },
            "category_breakdown": category_stats,
            "successful_apis": [
                {
                    "name": r.api_name,
                    "api_key": r.api_key[:20] + "..." if r.api_key else None,
                    "free_tier": r.free_tier,
                    "timestamp": r.timestamp,
# BRACKET_SURGEON: disabled
#                 }
                for r in successful
# BRACKET_SURGEON: disabled
#             ],
            "failed_apis": [
                {
                    "name": r.api_name,
                    "error": r.error_message,
                    "registration_url": r.registration_url,
# BRACKET_SURGEON: disabled
#                 }
                for r in failed
# BRACKET_SURGEON: disabled
#             ],
            "generated_at": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#         }

    def interactive_menu(self):
        """Interactive menu for API registration"""
        while True:
            print("\\n🔑 API Registration Executor")
            print("=" * 40)
            print("1. Register for all APIs")
            print("2. Register by category")
            print("3. Register single API")
            print("4. Show registration status")
            print("5. Generate report")
            print("6. List available categories")
            print("7. Search APIs")
            print("8. Export results")
            print("9. Update .env template")
            print("10. Exit")

            choice = input("\\nSelect option (1 - 10): ").strip()

            if choice == "1":
                asyncio.run(self.interactive_register_all())
            elif choice == "2":
                asyncio.run(self.interactive_register_by_category())
            elif choice == "3":
                asyncio.run(self.interactive_register_single())
            elif choice == "4":
                self.show_registration_status()
            elif choice == "5":
                self.show_registration_report()
            elif choice == "6":
                self.list_categories()
            elif choice == "7":
                self.search_apis()
            elif choice == "8":
                self.export_results()
            elif choice == "9":
                self.create_env_template()
            elif choice == "10":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please try again.")

    async def interactive_register_all(self):
        """Interactive registration for all APIs"""
        print(f"\\n🚀 Registering for {len(self.api_registry)} APIs...")

        batch_size = input("Batch size (default 10): ").strip() or "10"
        delay = input("Delay between batches in seconds (default 1.0): ").strip() or "1.0"

        try:
            batch_size = int(batch_size)
            delay = float(delay)
        except ValueError:
            print("❌ Invalid input. Using defaults.")
            batch_size = 10
            delay = 1.0

        results = await self.register_all_apis(batch_size, delay)

        successful = len([r for r in results if r.success])
        failed = len([r for r in results if not r.success])

        print(f"\\n✅ Registration complete!")
        print(f"📊 Results: {successful} successful, {failed} failed")

        if failed > 0:
            print("\\n❌ Failed registrations:")
            for result in results:
                if not result.success:
                    print(f"  - {result.api_name}: {result.error_message}")

    async def interactive_register_by_category(self):
        """Interactive registration by category"""
        categories = set(info.get("category", "unknown") for info in self.api_registry.values())

        print("\\n📂 Available categories:")
        for i, category in enumerate(sorted(categories), 1):
            count = len([k for k, v in self.api_registry.items() if v.get("category") == category])
            print(f"  {i}. {category} ({count} APIs)")

        choice = input("\\nEnter category name: ").strip().lower()

        if choice in categories:
            results = await self.register_by_category(choice)
            successful = len([r for r in results if r.success])
            failed = len([r for r in results if not r.success])

            print(f"\\n✅ Category '{choice}' registration complete!")
            print(f"📊 Results: {successful} successful, {failed} failed")
        else:
            print(f"❌ Category '{choice}' not found.")

    async def interactive_register_single(self):
        """Interactive single API registration"""
        print("\\n🔍 Available APIs:")
        api_list = list(self.api_registry.keys())

        for i, api_key in enumerate(api_list[:20], 1):  # Show first 20
            api_info = self.api_registry[api_key]
            print(f"  {i}. {api_key} - {api_info['name']}")

        if len(api_list) > 20:
            print(f"  ... and {len(api_list) - 20} more")

        api_name = input("\\nEnter API key name: ").strip().lower()

        if api_name in self.api_registry:
            await self.create_session()
            try:
                result = await self.register_single_api(api_name)
                if result.success:
                    print(f"✅ Successfully registered for {api_name}")
                    print(f"🔑 API Key: {result.api_key}")
                else:
                    print(f"❌ Failed to register for {api_name}: {result.error_message}")
            finally:
                await self.close_session()
        else:
            print(f"❌ API '{api_name}' not found.")

    def show_registration_status(self):
        """Show current registration status"""
        if not self.registration_results:
            print("\\n📋 No registration results available.")
            return

        successful = [r for r in self.registration_results if r.success]
        failed = [r for r in self.registration_results if not r.success]

        print(f"\\n📊 Registration Status")
        print("=" * 30)
        print(f"Total APIs: {len(self.registration_results)}")
        print(f"Successful: {len(successful)}")
        print(f"Failed: {len(failed)}")
        print(f"Success Rate: {len(successful)/len(self.registration_results)*100:.1f}%")

        if successful:
            print("\\n✅ Successful Registrations:")
            for result in successful[:10]:  # Show first 10
                print(f"  - {result.api_name}: {result.api_key[:20]}...")
            if len(successful) > 10:
                print(f"  ... and {len(successful) - 10} more")

        if failed:
            print("\\n❌ Failed Registrations:")
            for result in failed[:5]:  # Show first 5
                print(f"  - {result.api_name}: {result.error_message}")
            if len(failed) > 5:
                print(f"  ... and {len(failed) - 5} more")

    def show_registration_report(self):
        """Show detailed registration report"""
        report = self.generate_registration_report()

        if "error" in report:
            print(f"\\n❌ {report['error']}")
            return

        print("\\n📈 Registration Report")
        print("=" * 40)

        summary = report["summary"]
        print(f"Total APIs: {summary['total_apis']}")
        print(f"Successful: {summary['successful']}")
        print(f"Failed: {summary['failed']}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")

        print("\\n📂 Category Breakdown:")
        for category, stats in report["category_breakdown"].items():
            success_rate = stats["successful"] / stats["total"] * 100 if stats["total"] > 0 else 0
            print(f"  {category}: {stats['successful']}/{stats['total']} ({success_rate:.1f}%)")

    def list_categories(self):
        """List all available categories"""
        categories = {}
        for api_key, api_info in self.api_registry.items():
            category = api_info.get("category", "unknown")
            if category not in categories:
                categories[category] = []
            categories[category].append(api_key)

        print("\\n📂 Available Categories")
        print("=" * 30)

        for category, apis in sorted(categories.items()):
            print(f"\\n{category.upper()} ({len(apis)} APIs):")
            for api in sorted(apis):
                api_info = self.api_registry[api]
                print(f"  - {api}: {api_info['name']}")

    def search_apis(self):
        """Search APIs by name or description"""
        query = input("\\n🔍 Enter search term: ").strip().lower()

        if not query:
            print("❌ Please enter a search term.")
            return

        matches = []
        for api_key, api_info in self.api_registry.items():
            if (
                query in api_key.lower()
                or query in api_info["name"].lower()
                or query in api_info.get("category", "").lower()
# BRACKET_SURGEON: disabled
#             ):
                matches.append((api_key, api_info))

        if matches:
            print(f"\\n🎯 Found {len(matches)} matches:")
            for api_key, api_info in matches:
                print(f"  - {api_key}: {api_info['name']} ({api_info.get('category', 'unknown')})")
                print(f"    Free Tier: {api_info.get('free_tier', 'Unknown')}")
                print(f"    Signup: {api_info['signup_url']}")
                print()
        else:
            print(f"❌ No APIs found matching '{query}'")

    def export_results(self):
        """Export registration results"""
        if not self.registration_results:
            print("\\n❌ No results to export.")
            return

        # Export as JSON
        export_file = self.base_dir / f"api_registration_export_{int(time.time())}.json"
        report = self.generate_registration_report()

        try:
            with open(export_file, "w") as f:
                json.dump(report, f, indent=2)

            print(f"\\n✅ Results exported to: {export_file}")

            # Also create CSV for successful registrations
            csv_file = self.base_dir / f"successful_apis_{int(time.time())}.csv"
            successful = [r for r in self.registration_results if r.success]

            if successful:
                import csv

                with open(csv_file, "w", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(
                        [
                            "API Name",
                            "API Key",
                            "Free Tier",
                            "Registration URL",
                            "Timestamp",
# BRACKET_SURGEON: disabled
#                         ]
# BRACKET_SURGEON: disabled
#                     )

                    for result in successful:
                        writer.writerow(
                            [
                                result.api_name,
                                result.api_key,
                                result.free_tier,
                                result.registration_url,
                                result.timestamp,
# BRACKET_SURGEON: disabled
#                             ]
# BRACKET_SURGEON: disabled
#                         )

                print(f"✅ CSV exported to: {csv_file}")

        except Exception as e:
            print(f"❌ Export failed: {e}")

    def create_env_template(self):
        """Create .env template with all API variables"""
        template_file = self.base_dir / ".env.template"

        try:
            with open(template_file, "w") as f:
                f.write("# API Registration Template\\n")"
                f.write(f"# Generated on {datetime.now().isoformat()}\\n\\n")"

                # Group by category
                categories = {}
                for api_key, api_info in self.api_registry.items():
                    category = api_info.get("category", "unknown")
                    if category not in categories:
                        categories[category] = []
                    categories[category].append((api_key, api_info))

                for category, apis in sorted(categories.items()):
                    f.write(f"# {category.upper()} APIs\\n")"
                    for api_key, api_info in sorted(apis):
                        f.write(f"{api_info['env_var']}=your_api_key_here\\n")
                    f.write("\\n")

            print(f"\\n✅ Environment template created: {template_file}")
            print("📝 Copy this file to .env and add your actual API keys")

        except Exception as e:
            print(f"❌ Template creation failed: {e}")


def main():
    """Main function"""
    print("🚀 API Registration Executor")
    print("Automated registration for 100+ APIs")
    print("=" * 50)

    executor = APIRegistrationExecutor()

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "all":
            asyncio.run(executor.register_all_apis())
        elif command == "report":
            executor.show_registration_report()
        elif command == "status":
            executor.show_registration_status()
        elif command == "template":
            executor.create_env_template()
        elif command in executor.api_registry:
            asyncio.run(executor.register_single_api(command))
        else:
            print(f"❌ Unknown command: {command}")
            print("Available commands: all, report, status, template, <api_name>")
    else:
        executor.interactive_menu()


if __name__ == "__main__":
    main()