from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Dict, List

from backend.core.settings import get_setting, set_setting


def get_resolve_path() -> str:
    """Get the configured DaVinci Resolve executable path."""
    return get_setting(
        "resolve_path",
        "/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/MacOS/Resolve",
    )


def set_resolve_path(path: str) -> Dict[str, Any]:
    """Set the DaVinci Resolve executable path."""
    set_setting("resolve_path", path)
    return {"ok": True, "path": path}


def validate_resolve_installation() -> Dict[str, Any]:
    """Validate that DaVinci Resolve is installed and accessible."""
    resolve_path = get_resolve_path()

    if not Path(resolve_path).exists():
        return {
            "ok": False,
            "error": f"DaVinci Resolve not found at {resolve_path}",
            "suggestion": "Please set the correct Resolve path using set_resolve_path()",
        }

    # Check if Resolve is accessible (basic check)
    try:
        # For DaVinci Resolve, we'll check if the application bundle exists
        app_bundle = Path(resolve_path).parent.parent.parent
        if app_bundle.name.endswith(".app"):
            return {"ok": True, "path": resolve_path, "app_bundle": str(app_bundle)}
        else:
            return {"ok": False, "error": "Invalid Resolve application structure"}

    except Exception as e:
        return {"ok": False, "error": f"Error checking Resolve: {str(e)}"}


def create_resolve_project(project_name: str, media_files: List[str]) -> Dict[str, Any]:
    """Create a new DaVinci Resolve project structure."""
    validation = validate_resolve_installation()
    if not validation["ok"]:
        return validation

    # Create project directory structure
    project_dir = Path("output") / "resolve_projects" / project_name
    project_dir.mkdir(parents=True, exist_ok=True)

    # Create standard Resolve project folders
    folders = ["Media", "Timeline Exports", "Audio", "Graphics", "Project Files"]

    for folder in folders:
        (project_dir / folder).mkdir(exist_ok=True)

    # Copy media files to Media folder
    media_dir = project_dir / "Media"
    copied_files = []

    for media_file in media_files:
        source_path = Path(media_file)
        if source_path.exists():
            dest_path = media_dir / source_path.name
            try:
                shutil.copy2(source_path, dest_path)
                copied_files.append(str(dest_path))
            except Exception as e:
                return {
                    "ok": False,
                    "error": f"Failed to copy media file {media_file}: {str(e)}",
                }

    # Create project metadata
    project_metadata = {
        "name": project_name,
        "created": str(project_dir.stat().st_ctime),
        "media_files": copied_files,
        "project_dir": str(project_dir),
    }

    metadata_file = project_dir / "project_metadata.json"
    metadata_file.write_text(json.dumps(project_metadata, indent=2))

    # Create a basic DRP (DaVinci Resolve Project) structure
    # Note: Actual DRP files are binary and complex, so we create a placeholder
    drp_info = {
        "project_name": project_name,
        "timeline_count": 1,
        "media_pool_items": len(copied_files),
        "created_by": "TRAE.AI Handoff Pipeline",
    }

    drp_info_file = project_dir / "Project Files" / f"{project_name}_info.json"
    drp_info_file.write_text(json.dumps(drp_info, indent=2))

    return {
        "ok": True,
        "project_path": str(project_dir),
        "project_name": project_name,
        "media_files": copied_files,
        "metadata_file": str(metadata_file),
        "message": f"Resolve project '{project_name}' created successfully",
    }


def create_resolve_timeline(
    project_path: str, timeline_name: str, clips: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Create a timeline structure for DaVinci Resolve."""
    project_dir = Path(project_path)
    if not project_dir.exists():
        return {"ok": False, "error": f"Project directory not found: {project_path}"}

    # Create timeline metadata
    timeline_data = {
        "name": timeline_name,
        "clips": clips,
        "frame_rate": 24,
        "resolution": "1920x1080",
        "created": str(Path().stat().st_ctime),
    }

    timeline_file = project_dir / "Project Files" / f"{timeline_name}_timeline.json"
    timeline_file.write_text(json.dumps(timeline_data, indent=2))

    return {
        "ok": True,
        "timeline_file": str(timeline_file),
        "timeline_name": timeline_name,
        "clips_count": len(clips),
    }


def export_resolve_timeline(
    project_path: str, timeline_name: str, export_settings: Dict[str, Any]
) -> Dict[str, Any]:
    """Export a timeline from DaVinci Resolve project."""
    project_dir = Path(project_path)
    if not project_dir.exists():
        return {"ok": False, "error": f"Project directory not found: {project_path}"}

    # Check if timeline exists
    timeline_file = project_dir / "Project Files" / f"{timeline_name}_timeline.json"
    if not timeline_file.exists():
        return {"ok": False, "error": f"Timeline not found: {timeline_name}"}

    # Create export directory
    export_dir = project_dir / "Timeline Exports"
    export_dir.mkdir(exist_ok=True)

    # Default export settings
    default_settings = {
        "format": "mp4",
        "codec": "h264",
        "quality": "high",
        "resolution": "1920x1080",
        "frame_rate": 24,
    }

    # Merge with provided settings
    final_settings = {**default_settings, **export_settings}

    # Create export metadata
    export_metadata = {
        "timeline_name": timeline_name,
        "export_settings": final_settings,
        "export_path": str(export_dir / f"{timeline_name}.{final_settings['format']}"),
        "status": "ready_for_export",
        "created": str(Path().stat().st_ctime),
    }

    export_file = export_dir / f"{timeline_name}_export.json"
    export_file.write_text(json.dumps(export_metadata, indent=2))

    return {
        "ok": True,
        "export_metadata": export_metadata,
        "export_file": str(export_file),
        "message": f"Export configuration created for timeline '{timeline_name}'",
    }


def list_resolve_projects() -> Dict[str, Any]:
    """List all available DaVinci Resolve projects."""
    projects_dir = Path("output") / "resolve_projects"

    if not projects_dir.exists():
        return {"ok": True, "projects": []}

    projects = []
    for project_dir in projects_dir.iterdir():
        if project_dir.is_dir():
            metadata_file = project_dir / "project_metadata.json"
            if metadata_file.exists():
                try:
                    metadata = json.loads(metadata_file.read_text())
                    projects.append(
                        {
                            "name": project_dir.name,
                            "path": str(project_dir),
                            "metadata": metadata,
                            "created": project_dir.stat().st_ctime,
                        }
                    )
                except Exception:
                    # Skip projects with invalid metadata
                    continue

    return {"ok": True, "projects": projects}


def get_resolve_project_info(project_path: str) -> Dict[str, Any]:
    """Get detailed information about a Resolve project."""
    project_dir = Path(project_path)
    if not project_dir.exists():
        return {"ok": False, "error": f"Project directory not found: {project_path}"}

    # Read project metadata
    metadata_file = project_dir / "project_metadata.json"
    if not metadata_file.exists():
        return {"ok": False, "error": "Project metadata not found"}

    try:
        metadata = json.loads(metadata_file.read_text())

        # Get timeline information
        project_files_dir = project_dir / "Project Files"
        timelines = []
        if project_files_dir.exists():
            for timeline_file in project_files_dir.glob("*_timeline.json"):
                timeline_data = json.loads(timeline_file.read_text())
                timelines.append(timeline_data)

        # Get export information
        export_dir = project_dir / "Timeline Exports"
        exports = []
        if export_dir.exists():
            for export_file in export_dir.glob("*_export.json"):
                export_data = json.loads(export_file.read_text())
                exports.append(export_data)

        return {
            "ok": True,
            "metadata": metadata,
            "timelines": timelines,
            "exports": exports,
            "project_path": project_path,
        }

    except Exception as e:
        return {"ok": False, "error": f"Error reading project info: {str(e)}"}
