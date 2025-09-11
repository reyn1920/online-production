#!/usr/bin/env python3
"""
API Discovery Service
Automatically discovers and evaluates APIs for different marketing channels
"""

import asyncio
import json
import logging
import re
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

try:
    import httpx
    from bs4 import BeautifulSoup
except ImportError:
    print("Missing dependencies. Install with: pip install httpx beautifulsoup4")
    exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class APICandidate:
    """Represents a discovered API candidate"""

    name: str
    url: str
    signup_url: str
    category: str
    cost_model: str  # 'free', 'freemium', 'paid', 'unknown'
    description: str
    features: List[str]
    rate_limits: str
    documentation_url: str
    score: float  # 0-10 rating based on various factors
    discovered_at: str
    channel: str  # marketing channel this API serves


class APIDiscoveryService:
    """Service for discovering and evaluating APIs for marketing channels"""

    def __init__(self, db_path: str = "intelligence.db"):
        self.db_path = db_path
        self.session = None
        self.search_patterns = {
            "youtube": [
                "youtube api creator monetization",
                "youtube data api v3 affiliate",
                "youtube creator economy api",
                "youtube channel analytics api",
            ],
            "tiktok": [
                "tiktok creator api affiliate marketing",
                "tiktok business api monetization",
                "tiktok marketing api free",
                "tiktok creator fund api",
            ],
            "instagram": [
                "instagram basic display api",
                "instagram graph api creator",
                "instagram affiliate marketing api",
                "meta creator api instagram",
            ],
            "twitter": [
                "twitter api v2 creator monetization",
                "twitter spaces api affiliate",
                "x api creator economy",
                "twitter developer api free",
            ],
            "affiliate": [
                "affiliate marketing api free",
                "commission tracking api",
                "affiliate network api integration",
                "performance marketing api",
            ],
            "email": [
                "email marketing api free tier",
                "transactional email api",
                "newsletter api integration",
                "email automation api",
            ],
            "analytics": [
                "marketing analytics api free",
                "social media analytics api",
                "creator analytics api",
                "engagement tracking api",
            ],
            "content": [
                "content creation api free",
                "ai content generation api",
                "stock photo api free",
                "video editing api",
            ],
        }
        self.init_database()

    def init_database(self):
        """Initialize database tables for API discovery"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS discovered_apis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    url TEXT,
                    signup_url TEXT,
                    category TEXT,
                    cost_model TEXT,
                    description TEXT,
                    features TEXT,  -- JSON array
                    rate_limits TEXT,
                    documentation_url TEXT,
                    score REAL,
                    discovered_at TEXT,
                    channel TEXT,
                    is_active BOOLEAN DEFAULT 0,
                    last_verified TEXT
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS api_search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT,
                    channel TEXT,
                    results_count INTEGER,
                    search_date TEXT
                )
            """
            )
            conn.commit()

    async def __aenter__(self):
        self.session = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            },
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.aclose()

    async def discover_apis_for_channel(self, channel: str) -> List[APICandidate]:
        """Discover APIs for a specific marketing channel"""
        if channel not in self.search_patterns:
            logger.warning(f"No search patterns defined for channel: {channel}")
            return []

        all_candidates = []

        for query in self.search_patterns[channel]:
            logger.info(f"Searching for: {query}")
            candidates = await self.search_and_analyze(query, channel)
            all_candidates.extend(candidates)

            # Record search in history
            self.record_search(query, channel, len(candidates))

            # Be respectful with rate limiting
            await asyncio.sleep(2)

        # Deduplicate and sort by score
        unique_candidates = self.deduplicate_candidates(all_candidates)
        return sorted(unique_candidates, key=lambda x: x.score, reverse=True)

    async def search_and_analyze(self, query: str, channel: str) -> List[APICandidate]:
        """Search for APIs and analyze the results"""
        candidates = []

        # Search multiple sources
        search_results = await self.multi_source_search(query)

        for result in search_results:
            try:
                candidate = await self.analyze_api_candidate(result, channel)
                if candidate and candidate.score > 3.0:  # Only keep decent candidates
                    candidates.append(candidate)
            except Exception as e:
                logger.error(
                    f"Error analyzing candidate {result.get('url', 'unknown')}: {e}"
                )

        return candidates

    async def multi_source_search(self, query: str) -> List[Dict]:
        """Search multiple sources for API information"""
        results = []

        # Known API directories and documentation sites
        search_sources = [
            f"site:rapidapi.com {query}",
            f"site:github.com {query} API",
            f"site:developers.google.com {query}",
            f"site:developer.twitter.com {query}",
            f"site:developers.facebook.com {query}",
            f"site:docs.microsoft.com {query}",
            f"site:aws.amazon.com {query}",
            f"{query} API documentation free",
            f"{query} REST API integration",
        ]

        # Simulate search results (in production, integrate with search APIs)
        # For now, return curated results based on known good APIs
        mock_results = await self.get_curated_api_results(query)
        results.extend(mock_results)

        return results

    async def get_curated_api_results(self, query: str) -> List[Dict]:
        """Return curated API results based on query patterns"""
        results = []

        # YouTube APIs
        if "youtube" in query.lower():
            results.extend(
                [
                    {
                        "title": "YouTube Data API v3",
                        "url": "https://developers.google.com/youtube/v3",
                        "description": "Access YouTube data including videos, channels, playlists",
                        "signup_url": "https://console.cloud.google.com/",
                        "cost": "free",
                        "features": [
                            "video analytics",
                            "channel data",
                            "playlist management",
                        ],
                    },
                    {
                        "title": "YouTube Analytics API",
                        "url": "https://developers.google.com/youtube/analytics",
                        "description": "Retrieve YouTube Analytics reports",
                        "signup_url": "https://console.cloud.google.com/",
                        "cost": "free",
                        "features": [
                            "revenue data",
                            "view analytics",
                            "audience insights",
                        ],
                    },
                ]
            )

        # TikTok APIs
        if "tiktok" in query.lower():
            results.extend(
                [
                    {
                        "title": "TikTok for Developers",
                        "url": "https://developers.tiktok.com/",
                        "description": "TikTok API for creators and businesses",
                        "signup_url": "https://developers.tiktok.com/",
                        "cost": "free",
                        "features": ["video upload", "user data", "analytics"],
                    }
                ]
            )

        # Email Marketing APIs
        if "email" in query.lower():
            results.extend(
                [
                    {
                        "title": "SendGrid API",
                        "url": "https://sendgrid.com/docs/api-reference/",
                        "description": "Email delivery service API",
                        "signup_url": "https://signup.sendgrid.com/",
                        "cost": "freemium",
                        "features": [
                            "transactional email",
                            "marketing campaigns",
                            "analytics",
                        ],
                    },
                    {
                        "title": "Mailchimp API",
                        "url": "https://mailchimp.com/developer/",
                        "description": "Email marketing and automation API",
                        "signup_url": "https://mailchimp.com/signup/",
                        "cost": "freemium",
                        "features": ["list management", "campaigns", "automation"],
                    },
                ]
            )

        # Affiliate Marketing APIs
        if "affiliate" in query.lower():
            results.extend(
                [
                    {
                        "title": "Amazon Associates API",
                        "url": "https://webservices.amazon.com/paapi5/documentation/",
                        "description": "Amazon Product Advertising API",
                        "signup_url": "https://affiliate-program.amazon.com/",
                        "cost": "free",
                        "features": ["product data", "pricing", "affiliate links"],
                    },
                    {
                        "title": "ShareASale API",
                        "url": "https://www.shareasale.com/info/api/",
                        "description": "Affiliate network API",
                        "signup_url": "https://www.shareasale.com/shareasale.cfm?call=signup",
                        "cost": "free",
                        "features": [
                            "merchant data",
                            "commission tracking",
                            "reporting",
                        ],
                    },
                ]
            )

        return results

    async def analyze_api_candidate(
        self, result: Dict, channel: str
    ) -> Optional[APICandidate]:
        """Analyze a search result to create an API candidate"""
        try:
            # Extract basic information
            name = result.get("title", "Unknown API")
            url = result.get("url", "")
            description = result.get("description", "")
            signup_url = result.get("signup_url", url)

            # Determine cost model
            cost_indicators = result.get("cost", "").lower()
            if "free" in cost_indicators:
                cost_model = "free"
            elif "freemium" in cost_indicators or "free tier" in description.lower():
                cost_model = "freemium"
            elif "paid" in cost_indicators or "subscription" in description.lower():
                cost_model = "paid"
            else:
                cost_model = "unknown"

            # Extract features
            features = result.get("features", [])
            if isinstance(features, str):
                features = [features]

            # Calculate score based on various factors
            score = self.calculate_api_score(
                cost_model, features, description, url, channel
            )

            return APICandidate(
                name=name,
                url=url,
                signup_url=signup_url,
                category=self.determine_category(name, description),
                cost_model=cost_model,
                description=description,
                features=features,
                rate_limits=self.extract_rate_limits(description),
                documentation_url=url,
                score=score,
                discovered_at=datetime.now().isoformat(),
                channel=channel,
            )

        except Exception as e:
            logger.error(f"Error creating API candidate: {e}")
            return None

    def calculate_api_score(
        self,
        cost_model: str,
        features: List[str],
        description: str,
        url: str,
        channel: str,
    ) -> float:
        """Calculate a score for an API candidate (0-10)"""
        score = 5.0  # Base score

        # Cost model scoring
        cost_scores = {"free": 3.0, "freemium": 2.0, "paid": 0.0, "unknown": 1.0}
        score += cost_scores.get(cost_model, 0.0)

        # Feature richness
        score += min(len(features) * 0.2, 1.5)

        # Documentation quality indicators
        if "documentation" in description.lower() or "docs" in url:
            score += 0.5

        # Trusted domains
        domain = urlparse(url).netloc.lower()
        trusted_domains = [
            "developers.google.com",
            "developer.twitter.com",
            "developers.facebook.com",
            "github.com",
            "rapidapi.com",
            "sendgrid.com",
            "mailchimp.com",
        ]
        if any(trusted in domain for trusted in trusted_domains):
            score += 1.0

        # Channel relevance
        channel_keywords = {
            "youtube": ["youtube", "video", "creator"],
            "email": ["email", "mail", "newsletter"],
            "affiliate": ["affiliate", "commission", "marketing"],
        }

        if channel in channel_keywords:
            keywords = channel_keywords[channel]
            text = (description + url).lower()
            matches = sum(1 for keyword in keywords if keyword in text)
            score += matches * 0.3

        return min(score, 10.0)

    def determine_category(self, name: str, description: str) -> str:
        """Determine the category of an API"""
        text = (name + " " + description).lower()

        categories = {
            "social": [
                "social",
                "twitter",
                "facebook",
                "instagram",
                "tiktok",
                "youtube",
            ],
            "email": ["email", "mail", "newsletter", "sendgrid", "mailchimp"],
            "affiliate": ["affiliate", "commission", "amazon", "shareasale"],
            "analytics": ["analytics", "tracking", "metrics", "insights"],
            "content": ["content", "media", "image", "video", "photo"],
            "payment": ["payment", "stripe", "paypal", "billing"],
        }

        for category, keywords in categories.items():
            if any(keyword in text for keyword in keywords):
                return category

        return "other"

    def extract_rate_limits(self, description: str) -> str:
        """Extract rate limit information from description"""
        # Look for common rate limit patterns
        patterns = [
            r"(\d+)\s*requests?\s*per\s*(minute|hour|day)",
            r"(\d+)\s*calls?\s*per\s*(minute|hour|day)",
            r"quota\s*of\s*(\d+)",
            r"limit\s*of\s*(\d+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, description.lower())
            if match:
                return match.group(0)

        return "Not specified"

    def deduplicate_candidates(
        self, candidates: List[APICandidate]
    ) -> List[APICandidate]:
        """Remove duplicate API candidates"""
        seen_urls = set()
        unique_candidates = []

        for candidate in candidates:
            if candidate.url not in seen_urls:
                seen_urls.add(candidate.url)
                unique_candidates.append(candidate)

        return unique_candidates

    def save_candidates(self, candidates: List[APICandidate]):
        """Save discovered API candidates to database"""
        with sqlite3.connect(self.db_path) as conn:
            for candidate in candidates:
                try:
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO discovered_apis 
                        (name, url, signup_url, category, cost_model, description, 
                         features, rate_limits, documentation_url, score, 
                         discovered_at, channel)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            candidate.name,
                            candidate.url,
                            candidate.signup_url,
                            candidate.category,
                            candidate.cost_model,
                            candidate.description,
                            json.dumps(candidate.features),
                            candidate.rate_limits,
                            candidate.documentation_url,
                            candidate.score,
                            candidate.discovered_at,
                            candidate.channel,
                        ),
                    )
                except sqlite3.Error as e:
                    logger.error(f"Error saving candidate {candidate.name}: {e}")

            conn.commit()

    def record_search(self, query: str, channel: str, results_count: int):
        """Record search history"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO api_search_history (query, channel, results_count, search_date)
                VALUES (?, ?, ?, ?)
            """,
                (query, channel, results_count, datetime.now().isoformat()),
            )
            conn.commit()

    def get_top_apis_by_channel(self, channel: str, limit: int = 10) -> List[Dict]:
        """Get top-rated APIs for a specific channel"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT * FROM discovered_apis 
                WHERE channel = ? 
                ORDER BY score DESC, cost_model = 'free' DESC
                LIMIT ?
            """,
                (channel, limit),
            )

            return [dict(row) for row in cursor.fetchall()]

    def get_free_apis(self) -> List[Dict]:
        """Get all free APIs"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT * FROM discovered_apis 
                WHERE cost_model IN ('free', 'freemium')
                ORDER BY score DESC
            """
            )

            return [dict(row) for row in cursor.fetchall()]

    async def discover_all_channels(self) -> Dict[str, List[APICandidate]]:
        """Discover APIs for all defined channels"""
        results = {}

        for channel in self.search_patterns.keys():
            logger.info(f"Discovering APIs for channel: {channel}")
            candidates = await self.discover_apis_for_channel(channel)
            results[channel] = candidates

            # Save to database
            self.save_candidates(candidates)

            logger.info(f"Found {len(candidates)} candidates for {channel}")

        return results


# CLI interface
async def main():
    """Main CLI interface for API discovery"""
    import argparse

    parser = argparse.ArgumentParser(description="Discover APIs for marketing channels")
    parser.add_argument("--channel", help="Specific channel to search")
    parser.add_argument("--all", action="store_true", help="Search all channels")
    parser.add_argument("--list-free", action="store_true", help="List all free APIs")
    parser.add_argument(
        "--top", type=int, default=5, help="Number of top results to show"
    )

    args = parser.parse_args()

    async with APIDiscoveryService() as service:
        if args.list_free:
            free_apis = service.get_free_apis()
            print(f"\n🟢 Found {len(free_apis)} free/freemium APIs:")
            for api in free_apis[: args.top]:
                print(
                    f"  • {api['name']} ({api['cost_model']}) - Score: {api['score']:.1f}"
                )
                print(f"    {api['description'][:100]}...")
                print(f"    Signup: {api['signup_url']}\n")

        elif args.channel:
            candidates = await service.discover_apis_for_channel(args.channel)
            print(f"\n🔍 Found {len(candidates)} APIs for {args.channel}:")
            for candidate in candidates[: args.top]:
                print(
                    f"  • {candidate.name} ({candidate.cost_model}) - Score: {candidate.score:.1f}"
                )
                print(f"    {candidate.description}")
                print(f"    Signup: {candidate.signup_url}\n")

        elif args.all:
            results = await service.discover_all_channels()
            for channel, candidates in results.items():
                print(f"\n📱 {channel.upper()} ({len(candidates)} APIs found):")
                for candidate in candidates[:3]:  # Top 3 per channel
                    print(
                        f"  • {candidate.name} ({candidate.cost_model}) - Score: {candidate.score:.1f}"
                    )

        else:
            print("Use --help for usage information")


if __name__ == "__main__":
    asyncio.run(main())
