"""
Research API Models

This module defines Pydantic models for the research functionality,
including request/response models and platform configurations.
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any, Union, Literal
from enum import Enum
from datetime import datetime


class ResearchPlatform(str, Enum):
    """Supported research platforms."""
    ABACUS_AI = "abacus_ai"
    GEMINI = "gemini"
    CHATGPT = "chatgpt"
    FREE_APIS = "free_apis"
    TRAE_AI = "trae_ai"
    CLAUDE = "claude"
    PERPLEXITY = "perplexity"
    BING_AI = "bing_ai"
    BARD = "bard"


class PlatformType(str, Enum):
    """Platform subscription types"""
    FREE = "free"
    PAID = "paid"
    FREEMIUM = "freemium"


class PlatformCategory(str, Enum):
    """Platform functional categories"""
    AI_RESEARCH = "ai_research"
    ANALYTICS = "analytics"
    MARKETING = "marketing"
    CONTENT_CREATION = "content_creation"
    CODING_DEBUG = "coding_debug"
    AFFILIATE = "affiliate"
    WRITING = "writing"
    GENERAL = "general"


class ResearchPriority(str, Enum):
    """Research query priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class ResearchCategory(str, Enum):
    """Research query categories."""
    GENERAL = "general"
    TECHNICAL = "technical"
    BUSINESS = "business"
    ACADEMIC = "academic"
    NEWS = "news"
    MARKET_RESEARCH = "market_research"
    COMPETITIVE_ANALYSIS = "competitive_analysis"


class PlatformConfig(BaseModel):
    """Configuration for a research platform"""
    platform: ResearchPlatform
    platform_type: PlatformType
    category: PlatformCategory
    enabled: bool = True
    api_endpoint: Optional[str] = None
    requires_auth: bool = False
    auth_token: Optional[str] = None
    rate_limit: Optional[int] = None
    description: Optional[str] = None
    features: List[str] = Field(default_factory=list)

class DynamicPlatformManager(BaseModel):
    """Manager for dynamic platform configuration"""
    platforms: Dict[str, PlatformConfig] = Field(default_factory=dict)
    active_platforms: List[ResearchPlatform] = Field(default_factory=list)
    
    def add_platform(self, config: PlatformConfig) -> bool:
        """Add a new platform configuration"""
        self.platforms[config.platform.value] = config
        if config.enabled and config.platform not in self.active_platforms:
            self.active_platforms.append(config.platform)
        return True
    
    def remove_platform(self, platform: ResearchPlatform) -> bool:
        """Remove a platform configuration"""
        if platform.value in self.platforms:
            del self.platforms[platform.value]
            if platform in self.active_platforms:
                self.active_platforms.remove(platform)
            return True
        return False
    
    def get_platforms_by_category(self, category: PlatformCategory) -> List[PlatformConfig]:
        """Get all platforms in a specific category"""
        return [config for config in self.platforms.values() if config.category == category]
    
    def get_platforms_by_type(self, platform_type: PlatformType) -> List[PlatformConfig]:
        """Get all platforms of a specific type (free/paid)"""
        return [config for config in self.platforms.values() if config.platform_type == platform_type]


class ResearchSource(BaseModel):
    """Information about a research source"""
    url: HttpUrl
    title: str
    description: Optional[str] = None
    platform: ResearchPlatform
    reliability_score: float = Field(ge=0.0, le=1.0, description="Source reliability (0-1)")
    last_accessed: datetime
    access_count: int = Field(default=0, ge=0)
    tags: List[str] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None


class ResearchQuery(BaseModel):
    """Research query request model"""
    query: str = Field(min_length=1, max_length=2000, description="The research query")
    category: ResearchCategory = ResearchCategory.GENERAL
    priority: ResearchPriority = ResearchPriority.MEDIUM
    platforms: Optional[List[ResearchPlatform]] = Field(
        default=None, 
        description="Specific platforms to use (if None, uses all enabled platforms)"
    )
    max_results: int = Field(default=10, ge=1, le=100, description="Maximum number of results")
    timeout_seconds: int = Field(default=60, ge=10, le=600, description="Query timeout")
    include_sources: bool = Field(default=True, description="Include source information")
    save_to_database: bool = Field(default=True, description="Save results to research database")
    context: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Additional context for the query"
    )
    user_id: Optional[str] = None
    session_id: Optional[str] = None


class ResearchResult(BaseModel):
    """Individual research result"""
    content: str
    source: Optional[ResearchSource] = None
    platform: ResearchPlatform
    confidence_score: float = Field(ge=0.0, le=1.0, description="Result confidence (0-1)")
    relevance_score: float = Field(ge=0.0, le=1.0, description="Query relevance (0-1)")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None


class ResearchResponse(BaseModel):
    """Research query response model"""
    query: str
    results: List[ResearchResult]
    total_results: int
    platforms_used: List[ResearchPlatform]
    execution_time_seconds: float
    success: bool = True
    error_message: Optional[str] = None
    sources_discovered: List[ResearchSource] = Field(default_factory=list)
    query_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None


class PlatformStatus(BaseModel):
    """Status of a research platform"""
    platform: ResearchPlatform
    status: Literal["online", "offline", "error", "maintenance"]
    last_check: datetime
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    success_rate: float = Field(ge=0.0, le=1.0, description="Recent success rate (0-1)")
    total_queries: int = Field(default=0, ge=0)
    successful_queries: int = Field(default=0, ge=0)


class ResearchDatabase(BaseModel):
    """Research database entry"""
    id: str
    query: str
    category: ResearchCategory
    results: List[ResearchResult]
    sources: List[ResearchSource]
    platforms_used: List[ResearchPlatform]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    access_count: int = Field(default=0, ge=0)
    user_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None


class ResearchStats(BaseModel):
    """Research system statistics"""
    total_queries: int = Field(default=0, ge=0)
    successful_queries: int = Field(default=0, ge=0)
    failed_queries: int = Field(default=0, ge=0)
    total_sources: int = Field(default=0, ge=0)
    unique_sources: int = Field(default=0, ge=0)
    platform_stats: Dict[ResearchPlatform, PlatformStatus]
    average_response_time_seconds: float = Field(default=0.0, ge=0.0)
    uptime_percentage: float = Field(ge=0.0, le=100.0, description="System uptime percentage")
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class BulkResearchQuery(BaseModel):
    """Bulk research query for multiple queries"""
    queries: List[ResearchQuery] = Field(min_items=1, max_items=50)
    parallel_execution: bool = Field(default=True, description="Execute queries in parallel")
    max_concurrent: int = Field(default=5, ge=1, le=20, description="Max concurrent queries")
    stop_on_error: bool = Field(default=False, description="Stop all queries if one fails")


class BulkResearchResponse(BaseModel):
    """Bulk research response"""
    responses: List[ResearchResponse]
    total_queries: int
    successful_queries: int
    failed_queries: int
    execution_time_seconds: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ResearchHealthCheck(BaseModel):
    """Health check response for research system"""
    status: Literal["healthy", "degraded", "unhealthy"]
    platforms: Dict[ResearchPlatform, PlatformStatus]
    database_status: Literal["connected", "disconnected", "error"]
    total_sources: int
    last_query_time: Optional[datetime] = None
    system_load: float = Field(ge=0.0, le=1.0, description="System load (0-1)")
    memory_usage_mb: float = Field(ge=0.0)
    uptime_seconds: float = Field(ge=0.0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)