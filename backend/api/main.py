from fastapi import FastAPI, status, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Any, Dict, Optional, List
import logging

from .models import (
    ResearchQuery, ResearchResponse, ResearchSource, ResearchDatabase,
    ResearchStats, ResearchPlatform, BulkResearchQuery, BulkResearchResponse,
    ResearchHealthCheck, PlatformStatus, PlatformConfig, PlatformType, PlatformCategory
)
from .research_service import ResearchService
import time
import asyncio
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Trae Live API", 
    version="1.0.0",
    docs_url=None,  # Disable default docs to use custom
    redoc_url=None  # Disable redoc
)

# Initialize research service
research_service = ResearchService()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Custom Swagger UI with security and performance fixes"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="description" content="Trae Live API - Interactive API documentation with Swagger UI" />
        <meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data: https:; connect-src 'self';" />
        <title>Trae Live API - Swagger UI</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css" 
              integrity="sha384-++DMKo1369T5pxDNqojF1F91bYxYiT1N7b1M15a7oCzEodflj/ztKlApQoH6eQSKI" 
              crossorigin="anonymous" />
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js" 
                integrity="sha384-fU7N0ipr7Rsi0J81QNqlN7WXb/tyAL8b16lEAJ2a01m7wdX+RU61ggqmxn8p3aJb" 
                crossorigin="anonymous" 
                defer></script>
        <script>
            window.addEventListener('load', function() {
                if (window.SwaggerUIBundle) {
                    // Fetch the OpenAPI spec and initialize with it directly
                    fetch('/openapi.json')
                        .then(response => response.json())
                        .then(spec => {
                            const ui = SwaggerUIBundle({
                                spec: spec,
                                dom_id: '#swagger-ui',
                                deepLinking: true,
                                presets: [
                                    SwaggerUIBundle.presets.apis,
                                    SwaggerUIBundle.presets.standalone
                                ]
                            });
                            console.log('SwaggerUI initialized successfully');
                        })
                        .catch(error => {
                            console.error('Failed to load OpenAPI spec:', error);
                        });
                } else {
                    console.error('SwaggerUIBundle is not available');
                }
            });
        </script>
    </body>
    </html>
    """)


@app.get("/api/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/api/agents/status")
def agents_status() -> Dict[str, Any]:
    return {
        "agents": [
            {"name": "orchestrator", "status": "ready"},
            {"name": "content", "status": "idle"},
            {"name": "analytics", "status": "ready"},
        ],
        "overall": "ready",
    }


class WorkflowPayload(BaseModel):
    workflow: Optional[str] = None
    params: Optional[Dict[str, Any]] = None


@app.post("/api/workflows/{name}", status_code=status.HTTP_202_ACCEPTED)
async def run_workflow(name: str, payload: WorkflowPayload) -> Dict[str, Any]:
    return {
        "ok": True,
        "workflow": name,
        "task_id": f"wf_{name}_0001",
        "message": "queued",
    }


# ============================================================================
# RESEARCH API ENDPOINTS
# ============================================================================

@app.post("/api/research/query", response_model=ResearchResponse)
async def conduct_research(query: ResearchQuery) -> ResearchResponse:
    """
    Conduct comprehensive research across multiple platforms.
    
    This endpoint orchestrates research queries across Abacus.AI, Google Gemini,
    ChatGPT, free APIs, and Trae AI resources, returning consolidated results
    with source tracking and confidence scoring.
    """
    try:
        logger.info(f"Research request: {query.query[:100]}...")
        response = await research_service.conduct_research(query)
        logger.info(f"Research completed: {len(response.results)} results in {response.execution_time_seconds:.2f}s")
        return response
    except Exception as e:
        logger.error(f"Research failed: {e}")
        raise HTTPException(status_code=500, detail=f"Research failed: {str(e)}")


@app.post("/api/research/bulk", response_model=BulkResearchResponse)
async def conduct_bulk_research(bulk_query: BulkResearchQuery) -> BulkResearchResponse:
    """
    Conduct multiple research queries in parallel or sequence.
    
    Allows for efficient batch processing of research queries with
    configurable concurrency and error handling.
    """
    try:
        logger.info(f"Bulk research request: {len(bulk_query.queries)} queries")
        
        responses = []
        start_time = time.time()
        
        if bulk_query.parallel_execution:
            # Execute queries in parallel with concurrency limit
            semaphore = asyncio.Semaphore(bulk_query.max_concurrent)
            
            async def execute_query(query: ResearchQuery):
                async with semaphore:
                    return await research_service.conduct_research(query)
            
            tasks = [execute_query(query) for query in bulk_query.queries]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions if stop_on_error is False
            if not bulk_query.stop_on_error:
                responses = [r for r in responses if isinstance(r, ResearchResponse)]
        else:
            # Execute queries sequentially
            for query in bulk_query.queries:
                try:
                    response = await research_service.conduct_research(query)
                    responses.append(response)
                except Exception as e:
                    if bulk_query.stop_on_error:
                        raise
                    logger.warning(f"Query failed in bulk operation: {e}")
        
        execution_time = time.time() - start_time
        successful_queries = len([r for r in responses if isinstance(r, ResearchResponse)])
        failed_queries = len(bulk_query.queries) - successful_queries
        
        bulk_response = BulkResearchResponse(
            responses=responses,
            total_queries=len(bulk_query.queries),
            successful_queries=successful_queries,
            failed_queries=failed_queries,
            execution_time_seconds=execution_time
        )
        
        logger.info(f"Bulk research completed: {successful_queries}/{len(bulk_query.queries)} successful")
        return bulk_response
        
    except Exception as e:
        logger.error(f"Bulk research failed: {e}")
        raise HTTPException(status_code=500, detail=f"Bulk research failed: {str(e)}")


@app.get("/api/research/sources", response_model=List[ResearchSource])
async def get_research_sources(
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum number of sources to return"),
    platform: Optional[ResearchPlatform] = Query(default=None, description="Filter by platform")
) -> List[ResearchSource]:
    """
    Get research sources discovered during previous queries.
    
    Returns a list of sources that have been discovered and catalogued
    during research operations, with optional platform filtering.
    """
    try:
        sources = await research_service.get_sources(limit=limit)
        
        if platform:
            sources = [s for s in sources if s.platform == platform]
        
        logger.info(f"Retrieved {len(sources)} research sources")
        return sources
        
    except Exception as e:
        logger.error(f"Failed to get research sources: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get sources: {str(e)}")


@app.get("/api/research/database/search", response_model=List[ResearchDatabase])
async def search_research_database(
    q: str = Query(description="Search query"),
    limit: int = Query(default=10, ge=1, le=100, description="Maximum number of results")
) -> List[ResearchDatabase]:
    """
    Search the research database for previous queries and results.
    
    Allows searching through historical research data to find
    relevant previous queries and their results.
    """
    try:
        results = await research_service.search_database(query=q, limit=limit)
        logger.info(f"Database search returned {len(results)} results for: {q}")
        return results
        
    except Exception as e:
        logger.error(f"Database search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Database search failed: {str(e)}")


@app.get("/api/research/search", response_model=List[ResearchDatabase])
async def search_research(
    q: str = Query(description="Search query"),
    limit: int = Query(default=10, ge=1, le=100, description="Maximum number of results")
) -> List[ResearchDatabase]:
    """
    Search research data and results.
    
    General search endpoint for finding research information.
    """
    try:
        results = await research_service.search_database(query=q, limit=limit)
        logger.info(f"Research search returned {len(results)} results for: {q}")
        return results
        
    except Exception as e:
        logger.error(f"Research search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Research search failed: {str(e)}")


@app.get("/api/research/database", response_model=List[ResearchDatabase])
async def get_research_database(
    limit: int = Query(default=50, ge=1, le=100, description="Maximum number of results")
) -> List[ResearchDatabase]:
    """
    Get research database entries.
    
    Returns stored research data and results.
    """
    try:
        # Return all database entries up to limit
        results = await research_service.search_database(query="", limit=limit)
        logger.info(f"Database returned {len(results)} entries")
        return results
        
    except Exception as e:
        logger.error(f"Database retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Database retrieval failed: {str(e)}")


@app.get("/api/research/platforms", response_model=Dict[ResearchPlatform, PlatformStatus])
async def get_platform_status() -> Dict[ResearchPlatform, PlatformStatus]:
    """
    Get the current status of all research platforms.
    
    Returns health and performance information for each
    configured research platform.
    """
    try:
        status = await research_service.get_platform_status()
        logger.info("Retrieved platform status for all research platforms")
        return status
        
    except Exception as e:
        logger.error(f"Failed to get platform status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get platform status: {str(e)}")


@app.get("/api/research/platforms/status", response_model=Dict[ResearchPlatform, PlatformStatus])
async def get_research_platforms_status() -> Dict[ResearchPlatform, PlatformStatus]:
    """
    Get the current status of all research platforms.
    
    Returns health and performance information for each
    configured research platform.
    """
    try:
        status = await research_service.get_platform_status()
        logger.info("Retrieved platform status for all research platforms")
        return status
        
    except Exception as e:
        logger.error(f"Failed to get platform status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get platform status: {str(e)}")


@app.get("/api/research/stats", response_model=ResearchStats)
async def get_research_stats() -> ResearchStats:
    """
    Get comprehensive research system statistics.
    
    Returns detailed statistics about research operations,
    platform performance, and system health.
    """
    try:
        stats = await research_service.get_research_stats()
        logger.info("Retrieved comprehensive research statistics")
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get research stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get research stats: {str(e)}")


@app.get("/api/research/health", response_model=ResearchHealthCheck)
async def research_health_check() -> ResearchHealthCheck:
    """
    Comprehensive health check for the research system.
    
    Returns detailed health information including platform status,
    database connectivity, and system performance metrics.
    """
    try:
        platforms = await research_service.get_platform_status()
        stats = await research_service.get_research_stats()
        
        # Determine overall system health
        platform_health = all(
            status.status == "online" for status in platforms.values()
        )
        
        overall_status = "healthy"
        if not platform_health:
            overall_status = "degraded"
        
        health_check = ResearchHealthCheck(
            status=overall_status,
            platforms=platforms,
            database_status="connected",  # Simplified for demo
            total_sources=stats.total_sources,
            last_query_time=datetime.utcnow(),  # Simplified
            system_load=0.3,  # Simplified
            memory_usage_mb=256.0,  # Simplified
            uptime_seconds=86400.0  # Simplified
        )
        
        logger.info(f"Research health check: {overall_status}")
        return health_check
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


# ============================================================================
# RESEARCH PLATFORM INTEGRATION ENDPOINTS
# ============================================================================

@app.post("/api/research/platforms/{platform}/query")
async def query_specific_platform(
    platform: ResearchPlatform,
    query: ResearchQuery
) -> ResearchResponse:
    """
    Query a specific research platform directly.
    
    Allows targeting a specific platform for research queries,
    useful for platform-specific research needs.
    """
    try:
        # Override the platforms in the query to use only the specified one
        query.platforms = [platform]
        
        logger.info(f"Direct platform query to {platform.value}: {query.query[:100]}...")
        response = await research_service.conduct_research(query)
        
        logger.info(f"Platform {platform.value} query completed: {len(response.results)} results")
        return response
        
    except Exception as e:
        logger.error(f"Platform {platform.value} query failed: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Platform {platform.value} query failed: {str(e)}"
        )


# Platform Management Endpoints
@app.post("/api/research/platforms/add", response_model=dict)
async def add_research_platform(config: PlatformConfig):
    """Add a new research platform configuration"""
    try:
        success = research_service.add_platform(config)
        if success:
            return {
                "success": True,
                "message": f"Platform {config.platform.value} added successfully",
                "platform": config.platform.value
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to add platform")
    except Exception as e:
        logger.error(f"Error adding platform: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.delete("/api/research/platforms/{platform}")
async def remove_research_platform(platform: ResearchPlatform):
    """Remove a research platform"""
    try:
        success = research_service.remove_platform(platform)
        if success:
            return {
                "success": True,
                "message": f"Platform {platform.value} removed successfully"
            }
        else:
            raise HTTPException(status_code=404, detail="Platform not found")
    except Exception as e:
        logger.error(f"Error removing platform: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/research/platforms/category/{category}", response_model=List[PlatformConfig])
async def get_platforms_by_category(category: PlatformCategory):
    """Get platforms by category"""
    try:
        platforms = research_service.get_platforms_by_category(category)
        return platforms
    except Exception as e:
        logger.error(f"Error getting platforms by category: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/research/platforms/type/{platform_type}", response_model=List[PlatformConfig])
async def get_platforms_by_type(platform_type: PlatformType):
    """Get platforms by type (free/paid)"""
    try:
        platforms = research_service.get_platforms_by_type(platform_type)
        return platforms
    except Exception as e:
        logger.error(f"Error getting platforms by type: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/research/platforms/active", response_model=List[ResearchPlatform])
async def get_active_platforms():
    """Get list of active research platforms"""
    try:
        platforms = research_service.get_active_platforms()
        return platforms
    except Exception as e:
        logger.error(f"Error getting active platforms: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
