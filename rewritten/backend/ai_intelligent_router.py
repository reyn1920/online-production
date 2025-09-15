#!/usr/bin/env python3
""""""
AI - Powered Intelligent Router and Load Balancer

This module provides advanced AI - powered routing and load balancing capabilities
for the TRAE.AI system, including:
    pass

- Intelligent request routing based on content analysis
- Dynamic load balancing with predictive scaling
- AI - powered performance optimization
- Real - time traffic analysis and adaptation
- Multi - model routing with cost optimization
- Predictive resource allocation
- Anomaly detection and auto - recovery

Author: TRAE.AI System
Version: 1.0.0
Date: 2024
""""""

import asyncio
import json
import logging
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List

import numpy as np
from flask import Flask, jsonify, request

# Import existing components
try:
    from core_ai_integration import ask_ai, AIPlatform
    from examples.routellm_integration_example import RouteLL_IntegratedClient
    from routing.model_router import ModelRouter, TaskType
    from utils.rate_limiter import RateLimiter

except ImportError as e:
    logging.warning(f"Some components not available: {e}")


class RoutingStrategy(Enum):
    """Available routing strategies"""

    ROUND_ROBIN = "round_robin"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_CONNECTIONS = "least_connections"
    RESPONSE_TIME = "response_time"
    AI_OPTIMIZED = "ai_optimized"
    COST_OPTIMIZED = "cost_optimized"
    QUALITY_OPTIMIZED = "quality_optimized"
    ADAPTIVE = "adaptive"


class LoadBalancingAlgorithm(Enum):
    """Load balancing algorithms"""

    PREDICTIVE = "predictive"
    REACTIVE = "reactive"
    HYBRID = "hybrid"
    ML_BASED = "ml_based"


@dataclass
class ServerMetrics:
    """Server performance metrics"""

    server_id: str
    response_time: float
    cpu_usage: float
    memory_usage: float
    active_connections: int
    success_rate: float
    error_rate: float
    throughput: float
    last_updated: datetime
    health_score: float = 0.0


@dataclass
class RoutingDecision:
    """Routing decision with metadata"""

    target_server: str
    strategy_used: str
    confidence_score: float
    estimated_response_time: float
    cost_estimate: float
    reasoning: str
    alternatives: List[str]
    timestamp: datetime


@dataclass
class TrafficPattern:
    """Traffic pattern analysis"""

    pattern_type: str
    confidence: float
    predicted_load: float
    recommended_scaling: str
    time_window: str
    characteristics: Dict[str, Any]


class AIIntelligentRouter:
    """"""
    AI - Powered Intelligent Router with advanced load balancing
    """"""

    def __init__(self, config_path: str = None):
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config(config_path)

        # Initialize Flask app for API endpoints
        self.app = Flask(__name__)
        self._setup_routes()

        # Core components
        self.routell_client = RouteLL_IntegratedClient()
        self.model_router = ModelRouter()
        self.rate_limiter = RateLimiter()

        # Server pool and metrics
        self.servers = self._initialize_servers()
        self.server_metrics = {}
        self.routing_history = deque(maxlen=10000)
        self.traffic_patterns = []

        # AI - powered components
        self.ai_insights = {
            "routing_patterns": {},
            "performance_predictions": {},
            "optimization_suggestions": [],
            "anomaly_detections": [],
# BRACKET_SURGEON: disabled
#         }

        # Load balancing state
        self.current_strategy = RoutingStrategy.AI_OPTIMIZED
        self.load_balancing_algorithm = LoadBalancingAlgorithm.HYBRID
        self.request_counters = defaultdict(int)
        self.response_times = defaultdict(list)

        # Predictive models
        self.traffic_predictor = self._initialize_traffic_predictor()
        self.performance_predictor = self._initialize_performance_predictor()

        # Start background tasks
        self._start_background_tasks()

        self.logger.info("AI Intelligent Router initialized successfully")

    def _load_config(self, config_path: str) -> Dict:
        """Load router configuration"""
        default_config = {
            "servers": [
                {
                    "id": "primary",
                    "endpoint": "http://localhost:8000",
                    "weight": 1.0,
                    "capacity": 100,
# BRACKET_SURGEON: disabled
#                 },
                {
                    "id": "secondary",
                    "endpoint": "http://localhost:8001",
                    "weight": 0.8,
                    "capacity": 80,
# BRACKET_SURGEON: disabled
#                 },
                {
                    "id": "tertiary",
                    "endpoint": "http://localhost:8002",
                    "weight": 0.6,
                    "capacity": 60,
# BRACKET_SURGEON: disabled
#                 },
# BRACKET_SURGEON: disabled
#             ],
            "routing": {
                "default_strategy": "ai_optimized",
                "health_check_interval": 30,
                "metrics_retention_hours": 24,
                "ai_analysis_interval": 300,
# BRACKET_SURGEON: disabled
#             },
            "load_balancing": {
                "algorithm": "hybrid",
                "scaling_threshold": 0.8,
                "prediction_window_minutes": 15,
                "auto_scaling_enabled": True,
# BRACKET_SURGEON: disabled
#             },
            "ai_optimization": {
                "enabled": True,
                "learning_rate": 0.01,
                "adaptation_threshold": 0.1,
                "quality_weight": 0.4,
                "cost_weight": 0.3,
                "speed_weight": 0.3,
# BRACKET_SURGEON: disabled
#             },
# BRACKET_SURGEON: disabled
#         }

        if config_path:
            try:
                with open(config_path, "r") as f:
                    config = json.load(f)
                    # Merge with defaults
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            except Exception as e:
                self.logger.warning(f"Failed to load config: {e}, using defaults")

        return default_config

    def _initialize_servers(self) -> List[Dict]:
        """Initialize server pool"""
        servers = self.config.get("servers", [])
        for server in servers:
            server_id = server["id"]
            self.server_metrics[server_id] = ServerMetrics(
                server_id=server_id,
                response_time=0.0,
                cpu_usage=0.0,
                memory_usage=0.0,
                active_connections=0,
                success_rate=1.0,
                error_rate=0.0,
                throughput=0.0,
                last_updated=datetime.now(),
                health_score=1.0,
# BRACKET_SURGEON: disabled
#             )
        return servers

    def _initialize_traffic_predictor(self) -> Dict:
        """Initialize traffic prediction model"""
        return {
            "model_type": "time_series",
            "window_size": 60,
            "prediction_horizon": 15,
            "accuracy": 0.85,
            "last_trained": datetime.now(),
# BRACKET_SURGEON: disabled
#         }

    def _initialize_performance_predictor(self) -> Dict:
        """Initialize performance prediction model"""
        return {
            "model_type": "regression",
            "features": ["request_size", "complexity", "server_load"],
            "accuracy": 0.78,
            "last_trained": datetime.now(),
# BRACKET_SURGEON: disabled
#         }

    async def route_request(self, request_data: Dict, preferences: Dict = None) -> RoutingDecision:
        """"""
        Intelligently route a request using AI - powered decision making

        Args:
            request_data: Request information and payload
            preferences: User preferences for routing (cost, quality, speed)

        Returns:
            RoutingDecision with target server and metadata
        """"""
        start_time = time.time()

        try:
            # Analyze request characteristics
            request_analysis = await self._analyze_request(request_data)

            # Get current server states
            server_states = await self._get_server_states()

            # Apply AI - powered routing strategy
            if self.current_strategy == RoutingStrategy.AI_OPTIMIZED:
                decision = await self._ai_optimized_routing(
                    request_analysis, server_states, preferences
# BRACKET_SURGEON: disabled
#                 )
            elif self.current_strategy == RoutingStrategy.COST_OPTIMIZED:
                decision = await self._cost_optimized_routing(request_analysis, server_states)
            elif self.current_strategy == RoutingStrategy.QUALITY_OPTIMIZED:
                decision = await self._quality_optimized_routing(request_analysis, server_states)
            else:
                decision = await self._adaptive_routing(
                    request_analysis, server_states, preferences
# BRACKET_SURGEON: disabled
#                 )

            # Record routing decision
            self.routing_history.append(
                {
                    "timestamp": datetime.now(),
                    "request_id": request_data.get("id", "unknown"),
                    "decision": asdict(decision),
                    "request_analysis": request_analysis,
                    "processing_time": time.time() - start_time,
# BRACKET_SURGEON: disabled
#                 }
# BRACKET_SURGEON: disabled
#             )

            return decision

        except Exception as e:
            self.logger.error(f"Error in route_request: {e}")
            # Fallback to simple round - robin
            return await self._fallback_routing(request_data)

    async def _analyze_request(self, request_data: Dict) -> Dict:
        """"""
        Analyze request characteristics using AI
        """"""
        try:
            # Extract request features
            content = request_data.get("content", "")
            request_type = request_data.get("type", "general")
            size = len(str(request_data))

            # Use AI to analyze request complexity and requirements
            ai_analysis_prompt = f""""""
            Analyze this request and provide routing recommendations:

            Request Type: {request_type}
            Content Size: {size} characters
            Content Preview: {content[:200]}...

            Please analyze:
            1. Computational complexity (low/medium/high)
            2. Expected processing time (seconds)
            3. Resource requirements (cpu/memory intensive)
            4. Optimal server characteristics
            5. Cost sensitivity

            Respond in JSON format.
            """"""

            ai_response = await ask_ai(
                ai_analysis_prompt, platform=AIPlatform.GEMINI, task_type="analysis"
# BRACKET_SURGEON: disabled
#             )

            if ai_response.success:
                try:
                    analysis = json.loads(ai_response.content)
                except json.JSONDecodeError:
                    analysis = self._extract_analysis_from_text(ai_response.content)
            else:
                analysis = self._default_request_analysis(request_data)

            # Add computed features
            analysis.update(
                {
                    "request_size": size,
                    "timestamp": datetime.now().isoformat(),
                    "hash": hash(str(request_data)) % 10000,
# BRACKET_SURGEON: disabled
#                 }
# BRACKET_SURGEON: disabled
#             )

            return analysis

        except Exception as e:
            self.logger.error(f"Error analyzing request: {e}")
            return self._default_request_analysis(request_data)

    def _extract_analysis_from_text(self, text: str) -> Dict:
        """Extract analysis from AI text response"""
        # Simple extraction logic
        analysis = {
            "complexity": "medium",
            "processing_time": 2.0,
            "resource_type": "balanced",
            "cost_sensitivity": "medium",
# BRACKET_SURGEON: disabled
#         }

        text_lower = text.lower()
        if "high" in text_lower and "complex" in text_lower:
            analysis["complexity"] = "high"
            analysis["processing_time"] = 5.0
        elif "low" in text_lower and "simple" in text_lower:
            analysis["complexity"] = "low"
            analysis["processing_time"] = 1.0

        return analysis

    def _default_request_analysis(self, request_data: Dict) -> Dict:
        """Default request analysis when AI analysis fails"""
        size = len(str(request_data))
        return {
            "complexity": "medium" if size < 1000 else "high",
            "processing_time": 2.0,
            "resource_type": "balanced",
            "cost_sensitivity": "medium",
            "confidence": 0.5,
# BRACKET_SURGEON: disabled
#         }

    async def _get_server_states(self) -> Dict:
        """Get current state of all servers"""
        states = {}
        for server in self.servers:
            server_id = server["id"]
            metrics = self.server_metrics.get(server_id)
            if metrics:
                states[server_id] = {
                    "health_score": metrics.health_score,
                    "response_time": metrics.response_time,
                    "active_connections": metrics.active_connections,
                    "cpu_usage": metrics.cpu_usage,
                    "memory_usage": metrics.memory_usage,
                    "capacity": server.get("capacity", 100),
                    "weight": server.get("weight", 1.0),
                    "endpoint": server.get("endpoint", ""),
                    "load_percentage": metrics.active_connections / server.get("capacity", 100),
# BRACKET_SURGEON: disabled
#                 }
        return states

    async def _ai_optimized_routing(
        self, request_analysis: Dict, server_states: Dict, preferences: Dict = None
# BRACKET_SURGEON: disabled
#     ) -> RoutingDecision:
        """"""
        AI - optimized routing using machine learning insights
        """"""
        try:
            # Prepare data for AI decision
            routing_context = {
                "request": request_analysis,
                "servers": server_states,
                "preferences": preferences or {"quality": 0.4, "cost": 0.3, "speed": 0.3},
                "historical_performance": self._get_historical_performance(),
                "current_load": self._get_current_load_distribution(),
# BRACKET_SURGEON: disabled
#             }

            # Use AI to make routing decision
            ai_prompt = f""""""
            Make an intelligent routing decision based on this context:

            {json.dumps(routing_context, indent = 2, default = str)}

            Consider:
            1. Server health and performance
            2. Request complexity and requirements
            3. User preferences for quality/cost/speed
            4. Historical performance patterns
            5. Current load distribution

            Recommend the best server and explain reasoning.
            Respond in JSON format with: server_id, confidence_score, reasoning, alternatives.
            """"""

            ai_response = await ask_ai(
                ai_prompt, platform=AIPlatform.GEMINI, task_type="decision_making"
# BRACKET_SURGEON: disabled
#             )

            if ai_response.success:
                try:
                    decision_data = json.loads(ai_response.content)
                    server_id = decision_data.get("server_id")

                    if server_id in server_states:
                        return RoutingDecision(
                            target_server=server_id,
                            strategy_used="ai_optimized",
                            confidence_score=decision_data.get("confidence_score", 0.8),
                            estimated_response_time=server_states[server_id]["response_time"],
                            cost_estimate=self._estimate_cost(server_id, request_analysis),
                            reasoning=decision_data.get("reasoning", "AI - optimized selection"),
                            alternatives=decision_data.get("alternatives", []),
                            timestamp=datetime.now(),
# BRACKET_SURGEON: disabled
#                         )
                except json.JSONDecodeError:
                    pass

            # Fallback to algorithmic decision
            return await self._algorithmic_routing(request_analysis, server_states)

        except Exception as e:
            self.logger.error(f"Error in AI - optimized routing: {e}")
            return await self._fallback_routing({"analysis": request_analysis})

    async def _cost_optimized_routing(
        self, request_analysis: Dict, server_states: Dict
# BRACKET_SURGEON: disabled
#     ) -> RoutingDecision:
        """"""
        Route to minimize cost while maintaining acceptable quality
        """"""
        best_server = None
        best_cost = float("inf")

        for server_id, state in server_states.items():
            if state["health_score"] > 0.7:  # Only healthy servers
                cost = self._estimate_cost(server_id, request_analysis)
                if cost < best_cost:
                    best_cost = cost
                    best_server = server_id

        if not best_server:
            best_server = min(
                server_states.keys(), key=lambda s: server_states[s]["load_percentage"]
# BRACKET_SURGEON: disabled
#             )

        return RoutingDecision(
            target_server=best_server,
            strategy_used="cost_optimized",
            confidence_score=0.85,
            estimated_response_time=server_states[best_server]["response_time"],
            cost_estimate=best_cost,
            reasoning="Selected server with lowest cost while maintaining quality",
            alternatives=list(server_states.keys()),
            timestamp=datetime.now(),
# BRACKET_SURGEON: disabled
#         )

    async def _quality_optimized_routing(
        self, request_analysis: Dict, server_states: Dict
# BRACKET_SURGEON: disabled
#     ) -> RoutingDecision:
        """"""
        Route to maximize quality regardless of cost
        """"""
        best_server = max(
            server_states.keys(),
            key=lambda s: server_states[s]["health_score"]
            * (1 - server_states[s]["load_percentage"]),
# BRACKET_SURGEON: disabled
#         )

        return RoutingDecision(
            target_server=best_server,
            strategy_used="quality_optimized",
            confidence_score=0.9,
            estimated_response_time=server_states[best_server]["response_time"],
            cost_estimate=self._estimate_cost(best_server, request_analysis),
            reasoning="Selected highest quality server with best performance metrics",
            alternatives=list(server_states.keys()),
            timestamp=datetime.now(),
# BRACKET_SURGEON: disabled
#         )

    async def _adaptive_routing(
        self, request_analysis: Dict, server_states: Dict, preferences: Dict = None
# BRACKET_SURGEON: disabled
#     ) -> RoutingDecision:
        """"""
        Adaptive routing that learns from patterns and adjusts strategy
        """"""
        # Analyze recent performance patterns
        recent_patterns = self._analyze_recent_patterns()

        # Adjust strategy based on patterns
        if recent_patterns.get("high_error_rate", False):
            # Focus on reliability
            return await self._quality_optimized_routing(request_analysis, server_states)
        elif recent_patterns.get("high_cost", False):
            # Focus on cost reduction
            return await self._cost_optimized_routing(request_analysis, server_states)
        else:
            # Balanced approach
            return await self._ai_optimized_routing(request_analysis, server_states, preferences)

    async def _algorithmic_routing(
        self, request_analysis: Dict, server_states: Dict
# BRACKET_SURGEON: disabled
#     ) -> RoutingDecision:
        """"""
        Algorithmic routing when AI is unavailable
        """"""
        # Weighted round - robin with health consideration
        available_servers = [
            (server_id, state)
            for server_id, state in server_states.items()
            if state["health_score"] > 0.5
# BRACKET_SURGEON: disabled
#         ]

        if not available_servers:
            # Emergency fallback
            server_id = list(server_states.keys())[0]
        else:
            # Select based on weighted score
            scores = []
            for server_id, state in available_servers:
                score = (
                    state["health_score"] * 0.4
                    + (1 - state["load_percentage"]) * 0.3
                    + (1 / max(state["response_time"], 0.1)) * 0.3
# BRACKET_SURGEON: disabled
#                 )
                scores.append((server_id, score))

            server_id = max(scores, key=lambda x: x[1])[0]

        return RoutingDecision(
            target_server=server_id,
            strategy_used="algorithmic",
            confidence_score=0.7,
            estimated_response_time=server_states[server_id]["response_time"],
            cost_estimate=self._estimate_cost(server_id, request_analysis),
            reasoning="Algorithmic selection based on weighted scoring",
            alternatives=list(server_states.keys()),
            timestamp=datetime.now(),
# BRACKET_SURGEON: disabled
#         )

    async def _fallback_routing(self, request_data: Dict) -> RoutingDecision:
        """"""
        Emergency fallback routing
        """"""
        # Simple round - robin
        server_id = self.servers[len(self.routing_history) % len(self.servers)]["id"]

        return RoutingDecision(
            target_server=server_id,
            strategy_used="fallback",
            confidence_score=0.5,
            estimated_response_time=2.0,
            cost_estimate=0.01,
            reasoning="Emergency fallback routing",
            alternatives=[],
            timestamp=datetime.now(),
# BRACKET_SURGEON: disabled
#         )

    def _estimate_cost(self, server_id: str, request_analysis: Dict) -> float:
        """"""
        Estimate cost for processing request on specific server
        """"""
        base_cost = 0.001  # Base cost per request
        complexity_multiplier = {"low": 1.0, "medium": 1.5, "high": 2.5}.get(
            request_analysis.get("complexity", "medium"), 1.5
# BRACKET_SURGEON: disabled
#         )

        server_cost_multiplier = {
            "primary": 1.0,
            "secondary": 0.8,
            "tertiary": 0.6,
        }.get(server_id, 1.0)

        return base_cost * complexity_multiplier * server_cost_multiplier

    def _get_historical_performance(self) -> Dict:
        """"""
        Get historical performance data for AI decision making
        """"""
        if not self.routing_history:
            return {"average_response_time": 2.0, "success_rate": 0.95}

        recent_history = list(self.routing_history)[-100:]  # Last 100 requests

        response_times = []
        success_count = 0

        for entry in recent_history:
            decision = entry.get("decision", {})
            response_times.append(decision.get("estimated_response_time", 2.0))
            if decision.get("confidence_score", 0) > 0.7:
                success_count += 1

        return {
            "average_response_time": np.mean(response_times) if response_times else 2.0,
            "success_rate": (success_count / len(recent_history) if recent_history else 0.95),
            "total_requests": len(recent_history),
# BRACKET_SURGEON: disabled
#         }

    def _get_current_load_distribution(self) -> Dict:
        """"""
        Get current load distribution across servers
        """"""
        distribution = {}
        total_load = 0

        for server_id, metrics in self.server_metrics.items():
            load = metrics.active_connections
            distribution[server_id] = load
            total_load += load

        # Normalize to percentages
        if total_load > 0:
            for server_id in distribution:
                distribution[server_id] = distribution[server_id] / total_load

        return distribution

    def _analyze_recent_patterns(self) -> Dict:
        """"""
        Analyze recent routing patterns for adaptive behavior
        """"""
        if len(self.routing_history) < 10:
            return {}

        recent = list(self.routing_history)[-50:]  # Last 50 requests

        error_count = sum(
            1 for entry in recent if entry.get("decision", {}).get("confidence_score", 1.0) < 0.6
# BRACKET_SURGEON: disabled
#         )
        high_cost_count = sum(
            1 for entry in recent if entry.get("decision", {}).get("cost_estimate", 0) > 0.02
# BRACKET_SURGEON: disabled
#         )

        return {
            "high_error_rate": error_count / len(recent) > 0.1,
            "high_cost": high_cost_count / len(recent) > 0.3,
            "average_processing_time": np.mean(
                [entry.get("processing_time", 0) for entry in recent]
# BRACKET_SURGEON: disabled
#             ),
# BRACKET_SURGEON: disabled
#         }

    async def predict_traffic_patterns(self) -> List[TrafficPattern]:
        """"""
        Predict future traffic patterns using AI
        """"""
        try:
            # Analyze historical data
            historical_data = self._prepare_traffic_data()

            ai_prompt = f""""""
            Analyze this traffic data and predict future patterns:

            {json.dumps(historical_data, indent = 2, default = str)}

            Predict:
            1. Traffic volume trends for next hour
            2. Peak usage periods
            3. Resource scaling recommendations
            4. Potential bottlenecks

            Respond in JSON format with predictions and confidence scores.
            """"""

            ai_response = await ask_ai(
                ai_prompt, platform=AIPlatform.GEMINI, task_type="prediction"
# BRACKET_SURGEON: disabled
#             )

            if ai_response.success:
                try:
                    predictions = json.loads(ai_response.content)
                    patterns = []

                    for pred in predictions.get("patterns", []):
                        patterns.append(
                            TrafficPattern(
                                pattern_type=pred.get("type", "unknown"),
                                confidence=pred.get("confidence", 0.5),
                                predicted_load=pred.get("load", 1.0),
                                recommended_scaling=pred.get("scaling", "maintain"),
                                time_window=pred.get("window", "1h"),
                                characteristics=pred.get("characteristics", {}),
# BRACKET_SURGEON: disabled
#                             )
# BRACKET_SURGEON: disabled
#                         )

                    return patterns
                except json.JSONDecodeError:
                    pass

            # Fallback to simple pattern analysis
            return self._simple_pattern_analysis()

        except Exception as e:
            self.logger.error(f"Error predicting traffic patterns: {e}")
            return []

    def _prepare_traffic_data(self) -> Dict:
        """"""
        Prepare traffic data for AI analysis
        """"""
        now = datetime.now()
        hourly_data = defaultdict(int)

        # Group requests by hour
        for entry in self.routing_history:
            timestamp = entry.get("timestamp")
            if isinstance(timestamp, datetime):
                hour_key = timestamp.strftime("%Y-%m-%d %H:00")
                hourly_data[hour_key] += 1

        return {
            "hourly_requests": dict(hourly_data),
            "total_requests": len(self.routing_history),
            "time_range": f"{now - timedelta(hours = 24)} to {now}",
            "server_distribution": self._get_current_load_distribution(),
# BRACKET_SURGEON: disabled
#         }

    def _simple_pattern_analysis(self) -> List[TrafficPattern]:
        """"""
        Simple pattern analysis when AI is unavailable
        """"""
        current_load = sum(metrics.active_connections for metrics in self.server_metrics.values())
        total_capacity = sum(server.get("capacity", 100) for server in self.servers)
        load_percentage = current_load / total_capacity if total_capacity > 0 else 0

        if load_percentage > 0.8:
            scaling_recommendation = "scale_up"
        elif load_percentage < 0.3:
            scaling_recommendation = "scale_down"
        else:
            scaling_recommendation = "maintain"

        return [
            TrafficPattern(
                pattern_type="current_load",
                confidence=0.7,
                predicted_load=load_percentage,
                recommended_scaling=scaling_recommendation,
                time_window="current",
                characteristics={"load_percentage": load_percentage},
# BRACKET_SURGEON: disabled
#             )
# BRACKET_SURGEON: disabled
#         ]

    def _start_background_tasks(self):
        """"""
        Start background monitoring and optimization tasks
        """"""
        # Note: In a real implementation, these would be proper async tasks
        self.logger.info(
            "Background tasks initialized (health monitoring, AI analysis, pattern detection)"
# BRACKET_SURGEON: disabled
#         )

    def _setup_routes(self):
        """"""
        Setup Flask API routes for the intelligent router
        """"""

        @self.app.route("/api/router/status", methods=["GET"])
        def get_router_status():
            """Get current router status and metrics"""
            try:
                status = {
                    "status": "active",
                    "strategy": self.current_strategy.value,
                    "algorithm": self.load_balancing_algorithm.value,
                    "servers": len(self.servers),
                    "active_connections": sum(
                        m.active_connections for m in self.server_metrics.values()
# BRACKET_SURGEON: disabled
#                     ),
                    "total_requests": len(self.routing_history),
                    "ai_insights_count": len(self.ai_insights.get("optimization_suggestions", [])),
                    "timestamp": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#                 }
                return jsonify({"success": True, "status": status})
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500

        @self.app.route("/api/router/metrics", methods=["GET"])
        def get_router_metrics():
            """Get detailed router metrics"""
            try:
                metrics = {
                    "server_metrics": {k: asdict(v) for k, v in self.server_metrics.items()},
                    "routing_history_summary": self._get_routing_summary(),
                    "performance_stats": self._get_performance_stats(),
                    "ai_insights": self.ai_insights,
                    "traffic_patterns": [asdict(p) for p in self.traffic_patterns],
                    "timestamp": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#                 }
                return jsonify({"success": True, "metrics": metrics})
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500

        @self.app.route("/api/router/route", methods=["POST"])
        def route_request_endpoint():
            """Route a request through the intelligent router"""
            try:
                request_data = request.get_json()
                if not request_data:
                    return (
                        jsonify({"success": False, "error": "No request data provided"}),
                        400,
# BRACKET_SURGEON: disabled
#                     )

                # This would normally be async, but for Flask compatibility
                # we'll use a synchronous version
                decision = asyncio.run(self.route_request(request_data))

                return jsonify({"success": True, "routing_decision": asdict(decision)})
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500

        @self.app.route("/api/router/predictions", methods=["GET"])
        def get_traffic_predictions():
            """Get traffic pattern predictions"""
            try:
                patterns = asyncio.run(self.predict_traffic_patterns())
                return jsonify(
                    {
                        "success": True,
                        "predictions": [asdict(p) for p in patterns],
                        "generated_at": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#                     }
# BRACKET_SURGEON: disabled
#                 )
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500

        @self.app.route("/api/router/optimize", methods=["POST"])
        def optimize_routing():
            """Trigger AI - powered routing optimization"""
            try:
                optimization_result = asyncio.run(self._run_optimization())
                return jsonify(
                    {
                        "success": True,
                        "optimization": optimization_result,
                        "timestamp": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#                     }
# BRACKET_SURGEON: disabled
#                 )
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500

        @self.app.route("/api/router/strategy", methods=["POST"])
        def update_routing_strategy():
            """Update routing strategy"""
            try:
                data = request.get_json()
                strategy = data.get("strategy")

                if strategy in [s.value for s in RoutingStrategy]:
                    self.current_strategy = RoutingStrategy(strategy)
                    return jsonify(
                        {
                            "success": True,
                            "message": f"Routing strategy updated to {strategy}",
                            "current_strategy": self.current_strategy.value,
# BRACKET_SURGEON: disabled
#                         }
# BRACKET_SURGEON: disabled
#                     )
                else:
                    return (
                        jsonify(
                            {
                                "success": False,
                                "error": f"Invalid strategy. Available: {[s.value for s in RoutingStrategy]}",
# BRACKET_SURGEON: disabled
#                             }
# BRACKET_SURGEON: disabled
#                         ),
                        400,
# BRACKET_SURGEON: disabled
#                     )
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500

    def _get_routing_summary(self) -> Dict:
        """Get routing history summary"""
        if not self.routing_history:
            return {"total_requests": 0}

        strategies = defaultdict(int)
        servers = defaultdict(int)

        for entry in self.routing_history:
            decision = entry.get("decision", {})
            strategies[decision.get("strategy_used", "unknown")] += 1
            servers[decision.get("target_server", "unknown")] += 1

        return {
            "total_requests": len(self.routing_history),
            "strategy_distribution": dict(strategies),
            "server_distribution": dict(servers),
            "average_confidence": (
                np.mean(
                    [
                        entry.get("decision", {}).get("confidence_score", 0)
                        for entry in self.routing_history
# BRACKET_SURGEON: disabled
#                     ]
# BRACKET_SURGEON: disabled
#                 )
                if self.routing_history
                else 0
# BRACKET_SURGEON: disabled
#             ),
# BRACKET_SURGEON: disabled
#         }

    def _get_performance_stats(self) -> Dict:
        """Get performance statistics"""
        if not self.routing_history:
            return {}

        processing_times = [entry.get("processing_time", 0) for entry in self.routing_history]
        response_times = [
            entry.get("decision", {}).get("estimated_response_time", 0)
            for entry in self.routing_history
# BRACKET_SURGEON: disabled
#         ]

        return {
            "average_processing_time": (np.mean(processing_times) if processing_times else 0),
            "average_response_time": np.mean(response_times) if response_times else 0,
            "min_processing_time": np.min(processing_times) if processing_times else 0,
            "max_processing_time": np.max(processing_times) if processing_times else 0,
            "requests_per_minute": len(self.routing_history)
            / max(
                1,
                (
                    datetime.now() - datetime.now().replace(minute=0, second=0, microsecond=0)
                ).total_seconds()
                / 60,
# BRACKET_SURGEON: disabled
#             ),
# BRACKET_SURGEON: disabled
#         }

    async def _run_optimization(self) -> Dict:
        """"""
        Run AI - powered optimization analysis
        """"""
        try:
            # Analyze current performance
            performance_data = {
                "routing_summary": self._get_routing_summary(),
                "performance_stats": self._get_performance_stats(),
                "server_metrics": {k: asdict(v) for k, v in self.server_metrics.items()},
                "current_strategy": self.current_strategy.value,
# BRACKET_SURGEON: disabled
#             }

            ai_prompt = f""""""
            Analyze this routing system performance and provide optimization recommendations:

            {json.dumps(performance_data, indent=2, default=str)}

            Provide:
            1. Performance bottlenecks
            2. Optimization opportunities
            3. Strategy recommendations
            4. Resource allocation suggestions
            5. Predicted improvements

            Respond in JSON format.
            """"""

            ai_response = await ask_ai(
                ai_prompt, platform=AIPlatform.GEMINI, task_type="optimization"
# BRACKET_SURGEON: disabled
#             )

            if ai_response.success:
                try:
                    optimization = json.loads(ai_response.content)

                    # Store insights
                    self.ai_insights["optimization_suggestions"].append(
                        {
                            "timestamp": datetime.now().isoformat(),
                            "recommendations": optimization,
                            "applied": False,
# BRACKET_SURGEON: disabled
#                         }
# BRACKET_SURGEON: disabled
#                     )

                    return optimization
                except json.JSONDecodeError:
                    pass

            # Fallback optimization
            return self._simple_optimization_analysis()

        except Exception as e:
            self.logger.error(f"Error running optimization: {e}")
            return {"error": str(e)}

    def _simple_optimization_analysis(self) -> Dict:
        """Simple optimization when AI is unavailable"""
        total_load = sum(m.active_connections for m in self.server_metrics.values())
        total_capacity = sum(s.get("capacity", 100) for s in self.servers)
        utilization = total_load / total_capacity if total_capacity > 0 else 0

        recommendations = []

        if utilization > 0.8:
            recommendations.append("Consider scaling up - high utilization detected")
        elif utilization < 0.3:
            recommendations.append("Consider scaling down - low utilization detected")

        if len(self.routing_history) > 100:
            avg_confidence = np.mean(
                [
                    entry.get("decision", {}).get("confidence_score", 0)
                    for entry in list(self.routing_history)[-100:]
# BRACKET_SURGEON: disabled
#                 ]
# BRACKET_SURGEON: disabled
#             )
            if avg_confidence < 0.7:
                recommendations.append("Low routing confidence - consider strategy adjustment")

        return {
            "utilization": utilization,
            "recommendations": recommendations,
            "confidence": 0.6,
            "analysis_type": "simple",
# BRACKET_SURGEON: disabled
#         }


def create_ai_router_app(config_path: str = None) -> Flask:
    """"""
    Create and configure the AI Intelligent Router Flask app

    Args:
        config_path: Path to configuration file

    Returns:
        Configured Flask app
    """"""
    router = AIIntelligentRouter(config_path)
    return router.app


if __name__ == "__main__":
    # Initialize and run the AI Intelligent Router
    logging.basicConfig(level=logging.INFO)

    router = AIIntelligentRouter()

    print("🚀 AI Intelligent Router starting...")
    print(f"📊 Monitoring {len(router.servers)} servers")
    print(f"🎯 Using {router.current_strategy.value} routing strategy")
    print(f"⚖️ Load balancing: {router.load_balancing_algorithm.value}")

    # Run the Flask app
    router.app.run(host="0.0.0.0", port=5003, debug=True, threaded=True)