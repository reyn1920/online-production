#!/usr / bin / env python3
"""
Intelligent Scaling Policies for TRAE AI Application
Implements dynamic scaling based on multiple metrics and machine learning predictions
"""

import asyncio
import json
import logging
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple

import aiohttp
import docker
import numpy as np
import yaml
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

# Configure logging
logging.basicConfig(
    level = logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ScalingAction(Enum):
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    NO_ACTION = "no_action"
    EMERGENCY_SCALE = "emergency_scale"


class MetricType(Enum):
    CPU_UTILIZATION = "cpu_utilization_percent"
    MEMORY_UTILIZATION = "memory_utilization_percent"
    REQUEST_RATE = "http_requests_per_second"
    RESPONSE_TIME = "http_request_duration_p95"
    ERROR_RATE = "http_error_rate_percent"
    QUEUE_SIZE = "model_generation_queue_size"
    ACTIVE_CONNECTIONS = "database_connections_active"
    CACHE_HIT_RATE = "cache_hit_rate_percent"

@dataclass


class ScalingRule:
    name: str
    service: str
    metric_type: MetricType
    scale_up_threshold: float
    scale_down_threshold: float
    min_replicas: int
    max_replicas: int
    cooldown_seconds: int
    weight: float = 1.0
    enabled: bool = True
    emergency_threshold: Optional[float] = None

@dataclass


class MetricData:
    timestamp: datetime
    value: float
    service: str
    metric_type: MetricType

@dataclass


class ScalingDecision:
    service: str
    action: ScalingAction
    current_replicas: int
    target_replicas: int
    reason: str
    confidence: float
    metrics_used: List[str]


class PrometheusClient:
    """Client for querying Prometheus metrics"""


    def __init__(self, prometheus_url: str = "http://prometheus:9090"):
        self.base_url = prometheus_url
        self.session = None


    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self


    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()


    async def query_metric(self, query: str) -> Dict:
        """Query Prometheus for a specific metric"""
        url = f"{self.base_url}/api / v1 / query"
        params = {"query": query}

        try:
            async with self.session.get(url, params = params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("data", {})
                else:
                    logger.error(f"Prometheus query failed: {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"Error querying Prometheus: {e}")
            return {}


    async def query_range(
        self, query: str, start: datetime, end: datetime, step: str = "1m"
    ) -> Dict:
        """Query Prometheus for a range of data"""
        url = f"{self.base_url}/api / v1 / query_range"
        params = {
            "query": query,
                "start": start.timestamp(),
                "end": end.timestamp(),
                "step": step,
                }

        try:
            async with self.session.get(url, params = params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("data", {})
                else:
                    logger.error(f"Prometheus range query failed: {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"Error querying Prometheus range: {e}")
            return {}


class PredictiveScaler:
    """Machine learning - based predictive scaling"""


    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.historical_data = {}
        self.prediction_window = 300  # 5 minutes ahead


    def add_historical_data(
        self, service: str, metric_type: MetricType, data: List[MetricData]
    ):
        """Add historical data for training"""
        key = f"{service}_{metric_type.value}"
        if key not in self.historical_data:
            self.historical_data[key] = []

        self.historical_data[key].extend(data)
        # Keep only last 24 hours of data
        cutoff = datetime.now() - timedelta(hours = 24)
        self.historical_data[key] = [
            d for d in self.historical_data[key] if d.timestamp > cutoff
        ]


    def train_model(self, service: str, metric_type: MetricType):
        """Train prediction model for a specific service and metric"""
        key = f"{service}_{metric_type.value}"
        if key not in self.historical_data or len(self.historical_data[key]) < 10:
            return False

        data = self.historical_data[key]
        data.sort(key = lambda x: x.timestamp)

        # Prepare features: time - based features and lagged values
        X = []
        y = []

        for i in range(5, len(data)):  # Need at least 5 previous points
            # Time - based features
            timestamp = data[i].timestamp
            hour = timestamp.hour
            day_of_week = timestamp.weekday()
            minute = timestamp.minute

            # Lagged values
            lag_values = [data[j].value for j in range(i - 5, i)]

            # Trend features
            recent_trend = np.mean([data[j].value for j in range(i - 3, i)])
            long_trend = np.mean([data[j].value for j in range(i - 5, i)])

            features = [
                hour,
                    day_of_week,
                    minute,
                    recent_trend,
                    long_trend,
                    ] + lag_values
            X.append(features)
            y.append(data[i].value)

        if len(X) < 5:
            return False

        X = np.array(X)
        y = np.array(y)

        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Train model
        model = LinearRegression()
        model.fit(X_scaled, y)

        self.models[key] = model
        self.scalers[key] = scaler

        logger.info(f"Trained prediction model for {key}")
        return True


    def predict_future_load(
        self, service: str, metric_type: MetricType, current_data: List[MetricData]
    ) -> Optional[float]:
        """Predict future load for a service"""
        key = f"{service}_{metric_type.value}"
        if key not in self.models or len(current_data) < 5:
            return None

        # Prepare features for prediction
        future_time = datetime.now() + timedelta(seconds = self.prediction_window)
        hour = future_time.hour
        day_of_week = future_time.weekday()
        minute = future_time.minute

        # Use last 5 data points
        current_data.sort(key = lambda x: x.timestamp)
        lag_values = [d.value for d in current_data[-5:]]

        recent_trend = np.mean([d.value for d in current_data[-3:]])
        long_trend = np.mean([d.value for d in current_data[-5:]])

        features = np.array(
            [[hour, day_of_week, minute, recent_trend, long_trend] + lag_values]
        )
        features_scaled = self.scalers[key].transform(features)

        prediction = self.models[key].predict(features_scaled)[0]
        return max(0, prediction)  # Ensure non - negative prediction


class IntelligentScalingEngine:
    """Main scaling engine with intelligent decision making"""


    def __init__(self, config_path: str = "/app / config / scaling - rules.yaml"):
        self.config_path = config_path
        self.scaling_rules = []
        self.last_scaling_actions = {}
        self.prometheus_client = None
        self.docker_client = docker.from_env()
        self.predictive_scaler = PredictiveScaler()
        self.load_config()


    def load_config(self):
        """Load scaling configuration from YAML file"""
        try:
            with open(self.config_path, "r") as f:
                config = yaml.safe_load(f)

            self.scaling_rules = []
            for rule_config in config.get("scaling_rules", []):
                rule = ScalingRule(
                    name = rule_config["name"],
                        service = rule_config["service"],
                        metric_type = MetricType(rule_config["metric_type"]),
                        scale_up_threshold = rule_config["scale_up_threshold"],
                        scale_down_threshold = rule_config["scale_down_threshold"],
                        min_replicas = rule_config.get("min_replicas", 1),
                        max_replicas = rule_config.get("max_replicas", 10),
                        cooldown_seconds = rule_config.get("cooldown_seconds", 300),
                        weight = rule_config.get("weight", 1.0),
                        enabled = rule_config.get("enabled", True),
                        emergency_threshold = rule_config.get("emergency_threshold"),
                        )
                self.scaling_rules.append(rule)

            logger.info(f"Loaded {len(self.scaling_rules)} scaling rules")
        except Exception as e:
            logger.error(f"Error loading scaling config: {e}")
            self._load_default_rules()


    def _load_default_rules(self):
        """Load default scaling rules if config file is not available"""
        self.scaling_rules = [
            ScalingRule(
                name="api_cpu_scaling",
                    service="api",
                    metric_type = MetricType.CPU_UTILIZATION,
                    scale_up_threshold = 70.0,
                    scale_down_threshold = 30.0,
                    min_replicas = 2,
                    max_replicas = 10,
                    cooldown_seconds = 300,
                    emergency_threshold = 90.0,
                    ),
                ScalingRule(
                name="api_memory_scaling",
                    service="api",
                    metric_type = MetricType.MEMORY_UTILIZATION,
                    scale_up_threshold = 80.0,
                    scale_down_threshold = 40.0,
                    min_replicas = 2,
                    max_replicas = 10,
                    cooldown_seconds = 300,
                    emergency_threshold = 95.0,
                    ),
                ScalingRule(
                name="content_queue_scaling",
                    service="content - agent",
                    metric_type = MetricType.QUEUE_SIZE,
                    scale_up_threshold = 15.0,
                    scale_down_threshold = 5.0,
                    min_replicas = 1,
                    max_replicas = 8,
                    cooldown_seconds = 180,
                    weight = 1.5,
                    ),
                ]


    async def get_current_replicas(self, service: str) -> int:
        """Get current number of replicas for a service"""
        try:
            containers = self.docker_client.containers.list(
                filters={"label": f"com.docker.compose.service={service}"}
            )
            return len([c for c in containers if c.status == "running"])
        except Exception as e:
            logger.error(f"Error getting replica count for {service}: {e}")
            return 1


    async def scale_service(self, service: str, target_replicas: int) -> bool:
        """Scale a service to target number of replicas"""
        try:
            # Use docker - compose to scale the service
            import subprocess

            result = subprocess.run(
                [
                    "docker - compose",
                        "-f",
                        "docker - compose.scaling.yml",
                        "up",
                        "--scale",
                        f"{service}={target_replicas}",
                        "-d",
                        ],
                    capture_output = True,
                    text = True,
                    )

            if result.returncode == 0:
                logger.info(
                    f"Successfully scaled {service} to {target_replicas} replicas"
                )
                return True
            else:
                logger.error(f"Failed to scale {service}: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error scaling service {service}: {e}")
            return False


    async def get_metric_value(
        self, metric_type: MetricType, service: str
    ) -> Optional[float]:
        """Get current metric value from Prometheus"""
        if not self.prometheus_client:
            return None

        # Build Prometheus query based on metric type
        queries = {
            MetricType.CPU_UTILIZATION: f'avg(system_cpu_usage_percent{{service="{service}"}})',
                MetricType.MEMORY_UTILIZATION: f'avg(system_memory_usage_percent{{service="{service}"}})',
                MetricType.REQUEST_RATE: f'rate(http_requests_total{{service="{service}"}}[5m])',
                MetricType.RESPONSE_TIME: f'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{{service="{service}"}}[5m]))',
                MetricType.ERROR_RATE: f'rate(http_requests_total{{service="{service}",status=~"5.."}}[5m]) / rate(http_requests_total{{service="{service}"}}[5m]) * 100',
                MetricType.QUEUE_SIZE: f'model_generation_queue_size{{service="{service}"}}',
                MetricType.ACTIVE_CONNECTIONS: f'database_connections_active{{service="{service}"}}',
                MetricType.CACHE_HIT_RATE: f'rate(cache_hits_total{{service="{service}"}}[5m]) / (rate(cache_hits_total{{service="{service}"}}[5m]) + rate(cache_misses_total{{service="{service}"}}[5m])) * 100',
                }

        query = queries.get(metric_type)
        if not query:
            return None

        try:
            result = await self.prometheus_client.query_metric(query)
            if result.get("result") and len(result["result"]) > 0:
                return float(result["result"][0]["value"][1])
        except Exception as e:
            logger.error(f"Error getting metric {metric_type.value} for {service}: {e}")

        return None


    async def evaluate_scaling_decision(
        self, rule: ScalingRule
    ) -> Optional[ScalingDecision]:
        """Evaluate if scaling action is needed for a specific rule"""
        if not rule.enabled:
            return None

        # Check cooldown period
        last_action_key = f"{rule.service}_{rule.name}"
        if last_action_key in self.last_scaling_actions:
            time_since_last = time.time() - self.last_scaling_actions[last_action_key]
            if time_since_last < rule.cooldown_seconds:
                return None

        # Get current metric value
        current_value = await self.get_metric_value(rule.metric_type, rule.service)
        if current_value is None:
            return None

        # Get current replicas
        current_replicas = await self.get_current_replicas(rule.service)

        # Determine scaling action
        action = ScalingAction.NO_ACTION
        target_replicas = current_replicas
        reason = ""
        confidence = 0.0

        # Emergency scaling
        if rule.emergency_threshold and current_value >= rule.emergency_threshold:
            action = ScalingAction.EMERGENCY_SCALE
            target_replicas = min(rule.max_replicas, current_replicas * 2)
            reason = f"Emergency scaling: {rule.metric_type.value} = {current_value:.2f} >= {rule.emergency_threshold}"
            confidence = 1.0

        # Scale up decision
        elif (
            current_value >= rule.scale_up_threshold
            and current_replicas < rule.max_replicas
        ):
            action = ScalingAction.SCALE_UP
            # Calculate target replicas based on load
            scale_factor = min(2.0, current_value / rule.scale_up_threshold)
            target_replicas = min(
                rule.max_replicas, int(current_replicas * scale_factor)
            )
            reason = f"Scale up: {rule.metric_type.value} = {current_value:.2f} >= {rule.scale_up_threshold}"
            confidence = min(
                1.0, (current_value - rule.scale_up_threshold) / rule.scale_up_threshold
            )

        # Scale down decision
        elif (
            current_value <= rule.scale_down_threshold
            and current_replicas > rule.min_replicas
        ):
            action = ScalingAction.SCALE_DOWN
            target_replicas = max(rule.min_replicas, current_replicas - 1)
            reason = f"Scale down: {rule.metric_type.value} = {current_value:.2f} <= {rule.scale_down_threshold}"
            confidence = min(
                1.0,
                    (rule.scale_down_threshold - current_value) / rule.scale_down_threshold,
                    )

        if action != ScalingAction.NO_ACTION:
            return ScalingDecision(
                service = rule.service,
                    action = action,
                    current_replicas = current_replicas,
                    target_replicas = target_replicas,
                    reason = reason,
                    confidence = confidence * rule.weight,
                    metrics_used=[rule.metric_type.value],
                    )

        return None


    async def execute_scaling_decisions(self, decisions: List[ScalingDecision]):
        """Execute scaling decisions with conflict resolution"""
        # Group decisions by service
        service_decisions = {}
        for decision in decisions:
            if decision.service not in service_decisions:
                service_decisions[decision.service] = []
            service_decisions[decision.service].append(decision)

        # Resolve conflicts and execute
        for service, service_decisions_list in service_decisions.items():
            if len(service_decisions_list) == 1:
                decision = service_decisions_list[0]
            else:
                # Resolve conflicts by choosing highest confidence decision
                decision = max(service_decisions_list, key = lambda d: d.confidence)
                logger.info(
                    f"Resolved conflict for {service}: chose {decision.action.value} with confidence {decision.confidence:.2f}"
                )

            # Execute scaling
            success = await self.scale_service(
                decision.service, decision.target_replicas
            )
            if success:
                self.last_scaling_actions[
                    f"{decision.service}_{decision.action.value}"
                ] = time.time()
                logger.info(
                    f"Executed scaling decision: {decision.service} {decision.action.value} to {decision.target_replicas} replicas - {decision.reason}"
                )
            else:
                logger.error(
                    f"Failed to execute scaling decision for {decision.service}"
                )


    async def run_scaling_loop(self, interval: int = 30):
        """Main scaling loop"""
        logger.info(f"Starting intelligent scaling engine with {interval}s interval")

        async with PrometheusClient() as prometheus:
            self.prometheus_client = prometheus

            while True:
                try:
                    decisions = []

                    # Evaluate all scaling rules
                    for rule in self.scaling_rules:
                        decision = await self.evaluate_scaling_decision(rule)
                        if decision:
                            decisions.append(decision)

                    # Execute scaling decisions
                    if decisions:
                        await self.execute_scaling_decisions(decisions)

                    # Train predictive models periodically
                    if int(time.time()) % 3600 == 0:  # Every hour
                        await self._train_predictive_models()

                except Exception as e:
                    logger.error(f"Error in scaling loop: {e}")

                await asyncio.sleep(interval)


    async def _train_predictive_models(self):
        """Train predictive models with recent data"""
        logger.info("Training predictive models...")

        # Collect historical data from Prometheus
        end_time = datetime.now()
        start_time = end_time - timedelta(hours = 24)

        for rule in self.scaling_rules:
            try:
                # Query historical data
                query = f'avg_over_time({rule.metric_type.value}{{service="{rule.service}"}}[1h])'
                result = await self.prometheus_client.query_range(
                    query, start_time, end_time, "5m"
                )

                if result.get("result"):
                    historical_data = []
                    for series in result["result"]:
                        for timestamp, value in series.get("values", []):
                            historical_data.append(
                                MetricData(
                                    timestamp = datetime.fromtimestamp(float(timestamp)),
                                        value = float(value),
                                        service = rule.service,
                                        metric_type = rule.metric_type,
                                        )
                            )

                    if historical_data:
                        self.predictive_scaler.add_historical_data(
                            rule.service, rule.metric_type, historical_data
                        )
                        self.predictive_scaler.train_model(
                            rule.service, rule.metric_type
                        )

            except Exception as e:
                logger.error(
                    f"Error training model for {rule.service} {rule.metric_type.value}: {e}"
                )


async def main():
    """Main entry point"""
    engine = IntelligentScalingEngine()
    await engine.run_scaling_loop()

if __name__ == "__main__":
    asyncio.run(main())
