#!/usr / bin / env python3
""""""
TRAE.AI Research Agent - The Intelligence Officer

The system's eyes and ears that runs the "Hypocrisy Engine," finds new'
zero - cost APIs and affiliates, and incorporates Autonomous Trend Forecasting
using pytrends to preempt market shifts.
""""""

import json
import logging
import queue
import re
import sqlite3
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

try:

    from pytrends.request import TrendReq

except ImportError:
    TrendReq = None
    print("Warning: pytrends not installed. Install with: pip install pytrends")

from .base_agents import BaseAgent

@dataclass


class TrendData:
    """Trend analysis data"""

    keyword: str
    interest_score: int
    trend_direction: str  # 'rising', 'falling', 'stable'
    related_queries: List[str]
    geographic_data: Dict[str, int]
    timestamp: datetime
    confidence: float

@dataclass


class APIDiscovery:
    """Discovered API information"""

    api_name: str
    base_url: str
    description: str
    endpoints: List[str]
    authentication_type: str
    cost_model: str  # 'free', 'freemium', 'paid'
    rate_limits: Dict[str, Any]
    discovered_at: datetime
    quality_score: float

@dataclass


class HypocrisyAlert:
    """Hypocrisy detection result"""

    target: str
    statement_1: str
    statement_2: str
    contradiction_type: str
    confidence: float
    evidence_urls: List[str]
    detected_at: datetime

@dataclass


class MarketIntelligence:
    """Market intelligence report"""

    sector: str
    key_trends: List[str]
    opportunities: List[str]
    threats: List[str]
    competitor_analysis: Dict[str, Any]
    market_sentiment: float
    generated_at: datetime


class ResearchAgent(BaseAgent):
    """The Intelligence Officer - Autonomous research and trend analysis"""


    def __init__(self, db_path: str = "data / right_perspective.db"):
        super().__init__("ResearchAgent")
        self.db_path = db_path
        self.logger = logging.getLogger(self.__class__.__name__)
        self.initialize_database()

        # Initialize pytrends
        self.pytrends = None
        if TrendReq:
            try:
                self.pytrends = TrendReq(hl="en - US", tz = 360)
            except Exception as e:
                self.logger.warning(f"Failed to initialize pytrends: {e}")

        # Research parameters
        self.trend_check_interval = 3600  # 1 hour
        self.api_discovery_interval = 86400  # 24 hours
        self.hypocrisy_scan_interval = 7200  # 2 hours

        # Monitoring threads
        self.monitoring_active = False
        self.trend_thread = None
        self.api_thread = None
        self.hypocrisy_thread = None

        # Research queues
        self.research_queue = queue.Queue()

        # Known API directories
        self.api_directories = [
            "https://api.publicapis.org / entries",
                "https://github.com / public - apis / public - apis",
                "https://rapidapi.com / search/",
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 ]

        # Hypocrisy detection patterns
        self.contradiction_patterns = [
            (r"never\\s+\\w+", r"always\\s+\\w+"),
                (r"impossible", r"definitely\\s + possible"),
                (r"will\\s + never", r"will\\s + definitely"),
                (r"completely\\s + against", r"fully\\s + support"),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 ]


    def get_status(self) -> Dict[str, Any]:
        """Get current status of the research agent"""
        return {
            "agent_name": self.name,
            "monitoring_active": self.monitoring_active,
            "pytrends_available": self.pytrends is not None,
            "last_trend_check": getattr(self, "last_trend_check", None),
            "last_api_discovery": getattr(self, "last_api_discovery", None),
            "last_hypocrisy_scan": getattr(self, "last_hypocrisy_scan", None),
# BRACKET_SURGEON: disabled
#         }


    def get_capabilities(self) -> List[str]:
        """Get list of agent capabilities"""
        return [
            "trend_analysis",
                "api_discovery",
                "hypocrisy_detection",
                "market_intelligence",
                "autonomous_monitoring",
                "research_target_management",
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 ]


    def _execute_with_monitoring(:
        self, task: str, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Execute task with monitoring and logging"""
        start_time = time.time()
        self.logger.info(f"Executing research task: {task}")

        try:
            if task == "discover_apis":
                search_terms = context.get("search_terms", []) if context else []
                result = self.discover_apis(search_terms)
        except Exception as e:
            pass
        return {
            "success": True,
            "data": result,
            "execution_time": time.time() - start_time,
# BRACKET_SURGEON: disabled
#         }
            elif task == "analyze_trends":
                keywords = context.get("keywords", []) if context else []
                result = self.analyze_trends(keywords)
        return {
            "success": True,
            "data": result,
            "execution_time": time.time() - start_time,
# BRACKET_SURGEON: disabled
#         }
            elif task == "run_hypocrisy_engine":
                target = context.get("target") if context else None
                result = self.run_hypocrisy_engine(target)
        return {
            "success": True,
            "data": result,
            "execution_time": time.time() - start_time,
# BRACKET_SURGEON: disabled
#         }
            else:
                pass
        return {
            "success": False,
            "error": f"Unknown task: {task}",
            "execution_time": time.time() - start_time,
# BRACKET_SURGEON: disabled
#         }
        except Exception as e:
            self.logger.error(f"Task execution failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "execution_time": time.time() - start_time,
# BRACKET_SURGEON: disabled
#             }


    def _rephrase_task(self, original_task: str) -> str:
        """Rephrase task for better execution"""
        # Simple rephrasing logic for research tasks
        task_mappings = {
            "find apis": "discover_apis",
            "search for apis": "discover_apis",
            "api discovery": "discover_apis",
            "trend analysis": "analyze_trends",
            "check trends": "analyze_trends",
            "hypocrisy check": "run_hypocrisy_engine",
            "contradiction detection": "run_hypocrisy_engine",
# BRACKET_SURGEON: disabled
#         }

        lower_task = original_task.lower().strip()
        for key, value in task_mappings.items():
            if key in lower_task:
                pass
        return value

        return original_task


    def _validate_rephrase_accuracy(self, original: str, rephrased: str) -> bool:
        """Validate if rephrased task maintains original intent"""
        # Simple validation - check if rephrased task is a known research operation
        valid_tasks = ["discover_apis", "analyze_trends", "run_hypocrisy_engine"]
        return rephrased in valid_tasks or rephrased == original

    @property


    def capabilities(self) -> List[str]:
        """Property accessor for capabilities"""
        return self.get_capabilities()


    def __post_init__(self):
        """Initialize agent parameters after parent initialization"""
        # Research parameters
        self.trend_check_interval = 3600  # 1 hour
        self.api_discovery_interval = 86400  # 24 hours
        self.hypocrisy_scan_interval = 7200  # 2 hours

        # Monitoring threads
        self.monitoring_active = False
        self.trend_thread = None
        self.api_thread = None
        self.hypocrisy_thread = None

        # Research queues
        self.research_queue = queue.Queue()

        # Known API directories
        self.api_directories = [
            "https://api.publicapis.org / entries",
                "https://github.com / public - apis / public - apis",
                "https://rapidapi.com / search/",
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 ]

        # Hypocrisy detection patterns
        self.contradiction_patterns = [
            (r"never\\s+\\w+", r"always\\s+\\w+"),
                (r"impossible", r"definitely\\s + possible"),
                (r"will\\s + never", r"will\\s + definitely"),
                (r"completely\\s + against", r"fully\\s + support"),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 ]


    def initialize_database(self):
        """Initialize research database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """"""
                CREATE TABLE IF NOT EXISTS trend_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        keyword TEXT NOT NULL,
                        interest_score INTEGER NOT NULL,
                        trend_direction TEXT NOT NULL,
                        related_queries TEXT NOT NULL,
                        geographic_data TEXT NOT NULL,
                        timestamp TIMESTAMP NOT NULL,
                        confidence REAL NOT NULL
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
            """"""
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

            conn.execute(
                """"""
                CREATE TABLE IF NOT EXISTS api_discoveries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        api_name TEXT NOT NULL,
                        base_url TEXT NOT NULL,
                        description TEXT NOT NULL,
                        endpoints TEXT NOT NULL,
                        authentication_type TEXT NOT NULL,
                        cost_model TEXT NOT NULL,
                        rate_limits TEXT NOT NULL,
                        discovered_at TIMESTAMP NOT NULL,
                        quality_score REAL NOT NULL
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
            """"""
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

            conn.execute(
                """"""
                CREATE TABLE IF NOT EXISTS hypocrisy_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        target TEXT NOT NULL,
                        statement_1 TEXT NOT NULL,
                        statement_2 TEXT NOT NULL,
                        contradiction_type TEXT NOT NULL,
                        confidence REAL NOT NULL,
                        evidence_urls TEXT NOT NULL,
                        detected_at TIMESTAMP NOT NULL
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
            """"""
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

            conn.execute(
                """"""
                CREATE TABLE IF NOT EXISTS market_intelligence (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        sector TEXT NOT NULL,
                        key_trends TEXT NOT NULL,
                        opportunities TEXT NOT NULL,
                        threats TEXT NOT NULL,
                        competitor_analysis TEXT NOT NULL,
                        market_sentiment REAL NOT NULL,
                        generated_at TIMESTAMP NOT NULL
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
            """"""
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

            conn.execute(
                """"""
                CREATE TABLE IF NOT EXISTS research_targets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        target_type TEXT NOT NULL,
                        target_value TEXT NOT NULL,
                        priority INTEGER NOT NULL,
                        last_researched TIMESTAMP,
                        created_at TIMESTAMP NOT NULL
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
            """"""
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )


    def start_monitoring(self):
        """Start autonomous research monitoring"""
        if self.monitoring_active:
            return

        self.monitoring_active = True

        # Start trend monitoring
        self.trend_thread = threading.Thread(target = self._trend_monitor,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     daemon = True)
        self.trend_thread.start()

        # Start API discovery
        self.api_thread = threading.Thread(
            target = self._api_discovery_monitor, daemon = True
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         )
        self.api_thread.start()

        # Start hypocrisy scanning
        self.hypocrisy_thread = threading.Thread(
            target = self._hypocrisy_monitor, daemon = True
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         )
        self.hypocrisy_thread.start()

        self.logger.info("Research monitoring started")


    def stop_monitoring(self):
        """Stop research monitoring"""
        self.monitoring_active = False
        self.logger.info("Research monitoring stopped")


    def analyze_trends(:
        self, keywords: List[str], timeframe: str = "today 3 - m"
    ) -> List[TrendData]:
        """Analyze trends for given keywords"""
        if not self.pytrends:
            self.logger.warning("pytrends not available")
        return []

        trend_data = []

        try:
            # Build payload
            self.pytrends.build_payload(
                keywords, cat = 0, timeframe = timeframe, geo="", gprop=""
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

            # Get interest over time
            interest_over_time = self.pytrends.interest_over_time()

            # Get related queries
            related_queries = self.pytrends.related_queries()

            # Get interest by region
            interest_by_region = self.pytrends.interest_by_region(resolution="COUNTRY")

            for keyword in keywords:
                if keyword in interest_over_time.columns:
                    # Calculate trend direction
                    values = interest_over_time[keyword].values
                    if len(values) >= 2:
                        recent_avg = (
                            values[-5:].mean() if len(values) >= 5 else values[-1]
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )
                        older_avg = (
                            values[:-5].mean() if len(values) >= 10 else values[0]
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )

                        if recent_avg > older_avg * 1.1:
                            trend_direction = "rising"
                        elif recent_avg < older_avg * 0.9:
                            trend_direction = "falling"
                        else:
                            trend_direction = "stable"
                    else:
                        trend_direction = "stable"

                    # Get related queries for this keyword
                    related = []
                    if (
                        keyword in related_queries
                        and related_queries[keyword]["top"] is not None
# BRACKET_SURGEON: disabled
#                     ):
                        related = related_queries[keyword]["top"]["query"].tolist()[:10]

                    # Get geographic data
                    geo_data = {}
                    if keyword in interest_by_region.columns:
                        geo_data = interest_by_region[keyword].to_dict()

                    trend_data.append(
                        TrendData(
                            keyword = keyword,
                                interest_score = int(values[-1]) if len(values) > 0 else 0,
                                trend_direction = trend_direction,
                                related_queries = related,
                                geographic_data = geo_data,
                                timestamp = datetime.now(),
                                confidence = 0.8,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                                 )
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )

            # Save trend data
            self._save_trend_data(trend_data)

        except Exception as e:
            self.logger.error(f"Error analyzing trends: {e}")

        return trend_data


    def discover_apis(self, search_terms: List[str] = None) -> List[APIDiscovery]:
        """Discover new APIs from multiple free sources"""
        if search_terms is None:
            search_terms = ["free api", "public api", "rest api", "json api"]

        discoveries = []

        # Source 1: PublicAPIs.org - Comprehensive free API directory
        discoveries.extend(self._discover_from_publicapis())

        # Source 2: GitHub API Collections - Curated lists
        discoveries.extend(self._discover_from_github_collections())

        # Source 3: RapidAPI Free Tier - Popular APIs with free tiers
        discoveries.extend(self._discover_from_rapidapi_free())

        # Source 4: Government and Open Data APIs
        discoveries.extend(self._discover_government_apis())

        # Source 5: Developer - friendly APIs with generous free tiers
        discoveries.extend(self._discover_developer_friendly_apis())

        # Remove duplicates and save
        unique_discoveries = self._deduplicate_apis(discoveries)
        self._save_api_discoveries(unique_discoveries)

        self.logger.info(
            f"Discovered {len(unique_discoveries)} unique APIs from {len(discoveries)} total"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         )
        return unique_discoveries


    def _discover_from_publicapis(self) -> List[APIDiscovery]:
        """Discover APIs from PublicAPIs.org"""
        discoveries = []
        try:
            response = requests.get("https://api.publicapis.org / entries",
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     timeout = 10)
            if response.status_code == 200:
                data = response.json()

                for entry in data.get("entries", [])[:100]:  # Increased limit
                    # Filter for free APIs
                    auth = entry.get("Auth", "").lower()
                    if (
                        auth in ["", "no", "none"]
                        or "free" in entry.get("Description", "").lower()
# BRACKET_SURGEON: disabled
#                     ):
                        discovery = APIDiscovery(
                            api_name = entry.get("API", "Unknown"),
                                base_url = entry.get("Link", ""),
                                description = entry.get("Description", ""),
                                endpoints=[],
                                authentication_type = auth if auth else "none",
                                cost_model="free",
                                rate_limits={"source": "publicapis.org"},
                                discovered_at = datetime.now(),
                                quality_score = self._calculate_api_quality_score(entry),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                                 )
                        discoveries.append(discovery)
        except Exception as e:
            self.logger.error(f"Error discovering from PublicAPIs: {e}")
        return discoveries


    def _discover_from_github_collections(self) -> List[APIDiscovery]:
        """Discover APIs from GitHub awesome lists and collections"""
        discoveries = []

        # Popular free APIs from known collections
        free_apis = [
            {
            "API": "JSONPlaceholder",
            "Link": "https://jsonplaceholder.typicode.com",
            "Description": "Fake REST API for testing and prototyping",
            "Auth": "none",
# BRACKET_SURGEON: disabled
#         },
                {
            "API": "httpbin",
            "Link": "https://httpbin.org",
            "Description": "HTTP request and response testing service",
            "Auth": "none",
# BRACKET_SURGEON: disabled
#         },
                {
            "API": "Cat Facts",
            "Link": "https://catfact.ninja",
            "Description": "Daily cat facts API",
            "Auth": "none",
# BRACKET_SURGEON: disabled
#         },
                {
            "API": "Dog API",
            "Link": "https://dog.ceo / dog - api",
            "Description": "Collection of dog images",
            "Auth": "none",
# BRACKET_SURGEON: disabled
#         },
                {
            "API": "Advice Slip",
            "Link": "https://api.adviceslip.com",
            "Description": "Random advice generator",
            "Auth": "none",
# BRACKET_SURGEON: disabled
#         },
                {
            "API": "JokeAPI",
            "Link": "https://jokeapi.dev",
            "Description": "Programming and general jokes",
            "Auth": "none",
# BRACKET_SURGEON: disabled
#         },
                {
            "API": "Numbers API",
            "Link": "http://numbersapi.com",
            "Description": "Interesting facts about numbers",
            "Auth": "none",
# BRACKET_SURGEON: disabled
#         },
                {
            "API": "Quotable",
            "Link": "https://quotable.io",
            "Description": "Random quotes API",
            "Auth": "none",
# BRACKET_SURGEON: disabled
#         },
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 ]

        for api_data in free_apis:
            discovery = APIDiscovery(
                api_name = api_data["API"],
                    base_url = api_data["Link"],
                    description = api_data["Description"],
                    endpoints=[],
                    authentication_type = api_data["Auth"],
                    cost_model="free",
                    rate_limits={"source": "github_collections"},
                    discovered_at = datetime.now(),
                    quality_score = 0.8,  # High quality curated APIs
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )
            discoveries.append(discovery)

        return discoveries


    def _discover_from_rapidapi_free(self) -> List[APIDiscovery]:
        """Discover free tier APIs from RapidAPI"""
        discoveries = []

        # Popular RapidAPI free tier APIs
        rapidapi_free = [
            {
            "API": "OpenWeatherMap",
            "Link": "https://openweathermap.org / api",
            "Description": "Weather data API with free tier",
            "Auth": "apikey",
# BRACKET_SURGEON: disabled
#         },
                {
            "API": "News API",
            "Link": "https://newsapi.org",
            "Description": "News articles from various sources",
            "Auth": "apikey",
# BRACKET_SURGEON: disabled
#         },
                {
            "API": "CoinGecko",
            "Link": "https://coingecko.com / en / api",
            "Description": "Cryptocurrency data API",
            "Auth": "none",
# BRACKET_SURGEON: disabled
#         },
                {
            "API": "REST Countries",
            "Link": "https://restcountries.com",
            "Description": "Country information API",
            "Auth": "none",
# BRACKET_SURGEON: disabled
#         },
                {
            "API": "IP Geolocation",
            "Link": "https://ipapi.co",
            "Description": "IP address geolocation",
            "Auth": "none",
# BRACKET_SURGEON: disabled
#         },
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 ]

        for api_data in rapidapi_free:
            discovery = APIDiscovery(
                api_name = api_data["API"],
                    base_url = api_data["Link"],
                    description = api_data["Description"],
                    endpoints=[],
                    authentication_type = api_data["Auth"],
                    cost_model="freemium",
                    rate_limits={"source": "rapidapi_free", "tier": "free"},
                    discovered_at = datetime.now(),
                    quality_score = 0.9,  # High quality commercial APIs
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )
            discoveries.append(discovery)

        return discoveries


    def _discover_government_apis(self) -> List[APIDiscovery]:
        """Discover government and open data APIs"""
        discoveries = []

        gov_apis = [
            {
            "API": "NASA Open Data",
            "Link": "https://api.nasa.gov",
            "Description": "NASA datasets and imagery",
            "Auth": "apikey",
# BRACKET_SURGEON: disabled
#         },
                {
            "API": "USGS Earthquake",
            "Link": "https://earthquake.usgs.gov / fdsnws / event / 1/",
            "Description": "Real - time earthquake data",
            "Auth": "none",
# BRACKET_SURGEON: disabled
#         },
                {
            "API": "World Bank",
            "Link": "https://datahelpdesk.worldbank.org / knowledgebase / articles / 889392",
            "Description": "World development indicators",
            "Auth": "none",
# BRACKET_SURGEON: disabled
#         },
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 ]

        for api_data in gov_apis:
            discovery = APIDiscovery(
                api_name = api_data["API"],
                    base_url = api_data["Link"],
                    description = api_data["Description"],
                    endpoints=[],
                    authentication_type = api_data["Auth"],
                    cost_model="free",
                    rate_limits={"source": "government", "reliability": "high"},
                    discovered_at = datetime.now(),
                    quality_score = 0.95,  # Government APIs are highly reliable
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )
            discoveries.append(discovery)

        return discoveries


    def _discover_developer_friendly_apis(self) -> List[APIDiscovery]:
        """Discover developer - friendly APIs with generous free tiers"""
        discoveries = []

        dev_apis = [
            {
            "API": "GitHub API",
            "Link": "https://api.github.com",
            "Description": "GitHub repository and user data",
            "Auth": "oauth",
# BRACKET_SURGEON: disabled
#         },
                {
            "API": "Unsplash",
            "Link": "https://unsplash.com / developers",
            "Description": "High - quality stock photos",
            "Auth": "oauth",
# BRACKET_SURGEON: disabled
#         },
                {
            "API": "Lorem Picsum",
            "Link": "https://picsum.photos",
            "Description": "Lorem Ipsum for photos",
            "Auth": "none",
# BRACKET_SURGEON: disabled
#         },
                {
            "API": "QR Server",
            "Link": "https://goqr.me / api",
            "Description": "QR code generation",
            "Auth": "none",
# BRACKET_SURGEON: disabled
#         },
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 ]

        for api_data in dev_apis:
            discovery = APIDiscovery(
                api_name = api_data["API"],
                    base_url = api_data["Link"],
                    description = api_data["Description"],
                    endpoints=[],
                    authentication_type = api_data["Auth"],
                    cost_model="freemium",
                    rate_limits={"source": "developer_friendly", "generous": True},
                    discovered_at = datetime.now(),
                    quality_score = 0.85,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )
            discoveries.append(discovery)

        return discoveries


    def _deduplicate_apis(self, discoveries: List[APIDiscovery]) -> List[APIDiscovery]:
        """Remove duplicate API discoveries based on name and base URL"""
        seen = set()
        unique_discoveries = []

        for discovery in discoveries:
            key = (discovery.api_name.lower(), discovery.base_url.lower())
            if key not in seen:
                seen.add(key)
                unique_discoveries.append(discovery)

        return unique_discoveries


    def run_hypocrisy_engine(self, targets: List[str]) -> List[HypocrisyAlert]:
        """Run hypocrisy detection on targets"""
        alerts = []

        for target in targets:
            try:
                # Search for statements by target
                statements = self._collect_statements(target)

                # Analyze for contradictions
                contradictions = self._detect_contradictions(statements)

                for contradiction in contradictions:
                    alert = HypocrisyAlert(
                        target = target,
                            statement_1 = contradiction["statement_1"],
                            statement_2 = contradiction["statement_2"],
                            contradiction_type = contradiction["type"],
                            confidence = contradiction["confidence"],
                            evidence_urls = contradiction["evidence_urls"],
                            detected_at = datetime.now(),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                             )
                    alerts.append(alert)

            except Exception as e:
                self.logger.error(f"Error running hypocrisy engine for {target}: {e}")

        # Save alerts
        self._save_hypocrisy_alerts(alerts)

        return alerts


    def generate_market_intelligence(self, sector: str) -> MarketIntelligence:
        """Generate comprehensive market intelligence report"""
        try:
            # Analyze trends for sector
                sector_keywords = self._get_sector_keywords(sector)
            trends = self.analyze_trends(sector_keywords)

            # Extract key trends
            key_trends = []
            opportunities = []
            threats = []

            for trend in trends:
                if trend.trend_direction == "rising" and trend.interest_score > 50:
                    key_trends.append(f"{trend.keyword} (↑{trend.interest_score})")
                    opportunities.append(f"Growing interest in {trend.keyword}")
                elif trend.trend_direction == "falling" and trend.interest_score < 30:
                    threats.append(f"Declining interest in {trend.keyword}")

            # Analyze competitors (placeholder)
            competitor_analysis = {
            "top_competitors": [],
            "market_share": {},
            "competitive_advantages": [],
        except Exception as e:
            pass
# BRACKET_SURGEON: disabled
#         }

            # Calculate market sentiment
            market_sentiment = self._calculate_market_sentiment(trends)

            intelligence = MarketIntelligence(
                sector = sector,
                    key_trends = key_trends,
                    opportunities = opportunities,
                    threats = threats,
                    competitor_analysis = competitor_analysis,
                    market_sentiment = market_sentiment,
                    generated_at = datetime.now(),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )

            # Save intelligence
            self._save_market_intelligence(intelligence)

        return intelligence

        except Exception as e:
            self.logger.error(f"Error generating market intelligence: {e}")
        return MarketIntelligence(
                sector = sector,
                    key_trends=[],
                    opportunities=[],
                    threats=[],
                    competitor_analysis={},
                    market_sentiment = 0.5,
                    generated_at = datetime.now(),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )


    def _trend_monitor(self):
        """Monitor trends continuously"""
        while self.monitoring_active:
            try:
                # Get research targets
                targets = self._get_research_targets("trend")

                if targets:
                    keywords = [target["target_value"] for target in targets]
                    self.analyze_trends(keywords)

                time.sleep(self.trend_check_interval)

            except Exception as e:
                self.logger.error(f"Trend monitor error: {e}")
                time.sleep(self.trend_check_interval)


    def _api_discovery_monitor(self):
        """Monitor for new API discoveries"""
        while self.monitoring_active:
            try:
                # Discover new APIs
                self.discover_apis()

                time.sleep(self.api_discovery_interval)

            except Exception as e:
                self.logger.error(f"API discovery monitor error: {e}")
                time.sleep(self.api_discovery_interval)


    def _hypocrisy_monitor(self):
        """Monitor for hypocrisy detection"""
        while self.monitoring_active:
            try:
                # Get hypocrisy targets
                targets = self._get_research_targets("hypocrisy")

                if targets:
                    target_names = [target["target_value"] for target in targets]
                    self.run_hypocrisy_engine(target_names)

                time.sleep(self.hypocrisy_scan_interval)

            except Exception as e:
                self.logger.error(f"Hypocrisy monitor error: {e}")
                time.sleep(self.hypocrisy_scan_interval)


    def _collect_statements(self, target: str) -> List[Dict[str, Any]]:
        """Collect statements from a target (placeholder)"""
        # This would integrate with social media APIs, news APIs, etc.
        # Placeholder implementation
        return [
            {
            "text": f"Sample statement 1 from {target}",
            "url": "https://example.com / 1",
            "date": datetime.now() - timedelta(days = 30),
# BRACKET_SURGEON: disabled
#         },
                {
            "text": f"Sample statement 2 from {target}",
            "url": "https://example.com / 2",
            "date": datetime.now() - timedelta(days = 1),
# BRACKET_SURGEON: disabled
#         },
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 ]


    def _detect_contradictions(:
        self, statements: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Detect contradictions in statements"""
        contradictions = []

        for i, stmt1 in enumerate(statements):
            for j, stmt2 in enumerate(statements[i + 1 :], i + 1):
                # Check for pattern - based contradictions
                for pattern1, pattern2 in self.contradiction_patterns:
                    if re.search(pattern1, stmt1["text"], re.IGNORECASE) and re.search(
                        pattern2, stmt2["text"], re.IGNORECASE
# BRACKET_SURGEON: disabled
#                     ):

                        contradictions.append(
                            {
            "statement_1": stmt1["text"],
            "statement_2": stmt2["text"],
            "type": "direct",  # Fixed: use valid constraint value instead of 'pattern_contradiction'
            "confidence": 0.7,
            "evidence_urls": [stmt1["url"], stmt2["url"]],
# BRACKET_SURGEON: disabled
#         }
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )

        return contradictions


    def _calculate_api_quality_score(self, api_entry: Dict[str, Any]) -> float:
        """Calculate quality score for discovered API"""
        score = 0.5  # Base score

        # Check for HTTPS
        if api_entry.get("Link", "").startswith("https://"):
            score += 0.2

        # Check for good description
        if len(api_entry.get("Description", "")) > 50:
            score += 0.1

        # Check for no auth (easier to use)
        if api_entry.get("Auth", "").lower() in ["", "no", "none"]:
            score += 0.2

        return min(1.0, score)


    def _get_sector_keywords(self, sector: str) -> List[str]:
        """Get relevant keywords for a sector"""
        sector_keywords = {
            "technology": [
                "AI",
                    "machine learning",
                    "blockchain",
                    "cloud computing",
                    "cybersecurity",
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     ],
            "finance": [
                "fintech",
                    "cryptocurrency",
                    "digital banking",
                    "robo advisor",
                    "payment",
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     ],
            "health": [
                "telemedicine",
                    "digital health",
                    "wearables",
                    "health app",
                    "medical AI",
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     ],
            "education": [
                "edtech",
                    "online learning",
                    "e - learning",
                    "educational app",
                    "remote education",
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     ],
            "retail": [
                "e - commerce",
                    "online shopping",
                    "retail tech",
                    "omnichannel",
                    "digital retail",
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     ],
# BRACKET_SURGEON: disabled
#         }

        return sector_keywords.get(sector.lower(), [sector])


    def _calculate_market_sentiment(self, trends: List[TrendData]) -> float:
        """Calculate overall market sentiment from trends"""
        if not trends:
            pass
        return 0.5

        rising_count = sum(1 for t in trends if t.trend_direction == "rising")
        falling_count = sum(1 for t in trends if t.trend_direction == "falling")
        total_count = len(trends)

        # Sentiment score based on trend directions
        sentiment = (rising_count - falling_count) / total_count
        return max(0, min(1, 0.5 + sentiment * 0.5))


    def _get_research_targets(self, target_type: str) -> List[Dict[str, Any]]:
        """Get research targets from database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """"""
                SELECT target_value, priority, last_researched
                FROM research_targets
                WHERE target_type = ?
                ORDER BY priority DESC, last_researched ASC
                LIMIT 10
            ""","""
                (target_type,),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )

        return [
                {"target_value": row[0], "priority": row[1], "last_researched": row[2]}
                for row in cursor.fetchall()
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             ]


    def add_research_target(:
        self, target_type: str, target_value: str, priority: int = 1
# BRACKET_SURGEON: disabled
#     ):
        """Add research target"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """"""
                INSERT OR REPLACE INTO research_targets
                (target_type, target_value, priority, created_at)
                VALUES (?, ?, ?, ?)
            ""","""
                (target_type, target_value, priority, datetime.now().isoformat()),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )


    def _save_trend_data(self, trends: List[TrendData]):
        """Save trend data to database"""
        with sqlite3.connect(self.db_path) as conn:
            for trend in trends:
                conn.execute(
                    """"""
                    INSERT INTO trend_data
                    (keyword, interest_score, trend_direction, related_queries,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         geographic_data, timestamp, confidence)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ""","""
                    (
                        trend.keyword,
                            trend.interest_score,
                            trend.trend_direction,
                            json.dumps(trend.related_queries),
                            json.dumps(trend.geographic_data),
                            trend.timestamp.isoformat(),
                            trend.confidence,
# BRACKET_SURGEON: disabled
#                             ),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )


    def _save_api_discoveries(self, discoveries: List[APIDiscovery]):
        """Save API discoveries to database"""
        with sqlite3.connect(self.db_path) as conn:
            for discovery in discoveries:
                conn.execute(
                    """"""
                    INSERT OR REPLACE INTO api_discoveries
                    (api_name, base_url, description, endpoints, authentication_type,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         cost_model, rate_limits, discovered_at, quality_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ""","""
                    (
                        discovery.api_name,
                            discovery.base_url,
                            discovery.description,
                            json.dumps(discovery.endpoints),
                            discovery.authentication_type,
                            discovery.cost_model,
                            json.dumps(discovery.rate_limits),
                            discovery.discovered_at.isoformat(),
                            discovery.quality_score,
# BRACKET_SURGEON: disabled
#                             ),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )


    def _save_hypocrisy_alerts(self, alerts: List[HypocrisyAlert]):
        """Save hypocrisy alerts to database"""
        with sqlite3.connect(self.db_path) as conn:
            for alert in alerts:
                conn.execute(
                    """"""
                    INSERT INTO hypocrisy_alerts
                    (target, statement_1, statement_2, contradiction_type,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         confidence, evidence_urls, detected_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ""","""
                    (
                        alert.target,
                            alert.statement_1,
                            alert.statement_2,
                            alert.contradiction_type,
                            alert.confidence,
                            json.dumps(alert.evidence_urls),
                            alert.detected_at.isoformat(),
# BRACKET_SURGEON: disabled
#                             ),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )


    def _save_market_intelligence(self, intelligence: MarketIntelligence):
        """Save market intelligence to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """"""
                INSERT INTO market_intelligence
                (sector, key_trends, opportunities, threats, competitor_analysis,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     market_sentiment, generated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ""","""
                (
                    intelligence.sector,
                        json.dumps(intelligence.key_trends),
                        json.dumps(intelligence.opportunities),
                        json.dumps(intelligence.threats),
                        json.dumps(intelligence.competitor_analysis),
                        intelligence.market_sentiment,
                        intelligence.generated_at.isoformat(),
# BRACKET_SURGEON: disabled
#                         ),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )


    def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute research task"""
        task_type = task_data.get("type")

        if task_type == "analyze_trends":
            keywords = task_data.get("keywords", [])
            trends = self.analyze_trends(keywords)
        return {"success": True, "trends": [asdict(t) for t in trends]}

        elif task_type == "discover_apis":
            discoveries = self.discover_apis(task_data.get("search_terms"))
        return {"success": True, "discoveries": [asdict(d) for d in discoveries]}

        elif task_type == "hypocrisy_scan":
            targets = task_data.get("targets", [])
            alerts = self.run_hypocrisy_engine(targets)
        return {"success": True, "alerts": [asdict(a) for a in alerts]}

        elif task_type == "market_intelligence":
            sector = task_data.get("sector", "technology")
            intelligence = self.generate_market_intelligence(sector)
        return {"success": True, "intelligence": asdict(intelligence)}

        elif task_type == "start_monitoring":
            self.start_monitoring()
        return {"success": True}

        return {"success": False, "error": f"Unknown task type: {task_type}"}

if __name__ == "__main__":
    # Test the Research Agent
    research_agent = ResearchAgent()

    # Add some research targets
    research_agent.add_research_target("trend", "artificial intelligence", 3)
    research_agent.add_research_target("trend", "machine learning", 2)
    research_agent.add_research_target("hypocrisy", "tech_ceo_example", 1)

    # Test trend analysis
    if research_agent.pytrends:
        trends = research_agent.analyze_trends(["AI", "machine learning"])
        print(f"Analyzed {len(trends)} trends")
        for trend in trends:
            print(
                f"- {trend.keyword}: {trend.interest_score} ({trend.trend_direction})"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

    # Test API discovery
    apis = research_agent.discover_apis()
    print(f"Discovered {len(apis)} APIs")

    # Test market intelligence
    intelligence = research_agent.generate_market_intelligence("technology")
    print(f"Market Intelligence for {intelligence.sector}:")
    print(f"- Key trends: {len(intelligence.key_trends)}")
    print(f"- Opportunities: {len(intelligence.opportunities)}")
    print(f"- Market sentiment: {intelligence.market_sentiment:.2f}")

    # Start monitoring
    research_agent.start_monitoring()

    try:
        time.sleep(5)
    except KeyboardInterrupt:
        pass
    finally:
        research_agent.stop_monitoring()