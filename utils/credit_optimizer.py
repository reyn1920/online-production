#!/usr / bin / env python3
"""
Credit Optimizer - Intelligent credit usage optimization
Optimizes API calls to minimize credit consumption while maintaining quality
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

@dataclass


class CreditUsagePattern:
    """Credit usage pattern analysis"""

    model: str
    avg_credits_per_request: float
    success_rate: float
    avg_response_time: float
    cost_efficiency: float  # Quality / cost ratio
    last_updated: datetime

@dataclass


class OptimizationRecommendation:
    """Credit optimization recommendation"""

    recommended_model: str
    estimated_credits: float
    confidence_score: float
    reasoning: str
    fallback_options: List[str]


class CreditOptimizer:
    """Intelligent credit usage optimizer"""


    def __init__(self, config_path: str = None):
        """Initialize the credit optimizer"""
        self.logger = logging.getLogger(__name__)

        # Usage patterns tracking
        self.usage_patterns: Dict[str, CreditUsagePattern] = {}

        # Optimization settings
        self.optimization_config = {
            "min_samples_for_optimization": 5,
                "cost_weight": 0.4,
                "quality_weight": 0.3,
                "speed_weight": 0.3,
                "pattern_decay_hours": 24,
                "confidence_threshold": 0.7,
                }

        # Model cost estimates (credits per 1k tokens)
        self.model_costs = {
            "gpt - 4": 0.03,
                "gpt - 3.5 - turbo": 0.002,
                "claude - 3-opus": 0.015,
                "claude - 3-sonnet": 0.003,
                "claude - 3-haiku": 0.00025,
                "gemini - pro": 0.001,
                "llama - 2-70b": 0.0007,
                "mixtral - 8x7b": 0.0006,
                }

        # Quality scores (subjective, 0 - 1)
        self.model_quality = {
            "gpt - 4": 0.95,
                "claude - 3-opus": 0.93,
                "gpt - 3.5 - turbo": 0.85,
                "claude - 3-sonnet": 0.88,
                "gemini - pro": 0.82,
                "mixtral - 8x7b": 0.80,
                "llama - 2-70b": 0.78,
                "claude - 3-haiku": 0.75,
                }

        # Speed estimates (requests per minute)
        self.model_speed = {
            "claude - 3-haiku": 60,
                "gpt - 3.5 - turbo": 50,
                "gemini - pro": 45,
                "mixtral - 8x7b": 40,
                "llama - 2-70b": 35,
                "claude - 3-sonnet": 30,
                "gpt - 4": 20,
                "claude - 3-opus": 15,
                }

        self.logger.info("Credit optimizer initialized")


    def estimate_token_count(self, messages: List[Dict]) -> int:
        """Estimate token count for messages"""
        # Simple estimation: ~4 characters per token
        total_chars = sum(len(str(msg.get("content", ""))) for msg in messages)
        return max(total_chars // 4, 10)  # Minimum 10 tokens


    def calculate_efficiency_score(self, model: str, estimated_tokens: int) -> float:
        """Calculate efficiency score for a model"""
        cost = self.model_costs.get(model, 0.01)
        quality = self.model_quality.get(model, 0.5)
        speed = self.model_speed.get(model, 30)

        # Normalize speed (higher is better)
        normalized_speed = min(speed / 60, 1.0)

        # Calculate weighted score
        config = self.optimization_config
        efficiency = (
            (quality * config["quality_weight"])
            + (normalized_speed * config["speed_weight"])
            + ((1 - min(cost, 0.05) / 0.05) * config["cost_weight"])
        )

        return efficiency


    def get_model_recommendation(
        self,
            messages: List[Dict],
            task_type: str = "general",
            budget_limit: float = None,
            speed_priority: bool = False,
            ) -> OptimizationRecommendation:
        """
        Get optimized model recommendation

        Args:
            messages: Input messages
            task_type: Type of task (general, creative, analytical, etc.)
            budget_limit: Maximum credits to spend
            speed_priority: Whether to prioritize speed over quality

        Returns:
            Optimization recommendation
        """
        estimated_tokens = self.estimate_token_count(messages)

        # Task - specific model preferences
        task_preferences = {
            "creative": ["gpt - 4", "claude - 3-opus", "claude - 3-sonnet"],
                "analytical": ["claude - 3-opus", "gpt - 4", "claude - 3-sonnet"],
                "coding": ["gpt - 4", "claude - 3-sonnet", "gpt - 3.5 - turbo"],
                "general": ["gpt - 3.5 - turbo", "claude - 3-sonnet", "gemini - pro"],
                "fast": ["claude - 3-haiku", "gpt - 3.5 - turbo", "gemini - pro"],
                }

        if speed_priority:
            task_type = "fast"

        preferred_models = task_preferences.get(task_type, task_preferences["general"])

        # Calculate scores for all models
        model_scores = []
        for model in preferred_models:
            if model not in self.model_costs:
                continue

            estimated_cost = (estimated_tokens / 1000) * self.model_costs[model]

            # Skip if over budget
            if budget_limit and estimated_cost > budget_limit:
                continue

            efficiency = self.calculate_efficiency_score(model, estimated_tokens)

            # Apply usage pattern adjustments if available
            if model in self.usage_patterns:
                pattern = self.usage_patterns[model]
                # Adjust based on historical success rate
                efficiency *= pattern.success_rate

            model_scores.append(
                {
                    "model": model,
                        "efficiency": efficiency,
                        "estimated_cost": estimated_cost,
                        "estimated_tokens": estimated_tokens,
                        }
            )

        # Sort by efficiency score
        model_scores.sort(key = lambda x: x["efficiency"], reverse = True)

        if not model_scores:
            # Fallback to cheapest model
            fallback_model = "claude - 3-haiku"
            estimated_cost = (estimated_tokens / 1000) * self.model_costs[
                fallback_model
            ]

            return OptimizationRecommendation(
                recommended_model = fallback_model,
                    estimated_credits = estimated_cost,
                    confidence_score = 0.3,
                    reasoning="Fallback to most cost - effective model",
                    fallback_options=["gpt - 3.5 - turbo", "gemini - pro"],
                    )

        best_model = model_scores[0]
        fallback_options = [score["model"] for score in model_scores[1:3]]

        # Calculate confidence based on efficiency gap
        confidence = min(best_model["efficiency"], 0.95)
        if len(model_scores) > 1:
            efficiency_gap = best_model["efficiency"] - model_scores[1]["efficiency"]
            confidence = min(confidence + (efficiency_gap * 0.5), 0.95)

        reasoning_parts = []
        if task_type != "general":
            reasoning_parts.append(f"Optimized for {task_type} tasks")
        if budget_limit:
            reasoning_parts.append(f"Within budget limit of {budget_limit:.4f} credits")
        if speed_priority:
            reasoning_parts.append("Prioritizing response speed")

        reasoning = (
            "; ".join(reasoning_parts) if reasoning_parts else "General optimization"
        )

        return OptimizationRecommendation(
            recommended_model = best_model["model"],
                estimated_credits = best_model["estimated_cost"],
                confidence_score = confidence,
                reasoning = reasoning,
                fallback_options = fallback_options,
                )


    def record_usage(
        self,
            model: str,
            actual_credits: float,
            success: bool,
            response_time: float,
            quality_score: float = None,
            ):
        """
        Record actual usage for pattern learning

        Args:
            model: Model used
            actual_credits: Actual credits consumed
            success: Whether the request was successful
            response_time: Response time in seconds
            quality_score: Optional quality assessment (0 - 1)
        """
        now = datetime.now()

        if model not in self.usage_patterns:
            # Initialize new pattern
            self.usage_patterns[model] = CreditUsagePattern(
                model = model,
                    avg_credits_per_request = actual_credits,
                    success_rate = 1.0 if success else 0.0,
                    avg_response_time = response_time,
                    cost_efficiency = quality_score or self.model_quality.get(model, 0.5),
                    last_updated = now,
                    )
        else:
            # Update existing pattern with exponential moving average
            pattern = self.usage_patterns[model]
            alpha = 0.3  # Learning rate

            pattern.avg_credits_per_request = (
                alpha * actual_credits + (1 - alpha) * pattern.avg_credits_per_request
            )

            pattern.success_rate = (
                alpha * (1.0 if success else 0.0) + (1 - alpha) * pattern.success_rate
            )

            pattern.avg_response_time = (
                alpha * response_time + (1 - alpha) * pattern.avg_response_time
            )

            if quality_score:
                pattern.cost_efficiency = (
                    alpha * quality_score + (1 - alpha) * pattern.cost_efficiency
                )

            pattern.last_updated = now

        self.logger.debug(
            f"Recorded usage for {model}: {actual_credits:.4f} credits, success: {success}"
        )


    def get_budget_recommendation(
        self,
            available_credits: float,
            expected_requests: int,
            task_distribution: Dict[str, float] = None,
            ) -> Dict:
        """
        Get budget allocation recommendations

        Args:
            available_credits: Total available credits
            expected_requests: Expected number of requests
            task_distribution: Distribution of task types (e.g., {'general': 0.7, 'creative': 0.3})

        Returns:
            Budget allocation recommendations
        """
        if not task_distribution:
            task_distribution = {"general": 1.0}

        # Calculate average cost per request for each task type
        task_costs = {}
        for task_type, proportion in task_distribution.items():
            # Get typical model for this task type
            typical_messages = [
                {"role": "user", "content": "Sample message for estimation"}
            ]
            recommendation = self.get_model_recommendation(typical_messages, task_type)
            task_costs[task_type] = recommendation.estimated_credits

        # Calculate weighted average cost
        avg_cost_per_request = sum(
            task_costs[task_type] * proportion
            for task_type, proportion in task_distribution.items()
        )

        total_estimated_cost = avg_cost_per_request * expected_requests

        # Budget recommendations
        recommendations = {
            "estimated_total_cost": total_estimated_cost,
                "avg_cost_per_request": avg_cost_per_request,
                "budget_utilization": min(total_estimated_cost / available_credits, 1.0),
                "recommended_requests": int(available_credits / avg_cost_per_request),
                "cost_breakdown": {
                task_type: {
                    "proportion": proportion,
                        "estimated_requests": int(expected_requests * proportion),
                        "cost_per_request": task_costs[task_type],
                        "total_cost": task_costs[task_type]
                    * expected_requests
                    * proportion,
                        }
                for task_type, proportion in task_distribution.items()
            },
                }

        # Add warnings
        if total_estimated_cost > available_credits:
            recommendations["warning"] = (
                f"Estimated cost ({total_estimated_cost:.4f}) exceeds available credits ({available_credits:.4f})"
            )
            recommendations["suggested_reduction"] = (
                total_estimated_cost - available_credits
            )

        return recommendations


    def get_optimization_analytics(self) -> Dict:
        """Get optimization analytics and insights"""
        analytics = {
            "tracked_models": len(self.usage_patterns),
                "total_requests_tracked": sum(
                1 for pattern in self.usage_patterns.values()
            ),
                "model_performance": {},
                "cost_insights": {},
                "recommendations": [],
                }

        # Analyze model performance
        for model, pattern in self.usage_patterns.items():
            analytics["model_performance"][model] = {
                "avg_credits": pattern.avg_credits_per_request,
                    "success_rate": pattern.success_rate,
                    "avg_response_time": pattern.avg_response_time,
                    "cost_efficiency": pattern.cost_efficiency,
                    "last_used": pattern.last_updated.isoformat(),
                    }

        # Cost insights
        if self.usage_patterns:
            total_credits = sum(
                p.avg_credits_per_request for p in self.usage_patterns.values()
            )
            avg_credits = total_credits / len(self.usage_patterns)

            most_efficient = max(
                self.usage_patterns.items(), key = lambda x: x[1].cost_efficiency
            )

            least_efficient = min(
                self.usage_patterns.items(), key = lambda x: x[1].cost_efficiency
            )

            analytics["cost_insights"] = {
                "avg_credits_per_request": avg_credits,
                    "most_efficient_model": most_efficient[0],
                    "least_efficient_model": least_efficient[0],
                    "efficiency_gap": most_efficient[1].cost_efficiency
                - least_efficient[1].cost_efficiency,
                    }

        # Generate recommendations
        recommendations = []

        # Check for underperforming models
        for model, pattern in self.usage_patterns.items():
            if pattern.success_rate < 0.8:
                recommendations.append(
                    f"Consider avoiding {model} due to low success rate ({pattern.success_rate:.1%})"
                )

            if pattern.cost_efficiency < 0.5:
                recommendations.append(
                    f"Review usage of {model} - low cost efficiency ({pattern.cost_efficiency:.2f})"
                )

        # Check for optimization opportunities
        if len(self.usage_patterns) > 1:
            efficiency_scores = [
                (model, pattern.cost_efficiency)
                for model, pattern in self.usage_patterns.items()
            ]
            efficiency_scores.sort(key = lambda x: x[1], reverse = True)

            if len(efficiency_scores) >= 2:
                best_model = efficiency_scores[0][0]
                recommendations.append(
                    f"Consider using {best_model} more frequently for better efficiency"
                )

        analytics["recommendations"] = recommendations

        return analytics


    async def cleanup(self):
        """Cleanup optimizer resources"""
        # Clean up old patterns
        cutoff_time = datetime.now() - timedelta(
            hours = self.optimization_config["pattern_decay_hours"]
        )

        expired_models = [
            model
            for model, pattern in self.usage_patterns.items()
            if pattern.last_updated < cutoff_time
        ]

        for model in expired_models:
            del self.usage_patterns[model]

        self.logger.info(
            f"Credit optimizer cleanup completed, removed {len(expired_models)} expired patterns"
        )

# Example usage and testing
if __name__ == "__main__":


    async def test_credit_optimizer():
        print("🔧 Credit Optimizer Test")
        print("=" * 40)

        optimizer = CreditOptimizer()

        # Test 1: Basic recommendation
        messages = [
            {
                "role": "user",
                    "content": "Write a creative story about a robot learning to paint",
                    }
        ]

        recommendation = optimizer.get_model_recommendation(
            messages, task_type="creative"
        )
        print(f"\n📊 Creative Task Recommendation:")
        print(f"   Model: {recommendation.recommended_model}")
        print(f"   Estimated credits: {recommendation.estimated_credits:.4f}")
        print(f"   Confidence: {recommendation.confidence_score:.2f}")
        print(f"   Reasoning: {recommendation.reasoning}")
        print(f"   Fallbacks: {recommendation.fallback_options}")

        # Test 2: Budget - constrained recommendation
        budget_rec = optimizer.get_model_recommendation(
            messages, task_type="general", budget_limit = 0.005
        )
        print(f"\n💰 Budget - Constrained Recommendation:")
        print(f"   Model: {budget_rec.recommended_model}")
        print(f"   Estimated credits: {budget_rec.estimated_credits:.4f}")
        print(f"   Within budget: {budget_rec.estimated_credits <= 0.005}")

        # Test 3: Speed priority
        speed_rec = optimizer.get_model_recommendation(messages, speed_priority = True)
        print(f"\n⚡ Speed Priority Recommendation:")
        print(f"   Model: {speed_rec.recommended_model}")
        print(f"   Estimated credits: {speed_rec.estimated_credits:.4f}")

        # Test 4: Record some usage patterns
        optimizer.record_usage("gpt - 3.5 - turbo", 0.002, True, 1.5, 0.85)
        optimizer.record_usage("claude - 3-sonnet", 0.003, True, 2.1, 0.90)
        optimizer.record_usage("gpt - 4", 0.025, False, 5.0, 0.0)  # Failed request

        # Test 5: Budget analysis
        budget_analysis = optimizer.get_budget_recommendation(
            available_credits = 1.0,
                expected_requests = 100,
                task_distribution={"general": 0.6, "creative": 0.3, "analytical": 0.1},
                )

        print(f"\n📈 Budget Analysis:")
        print(f"   Estimated total cost: {budget_analysis['estimated_total_cost']:.4f}")
        print(f"   Budget utilization: {budget_analysis['budget_utilization']:.1%}")
        print(f"   Recommended requests: {budget_analysis['recommended_requests']}")

        if "warning" in budget_analysis:
            print(f"   ⚠️  {budget_analysis['warning']}")

        # Test 6: Analytics
        analytics = optimizer.get_optimization_analytics()
        print(f"\n📊 Optimization Analytics:")
        print(f"   Tracked models: {analytics['tracked_models']}")

        for model, perf in analytics["model_performance"].items():
            print(
                f"   {model}: {perf['success_rate']:.1%} success, {perf['avg_credits']:.4f} credits"
            )

        if analytics["recommendations"]:
            print(f"\n💡 Recommendations:")
            for rec in analytics["recommendations"]:
                print(f"   • {rec}")

        await optimizer.cleanup()
        print("\n✅ Credit optimizer test completed")

    asyncio.run(test_credit_optimizer())
