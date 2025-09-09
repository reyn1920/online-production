from __future__ import annotations
from typing import Dict, Any, List, Optional
from pathlib import Path
import subprocess
import json
import os
from backend.core.settings import get_setting, set_setting

def get_blender_path() -> str:
    """Get the configured Blender executable path."""
    return get_setting("blender_path", "/Applications/Blender.app/Contents/MacOS/Blender")

def set_blender_path(path: str) -> Dict[str, Any]:
    """Set the Blender executable path."""
    set_setting("blender_path", path)
    return {"ok": True, "path": path}

def validate_blender_installation() -> Dict[str, Any]:
    """Validate that Blender is installed and accessible."""
    blender_path = get_blender_path()
    
    if not Path(blender_path).exists():
        return {
            "ok": False,
            "error": f"Blender not found at {blender_path}",
            "suggestion": "Please set the correct Blender path using set_blender_path()"
        }
    
    try:
        # Test Blender version
        result = subprocess.run(
            [blender_path, "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            version_info = result.stdout.strip().split('\n')[0]
            return {
                "ok": True,
                "version": version_info,
                "path": blender_path
            }
        else:
            return {
                "ok": False,
                "error": f"Blender execution failed: {result.stderr}"
            }
    
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "error": "Blender version check timed out"
        }
    except Exception as e:
        return {
            "ok": False,
            "error": f"Error checking Blender: {str(e)}"
        }

def create_blender_project(project_name: str, assets: List[str]) -> Dict[str, Any]:
    """Create a new Blender project with specified assets."""
    validation = validate_blender_installation()
    if not validation["ok"]:
        return validation
    
    # Create project directory
    project_dir = Path("output") / "blender_projects" / project_name
    project_dir.mkdir(parents=True, exist_ok=True)
    
    # Create Blender project file path
    blend_file = project_dir / f"{project_name}.blend"
    
    # Create a basic Blender script to set up the project
    script_content = f"""
import bpy
import os

# Clear existing mesh objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Add a basic cube
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))

# Save the project
bpy.ops.wm.save_as_mainfile(filepath=r"{blend_file}")

print(f"Blender project created: {blend_file}")
"""
    
    script_file = project_dir / "setup_project.py"
    script_file.write_text(script_content)
    
    try:
        # Run Blender with the setup script
        blender_path = get_blender_path()
        result = subprocess.run([
            blender_path,
            "--background",
            "--python", str(script_file)
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            return {
                "ok": True,
                "project_path": str(blend_file),
                "project_dir": str(project_dir),
                "assets": assets,
                "message": f"Blender project '{project_name}' created successfully"
            }
        else:
            return {
                "ok": False,
                "error": f"Blender project creation failed: {result.stderr}",
                "stdout": result.stdout
            }
    
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "error": "Blender project creation timed out"
        }
    except Exception as e:
        return {
            "ok": False,
            "error": f"Error creating Blender project: {str(e)}"
        }

def export_blender_assets(project_path: str, export_format: str = "fbx") -> Dict[str, Any]:
    """Export assets from a Blender project."""
    validation = validate_blender_installation()
    if not validation["ok"]:
        return validation
    
    project_file = Path(project_path)
    if not project_file.exists():
        return {
            "ok": False,
            "error": f"Blender project file not found: {project_path}"
        }
    
    # Create export directory
    export_dir = project_file.parent / "exports"
    export_dir.mkdir(exist_ok=True)
    
    # Create export script
    export_script = f"""
import bpy
import os

# Load the project
bpy.ops.wm.open_mainfile(filepath=r"{project_file}")

# Export all objects
export_path = r"{export_dir / f'export.{export_format}'}"

if "{export_format.lower()}" == "fbx":
    bpy.ops.export_scene.fbx(filepath=export_path)
elif "{export_format.lower()}" == "obj":
    bpy.ops.export_scene.obj(filepath=export_path)
else:
    print(f"Unsupported export format: {export_format}")
    exit(1)

print(f"Assets exported to: {export_path}")
"""
    
    script_file = project_file.parent / "export_script.py"
    script_file.write_text(export_script)
    
    try:
        blender_path = get_blender_path()
        result = subprocess.run([
            blender_path,
            "--background",
            "--python", str(script_file)
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            return {
                "ok": True,
                "export_dir": str(export_dir),
                "format": export_format,
                "message": f"Assets exported successfully in {export_format} format"
            }
        else:
            return {
                "ok": False,
                "error": f"Export failed: {result.stderr}",
                "stdout": result.stdout
            }
    
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "error": "Export operation timed out"
        }
    except Exception as e:
        return {
            "ok": False,
            "error": f"Error during export: {str(e)}"
        }

def list_blender_projects() -> Dict[str, Any]:
    """List all available Blender projects."""
    projects_dir = Path("output") / "blender_projects"
    
    if not projects_dir.exists():
        return {"ok": True, "projects": []}
    
    projects = []
    for project_dir in projects_dir.iterdir():
        if project_dir.is_dir():
            blend_files = list(project_dir.glob("*.blend"))
            if blend_files:
                projects.append({
                    "name": project_dir.name,
                    "path": str(project_dir),
                    "blend_file": str(blend_files[0]),
                    "created": project_dir.stat().st_ctime
                })
    
    return {"ok": True, "projects": projects}