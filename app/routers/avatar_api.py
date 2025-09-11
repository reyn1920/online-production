import base64
import io
import os
import sqlite3
import sys
from typing import Any, Dict, List, Optional

from avatar.background_remover import BackgroundRemover
from avatar.channel_avatar_manager import ChannelAvatarManager
from avatar.golden_ratio_generator import GoldenRatioAvatarGenerator
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from PIL import Image
from pydantic import BaseModel

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), "../../backend"))


router = APIRouter(prefix="/api/avatar", tags=["avatar"])

# Initialize components
avatar_generator = GoldenRatioAvatarGenerator()
background_remover = BackgroundRemover()
channel_manager = ChannelAvatarManager()

# Pydantic models


class AvatarGenerationRequest(BaseModel):
    style: str = "geometric"
    color_scheme: str = "monochrome"
    size: int = 400
    customizations: Dict[str, Any] = {
        "complexity": 0.6,
        "symmetry": 0.8,
        "golden_ratio_emphasis": 0.8,
        "transparency": True,
        "border_style": "none",
        "texture": "smooth",
    }


class ImageProcessRequest(BaseModel):
    image_data: str  # Base64 encoded image
    enhance: bool = True
    target_size: Optional[int] = None


class AvatarSaveRequest(BaseModel):
    channel_id: int
    image_data: str  # Base64 encoded image
    make_default: bool = True
    metadata: Optional[Dict[str, Any]] = None


class ChannelAvatarRequest(BaseModel):
    channel_id: int
    style: Optional[str] = "golden_ratio"
    color_scheme: Optional[str] = "monochrome"
    force_regenerate: bool = False


@router.post("/generate")
async def generate_avatar(request: AvatarGenerationRequest):
    """
    Generate a new avatar using golden ratio principles
    """
    try:
        # Generate the avatar
        result = avatar_generator.generate_avatar(
            style=request.style,
            color_scheme=request.color_scheme,
            size=request.size,
            **request.customizations,
        )

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])

        # Convert PIL Image to base64
        img_buffer = io.BytesIO()
        result["image"].save(img_buffer, format="PNG")
        img_buffer.seek(0)

        base64_image = base64.b64encode(img_buffer.getvalue()).decode("utf-8")
        base64_data_uri = f"data:image/png;base64,{base64_image}"

        return JSONResponse(
            {
                "success": True,
                "base64_image": base64_data_uri,
                "metadata": result["metadata"],
                "style": request.style,
                "color_scheme": request.color_scheme,
                "size": request.size,
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Avatar generation failed: {
                str(e)}",
        )


@router.post("/process-upload")
async def process_uploaded_image(request: ImageProcessRequest):
    """
    Process an uploaded image by removing background and enhancing transparency
    """
    try:
        # Decode base64 image
        if request.image_data.startswith("data:image"):
            # Remove data URI prefix
            base64_data = request.image_data.split(",")[1]
        else:
            base64_data = request.image_data

        image_bytes = base64.b64decode(base64_data)
        image = Image.open(io.BytesIO(image_bytes))

        # Remove background
        processed_result = background_remover.remove_background(
            image, enhance_transparency=request.enhance
        )

        if not processed_result["success"]:
            raise HTTPException(status_code=400, detail=processed_result["error"])

        processed_image = processed_result["image"]

        # Resize if requested
        if request.target_size:
            processed_image = processed_image.resize(
                (request.target_size, request.target_size), Image.Resampling.LANCZOS
            )

        # Convert back to base64
        img_buffer = io.BytesIO()
        processed_image.save(img_buffer, format="PNG")
        img_buffer.seek(0)

        base64_processed = base64.b64encode(img_buffer.getvalue()).decode("utf-8")
        base64_data_uri = f"data:image/png;base64,{base64_processed}"

        return JSONResponse(
            {
                "success": True,
                "processed_image": base64_data_uri,
                "original_size": image.size,
                "processed_size": processed_image.size,
                "has_transparency": processed_image.mode in ("RGBA", "LA"),
                "metadata": processed_result.get("metadata", {}),
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Image processing failed: {
                str(e)}",
        )


@router.post("/save")
async def save_avatar_to_channel(request: AvatarSaveRequest):
    """
    Save an avatar to a specific channel
    """
    try:
        # Decode base64 image
        if request.image_data.startswith("data:image"):
            base64_data = request.image_data.split(",")[1]
        else:
            base64_data = request.image_data

        image_bytes = base64.b64decode(base64_data)
        image = Image.open(io.BytesIO(image_bytes))

        # Save avatar using channel manager
        result = channel_manager.save_avatar(
            channel_id=request.channel_id,
            image=image,
            is_default=request.make_default,
            metadata=request.metadata or {},
        )

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])

        return JSONResponse(
            {
                "success": True,
                "avatar_id": result["avatar_id"],
                "file_path": result["file_path"],
                "is_default": request.make_default,
                "message": "Avatar saved successfully",
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save avatar: {str(e)}")


@router.get("/channel/{channel_id}")
async def get_channel_avatar(channel_id: int):
    """
    Get the current avatar for a channel, generating one if none exists
    """
    try:
        result = channel_manager.get_or_create_avatar(channel_id)

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])

        # Convert image to base64 if it exists
        avatar_data = None
        if result.get("image"):
            img_buffer = io.BytesIO()
            result["image"].save(img_buffer, format="PNG")
            img_buffer.seek(0)

            base64_image = base64.b64encode(img_buffer.getvalue()).decode("utf-8")
            avatar_data = f"data:image/png;base64,{base64_image}"

        return JSONResponse(
            {
                "success": True,
                "avatar_id": result.get("avatar_id"),
                "image_data": avatar_data,
                "file_path": result.get("file_path"),
                "is_default": result.get("is_default", False),
                "was_generated": result.get("was_generated", False),
                "metadata": result.get("metadata", {}),
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get channel avatar: {
                str(e)}",
        )


@router.post("/channel/generate")
async def generate_channel_avatar(request: ChannelAvatarRequest):
    """
    Generate a new avatar for a specific channel
    """
    try:
        result = channel_manager.generate_avatar_for_channel(
            channel_id=request.channel_id,
            style=request.style,
            color_scheme=request.color_scheme,
            force_regenerate=request.force_regenerate,
        )

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])

        # Convert image to base64
        img_buffer = io.BytesIO()
        result["image"].save(img_buffer, format="PNG")
        img_buffer.seek(0)

        base64_image = base64.b64encode(img_buffer.getvalue()).decode("utf-8")
        base64_data_uri = f"data:image/png;base64,{base64_image}"

        return JSONResponse(
            {
                "success": True,
                "avatar_id": result["avatar_id"],
                "image_data": base64_data_uri,
                "file_path": result["file_path"],
                "style": request.style,
                "color_scheme": request.color_scheme,
                "metadata": result.get("metadata", {}),
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate channel avatar: {
                str(e)}",
        )


@router.get("/channels")
async def get_all_channels():
    """
    Get all available channels
    """
    try:
        channels = channel_manager.get_all_channels()
        return JSONResponse(channels)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get channels: {str(e)}")


@router.get("/channel/{channel_id}/avatars")
async def get_channel_avatars(channel_id: int):
    """
    Get all avatars for a specific channel
    """
    try:
        avatars = channel_manager.get_channel_avatars(channel_id)

        # Convert images to base64 for each avatar
        for avatar in avatars:
            if avatar.get("file_path") and os.path.exists(avatar["file_path"]):
                try:
                    with Image.open(avatar["file_path"]) as img:
                        img_buffer = io.BytesIO()
                        img.save(img_buffer, format="PNG")
                        img_buffer.seek(0)

                        base64_image = base64.b64encode(img_buffer.getvalue()).decode(
                            "utf-8"
                        )
                        avatar["image_data"] = f"data:image/png;base64,{base64_image}"
                except Exception as img_error:
                    print(f"Error loading avatar image: {img_error}")
                    avatar["image_data"] = None

        return JSONResponse({"success": True, "avatars": avatars})

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get channel avatars: {
                str(e)}",
        )


@router.delete("/avatar/{avatar_id}")
async def delete_avatar(avatar_id: int):
    """
    Delete a specific avatar
    """
    try:
        result = channel_manager.delete_avatar(avatar_id)

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])

        return JSONResponse({"success": True, "message": "Avatar deleted successfully"})

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete avatar: {
                str(e)}",
        )


@router.get("/styles")
async def get_available_styles():
    """
    Get all available avatar styles
    """
    return JSONResponse(
        {
            "styles": [
                {
                    "id": "geometric",
                    "name": "Geometric",
                    "description": "Clean geometric shapes with golden ratio proportions",
                },
                {
                    "id": "organic",
                    "name": "Organic",
                    "description": "Natural, flowing forms inspired by nature",
                },
                {
                    "id": "professional",
                    "name": "Professional",
                    "description": "Clean, business-appropriate designs",
                },
                {
                    "id": "artistic",
                    "name": "Artistic",
                    "description": "Creative and expressive designs",
                },
                {
                    "id": "minimal",
                    "name": "Minimal",
                    "description": "Simple, clean designs with maximum impact",
                },
                {
                    "id": "golden_ratio",
                    "name": "Golden Ratio",
                    "description": "Pure mathematical beauty based on golden ratio",
                },
            ],
            "color_schemes": [
                {
                    "id": "monochrome",
                    "name": "Monochrome",
                    "description": "Single color with variations",
                },
                {
                    "id": "complementary",
                    "name": "Complementary",
                    "description": "Opposite colors on the color wheel",
                },
                {
                    "id": "triadic",
                    "name": "Triadic",
                    "description": "Three evenly spaced colors",
                },
                {
                    "id": "warm",
                    "name": "Warm",
                    "description": "Warm colors like reds, oranges, yellows",
                },
                {
                    "id": "cool",
                    "name": "Cool",
                    "description": "Cool colors like blues, greens, purples",
                },
                {
                    "id": "vibrant",
                    "name": "Vibrant",
                    "description": "Bright, energetic colors",
                },
            ],
        }
    )


@router.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return JSONResponse(
        {
            "status": "healthy",
            "components": {
                "avatar_generator": "ready",
                "background_remover": "ready",
                "channel_manager": "ready",
            },
        }
    )
