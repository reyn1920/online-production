from fastapi import APIRouter
import shutil
import os
from datetime import datetime

router = APIRouter(prefix="/api", tags=["Software Status"])

def ok(name, available, reason=None, extra=None):
    """Standard response format for software status checks"""
    out = {
        "name": name,
        "available": bool(available),
        "timestamp": datetime.utcnow().isoformat()
    }
    if reason:
        out["reason"] = reason
    if extra:
        out["extra"] = extra
    return out

@router.get("/software/status")
def software_status():
    """Check availability of creative software tools"""
    return {
        "blender": ok(
            "blender",
            shutil.which("blender") is not None,
            reason=None if shutil.which("blender") else "binary_not_found"
        ),
        "resolve": ok(
            "resolve",
            bool(os.getenv("RESOLVE_SDK")),
            reason=None if os.getenv("RESOLVE_SDK") else "sdk_not_configured"
        ),
        "ffmpeg": ok(
            "ffmpeg",
            shutil.which("ffmpeg") is not None,
            reason=None if shutil.which("ffmpeg") else "binary_not_found"
        ),
        "davinci": ok(
            "davinci",
            False,
            reason="not_connected"
        )
    }

@router.get("/blender/validate")
def blender_validate():
    """Validate Blender installation"""
    blender_path = shutil.which("blender")
    return ok(
        "blender",
        bool(blender_path),
        None if blender_path else "binary_not_found",
        {"path": blender_path} if blender_path else None
    )

@router.get("/resolve/validate")
def resolve_validate():
    """Validate DaVinci Resolve SDK configuration"""
    sdk_path = os.getenv("RESOLVE_SDK")
    return ok(
        "resolve",
        bool(sdk_path),
        None if sdk_path else "sdk_not_configured",
        {"sdk_path": sdk_path} if sdk_path else None
    )

@router.get("/davinci/status")
def davinci_status():
    """DaVinci Resolve connection status - soft fail, never crash"""
    # Don't crash: reflect unavailability truthfully
    return ok("davinci", False, "not_connected")

@router.get("/creative/toolchain")
def creative_toolchain_status():
    """Overall creative toolchain status"""
    tools = {
        "blender": shutil.which("blender") is not None,
        "ffmpeg": shutil.which("ffmpeg") is not None,
        "resolve_sdk": bool(os.getenv("RESOLVE_SDK")),
        "davinci_connected": False  # Always false for now
    }

    available_count = sum(tools.values())
    total_count = len(tools)

    return {
        "toolchain_status": "partial" if available_count > 0 else "unavailable",
        "available_tools": available_count,
        "total_tools": total_count,
        "tools": {name: ok(name, available) for name, available in tools.items()},
        "timestamp": datetime.utcnow().isoformat()
    }