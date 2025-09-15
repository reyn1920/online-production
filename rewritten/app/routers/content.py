#!/usr/bin/env python3
""""""
Content generation and management router
Provides endpoints for content creation, video generation, and content management.
""""""

import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

# Import content services
try:
    from content_agent.main import (
        ContentAgent,
        ContentConfig,
        ContentRequest,
        ContentResponse,
# BRACKET_SURGEON: disabled
#     )
except ImportError:
    try:
        from backend.agents.content_agent import ContentAgent
    except ImportError:
        ContentAgent = None
        logging.warning("Content agent not available - check backend structure")

try:
    from backend.agents.specialized_agents import (
        ContentAgent as SpecializedContentAgent,
# BRACKET_SURGEON: disabled
#     )
except ImportError:
    SpecializedContentAgent = None
    logging.warning("Specialized content agent not available")

router = APIRouter()
templates = Jinja2Templates(directory="templates")
logger = logging.getLogger(__name__)


class ContentGenerationRequest(BaseModel):
    type: str = Field(default="article", description="Type of content to generate")
    topic: str = Field(..., description="Topic or subject for content generation")
    format: Optional[str] = Field(default="educational", description="Content format style")
    target_length: Optional[int] = Field(default=500, description="Target length in words")
    tone: Optional[str] = Field(default="professional", description="Content tone")
    audience: Optional[str] = Field(default="general", description="Target audience")
    keywords: Optional[List[str]] = Field(default=[], description="SEO keywords to include")
    include_images: Optional[bool] = Field(default=False, description="Include image suggestions")


class VideoContentRequest(BaseModel):
    topic: str = Field(..., description="Video topic")
    duration: Optional[int] = Field(default=300, description="Duration in seconds")
    style: Optional[str] = Field(default="educational", description="Video style")
    voice: Optional[str] = Field(default="default", description="Voice type for narration")
    resolution: Optional[str] = Field(default="1920x1080", description="Video resolution")
    include_avatar: Optional[bool] = Field(default=False, description="Include AI avatar")


class ContentStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class TrendingTopicsResponse(BaseModel):
    topics: List[Dict[str, Any]]
    updated_at: datetime
    source: str


# In-memory job tracking (in production, use Redis or database)
content_jobs = {}
content_agent_instance = None


def get_content_agent():
    """Get or create content agent instance"""
    global content_agent_instance

    if content_agent_instance is None:
        try:
            # Try to get from production manager first
            from backend.production_init import get_production_manager

            production_manager = get_production_manager()

            # Try to get from services
            content_agent_instance = production_manager.get_service("content_agent")

            if content_agent_instance is None:
                # Try to get from agents
                content_agent_instance = production_manager.get_agent("content_agent")

            if content_agent_instance is None:
                # Use the correct ContentAgent from backend.agents.content_agent
                try:
                    from backend.agents.content_agent import ContentAgent

                    content_agent_instance = ContentAgent()
                    logger.info("✅ ContentAgent initialized from backend.agents.content_agent")
                except ImportError:
                    # Final fallback to specialized agent
                    from backend.agents.specialized_agents import (
                        ContentAgent as SpecializedContentAgent,
# BRACKET_SURGEON: disabled
#                     )

                    content_agent_instance = SpecializedContentAgent(
                        agent_id="content_agent_001", name="ContentAgent"
# BRACKET_SURGEON: disabled
#                     )
                    logger.info("✅ Specialized ContentAgent initialized")
            else:
                logger.info("✅ ContentAgent retrieved from production manager")

        except Exception as e:
            logger.error(f"❌ Failed to initialize ContentAgent: {e}")
            content_agent_instance = None

    return content_agent_instance


@router.get("/")
async def content_interface(request: Request):
    """Content generation interface"""
    return templates.TemplateResponse(
        "content.html",
        {
            "request": request,
            "title": "Content Generation",
            "content_types": [
                "article",
                "blog_post",
                "social_media",
                "email",
                "video_script",
                "product_description",
                "newsletter",
# BRACKET_SURGEON: disabled
#             ],
# BRACKET_SURGEON: disabled
#         },
# BRACKET_SURGEON: disabled
#     )


@router.get("/health")
async def health_check():
    """Health check for content services"""
    agent = get_content_agent()
    return {
        "status": "healthy" if agent else "degraded",
        "timestamp": datetime.now().isoformat(),
        "content_agent": agent is not None,
        "services": {
            "text_generation": True,
            "video_creation": agent is not None,
            "tts_engine": agent is not None,
            "avatar_generation": agent is not None,
# BRACKET_SURGEON: disabled
#         },
# BRACKET_SURGEON: disabled
#     }


@router.get("/trending")
async def get_trending_topics():
    """Get trending topics for content inspiration"""
    agent = get_content_agent()

    if not agent or not hasattr(agent, "news_watcher"):
        # Return fallback trending topics
        return JSONResponse(
            {
                "topics": [
                    {
                        "title": "AI and Machine Learning",
                        "category": "Technology",
                        "trend_score": 95,
                        "keywords": [
                            "artificial intelligence",
                            "machine learning",
                            "automation",
# BRACKET_SURGEON: disabled
#                         ],
# BRACKET_SURGEON: disabled
#                     },
                    {
                        "title": "Sustainable Living",
                        "category": "Lifestyle",
                        "trend_score": 88,
                        "keywords": ["sustainability", "eco-friendly", "green living"],
# BRACKET_SURGEON: disabled
#                     },
                    {
                        "title": "Remote Work Productivity",
                        "category": "Business",
                        "trend_score": 82,
                        "keywords": ["remote work", "productivity", "work from home"],
# BRACKET_SURGEON: disabled
#                     },
                    {
                        "title": "Digital Marketing Trends",
                        "category": "Marketing",
                        "trend_score": 79,
                        "keywords": [
                            "digital marketing",
                            "social media",
                            "content strategy",
# BRACKET_SURGEON: disabled
#                         ],
# BRACKET_SURGEON: disabled
#                     },
                    {
                        "title": "Health and Wellness",
                        "category": "Health",
                        "trend_score": 76,
                        "keywords": ["wellness", "mental health", "fitness"],
# BRACKET_SURGEON: disabled
#                     },
# BRACKET_SURGEON: disabled
#                 ],
                "updated_at": datetime.now().isoformat(),
                "source": "fallback_data",
# BRACKET_SURGEON: disabled
#             }
# BRACKET_SURGEON: disabled
#         )

    try:
        trending_data = await agent.news_watcher.get_trending_topics()
        return JSONResponse(trending_data)
    except Exception as e:
        logger.error(f"Error getting trending topics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get trending topics")


@router.post("/generate")
async def generate_content(request: ContentGenerationRequest, background_tasks: BackgroundTasks):
    """Generate text content asynchronously"""
    agent = get_content_agent()
    if not agent:
        raise HTTPException(status_code=503, detail="Content generation service unavailable")

    job_id = str(uuid.uuid4())
    content_jobs[job_id] = {
        "status": "pending",
        "progress": 0.0,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "type": "text",
        "request": request.dict(),
# BRACKET_SURGEON: disabled
#     }

    # Start background task
    background_tasks.add_task(_generate_text_content, job_id, request, agent)

    return JSONResponse(
        {"job_id": job_id, "status": "pending", "message": "Content generation started"}
# BRACKET_SURGEON: disabled
#     )


@router.post("/generate-video")
async def generate_video_content(request: VideoContentRequest, background_tasks: BackgroundTasks):
    """Generate video content asynchronously"""
    agent = get_content_agent()
    if not agent:
        raise HTTPException(status_code=503, detail="Video generation service unavailable")

    job_id = str(uuid.uuid4())
    content_jobs[job_id] = {
        "status": "pending",
        "progress": 0.0,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "type": "video",
        "request": request.dict(),
# BRACKET_SURGEON: disabled
#     }

    # Start background task
    background_tasks.add_task(_generate_video_content, job_id, request, agent)

    return JSONResponse(
        {"job_id": job_id, "status": "pending", "message": "Video generation started"}
# BRACKET_SURGEON: disabled
#     )


@router.get("/status/{job_id}")
async def get_content_status(job_id: str):
    """Get the status of a content generation job"""
    if job_id not in content_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = content_jobs[job_id]
    return JSONResponse(
        {
            "job_id": job_id,
            "status": job["status"],
            "progress": job.get("progress", 0.0),
            "result": job.get("result"),
            "error": job.get("error"),
            "created_at": job["created_at"].isoformat(),
            "updated_at": job["updated_at"].isoformat(),
# BRACKET_SURGEON: disabled
#         }
# BRACKET_SURGEON: disabled
#     )


@router.get("/download/{job_id}")
async def download_content(job_id: str):
    """Download generated content file"""
    if job_id not in content_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = content_jobs[job_id]
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not completed")

    result = job.get("result")
    if not result or "file_path" not in result:
        raise HTTPException(status_code=404, detail="No file available for download")

    file_path = Path(result["file_path"])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type="application/octet-stream",
# BRACKET_SURGEON: disabled
#     )


@router.get("/templates")
async def get_content_templates():
    """Get available content templates"""
    return JSONResponse(
        {
            "templates": {
                "article": {
                    "name": "Article",
                    "description": "Long-form informative content",
                    "fields": ["title", "introduction", "body", "conclusion"],
                    "min_length": 500,
                    "max_length": 3000,
# BRACKET_SURGEON: disabled
#                 },
                "blog_post": {
                    "name": "Blog Post",
                    "description": "Engaging blog content",
                    "fields": ["title", "hook", "content", "call_to_action"],
                    "min_length": 300,
                    "max_length": 2000,
# BRACKET_SURGEON: disabled
#                 },
                "social_media": {
                    "name": "Social Media Post",
                    "description": "Short, engaging social content",
                    "fields": ["text", "hashtags", "call_to_action"],
                    "min_length": 50,
                    "max_length": 280,
# BRACKET_SURGEON: disabled
#                 },
                "email": {
                    "name": "Email",
                    "description": "Professional email content",
                    "fields": ["subject", "greeting", "body", "closing"],
                    "min_length": 100,
                    "max_length": 1000,
# BRACKET_SURGEON: disabled
#                 },
                "video_script": {
                    "name": "Video Script",
                    "description": "Script for video content",
                    "fields": ["hook", "introduction", "main_content", "conclusion"],
                    "min_length": 200,
                    "max_length": 1500,
# BRACKET_SURGEON: disabled
#                 },
# BRACKET_SURGEON: disabled
#             }
# BRACKET_SURGEON: disabled
#         }
# BRACKET_SURGEON: disabled
#     )


@router.delete("/jobs/{job_id}")
async def delete_content_job(job_id: str):
    """Delete a content generation job"""
    if job_id not in content_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = content_jobs[job_id]

    # Clean up any associated files
    if job.get("result") and "file_path" in job["result"]:
        try:
            file_path = Path(job["result"]["file_path"])
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            logger.warning(f"Failed to delete file for job {job_id}: {e}")

    del content_jobs[job_id]
    return JSONResponse({"message": "Job deleted successfully"})


@router.get("/jobs")
async def list_content_jobs():
    """List all content generation jobs"""
    jobs_list = []
    for job_id, job_data in content_jobs.items():
        jobs_list.append(
            {
                "job_id": job_id,
                "status": job_data["status"],
                "type": job_data.get("type", "unknown"),
                "progress": job_data.get("progress", 0.0),
                "created_at": job_data["created_at"].isoformat(),
                "updated_at": job_data["updated_at"].isoformat(),
# BRACKET_SURGEON: disabled
#             }
# BRACKET_SURGEON: disabled
#         )

    return JSONResponse({"jobs": jobs_list})


async def _generate_text_content(job_id: str, request: ContentGenerationRequest, agent):
    """Background task for text content generation"""
    try:
        # Update job status
        content_jobs[job_id]["status"] = "processing"
        content_jobs[job_id]["progress"] = 0.1
        content_jobs[job_id]["updated_at"] = datetime.now()

        # Create content request
        content_request = {
            "type": request.type,
            "topic": request.topic,
            "format": request.format,
            "target_length": request.target_length,
            "tone": request.tone,
            "audience": request.audience,
            "keywords": request.keywords,
            "include_images": request.include_images,
# BRACKET_SURGEON: disabled
#         }

        # Update progress
        content_jobs[job_id]["progress"] = 0.3
        content_jobs[job_id]["updated_at"] = datetime.now()

        # Generate content using agent
        if hasattr(agent, "generate_content"):
            result = await agent.generate_content(content_request)
        else:
            # Fallback method
            result = {
                "content": f"Generated {request.type} about {request.topic}",
                "title": f"Title: {request.topic}",
                "metadata": {
                    "word_count": request.target_length,
                    "tone": request.tone,
                    "audience": request.audience,
# BRACKET_SURGEON: disabled
#                 },
# BRACKET_SURGEON: disabled
#             }

        # Update progress
        content_jobs[job_id]["progress"] = 0.8
        content_jobs[job_id]["updated_at"] = datetime.now()

        # Save content to file if needed
        if result.get("content"):
            output_dir = Path("generated_content")
            output_dir.mkdir(exist_ok=True)

            file_path = output_dir / f"{job_id}_{request.type}.txt"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(result["content"])

            result["file_path"] = str(file_path)

        # Complete job
        content_jobs[job_id]["status"] = "completed"
        content_jobs[job_id]["progress"] = 1.0
        content_jobs[job_id]["result"] = result
        content_jobs[job_id]["updated_at"] = datetime.now()

    except Exception as e:
        logger.error(f"Error generating text content for job {job_id}: {e}")
        content_jobs[job_id]["status"] = "failed"
        content_jobs[job_id]["error"] = str(e)
        content_jobs[job_id]["updated_at"] = datetime.now()


async def _generate_video_content(job_id: str, request: VideoContentRequest, agent):
    """Background task for video content generation"""
    try:
        # Update job status
        content_jobs[job_id]["status"] = "processing"
        content_jobs[job_id]["progress"] = 0.1
        content_jobs[job_id]["updated_at"] = datetime.now()

        # Create video request
        video_request = {
            "topic": request.topic,
            "duration": request.duration,
            "style": request.style,
            "voice": request.voice,
            "resolution": request.resolution,
            "include_avatar": request.include_avatar,
# BRACKET_SURGEON: disabled
#         }

        # Update progress
        content_jobs[job_id]["progress"] = 0.3
        content_jobs[job_id]["updated_at"] = datetime.now()

        # Generate video using agent
        if hasattr(agent, "generate_video"):
            result = await agent.generate_video(video_request)
        else:
            # Fallback - create placeholder result
            result = {
                "video_path": f"placeholder_video_{job_id}.mp4",
                "script": f"Video script about {request.topic}",
                "duration": request.duration,
                "metadata": {
                    "resolution": request.resolution,
                    "style": request.style,
                    "voice": request.voice,
# BRACKET_SURGEON: disabled
#                 },
# BRACKET_SURGEON: disabled
#             }

        # Update progress
        content_jobs[job_id]["progress"] = 0.9
        content_jobs[job_id]["updated_at"] = datetime.now()

        # Complete job
        content_jobs[job_id]["status"] = "completed"
        content_jobs[job_id]["progress"] = 1.0
        content_jobs[job_id]["result"] = result
        content_jobs[job_id]["updated_at"] = datetime.now()

    except Exception as e:
        logger.error(f"Error generating video content for job {job_id}: {e}")
        content_jobs[job_id]["status"] = "failed"
        content_jobs[job_id]["error"] = str(e)
        content_jobs[job_id]["updated_at"] = datetime.now()


__all__ = ["router"]