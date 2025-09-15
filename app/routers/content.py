#!/usr/bin/env python3
"""
Content generation and management router
Provides endpoints for content creation, video generation, and content management.
"""

import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/content", tags=["content"])

# In-memory storage for demo purposes
content_storage: Dict[str, Dict[str, Any]] = {}
video_storage: Dict[str, Dict[str, Any]] = {}

# Pydantic models
class ContentRequest(BaseModel):
    title: str = Field(..., description="Content title")
    description: Optional[str] = Field(None, description="Content description")
    content_type: str = Field("article", description="Type of content")
    tags: List[str] = Field(default_factory=list, description="Content tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class ContentResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    content_type: str
    tags: List[str]
    metadata: Dict[str, Any]
    created_at: str
    status: str

class VideoRequest(BaseModel):
    title: str = Field(..., description="Video title")
    script: str = Field(..., description="Video script")
    style: str = Field("default", description="Video style")
    duration: Optional[int] = Field(None, description="Target duration in seconds")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class VideoResponse(BaseModel):
    id: str
    title: str
    script: str
    style: str
    duration: Optional[int]
    metadata: Dict[str, Any]
    created_at: str
    status: str
    video_url: Optional[str] = None

# Content endpoints
@router.post("/create", response_model=ContentResponse)
async def create_content(request: ContentRequest):
    """Create new content"""
    try:
        content_id = str(uuid.uuid4())
        
        content_data = {
            "id": content_id,
            "title": request.title,
            "description": request.description,
            "content_type": request.content_type,
            "tags": request.tags,
            "metadata": request.metadata,
            "created_at": datetime.now().isoformat(),
            "status": "created"
        }
        
        content_storage[content_id] = content_data
        
        logger.info(f"Created content: {content_id}")
        return ContentResponse(
            id=str(content_data["id"]),
            title=str(content_data["title"]),
            description=str(content_data["description"]) if content_data["description"] is not None else None,
            content_type=str(content_data["content_type"]),
            tags=content_data["tags"] if isinstance(content_data["tags"], list) else [],
            metadata=content_data["metadata"] if isinstance(content_data["metadata"], dict) else {},
            created_at=str(content_data["created_at"]),
            status=str(content_data["status"])
        )
        
    except Exception as e:
        logger.error(f"Error creating content: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create content")

@router.get("/list", response_model=List[ContentResponse])
async def list_content():
    """List all content"""
    try:
        content_list = []
        for data in content_storage.values():
            content_list.append(ContentResponse(
                id=str(data["id"]),
                title=str(data["title"]),
                description=str(data["description"]) if data["description"] is not None else None,
                content_type=str(data["content_type"]),
                tags=data["tags"] if isinstance(data["tags"], list) else [],
                metadata=data["metadata"] if isinstance(data["metadata"], dict) else {},
                created_at=str(data["created_at"]),
                status=str(data["status"])
            ))
        return content_list
    except Exception as e:
        logger.error(f"Error listing content: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list content")

@router.get("/{content_id}", response_model=ContentResponse)
async def get_content(content_id: str):
    """Get specific content by ID"""
    if content_id not in content_storage:
        raise HTTPException(status_code=404, detail="Content not found")
    
    data = content_storage[content_id]
    return ContentResponse(
        id=str(data["id"]),
        title=str(data["title"]),
        description=str(data["description"]) if data["description"] is not None else None,
        content_type=str(data["content_type"]),
        tags=data["tags"] if isinstance(data["tags"], list) else [],
        metadata=data["metadata"] if isinstance(data["metadata"], dict) else {},
        created_at=str(data["created_at"]),
        status=str(data["status"])
    )

@router.delete("/{content_id}")
async def delete_content(content_id: str):
    """Delete content by ID"""
    if content_id not in content_storage:
        raise HTTPException(status_code=404, detail="Content not found")
    
    del content_storage[content_id]
    logger.info(f"Deleted content: {content_id}")
    return {"message": "Content deleted successfully"}

# Video endpoints
@router.post("/video/create", response_model=VideoResponse)
async def create_video(request: VideoRequest, background_tasks: BackgroundTasks):
    """Create new video content"""
    try:
        video_id = str(uuid.uuid4())
        
        video_data = {
            "id": video_id,
            "title": request.title,
            "script": request.script,
            "style": request.style,
            "duration": request.duration,
            "metadata": request.metadata,
            "created_at": datetime.now().isoformat(),
            "status": "processing",
            "video_url": None
        }
        
        video_storage[video_id] = video_data
        
        # Simulate video processing in background
        background_tasks.add_task(process_video, video_id)
        
        logger.info(f"Created video: {video_id}")
        return VideoResponse(
            id=str(video_data["id"]),
            title=str(video_data["title"]),
            script=str(video_data["script"]),
            style=str(video_data["style"]),
            duration=video_data["duration"] if isinstance(video_data["duration"], int) else None,
            metadata=video_data["metadata"] if isinstance(video_data["metadata"], dict) else {},
            created_at=str(video_data["created_at"]),
            status=str(video_data["status"]),
            video_url=str(video_data["video_url"]) if video_data["video_url"] is not None else None
        )
        
    except Exception as e:
        logger.error(f"Error creating video: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create video")

@router.get("/video/list", response_model=List[VideoResponse])
async def list_videos():
    """List all videos"""
    try:
        video_list = []
        for data in video_storage.values():
            video_list.append(VideoResponse(
                id=str(data["id"]),
                title=str(data["title"]),
                script=str(data["script"]),
                style=str(data["style"]),
                duration=data["duration"] if isinstance(data["duration"], int) else None,
                metadata=data["metadata"] if isinstance(data["metadata"], dict) else {},
                created_at=str(data["created_at"]),
                status=str(data["status"]),
                video_url=str(data["video_url"]) if data["video_url"] is not None else None
            ))
        return video_list
    except Exception as e:
        logger.error(f"Error listing videos: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list videos")

@router.get("/video/{video_id}", response_model=VideoResponse)
async def get_video(video_id: str):
    """Get specific video by ID"""
    if video_id not in video_storage:
        raise HTTPException(status_code=404, detail="Video not found")
    
    data = video_storage[video_id]
    return VideoResponse(
        id=str(data["id"]),
        title=str(data["title"]),
        script=str(data["script"]),
        style=str(data["style"]),
        duration=data["duration"] if isinstance(data["duration"], int) else None,
        metadata=data["metadata"] if isinstance(data["metadata"], dict) else {},
        created_at=str(data["created_at"]),
        status=str(data["status"]),
        video_url=str(data["video_url"]) if data["video_url"] is not None else None
    )

@router.delete("/video/{video_id}")
async def delete_video(video_id: str):
    """Delete video by ID"""
    if video_id not in video_storage:
        raise HTTPException(status_code=404, detail="Video not found")
    
    del video_storage[video_id]
    logger.info(f"Deleted video: {video_id}")
    return {"message": "Video deleted successfully"}

# Upload endpoints
@router.post("/upload")
async def upload_content(file: UploadFile = File(...), title: str = Form(...)):
    """Upload content file"""
    try:
        # Simulate file processing
        content_id = str(uuid.uuid4())
        
        content_data = {
            "id": content_id,
            "title": title,
            "description": f"Uploaded file: {file.filename}",
            "content_type": "upload",
            "tags": ["uploaded"],
            "metadata": {
                "filename": file.filename,
                "content_type": file.content_type,
                "size": file.size if hasattr(file, 'size') else 0
            },
            "created_at": datetime.now().isoformat(),
            "status": "uploaded"
        }
        
        content_storage[content_id] = content_data
        
        logger.info(f"Uploaded content: {content_id}")
        return {"message": "File uploaded successfully", "content_id": content_id}
        
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload file")

# Analytics endpoints
@router.get("/analytics")
async def get_content_analytics():
    """Get content analytics"""
    try:
        total_content = len(content_storage)
        total_videos = len(video_storage)
        
        content_types = {}
        for content in content_storage.values():
            content_type = content.get("content_type", "unknown")
            content_types[content_type] = content_types.get(content_type, 0) + 1
        
        video_statuses = {}
        for video in video_storage.values():
            status = video.get("status", "unknown")
            video_statuses[status] = video_statuses.get(status, 0) + 1
        
        return {
            "total_content": total_content,
            "total_videos": total_videos,
            "content_types": content_types,
            "video_statuses": video_statuses,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get analytics")

# Background task for video processing
async def process_video(video_id: str):
    """Simulate video processing"""
    try:
        # Simulate processing time
        import asyncio
        await asyncio.sleep(5)
        
        if video_id in video_storage:
            video_storage[video_id]["status"] = "completed"
            video_storage[video_id]["video_url"] = f"/videos/{video_id}.mp4"
            logger.info(f"Video processing completed: {video_id}")
        
    except Exception as e:
        logger.error(f"Error processing video {video_id}: {str(e)}")
        if video_id in video_storage:
            video_storage[video_id]["status"] = "failed"

# Health check
@router.get("/health")
async def content_health():
    """Content service health check"""
    return {
        "status": "healthy",
        "service": "content",
        "timestamp": datetime.now().isoformat(),
        "content_count": len(content_storage),
        "video_count": len(video_storage)
    }