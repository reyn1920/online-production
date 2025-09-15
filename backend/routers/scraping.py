from __future__ import annotations

import asyncio
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, HttpUrl

from backend.agents.enhanced_web_scraping_tools import (
    EnhancedWebScraper,
    ScrapingMethod,
    ScrapingConfig,
    ExtractionRule,
    ScrapingResult
 )

router = APIRouter(prefix="/api/scrape", tags=["webscraping"])

# In-memory storage for scraping tasks and results
scraping_tasks: Dict[str, Dict[str, Any]] = {}
scraping_results: Dict[str, ScrapingResult] = {}

# Pydantic models for API requests/responses
class ScrapeRequest(BaseModel):
    url: HttpUrl
    method: Optional[str] = "REQUESTS"  # REQUESTS, SELENIUM, HYBRID
    extraction_rules: Optional[List[Dict[str, Any]]] = None
    use_proxy: Optional[bool] = False
    proxy_type: Optional[str] = "HTTP"  # HTTP, SOCKS5
    cache_enabled: Optional[bool] = True
    respect_robots: Optional[bool] = True
    delay_range: Optional[List[float]] = [1.0, 3.0]
    timeout: Optional[int] = 30
    max_retries: Optional[int] = 3
    custom_headers: Optional[Dict[str, str]] = None

class ScrapeResponse(BaseModel):
    task_id: str
    status: str
    message: str
    estimated_completion: Optional[str] = None

class ScrapingTaskStatus(BaseModel):
    task_id: str
    status: str  # pending, running, completed, failed
    progress: Optional[float] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result_available: bool = False

class ScrapingResultResponse(BaseModel):
    task_id: str
    url: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    extracted_data: Optional[List[Dict[str, Any]]] = None
    error_message: Optional[str] = None
    scraped_at: Optional[datetime] = None
    processing_time: Optional[float] = None

class BulkScrapeRequest(BaseModel):
    urls: List[HttpUrl]
    method: Optional[str] = "REQUESTS"
    extraction_rules: Optional[List[Dict[str, Any]]] = None
    use_proxy: Optional[bool] = False
    concurrent_limit: Optional[int] = 5
    cache_enabled: Optional[bool] = True
    respect_robots: Optional[bool] = True
    delay_range: Optional[List[float]] = [1.0, 3.0]

class ScrapingConfigRequest(BaseModel):
    method: Optional[str] = "REQUESTS"
    proxy_enabled: Optional[bool] = False
    proxy_type: Optional[str] = "HTTP"
    proxy_list: Optional[List[str]] = None
    cache_enabled: Optional[bool] = True
    respect_robots: Optional[bool] = True
    delay_range: Optional[List[float]] = [1.0, 3.0]
    timeout: Optional[int] = 30
    max_retries: Optional[int] = 3
    user_agents: Optional[List[str]] = None

# Global scraper instance
scraper = None

async def get_scraper() -> EnhancedWebScraper:
    """
Get or create the global scraper instance.

   
""""""

    global scraper
   

    
   
"""
    if scraper is None:
   """

    
   

    global scraper
   
""""""

        config = ScrapingConfig(
            method=ScrapingMethod.REQUESTS,
            use_proxies=False,
            cache_responses=True,
            respect_robots_txt=True,
            rate_limit=1.0,
            timeout=30.0,
            max_retries=3
         )
        scraper = EnhancedWebScraper(config)
    

    return scraper
    
""""""

    
   

async def perform_scraping_task(task_id: str, request: ScrapeRequest):
    
"""Background task to perform web scraping."""
    try:
        # Update task status
        scraping_tasks[task_id]["status"] = "running"
        scraping_tasks[task_id]["started_at"] = datetime.now()
    """

    return scraper
    

   
""""""
        # Get scraper instance
        scraper_instance = await get_scraper()

        # Configure scraping parameters
        config = ScrapingConfig(
            method=ScrapingMethod[request.method.upper()],
            use_proxies=request.use_proxy,
            cache_responses=request.cache_enabled,
            respect_robots_txt=request.respect_robots,
            rate_limit=request.delay_range[0] if request.delay_range else 1.0,
            timeout=float(request.timeout),
            max_retries=request.max_retries
         )

        # Create extraction rules if provided
        extraction_rules = []
        if request.extraction_rules:
            for rule_data in request.extraction_rules:
                rule = ExtractionRule(
                    name=rule_data.get("name", "default"),
                    selector=rule_data.get("selector", ""),
                    attribute=rule_data.get("attribute", "text"),
                    multiple=rule_data.get("multiple", False),
                    required=rule_data.get("required", False)
                 )
                extraction_rules.append(rule)

        # Update scraper config
        scraper_instance.config = config

        # Perform scraping
        result = await scraper_instance.scrape_url(
            str(request.url),
            extraction_rules=extraction_rules
         )

        # Store result
        scraping_results[task_id] = result

        # Update task status
        scraping_tasks[task_id]["status"] = "completed"
        scraping_tasks[task_id]["completed_at"] = datetime.now()
        scraping_tasks[task_id]["result_available"] = True

    except Exception as e:
        # Update task status with error
        scraping_tasks[task_id]["status"] = "failed"
        scraping_tasks[task_id]["completed_at"] = datetime.now()
        scraping_tasks[task_id]["error_message"] = str(e)

@router.post("/", response_model=ScrapeResponse)
async def scrape_url(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks
):
    """
Scrape a single URL with specified configuration.

   
""""""

    task_id = str(uuid.uuid4())
   

    
   
"""
    # Initialize task tracking
    scraping_tasks[task_id] = {
        "task_id": task_id,
        "url": str(request.url),
        "status": "pending",
        "created_at": datetime.now(),
        "started_at": None,
        "completed_at": None,
        "error_message": None,
        "result_available": False
     }
   """

    
   

    task_id = str(uuid.uuid4())
   
""""""
    # Add background task
    background_tasks.add_task(perform_scraping_task, task_id, request)

    return ScrapeResponse(
        task_id=task_id,
        status="pending",
        message="Scraping task has been queued",
        estimated_completion="1-30 seconds depending on complexity"
     )

@router.post("/bulk", response_model=ScrapeResponse)
async def scrape_bulk_urls(
    request: BulkScrapeRequest,
    background_tasks: BackgroundTasks
):
    """
Scrape multiple URLs concurrently.

   
""""""

    task_id = str(uuid.uuid4())
   

    
   
"""
    # Initialize task tracking
    scraping_tasks[task_id] = {
        "task_id": task_id,
        "urls": [str(url) for url in request.urls],
        "status": "pending",
        "created_at": datetime.now(),
        "started_at": None,
        "completed_at": None,
        "error_message": None,
        "result_available": False,
        "bulk_operation": True,
        "total_urls": len(request.urls)
     }
   """

    
   

    task_id = str(uuid.uuid4())
   
""""""
    # Convert to individual scrape requests and process
    async def bulk_scraping_task():
        try:
            scraping_tasks[task_id]["status"] = "running"
            scraping_tasks[task_id]["started_at"] = datetime.now()

            scraper_instance = await get_scraper()
            results = []

            # Process URLs with concurrency limit
            semaphore = asyncio.Semaphore(request.concurrent_limit)

            async def scrape_single_url(url):
                async with semaphore:
                    ScrapeRequest(
                        url=url,
                        method=request.method,
                        extraction_rules=request.extraction_rules,
                        use_proxy=request.use_proxy,
                        cache_enabled=request.cache_enabled,
                        respect_robots=request.respect_robots,
                        delay_range=request.delay_range
                     )

                    # Configure and scrape
                    config = ScrapingConfig(
                        method=ScrapingMethod[request.method.upper()],
                        use_proxies=request.use_proxy,
                        cache_responses=request.cache_enabled,
                        respect_robots_txt=request.respect_robots,
                        rate_limit=request.delay_range[0] if request.delay_range else 1.0,
                        timeout=30.0,
                        max_retries=3
                     )
                    scraper_instance.config = config

                    return await scraper_instance.scrape_url(str(url))

            # Execute all scraping tasks
            tasks = [scrape_single_url(url) for url in request.urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Store results
            scraping_results[task_id] = {
                "bulk_results": results,
                "total_urls": len(request.urls),
                "successful_scrapes": sum(1 for r in results if not isinstance(r, Exception))
             }

            scraping_tasks[task_id]["status"] = "completed"
            scraping_tasks[task_id]["completed_at"] = datetime.now()
            scraping_tasks[task_id]["result_available"] = True

        except Exception as e:
            scraping_tasks[task_id]["status"] = "failed"
            scraping_tasks[task_id]["completed_at"] = datetime.now()
            scraping_tasks[task_id]["error_message"] = str(e)

    background_tasks.add_task(bulk_scraping_task)

    return ScrapeResponse(
        task_id=task_id,
        status="pending",
        message=f"Bulk scraping task queued for {len(request.urls)} URLs",
        estimated_completion="30 seconds to 5 minutes depending on URL count and complexity"
     )

@router.get("/status/{task_id}", response_model=ScrapingTaskStatus)
async def get_scraping_status(task_id: str):
    """Get the status of a scraping task."""
    if task_id not in scraping_tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = scraping_tasks[task_id]
    return ScrapingTaskStatus(
        task_id=task_id,
        status=task["status"],
        started_at=task.get("started_at"),
        completed_at=task.get("completed_at"),
        error_message=task.get("error_message"),
        result_available=task.get("result_available", False)
     )

@router.get("/result/{task_id}", response_model=ScrapingResultResponse)
async def get_scraping_result(task_id: str):
    """Get the result of a completed scraping task."""
    if task_id not in scraping_tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = scraping_tasks[task_id]
    if task["status"] != "completed":
        raise HTTPException(status_code=400, detail="Task not completed yet")

    if task_id not in scraping_results:
        raise HTTPException(status_code=404, detail="Result not found")

    result = scraping_results[task_id]

    # Handle bulk results
    if isinstance(result, dict) and "bulk_results" in result:
        return ScrapingResultResponse(
            task_id=task_id,
            url="bulk_operation",
            success=True,
            data={
                "bulk_results": result["bulk_results"],
                "total_urls": result["total_urls"],
                "successful_scrapes": result["successful_scrapes"]
             },
            scraped_at=task.get("completed_at")
         )

    # Handle single result
    return ScrapingResultResponse(
        task_id=task_id,
        url=result.url,
        success=result.success,
        data=result.data,
        metadata=result.metadata,
        extracted_data=result.extracted_data,
        error_message=result.error_message,
        scraped_at=result.scraped_at,
        processing_time=result.processing_time
     )

@router.get("/tasks")
async def list_scraping_tasks(limit: int = 50, status: Optional[str] = None):
    """
List all scraping tasks with optional filtering.

   
""""""

    tasks = list(scraping_tasks.values())
   

    
   
""""""


    

   

    tasks = list(scraping_tasks.values())
   
""""""
    if status:
        tasks = [task for task in tasks if task["status"] == status]

    # Sort by creation time (newest first)
    tasks.sort(key=lambda x: x["created_at"], reverse=True)

    return {
        "tasks": tasks[:limit],
        "total": len(tasks),
        "filtered_by_status": status
     }

@router.post("/config")
async def update_scraping_config(config_request: ScrapingConfigRequest):
    """
Update the global scraping configuration.

    
"""
    try:
    """"""
        scraper_instance = await get_scraper()
       """"""
    try:
    """"""
        # Update configuration
        new_config = ScrapingConfig(
            method=ScrapingMethod[config_request.method.upper()],
            use_proxies=config_request.proxy_enabled,
            cache_responses=config_request.cache_enabled,
            respect_robots_txt=config_request.respect_robots,
            rate_limit=config_request.delay_range[0] if config_request.delay_range else 1.0,
            timeout=float(config_request.timeout),
            max_retries=config_request.max_retries
         )

        scraper_instance.config = new_config

        return {
            "message": "Scraping configuration updated successfully",
            "config": {
                "method": config_request.method,
                "proxy_enabled": config_request.proxy_enabled,
                "cache_enabled": config_request.cache_enabled,
                "respect_robots": config_request.respect_robots,
                "timeout": config_request.timeout,
                "max_retries": config_request.max_retries
             }
         }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Configuration update failed: {str(e)}")

@router.get("/config")
async def get_scraping_config():
    """
Get the current scraping configuration.

    scraper_instance = await get_scraper()
   
""""""

    config = scraper_instance.config
   

    
   
""""""


    

   

    config = scraper_instance.config
   
""""""
    return {
        "method": config.method.value,
        "use_proxies": config.use_proxies,
        "cache_responses": config.cache_responses,
        "respect_robots_txt": config.respect_robots_txt,
        "rate_limit": config.rate_limit,
        "timeout": config.timeout,
        "max_retries": config.max_retries
     }

@router.delete("/tasks/{task_id}")
async def delete_scraping_task(task_id: str):
    """Delete a scraping task and its results."""
    if task_id not in scraping_tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    # Remove task and result
    del scraping_tasks[task_id]
    if task_id in scraping_results:
        del scraping_results[task_id]

    return {"message": "Task deleted successfully"}

@router.post("/clear")
async def clear_all_tasks(confirm: bool = False):
    """Clear all scraping tasks and results."""
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Please set confirm=true to clear all tasks"
         )

    scraping_tasks.clear()
    scraping_results.clear()

    return {"message": "All scraping tasks and results cleared"}

@router.get("/health")
async def scraping_health_check():
    """
Health check for the scraping service.

   
""""""

    scraper_instance = await get_scraper()
   

    
   
""""""


    

   

    scraper_instance = await get_scraper()
   
""""""
    return {
        "status": "healthy",
        "scraper_initialized": scraper_instance is not None,
        "active_tasks": len([t for t in scraping_tasks.values() if t["status"] == "running"]),
        "total_tasks": len(scraping_tasks),
        "cached_results": len(scraping_results),
        "timestamp": datetime.now().isoformat()
     }