from __future__ import annotations

import asyncio
import json
import logging
import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from backend.core.settings import get_setting, set_setting
from backend.pipelines.blender_handoff import (
    get_blender_path,
    validate_blender_installation,
)

logger = logging.getLogger(__name__)


class BlenderRenderEngine(Enum):
    """Blender render engines."""

    CYCLES = "CYCLES"
    EEVEE = "BLENDER_EEVEE"
    WORKBENCH = "BLENDER_WORKBENCH"


class BlenderOutputFormat(Enum):
    """Blender output formats."""

    MP4 = "FFMPEG"
    PNG = "PNG"
    EXR = "OPEN_EXR"
    FBX = "FBX"
    OBJ = "OBJ"
    GLTF = "GLTF"


@dataclass
class BlenderRenderConfig:
    """Configuration for Blender rendering."""

    engine: BlenderRenderEngine = BlenderRenderEngine.EEVEE
    resolution_x: int = 1920
    resolution_y: int = 1080
    frame_start: int = 1
    frame_end: int = 250
    samples: int = 128
    output_format: BlenderOutputFormat = BlenderOutputFormat.MP4
    output_path: Optional[str] = None
    use_gpu: bool = True
    denoising: bool = True


@dataclass
class AvatarConfig:
    """Configuration for 3D avatar generation."""

    gender: str = "female"
    age: float = 25.0
    ethnicity: str = "caucasian"
    body_type: str = "average"
    clothing_style: str = "casual"
    hair_style: str = "medium"
    facial_expression: str = "neutral"
    animation_type: str = "idle"
    voice_sync: bool = True


class EnhancedBlenderPipeline:
    """Enhanced Blender pipeline with cloud software integration."""

    def __init__(self):
        self.blender_path = get_blender_path()
        self.project_root = Path("output / blender_projects")
        self.project_root.mkdir(parents=True, exist_ok=True)

        self.scripts_dir = Path("backend / pipelines / blender_scripts")
        self.scripts_dir.mkdir(parents=True, exist_ok=True)

        self.executor = ThreadPoolExecutor(max_workers=4)
        self.active_renders = {}

        logger.info("Enhanced Blender Pipeline initialized")

    async def validate_installation(self) -> Dict[str, Any]:
        """Validate Blender installation and capabilities."""
        validation = validate_blender_installation()
        if not validation["ok"]:
            return validation

        # Check for required addons
        addons_check = await self._check_required_addons()
        validation["addons"] = addons_check

        return validation

    async def create_3d_avatar(
        self, avatar_config: AvatarConfig, project_name: str
    ) -> Dict[str, Any]:
        """Create a 3D avatar using Blender and MPFB addon."""
        try:
            # Validate installation
            validation = await self.validate_installation()
            if not validation["ok"]:
                return validation

            # Create project directory
            project_dir = self.project_root / project_name
            project_dir.mkdir(parents=True, exist_ok=True)

            # Generate avatar creation script
            script_content = self._generate_avatar_script(avatar_config, project_dir)
            script_path = self.scripts_dir / f"create_avatar_{project_name}.py"
            script_path.write_text(script_content)

            # Execute Blender script
            result = await self._execute_blender_script(script_path, project_dir)

            if result["success"]:
                avatar_file = project_dir / f"{project_name}_avatar.blend"
                return {
                    "ok": True,
                    "project_name": project_name,
                    "avatar_file": str(avatar_file),
                    "project_dir": str(project_dir),
                    "config": avatar_config.__dict__,
                }
            else:
                return {"ok": False, "error": result["error"]}

        except Exception as e:
            logger.error(f"Avatar creation failed: {e}")
            return {"ok": False, "error": str(e)}

    async def create_animated_scene(
        self,
        project_name: str,
        avatar_file: str,
        audio_file: Optional[str] = None,
        background_type: str = "studio",
    ) -> Dict[str, Any]:
        """Create an animated scene with avatar and background."""
        try:
            project_dir = self.project_root / project_name
            project_dir.mkdir(parents=True, exist_ok=True)

            # Generate scene creation script
            script_content = self._generate_scene_script(
                avatar_file, audio_file, background_type, project_dir
            )
            script_path = self.scripts_dir / f"create_scene_{project_name}.py"
            script_path.write_text(script_content)

            # Execute Blender script
            result = await self._execute_blender_script(script_path, project_dir)

            if result["success"]:
                scene_file = project_dir / f"{project_name}_scene.blend"
                return {
                    "ok": True,
                    "project_name": project_name,
                    "scene_file": str(scene_file),
                    "project_dir": str(project_dir),
                }
            else:
                return {"ok": False, "error": result["error"]}

        except Exception as e:
            logger.error(f"Scene creation failed: {e}")
            return {"ok": False, "error": str(e)}

    async def render_animation(
        self, project_name: str, render_config: BlenderRenderConfig
    ) -> Dict[str, Any]:
        """Render animation with specified configuration."""
        try:
            project_dir = self.project_root / project_name
            scene_file = project_dir / f"{project_name}_scene.blend"

            if not scene_file.exists():
                return {"ok": False, "error": f"Scene file not found: {scene_file}"}

            # Set output path if not specified
            if not render_config.output_path:
                render_config.output_path = str(project_dir / f"{project_name}_render")

            # Generate render script
            script_content = self._generate_render_script(render_config, scene_file)
            script_path = self.scripts_dir / f"render_{project_name}.py"
            script_path.write_text(script_content)

            # Start render process
            render_id = f"{project_name}_{int(time.time())}"
            self.active_renders[render_id] = {
                "project_name": project_name,
                "status": "starting",
                "progress": 0,
                "start_time": time.time(),
            }

            # Execute render in background
            future = self.executor.submit(
                self._execute_render_process, script_path, project_dir, render_id
            )

            return {
                "ok": True,
                "render_id": render_id,
                "project_name": project_name,
                "status": "started",
                "output_path": render_config.output_path,
            }

        except Exception as e:
            logger.error(f"Render start failed: {e}")
            return {"ok": False, "error": str(e)}

    async def get_render_status(self, render_id: str) -> Dict[str, Any]:
        """Get the status of a render job."""
        if render_id not in self.active_renders:
            return {"ok": False, "error": "Render ID not found"}

        render_info = self.active_renders[render_id]
        return {
            "ok": True,
            "render_id": render_id,
            "status": render_info["status"],
            "progress": render_info["progress"],
            "elapsed_time": time.time() - render_info["start_time"],
        }

    async def export_for_davinci_resolve(
        self, project_name: str, export_format: str = "mp4"
    ) -> Dict[str, Any]:
        """Export Blender project for DaVinci Resolve integration."""
        try:
            project_dir = self.project_root / project_name
            export_dir = project_dir / "davinci_export"
            export_dir.mkdir(exist_ok=True)

            # Generate export script
            script_content = self._generate_export_script(project_dir, export_dir, export_format)
            script_path = self.scripts_dir / f"export_{project_name}.py"
            script_path.write_text(script_content)

            # Execute export
            result = await self._execute_blender_script(script_path, project_dir)

            if result["success"]:
                return {
                    "ok": True,
                    "project_name": project_name,
                    "export_dir": str(export_dir),
                    "format": export_format,
                }
            else:
                return {"ok": False, "error": result["error"]}

        except Exception as e:
            logger.error(f"Export failed: {e}")
            return {"ok": False, "error": str(e)}

    async def integrate_with_cloud_software(
        self, project_name: str, cloud_assets: Dict[str, str]
    ) -> Dict[str, Any]:
        """Integrate cloud software assets into Blender project."""
        try:
            project_dir = self.project_root / project_name

            # Process different cloud software assets
            integration_results = {}

            # Speechelo / Voice Generator audio
            if "audio_file" in cloud_assets:
                audio_result = await self._integrate_audio(project_dir, cloud_assets["audio_file"])
                integration_results["audio"] = audio_result

            # Thumbnail Blaster images
            if "thumbnail_images" in cloud_assets:
                thumbnail_result = await self._integrate_thumbnails(
                    project_dir, cloud_assets["thumbnail_images"]
                )
                integration_results["thumbnails"] = thumbnail_result

            # Background music
            if "background_music" in cloud_assets:
                music_result = await self._integrate_background_music(
                    project_dir, cloud_assets["background_music"]
                )
                integration_results["background_music"] = music_result

            return {
                "ok": True,
                "project_name": project_name,
                "integrations": integration_results,
            }

        except Exception as e:
            logger.error(f"Cloud software integration failed: {e}")
            return {"ok": False, "error": str(e)}

    def _generate_avatar_script(self, config: AvatarConfig, project_dir: Path) -> str:
        """Generate Blender script for avatar creation."""
        return f"""

import bpy
import bmesh
import os
from mathutils import Vector

# Clear existing mesh objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global = False)

# Enable MPFB addon if available
try:
    bpy.ops.wm.addon_enable(module="mpfb")
    print("MPFB addon enabled")
except Exception:
    print("MPFB addon not available, using basic mesh")

# Create basic humanoid figure
bpy.ops.mesh.primitive_cube_add(size = 2, location=(0, 0, 1))
body = bpy.context.active_object
body.name = "Avatar_Body"

# Add head
bpy.ops.mesh.primitive_uv_sphere_add(radius = 0.5, location=(0, 0, 2.5))
head = bpy.context.active_object
head.name = "Avatar_Head"

# Add basic materials
body_material = bpy.data.materials.new(name="Body_Material")
body_material.use_nodes = True
body_material.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.8,
    0.7,
    0.6,
    1.0)
body.data.materials.append(body_material)

head_material = bpy.data.materials.new(name="Head_Material")
head_material.use_nodes = True
head_material.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.9,
    0.8,
    0.7,
    1.0)
head.data.materials.append(head_material)

# Set up basic lighting
bpy.ops.object.light_add(type='SUN', location=(5, 5, 10))
sun = bpy.context.active_object
sun.data.energy = 3

# Add camera
bpy.ops.object.camera_add(location=(7, -7, 5))
camera = bpy.context.active_object
camera.rotation_euler = (1.1, 0, 0.785)

# Set render settings
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080

# Save the project
output_file = r"{project_dir / f"{config.gender}_avatar.blend"}"
bpy.ops.wm.save_as_mainfile(filepath = output_file)

print(f"Avatar created and saved: {{output_file}}")
"""

    def _generate_scene_script(
        self,
        avatar_file: str,
        audio_file: Optional[str],
        background_type: str,
        project_dir: Path,
    ) -> str:
        """Generate Blender script for scene creation."""
        audio_setup = ""
        if audio_file:
            audio_setup = f"""
# Add audio
try:
    bpy.ops.sequencer.sound_strip_add(filepath = r"{audio_file}")
    print("Audio added to scene")
except Exception:
    print("Failed to add audio")
"""

        return f"""

import bpy
import os
from mathutils import Vector

# Load avatar file
bpy.ops.wm.open_mainfile(filepath = r"{avatar_file}")

# Set up background based on type
if "{background_type}" == "studio":
    # Studio lighting setup
    world = bpy.context.scene.world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.1, 0.1, 0.1, 1.0)  # Dark background
    bg.inputs[1].default_value = 0.5  # Strength

    # Add key light
    bpy.ops.object.light_add(type='AREA', location=(3, -3, 4))
    key_light = bpy.context.active_object
    key_light.data.energy = 100
    key_light.data.size = 2

    # Add fill light
    bpy.ops.object.light_add(type='AREA', location=(-2, -3, 3))
    fill_light = bpy.context.active_object
    fill_light.data.energy = 50
    fill_light.data.size = 3

elif "{background_type}" == "outdoor":
    # Outdoor HDRI setup
    world = bpy.context.scene.world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[1].default_value = 1.0

# Set up animation timeline
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 250
scene.frame_set(1)

{audio_setup}

# Set render settings for animation
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.fps = 24

# Save scene
output_file = r"{project_dir / "animated_scene.blend"}"
bpy.ops.wm.save_as_mainfile(filepath = output_file)

print(f"Scene created and saved: {{output_file}}")
"""

    def _generate_render_script(self, config: BlenderRenderConfig, scene_file: Path) -> str:
        """Generate Blender script for rendering."""
        return f"""

import bpy
import os

# Load scene file
bpy.ops.wm.open_mainfile(filepath = r"{scene_file}")

# Set render settings
scene = bpy.context.scene
scene.render.engine = '{config.engine.value}'
scene.render.resolution_x = {config.resolution_x}
scene.render.resolution_y = {config.resolution_y}
scene.frame_start = {config.frame_start}
scene.frame_end = {config.frame_end}

# Set output settings
scene.render.filepath = r"{config.output_path}"

if '{config.output_format.value}' == 'FFMPEG':
    scene.render.image_settings.file_format = 'FFMPEG'
    scene.render.ffmpeg.format = 'MPEG4'
    scene.render.ffmpeg.codec = 'H264'
else:
    scene.render.image_settings.file_format = '{config.output_format.value}'

# GPU settings
if {str(config.use_gpu).lower()}:
    preferences = bpy.context.preferences
    cycles_preferences = preferences.addons["cycles"].preferences
    cycles_preferences.compute_device_type = "CUDA"

    # Enable all available GPU devices
    for device in cycles_preferences.devices:
        if device.type == "CUDA":
            device.use = True

# Cycles specific settings
if scene.render.engine == 'CYCLES':
    scene.cycles.samples = {config.samples}
    scene.cycles.use_denoising = {str(config.denoising).lower()}

# Start render
print("Starting render...")
bpy.ops.render.render(animation = True)
print("Render completed!")
"""

    def _generate_export_script(
        self, project_dir: Path, export_dir: Path, export_format: str
    ) -> str:
        """Generate Blender script for exporting to DaVinci Resolve."""
        return f"""

import bpy
import os

# Export settings based on format
if "{export_format}" == "mp4":
    # Export as MP4 for DaVinci Resolve
    scene = bpy.context.scene
    scene.render.filepath = r"{export_dir / "exported_video"}"
    scene.render.image_settings.file_format = 'FFMPEG'
    scene.render.ffmpeg.format = 'MPEG4'
    scene.render.ffmpeg.codec = 'H264'
    bpy.ops.render.render(animation = True)

elif "{export_format}" == "fbx":
    # Export objects as FBX
    bpy.ops.export_scene.fbx(
        filepath = r"{export_dir / "scene_objects.fbx"}",
            use_selection = False,
            use_active_collection = False
    )

elif "{export_format}" == "alembic":
    # Export as Alembic for DaVinci Resolve
    bpy.ops.wm.alembic_export(
        filepath = r"{export_dir / "scene_animation.abc"}",
            selected = False
    )

print(f"Export completed to: {export_dir}")
"""

    async def _execute_blender_script(self, script_path: Path, project_dir: Path) -> Dict[str, Any]:
        """Execute a Blender script."""
        try:
            cmd = [self.blender_path, "--background", "--python", str(script_path)]

            result = subprocess.run(
                cmd,
                cwd=str(project_dir),
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            if result.returncode == 0:
                return {"success": True, "output": result.stdout}
            else:
                return {"success": False, "error": result.stderr or "Unknown error"}

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Script execution timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_render_process(self, script_path: Path, project_dir: Path, render_id: str) -> None:
        """Execute render process in background."""
        try:
            self.active_renders[render_id]["status"] = "rendering"

            cmd = [self.blender_path, "--background", "--python", str(script_path)]

            process = subprocess.Popen(
                cmd,
                cwd=str(project_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Monitor progress (simplified)
            while process.poll() is None:
                time.sleep(1)
                # Update progress (this would need more sophisticated parsing)
                self.active_renders[render_id]["progress"] += 1

            if process.returncode == 0:
                self.active_renders[render_id]["status"] = "completed"
                self.active_renders[render_id]["progress"] = 100
            else:
                self.active_renders[render_id]["status"] = "failed"
                self.active_renders[render_id]["error"] = process.stderr.read()

        except Exception as e:
            self.active_renders[render_id]["status"] = "failed"
            self.active_renders[render_id]["error"] = str(e)

    async def _check_required_addons(self) -> Dict[str, bool]:
        """Check for required Blender addons."""
        # This would check for MPFB, Animation Nodes, etc.
        return {"mpfb": True, "animation_nodes": False, "rigify": True}  # Placeholder

    async def _integrate_audio(self, project_dir: Path, audio_file: str) -> Dict[str, Any]:
        """Integrate audio from Speechelo / Voice Generator."""
        # Copy audio file to project directory

        import shutil

        audio_dest = project_dir / "audio" / "voice.wav"
        audio_dest.parent.mkdir(exist_ok=True)
        shutil.copy2(audio_file, audio_dest)

        return {"success": True, "audio_path": str(audio_dest)}

    async def _integrate_thumbnails(
        self, project_dir: Path, thumbnail_images: List[str]
    ) -> Dict[str, Any]:
        """Integrate thumbnail images from Thumbnail Blaster."""

        import shutil

        thumbnails_dir = project_dir / "thumbnails"
        thumbnails_dir.mkdir(exist_ok=True)

        integrated_thumbnails = []
        for i, thumb in enumerate(thumbnail_images):
            thumb_dest = thumbnails_dir / f"thumbnail_{i}.png"
            shutil.copy2(thumb, thumb_dest)
            integrated_thumbnails.append(str(thumb_dest))

        return {"success": True, "thumbnails": integrated_thumbnails}

    async def _integrate_background_music(
        self, project_dir: Path, music_file: str
    ) -> Dict[str, Any]:
        """Integrate background music."""

        import shutil

        music_dest = project_dir / "audio" / "background.mp3"
        music_dest.parent.mkdir(exist_ok=True)
        shutil.copy2(music_file, music_dest)

        return {"success": True, "music_path": str(music_dest)}


# Global pipeline instance
blender_pipeline = EnhancedBlenderPipeline()
