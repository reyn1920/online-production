#!/usr/bin/env python3
"""
API Opportunity Finder - Research Agent for Automated API Discovery

This module acts as an intelligent research agent that discovers new API opportunities
by analyzing public repositories, documentation, and market trends. It integrates with
the existing Ollama LLM system for advanced analysis and scoring.

Features:
- Automated API discovery from GitHub, GitLab, and other sources
- LLM-powered API documentation analysis and capability assessment
- Intelligent scoring and prioritization of API opportunities
- Integration with existing Ollama infrastructure
- Comprehensive logging and analytics
"""

import asyncio
import aiohttp
import json
import logging
import sqlite3
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import requests
from urllib.parse import urlparse, urljoin
import re
import hashlib

# Import existing Ollama integration
from backend.integrations.ollama_integration import OllamaIntegration, PromptTemplate, QueryRequest

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
    task_id: str
    search_query: str
    discovery_source: str
    status: DiscoveryStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    results_count: int = 0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None

@dataclass
class APISuggestion:
    """Represents a discovered API suggestion"""
    suggestion_id: str
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
    
    def __init__(self, db_path: str = "right_perspective.db", 
                 ollama_base_url: str = "http://localhost:11434",
                 ollama_model: str = "llama2:7b"):
        self.db_path = db_path
        self.ollama_base_url = ollama_base_url
        self.ollama_model = ollama_model
        self._ollama_integration = None
        self._github_token = None  # Set via environment or config
        self._discovery_sources = {
            'github': 'https://api.github.com',
            'gitlab': 'https://gitlab.com/api/v4',
            'rapidapi': 'https://rapidapi.com/search',
            'programmableweb': 'https://www.programmableweb.com/apis/directory'
        }
        
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
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_discovery_tasks (
                    task_id TEXT PRIMARY KEY,
                    search_query TEXT NOT NULL,
                    discovery_source TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    results_count INTEGER DEFAULT 0,
                    error_message TEXT,
                    metadata TEXT
                )
            """)
            
            # Ensure api_suggestions table exists
            cursor.execute("""
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
                )
            """)
            
            conn.commit()
            conn.close()
            logger.info("API discovery database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize API discovery database: {e}")
    
    def _init_ollama_integration(self):
        """Initialize Ollama integration for LLM analysis"""
        try:
            self._ollama_integration = OllamaIntegration({
                'ollama_url': self.ollama_base_url,
                'default_model': self.ollama_model,
                'enable_caching': True,
                'performance_monitoring': True,
                'max_concurrent_requests': 3
            })
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
            context = {
                'task_type': 'api_research',
                'system_prompt': system_prompt
            }
            
            # Use the existing integration's query method
            response = await self._ollama_integration.query_llm(
                prompt=prompt,
                model_name=self.ollama_model,
                template=PromptTemplate.RESEARCH_SYNTHESIS,
                context=context,
                priority=7
            )
            
            if response and response.response_text:
                return response.response_text.strip()
            else:
                logger.error("Ollama integration returned empty response")
                return None
        
        except Exception as e:
            logger.error(f"Error querying Ollama via integration: {e}")
            return None
    
    async def research_api_opportunities(self, context: ResearchContext, 
                                       max_results: int = 50) -> List[APISuggestion]:
        """Research and discover new API opportunities"""
        logger.info(f"Starting API opportunity research with context: {context.priority_areas}")
        
        suggestions = []
        
        # Create discovery task
        task_id = self._generate_task_id()
        task = APIDiscoveryTask(
            task_id=task_id,
            search_query=f"APIs for {', '.join(context.priority_areas)}",
            discovery_source="multi-source",
            status=DiscoveryStatus.PENDING,
            created_at=datetime.now(timezone.utc),
            metadata={'context': context.__dict__}
        )
        
        await self._save_discovery_task(task)
        
        try:
            # Update task status
            task.status = DiscoveryStatus.IN_PROGRESS
            task.started_at = datetime.now(timezone.utc)
            await self._update_discovery_task(task)
            
            # Search GitHub for API repositories
            github_suggestions = await self._search_github_apis(context, max_results // 2)
            suggestions.extend(github_suggestions)
            
            # Search RapidAPI marketplace
            rapidapi_suggestions = await self._search_rapidapi(context, max_results // 4)
            suggestions.extend(rapidapi_suggestions)
            
            # Search ProgrammableWeb directory
            programmableweb_suggestions = await self._search_programmableweb(context, max_results // 4)
            suggestions.extend(programmableweb_suggestions)
            
            # Analyze and score suggestions using LLM
            analyzed_suggestions = await self._analyze_suggestions_with_llm(suggestions, context)
            
            # Save suggestions to database
            for suggestion in analyzed_suggestions:
                await self._save_api_suggestion(suggestion)
            
            # Update task completion
            task.status = DiscoveryStatus.COMPLETED
            task.completed_at = datetime.now(timezone.utc)
            task.results_count = len(analyzed_suggestions)
            await self._update_discovery_task(task)
            
            logger.info(f"API research completed. Found {len(analyzed_suggestions)} opportunities")
            return analyzed_suggestions
            
        except Exception as e:
            logger.error(f"API research failed: {e}")
            task.status = DiscoveryStatus.FAILED
            task.error_message = str(e)
            await self._update_discovery_task(task)
            return []
    
    async def _search_github_apis(self, context: ResearchContext, max_results: int) -> List[APISuggestion]:
        """Search GitHub for API repositories"""
        suggestions = []
        
        try:
            for priority_area in context.priority_areas[:3]:  # Limit to top 3 areas
                query = f"{priority_area} API language:Python language:JavaScript language:TypeScript"
                
                async with aiohttp.ClientSession() as session:
                    headers = {}
                    if self._github_token:
                        headers['Authorization'] = f'token {self._github_token}'
                    
                    url = f"https://api.github.com/search/repositories"
                    params = {
                        'q': query,
                        'sort': 'stars',
                        'order': 'desc',
                        'per_page': min(max_results // len(context.priority_areas), 20)
                    }
                    
                    async with session.get(url, headers=headers, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            for repo in data.get('items', []):
                                suggestion = APISuggestion(
                                    suggestion_id=self._generate_suggestion_id(),
                                    api_name=repo['name'],
                                    api_url=repo.get('homepage', repo['html_url']),
                                    description=repo.get('description', ''),
                                    capability=priority_area,
                                    discovery_source='github',
                                    confidence_score=min(repo['stargazers_count'] / 1000, 1.0),
                                    priority_score=0.0,  # Will be calculated by LLM
                                    status=SuggestionStatus.DISCOVERED,
                                    github_url=repo['html_url'],
                                    created_at=datetime.now(timezone.utc)
                                )
                                suggestions.append(suggestion)
                        else:
                            logger.warning(f"GitHub API search failed: {response.status}")
                
                # Rate limiting
                await asyncio.sleep(1)
        
        except Exception as e:
            logger.error(f"GitHub API search error: {e}")
        
        return suggestions
    
    async def _search_rapidapi(self, context: ResearchContext, max_results: int) -> List[APISuggestion]:
        """Search RapidAPI marketplace (simplified implementation)"""
        suggestions = []
        
        # Note: This would require RapidAPI marketplace API access
        # For now, return empty list - can be implemented with proper API access
        logger.info("RapidAPI search not implemented - requires marketplace API access")
        
        return suggestions
    
    async def _search_programmableweb(self, context: ResearchContext, max_results: int) -> List[APISuggestion]:
        """Search ProgrammableWeb directory (simplified implementation)"""
        suggestions = []
        
        # Note: This would require web scraping or API access
        # For now, return empty list - can be implemented with proper scraping
        logger.info("ProgrammableWeb search not implemented - requires web scraping")
        
        return suggestions
    
    async def _analyze_suggestions_with_llm(self, suggestions: List[APISuggestion], 
                                          context: ResearchContext) -> List[APISuggestion]:
        """Analyze API suggestions using LLM for scoring and validation"""
        analyzed_suggestions = []
        
        for suggestion in suggestions:
            try:
                # Create analysis prompt
                analysis_prompt = f"""
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
}}
"""
                
                system_prompt = """
You are an expert API strategist analyzing API opportunities for integration.
Focus on strategic value, technical feasibility, and business impact.
Provide objective, data-driven analysis with specific scores and recommendations.
"""
                
                # Query LLM for analysis
                llm_response = await self._query_ollama(analysis_prompt, system_prompt)
                
                if llm_response:
                    try:
                        # Extract JSON from response
                        json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
                        if json_match:
                            analysis = json.loads(json_match.group())
                            
                            # Update suggestion with LLM analysis
                            suggestion.priority_score = analysis.get('overall_priority_score', 5.0)
                            suggestion.confidence_score = analysis.get('confidence_level', 0.5)
                            suggestion.status = SuggestionStatus.ANALYZED
                            suggestion.analyzed_at = datetime.now(timezone.utc)
                            suggestion.llm_analysis = analysis
                            
                            analyzed_suggestions.append(suggestion)
                        else:
                            logger.warning(f"No JSON found in LLM analysis for {suggestion.api_name}")
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
            
            cursor.execute("""
                INSERT OR REPLACE INTO api_discovery_tasks 
                (task_id, search_query, discovery_source, status, created_at, 
                 started_at, completed_at, results_count, error_message, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task.task_id, task.search_query, task.discovery_source, task.status.value,
                task.created_at, task.started_at, task.completed_at, task.results_count,
                task.error_message, json.dumps(task.metadata) if task.metadata else None
            ))
            
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
            
            cursor.execute("""
                INSERT OR REPLACE INTO api_suggestions 
                (suggestion_id, api_name, api_url, description, capability, discovery_source,
                 confidence_score, priority_score, status, documentation_url, github_url,
                 pricing_model, rate_limits, authentication_type, created_at, analyzed_at, llm_analysis)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                suggestion.suggestion_id, suggestion.api_name, suggestion.api_url,
                suggestion.description, suggestion.capability, suggestion.discovery_source,
                suggestion.confidence_score, suggestion.priority_score, suggestion.status.value,
                suggestion.documentation_url, suggestion.github_url, suggestion.pricing_model,
                json.dumps(suggestion.rate_limits) if suggestion.rate_limits else None,
                suggestion.authentication_type, suggestion.created_at, suggestion.analyzed_at,
                json.dumps(suggestion.llm_analysis) if suggestion.llm_analysis else None
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to save API suggestion: {e}")
    
    def get_api_suggestions(self, status: Optional[SuggestionStatus] = None, 
                           limit: int = 50) -> List[APISuggestion]:
        """Retrieve API suggestions from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if status:
                cursor.execute("""
                    SELECT * FROM api_suggestions 
                    WHERE status = ? 
                    ORDER BY priority_score DESC, created_at DESC 
                    LIMIT ?
                """, (status.value, limit))
            else:
                cursor.execute("""
                    SELECT * FROM api_suggestions 
                    ORDER BY priority_score DESC, created_at DESC 
                    LIMIT ?
                """, (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            
            suggestions = []
            for row in rows:
                suggestion = APISuggestion(
                    suggestion_id=row[0],
                    api_name=row[1],
                    api_url=row[2],
                    description=row[3],
                    capability=row[4],
                    discovery_source=row[5],
                    confidence_score=row[6],
                    priority_score=row[7],
                    status=SuggestionStatus(row[8]),
                    documentation_url=row[9],
                    github_url=row[10],
                    pricing_model=row[11],
                    rate_limits=json.loads(row[12]) if row[12] else None,
                    authentication_type=row[13],
                    created_at=datetime.fromisoformat(row[14]) if row[14] else None,
                    analyzed_at=datetime.fromisoformat(row[15]) if row[15] else None,
                    llm_analysis=json.loads(row[16]) if row[16] else None
                )
                suggestions.append(suggestion)
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Failed to retrieve API suggestions: {e}")
            return []
    
    def get_discovery_tasks(self, status: Optional[DiscoveryStatus] = None, 
                           limit: int = 20) -> List[APIDiscoveryTask]:
        """Retrieve discovery tasks from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if status:
                cursor.execute("""
                    SELECT * FROM api_discovery_tasks 
                    WHERE status = ? 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (status.value, limit))
            else:
                cursor.execute("""
                    SELECT * FROM api_discovery_tasks 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            
            tasks = []
            for row in rows:
                task = APIDiscoveryTask(
                    task_id=row[0],
                    search_query=row[1],
                    discovery_source=row[2],
                    status=DiscoveryStatus(row[3]),
                    created_at=datetime.fromisoformat(row[4]) if row[4] else datetime.now(timezone.utc),
                    started_at=datetime.fromisoformat(row[5]) if row[5] else None,
                    completed_at=datetime.fromisoformat(row[6]) if row[6] else None,
                    results_count=row[7],
                    error_message=row[8],
                    metadata=json.loads(row[9]) if row[9] else None
                )
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
                    current_capabilities=["text-generation", "image-generation"],
                    usage_patterns={"text-generation": 1000, "image-generation": 500},
                    budget_constraints=1000.0,
                    priority_areas=["machine-learning", "data-analysis", "automation"]
                )
                
                # Run discovery
                suggestions = await self.research_api_opportunities(context, max_results=20)
                
                logger.info(f"Automated discovery completed. Found {len(suggestions)} new opportunities")
                
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
            cursor.execute("""
                SELECT status, COUNT(*) as count 
                FROM api_suggestions 
                GROUP BY status
            """)
            suggestion_stats = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Get discovery task statistics
            cursor.execute("""
                SELECT status, COUNT(*) as count 
                FROM api_discovery_tasks 
                GROUP BY status
            """)
            task_stats = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Get top capabilities
            cursor.execute("""
                SELECT capability, COUNT(*) as count 
                FROM api_suggestions 
                GROUP BY capability 
                ORDER BY count DESC 
                LIMIT 10
            """)
            top_capabilities = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Get discovery sources
            cursor.execute("""
                SELECT discovery_source, COUNT(*) as count 
                FROM api_suggestions 
                GROUP BY discovery_source
            """)
            source_stats = {row[0]: row[1] for row in cursor.fetchall()}
            
            conn.close()
            
            return {
                "suggestion_statistics": suggestion_stats,
                "task_statistics": task_stats,
                "top_capabilities": top_capabilities,
                "discovery_sources": source_stats,
                "total_suggestions": sum(suggestion_stats.values()),
                "total_tasks": sum(task_stats.values())
            }
            
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
        current_capabilities=["text-generation", "image-generation"],
        usage_patterns={"text-generation": 2000, "image-generation": 800},
        budget_constraints=2000.0,
        priority_areas=["machine-learning", "data-analysis", "automation", "payment-processing"]
    )
    
    # Research API opportunities
    print("Starting API opportunity research...")
    suggestions = await finder.research_api_opportunities(context, max_results=10)
    
    print(f"\nFound {len(suggestions)} API opportunities:")
    for suggestion in suggestions[:5]:  # Show top 5
        print(f"\n- {suggestion.api_name}")
        print(f"  Capability: {suggestion.capability}")
        print(f"  Priority Score: {suggestion.priority_score:.2f}")
        print(f"  Confidence: {suggestion.confidence_score:.2f}")
        print(f"  Source: {suggestion.discovery_source}")
        if suggestion.llm_analysis:
            print(f"  Recommendation: {suggestion.llm_analysis.get('recommendation', 'N/A')}")
    
    # Get analytics
    analytics = finder.get_analytics()
    print(f"\nAnalytics:")
    print(f"Total suggestions: {analytics.get('total_suggestions', 0)}")
    print(f"Top capabilities: {analytics.get('top_capabilities', {})}")

if __name__ == "__main__":
    # Run example
    asyncio.run(example_usage())