#!/usr/bin/env python3
"""
TRAE.AI Ollama LLM Integration - Advanced Language Model Integration

This module provides comprehensive integration with Ollama for advanced AI - powered
strategic analysis, content generation, and decision - making capabilities.
It handles model management, prompt optimization, and response processing.

Features:
- Ollama service management and health monitoring
- Model downloading and management
- Optimized prompt engineering for strategic analysis
- Response caching and optimization
- Multi - model support and fallback mechanisms
- Performance monitoring and analytics

Author: TRAE.AI System
Version: 1.0.0
"""

import asyncio
import logging
import sqlite3
import subprocess
import threading
import time
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp
import psutil
import requests

logger = logging.getLogger(__name__)


class ModelType(Enum):
    """Ollama model types and their use cases"""

    STRATEGIC_ANALYSIS = "llama2:13b"  # For strategic thinking
    CONTENT_GENERATION = "mistral:7b"  # For content creation
    CODE_ANALYSIS = "codellama:7b"  # For code review and generation
    RESEARCH_SYNTHESIS = "llama2:7b"  # For research and data analysis
    GENERAL_PURPOSE = "llama2:7b"  # Default fallback model


class PromptTemplate(Enum):
    """Predefined prompt templates for different use cases"""

    STRATEGIC_BRIEF = "strategic_brief"
    MARKET_ANALYSIS = "market_analysis"
    COMPETITIVE_INTEL = "competitive_intelligence"
    OPPORTUNITY_ASSESSMENT = "opportunity_assessment"
    RISK_ANALYSIS = "risk_analysis"
    CONTENT_STRATEGY = "content_strategy"
    FINANCIAL_ANALYSIS = "financial_analysis"
    RESEARCH_SYNTHESIS = "research_synthesis"


class ResponseQuality(Enum):
    """Response quality levels"""

    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    FAILED = "failed"


@dataclass
class OllamaModel:
    """Ollama model configuration"""

    name: str
    size: str
    description: str
    use_cases: List[str]
    parameters: Dict[str, Any]
    performance_score: float = 0.0
    last_used: Optional[datetime] = None
    usage_count: int = 0
    average_response_time: float = 0.0
    success_rate: float = 1.0


@dataclass
class PromptConfig:
    """Prompt configuration and optimization settings"""

    template_name: str
    system_prompt: str
    user_prompt_template: str
    parameters: Dict[str, Any]
    max_tokens: int = 2000
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    repeat_penalty: float = 1.1
    context_length: int = 4096


@dataclass
class QueryRequest:
    """LLM query request structure"""

    request_id: str
    prompt: str
    model_name: str
    parameters: Dict[str, Any]
    context: Dict[str, Any]
    priority: int = 5  # 1 - 10 scale
    timeout: int = 120
    retry_count: int = 3
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class QueryResponse:
    """LLM query response structure"""

    request_id: str
    response_text: str
    model_used: str
    response_time: float
    token_count: int
    quality_score: float
    confidence_level: float
    metadata: Dict[str, Any]
    completed_at: datetime = field(default_factory=datetime.now)
    cached: bool = False


class OllamaIntegration:
    """
    Comprehensive Ollama LLM Integration

    Provides advanced language model capabilities for strategic analysis,
        content generation, and AI - powered decision making.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.ollama_endpoint = config.get("ollama_endpoint", "http://localhost:11434")
        self.default_model = config.get("default_model", "llama2:7b")
        self.max_concurrent_requests = config.get("max_concurrent_requests", 5)
        self.cache_enabled = config.get("cache_enabled", True)
        self.cache_ttl = config.get("cache_ttl", 3600)  # 1 hour

        # Model management
        self.available_models: Dict[str, OllamaModel] = {}
        self.model_queue = deque(maxlen=100)
        self.active_requests: Dict[str, QueryRequest] = {}

        # Performance tracking
        self.performance_metrics = defaultdict(list)
        self.response_cache: Dict[str, QueryResponse] = {}
        self.request_history = deque(maxlen=1000)

        # Threading and async support
        self.executor = ThreadPoolExecutor(max_workers=self.max_concurrent_requests)
        self.request_semaphore = asyncio.Semaphore(self.max_concurrent_requests)

        # Initialize components
        self._initialize_ollama_integration()
        self._setup_prompt_templates()
        self._setup_performance_monitoring()

    def _setup_performance_monitoring(self):
        """Setup performance monitoring and metrics collection"""
        try:
            # Initialize performance tracking structures
            self.performance_stats = {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "average_response_time": 0.0,
                "total_tokens_processed": 0,
                "cache_hit_rate": 0.0,
                "model_performance": defaultdict(dict),
            }

            # Setup metrics collection intervals
            self.metrics_collection_interval = self.config.get("metrics_interval", 300)  # 5 minutes
            self.performance_history = deque(maxlen=1000)

            # Initialize model performance tracking
            for model_name in self.available_models:
                self.performance_stats["model_performance"][model_name] = {
                    "requests": 0,
                    "successes": 0,
                    "failures": 0,
                    "avg_response_time": 0.0,
                    "total_tokens": 0,
                    "quality_scores": [],
                }

            # Start background metrics collection
            self._start_metrics_collection()

            logger.info("Performance monitoring setup completed")

        except Exception as e:
            logger.error(f"Failed to setup performance monitoring: {e}")

    def _start_metrics_collection(self):
        """Start background metrics collection thread"""

        def collect_metrics():
            while True:
                try:
                    self._collect_system_metrics()
                    time.sleep(self.metrics_collection_interval)
                except Exception as e:
                    logger.error(f"Metrics collection error: {e}")
                    time.sleep(60)  # Wait 1 minute before retrying

        metrics_thread = threading.Thread(target=collect_metrics, daemon=True)
        metrics_thread.start()
        logger.info("Background metrics collection started")

    def _collect_system_metrics(self):
        """Collect system performance metrics"""
        try:
            # System resource usage
            cpu_usage = psutil.cpu_percent()
            memory_usage = psutil.virtual_memory().percent

            # Calculate cache hit rate
            total_requests = self.performance_stats["total_requests"]
            cache_hits = sum(1 for r in self.request_history if hasattr(r, "cached") and r.cached)
            cache_hit_rate = (cache_hits / total_requests) if total_requests > 0 else 0.0

            # Update performance stats
            self.performance_stats["cache_hit_rate"] = cache_hit_rate

            # Store metrics snapshot
            metrics_snapshot = {
                "timestamp": datetime.now(),
                "cpu_usage": cpu_usage,
                "memory_usage": memory_usage,
                "cache_hit_rate": cache_hit_rate,
                "active_requests": len(self.active_requests),
                "total_requests": total_requests,
            }

            self.performance_history.append(metrics_snapshot)

            # Log metrics periodically
            if total_requests % 100 == 0 and total_requests > 0:
                logger.info(
                    f"Performance metrics - Requests: {total_requests}, "
                    f"Cache hit rate: {cache_hit_rate:.2%}, "
                    f"CPU: {cpu_usage:.1f}%, Memory: {memory_usage:.1f}%"
                )

        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")

        logger.info(f"OllamaIntegration initialized with endpoint: {self.ollama_endpoint}")

    def _initialize_ollama_integration(self):
        """Initialize Ollama integration and check service health"""
        try:
            # Check Ollama service health
            self._check_ollama_health()

            # Discover available models
            self._discover_available_models()

            # Ensure required models are available
            self._ensure_required_models()

            # Setup database for caching and metrics
            self._setup_ollama_database()

            logger.info("Ollama integration initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Ollama integration: {e}")
            raise

    def _check_ollama_health(self) -> bool:
        """Check if Ollama service is running and healthy"""
        try:
            response = requests.get(f"{self.ollama_endpoint}/api/tags", timeout=10)
            if response.status_code == 200:
                logger.info("Ollama service is healthy")
                return True
            else:
                raise Exception(f"Ollama service unhealthy: {response.status_code}")
        except requests.exceptions.ConnectionError:
            logger.error("Ollama service is not running. Attempting to start...")
            self._start_ollama_service()
            return False
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False

    def _start_ollama_service(self):
        """Attempt to start Ollama service if not running"""
        try:
            # Check if Ollama is installed
            result = subprocess.run(["which", "ollama"], capture_output=True, text=True)
            if result.returncode != 0:
                logger.error("Ollama is not installed. Please install Ollama first.")
                return False

            # Start Ollama service
            logger.info("Starting Ollama service...")
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            # Wait for service to start
            for i in range(30):  # Wait up to 30 seconds
                time.sleep(1)
                if self._check_ollama_health():
                    logger.info("Ollama service started successfully")
                    return True

            logger.error("Failed to start Ollama service within timeout")
            return False

        except Exception as e:
            logger.error(f"Failed to start Ollama service: {e}")
            return False

    def _discover_available_models(self):
        """Discover and catalog available Ollama models"""
        try:
            response = requests.get(f"{self.ollama_endpoint}/api/tags", timeout=10)
            if response.status_code == 200:
                models_data = response.json().get("models", [])

                for model_info in models_data:
                    model_name = model_info.get("name", "")
                    model_size = model_info.get("size", 0)

                    # Create model configuration
                    model = OllamaModel(
                        name=model_name,
                        size=self._format_model_size(model_size),
                        description=f"Ollama model: {model_name}",
                        use_cases=self._determine_model_use_cases(model_name),
                        parameters=self._get_default_model_parameters(model_name),
                    )

                    self.available_models[model_name] = model

                logger.info(f"Discovered {len(self.available_models)} available models")
            else:
                logger.error(f"Failed to discover models: {response.status_code}")
        except Exception as e:
            logger.error(f"Model discovery failed: {e}")

    def _format_model_size(self, size_bytes: int) -> str:
        """Format model size in human - readable format"""
        try:
            if size_bytes == 0:
                return "Unknown"

            # Convert bytes to appropriate unit
            for unit in ["B", "KB", "MB", "GB", "TB"]:
                if size_bytes < 1024.0:
                    return f"{size_bytes:.1f} {unit}"
                size_bytes /= 1024.0
            return f"{size_bytes:.1f} PB"
        except Exception as e:
            logger.warning(f"Failed to format model size: {e}")
            return "Unknown"

    def _determine_model_use_cases(self, model_name: str) -> List[str]:
        """Determine use cases for a model based on its name"""
        use_cases = []
        model_lower = model_name.lower()

        if "llama" in model_lower:
            use_cases.extend(["general", "analysis", "reasoning"])
        if "mistral" in model_lower:
            use_cases.extend(["content", "creative", "writing"])
        if "code" in model_lower:
            use_cases.extend(["coding", "programming", "technical"])
        if "13b" in model_lower or "70b" in model_lower:
            use_cases.extend(["strategic", "complex_reasoning"])

        return use_cases if use_cases else ["general"]

    def _get_default_model_parameters(self, model_name: str) -> Dict[str, Any]:
        """Get default parameters for a model"""
        return {
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 40,
            "repeat_penalty": 1.1,
            "max_tokens": 2000,
        }

    def _ensure_required_models(self):
        """Ensure required models are downloaded and available"""
        required_models = [
            ModelType.STRATEGIC_ANALYSIS.value,
            ModelType.CONTENT_GENERATION.value,
            ModelType.GENERAL_PURPOSE.value,
        ]

        for model_name in required_models:
            if model_name not in self.available_models:
                logger.info(f"Downloading required model: {model_name}")
                self._download_model(model_name)

    def _download_model(self, model_name: str) -> bool:
        """Download a model from Ollama registry"""
        try:
            logger.info(f"Starting download of model: {model_name}")

            # Use Ollama CLI to pull the model
            result = subprocess.run(
                ["ollama", "pull", model_name],
                capture_output=True,
                text=True,
                timeout=1800,  # 30 minutes timeout
            )

            if result.returncode == 0:
                logger.info(f"Successfully downloaded model: {model_name}")
                # Refresh available models
                self._discover_available_models()
                return True
            else:
                logger.error(f"Failed to download model {model_name}: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error(f"Model download timeout for: {model_name}")
            return False
        except Exception as e:
            logger.error(f"Model download error for {model_name}: {e}")
            return False

    def _setup_prompt_templates(self):
        """Setup optimized prompt templates for different use cases"""
        self.prompt_templates = {
            PromptTemplate.STRATEGIC_BRIEF: PromptConfig(
                template_name="strategic_brief",
                system_prompt="You are a senior strategic advisor with 20+ years of experience in business strategy, market analysis, \
    and corporate planning. Provide comprehensive, actionable insights.",
                user_prompt_template="Analyze the following business data \
    and generate a strategic brief: {data}\\n\\nFocus on: {focus_areas}\\n\\nProvide specific recommendations with implementation timelines.",
                parameters={"temperature": 0.7, "top_p": 0.9, "max_tokens": 3000},
            ),
            PromptTemplate.MARKET_ANALYSIS: PromptConfig(
                template_name="market_analysis",
                system_prompt="You are a market research expert specializing in digital marketing, content creation, \
    and online business models. Provide data - driven market insights.",
                user_prompt_template="Conduct a comprehensive market analysis for: {market_segment}\\n\\nData: {market_data}\\n\\nInclude market size, growth trends, competitive landscape, \
    and opportunities.",
                parameters={"temperature": 0.6, "top_p": 0.85, "max_tokens": 2500},
            ),
            PromptTemplate.COMPETITIVE_INTEL: PromptConfig(
                template_name="competitive_intelligence",
                system_prompt="You are a competitive intelligence analyst with expertise in digital business models, content strategies, \
    and market positioning.",
                user_prompt_template="Analyze competitive landscape: {competitors}\\n\\nOur position: {our_data}\\n\\nIdentify competitive advantages, threats, \
    and strategic opportunities.",
                parameters={"temperature": 0.65, "top_p": 0.9, "max_tokens": 2000},
            ),
            PromptTemplate.OPPORTUNITY_ASSESSMENT: PromptConfig(
                template_name="opportunity_assessment",
                system_prompt="You are a business development expert specializing in identifying \
    and evaluating new market opportunities \
    and revenue streams.",
                user_prompt_template="Evaluate this business opportunity: {opportunity_data}\\n\\nAssess: market potential, risks, resource requirements, ROI projections, \
    and implementation strategy.",
                parameters={"temperature": 0.7, "top_p": 0.9, "max_tokens": 2200},
            ),
            PromptTemplate.CONTENT_STRATEGY: PromptConfig(
                template_name="content_strategy",
                system_prompt="You are a content strategist \
    and digital marketing expert with deep knowledge of YouTube, social media, \
    and content monetization.",
                user_prompt_template="Develop content strategy for: {platform}\\n\\nTarget audience: {audience}\\n\\nCurrent performance: {performance_data}\\n\\nProvide specific content recommendations \
    and optimization strategies.",
                parameters={"temperature": 0.8, "top_p": 0.9, "max_tokens": 2000},
            ),
        }

        logger.info(f"Loaded {len(self.prompt_templates)} prompt templates")

    async def query_llm(
        self,
        prompt: str,
        model_name: Optional[str] = None,
        template: Optional[PromptTemplate] = None,
        context: Optional[Dict[str, Any]] = None,
        priority: int = 5,
    ) -> QueryResponse:
        """Query Ollama LLM with advanced features"""

        request_id = self._generate_request_id()

        try:
            # Select optimal model
            if not model_name:
                model_name = self._select_optimal_model(template, context)

            # Check cache first
            if self.cache_enabled:
                cached_response = self._check_cache(prompt, model_name)
                if cached_response:
                    logger.info(f"Cache hit for request {request_id}")
                    cached_response.request_id = request_id
                    cached_response.cached = True
                    return cached_response

            # Apply prompt template if specified
            if template and template in self.prompt_templates:
                prompt = self._apply_prompt_template(template, prompt, context)

            # Create request
            request = QueryRequest(
                request_id=request_id,
                prompt=prompt,
                model_name=model_name,
                parameters=self._get_model_parameters(model_name, template),
                context=context or {},
                priority=priority,
            )

            # Execute query with semaphore control
            async with self.request_semaphore:
                response = await self._execute_llm_query(request)

            # Cache successful responses
            if self.cache_enabled and response.quality_score > 0.7:
                self._cache_response(prompt, model_name, response)

            # Update performance metrics
            self._update_performance_metrics(request, response)

            return response

        except Exception as e:
            logger.error(f"LLM query failed for request {request_id}: {e}")
            return QueryResponse(
                request_id=request_id,
                response_text=f"Query failed: {str(e)}",
                model_used=model_name or self.default_model,
                response_time=0.0,
                token_count=0,
                quality_score=0.0,
                confidence_level=0.0,
                metadata={"error": str(e)},
            )

    async def _execute_llm_query(self, request: QueryRequest) -> QueryResponse:
        """Execute the actual LLM query"""
        start_time = time.time()

        try:
            # Prepare request payload
            payload = {
                "model": request.model_name,
                "prompt": request.prompt,
                "stream": False,
                "options": request.parameters,
            }

            # Execute request
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_endpoint}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=request.timeout),
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        response_text = result.get("response", "").strip()

                        # Calculate metrics
                        response_time = time.time() - start_time
                        token_count = len(response_text.split())
                        quality_score = self._assess_response_quality(response_text, request)
                        confidence_level = self._calculate_confidence_level(result, response_text)

                        return QueryResponse(
                            request_id=request.request_id,
                            response_text=response_text,
                            model_used=request.model_name,
                            response_time=response_time,
                            token_count=token_count,
                            quality_score=quality_score,
                            confidence_level=confidence_level,
                            metadata={
                                "model_info": result.get("model", {}),
                                "total_duration": result.get("total_duration", 0),
                                "load_duration": result.get("load_duration", 0),
                                "prompt_eval_count": result.get("prompt_eval_count", 0),
                                "eval_count": result.get("eval_count", 0),
                            },
                        )
                    else:
                        raise Exception(f"Ollama API error: {response.status}")

        except asyncio.TimeoutError:
            raise Exception(f"Query timeout after {request.timeout} seconds")
        except Exception as e:
            raise Exception(f"Query execution failed: {str(e)}")

    def _select_optimal_model(
        self, template: Optional[PromptTemplate], context: Optional[Dict]
    ) -> str:
        """Select the optimal model based on use case and context"""
        try:
            # Use template - specific model if available
            if template:
                if template == PromptTemplate.STRATEGIC_BRIEF:
                    return ModelType.STRATEGIC_ANALYSIS.value
                elif template == PromptTemplate.CONTENT_STRATEGY:
                    return ModelType.CONTENT_GENERATION.value
                elif template in [
                    PromptTemplate.MARKET_ANALYSIS,
                    PromptTemplate.COMPETITIVE_INTEL,
                ]:
                    return ModelType.RESEARCH_SYNTHESIS.value

            # Check context for hints
            if context:
                if "code" in context or "programming" in str(context).lower():
                    return ModelType.CODE_ANALYSIS.value
                elif "strategy" in str(context).lower() or "analysis" in str(context).lower():
                    return ModelType.STRATEGIC_ANALYSIS.value

            # Default to general purpose model
            return self.default_model

        except Exception as e:
            logger.warning(f"Model selection failed, using default: {e}")
            return self.default_model

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        try:
            # Ollama service status
            service_healthy = self._check_ollama_health()

            # Model statistics
            model_stats = {}
            for name, model in self.available_models.items():
                model_stats[name] = {
                    "size": model.size,
                    "usage_count": model.usage_count,
                    "success_rate": model.success_rate,
                    "avg_response_time": model.average_response_time,
                }

            # Performance metrics
            recent_requests = len(
                [
                    r
                    for r in self.request_history
                    if r.completed_at > datetime.now() - timedelta(hours=1)
                ]
            )

            return {
                "service_healthy": service_healthy,
                "endpoint": self.ollama_endpoint,
                "available_models": len(self.available_models),
                "model_statistics": model_stats,
                "active_requests": len(self.active_requests),
                "cache_size": len(self.response_cache),
                "recent_requests_1h": recent_requests,
                "prompt_templates": len(self.prompt_templates),
                "max_concurrent": self.max_concurrent_requests,
            }

        except Exception as e:
            logger.error(f"Status check failed: {e}")
            return {"error": str(e)}

    async def optimize_performance(self):
        """Optimize Ollama integration performance"""
        try:
            # Clean old cache entries
            self._cleanup_cache()

            # Update model performance scores
            self._update_model_scores()

            # Optimize model parameters based on usage patterns
            self._optimize_model_parameters()

            logger.info("Ollama performance optimization completed")

        except Exception as e:
            logger.error(f"Performance optimization failed: {e}")

    def _setup_ollama_database(self):
        """Setup SQLite database for caching and metrics storage"""
        try:
            db_path = Path(self.config.get("cache_db_path", "./data/ollama_cache.db"))
            db_path.parent.mkdir(parents=True, exist_ok=True)

            self.db_connection = sqlite3.connect(str(db_path), check_same_thread=False)
            cursor = self.db_connection.cursor()

            # Create response cache table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS response_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        prompt_hash TEXT UNIQUE NOT NULL,
                        model_name TEXT NOT NULL,
                        prompt TEXT NOT NULL,
                        response TEXT NOT NULL,
                        quality_score REAL NOT NULL,
                        token_count INTEGER NOT NULL,
                        response_time REAL NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP NOT NULL
                )
            """
            )

            # Create performance metrics table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        model_name TEXT NOT NULL,
                        request_id TEXT NOT NULL,
                        response_time REAL NOT NULL,
                        token_count INTEGER NOT NULL,
                        quality_score REAL NOT NULL,
                        success BOOLEAN NOT NULL,
                        error_message TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Create model usage statistics table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS model_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        model_name TEXT NOT NULL,
                        usage_count INTEGER DEFAULT 0,
                        total_response_time REAL DEFAULT 0.0,
                        success_count INTEGER DEFAULT 0,
                        failure_count INTEGER DEFAULT 0,
                        last_used TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Create indexes for better performance
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_prompt_hash ON response_cache(prompt_hash)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_model_name ON response_cache(model_name)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_expires_at ON response_cache(expires_at)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_performance_model ON performance_metrics(model_name)"
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_usage_model ON model_usage(model_name)")

            self.db_connection.commit()
            logger.info("Ollama database setup completed successfully")

        except Exception as e:
            logger.error(f"Failed to setup Ollama database: {e}")
            # Fallback to in - memory storage if database setup fails
            self.db_connection = None
