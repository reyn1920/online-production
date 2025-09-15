#!/usr/bin/env python3
""""""
TRAE.AI Planner Agent - The Strategist

The system's brain that uses closed - loop feedback from performance data'
to autonomously refine its own strategies. Implements the "2% Blueprint"
for resilient, self - improving strategic oversight.
""""""

import json
import logging
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .base_agents import BaseAgent


@dataclass
class StrategyMetrics:
    """Performance metrics for strategy evaluation"""

    strategy_id: str
    content_performance: float  # 0 - 1 score
    marketing_roi: float
    audience_engagement: float
    technical_health: float
    timestamp: datetime

    def overall_score(self) -> float:
        """Calculate weighted overall performance score"""
        weights = {
            "content": 0.3,
            "marketing": 0.3,
            "engagement": 0.25,
            "technical": 0.15,
# BRACKET_SURGEON: disabled
#         }
        return (
            self.content_performance * weights["content"]
            + self.marketing_roi * weights["marketing"]
            + self.audience_engagement * weights["engagement"]
            + self.technical_health * weights["technical"]
# BRACKET_SURGEON: disabled
#         )


@dataclass
class StrategyPlan:
    """Strategic plan with autonomous refinement capabilities"""

    strategy_id: str
    name: str
    objectives: List[str]
    tactics: Dict[str, Any]
    success_metrics: Dict[str, float]
    confidence_score: float
    created_at: datetime
    last_refined: datetime
    refinement_count: int = 0


class PlannerAgent(BaseAgent):
    """The Strategist - Autonomous strategic planning and refinement"""

    def __init__(self, db_path: str = "data/right_perspective.db"):
        super().__init__("PlannerAgent")
        self.db_path = db_path
        self.logger = logging.getLogger(self.__class__.__name__)
        self.initialize_database()

        # Strategic parameters
        self.min_confidence_threshold = 0.7
        self.refinement_trigger_threshold = 0.6
        self.learning_rate = 0.1

    def initialize_database(self):
        """Initialize strategy tracking database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """"""
                CREATE TABLE IF NOT EXISTS strategy_plans (
                    strategy_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        objectives TEXT NOT NULL,
                        tactics TEXT NOT NULL,
                        success_metrics TEXT NOT NULL,
                        confidence_score REAL NOT NULL,
                        created_at TIMESTAMP NOT NULL,
                        last_refined TIMESTAMP NOT NULL,
                        refinement_count INTEGER DEFAULT 0
# BRACKET_SURGEON: disabled
#                 )
            """"""
# BRACKET_SURGEON: disabled
#             )

            conn.execute(
                """"""
                CREATE TABLE IF NOT EXISTS strategy_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        strategy_id TEXT NOT NULL,
                        content_performance REAL NOT NULL,
                        marketing_roi REAL NOT NULL,
                        audience_engagement REAL NOT NULL,
                        technical_health REAL NOT NULL,
                        overall_score REAL NOT NULL,
                        timestamp TIMESTAMP NOT NULL,
                        FOREIGN KEY (strategy_id) REFERENCES strategy_plans (strategy_id)
# BRACKET_SURGEON: disabled
#                 )
            """"""
# BRACKET_SURGEON: disabled
#             )

            conn.execute(
                """"""
                CREATE TABLE IF NOT EXISTS strategic_insights (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        insight_type TEXT NOT NULL,
                        content TEXT NOT NULL,
                        confidence REAL NOT NULL,
                        created_at TIMESTAMP NOT NULL
# BRACKET_SURGEON: disabled
#                 )
            """"""
# BRACKET_SURGEON: disabled
#             )

    def create_strategy(
        self, name: str, objectives: List[str], initial_tactics: Dict[str, Any]
# BRACKET_SURGEON: disabled
#     ) -> StrategyPlan:
        """Create new strategic plan with autonomous refinement capability"""
        strategy_id = f"strategy_{datetime.now().strftime('%Y % m%d_ % H%M % S')}"

        # Initialize success metrics based on objectives
        success_metrics = self._generate_success_metrics(objectives)

        strategy = StrategyPlan(
            strategy_id=strategy_id,
            name=name,
            objectives=objectives,
            tactics=initial_tactics,
            success_metrics=success_metrics,
            confidence_score=0.8,  # Initial confidence
            created_at=datetime.now(),
            last_refined=datetime.now(),
# BRACKET_SURGEON: disabled
#         )

        self._save_strategy(strategy)
        self.logger.info(f"Created new strategy: {name} ({strategy_id})")

        return strategy

    def process_performance_feedback(
        self, strategy_id: str, performance_data: Dict[str, Any]
# BRACKET_SURGEON: disabled
#     ) -> bool:
        """Process performance feedback and trigger refinement if needed"""
        try:
            # Convert performance data to metrics
            metrics = StrategyMetrics(
                strategy_id=strategy_id,
                content_performance=performance_data.get("content_score", 0.5),
                marketing_roi=performance_data.get("marketing_roi", 0.5),
                audience_engagement=performance_data.get("engagement_score", 0.5),
                technical_health=performance_data.get("system_health", 0.9),
                timestamp=datetime.now(),
# BRACKET_SURGEON: disabled
#             )

            # Save metrics
            self._save_metrics(metrics)

            # Check if refinement is needed
            if metrics.overall_score() < self.refinement_trigger_threshold:
                self.logger.info(
                    f"Performance below threshold ({metrics.overall_score():.2f}), triggering refinement"
# BRACKET_SURGEON: disabled
#                 )
                return self._refine_strategy(strategy_id, metrics)

            return True

        except Exception as e:
            self.logger.error(f"Error processing feedback: {e}")
            return False

    def _refine_strategy(self, strategy_id: str, current_metrics: StrategyMetrics) -> bool:
        """Autonomously refine strategy based on performance data"""
        try:
            strategy = self._load_strategy(strategy_id)
            if not strategy:
                return False

            # Analyze historical performance
            historical_metrics = self._get_historical_metrics(strategy_id, days=30)

            # Generate refinement insights
            insights = self._generate_refinement_insights(
                strategy, current_metrics, historical_metrics
# BRACKET_SURGEON: disabled
#             )

            # Apply refinements
            refined_strategy = self._apply_refinements(strategy, insights)

            # Update strategy
            refined_strategy.last_refined = datetime.now()
            refined_strategy.refinement_count += 1
            refined_strategy.confidence_score = min(
                0.95, refined_strategy.confidence_score + self.learning_rate
# BRACKET_SURGEON: disabled
#             )

            self._save_strategy(refined_strategy)

            # Log strategic insight
            self._log_strategic_insight(
                "strategy_refinement",
                f"Refined strategy {strategy_id} based on performance feedback",
                0.8,
# BRACKET_SURGEON: disabled
#             )

            self.logger.info(f"Successfully refined strategy {strategy_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error refining strategy: {e}")
            return False

    def _generate_refinement_insights(
        self,
        strategy: StrategyPlan,
        current_metrics: StrategyMetrics,
        historical_metrics: List[StrategyMetrics],
    ) -> Dict[str, Any]:
        """Generate insights for strategy refinement"""
        insights = {
            "performance_trends": {},
            "tactical_adjustments": {},
            "objective_modifications": [],
# BRACKET_SURGEON: disabled
#         }

        # Analyze performance trends
        if historical_metrics:
            avg_content = sum(m.content_performance for m in historical_metrics) / len(
                historical_metrics
# BRACKET_SURGEON: disabled
#             )
            avg_marketing = sum(m.marketing_roi for m in historical_metrics) / len(
                historical_metrics
# BRACKET_SURGEON: disabled
#             )
            avg_engagement = sum(m.audience_engagement for m in historical_metrics) / len(
                historical_metrics
# BRACKET_SURGEON: disabled
#             )

            insights["performance_trends"] = {
                "content_trend": current_metrics.content_performance - avg_content,
                "marketing_trend": current_metrics.marketing_roi - avg_marketing,
                "engagement_trend": current_metrics.audience_engagement - avg_engagement,
# BRACKET_SURGEON: disabled
#             }

        # Generate tactical adjustments based on weak areas
        if current_metrics.content_performance < 0.6:
            insights["tactical_adjustments"]["content"] = {
                "increase_quality_checks": True,
                "diversify_content_types": True,
                "optimize_posting_schedule": True,
# BRACKET_SURGEON: disabled
#             }

        if current_metrics.marketing_roi < 0.6:
            insights["tactical_adjustments"]["marketing"] = {
                "refine_targeting": True,
                "test_new_channels": True,
                "optimize_conversion_funnel": True,
# BRACKET_SURGEON: disabled
#             }

        if current_metrics.audience_engagement < 0.6:
            insights["tactical_adjustments"]["engagement"] = {
                "improve_call_to_actions": True,
                "increase_interactive_content": True,
                "personalize_messaging": True,
# BRACKET_SURGEON: disabled
#             }

        return insights

    def _apply_refinements(self, strategy: StrategyPlan, insights: Dict[str, Any]) -> StrategyPlan:
        """Apply refinement insights to strategy"""
        refined_tactics = strategy.tactics.copy()

        # Apply tactical adjustments
        for area, adjustments in insights.get("tactical_adjustments", {}).items():
            if area not in refined_tactics:
                refined_tactics[area] = {}
            refined_tactics[area].update(adjustments)

        # Update success metrics based on trends
        refined_metrics = strategy.success_metrics.copy()
        trends = insights.get("performance_trends", {})

        for metric, trend in trends.items():
            if trend < -0.1:  # Declining trend
                metric_key = metric.replace("_trend", "_target")
                if metric_key in refined_metrics:
                    refined_metrics[metric_key] = min(1.0, refined_metrics[metric_key] + 0.1)

        return StrategyPlan(
            strategy_id=strategy.strategy_id,
            name=strategy.name,
            objectives=strategy.objectives,
            tactics=refined_tactics,
            success_metrics=refined_metrics,
            confidence_score=strategy.confidence_score,
            created_at=strategy.created_at,
            last_refined=strategy.last_refined,
            refinement_count=strategy.refinement_count,
# BRACKET_SURGEON: disabled
#         )

    def get_current_strategy(self) -> Optional[StrategyPlan]:
        """Get the most recent active strategy"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """"""
                SELECT * FROM strategy_plans
                ORDER BY last_refined DESC
                LIMIT 1
            """"""
# BRACKET_SURGEON: disabled
#             )
            row = cursor.fetchone()

            if row:
                return StrategyPlan(
                    strategy_id=row[0],
                    name=row[1],
                    objectives=json.loads(row[2]),
                    tactics=json.loads(row[3]),
                    success_metrics=json.loads(row[4]),
                    confidence_score=row[5],
                    created_at=datetime.fromisoformat(row[6]),
                    last_refined=datetime.fromisoformat(row[7]),
                    refinement_count=row[8],
# BRACKET_SURGEON: disabled
#                 )
        return None

    def get_strategic_insights(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get recent strategic insights"""
        cutoff_date = datetime.now() - timedelta(days=days)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """"""
                SELECT insight_type, content, confidence, created_at
                FROM strategic_insights
                WHERE created_at > ?
                ORDER BY created_at DESC
            ""","""
                (cutoff_date,),
# BRACKET_SURGEON: disabled
#             )

            return [
                {
                    "type": row[0],
                    "content": row[1],
                    "confidence": row[2],
                    "created_at": row[3],
# BRACKET_SURGEON: disabled
#                 }
                for row in cursor.fetchall()
# BRACKET_SURGEON: disabled
#             ]

    def _generate_success_metrics(self, objectives: List[str]) -> Dict[str, float]:
        """Generate success metrics based on objectives"""
        return {
            "content_quality_target": 0.8,
            "marketing_roi_target": 0.75,
            "engagement_rate_target": 0.7,
            "system_uptime_target": 0.99,
            "growth_rate_target": 0.1,
# BRACKET_SURGEON: disabled
#         }

    def _save_strategy(self, strategy: StrategyPlan):
        """Save strategy to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """"""
                INSERT OR REPLACE INTO strategy_plans
                (strategy_id, name, objectives, tactics, success_metrics,
# BRACKET_SURGEON: disabled
#                     confidence_score, created_at, last_refined, refinement_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ""","""
                (
                    strategy.strategy_id,
                    strategy.name,
                    json.dumps(strategy.objectives),
                    json.dumps(strategy.tactics),
                    json.dumps(strategy.success_metrics),
                    strategy.confidence_score,
                    strategy.created_at.isoformat(),
                    strategy.last_refined.isoformat(),
                    strategy.refinement_count,
# BRACKET_SURGEON: disabled
#                 ),
# BRACKET_SURGEON: disabled
#             )

    def _load_strategy(self, strategy_id: str) -> Optional[StrategyPlan]:
        """Load strategy from database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM strategy_plans WHERE strategy_id = ?", (strategy_id,)
# BRACKET_SURGEON: disabled
#             )
            row = cursor.fetchone()

            if row:
                return StrategyPlan(
                    strategy_id=row[0],
                    name=row[1],
                    objectives=json.loads(row[2]),
                    tactics=json.loads(row[3]),
                    success_metrics=json.loads(row[4]),
                    confidence_score=row[5],
                    created_at=datetime.fromisoformat(row[6]),
                    last_refined=datetime.fromisoformat(row[7]),
                    refinement_count=row[8],
# BRACKET_SURGEON: disabled
#                 )
        return None

    def _save_metrics(self, metrics: StrategyMetrics):
        """Save performance metrics to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """"""
                INSERT INTO strategy_metrics
                (strategy_id, content_performance, marketing_roi,
# BRACKET_SURGEON: disabled
#                     audience_engagement, technical_health, overall_score, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ""","""
                (
                    metrics.strategy_id,
                    metrics.content_performance,
                    metrics.marketing_roi,
                    metrics.audience_engagement,
                    metrics.technical_health,
                    metrics.overall_score(),
                    metrics.timestamp.isoformat(),
# BRACKET_SURGEON: disabled
#                 ),
# BRACKET_SURGEON: disabled
#             )

    def _get_historical_metrics(self, strategy_id: str, days: int = 30) -> List[StrategyMetrics]:
        """Get historical performance metrics"""
        cutoff_date = datetime.now() - timedelta(days=days)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """"""
                SELECT strategy_id, content_performance, marketing_roi,
                    audience_engagement, technical_health, timestamp
                FROM strategy_metrics
                WHERE strategy_id = ? AND timestamp > ?
                ORDER BY timestamp DESC
            ""","""
                (strategy_id, cutoff_date),
# BRACKET_SURGEON: disabled
#             )

            return [
                StrategyMetrics(
                    strategy_id=row[0],
                    content_performance=row[1],
                    marketing_roi=row[2],
                    audience_engagement=row[3],
                    technical_health=row[4],
                    timestamp=datetime.fromisoformat(row[5]),
# BRACKET_SURGEON: disabled
#                 )
                for row in cursor.fetchall()
# BRACKET_SURGEON: disabled
#             ]

    def _log_strategic_insight(self, insight_type: str, content: str, confidence: float):
        """Log strategic insight to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """"""
                INSERT INTO strategic_insights
                (insight_type, content, confidence, created_at)
                VALUES (?, ?, ?, ?)
            ""","""
                (insight_type, content, confidence, datetime.now().isoformat()),
# BRACKET_SURGEON: disabled
#             )

    @property
    def capabilities(self) -> List["AgentCapability"]:
        """Return the capabilities of this agent"""

        from .base_agents import AgentCapability

        return [AgentCapability.PLANNING, AgentCapability.ANALYSIS]

    async def _execute_with_monitoring(self, task: Dict[str, Any], context) -> Dict[str, Any]:
        """Execute task with monitoring - required abstract method implementation"""
        try:
            result = self.execute_task(task)
            return result
        except Exception as e:
            self.logger.error(f"Error executing task with monitoring: {e}")
            return {"success": False, "error": str(e)}

    async def _rephrase_task(self, task: Dict[str, Any], context) -> str:
        """Rephrase task - required abstract method implementation"""
        task_type = task.get("type", "unknown")
        task_name = task.get("name", "strategic planning task")
        return f"Strategic Planning: {task_name} ({task_type})"

    async def _validate_rephrase_accuracy(
        self, original_task: Dict[str, Any], rephrased: str, context
# BRACKET_SURGEON: disabled
#     ) -> bool:
        """Validate rephrase accuracy - required abstract method implementation"""
        # For now, always return True as basic validation
        return True

    def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute strategic planning task"""
        task_type = task_data.get("type")

        if task_type == "create_strategy":
            strategy = self.create_strategy(
                task_data["name"], task_data["objectives"], task_data.get("tactics", {})
# BRACKET_SURGEON: disabled
#             )
            return {"success": True, "strategy_id": strategy.strategy_id}

        elif task_type == "process_feedback":
            success = self.process_performance_feedback(
                task_data["strategy_id"], task_data["performance_data"]
# BRACKET_SURGEON: disabled
#             )
            return {"success": success}

        elif task_type == "get_current_strategy":
            strategy = self.get_current_strategy()
            return {"success": True, "strategy": asdict(strategy) if strategy else None}

        return {"success": False, "error": f"Unknown task type: {task_type}"}


if __name__ == "__main__":
    # Test the Planner Agent
    planner = PlannerAgent()

    # Create initial strategy
    strategy = planner.create_strategy(
        "Content Empire Growth",
        [
            "Achieve 100K monthly views",
            "Generate $10K monthly revenue",
            "Build engaged community of 50K followers",
# BRACKET_SURGEON: disabled
#         ],
        {
            "content": {
                "posting_frequency": "daily",
                "content_types": ["educational", "entertaining", "promotional"],
                "quality_threshold": 0.8,
# BRACKET_SURGEON: disabled
#             },
            "marketing": {
                "channels": ["youtube", "twitter", "linkedin"],
                "budget_allocation": {"organic": 0.7, "paid": 0.3},
# BRACKET_SURGEON: disabled
#             },
# BRACKET_SURGEON: disabled
#         },
# BRACKET_SURGEON: disabled
#     )

    print(f"Created strategy: {strategy.name} ({strategy.strategy_id})")

    # Simulate performance feedback
    performance_data = {
        "content_score": 0.5,  # Below threshold
        "marketing_roi": 0.7,
        "engagement_score": 0.6,
        "system_health": 0.95,
# BRACKET_SURGEON: disabled
#     }

    success = planner.process_performance_feedback(strategy.strategy_id, performance_data)
    print(f"Processed feedback: {success}")

    # Get insights
    insights = planner.get_strategic_insights()
    print(f"Strategic insights: {len(insights)} found")