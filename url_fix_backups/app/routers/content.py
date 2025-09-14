# app / routers / content.py - Content generation and management router

import asyncio
import json
import logging
import os
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

    from content_agent.main import (ContentAgent, ContentConfig, ContentRequest,

        ContentResponse)
except ImportError:
    try:

        from backend.agents.content_agent import ContentAgent

    except ImportError:
        ContentAgent = None
        logging.warning("Content agent not available - check backend structure")

try:

    from backend.agents.specialized_agents import \\

        ContentAgent as SpecializedContentAgent
except ImportError:
    SpecializedContentAgent = None
    logging.warning("Specialized content agent not available")

router = APIRouter()
templates = Jinja2Templates(directory="templates")
logger = logging.getLogger(__name__)

# Request / Response Models


class ContentGenerationRequest(BaseModel):
    type: str = Field(default="article", description="Type of content to generate")
    topic: str = Field(..., description="Topic or subject for content generation")
    format: Optional[str] = Field(
        default="educational", description="Content format style"
    )
    target_length: Optional[int] = Field(
        default = 500, description="Target length in words"
    )
    tone: Optional[str] = Field(default="professional", description="Content tone")
    audience: Optional[str] = Field(default="general", description="Target audience")
    keywords: Optional[List[str]] = Field(
        default=[], description="SEO keywords to include"
    )
    include_images: Optional[bool] = Field(
        default = False, description="Include image suggestions"
    )


class VideoContentRequest(BaseModel):
    topic: str = Field(..., description="Video topic")
    duration: Optional[int] = Field(default = 300, description="Duration in seconds")
    style: Optional[str] = Field(default="educational", description="Video style")
    voice: Optional[str] = Field(
        default="default", description="Voice type for narration"
    )
    resolution: Optional[str] = Field(
        default="1920x1080", description="Video resolution"
    )
    include_avatar: Optional[bool] = Field(
        default = False, description="Include AI avatar"
    )


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

# In - memory job tracking (in production, use Redis or database)
content_jobs = {}
content_agent_instance = None

# Initialize content agent


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
                    logger.info(
                        "✅ ContentAgent initialized from backend.agents.content_agent"
                    )
                except ImportError:
                    # Final fallback to specialized agent

                    from backend.agents.specialized_agents import \\

                        ContentAgent as SpecializedContentAgent

                    content_agent_instance = SpecializedContentAgent(
                        agent_id="content_agent_001", name="ContentAgent"
                    )
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
                    ],
                },
            )

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
                },
            }

@router.get("/trending")


async def get_trending_topics():
    """Get trending topics for content inspiration"""
    agent = get_content_agent()

    if not agent or not hasattr(agent, "news_watcher"):
        # Fallback trending topics
        fallback_topics = [
            {
                "title": "AI and Machine Learning Trends",
                    "category": "technology",
                    "score": 0.9,
                    },
                {
                "title": "Sustainable Business Practices",
                    "category": "business",
                    "score": 0.8,
                    },
                {
                "title": "Remote Work Productivity",
                    "category": "workplace",
                    "score": 0.7,
                    },
                {
                "title": "Digital Marketing Strategies",
                    "category": "marketing",
                    "score": 0.6,
                    },
                {
                "title": "Health and Wellness Tips",
                    "category": "lifestyle",
                    "score": 0.5,
                    },
                ]
        return TrendingTopicsResponse(
            topics = fallback_topics, updated_at = datetime.now(), source="fallback"
        )

    try:
        topics = agent.news_watcher.get_trending_topics(limit = 10)
        return TrendingTopicsResponse(
            topics = topics, updated_at = datetime.now(), source="live_feeds"
        )
    except Exception as e:
        logger.error(f"Error getting trending topics: {e}")
        raise HTTPException(status_code = 500, detail="Failed to get trending topics")

@router.post("/generate")


async def generate_content(
    request: ContentGenerationRequest, background_tasks: BackgroundTasks
):
    """Generate text content"""
    agent = get_content_agent()

    if not agent:
        raise HTTPException(status_code = 503, detail="Content agent not available")

    # Create job ID
    job_id = str(uuid.uuid4())

    # Store job info
    content_jobs[job_id] = {
        "status": "processing",
            "progress": 0.0,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "type": "text_content",
            "request": request.dict(),
            }

    # Start content generation in background
    background_tasks.add_task(_generate_text_content, job_id, request, agent)

    return {"job_id": job_id, "status": "started"}

@router.post("/generate - video")


async def generate_video_content(
    request: VideoContentRequest, background_tasks: BackgroundTasks
):
    """Generate video content"""
    agent = get_content_agent()

    if not agent or not hasattr(agent, "script_generator"):
        raise HTTPException(status_code = 503, detail="Video generation not available")

    # Create job ID
    job_id = str(uuid.uuid4())

    # Store job info
    content_jobs[job_id] = {
        "status": "processing",
            "progress": 0.0,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "type": "video_content",
            "request": request.dict(),
            }

    # Start video generation in background
    background_tasks.add_task(_generate_video_content, job_id, request, agent)

    return {"job_id": job_id, "status": "started"}

@router.get("/status/{job_id}")


async def get_content_status(job_id: str):
    """Get status of content generation job"""
    if job_id not in content_jobs:
        raise HTTPException(status_code = 404, detail="Job not found")

    job_info = content_jobs[job_id]
    return ContentStatusResponse(
        job_id = job_id,
            status = job_info["status"],
            progress = job_info.get("progress"),
            result = job_info.get("result"),
            error = job_info.get("error"),
            created_at = job_info["created_at"],
            updated_at = job_info["updated_at"],
            )

@router.get("/download/{job_id}")


async def download_content(job_id: str):
    """Download generated content file"""
    if job_id not in content_jobs:
        raise HTTPException(status_code = 404, detail="Job not found")

    job_info = content_jobs[job_id]
    if job_info["status"] != "completed" or not job_info.get("result", {}).get(
        "file_path"
    ):
        raise HTTPException(status_code = 400, detail="Content not ready for download")

    file_path = job_info["result"]["file_path"]
    if not os.path.exists(file_path):
        raise HTTPException(status_code = 404, detail="Content file not found")

    # Determine media type based on file extension
    file_ext = Path(file_path).suffix.lower()
    media_type_map = {
        ".mp4": "video / mp4",
            ".mp3": "audio / mpeg",
            ".wav": "audio / wav",
            ".txt": "text / plain",
            ".json": "application / json",
            ".pdf": "application / pdf",
            }

    media_type = media_type_map.get(file_ext, "application / octet - stream")
    filename = f"content_{job_id}{file_ext}"

    return FileResponse(path = file_path, filename = filename, media_type = media_type)

@router.get("/templates")


async def get_content_templates():
    """Get available content templates"""
    templates_data = {
        "article": {
            "structure": ["introduction", "main_points", "conclusion"],
                "recommended_length": "800 - 1200 words",
                "tone_options": ["professional", "casual", "academic", "conversational"],
                },
            "blog_post": {
            "structure": ["hook", "problem", "solution", "call_to_action"],
                "recommended_length": "600 - 1000 words",
                "tone_options": ["friendly", "informative", "persuasive", "entertaining"],
                },
            "social_media": {
            "structure": ["hook", "value", "engagement"],
                "recommended_length": "50 - 280 characters",
                "tone_options": ["casual", "witty", "inspirational", "promotional"],
                },
            "video_script": {
            "structure": [
                "hook",
                    "introduction",
                    "main_content",
                    "conclusion",
                    "call_to_action",
                    ],
                "recommended_length": "150 - 200 words per minute",
                "tone_options": [
                "educational",
                    "entertaining",
                    "promotional",
                    "documentary",
                    ],
                },
            }

    return {"templates": templates_data}

@router.delete("/jobs/{job_id}")


async def delete_content_job(job_id: str):
    """Delete content generation job and cleanup files"""
    if job_id not in content_jobs:
        raise HTTPException(status_code = 404, detail="Job not found")

    job_info = content_jobs[job_id]

    # Cleanup result file if exists
    if job_info.get("result", {}).get("file_path"):
        file_path = job_info["result"]["file_path"]
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                logger.warning(f"Failed to cleanup file {file_path}: {e}")

    # Remove job from tracking
    del content_jobs[job_id]

    return {"success": True, "message": "Job deleted successfully"}

@router.get("/jobs")


async def list_content_jobs():
    """List all content generation jobs"""
    jobs = []
    for job_id, job_info in content_jobs.items():
        jobs.append(
            {
                "job_id": job_id,
                    "status": job_info["status"],
                    "progress": job_info.get("progress"),
                    "type": job_info.get("type"),
                    "created_at": job_info["created_at"],
                    "updated_at": job_info["updated_at"],
                    }
        )

    return {"jobs": jobs, "total": len(jobs)}

# Background task functions


async def _generate_text_content(job_id: str, request: ContentGenerationRequest, agent):
    """Background task for text content generation"""
    try:
        # Update progress
        content_jobs[job_id]["progress"] = 25.0
        content_jobs[job_id]["updated_at"] = datetime.now()

        # Generate content based on agent type
        if hasattr(agent, "create_content"):
            # Use specialized agent
            result = await agent.create_content(
                content_type = request.type,
                    topic = request.topic,
                    target_length = request.target_length,
                    tone = request.tone,
                    )
        else:
            # Fallback content generation
            result = {
                "content": f"Generated {
                    request.type} about {
                        request.topic}\\n\\nThis is a sample content generated for the topic '{
                        request.topic}' in {
                        request.tone} tone. The content would be approximately {
                        request.target_length} words long and tailored for {
                            request.audience} audience.",
                                "title": f"{
                    request.topic} - {
                                    request.type.title()}",
                                        "metadata": {
                    "word_count": request.target_length,
                        "tone": request.tone,
                        "type": request.type,
                        },
                    }

        # Update progress
        content_jobs[job_id]["progress"] = 75.0
        content_jobs[job_id]["updated_at"] = datetime.now()

        # Save content to file
        output_dir = Path("output / content")
        output_dir.mkdir(parents = True, exist_ok = True)

        file_path = output_dir / f"content_{job_id}.txt"
        with open(file_path, "w", encoding="utf - 8") as f:
            f.write(result.get("content", ""))

        # Complete job
        content_jobs[job_id].update(
            {
                "status": "completed",
                    "progress": 100.0,
                    "result": {
                    "content": result.get("content", ""),
                        "title": result.get("title", ""),
                        "metadata": result.get("metadata", {}),
                        "file_path": str(file_path),
                        },
                    "updated_at": datetime.now(),
                    }
        )

    except Exception as e:
        logger.error(f"Error generating text content: {e}")
        content_jobs[job_id].update(
            {"status": "failed", "error": str(e), "updated_at": datetime.now()}
        )


async def _generate_video_content(job_id: str, request: VideoContentRequest, agent):
    """Background task for video content generation"""
    try:
        # Update progress
        content_jobs[job_id]["progress"] = 10.0
        content_jobs[job_id]["updated_at"] = datetime.now()

        # Generate script
        script_data = await agent.script_generator.generate_script(
            topic = request.topic, duration = request.duration, style = request.style
        )

        # Update progress
        content_jobs[job_id]["progress"] = 30.0
        content_jobs[job_id]["updated_at"] = datetime.now()

        # Generate audio
        output_dir = Path("output / content")
        output_dir.mkdir(parents = True, exist_ok = True)

        audio_path = output_dir / f"audio_{job_id}.wav"
        await agent.tts_engine.generate_audio(
            text = script_data.get("transcript", ""),
                output_path = str(audio_path),
                voice = request.voice,
                )

        # Update progress
        content_jobs[job_id]["progress"] = 60.0
        content_jobs[job_id]["updated_at"] = datetime.now()

        # Generate video
        video_path = output_dir / f"video_{job_id}.mp4"
        if hasattr(agent, "avatar_generator"):
            final_video = agent.avatar_generator.create_avatar_video(
                script_data = script_data,
                    audio_path = str(audio_path),
                    output_path = str(video_path),
                    )
        else:
            # Create simple video with text overlay
            final_video = str(video_path)
            # This would need actual video creation logic

        # Complete job
        content_jobs[job_id].update(
            {
                "status": "completed",
                    "progress": 100.0,
                    "result": {
                    "script": script_data,
                        "video_path": final_video,
                        "audio_path": str(audio_path),
                        "file_path": final_video,
                        "duration": request.duration,
                        },
                    "updated_at": datetime.now(),
                    }
        )

    except Exception as e:
        logger.error(f"Error generating video content: {e}")
        content_jobs[job_id].update(
            {"status": "failed", "error": str(e), "updated_at": datetime.now()}
        )

# Export router
__all__ = ["router"]