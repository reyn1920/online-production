#!/usr / bin / env python3
"""
Web Search Service

Integrates web search capabilities to automatically discover \
    and evaluate APIs for marketing channels.
Uses multiple search strategies to find the best free and paid API options.
"""

import json
import logging
import re
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

import requests

@dataclass


class SearchResult:
    """Represents a web search result."""

    title: str
    url: str
    snippet: str
    relevance_score: float
    api_indicators: List[str]
    pricing_info: Optional[str] = None
    documentation_url: Optional[str] = None

@dataclass


class APICandidate:
    """Represents a discovered API candidate."""

    name: str
    provider: str
    category: str
    pricing_model: str  # 'free', 'freemium', 'paid'
    api_url: str
    documentation_url: str
    signup_url: str
    features: List[str]
    rate_limits: Optional[str]
    cost_estimate: Optional[str]
    quality_score: float
    discovered_at: datetime


class WebSearchService:
    """Service for discovering APIs through web search."""


    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Search patterns for API discovery
        self.api_search_patterns = {
            "youtube": [
                "YouTube API free alternatives",
                    "YouTube data API competitors",
                    "video platform APIs free tier",
                    "YouTube analytics API alternatives",
                    ],
            "tiktok": [
                "TikTok API alternatives free",
                    "short video platform APIs",
                    "TikTok marketing API competitors",
                    "social media video APIs",
                    ],
            "instagram": [
                "Instagram API alternatives",
                    "Instagram marketing API free",
                    "social media photo APIs",
                    "Instagram analytics alternatives",
                    ],
            "email": [
                "email marketing API free tier",
                    "transactional email API alternatives",
                    "bulk email service APIs",
                    "newsletter API providers",
                    ],
            "sms": [
                "SMS API free tier providers",
                    "text messaging API alternatives",
                    "bulk SMS service APIs",
                    "notification SMS APIs",
                    ],
            "ai_content": [
                "AI content generation API free",
                    "text generation API alternatives",
                    "GPT API competitors free tier",
                    "content writing API services",
                    ],
        }

        # API quality indicators
        self.quality_indicators = {
            "positive": [
                "free tier",
                    "free plan",
                    "no cost",
                    "open source",
                    "generous limits",
                    "good documentation",
                    "active community",
                    "reliable uptime",
                    "fast response",
                    "easy integration",
                    ],
            "negative": [
                "expensive",
                    "limited free",
                    "poor documentation",
                    "unreliable",
                    "slow response",
                    "complex setup",
                    "deprecated",
                    "shutting down",
                    ],
        }


    def search_apis_for_channel(:
        self, channel: str, max_results: int = 10
    ) -> List[APICandidate]:
        """Search for APIs suitable for a specific marketing channel."""
        try:
            search_queries = self.api_search_patterns.get(
                channel, [f"{channel} API free alternatives"]
            )
            all_candidates = []

            for query in search_queries:
                self.logger.info(f"Searching for: {query}")

                # Simulate web search (in production, integrate with actual search API)
                search_results = self._perform_web_search(query, max_results = 5)

                # Extract API candidates from search results
                candidates = self._extract_api_candidates(search_results, channel)
                all_candidates.extend(candidates)

                # Rate limiting
                time.sleep(1)

            # Deduplicate and rank candidates
            unique_candidates = self._deduplicate_candidates(all_candidates)
            ranked_candidates = self._rank_candidates(unique_candidates)

        except Exception as e:
            pass
        return ranked_candidates[:max_results]

        except Exception as e:
            self.logger.error(f"Error searching APIs for channel {channel}: {e}")
        return []


    def _perform_web_search(:
        self, query: str, max_results: int = 5
    ) -> List[SearchResult]:
        """Perform web search for API discovery."""
        # Mock search results for demonstration
        # In production, integrate with Google Custom Search API, Bing API, or SerpAPI

        mock_results = {
            "YouTube API free alternatives": [
                {
            "title": "YouTube Data API v3 - Free Tier",
            "url": "https://developers.google.com / youtube / v3",
            "snippet": "YouTube Data API v3 provides free access to YouTube data with 10,000 units per day quota.",
            "api_indicators": ["free tier", "quota limits", "official API"],
        },
                    {
            "title": "Invidious API - Open Source YouTube Alternative",
            "url": "https://docs.invidious.io / api/",
            "snippet": "Open source alternative to YouTube API with no rate limits \
    or API keys required.",
            "api_indicators": ["open source", "no limits", "free"],
        },
                    ],
            "email marketing API free tier": [
                {
            "title": "Mailgun Free Tier - 5000 emails / month",
            "url": "https://www.mailgun.com / pricing/",
            "snippet": "Mailgun offers 5,000 free emails per month with full API access \
    and analytics.",
            "api_indicators": ["free tier", "5000 emails", "full API"],
        },
                    {
            "title": "SendGrid Free Plan - 100 emails / day",
            "url": "https://sendgrid.com / pricing/",
            "snippet": "SendGrid provides 100 free emails per day with comprehensive API \
    and SMTP access.",
            "api_indicators": ["free plan", "100 daily", "SMTP"],
        },
                    ],
        }

        results = []
        mock_data = mock_results.get(query, [])

        for item in mock_data[:max_results]:
            result = SearchResult(
                title = item["title"],
                    url = item["url"],
                    snippet = item["snippet"],
                    relevance_score = 0.8,
                    api_indicators = item["api_indicators"],
                    )
            results.append(result)

        return results


    def _extract_api_candidates(:
        self, search_results: List[SearchResult], channel: str
    ) -> List[APICandidate]:
        """Extract API candidates from search results."""
        candidates = []

        for result in search_results:
            try:
                # Extract API information from search result
                name = self._extract_api_name(result.title)
                provider = self._extract_provider(result.url)
                pricing_model = self._determine_pricing_model(
                    result.snippet, result.api_indicators
                )
                features = self._extract_features(result.snippet)
                rate_limits = self._extract_rate_limits(result.snippet)

                candidate = APICandidate(
                    name = name,
                        provider = provider,
                        category = channel,
                        pricing_model = pricing_model,
                        api_url = result.url,
                        documentation_url = result.url,
                        signup_url = self._generate_signup_url(result.url),
                        features = features,
                        rate_limits = rate_limits,
                        cost_estimate = self._estimate_cost(result.snippet),
                        quality_score = self._calculate_quality_score(result),
                        discovered_at = datetime.now(),
                        )

                candidates.append(candidate)

            except Exception as e:
                self.logger.error(f"Error extracting API candidate from result: {e}")

        return candidates


    def _extract_api_name(self, title: str) -> str:
        """Extract API name from search result title."""
        # Remove common suffixes and clean up
        name = re.sub(
            r"\\s*-\\s*(API|Free|Tier|Plan|Pricing).*$", "",
    title,
    flags = re.IGNORECASE
        )
        name = re.sub(r"\\s*(API|Service)\\s*$", "", name, flags = re.IGNORECASE)
        return name.strip()


    def _extract_provider(self, url: str) -> str:
        """Extract provider name from URL."""
        domain = urlparse(url).netloc
        # Remove www and common TLDs
        provider = re.sub(r"^www\\.", "", domain)
        provider = re.sub(r"\\.(com|org|net|io)$", "", provider)
        return provider.title()


    def _determine_pricing_model(self, snippet: str, indicators: List[str]) -> str:
        """Determine pricing model from snippet and indicators."""
        text = (snippet + " " + " ".join(indicators)).lower()

        if any(term in text for term in ["free", "no cost", "open source"]):
            if any(term in text for term in ["tier", "plan", "limit"]):
        return "freemium"
        return "free"
        elif any(term in text for term in ["paid", "premium", "subscription"]):
        return "paid"
        else:
        return "freemium"  # Default assumption


    def _extract_features(self, snippet: str) -> List[str]:
        """Extract API features from snippet."""
        features = []

        # Common API features to look for
            feature_patterns = {
            "analytics": r"analytic|metric|stat|report",
            "real - time": r"real.?time|live|instant",
            "webhook": r"webhook|callback|notification",
            "rate_limiting": r"rate.?limit|quota|throttl",
            "authentication": r"auth|token|key|oauth",
            "documentation": r"doc|guide|tutorial",
            "sdk": r"sdk|library|wrapper",
            "rest_api": r"rest|http|json",
            "graphql": r"graphql|graph.?ql",
        }

        for feature, pattern in feature_patterns.items():
            if re.search(pattern, snippet, re.IGNORECASE):
                features.append(feature)

        return features


    def _extract_rate_limits(self, snippet: str) -> Optional[str]:
        """Extract rate limit information from snippet."""
        # Look for common rate limit patterns
        patterns = [
            r"(\\d+[,\\d]*?)\\s*(requests?|calls?|emails?)\\s * per\\s*(day|month|hour|minute)",
                r"(\\d+[,\\d]*?)\\s*(units?)\\s * per\\s*(day|month)",
                r"quota\\s * of\\s*(\\d+[,\\d]*?)",
                ]

        for pattern in patterns:
            match = re.search(pattern, snippet, re.IGNORECASE)
            if match:
        return match.group(0)

        return None


    def _generate_signup_url(self, api_url: str) -> str:
        """Generate likely signup URL from API URL."""
        base_url = f"{urlparse(api_url).scheme}://{urlparse(api_url).netloc}"

        # Common signup paths
        signup_paths = ["/signup", "/register", "/get - started", "/pricing", "/plans"]

        # Return the first likely signup URL (in production, verify these exist)
        return urljoin(base_url, "/signup")


    def _estimate_cost(self, snippet: str) -> Optional[str]:
        """Estimate cost from snippet text."""
        # Look for pricing information
        price_patterns = [
            r"\\$([0 - 9,]+(?:\\.[0 - 9]{2})?)\\s*(?:per|/)?\\s*(month|year|request)",
                r"([0 - 9,]+)\\s * free\\s*(emails?|requests?|calls?)",
                ]

        for pattern in price_patterns:
            match = re.search(pattern, snippet, re.IGNORECASE)
            if match:
        return match.group(0)

        return None


    def _calculate_quality_score(self, result: SearchResult) -> float:
        """Calculate quality score for an API candidate."""
        score = result.relevance_score

        # Boost score for positive indicators
        for indicator in result.api_indicators:
            if any(
                pos in indicator.lower() for pos in self.quality_indicators["positive"]
            ):
                score += 0.1
            if any(
                neg in indicator.lower() for neg in self.quality_indicators["negative"]
            ):
                score -= 0.2

        # Boost for official APIs
        if "official" in result.title.lower() or "developers." in result.url:
            score += 0.2

        # Boost for well - known providers
        well_known = [
            "google",
                "microsoft",
                "amazon",
                "github",
                "mailgun",
                "sendgrid",
                "twilio",
                ]
        if any(provider in result.url.lower() for provider in well_known):
            score += 0.15

        return min(1.0, max(0.0, score))


    def _deduplicate_candidates(:
        self, candidates: List[APICandidate]
    ) -> List[APICandidate]:
        """Remove duplicate API candidates."""
        seen = set()
        unique_candidates = []

        for candidate in candidates:
            # Create a unique key based on provider and name
            key = f"{candidate.provider.lower()}_{candidate.name.lower()}"

            if key not in seen:
                seen.add(key)
                unique_candidates.append(candidate)

        return unique_candidates


    def _rank_candidates(self, candidates: List[APICandidate]) -> List[APICandidate]:
        """Rank API candidates by quality and suitability."""


        def ranking_key(candidate):
            # Prioritize free > freemium > paid
            pricing_score = {"free": 3, "freemium": 2, "paid": 1}[
                candidate.pricing_model
            ]

            # Combine quality score with pricing preference
        return (pricing_score, candidate.quality_score)

        return sorted(candidates, key = ranking_key, reverse = True)


    def discover_trending_apis(self, category: str = "marketing") -> List[APICandidate]:
        """Discover trending APIs in a category."""
        trending_queries = [
            f"best {category} APIs 2024",
                f"new {category} API services",
                f"trending {category} tools API",
                f"popular {category} integrations",
                ]

        all_candidates = []

        for query in trending_queries:
            results = self._perform_web_search(query, max_results = 3)
            candidates = self._extract_api_candidates(results, category)
            all_candidates.extend(candidates)

        return self._rank_candidates(self._deduplicate_candidates(all_candidates))


    def evaluate_api_quality(self, api_url: str) -> Dict[str, Any]:
        """Evaluate the quality of a specific API."""
        try:
            # In production, this would:
            # 1. Check API documentation quality
            # 2. Test API endpoints
            # 3. Check uptime / reliability
            # 4. Analyze community feedback

            # Mock evaluation
            evaluation = {
            "documentation_quality": 0.8,
            "api_reliability": 0.9,
            "community_support": 0.7,
            "ease_of_integration": 0.8,
            "pricing_transparency": 0.9,
            "overall_score": 0.82,
            "recommendations": [
                    "Good documentation with examples",
                        "Reliable uptime and fast responses",
                        "Clear pricing structure",
                        ],
            "concerns": [
                    "Limited community tutorials",
                        "Rate limits could be higher",
                        ],
        except Exception as e:
            pass
        }

        return evaluation

        except Exception as e:
            self.logger.error(f"Error evaluating API quality for {api_url}: {e}")
        return {"overall_score": 0.5, "error": str(e)}

# CLI interface for web search service
if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(description="Web Search Service CLI")
    parser.add_argument(
        "--action", choices=["search", "trending", "evaluate"], required = True
    )
    parser.add_argument("--channel", help="Marketing channel to search APIs for")
    parser.add_argument("--category", help="Category for trending search")
    parser.add_argument("--api - url", help="API URL to evaluate")
    parser.add_argument(
        "--max - results", type = int, default = 10, help="Maximum results to return"
    )

    args = parser.parse_args()

    service = WebSearchService()

    if args.action == "search" and args.channel:
        candidates = service.search_apis_for_channel(args.channel, args.max_results)
        for candidate in candidates:
            print(f"\\n{candidate.name} ({candidate.provider})")
            print(f"  Pricing: {candidate.pricing_model}")
            print(f"  Quality Score: {candidate.quality_score:.2f}")
            print(f"  URL: {candidate.api_url}")
            print(f"  Features: {', '.join(candidate.features)}")
            if candidate.rate_limits:
                print(f"  Rate Limits: {candidate.rate_limits}")

    elif args.action == "trending":
        category = args.category or "marketing"
        candidates = service.discover_trending_apis(category)
        print(f"\\nTrending {category} APIs:")
        for candidate in candidates[:5]:
            print(
                f"  {candidate.name} - {candidate.pricing_model} - Score: {candidate.quality_score:.2f}"
            )

    elif args.action == "evaluate" and args.api_url:
        evaluation = service.evaluate_api_quality(args.api_url)
        print(f"\\nAPI Quality Evaluation for {args.api_url}:")
        print(f"Overall Score: {evaluation.get('overall_score', 'N / A')}")
        if "recommendations" in evaluation:
            print("Recommendations:")
            for rec in evaluation["recommendations"]:
                print(f"  + {rec}")
        if "concerns" in evaluation:
            print("Concerns:")
            for concern in evaluation["concerns"]:
                print(f"  - {concern}")

    else:
        parser.print_help()