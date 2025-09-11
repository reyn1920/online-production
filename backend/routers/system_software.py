import asyncio
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/software", tags=["System Software Integration"])


# Pydantic Models
class SoftwareInfo(BaseModel):
    name: str
    path: str
    version: Optional[str] = None
    status: str
    capabilities: List[str] = []
    integration_type: str


class CommandRequest(BaseModel):
    software: str
    command: str
    args: List[str] = []
    working_directory: Optional[str] = None


class FileOperation(BaseModel):
    software: str
    operation: str  # open, create, export, import
    file_path: str
    options: Dict[str, Any] = {}


class AutomationTask(BaseModel):
    name: str
    software_chain: List[str]
    steps: List[Dict[str, Any]]
    input_files: List[str] = []
    output_directory: str


# Software Registry
SOFTWARE_REGISTRY = {
    # Creative Applications
    "blender": {
        "name": "Blender",
        "path": "/Applications/Blender.app",
        "cli_path": "/Applications/Blender.app/Contents/MacOS/Blender",
        "capabilities": [
            "3d_modeling",
            "animation",
            "rendering",
            "video_editing",
            "scripting",
        ],
        "integration_type": "creative",
        "file_formats": [".blend", ".fbx", ".obj", ".dae", ".ply"],
    },
    "davinci_resolve": {
        "name": "DaVinci Resolve",
        "path": "/Applications/DaVinci Resolve/DaVinci Resolve.app",
        "capabilities": [
            "video_editing",
            "color_grading",
            "audio_editing",
            "vfx",
            "rendering",
        ],
        "integration_type": "creative",
        "file_formats": [".drp", ".mp4", ".mov", ".avi", ".mkv"],
    },
    "gimp": {
        "name": "GIMP",
        "path": "/Applications/GIMP.app",
        "cli_path": "/Applications/GIMP.app/Contents/MacOS/GIMP",
        "capabilities": [
            "image_editing",
            "photo_manipulation",
            "graphics_design",
            "scripting",
        ],
        "integration_type": "creative",
        "file_formats": [".xcf", ".png", ".jpg", ".gif", ".tiff"],
    },
    "inkscape": {
        "name": "Inkscape",
        "path": "/Applications/Inkscape.app",
        "cli_path": "/Applications/Inkscape.app/Contents/MacOS/inkscape",
        "capabilities": [
            "vector_graphics",
            "svg_editing",
            "illustration",
            "logo_design",
        ],
        "integration_type": "creative",
        "file_formats": [".svg", ".eps", ".pdf", ".ai"],
    },
    "filmora": {
        "name": "Wondershare Filmora",
        "path": "/Applications/Wondershare Filmora Mac.app",
        "capabilities": ["video_editing", "effects", "transitions", "audio_editing"],
        "integration_type": "creative",
        "file_formats": [".wfp", ".mp4", ".mov", ".avi"],
    },
    # Development Tools
    "xcode": {
        "name": "Xcode",
        "path": "/Applications/Xcode.app",
        "cli_path": "/usr/bin/xcodebuild",
        "capabilities": [
            "ios_development",
            "macos_development",
            "swift",
            "objective_c",
            "debugging",
        ],
        "integration_type": "development",
        "file_formats": [".xcodeproj", ".xcworkspace", ".swift", ".m", ".h"],
    },
    "cursor": {
        "name": "Cursor",
        "path": "/Applications/Cursor.app",
        "capabilities": [
            "code_editing",
            "ai_assistance",
            "debugging",
            "git_integration",
        ],
        "integration_type": "development",
        "file_formats": [".*"],
    },
    "sublime_text": {
        "name": "Sublime Text",
        "path": "/Applications/Sublime Text.app",
        "cli_path": "/Applications/Sublime Text.app/Contents/SharedSupport/bin/subl",
        "capabilities": ["text_editing", "code_editing", "multiple_cursors", "plugins"],
        "integration_type": "development",
        "file_formats": [".*"],
    },
    "github_desktop": {
        "name": "GitHub Desktop",
        "path": "/Applications/GitHub Desktop.app",
        "capabilities": [
            "git_gui",
            "repository_management",
            "branch_management",
            "pull_requests",
        ],
        "integration_type": "development",
        "file_formats": [],
    },
    # AI and Machine Learning
    "ollama": {
        "name": "Ollama",
        "path": "/Applications/Ollama.app",
        "cli_path": "/usr/local/bin/ollama",
        "capabilities": [
            "local_llm",
            "model_management",
            "api_server",
            "chat_interface",
        ],
        "integration_type": "ai",
        "file_formats": [],
    },
    "jan": {
        "name": "Jan",
        "path": "/Applications/Jan.app",
        "capabilities": [
            "local_ai",
            "model_management",
            "chat_interface",
            "privacy_focused",
        ],
        "integration_type": "ai",
        "file_formats": [],
    },
    # System and Utilities
    "docker": {
        "name": "Docker",
        "path": "/Applications/Docker.app",
        "cli_path": "/usr/local/bin/docker",
        "capabilities": [
            "containerization",
            "deployment",
            "microservices",
            "orchestration",
        ],
        "integration_type": "system",
        "file_formats": ["Dockerfile", "docker-compose.yml"],
    },
    "google_drive": {
        "name": "Google Drive",
        "path": "/Applications/Google Drive.app",
        "capabilities": ["cloud_storage", "file_sync", "collaboration", "backup"],
        "integration_type": "productivity",
        "file_formats": [".*"],
    },
    # Command Line Tools
    "git": {
        "name": "Git",
        "cli_path": "/Users/thomasbrianreynolds/homebrew/bin/git",
        "capabilities": ["version_control", "branching", "merging", "collaboration"],
        "integration_type": "development",
        "file_formats": [],
    },
    "ffmpeg": {
        "name": "FFmpeg",
        "cli_path": "/opt/homebrew/bin/ffmpeg",
        "capabilities": [
            "video_conversion",
            "audio_conversion",
            "streaming",
            "codec_support",
        ],
        "integration_type": "media",
        "file_formats": [".mp4", ".avi", ".mkv", ".mp3", ".wav", ".flac"],
    },
    "imagemagick": {
        "name": "ImageMagick",
        "cli_path": "/Users/thomasbrianreynolds/homebrew/bin/convert",
        "capabilities": [
            "image_conversion",
            "image_manipulation",
            "batch_processing",
            "format_support",
        ],
        "integration_type": "media",
        "file_formats": [".png", ".jpg", ".gif", ".tiff", ".bmp", ".svg"],
    },
    "node": {
        "name": "Node.js",
        "cli_path": "/Users/thomasbrianreynolds/.nvm/versions/node/v22.17.1/bin/node",
        "capabilities": [
            "javascript_runtime",
            "npm_packages",
            "web_development",
            "api_development",
        ],
        "integration_type": "development",
        "file_formats": [".js", ".json", ".ts"],
    },
    "python": {
        "name": "Python",
        "cli_path": "/Users/thomasbrianreynolds/online production/venv/bin/python3",
        "capabilities": [
            "scripting",
            "data_science",
            "machine_learning",
            "web_development",
        ],
        "integration_type": "development",
        "file_formats": [".py", ".ipynb", ".pyx"],
    },
}


# Helper Functions
async def check_software_availability(software_key: str) -> bool:
    """Check if software is available and accessible"""
    software = SOFTWARE_REGISTRY.get(software_key)
    if not software:
        return False

    # Check GUI application
    if "path" in software:
        return os.path.exists(software["path"])

    # Check CLI tool
    if "cli_path" in software:
        return (
            os.path.exists(software["cli_path"])
            or shutil.which(software["cli_path"].split("/")[-1]) is not None
        )

    return False


async def execute_command(
    command: str, args: list = None, cwd: str = None
) -> Dict[str, Any]:
    """Execute a system command safely"""
    try:
        if args is None:
            args = []

        full_command = [command] + args

        process = await asyncio.create_subprocess_exec(
            *full_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
        )

        stdout, stderr = await process.communicate()

        return {
            "success": process.returncode == 0,
            "returncode": process.returncode,
            "stdout": stdout.decode("utf-8", errors="ignore"),
            "stderr": stderr.decode("utf-8", errors="ignore"),
        }
    except Exception as e:
        return {"success": False, "error": str(e), "stdout": "", "stderr": ""}


# API Endpoints
@router.get("/status", response_model=Dict[str, Any])
async def get_system_software_status():
    """Get status of all integrated software"""
    status = {}

    for key, software in SOFTWARE_REGISTRY.items():
        is_available = await check_software_availability(key)
        status[key] = {
            "name": software["name"],
            "available": is_available,
            "integration_type": software["integration_type"],
            "capabilities": software["capabilities"],
        }

    return {
        "total_software": len(SOFTWARE_REGISTRY),
        "available_count": sum(1 for s in status.values() if s["available"]),
        "software": status,
    }


@router.get("/software/{software_key}", response_model=SoftwareInfo)
async def get_software_info(software_key: str):
    """Get detailed information about specific software"""
    if software_key not in SOFTWARE_REGISTRY:
        raise HTTPException(status_code=404, detail="Software not found")

    software = SOFTWARE_REGISTRY[software_key]
    is_available = await check_software_availability(software_key)

    return SoftwareInfo(
        name=software["name"],
        path=software.get("path", software.get("cli_path", "")),
        status="available" if is_available else "unavailable",
        capabilities=software["capabilities"],
        integration_type=software["integration_type"],
    )


@router.post("/execute")
async def execute_software_command(request: CommandRequest):
    """Execute a command with specific software"""
    if request.software not in SOFTWARE_REGISTRY:
        raise HTTPException(status_code=404, detail="Software not found")

    software = SOFTWARE_REGISTRY[request.software]

    # Determine the executable path
    executable = software.get("cli_path", software.get("path"))
    if not executable:
        raise HTTPException(status_code=400, detail="Software not executable via CLI")

    # For GUI applications, use 'open' command on macOS
    if executable.endswith(".app"):
        command_args = ["open", "-a", executable]
        if request.args:
            command_args.extend(["--args"] + request.args)
        result = await execute_command(
            "open", command_args[1:], request.working_directory
        )
    else:
        # Direct CLI execution
        result = await execute_command(
            executable, [request.command] + request.args, request.working_directory
        )

    return result


@router.post("/blender/render")
async def blender_render(
    background_tasks: BackgroundTasks,
    blend_file: str,
    output_path: str,
    frame_range: Optional[str] = None,
):
    """Render a Blender project"""
    if not await check_software_availability("blender"):
        raise HTTPException(status_code=404, detail="Blender not available")

    args = ["-b", blend_file, "-o", output_path]
    if frame_range:
        args.extend(["-f", frame_range])
    else:
        args.append("-a")  # Render all frames

    result = await execute_command(SOFTWARE_REGISTRY["blender"]["cli_path"], args)
    return result


@router.post("/ffmpeg/convert")
async def ffmpeg_convert(input_file: str, output_file: str, options: List[str] = None):
    """Convert media files using FFmpeg"""
    if not await check_software_availability("ffmpeg"):
        raise HTTPException(status_code=404, detail="FFmpeg not available")

    args = ["-i", input_file]
    if options:
        args.extend(options)
    args.append(output_file)

    result = await execute_command(SOFTWARE_REGISTRY["ffmpeg"]["cli_path"], args)
    return result


@router.post("/imagemagick/convert")
async def imagemagick_convert(
    input_file: str, output_file: str, options: List[str] = None
):
    """Convert images using ImageMagick"""
    if not await check_software_availability("imagemagick"):
        raise HTTPException(status_code=404, detail="ImageMagick not available")

    args = [input_file]
    if options:
        args.extend(options)
    args.append(output_file)

    result = await execute_command(SOFTWARE_REGISTRY["imagemagick"]["cli_path"], args)
    return result


@router.post("/git/operation")
async def git_operation(
    operation: str, args: List[str] = None, repository_path: str = None
):
    """Perform Git operations"""
    if not await check_software_availability("git"):
        raise HTTPException(status_code=404, detail="Git not available")

    command_args = [operation]
    if args:
        command_args.extend(args)

    result = await execute_command(
        SOFTWARE_REGISTRY["git"]["cli_path"], command_args, repository_path
    )
    return result


@router.post("/docker/operation")
async def docker_operation(operation: str, args: List[str] = None):
    """Perform Docker operations"""
    if not await check_software_availability("docker"):
        raise HTTPException(status_code=404, detail="Docker not available")

    command_args = [operation]
    if args:
        command_args.extend(args)

    result = await execute_command(
        SOFTWARE_REGISTRY["docker"]["cli_path"], command_args
    )
    return result


@router.post("/ollama/chat")
async def ollama_chat(model: str, prompt: str, system_prompt: Optional[str] = None):
    """Chat with Ollama models"""
    if not await check_software_availability("ollama"):
        raise HTTPException(status_code=404, detail="Ollama not available")

    # Prepare the chat payload
    chat_data = {"model": model, "messages": [{"role": "user", "content": prompt}]}

    if system_prompt:
        chat_data["messages"].insert(0, {"role": "system", "content": system_prompt})

    # Use ollama run command
    result = await execute_command(
        SOFTWARE_REGISTRY["ollama"]["cli_path"], ["run", model, prompt]
    )
    return result


@router.post("/automation/workflow")
async def create_automation_workflow(
    task: AutomationTask, background_tasks: BackgroundTasks
):
    """Create and execute an automation workflow across multiple software"""
    workflow_results = []

    for step in task.steps:
        software_key = step.get("software")
        if software_key not in SOFTWARE_REGISTRY:
            workflow_results.append(
                {
                    "step": step,
                    "success": False,
                    "error": f"Software {software_key} not found",
                }
            )
            continue

        if not await check_software_availability(software_key):
            workflow_results.append(
                {
                    "step": step,
                    "success": False,
                    "error": f"Software {software_key} not available",
                }
            )
            continue

        # Execute the step based on software type
        try:
            software = SOFTWARE_REGISTRY[software_key]
            command = step.get("command", "")
            args = step.get("args", [])

            if software.get("cli_path"):
                result = await execute_command(
                    software["cli_path"],
                    [command] + args,
                    step.get("working_directory"),
                )
            else:
                # For GUI apps, use open command
                result = await execute_command(
                    "open", ["-a", software["path"]], step.get("working_directory")
                )

            workflow_results.append(
                {"step": step, "success": result["success"], "result": result}
            )
        except Exception as e:
            workflow_results.append({"step": step, "success": False, "error": str(e)})

    return {
        "workflow_name": task.name,
        "total_steps": len(task.steps),
        "successful_steps": sum(1 for r in workflow_results if r["success"]),
        "results": workflow_results,
    }


@router.get("/integrations/creative")
async def get_creative_software():
    """Get all creative software integrations"""
    creative_software = {
        k: v
        for k, v in SOFTWARE_REGISTRY.items()
        if v["integration_type"] == "creative"
    }

    status = {}
    for key, software in creative_software.items():
        is_available = await check_software_availability(key)
        status[key] = {
            "name": software["name"],
            "available": is_available,
            "capabilities": software["capabilities"],
            "file_formats": software.get("file_formats", []),
        }

    return status


@router.get("/integrations/development")
async def get_development_software():
    """Get all development software integrations"""
    dev_software = {
        k: v
        for k, v in SOFTWARE_REGISTRY.items()
        if v["integration_type"] == "development"
    }

    status = {}
    for key, software in dev_software.items():
        is_available = await check_software_availability(key)
        status[key] = {
            "name": software["name"],
            "available": is_available,
            "capabilities": software["capabilities"],
            "file_formats": software.get("file_formats", []),
        }

    return status


@router.get("/integrations/ai")
async def get_ai_software():
    """Get all AI software integrations"""
    ai_software = {
        k: v for k, v in SOFTWARE_REGISTRY.items() if v["integration_type"] == "ai"
    }

    status = {}
    for key, software in ai_software.items():
        is_available = await check_software_availability(key)
        status[key] = {
            "name": software["name"],
            "available": is_available,
            "capabilities": software["capabilities"],
        }

    return status


@router.post("/batch/creative-pipeline")
async def creative_pipeline(
    input_files: List[str], output_directory: str, pipeline_type: str
):
    """Execute a creative pipeline across multiple software"""
    if pipeline_type == "video_production":
        # Blender -> DaVinci Resolve -> FFmpeg pipeline
        results = []

        for input_file in input_files:
            # Step 1: Blender processing (if .blend file)
            if input_file.endswith(".blend"):
                blender_result = await blender_render(
                    None, input_file, f"{output_directory}/blender_output.mov"
                )
                results.append({"step": "blender_render", "result": blender_result})

            # Step 2: FFmpeg conversion
            ffmpeg_result = await ffmpeg_convert(
                input_file,
                f"{output_directory}/final_output.mp4",
                ["-c:v", "libx264", "-crf", "23"],
            )
            results.append({"step": "ffmpeg_convert", "result": ffmpeg_result})

        return {"pipeline": "video_production", "results": results}

    elif pipeline_type == "image_processing":
        # GIMP -> ImageMagick pipeline
        results = []

        for input_file in input_files:
            # ImageMagick batch processing
            convert_result = await imagemagick_convert(
                input_file,
                f"{output_directory}/processed_{os.path.basename(input_file)}",
                ["-resize", "1920x1080", "-quality", "90"],
            )
            results.append({"step": "imagemagick_convert", "result": convert_result})

        return {"pipeline": "image_processing", "results": results}

    else:
        raise HTTPException(status_code=400, detail="Unknown pipeline type")
