#!/usr/bin/env python3
""""""
API Aggregation Engine
Combines multiple free APIs to create superior functionality than paid services
""""""

import asyncio
import aiohttp
import json
import logging
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import hashlib
import statistics
from .free_api_catalog import FreeAPICatalog, FreeAPIRouter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AggregationStrategy(Enum):
    """Strategies for combining API results"""

    CONSENSUS = "consensus"  # Use majority vote/average
    BEST_QUALITY = "best_quality"  # Use highest quality source
    FASTEST = "fastest"  # Use fastest response
    COMPREHENSIVE = "comprehensive"  # Combine all unique data
    REDUNDANT = "redundant"  # Multiple sources for reliability
    HYBRID = "hybrid"  # Smart combination based on context


@dataclass
class AggregationTask:
    """Task for API aggregation"""

    name: str
    requirement: str
    apis: List[str]
    strategy: AggregationStrategy
    weight_factors: Optional[Dict[str, float]] = None
    timeout: int = 30
    min_sources: int = 2
    quality_threshold: float = 0.7
    cache_duration: int = 300  # 5 minutes


class SuperiorAPIAggregator:
    """Aggregates multiple free APIs to outperform paid services"""

    def __init__(self, catalog: FreeAPICatalog):
        self.catalog = catalog
        self.cache = {}
        self.performance_history = {}
        self.quality_metrics = {}
        self.session = None

        # Pre-defined superior aggregation tasks
        self.superior_tasks = self._initialize_superior_tasks()

    def _initialize_superior_tasks(self) -> Dict[str, AggregationTask]:
        """Initialize tasks that outperform paid services"""
        tasks = {}

        # Superior Content Generation (vs GPT-4, Claude)
        tasks["advanced_content_generation"] = AggregationTask(
            name="Advanced Content Generation",
            requirement="content generation writing creative",
            apis=["huggingface", "openai_compatible", "replicate"],
            strategy=AggregationStrategy.HYBRID,
            weight_factors={"quality": 0.4, "creativity": 0.3, "speed": 0.3},
            min_sources=3,
# BRACKET_SURGEON: disabled
#         )

        # Superior Image Analysis (vs Google Vision, AWS Rekognition)
        tasks["comprehensive_image_analysis"] = AggregationTask(
            name="Comprehensive Image Analysis",
            requirement="image analysis computer vision object detection",
            apis=["huggingface", "replicate"],
            strategy=AggregationStrategy.COMPREHENSIVE,
            weight_factors={"accuracy": 0.5, "detail": 0.3, "speed": 0.2},
# BRACKET_SURGEON: disabled
#         )

        # Superior Market Intelligence (vs Bloomberg, Reuters)
        tasks["market_intelligence"] = AggregationTask(
            name="Superior Market Intelligence",
            requirement="finance stock market cryptocurrency",
            apis=["alpha_vantage", "coinapi", "newsapi", "guardian"],
            strategy=AggregationStrategy.COMPREHENSIVE,
            weight_factors={"accuracy": 0.4, "timeliness": 0.3, "coverage": 0.3},
# BRACKET_SURGEON: disabled
#         )

        # Superior Weather Intelligence (vs AccuWeather Pro)
        tasks["weather_intelligence"] = AggregationTask(
            name="Weather Intelligence System",
            requirement="weather forecast climate",
            apis=["openweather", "weatherapi"],
            strategy=AggregationStrategy.CONSENSUS,
            weight_factors={"accuracy": 0.5, "detail": 0.3, "reliability": 0.2},
# BRACKET_SURGEON: disabled
#         )

        # Superior Content Discovery (vs Shutterstock, Getty Images)
        tasks["content_discovery"] = AggregationTask(
            name="Superior Content Discovery",
            requirement="images photos videos content media",
            apis=["unsplash", "pixabay", "pexels", "lorem_picsum"],
            strategy=AggregationStrategy.COMPREHENSIVE,
            weight_factors={"quality": 0.4, "variety": 0.3, "relevance": 0.3},
# BRACKET_SURGEON: disabled
#         )

        # Superior Translation (vs Google Translate Pro)
        tasks["advanced_translation"] = AggregationTask(
            name="Advanced Translation System",
            requirement="translation language multilingual",
            apis=["mymemory", "libretranslate", "huggingface"],
            strategy=AggregationStrategy.CONSENSUS,
            weight_factors={"accuracy": 0.5, "naturalness": 0.3, "context": 0.2},
# BRACKET_SURGEON: disabled
#         )

        # Superior News Intelligence (vs premium news services)
        tasks["news_intelligence"] = AggregationTask(
            name="News Intelligence System",
            requirement="news information current events",
            apis=["newsapi", "guardian"],
            strategy=AggregationStrategy.COMPREHENSIVE,
            weight_factors={"credibility": 0.4, "coverage": 0.3, "timeliness": 0.3},
# BRACKET_SURGEON: disabled
#         )

        # Superior Data Analytics (vs premium analytics platforms)
        tasks["data_analytics"] = AggregationTask(
            name="Comprehensive Data Analytics",
            requirement="data analytics statistics information",
            apis=["worldbank", "restcountries", "alpha_vantage"],
            strategy=AggregationStrategy.COMPREHENSIVE,
            weight_factors={"accuracy": 0.4, "completeness": 0.3, "relevance": 0.3},
# BRACKET_SURGEON: disabled
#         )

        return tasks

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def execute_superior_task(
        self, task_name: str, input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a pre-defined superior aggregation task"""
        if task_name not in self.superior_tasks:
            return {"success": False, "error": f"Task {task_name} not found"}

        task = self.superior_tasks[task_name]
        return await self.aggregate_apis(task, input_data)

    async def aggregate_apis(
        self, task: AggregationTask, input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Aggregate multiple APIs based on strategy"""
        start_time = time.time()

        # Check cache first
        cache_key = self._generate_cache_key(task.name, input_data)
        if cache_key in self.cache:
            cached_result = self.cache[cache_key]
            if time.time() - cached_result["timestamp"] < task.cache_duration:
                cached_result["from_cache"] = True
                return cached_result

        # Execute API calls concurrently
        api_results = await self._execute_concurrent_api_calls(task, input_data)

        if len(api_results) < task.min_sources:
            return {
                "success": False,
                "error": f"Insufficient sources: {len(api_results)}/{task.min_sources}",
                "partial_results": api_results,
# BRACKET_SURGEON: disabled
#             }

        # Apply aggregation strategy
        aggregated_result = await self._apply_aggregation_strategy(task, api_results)

        # Calculate quality metrics
        quality_score = self._calculate_quality_score(task, api_results, aggregated_result)

        final_result = {
            "success": True,
            "task_name": task.name,
            "strategy": task.strategy.value,
            "data": aggregated_result,
            "quality_score": quality_score,
            "sources_used": len(api_results),
            "execution_time": time.time() - start_time,
            "api_results": api_results,
            "advantages_over_paid": self._get_advantages_over_paid(task_name),
            "timestamp": time.time(),
# BRACKET_SURGEON: disabled
#         }

        # Cache result
        self.cache[cache_key] = final_result

        # Update performance history
        self._update_performance_history(task.name, final_result)

        return final_result

    async def _execute_concurrent_api_calls(
        self, task: AggregationTask, input_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Execute API calls concurrently with timeout"""
        async with FreeAPIRouter(self.catalog) as router:
            # Create tasks for concurrent execution
            api_tasks = []
            for api_name in task.apis:
                if api_name in self.catalog.apis:
                    api_task = asyncio.create_task(
                        self._safe_api_call(router, task.requirement, input_data, [api_name])
# BRACKET_SURGEON: disabled
#                     )
                    api_tasks.append((api_name, api_task))

            # Wait for all tasks with timeout
            results = []
            try:
                completed_tasks = await asyncio.wait_for(
                    asyncio.gather(*[task for _, task in api_tasks], return_exceptions=True),
                    timeout=task.timeout,
# BRACKET_SURGEON: disabled
#                 )

                for i, result in enumerate(completed_tasks):
                    api_name = api_tasks[i][0]
                    if isinstance(result, Exception):
                        logger.warning(f"API {api_name} failed: {str(result)}")
                    elif result and result.get("success"):
                        result["api_name"] = api_name
                        result["quality_weight"] = self._get_api_quality_weight(api_name)
                        results.append(result)

            except asyncio.TimeoutError:
                logger.warning(f"Timeout reached for task {task.name}")
                # Collect any completed results
                for api_name, api_task in api_tasks:
                    if api_task.done() and not api_task.exception():
                        result = api_task.result()
                        if result and result.get("success"):
                            result["api_name"] = api_name
                            result["quality_weight"] = self._get_api_quality_weight(api_name)
                            results.append(result)

            return results

    async def _safe_api_call(
        self,
        router: FreeAPIRouter,
        requirement: str,
        input_data: Dict[str, Any],
        preferred_apis: List[str],
    ) -> Optional[Dict[str, Any]]:
        """Make safe API call with error handling"""
        try:
            return await router.smart_request(requirement, input_data, preferred_apis)
        except Exception as e:
            logger.error(f"Safe API call failed: {str(e)}")
            return None

    async def _apply_aggregation_strategy(
        self, task: AggregationTask, api_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Apply the specified aggregation strategy"""
        if task.strategy == AggregationStrategy.CONSENSUS:
            return await self._consensus_aggregation(api_results, task.weight_factors)
        elif task.strategy == AggregationStrategy.BEST_QUALITY:
            return await self._best_quality_aggregation(api_results)
        elif task.strategy == AggregationStrategy.FASTEST:
            return await self._fastest_aggregation(api_results)
        elif task.strategy == AggregationStrategy.COMPREHENSIVE:
            return await self._comprehensive_aggregation(api_results)
        elif task.strategy == AggregationStrategy.REDUNDANT:
            return await self._redundant_aggregation(api_results)
        elif task.strategy == AggregationStrategy.HYBRID:
            return await self._hybrid_aggregation(api_results, task.weight_factors)
        else:
            return await self._comprehensive_aggregation(api_results)

    async def _consensus_aggregation(
        self,
        api_results: List[Dict[str, Any]],
        weight_factors: Optional[Dict[str, float]],
    ) -> Dict[str, Any]:
        """Aggregate using consensus/averaging approach"""
        if not api_results:
            return {}

        # For numerical data, calculate weighted averages
        # For text data, use majority vote or combine
        aggregated = {
            "consensus_data": {},
            "confidence_score": 0,
            "source_agreement": 0,
            "method": "consensus",
# BRACKET_SURGEON: disabled
#         }

        # Collect all data points
        all_data = [result.get("data", {}) for result in api_results]
        weights = [result.get("quality_weight", 1.0) for result in api_results]

        # Find common keys
        common_keys = set()
        for data in all_data:
            if isinstance(data, dict):
                common_keys.update(data.keys())

        # Aggregate each key
        for key in common_keys:
            values = []
            value_weights = []

            for i, data in enumerate(all_data):
                if isinstance(data, dict) and key in data:
                    values.append(data[key])
                    value_weights.append(weights[i])

            if values:
                if all(isinstance(v, (int, float)) for v in values):
                    # Numerical data - weighted average
                    weighted_sum = sum(v * w for v, w in zip(values, value_weights))
                    total_weight = sum(value_weights)
                    aggregated["consensus_data"][key] = (
                        weighted_sum / total_weight if total_weight > 0 else 0
# BRACKET_SURGEON: disabled
#                     )
                else:
                    # Text data - majority vote or combine
                    aggregated["consensus_data"][key] = self._aggregate_text_values(
                        values, value_weights
# BRACKET_SURGEON: disabled
#                     )

        # Calculate confidence based on agreement
        aggregated["confidence_score"] = self._calculate_consensus_confidence(api_results)
        aggregated["source_agreement"] = len(common_keys) / max(
            len(set().union(*[d.keys() if isinstance(d, dict) else [] for d in all_data])),
            1,
# BRACKET_SURGEON: disabled
#         )

        return aggregated

    async def _best_quality_aggregation(self, api_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Use result from highest quality API"""
        if not api_results:
            return {}

        # Sort by quality weight
        sorted_results = sorted(api_results, key=lambda x: x.get("quality_weight", 0), reverse=True)
        best_result = sorted_results[0]

        return {
            "best_quality_data": best_result.get("data", {}),
            "selected_api": best_result.get("api_name", "unknown"),
            "quality_score": best_result.get("quality_weight", 0),
            "method": "best_quality",
            "alternatives_available": len(api_results) - 1,
# BRACKET_SURGEON: disabled
#         }

    async def _fastest_aggregation(self, api_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Use result from fastest API"""
        if not api_results:
            return {}

        # Sort by response time
        sorted_results = sorted(api_results, key=lambda x: x.get("response_time", float("inf")))
        fastest_result = sorted_results[0]

        return {
            "fastest_data": fastest_result.get("data", {}),
            "selected_api": fastest_result.get("api_name", "unknown"),
            "response_time": fastest_result.get("response_time", 0),
            "method": "fastest",
            "speed_advantage": self._calculate_speed_advantage(api_results),
# BRACKET_SURGEON: disabled
#         }

    async def _comprehensive_aggregation(self, api_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Combine all unique data from all sources"""
        if not api_results:
            return {}

        comprehensive_data = {
            "combined_data": {},
            "source_breakdown": {},
            "total_data_points": 0,
            "method": "comprehensive",
# BRACKET_SURGEON: disabled
#         }

        for result in api_results:
            api_name = result.get("api_name", "unknown")
            data = result.get("data", {})

            if isinstance(data, dict):
                # Merge data, keeping track of sources
                for key, value in data.items():
                    if key not in comprehensive_data["combined_data"]:
                        comprehensive_data["combined_data"][key] = []

                    comprehensive_data["combined_data"][key].append(
                        {
                            "value": value,
                            "source": api_name,
                            "quality": result.get("quality_weight", 1.0),
# BRACKET_SURGEON: disabled
#                         }
# BRACKET_SURGEON: disabled
#                     )

                comprehensive_data["source_breakdown"][api_name] = {
                    "data_points": len(data),
                    "quality_score": result.get("quality_weight", 1.0),
                    "response_time": result.get("response_time", 0),
# BRACKET_SURGEON: disabled
#                 }

                comprehensive_data["total_data_points"] += len(data)

        # Calculate coverage score
        comprehensive_data["coverage_score"] = len(comprehensive_data["combined_data"])
        comprehensive_data["source_diversity"] = len(comprehensive_data["source_breakdown"])

        return comprehensive_data

    async def _redundant_aggregation(self, api_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Provide redundant data for maximum reliability"""
        if not api_results:
            return {}

        redundant_data = {
            "primary_data": {},
            "backup_data": [],
            "reliability_score": 0,
            "method": "redundant",
# BRACKET_SURGEON: disabled
#         }

        # Use highest quality as primary
        sorted_results = sorted(api_results, key=lambda x: x.get("quality_weight", 0), reverse=True)

        if sorted_results:
            redundant_data["primary_data"] = sorted_results[0].get("data", {})
            redundant_data["primary_source"] = sorted_results[0].get("api_name", "unknown")

            # Store backups
            for result in sorted_results[1:]:
                redundant_data["backup_data"].append(
                    {
                        "data": result.get("data", {}),
                        "source": result.get("api_name", "unknown"),
                        "quality": result.get("quality_weight", 1.0),
# BRACKET_SURGEON: disabled
#                     }
# BRACKET_SURGEON: disabled
#                 )

        # Calculate reliability based on redundancy
        redundant_data["reliability_score"] = min(len(api_results) / 3.0, 1.0)  # Max at 3 sources
        redundant_data["backup_sources_available"] = len(redundant_data["backup_data"])

        return redundant_data

    async def _hybrid_aggregation(
        self,
        api_results: List[Dict[str, Any]],
        weight_factors: Optional[Dict[str, float]],
    ) -> Dict[str, Any]:
        """Smart hybrid approach combining multiple strategies"""
        if not api_results:
            return {}

        # Apply multiple strategies and combine intelligently
        consensus_result = await self._consensus_aggregation(api_results, weight_factors)
        best_quality_result = await self._best_quality_aggregation(api_results)
        comprehensive_result = await self._comprehensive_aggregation(api_results)

        hybrid_data = {
            "hybrid_data": {
                "consensus": consensus_result.get("consensus_data", {}),
                "best_quality": best_quality_result.get("best_quality_data", {}),
                "comprehensive": comprehensive_result.get("combined_data", {}),
# BRACKET_SURGEON: disabled
#             },
            "recommended_data": {},
            "confidence_breakdown": {
                "consensus_confidence": consensus_result.get("confidence_score", 0),
                "quality_confidence": best_quality_result.get("quality_score", 0),
                "coverage_confidence": comprehensive_result.get("coverage_score", 0),
# BRACKET_SURGEON: disabled
#             },
            "method": "hybrid",
# BRACKET_SURGEON: disabled
#         }

        # Intelligently select best data for each field
        all_keys = set()
        for strategy_data in hybrid_data["hybrid_data"].values():
            if isinstance(strategy_data, dict):
                all_keys.update(strategy_data.keys())

        for key in all_keys:
            # Choose best value based on context and confidence
            best_value = self._select_best_hybrid_value(
                key, hybrid_data["hybrid_data"], weight_factors
# BRACKET_SURGEON: disabled
#             )
            if best_value is not None:
                hybrid_data["recommended_data"][key] = best_value

        # Calculate overall hybrid confidence
        confidence_scores = list(hybrid_data["confidence_breakdown"].values())
        hybrid_data["overall_confidence"] = (
            statistics.mean(confidence_scores) if confidence_scores else 0
# BRACKET_SURGEON: disabled
#         )

        return hybrid_data

    def _aggregate_text_values(self, values: List[str], weights: List[float]) -> str:
        """Aggregate text values using weighted approach"""
        if not values:
            return ""

        # For text, combine unique values or use most weighted
        if len(set(values)) == 1:
            return values[0]  # All same

        # Weight-based selection for different values
        weighted_values = list(zip(values, weights))
        weighted_values.sort(key=lambda x: x[1], reverse=True)

        # Return highest weighted, or combine if similar weights
        if len(weighted_values) > 1 and abs(weighted_values[0][1] - weighted_values[1][1]) < 0.1:
            # Similar weights, combine
            unique_values = list(dict.fromkeys(values))  # Preserve order, remove duplicates
            return " | ".join(unique_values[:3])  # Limit to top 3
        else:
            return weighted_values[0][0]

    def _calculate_consensus_confidence(self, api_results: List[Dict[str, Any]]) -> float:
        """Calculate confidence score based on consensus"""
        if len(api_results) < 2:
            return 0.5

        # Simple confidence based on number of sources and their agreement
        source_count_factor = min(len(api_results) / 5.0, 1.0)  # Max at 5 sources
        quality_factor = statistics.mean([r.get("quality_weight", 1.0) for r in api_results])

        return (source_count_factor + quality_factor) / 2.0

    def _calculate_speed_advantage(self, api_results: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate speed advantage metrics"""
        response_times = [r.get("response_time", 0) for r in api_results]
        if not response_times:
            return {"advantage": 0, "fastest_time": 0, "average_time": 0}

        fastest_time = min(response_times)
        average_time = statistics.mean(response_times)

        return {
            "advantage": ((average_time - fastest_time) / average_time if average_time > 0 else 0),
            "fastest_time": fastest_time,
            "average_time": average_time,
# BRACKET_SURGEON: disabled
#         }

    def _select_best_hybrid_value(
        self,
        key: str,
        strategy_data: Dict[str, Any],
        weight_factors: Optional[Dict[str, float]],
# BRACKET_SURGEON: disabled
#     ) -> Any:
        """Select best value for hybrid aggregation"""
        # Priority: consensus > best_quality > comprehensive
        if "consensus" in strategy_data and key in strategy_data["consensus"]:
            return strategy_data["consensus"][key]
        elif "best_quality" in strategy_data and key in strategy_data["best_quality"]:
            return strategy_data["best_quality"][key]
        elif "comprehensive" in strategy_data and key in strategy_data["comprehensive"]:
            comp_data = strategy_data["comprehensive"][key]
            if isinstance(comp_data, list) and comp_data:
                # Return highest quality value from comprehensive data
                best_item = max(comp_data, key=lambda x: x.get("quality", 0))
                return best_item.get("value")

        return None

    def _get_api_quality_weight(self, api_name: str) -> float:
        """Get quality weight for an API"""
        if api_name in self.catalog.apis:
            api = self.catalog.apis[api_name]
            return (api.quality_score + api.reliability_score) / 20.0  # Normalize to 0-1
        return 0.5  # Default weight

    def _calculate_quality_score(
        self,
        task: AggregationTask,
        api_results: List[Dict[str, Any]],
        aggregated_result: Dict[str, Any],
# BRACKET_SURGEON: disabled
#     ) -> float:
        """Calculate overall quality score for the aggregated result"""
        if not api_results:
            return 0.0

        # Factors: source count, source quality, data completeness, response time
        source_count_score = min(len(api_results) / task.min_sources, 1.0)

        avg_quality = statistics.mean([r.get("quality_weight", 0.5) for r in api_results])

        data_completeness = 1.0  # Assume complete for now
        if "combined_data" in aggregated_result:
            data_completeness = min(len(aggregated_result["combined_data"]) / 10.0, 1.0)

        avg_response_time = statistics.mean([r.get("response_time", 1.0) for r in api_results])
        speed_score = max(0, 1.0 - (avg_response_time / 10.0))  # Penalize slow responses

        # Weighted combination
        quality_score = (
            source_count_score * 0.3
            + avg_quality * 0.4
            + data_completeness * 0.2
            + speed_score * 0.1
# BRACKET_SURGEON: disabled
#         )

        return min(quality_score, 1.0)

    def _get_advantages_over_paid(self, task_name: str) -> List[str]:
        """Get advantages over paid services for specific task"""
        base_advantages = [
            "Zero subscription costs",
            "Multiple redundant sources",
            "No vendor lock-in",
            "Transparent rate limits",
            "Community-driven improvements",
# BRACKET_SURGEON: disabled
#         ]

        task_specific = {
            "advanced_content_generation": [
                "Multiple AI models combined",
                "Bias reduction through diversity",
                "Creative variety from different sources",
                "No content restrictions",
# BRACKET_SURGEON: disabled
#             ],
            "comprehensive_image_analysis": [
                "Multiple computer vision models",
                "Cross-validation of results",
                "Specialized model selection",
                "Higher accuracy through consensus",
# BRACKET_SURGEON: disabled
#             ],
            "market_intelligence": [
                "Real-time data from multiple sources",
                "Cross-referenced financial data",
                "News sentiment integration",
                "Global market coverage",
# BRACKET_SURGEON: disabled
#             ],
            "weather_intelligence": [
                "Multiple meteorological sources",
                "Consensus-based accuracy",
                "Redundant data for reliability",
                "Local and global coverage",
# BRACKET_SURGEON: disabled
#             ],
# BRACKET_SURGEON: disabled
#         }

        return base_advantages + task_specific.get(task_name, [])

    def _generate_cache_key(self, task_name: str, input_data: Dict[str, Any]) -> str:
        """Generate cache key for task and input"""
        data_str = json.dumps(input_data, sort_keys=True)
        return hashlib.md5(f"{task_name}:{data_str}".encode()).hexdigest()

    def _update_performance_history(self, task_name: str, result: Dict[str, Any]):
        """Update performance history for task"""
        if task_name not in self.performance_history:
            self.performance_history[task_name] = []

        self.performance_history[task_name].append(
            {
                "timestamp": result["timestamp"],
                "quality_score": result["quality_score"],
                "execution_time": result["execution_time"],
                "sources_used": result["sources_used"],
# BRACKET_SURGEON: disabled
#             }
# BRACKET_SURGEON: disabled
#         )

        # Keep only last 100 entries
        if len(self.performance_history[task_name]) > 100:
            self.performance_history[task_name] = self.performance_history[task_name][-100:]

    def get_performance_analytics(self) -> Dict[str, Any]:
        """Get comprehensive performance analytics"""
        analytics = {
            "total_tasks": len(self.superior_tasks),
            "executed_tasks": len(self.performance_history),
            "cache_hit_rate": 0,
            "average_quality_score": 0,
            "average_execution_time": 0,
            "task_performance": {},
# BRACKET_SURGEON: disabled
#         }

        all_quality_scores = []
        all_execution_times = []

        for task_name, history in self.performance_history.items():
            if history:
                task_quality = [h["quality_score"] for h in history]
                task_times = [h["execution_time"] for h in history]

                analytics["task_performance"][task_name] = {
                    "executions": len(history),
                    "avg_quality": statistics.mean(task_quality),
                    "avg_time": statistics.mean(task_times),
                    "quality_trend": (
                        "improving"
                        if len(task_quality) > 1 and task_quality[-1] > task_quality[0]
                        else "stable"
# BRACKET_SURGEON: disabled
#                     ),
# BRACKET_SURGEON: disabled
#                 }

                all_quality_scores.extend(task_quality)
                all_execution_times.extend(task_times)

        if all_quality_scores:
            analytics["average_quality_score"] = statistics.mean(all_quality_scores)
        if all_execution_times:
            analytics["average_execution_time"] = statistics.mean(all_execution_times)

        # Calculate cache hit rate
        total_requests = sum(len(history) for history in self.performance_history.values())
        cache_hits = sum(1 for result in self.cache.values() if result.get("from_cache", False))
        analytics["cache_hit_rate"] = (
            (cache_hits / total_requests * 100) if total_requests > 0 else 0
# BRACKET_SURGEON: disabled
#         )

        return analytics

    def create_custom_superior_task(
        self,
        name: str,
        requirement: str,
        apis: List[str],
        strategy: AggregationStrategy = AggregationStrategy.HYBRID,
# BRACKET_SURGEON: disabled
#     ) -> bool:
        """Create custom superior aggregation task"""
        task = AggregationTask(
            name=name,
            requirement=requirement,
            apis=apis,
            strategy=strategy,
            min_sources=min(2, len(apis)),
# BRACKET_SURGEON: disabled
#         )

        self.superior_tasks[name] = task
        return True

    def get_available_superior_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Get all available superior tasks with descriptions"""
        tasks_info = {}

        for task_name, task in self.superior_tasks.items():
            tasks_info[task_name] = {
                "name": task.name,
                "description": f"Superior {task.requirement} using {len(task.apis)} APIs",
                "strategy": task.strategy.value,
                "apis_count": len(task.apis),
                "min_sources": task.min_sources,
                "advantages": self._get_advantages_over_paid(task_name),
# BRACKET_SURGEON: disabled
#             }

        return tasks_info


# Convenience functions
async def create_superior_api_service() -> SuperiorAPIAggregator:
    """Create superior API aggregation service"""
    catalog = FreeAPICatalog()
    return SuperiorAPIAggregator(catalog)


async def demonstrate_superiority(requirement: str) -> Dict[str, Any]:
    """Demonstrate how free API aggregation outperforms paid services"""
    async with await create_superior_api_service() as aggregator:
        # Find matching superior task
        matching_tasks = []
        for task_name, task in aggregator.superior_tasks.items():
            if any(word in task.requirement.lower() for word in requirement.lower().split()):
                matching_tasks.append(task_name)

        if not matching_tasks:
            return {"success": False, "error": "No matching superior task found"}

        # Execute the best matching task
        best_task = matching_tasks[0]
        result = await aggregator.execute_superior_task(best_task, {"query": requirement})

        # Add comparison with paid services
        result["paid_service_comparison"] = {
            "cost_savings": "100% - completely free vs $20-100+/month",
            "feature_comparison": "Superior through aggregation",
            "reliability": "Higher through redundancy",
            "vendor_independence": "No lock-in, multiple sources",
# BRACKET_SURGEON: disabled
#         }

        return result


if __name__ == "__main__":
    # Example usage
    async def main():
        async with await create_superior_api_service() as aggregator:
            # Demonstrate superior content generation
            result = await aggregator.execute_superior_task(
                "advanced_content_generation",
                {"query": "Write a creative story about AI"},
# BRACKET_SURGEON: disabled
#             )

            print(
                f"Superior task executed with quality score: {result.get('quality_score', 0):.2f}"
# BRACKET_SURGEON: disabled
#             )
            print(f"Sources used: {result.get('sources_used', 0)}")
            print(f"Advantages: {len(result.get('advantages_over_paid', []))}")

    # asyncio.run(main())
    print("Superior API Aggregation Engine - Ready to outperform paid services")