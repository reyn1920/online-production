#!/usr/bin/env python3
""""""
Avatar API Router
Provides endpoints for avatar generation, processing, and management.
""""""

import base64
import io
import os
import sys
from typing import Any, Dict, Optional

from avatar.background_remover import BackgroundRemover
from avatar.channel_avatar_manager import ChannelAvatarManager
from avatar.golden_ratio_generator import GoldenRatioAvatarGenerator
from fastapi import APIRouter, HTTPException
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
# BRACKET_SURGEON: disabled
#     }


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
    """"""
    Generate a new avatar using golden ratio principles
    """"""
    try:
        # Generate the avatar
        result = avatar_generator.generate_avatar(
            style=request.style,
            color_scheme=request.color_scheme,
            size=request.size,
            **request.customizations,
# BRACKET_SURGEON: disabled
#         )

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
# BRACKET_SURGEON: disabled
#             }
# BRACKET_SURGEON: disabled
#         )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Avatar generation failed: {str(e)}",
# BRACKET_SURGEON: disabled
#         )


@router.post("/process-upload")
async def process_uploaded_image(request: ImageProcessRequest):
    """"""
    Process an uploaded image by removing background and enhancing transparency
    """"""
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
# BRACKET_SURGEON: disabled
#         )

        if not processed_result["success"]:
            raise HTTPException(status_code=400, detail=processed_result["error"])

        processed_image = processed_result["image"]

        # Resize if requested
        if request.target_size:
            processed_image = processed_image.resize(
                (request.target_size, request.target_size), Image.Resampling.LANCZOS
# BRACKET_SURGEON: disabled
#             )

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
# BRACKET_SURGEON: disabled
#             }
# BRACKET_SURGEON: disabled
#         )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Image processing failed: {str(e)}",
# BRACKET_SURGEON: disabled
#         )


@router.post("/save")
async def save_avatar_to_channel(request: AvatarSaveRequest):
    """"""
    Save an avatar to a specific channel
    """"""
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
# BRACKET_SURGEON: disabled
#         )

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])

        return JSONResponse(
            {
                "success": True,
                "avatar_id": result["avatar_id"],
                "file_path": result["file_path"],
                "is_default": request.make_default,
                "metadata": result.get("metadata", {}),
# BRACKET_SURGEON: disabled
#             }
# BRACKET_SURGEON: disabled
#         )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Avatar save failed: {str(e)}",
# BRACKET_SURGEON: disabled
#         )


@router.get("/channel/{channel_id}")
async def get_channel_avatar(channel_id: int):
    """"""
    Get the current avatar for a specific channel
    """"""
    try:
        result = channel_manager.get_channel_avatar(channel_id)

        if not result["success"]:
            raise HTTPException(status_code=404, detail=result["error"])

        return JSONResponse(
            {
                "success": True,
                "avatar_id": result["avatar_id"],
                "file_path": result["file_path"],
                "is_default": result["is_default"],
                "metadata": result.get("metadata", {}),
                "created_at": result.get("created_at"),
# BRACKET_SURGEON: disabled
#             }
# BRACKET_SURGEON: disabled
#         )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get channel avatar: {str(e)}",
# BRACKET_SURGEON: disabled
#         )


@router.post("/channel/generate")
async def generate_channel_avatar(request: ChannelAvatarRequest):
    """"""
    Generate and save a new avatar for a specific channel
    """"""
    try:
        result = channel_manager.generate_channel_avatar(
            channel_id=request.channel_id,
            style=request.style,
            color_scheme=request.color_scheme,
            force_regenerate=request.force_regenerate,
# BRACKET_SURGEON: disabled
#         )

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])

        return JSONResponse(
            {
                "success": True,
                "avatar_id": result["avatar_id"],
                "file_path": result["file_path"],
                "style": request.style,
                "color_scheme": request.color_scheme,
                "metadata": result.get("metadata", {}),
# BRACKET_SURGEON: disabled
#             }
# BRACKET_SURGEON: disabled
#         )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Channel avatar generation failed: {str(e)}",
# BRACKET_SURGEON: disabled
#         )


@router.get("/channels")
async def get_all_channels():
    """"""
    Get all channels with their avatar information
    """"""
    try:
        result = channel_manager.get_all_channels()
        return JSONResponse({"success": True, "channels": result})
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get channels: {str(e)}",
# BRACKET_SURGEON: disabled
#         )


@router.get("/channel/{channel_id}/avatars")
async def get_channel_avatars(channel_id: int):
    """"""
    Get all avatars for a specific channel
    """"""
    try:
        result = channel_manager.get_channel_avatars(channel_id)

        if not result["success"]:
            raise HTTPException(status_code=404, detail=result["error"])

        return JSONResponse(
            {
                "success": True,
                "channel_id": channel_id,
                "avatars": result["avatars"],
                "total_count": len(result["avatars"]),
# BRACKET_SURGEON: disabled
#             }
# BRACKET_SURGEON: disabled
#         )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get channel avatars: {str(e)}",
# BRACKET_SURGEON: disabled
#         )


@router.delete("/avatar/{avatar_id}")
async def delete_avatar(avatar_id: int):
    """"""
    Delete a specific avatar
    """"""
    try:
        result = channel_manager.delete_avatar(avatar_id)

        if not result["success"]:
            raise HTTPException(status_code=404, detail=result["error"])

        return JSONResponse(
            {
                "success": True,
                "message": "Avatar deleted successfully",
                "avatar_id": avatar_id,
# BRACKET_SURGEON: disabled
#             }
# BRACKET_SURGEON: disabled
#         )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete avatar: {str(e)}",
# BRACKET_SURGEON: disabled
#         )


@router.get("/styles")
async def get_available_styles():
    """"""
    Get all available avatar styles and their configurations
    """"""
    return JSONResponse(
        {
            "success": True,
            "styles": {
                "geometric": {
                    "name": "Geometric",
                    "description": "Clean geometric shapes with golden ratio proportions",
                    "color_schemes": ["monochrome", "vibrant", "pastel", "neon"],
# BRACKET_SURGEON: disabled
#                 },
                "organic": {
                    "name": "Organic",
                    "description": "Natural flowing forms with golden ratio harmony",
                    "color_schemes": ["earth", "ocean", "forest", "sunset"],
# BRACKET_SURGEON: disabled
#                 },
                "minimal": {
                    "name": "Minimal",
                    "description": "Simple, clean design with perfect proportions",
                    "color_schemes": ["monochrome", "grayscale", "accent"],
# BRACKET_SURGEON: disabled
#                 },
                "abstract": {
                    "name": "Abstract",
                    "description": "Creative abstract patterns with mathematical beauty",
                    "color_schemes": ["vibrant", "gradient", "complementary"],
# BRACKET_SURGEON: disabled
#                 },
# BRACKET_SURGEON: disabled
#             },
            "color_schemes": {
                "monochrome": {"primary": "#000000", "secondary": "#FFFFFF"},"
                "vibrant": {"primary": "#FF6B6B", "secondary": "#4ECDC4"},"
                "pastel": {"primary": "#FFB3BA", "secondary": "#BAFFC9"},"
                "neon": {"primary": "#FF073A", "secondary": "#39FF14"},"
                "earth": {"primary": "#8B4513", "secondary": "#228B22"},"
                "ocean": {"primary": "#006994", "secondary": "#87CEEB"},"
                "forest": {"primary": "#228B22", "secondary": "#90EE90"},"
                "sunset": {"primary": "#FF4500", "secondary": "#FFD700"},"
                "grayscale": {"primary": "#808080", "secondary": "#D3D3D3"},"
                "accent": {"primary": "#000000", "secondary": "#FF6B6B"},"
                "gradient": {"primary": "#667eea", "secondary": "#764ba2"},"
                "complementary": {"primary": "#FF6B6B", "secondary": "#6BCF7F"},"
# BRACKET_SURGEON: disabled
#             },
# BRACKET_SURGEON: disabled
#         }
# BRACKET_SURGEON: disabled
#     )


@router.get("/health")
async def health_check():
    """"""
    Health check endpoint for the avatar API
    """"""
    return JSONResponse(
        {
            "status": "healthy",
            "service": "avatar-api",
            "components": {
                "avatar_generator": "active",
                "background_remover": "active",
                "channel_manager": "active",
# BRACKET_SURGEON: disabled
#             },
# BRACKET_SURGEON: disabled
#         }
# BRACKET_SURGEON: disabled
#     )