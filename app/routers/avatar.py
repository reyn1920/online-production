# app/routers/avatar.py - Avatar generation and 3D pipeline router
from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os
import logging
from datetime import datetime
import tempfile
import uuid

# Import avatar services
try:
    from backend.services.avatar_engines import engine_manager, AvatarRequest, AvatarResponse
except ImportError:
    engine_manager = None
    logging.warning("Avatar engines not available - check backend structure")

try:
    from backend.avatar_pipeline import AvatarPipeline, CharacterSpec, AnimationSpec
except ImportError:
    try:
        from copy_of_code.avatar_pipeline import AvatarPipeline, CharacterSpec, AnimationSpec
    except ImportError:
        AvatarPipeline = None
        logging.warning("Avatar pipeline not available - check backend structure")

router = APIRouter()
templates = Jinja2Templates(directory="templates")
logger = logging.getLogger(__name__)

# Request/Response Models


class AvatarGenerationRequest(BaseModel):
    text: str = Field(..., description="Text for the avatar to speak")
    voice_settings: Optional[Dict[str, Any]] = Field(
        default={}, description="Voice configuration")
    video_settings: Optional[Dict[str, Any]] = Field(
        default={}, description="Video configuration")
    source_image: Optional[str] = Field(
        None, description="Base64 encoded source image or image URL")
    engine: Optional[str] = Field("linly-talker", description="Avatar engine to use")
    gender: Optional[str] = Field(
        "neutral", description="Avatar gender (neutral, male, female)")


class Avatar3DRequest(BaseModel):
    character_description: str = Field(...,
                                       description="Description of the 3D character to create")
    animation_type: Optional[str] = Field(
        "idle", description="Type of animation to apply")
    voice_text: Optional[str] = Field(None, description="Text for voice synthesis")
    export_format: Optional[str] = Field(
        "mp4", description="Export format (mp4, fbx, obj)")
    quality: Optional[str] = Field(
        "medium", description="Rendering quality (low, medium, high)")
    gender: Optional[str] = Field(
        "neutral", description="Avatar gender (neutral, male, female)")


class AvatarStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: Optional[float] = None
    result_url: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# In-memory job tracking (in production, use Redis or database)
avatar_jobs = {}


@router.get("/")
async def avatar_interface(request: Request):
    """Avatar generation interface"""
    return templates.TemplateResponse("avatar.html", {
        "request": request,
        "title": "Avatar Generation",
        "engines": await get_available_engines()
    })


@router.get("/health")
async def health_check():
    """Health check for avatar services"""
    status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "engines": {},
        "pipeline": AvatarPipeline is not None
    }

    if engine_manager:
        try:
            engines = await engine_manager.get_available_engines()
            for engine_name in engines:
                engine = await engine_manager.get_engine(engine_name)
                if engine:
                    status["engines"][engine_name] = await engine.health_check()
        except Exception as e:
            logger.error(f"Error checking engine health: {e}")
            status["engines"]["error"] = str(e)

    return status


@router.get("/engines")
async def get_available_engines():
    """Get list of available avatar engines"""
    if not engine_manager:
        return {"engines": [], "error": "Avatar engines not available"}

    try:
        engines = await engine_manager.get_available_engines()
        engine_info = []

        for engine_name in engines:
            engine = await engine_manager.get_engine(engine_name)
            if engine:
                health = await engine.health_check()
                engine_info.append({
                    "name": engine_name,
                    "healthy": health,
                    "capabilities": getattr(engine, 'capabilities', [])
                })

        return {"engines": engine_info}
    except Exception as e:
        logger.error(f"Error getting available engines: {e}")
        raise HTTPException(status_code=500, detail="Failed to get available engines")


@router.post("/generate")
async def generate_avatar(request: AvatarGenerationRequest):
    """Generate avatar using specified engine"""
    if not engine_manager:
        raise HTTPException(status_code=503, detail="Avatar engines not available")

    try:
        # Create job ID
        job_id = str(uuid.uuid4())

        # Get engine
        engine = await engine_manager.get_engine(request.engine)
        if not engine:
            raise HTTPException(
                status_code=400, detail=f"Engine {
                    request.engine} not available")

        # Check engine health
        if not await engine.health_check():
            raise HTTPException(
                status_code=503, detail=f"Engine {
                    request.engine} is not responding")

        # Create avatar request
        avatar_request = AvatarRequest(
            text=request.text,
            voice_settings=request.voice_settings,
            video_settings=request.video_settings,
            source_image=request.source_image,
            gender=request.gender
        )

        # Store job info
        avatar_jobs[job_id] = {
            "status": "processing",
            "progress": 0.0,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "engine": request.engine
        }

        # Start generation (async)
        try:
            response = await engine.generate_avatar(avatar_request)

            if response.success:
                avatar_jobs[job_id].update({
                    "status": "completed",
                    "progress": 100.0,
                    "result_url": response.output_path,
                    "updated_at": datetime.now()
                })
            else:
                avatar_jobs[job_id].update({
                    "status": "failed",
                    "error": response.error,
                    "updated_at": datetime.now()
                })
        except Exception as e:
            avatar_jobs[job_id].update({
                "status": "failed",
                "error": str(e),
                "updated_at": datetime.now()
            })

        return {"job_id": job_id, "status": "started"}

    except Exception as e:
        logger.error(f"Error generating avatar: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate avatar")


@router.post("/generate-3d")
async def generate_3d_avatar(request: Avatar3DRequest):
    """Generate 3D avatar using the avatar pipeline"""
    if not AvatarPipeline:
        raise HTTPException(status_code=503, detail="3D Avatar pipeline not available")

    try:
        # Create job ID
        job_id = str(uuid.uuid4())

        # Store job info
        avatar_jobs[job_id] = {
            "status": "processing",
            "progress": 0.0,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "type": "3d_pipeline"
        }

        # Initialize pipeline
        pipeline = AvatarPipeline()

        # Create character spec
        character_spec = CharacterSpec(
            description=request.character_description,
            gender=request.gender or "neutral",
            age_range="adult",
            style="realistic"
        )

        # Create animation spec if voice text provided
        animation_spec = None
        if request.voice_text:
            animation_spec = AnimationSpec(
                animation_type=request.animation_type,
                voice_text=request.voice_text,
                duration=None  # Auto-calculate from text
            )

        # Start generation (async)
        try:
            result = await pipeline.create_avatar(
                spec=character_spec,
                animation_spec=animation_spec,
                output_format=request.export_format,
                quality=request.quality
            )

            avatar_jobs[job_id].update({
                "status": "completed",
                "progress": 100.0,
                "result_url": str(result.final_render_path),
                "metadata": result.metadata,
                "updated_at": datetime.now()
            })

        except Exception as e:
            avatar_jobs[job_id].update({
                "status": "failed",
                "error": str(e),
                "updated_at": datetime.now()
            })

        return {"job_id": job_id, "status": "started"}

    except Exception as e:
        logger.error(f"Error generating 3D avatar: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate 3D avatar")


@router.get("/status/{job_id}")
async def get_avatar_status(job_id: str):
    """Get status of avatar generation job"""
    if job_id not in avatar_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job_info = avatar_jobs[job_id]
    return AvatarStatusResponse(
        job_id=job_id,
        status=job_info["status"],
        progress=job_info.get("progress"),
        result_url=job_info.get("result_url"),
        error=job_info.get("error"),
        created_at=job_info["created_at"],
        updated_at=job_info["updated_at"]
    )


@router.get("/download/{job_id}")
async def download_avatar(job_id: str):
    """Download generated avatar file"""
    if job_id not in avatar_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job_info = avatar_jobs[job_id]
    if job_info["status"] != "completed" or not job_info.get("result_url"):
        raise HTTPException(status_code=400, detail="Avatar not ready for download")

    result_path = job_info["result_url"]
    if not os.path.exists(result_path):
        raise HTTPException(status_code=404, detail="Avatar file not found")

    return FileResponse(
        path=result_path,
        filename=f"avatar_{job_id}.mp4",
        media_type="video/mp4"
    )


@router.post("/upload-image")
async def upload_source_image(file: UploadFile = File(...)):
    """Upload source image for avatar generation"""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name

        # Return file path for use in generation
        return {
            "success": True,
            "file_path": tmp_file_path,
            "filename": file.filename,
            "size": len(content)
        }

    except Exception as e:
        logger.error(f"Error uploading image: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload image")


@router.delete("/jobs/{job_id}")
async def delete_avatar_job(job_id: str):
    """Delete avatar generation job and cleanup files"""
    if job_id not in avatar_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job_info = avatar_jobs[job_id]

    # Cleanup result file if exists
    if job_info.get("result_url") and os.path.exists(job_info["result_url"]):
        try:
            os.remove(job_info["result_url"])
        except Exception as e:
            logger.warning(f"Failed to cleanup file {job_info['result_url']}: {e}")

    # Remove job from tracking
    del avatar_jobs[job_id]

    return {"success": True, "message": "Job deleted successfully"}


@router.get("/jobs")
async def list_avatar_jobs():
    """List all avatar generation jobs"""
    jobs = []
    for job_id, job_info in avatar_jobs.items():
        jobs.append({
            "job_id": job_id,
            "status": job_info["status"],
            "progress": job_info.get("progress"),
            "created_at": job_info["created_at"],
            "updated_at": job_info["updated_at"],
            "type": job_info.get("type", "standard")
        })

    return {"jobs": jobs, "total": len(jobs)}

# Export router
__all__ = ["router"]
