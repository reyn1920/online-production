#!/usr / bin / env python3
""""""
API Opportunity Finder - Research Agent for API Discovery

This module implements an intelligent research agent that:
- Discovers new APIs based on current capabilities and gaps
- Uses LLM to analyze API documentation and suggest integrations
- Tracks discovery tasks and maintains a suggestion database
- Provides scoring and prioritization for new API opportunities
""""""

import asyncio
import json
import logging
import re
import sqlite3
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import aiohttp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DiscoveryStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class SuggestionStatus(Enum):
    NEW = "new"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    REJECTED = "rejected"
    INTEGRATED = "integrated"


@dataclass
class APIDiscoveryTask:
    """Represents a task for discovering APIs in a specific domain"""

    id: Optional[int]
    task_name: str
    capability_gap: str
    search_keywords: List[str]
    target_domains: List[str]
    priority: int
    status: str
    assigned_agent: str
    progress_notes: Optional[str]
    apis_found: int
    created_at: Optional[str]
    completed_at: Optional[str]


@dataclass
class APISuggestion:
    """Represents a discovered API suggestion"""

    id: Optional[int]
    discovery_task_id: int
    api_name: str
    api_url: str
    capability: str
    description: str
    documentation_url: Optional[str]
    pricing_model: Optional[str]
    estimated_cost: Optional[float]
    integration_complexity: int  # 1 - 10 scale
    potential_value: int  # 1 - 10 scale
    confidence_score: float  # 0 - 1 scale
    status: str
    review_notes: Optional[str]
    discovered_at: Optional[str]


@dataclass
class ResearchContext:
    """Context for research agent operations"""

    current_capabilities: List[str]
    capability_gaps: List[str]
    usage_patterns: Dict[str, int]
    budget_constraints: Optional[float]
    preferred_pricing_models: List[str]
    integration_preferences: Dict[str, Any]


class APIOpportunityFinder:
    """Research Agent for discovering and evaluating new API opportunities"""

    def __init__(
        self,
        db_path: str = "right_perspective.db",
        ollama_url: str = "http://localhost:11434",
# BRACKET_SURGEON: disabled
#     ):
        self.db_path = db_path
        self.ollama_url = ollama_url
        self.session = None
        self._init_database()

    def _init_database(self):
        """Initialize database connection and ensure tables exist"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            # Add indexes for better performance
            conn.execute(
                """"""
                CREATE INDEX IF NOT EXISTS idx_api_suggestions_status
                ON api_suggestions(status, confidence_score DESC)
            """"""
# BRACKET_SURGEON: disabled
#             )
            conn.execute(
                """"""
                CREATE INDEX IF NOT EXISTS idx_api_discovery_tasks_status
                ON api_discovery_tasks(status, priority DESC)
            """"""
# BRACKET_SURGEON: disabled
#             )
            conn.commit()

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    def get_research_context(self) -> ResearchContext:
        """Analyze current API registry to understand capabilities and gaps"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Get current capabilities
            cursor = conn.execute(
                """"""
                SELECT DISTINCT capability, COUNT(*) as api_count,
                    AVG(success_rate) as avg_success_rate,
                           SUM(daily_usage_count) as total_usage
                FROM api_registry
                WHERE is_active = 1
                GROUP BY capability
                ORDER BY total_usage DESC
            """"""
# BRACKET_SURGEON: disabled
#             )

            capabilities_data = cursor.fetchall()
            current_capabilities = [row["capability"] for row in capabilities_data]
            usage_patterns = {row["capability"]: row["total_usage"] for row in capabilities_data}

            # Identify potential gaps based on low API count or poor performance
            capability_gaps = []
            for row in capabilities_data:
                if row["api_count"] < 2:  # Less than 2 APIs for redundancy
                    capability_gaps.append(f"Limited redundancy for {row['capability']}")
                if row["avg_success_rate"] < 0.9:  # Poor success rate
                    capability_gaps.append(f"Poor reliability for {row['capability']}")

            return ResearchContext(
                current_capabilities=current_capabilities,
                capability_gaps=capability_gaps,
                usage_patterns=usage_patterns,
                budget_constraints=None,  # Could be configured
                preferred_pricing_models=["freemium", "pay - per - use"],
                integration_preferences={"auth_type": "api_key", "format": "json"},
# BRACKET_SURGEON: disabled
#             )

    async def query_ollama(self, prompt: str, model: str = "llama2") -> Optional[str]:
        """Query Ollama LLM for research assistance"""
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.7, "top_p": 0.9},
# BRACKET_SURGEON: disabled
#             }

            async with self.session.post(
                f"{self.ollama_url}/api / generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60),
# BRACKET_SURGEON: disabled
#             ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("response", "").strip()
                else:
                    logger.error(f"Ollama request failed: {response.status}")
                    return None

        except Exception as e:
            logger.error(f"Error querying Ollama: {e}")
            return None

    async def research_api_opportunities(
        self, context: ResearchContext, focus_area: str = None
    ) -> List[Dict[str, Any]]:
        """Use LLM to research and suggest API opportunities"""

        # Construct research prompt
        prompt = f""""""
You are an expert API researcher. Analyze the following context \
#     and suggest new API opportunities.

Current Capabilities: {', '.join(context.current_capabilities)}
Capability Gaps: {', '.join(context.capability_gaps)}
Usage Patterns: {json.dumps(context.usage_patterns, indent = 2)}

{f'Focus Area: {focus_area}' if focus_area else ''}

Please suggest 5 - 10 specific APIs that would:
1. Fill capability gaps
2. Provide redundancy for high - usage capabilities
3. Offer better performance or cost efficiency
4. Enable new capabilities that complement existing ones

For each API suggestion, provide:
- API Name
- Primary Capability
- Brief Description
- Estimated Integration Complexity (1 - 10)
- Potential Business Value (1 - 10)
- Confidence in Recommendation (1 - 10)

Format your response as a JSON array of objects with these fields:
[{{
    "api_name": "Example API",
      "capability": "text - generation",
      "description": "High - quality text generation with...",
      "integration_complexity": 5,
      "potential_value": 8,
      "confidence_score": 7,
      "reasoning": "This API would help because..."
# BRACKET_SURGEON: disabled
# }}]
""""""

        response = await self.query_ollama(prompt)
        if not response:
            return []

        try:
            # Extract JSON from response
            json_match = re.search(r"\\[.*\\]", response, re.DOTALL)
            if json_match:
                suggestions_data = json.loads(json_match.group())
                return suggestions_data
            else:
                logger.warning("No JSON found in LLM response")
                return []

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            return []

    def create_discovery_task(
        self,
        task_name: str,
        capability_gap: str,
        search_keywords: List[str],
        target_domains: List[str] = None,
        priority: int = 5,
# BRACKET_SURGEON: disabled
#     ) -> int:
        """Create a new API discovery task"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """"""
                INSERT INTO api_discovery_tasks
                (task_name,
    capability_gap,
    search_keywords,
    target_domains,
    priority,
    status,
# BRACKET_SURGEON: disabled
#     assigned_agent)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ""","""
                (
                    task_name,
                    capability_gap,
                    json.dumps(search_keywords),
                    json.dumps(target_domains or []),
                    priority,
                    DiscoveryStatus.PENDING.value,
                    "research_agent_v1",
# BRACKET_SURGEON: disabled
#                 ),
# BRACKET_SURGEON: disabled
#             )
            conn.commit()
            return cursor.lastrowid

    def update_discovery_task(
        self,
        task_id: int,
        status: DiscoveryStatus,
        progress_notes: str = None,
        apis_found: int = None,
# BRACKET_SURGEON: disabled
#     ):
        """Update discovery task status and progress"""
        with sqlite3.connect(self.db_path) as conn:
            updates = ["status = ?", "updated_at = ?", "progress_notes = ?"]
            values = [
                status.value,
                datetime.now(timezone.utc).isoformat(),
                progress_notes,
# BRACKET_SURGEON: disabled
#             ]

            if apis_found is not None:
                updates.append("apis_found = ?")
                values.append(apis_found)

            if status == DiscoveryStatus.COMPLETED:
                updates.append("completed_at = ?")
                values.append(datetime.now(timezone.utc).isoformat())

            values.append(task_id)

            conn.execute(
                f""""""
                UPDATE api_discovery_tasks
                SET {', '.join(updates)}
                WHERE id = ?
            ""","""
                values,
# BRACKET_SURGEON: disabled
#             )
            conn.commit()

    def save_api_suggestion(self, suggestion: APISuggestion) -> int:
        """Save a discovered API suggestion to the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """"""
                INSERT INTO api_suggestions
                (discovery_task_id, api_name, api_url, capability, description,
                    documentation_url, pricing_model, estimated_cost, integration_complexity,
# BRACKET_SURGEON: disabled
#                      potential_value, confidence_score, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ""","""
                (
                    suggestion.discovery_task_id,
                    suggestion.api_name,
                    suggestion.api_url,
                    suggestion.capability,
                    suggestion.description,
                    suggestion.documentation_url,
                    suggestion.pricing_model,
                    suggestion.estimated_cost,
                    suggestion.integration_complexity,
                    suggestion.potential_value,
                    suggestion.confidence_score,
                    suggestion.status,
# BRACKET_SURGEON: disabled
#                 ),
# BRACKET_SURGEON: disabled
#             )
            conn.commit()
            return cursor.lastrowid

    async def execute_discovery_task(self, task_id: int) -> List[APISuggestion]:
        """Execute a specific discovery task"""
        # Get task details
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM api_discovery_tasks WHERE id = ?", (task_id,))
            task_row = cursor.fetchone()

            if not task_row:
                raise ValueError(f"Discovery task {task_id} not found")

            task = APIDiscoveryTask(**dict(task_row))

        # Update task status to in_progress
        self.update_discovery_task(
            task_id, DiscoveryStatus.IN_PROGRESS, "Starting API research with LLM"
# BRACKET_SURGEON: disabled
#         )

        try:
            # Get research context
            context = self.get_research_context()

            # Use LLM to research opportunities
            focus_area = (
                f"{task.capability_gap} - Keywords: {', '.join(json.loads(task.search_keywords))}"
# BRACKET_SURGEON: disabled
#             )
            suggestions_data = await self.research_api_opportunities(context, focus_area)

            suggestions = []
            for suggestion_data in suggestions_data:
                # Create APISuggestion object
                suggestion = APISuggestion(
                    id=None,
                    discovery_task_id=task_id,
                    api_name=suggestion_data.get("api_name", "Unknown API"),
                    api_url=suggestion_data.get("api_url", ""),
                    capability=suggestion_data.get("capability", task.capability_gap),
                    description=suggestion_data.get("description", ""),
                    documentation_url=suggestion_data.get("documentation_url"),
                    pricing_model=suggestion_data.get("pricing_model"),
                    estimated_cost=suggestion_data.get("estimated_cost"),
                    integration_complexity=suggestion_data.get("integration_complexity", 5),
                    potential_value=suggestion_data.get("potential_value", 5),
                    confidence_score=suggestion_data.get("confidence_score", 5)
                    / 10.0,  # Convert to 0 - 1
                    status=SuggestionStatus.NEW.value,
                    review_notes=suggestion_data.get("reasoning"),
                    discovered_at=datetime.now(timezone.utc).isoformat(),
# BRACKET_SURGEON: disabled
#                 )

                # Save to database
                suggestion.id = self.save_api_suggestion(suggestion)
                suggestions.append(suggestion)

            # Update task as completed
            self.update_discovery_task(
                task_id,
                DiscoveryStatus.COMPLETED,
                f"Discovered {len(suggestions)} API opportunities",
                len(suggestions),
# BRACKET_SURGEON: disabled
#             )

            logger.info(f"Discovery task {task_id} completed with {len(suggestions)} suggestions")
            return suggestions

        except Exception as e:
            # Update task as failed
            self.update_discovery_task(task_id, DiscoveryStatus.FAILED, f"Task failed: {str(e)}")
            logger.error(f"Discovery task {task_id} failed: {e}")
            raise

    def get_top_suggestions(self, limit: int = 10, capability: str = None) -> List[Dict[str, Any]]:
        """Get top API suggestions based on confidence score and potential value"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            query = """"""
                SELECT s.*, t.task_name, t.capability_gap
                FROM api_suggestions s
                JOIN api_discovery_tasks t ON s.discovery_task_id = t.id
                WHERE s.status IN ('new', 'reviewed')
            """"""
            params = []

            if capability:
                query += " AND s.capability = ?"
                params.append(capability)

            query += """"""
                ORDER BY (s.confidence_score * s.potential_value) DESC,
    s.discovered_at DESC
                LIMIT ?
            """"""
            params.append(limit)

            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_suggestions_by_status(self, status: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get API suggestions filtered by status"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            query = """"""
                SELECT *
                    FROM api_suggestions
                WHERE status = ?
                ORDER BY discovered_at DESC
                LIMIT ?
            """"""

            cursor = conn.execute(query, [status, limit])
            return [dict(row) for row in cursor.fetchall()]

    def update_suggestion_status(
        self, suggestion_id: int, status: SuggestionStatus, review_notes: str = None
# BRACKET_SURGEON: disabled
#     ):
        """Update the status of an API suggestion"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """"""
                UPDATE api_suggestions
                SET status = ?, review_notes = ?, updated_at = ?
                WHERE id = ?
            ""","""
                (
                    status.value,
                    review_notes,
                    datetime.now(timezone.utc).isoformat(),
                    suggestion_id,
# BRACKET_SURGEON: disabled
#                 ),
# BRACKET_SURGEON: disabled
#             )
            conn.commit()

    async def run_automated_discovery(self, max_tasks: int = 3) -> Dict[str, Any]:
        """Run automated discovery for pending tasks"""
        # Get pending tasks
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """"""
                SELECT * FROM api_discovery_tasks
                WHERE status = 'pending'
                ORDER BY priority DESC, created_at ASC
                LIMIT ?
            ""","""
                (max_tasks,),
# BRACKET_SURGEON: disabled
#             )

            pending_tasks = [dict(row) for row in cursor.fetchall()]

        results = {"tasks_processed": 0, "suggestions_generated": 0, "errors": []}

        for task_data in pending_tasks:
            try:
                suggestions = await self.execute_discovery_task(task_data["id"])
                results["tasks_processed"] += 1
                results["suggestions_generated"] += len(suggestions)

                logger.info(f"Processed task {task_data['id']}: {len(suggestions)} suggestions")

            except Exception as e:
                error_msg = f"Task {task_data['id']} failed: {str(e)}"
                results["errors"].append(error_msg)
                logger.error(error_msg)

        return results

    def get_discovery_analytics(self) -> Dict[str, Any]:
        """Get analytics on discovery performance"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Task statistics
            cursor = conn.execute(
                """"""
                SELECT
                    status,
                        COUNT(*) as count,
                        AVG(apis_found) as avg_apis_found
                FROM api_discovery_tasks
                GROUP BY status
            """"""
# BRACKET_SURGEON: disabled
#             )
            task_stats = {row["status"]: dict(row) for row in cursor.fetchall()}

            # Suggestion statistics
            cursor = conn.execute(
                """"""
                SELECT
                    capability,
                        status,
                        COUNT(*) as count,
                        AVG(confidence_score) as avg_confidence,
                        AVG(potential_value) as avg_potential_value
                FROM api_suggestions
                GROUP BY capability, status
            """"""
# BRACKET_SURGEON: disabled
#             )
            suggestion_stats = [dict(row) for row in cursor.fetchall()]

            # Top capabilities by suggestion count
            cursor = conn.execute(
                """"""
                SELECT
                    capability,
                        COUNT(*) as suggestion_count,
                        AVG(confidence_score) as avg_confidence
                FROM api_suggestions
                GROUP BY capability
                ORDER BY suggestion_count DESC
                LIMIT 10
            """"""
# BRACKET_SURGEON: disabled
#             )
            top_capabilities = [dict(row) for row in cursor.fetchall()]

            return {
                "task_statistics": task_stats,
                "suggestion_statistics": suggestion_stats,
                "top_capabilities": top_capabilities,
# BRACKET_SURGEON: disabled
#             }


# Example usage


async def example_usage():
    """Example of how to use the API Opportunity Finder"""
    async with APIOpportunityFinder() as finder:
        # Create a discovery task
        task_id = finder.create_discovery_task(
            task_name="Find better text generation APIs",
            capability_gap="text - generation reliability",
            search_keywords=["text generation", "GPT", "language model", "AI writing"],
            target_domains=["openai.com", "anthropic.com", "cohere.ai"],
            priority=8,
# BRACKET_SURGEON: disabled
#         )

        print(f"Created discovery task: {task_id}")

        # Execute the task
        suggestions = await finder.execute_discovery_task(task_id)

        print(f"\\nDiscovered {len(suggestions)} API opportunities:")
        for suggestion in suggestions:
            print(f"- {suggestion.api_name}: {suggestion.description}")
            print(
                f"  Confidence: {suggestion.confidence_score:.2f}, Value: {suggestion.potential_value}"
# BRACKET_SURGEON: disabled
#             )

        # Get top suggestions
        top_suggestions = finder.get_top_suggestions(limit=5)
        print(f"\\nTop {len(top_suggestions)} suggestions:")
        for suggestion in top_suggestions:
            print(f"- {suggestion['api_name']} ({suggestion['capability']})")
            print(f"  Score: {suggestion['confidence_score'] * suggestion['potential_value']:.2f}")

        # Get analytics
        analytics = finder.get_discovery_analytics()
        print("\\nDiscovery Analytics:")
        print(json.dumps(analytics, indent=2, default=str))


if __name__ == "__main__":
    # Run example
    asyncio.run(example_usage())