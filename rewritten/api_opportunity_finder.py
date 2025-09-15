#!/usr/bin/env python3
""""""
API Opportunity Finder - Research Agent for Automated API Discovery

This module acts as an intelligent research agent that discovers new API opportunities
by analyzing public repositories, documentation, and market trends. It integrates with
the existing Ollama LLM system for advanced analysis and scoring.

Features:
- Automated API discovery from GitHub, GitLab, and other sources
- LLM - powered API documentation analysis and capability assessment
- Intelligent scoring and prioritization of API opportunities
- Integration with existing Ollama infrastructure
- Comprehensive logging and analytics
""""""

import asyncio
import hashlib
import json
import logging
import re
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

import aiohttp

# Import existing Ollama integration

from backend.integrations.ollama_integration import (
    OllamaIntegration,
    PromptTemplate,
# BRACKET_SURGEON: disabled
# )

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DiscoveryStatus(Enum):
    """Status of API discovery tasks"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SuggestionStatus(Enum):
    """Status of API suggestions"""

    DISCOVERED = "discovered"
    ANALYZED = "analyzed"
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"


@dataclass
class APIDiscoveryTask:
    """Represents an API discovery task"""

    id: Optional[int]
    task_type: str
    target_capability: Optional[str]
    search_parameters: Optional[str]
    task_name: Optional[str]
    capability_gap: Optional[str]
    search_keywords: Optional[str]
    target_domains: Optional[str]
    priority: int = 5
    status: str = "pending"
    assigned_agent: Optional[str] = None
    progress_notes: Optional[str] = None
    apis_found: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class APISuggestion:
    """Represents a discovered API suggestion"""

    id: Optional[int]
    api_name: str
    api_url: str
    description: str
    capability: str
    discovery_source: str
    confidence_score: float
    priority_score: float
    status: SuggestionStatus
    documentation_url: Optional[str] = None
    github_url: Optional[str] = None
    pricing_model: Optional[str] = None
    rate_limits: Optional[Dict[str, Any]] = None
    authentication_type: Optional[str] = None
    created_at: datetime = None
    analyzed_at: Optional[datetime] = None
    llm_analysis: Optional[Dict[str, Any]] = None


@dataclass
class ResearchContext:
    """Context for research operations"""

    current_capabilities: List[str]
    usage_patterns: Dict[str, int]
    budget_constraints: float
    priority_areas: List[str]
    excluded_sources: List[str] = None


class APIOpportunityFinder:
    """Intelligent API discovery and research agent"""

    def __init__(
        self,
        db_path: str = "right_perspective.db",
        ollama_base_url: str = "http://localhost:11434",
        ollama_model: str = "llama2:7b",
# BRACKET_SURGEON: disabled
#     ):
        self.db_path = db_path
        self.ollama_base_url = ollama_base_url
        self.ollama_model = ollama_model
        self._ollama_integration = None
        self._github_token = None  # Set via environment or config
        self._discovery_sources = {
            "github": "https://api.github.com",
            "gitlab": "https://gitlab.com/api/v4",
            "rapidapi": "https://rapidapi.com/search",
            "programmableweb": "https://www.programmableweb.com/apis/directory",
# BRACKET_SURGEON: disabled
#         }

        # Initialize database
        self._init_database()

        # Initialize Ollama integration
        self._init_ollama_integration()

    def _init_database(self):
        """Initialize database tables for API discovery"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Ensure api_discovery_tasks table exists
            cursor.execute(
                """"""
                CREATE TABLE IF NOT EXISTS api_discovery_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task_type TEXT NOT NULL,
                        target_capability TEXT,
                        search_parameters TEXT,
                        task_name TEXT,
                        capability_gap TEXT,
                        search_keywords TEXT,
                        target_domains TEXT,
                        priority INTEGER DEFAULT 5,
                        status TEXT DEFAULT 'pending',
                        assigned_agent TEXT,
                        progress_notes TEXT,
                        apis_found INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        completed_at TIMESTAMP
# BRACKET_SURGEON: disabled
#                 )
            """"""
# BRACKET_SURGEON: disabled
#             )

            # Ensure api_suggestions table exists
            cursor.execute(
                """"""
                CREATE TABLE IF NOT EXISTS api_suggestions (
                    suggestion_id TEXT PRIMARY KEY,
                        api_name TEXT NOT NULL,
                        api_url TEXT NOT NULL,
                        description TEXT,
                        capability TEXT NOT NULL,
                        discovery_source TEXT NOT NULL,
                        confidence_score REAL DEFAULT 0.0,
                        priority_score REAL DEFAULT 0.0,
                        status TEXT DEFAULT 'discovered',
                        documentation_url TEXT,
                        github_url TEXT,
                        pricing_model TEXT,
                        rate_limits TEXT,
                        authentication_type TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        analyzed_at TIMESTAMP,
                        llm_analysis TEXT,
                        UNIQUE(api_name, api_url)
# BRACKET_SURGEON: disabled
#                 )
            """"""
# BRACKET_SURGEON: disabled
#             )

            conn.commit()
            conn.close()
            logger.info("API discovery database initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize API discovery database: {e}")

    def _init_ollama_integration(self):
        """Initialize Ollama integration for LLM analysis"""
        try:
            self._ollama_integration = OllamaIntegration(
                {
                    "ollama_url": self.ollama_base_url,
                    "default_model": self.ollama_model,
                    "enable_caching": True,
                    "performance_monitoring": True,
                    "max_concurrent_requests": 3,
# BRACKET_SURGEON: disabled
#                 }
# BRACKET_SURGEON: disabled
#             )
            logger.info("Ollama integration initialized for API research")
        except Exception as e:
            logger.error(f"Failed to initialize Ollama integration: {e}")

    async def _query_ollama(self, prompt: str, system_prompt: str = None) -> Optional[str]:
        """Query local Ollama LLM for analysis using existing integration"""
        try:
            if not self._ollama_integration:
                logger.error("Ollama integration not initialized")
                return None

            # Create context for the query
            context = {"task_type": "api_research", "system_prompt": system_prompt}

            # Use the existing integration's query method
            response = await self._ollama_integration.query_llm(
                prompt=prompt,
                model_name=self.ollama_model,
                template=PromptTemplate.RESEARCH_SYNTHESIS,
                context=context,
                priority=7,
# BRACKET_SURGEON: disabled
#             )

            if response and response.response_text:
                return response.response_text.strip()
            else:
                logger.error("Ollama integration returned empty response")
                return None

        except Exception as e:
            logger.error(f"Error querying Ollama via integration: {e}")
            return None

    async def research_api_opportunities(
        self, context: ResearchContext, max_results: int = 50
    ) -> List[APISuggestion]:
        """Research and discover new API opportunities"""
        logger.info(f"Starting API opportunity research with context: {context.priority_areas}")

        suggestions = []

        # Create discovery task
        task = APIDiscoveryTask(
            id=None,  # Will be auto - generated by database
            task_type="api_research",
            target_capability=", ".join(context.priority_areas),
            search_parameters=json.dumps({"context": context.__dict__}),
            task_name=f"API Research for {', '.join(context.priority_areas)}",
            capability_gap="Research new API opportunities",
            search_keywords=json.dumps(context.priority_areas),
            target_domains=None,
            priority=5,
            status="pending",
            assigned_agent="api_opportunity_finder",
            progress_notes="Task created",
            apis_found=0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            completed_at=None,
# BRACKET_SURGEON: disabled
#         )

        await self._save_discovery_task(task)

        try:
            # Update task status
            task.status = "in_progress"
            task.started_at = datetime.now(timezone.utc)
            await self._update_discovery_task(task)

            # Search GitHub for API repositories
            github_suggestions = await self._search_github_apis(context, max_results // 2)
            suggestions.extend(github_suggestions)

            # Search RapidAPI marketplace
            rapidapi_suggestions = await self._search_rapidapi(context, max_results // 4)
            suggestions.extend(rapidapi_suggestions)

            # Search ProgrammableWeb directory
            programmableweb_suggestions = await self._search_programmableweb(
                context, max_results // 4
# BRACKET_SURGEON: disabled
#             )
            suggestions.extend(programmableweb_suggestions)

            # Analyze and score suggestions using LLM
            analyzed_suggestions = await self._analyze_suggestions_with_llm(suggestions, context)

            # Save suggestions to database
            for suggestion in analyzed_suggestions:
                await self._save_api_suggestion(suggestion)

            # Update task completion
            task.status = "completed"
            task.completed_at = datetime.now(timezone.utc)
            task.results_count = len(analyzed_suggestions)
            await self._update_discovery_task(task)

            logger.info(f"API research completed. Found {len(analyzed_suggestions)} opportunities")
            return analyzed_suggestions

        except Exception as e:
            logger.error(f"API research failed: {e}")
            task.status = "failed"
            task.error_message = str(e)
            await self._update_discovery_task(task)
            return []

    async def _search_github_apis(
        self, context: ResearchContext, max_results: int
    ) -> List[APISuggestion]:
        """Search GitHub for API repositories"""
        suggestions = []

        try:
            for priority_area in context.priority_areas[:3]:  # Limit to top 3 areas
                query = (
                    f"{priority_area} API language:Python language:JavaScript language:TypeScript"
# BRACKET_SURGEON: disabled
#                 )

                async with aiohttp.ClientSession() as session:
                    headers = {}
                    if self._github_token:
                        headers["Authorization"] = f"token {self._github_token}"

                    url = "https://api.github.com/search/repositories"
                    params = {
                        "q": query,
                        "sort": "stars",
                        "order": "desc",
                        "per_page": min(max_results // len(context.priority_areas), 20),
# BRACKET_SURGEON: disabled
#                     }

                    async with session.get(url, headers=headers, params=params) as response:
                        if response.status == 200:
                            data = await response.json()

                            for repo in data.get("items", []):
                                suggestion = APISuggestion(
                                    id=None,
                                    api_name=repo["name"],
                                    api_url=repo.get("homepage", repo["html_url"]),
                                    description=repo.get("description", ""),
                                    capability=priority_area,
                                    discovery_source="github",
                                    confidence_score=min(repo["stargazers_count"] / 1000, 1.0),
                                    priority_score=0.0,  # Will be calculated by LLM
                                    status=SuggestionStatus.DISCOVERED,
                                    github_url=repo["html_url"],
                                    created_at=datetime.now(timezone.utc),
# BRACKET_SURGEON: disabled
#                                 )
                                suggestions.append(suggestion)
                        else:
                            logger.warning(f"GitHub API search failed: {response.status}")

                # Rate limiting
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"GitHub API search error: {e}")

        return suggestions

    async def _search_rapidapi(
        self, context: ResearchContext, max_results: int
    ) -> List[APISuggestion]:
        """Search RapidAPI marketplace (simplified implementation)"""
        suggestions = []

        # Note: This would require RapidAPI marketplace API access
        # For now, return empty list - can be implemented with proper API access
        logger.info("RapidAPI search not implemented - requires marketplace API access")

        return suggestions

    async def _search_programmableweb(
        self, context: ResearchContext, max_results: int
    ) -> List[APISuggestion]:
        """Search ProgrammableWeb directory using web scraping"""
        suggestions = []

        try:
            # Import required libraries

            import requests
            from bs4 import BeautifulSoup

            # Search categories based on context priority areas
            search_categories = (
                context.priority_areas
                if context.priority_areas
                else ["data", "social", "messaging", "financial"]
# BRACKET_SURGEON: disabled
#             )

            for category in search_categories[:3]:  # Limit to 3 categories
                try:
                    # Construct search URL for ProgrammableWeb
                    search_url = f"https://www.programmableweb.com/category/{category}/apis"

                    headers = {
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                        "Accept": "text/html,application/xhtml + xml,application/xml;q = 0.9,*/*;q = 0.8",
                        "Accept - Language": "en - US,en;q = 0.5",
                        "Accept - Encoding": "gzip, deflate",
                        "Connection": "keep - alive",
# BRACKET_SURGEON: disabled
#                     }

                    # Make request with timeout
                    response = requests.get(search_url, headers=headers, timeout=15)
                    response.raise_for_status()

                    # Parse HTML content
                    soup = BeautifulSoup(response.content, "html.parser")

                    # Find API listings (adjust selectors based on actual ProgrammableWeb structure)
                    api_listings = soup.find_all(
                        "div", class_=["views - row", "api - listing", "node"]
                    ) or soup.find_all("article")

                    for listing in api_listings[
                        : max_results // 3
# BRACKET_SURGEON: disabled
#                     ]:  # Distribute results across categories
                        try:
                            # Extract API information
                            api_name = self._extract_api_name(listing)
                            api_url = self._extract_api_url(listing)
                            description = self._extract_api_description(listing)

                            if api_name and api_url:
                                # Check if it's a free API
                                is_free = self._check_if_free_api(description, api_name)

                                if (
                                    is_free or context.budget_constraints > 0
# BRACKET_SURGEON: disabled
#                                 ):  # Include if free or budget allows
                                    suggestion = APISuggestion(
                                        id=None,
                                        api_name=api_name,
                                        api_url=api_url,
                                        description=description
                                        or f"{api_name} API from ProgrammableWeb",
                                        capability=category,
                                        discovery_source="ProgrammableWeb",
                                        confidence_score=0.7,  # Medium confidence for scraped data
                                        priority_score=8.0 if is_free else 6.0,
                                        status=SuggestionStatus.DISCOVERED,
                                        created_at=datetime.now(timezone.utc),
                                        pricing_model="Free" if is_free else "Unknown",
# BRACKET_SURGEON: disabled
#                                     )
                                    suggestions.append(suggestion)

                        except Exception as e:
                            logger.warning(f"Error processing API listing: {e}")
                            continue

                    # Rate limiting between requests
                    await asyncio.sleep(2)

                except requests.RequestException as e:
                    logger.error(f"Failed to scrape ProgrammableWeb category {category}: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Unexpected error scraping category {category}: {e}")
                    continue

            logger.info(f"Found {len(suggestions)} API suggestions from ProgrammableWeb")
            return suggestions

        except ImportError as e:
            logger.error(f"Required libraries not available for ProgrammableWeb scraping: {e}")
            return []
        except Exception as e:
            logger.error(f"Error in ProgrammableWeb search: {e}")
            return []

    def _extract_api_name(self, listing) -> Optional[str]:
        """Extract API name from listing element"""
        try:
            # Try multiple selectors for API name
            name_selectors = [
                "h2 a",
                "h3 a",
                ".title a",
                ".api - name",
                'a[href*="/api/"]',
# BRACKET_SURGEON: disabled
#             ]

            for selector in name_selectors:
                element = listing.select_one(selector)
                if element:
                    name = element.get_text(strip=True)
                    if name and len(name) > 2:
                        return name

            # Fallback: look for any link that might be the API name
            links = listing.find_all("a")
            for link in links:
                text = link.get_text(strip=True)
                if text and "api" in text.lower() and len(text) < 100:
                    return text

            return None
        except Exception:
            return None

    def _extract_api_url(self, listing) -> Optional[str]:
        """Extract API URL from listing element"""
        try:
            # Try to find the main API link
            url_selectors = ["h2 a", "h3 a", ".title a", 'a[href*="/api/"]']

            for selector in url_selectors:
                element = listing.select_one(selector)
                if element and element.get("href"):
                    href = element.get("href")
                    # Convert relative URLs to absolute
                    if href.startswith("/"):
                        return f"https://www.programmableweb.com{href}"
                    elif href.startswith("http"):
                        return href

            return None
        except Exception:
            return None

    def _extract_api_description(self, listing) -> Optional[str]:
        """Extract API description from listing element"""
        try:
            # Try multiple selectors for description
            desc_selectors = [".description", ".summary", ".excerpt", "p", ".content"]

            for selector in desc_selectors:
                element = listing.select_one(selector)
                if element:
                    desc = element.get_text(strip=True)
                    if desc and len(desc) > 10:
                        return desc[:500]  # Limit description length

            return None
        except Exception:
            return None

    def _check_if_free_api(self, description: str, api_name: str) -> bool:
        """Check if API appears to be free based on description and name"""
        if not description:
            description = ""

        text_to_check = f"{description} {api_name}".lower()

        # Free indicators
        free_indicators = [
            "free",
            "no cost",
            "open source",
            "gratis",
            "complimentary",
            "no charge",
# BRACKET_SURGEON: disabled
#         ]
        paid_indicators = [
            "premium",
            "paid",
            "subscription",
            "billing",
            "pricing",
            "cost",
            "$",
# BRACKET_SURGEON: disabled
#         ]

        has_free = any(indicator in text_to_check for indicator in free_indicators)
        has_paid = any(indicator in text_to_check for indicator in paid_indicators)

        # If both indicators present, lean towards paid
        if has_free and not has_paid:
            return True

        return False

    async def _analyze_suggestions_with_llm(
        self, suggestions: List[APISuggestion], context: ResearchContext
    ) -> List[APISuggestion]:
        """Analyze API suggestions using LLM for scoring and validation"""
        analyzed_suggestions = []

        for suggestion in suggestions:
            try:
                # Create analysis prompt
                analysis_prompt = f""""""
Analyze this API opportunity:

API Name: {suggestion.api_name}
Description: {suggestion.description}
Capability: {suggestion.capability}
Source: {suggestion.discovery_source}
URL: {suggestion.api_url}

Current Context:
- Existing capabilities: {context.current_capabilities}
- Usage patterns: {context.usage_patterns}
- Budget constraints: ${context.budget_constraints}
- Priority areas: {context.priority_areas}

Provide analysis in JSON format:
{{
    "strategic_fit_score": 8.5,
      "market_demand_score": 7.0,
      "integration_complexity_score": 6.0,
      "cost_benefit_score": 9.0,
      "overall_priority_score": 7.6,
      "recommendation": "highly_recommended|recommended|neutral|not_recommended",
      "key_benefits": ["benefit1", "benefit2"],
      "potential_risks": ["risk1", "risk2"],
      "estimated_integration_hours": 12,
      "confidence_level": 0.85
# BRACKET_SURGEON: disabled
# }}
""""""

                system_prompt = """"""
You are an expert API strategist analyzing API opportunities for integration.
Focus on strategic value, technical feasibility, and business impact.
Provide objective, data - driven analysis with specific scores and recommendations.
""""""

                # Query LLM for analysis
                llm_response = await self._query_ollama(analysis_prompt, system_prompt)

                if llm_response:
                    try:
                        # Extract JSON from response
                        json_match = re.search(r"\\{.*\\}", llm_response, re.DOTALL)
                        if json_match:
                            analysis = json.loads(json_match.group())

                            # Update suggestion with LLM analysis
                            suggestion.priority_score = analysis.get("overall_priority_score", 5.0)
                            suggestion.confidence_score = analysis.get("confidence_level", 0.5)
                            suggestion.status = SuggestionStatus.ANALYZED
                            suggestion.analyzed_at = datetime.now(timezone.utc)
                            suggestion.llm_analysis = analysis

                            analyzed_suggestions.append(suggestion)
                        else:
                            logger.warning(
                                f"No JSON found in LLM analysis for {suggestion.api_name}"
# BRACKET_SURGEON: disabled
#                             )
                            suggestion.status = SuggestionStatus.DISCOVERED  # Keep as discovered
                            analyzed_suggestions.append(suggestion)

                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse LLM analysis JSON: {e}")
                        suggestion.status = SuggestionStatus.DISCOVERED
                        analyzed_suggestions.append(suggestion)
                else:
                    logger.warning(f"No LLM response for {suggestion.api_name}")
                    suggestion.status = SuggestionStatus.DISCOVERED
                    analyzed_suggestions.append(suggestion)

                # Rate limiting for LLM queries
                await asyncio.sleep(2)

            except Exception as e:
                logger.error(f"Error analyzing suggestion {suggestion.api_name}: {e}")
                suggestion.status = SuggestionStatus.DISCOVERED
                analyzed_suggestions.append(suggestion)

        return analyzed_suggestions

    async def _save_discovery_task(self, task: APIDiscoveryTask):
        """Save discovery task to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """"""
                INSERT OR REPLACE INTO api_discovery_tasks
                (id, task_type, target_capability, search_parameters, task_name,
                    capability_gap, search_keywords, target_domains, priority, status,
# BRACKET_SURGEON: disabled
#                      assigned_agent, progress_notes, apis_found, created_at, updated_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ""","""
                (
                    task.id,
                    task.task_type,
                    task.target_capability,
                    task.search_parameters,
                    task.task_name,
                    task.capability_gap,
                    task.search_keywords,
                    task.target_domains,
                    task.priority,
                    task.status,
                    task.assigned_agent,
                    task.progress_notes,
                    task.apis_found,
                    task.created_at,
                    task.updated_at,
                    task.completed_at,
# BRACKET_SURGEON: disabled
#                 ),
# BRACKET_SURGEON: disabled
#             )

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to save discovery task: {e}")

    async def _update_discovery_task(self, task: APIDiscoveryTask):
        """Update discovery task in database"""
        await self._save_discovery_task(task)  # Same as save with OR REPLACE

    async def _save_api_suggestion(self, suggestion: APISuggestion):
        """Save API suggestion to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """"""
                INSERT INTO api_suggestions
                (service_name, api_url, description, capability, discovery_source,
# BRACKET_SURGEON: disabled
#                     confidence_score, status, documentation_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ""","""
                (
                    suggestion.api_name,
                    suggestion.api_url,
                    suggestion.description,
                    suggestion.capability,
                    suggestion.discovery_source,
                    suggestion.confidence_score,
                    suggestion.status.value,
                    suggestion.documentation_url,
# BRACKET_SURGEON: disabled
#                 ),
# BRACKET_SURGEON: disabled
#             )

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to save API suggestion: {e}")

    def get_api_suggestions(
        self, status: Optional[SuggestionStatus] = None, limit: int = 50
    ) -> List[APISuggestion]:
        """Retrieve API suggestions from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            if status:
                cursor.execute(
                    """"""
                    SELECT id, service_name, capability, api_url, documentation_url, description,
                        discovery_source, confidence_score, status, created_at
                    FROM api_suggestions
                    WHERE status = ?
                    ORDER BY confidence_score DESC, created_at DESC
                    LIMIT ?
                ""","""
                    (status.value, limit),
# BRACKET_SURGEON: disabled
#                 )
            else:
                cursor.execute(
                    """"""
                    SELECT id, service_name, capability, api_url, documentation_url, description,
                        discovery_source, confidence_score, status, created_at
                    FROM api_suggestions
                    ORDER BY confidence_score DESC, created_at DESC
                    LIMIT ?
                ""","""
                    (limit,),
# BRACKET_SURGEON: disabled
#                 )

            rows = cursor.fetchall()
            conn.close()

            suggestions = []
            for row in rows:
                suggestion = APISuggestion(
                    id=row[0],
                    api_name=row[1],
                    capability=row[2],
                    api_url=row[3],
                    documentation_url=row[4],
                    description=row[5],
                    discovery_source=row[6],
                    confidence_score=row[7] or 0.0,
                    priority_score=0.0,  # Not stored in current schema
                    status=(
                        SuggestionStatus(row[8])
                        if row[8] in [s.value for s in SuggestionStatus]
                        else SuggestionStatus.DISCOVERED
# BRACKET_SURGEON: disabled
#                     ),
# BRACKET_SURGEON: disabled
#                 )
                suggestions.append(suggestion)

            return suggestions

        except Exception as e:
            logger.error(f"Failed to retrieve API suggestions: {e}")
            return []

    def get_discovery_tasks(
        self, status: Optional[str] = None, limit: int = 20
    ) -> List[APIDiscoveryTask]:
        """Retrieve discovery tasks from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            if status:
                cursor.execute(
                    """"""
                    SELECT * FROM api_discovery_tasks
                    WHERE status = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                ""","""
                    (status, limit),
# BRACKET_SURGEON: disabled
#                 )
            else:
                cursor.execute(
                    """"""
                    SELECT * FROM api_discovery_tasks
                    ORDER BY created_at DESC
                    LIMIT ?
                ""","""
                    (limit,),
# BRACKET_SURGEON: disabled
#                 )

            rows = cursor.fetchall()
            conn.close()

            tasks = []
            for row in rows:
                task = APIDiscoveryTask(
                    id=row[0],
                    task_type=row[1],
                    target_capability=row[2],
                    search_parameters=row[3],
                    task_name=row[4],
                    capability_gap=row[5],
                    search_keywords=row[6],
                    target_domains=row[7],
                    priority=row[8],
                    status=row[9],
                    assigned_agent=row[10],
                    progress_notes=row[11],
                    apis_found=row[12],
                    created_at=(
                        datetime.fromisoformat(row[13]) if row[13] else datetime.now(timezone.utc)
# BRACKET_SURGEON: disabled
#                     ),
                    updated_at=datetime.fromisoformat(row[14]) if row[14] else None,
                    completed_at=datetime.fromisoformat(row[15]) if row[15] else None,
# BRACKET_SURGEON: disabled
#                 )
                tasks.append(task)

            return tasks

        except Exception as e:
            logger.error(f"Failed to retrieve discovery tasks: {e}")
            return []

    async def run_automated_discovery(self, interval_hours: int = 24):
        """Run automated API discovery at regular intervals"""
        logger.info(f"Starting automated API discovery (interval: {interval_hours} hours)")

        while True:
            try:
                # Create default research context
                context = ResearchContext(
                    current_capabilities=["text - generation", "image - generation"],
                    usage_patterns={
                        "text - generation": 1000,
                        "image - generation": 500,
# BRACKET_SURGEON: disabled
#                     },
                    budget_constraints=1000.0,
                    priority_areas=[
                        "machine - learning",
                        "data - analysis",
                        "automation",
# BRACKET_SURGEON: disabled
#                     ],
# BRACKET_SURGEON: disabled
#                 )

                # Run discovery
                suggestions = await self.research_api_opportunities(context, max_results=20)

                logger.info(
                    f"Automated discovery completed. Found {len(suggestions)} new opportunities"
# BRACKET_SURGEON: disabled
#                 )

                # Wait for next interval
                await asyncio.sleep(interval_hours * 3600)

            except Exception as e:
                logger.error(f"Automated discovery error: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour before retry

    def get_analytics(self) -> Dict[str, Any]:
        """Get analytics and statistics about API discovery"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get suggestion statistics
            cursor.execute(
                """"""
                SELECT status, COUNT(*) as count
                FROM api_suggestions
                GROUP BY status
            """"""
# BRACKET_SURGEON: disabled
#             )
            suggestion_stats = {row[0]: row[1] for row in cursor.fetchall()}

            # Get discovery task statistics
            cursor.execute(
                """"""
                SELECT status, COUNT(*) as count
                FROM api_discovery_tasks
                GROUP BY status
            """"""
# BRACKET_SURGEON: disabled
#             )
            task_stats = {row[0]: row[1] for row in cursor.fetchall()}

            # Get top capabilities
            cursor.execute(
                """"""
                SELECT capability, COUNT(*) as count
                FROM api_suggestions
                GROUP BY capability
                ORDER BY count DESC
                LIMIT 10
            """"""
# BRACKET_SURGEON: disabled
#             )
            top_capabilities = {row[0]: row[1] for row in cursor.fetchall()}

            # Get discovery sources
            cursor.execute(
                """"""
                SELECT discovery_source, COUNT(*) as count
                FROM api_suggestions
                GROUP BY discovery_source
            """"""
# BRACKET_SURGEON: disabled
#             )
            source_stats = {row[0]: row[1] for row in cursor.fetchall()}

            conn.close()

            return {
                "suggestion_statistics": suggestion_stats,
                "task_statistics": task_stats,
                "top_capabilities": top_capabilities,
                "discovery_sources": source_stats,
                "total_suggestions": sum(suggestion_stats.values()),
                "total_tasks": sum(task_stats.values()),
# BRACKET_SURGEON: disabled
#             }

        except Exception as e:
            logger.error(f"Failed to get analytics: {e}")
            return {}

    def _generate_task_id(self) -> str:
        """Generate unique task ID"""
        timestamp = str(int(time.time()))
        hash_input = f"task_{timestamp}_{id(self)}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:12]

    def _generate_suggestion_id(self) -> str:
        """Generate unique suggestion ID"""
        timestamp = str(int(time.time()))
        hash_input = f"suggestion_{timestamp}_{id(self)}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:12]


# Example usage and testing


async def example_usage():
    """Example of how to use the API Opportunity Finder"""
    finder = APIOpportunityFinder()

    # Create research context
    context = ResearchContext(
        current_capabilities=["text - generation", "image - generation"],
        usage_patterns={"text - generation": 2000, "image - generation": 800},
        budget_constraints=2000.0,
        priority_areas=[
            "machine - learning",
            "data - analysis",
            "automation",
            "payment - processing",
# BRACKET_SURGEON: disabled
#         ],
# BRACKET_SURGEON: disabled
#     )

    # Research API opportunities
    print("Starting API opportunity research...")
    suggestions = await finder.research_api_opportunities(context, max_results=10)

    print(f"\\nFound {len(suggestions)} API opportunities:")
    for suggestion in suggestions[:5]:  # Show top 5
        print(f"\\n- {suggestion.api_name}")
        print(f"  Capability: {suggestion.capability}")
        print(f"  Priority Score: {suggestion.priority_score:.2f}")
        print(f"  Confidence: {suggestion.confidence_score:.2f}")
        print(f"  Source: {suggestion.discovery_source}")
        if suggestion.llm_analysis:
            print(f"  Recommendation: {suggestion.llm_analysis.get('recommendation', 'N/A')}")

    # Get analytics
    analytics = finder.get_analytics()
    print("\\nAnalytics:")
    print(f"Total suggestions: {analytics.get('total_suggestions', 0)}")
    print(f"Top capabilities: {analytics.get('top_capabilities', {})}")


if __name__ == "__main__":
    # Run example
    asyncio.run(example_usage())