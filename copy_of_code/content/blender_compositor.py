#!/usr/bin/env python3
"""
Blender Compositor - Avatar Video Compositing with Checkpointed Rendering

This module implements Blender integration for compositing avatar videos,
backgrounds, and VFX with crash recovery through checkpointed rendering.
It supports batch processing, automated scene setup, and render optimization.

Author: TRAE.AI System
Version: 1.0.0
"""

import json
import logging
import os
import pickle
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Import TRAE.AI utilities
try:
    from utils.logger import get_logger
except ImportError:

    def get_logger(name):
        return logging.getLogger(name)


class RenderEngine(Enum):
    """Available render engines."""

    CYCLES = "CYCLES"
    EEVEE = "BLENDER_EEVEE"
    WORKBENCH = "BLENDER_WORKBENCH"


class RenderQuality(Enum):
    """Render quality presets."""

    PREVIEW = "preview"  # Fast preview quality
    DRAFT = "draft"  # Draft quality
    PRODUCTION = "production"  # Production quality
    FINAL = "final"  # Final quality


class CompositeMode(Enum):
    """Compositing modes."""

    AVATAR_ONLY = "avatar_only"
    AVATAR_BACKGROUND = "avatar_background"
    FULL_COMPOSITE = "full_composite"
    GREEN_SCREEN = "green_screen"


@dataclass
class RenderConfig:
    """Configuration for Blender rendering."""

    engine: RenderEngine = RenderEngine.EEVEE
    quality: RenderQuality = RenderQuality.PRODUCTION
    resolution_x: int = 1920
    resolution_y: int = 1080
    frame_start: int = 1
    frame_end: int = 250
    fps: int = 24
    samples: int = 128
    use_denoising: bool = True
    use_motion_blur: bool = False
    use_gpu: bool = True
    checkpoint_interval: int = 10  # Frames between checkpoints
    max_memory_gb: float = 8.0
    thread_count: Optional[int] = None
    output_format: str = "PNG"  # PNG, JPEG, EXR, etc.
    color_depth: str = "8"  # 8, 16, 32
    compression: int = 15  # 0-100 for JPEG, 0-100 for PNG


@dataclass
class CompositeLayer:
    """Represents a layer in the composite."""

    name: str
    type: str  # "video", "image", "background", "effect"
    source_path: str
    blend_mode: str = "ALPHA_OVER"
    opacity: float = 1.0
    position: Tuple[float, float] = (0.0, 0.0)
    scale: Tuple[float, float] = (1.0, 1.0)
    rotation: float = 0.0
    start_frame: int = 1
    end_frame: Optional[int] = None
    properties: Dict[str, Any] = None

    def __post_init__(self):
        if self.properties is None:
            self.properties = {}


@dataclass
class RenderJob:
    """Represents a Blender render job."""

    job_id: str
    project_file: str
    output_path: str
    layers: List[CompositeLayer]
    config: RenderConfig
    mode: CompositeMode = CompositeMode.FULL_COMPOSITE
    status: str = "pending"  # pending, processing, completed, failed, paused
    progress: float = 0.0
    current_frame: int = 1
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    checkpoint_data: Dict[str, Any] = None
    rendered_frames: List[int] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.checkpoint_data is None:
            self.checkpoint_data = {}
        if self.rendered_frames is None:
            self.rendered_frames = []
        if self.metadata is None:
            self.metadata = {}


class BlenderScriptGenerator:
    """Generates Blender Python scripts for compositing."""

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

    def generate_composite_script(self, job: RenderJob) -> str:
        """Generate Blender Python script for compositing."""
        script_lines = [
            "import bpy",
            "import bmesh",
            "import os",
            "import sys",
            "from mathutils import Vector",
            "",
            "# Clear existing mesh objects",
            "bpy.ops.object.select_all(action='SELECT')",
            "bpy.ops.object.delete(use_global=False)",
            "",
            "# Set render settings",
            f"bpy.context.scene.render.engine = '{job.config.engine.value}'",
            f"bpy.context.scene.render.resolution_x = {job.config.resolution_x}",
            f"bpy.context.scene.render.resolution_y = {job.config.resolution_y}",
            f"bpy.context.scene.frame_start = {job.config.frame_start}",
            f"bpy.context.scene.frame_end = {job.config.frame_end}",
            f"bpy.context.scene.render.fps = {job.config.fps}",
            f"bpy.context.scene.render.filepath = '{job.output_path}'",
            f"bpy.context.scene.render.image_settings.file_format = '{job.config.output_format}'",
            f"bpy.context.scene.render.image_settings.color_depth = '{job.config.color_depth}'",
            "",
        ]

        # Add engine-specific settings
        if job.config.engine == RenderEngine.CYCLES:
            script_lines.extend(
                [
                    "# Cycles settings",
                    f"bpy.context.scene.cycles.samples = {job.config.samples}",
                    f"bpy.context.scene.cycles.use_denoising = {job.config.use_denoising}",
                    f"bpy.context.scene.render.use_motion_blur = {job.config.use_motion_blur}",
                    "",
                ]
            )
        elif job.config.engine == RenderEngine.EEVEE:
            script_lines.extend(
                [
                    "# Eevee settings",
                    f"bpy.context.scene.eevee.taa_render_samples = {job.config.samples}",
                    "bpy.context.scene.eevee.use_bloom = True",
                    "bpy.context.scene.eevee.use_ssr = True",
                    "",
                ]
            )

        # Setup compositor
        script_lines.extend(
            [
                "# Enable compositor",
                "bpy.context.scene.use_nodes = True",
                "tree = bpy.context.scene.node_tree",
                "tree.nodes.clear()",
                "",
                "# Create render layers node",
                "render_layers = tree.nodes.new('CompositorNodeRLayers')",
                "render_layers.location = (0, 0)",
                "",
                "# Create composite output",
                "composite = tree.nodes.new('CompositorNodeComposite')",
                "composite.location = (800, 0)",
                "",
            ]
        )

        # Add layers
        y_offset = 0
        for i, layer in enumerate(job.layers):
            script_lines.extend(self._generate_layer_nodes(layer, i, y_offset))
            y_offset -= 300

        # Connect final composite
        script_lines.extend(
            [
                "",
                "# Connect final composite",
                "if len(tree.nodes) > 2:",
                "    last_node = [n for n in tree.nodes if n.type != 'COMPOSITE'][-1]",
                "    tree.links.new(last_node.outputs[0], composite.inputs[0])",
                "else:",
                "    tree.links.new(render_layers.outputs[0], composite.inputs[0])",
                "",
            ]
        )

        # Add checkpoint rendering logic
        script_lines.extend(self._generate_checkpoint_script(job))

        return "\n".join(script_lines)

    def _generate_layer_nodes(
        self, layer: CompositeLayer, index: int, y_offset: int
    ) -> List[str]:
        """Generate compositor nodes for a layer."""
        lines = [
            f"# Layer {index}: {layer.name}",
        ]

        if layer.type == "video":
            lines.extend(
                [
                    f"movie_clip_{index} = tree.nodes.new('CompositorNodeMovieClip')",
                    f"movie_clip_{index}.location = (200, {y_offset})",
                    f"# Load movie clip",
                    f"try:",
                    f"    clip = bpy.data.movieclips.load('{layer.source_path}')",
                    f"    movie_clip_{index}.clip = clip",
                    f"except:",
                    f"    print('Failed to load video: {layer.source_path}')",
                ]
            )
        elif layer.type == "image":
            lines.extend(
                [
                    f"image_{index} = tree.nodes.new('CompositorNodeImage')",
                    f"image_{index}.location = (200, {y_offset})",
                    f"# Load image",
                    f"try:",
                    f"    img = bpy.data.images.load('{layer.source_path}')",
                    f"    image_{index}.image = img",
                    f"except:",
                    f"    print('Failed to load image: {layer.source_path}')",
                ]
            )

        # Add transform nodes
        if (
            layer.scale != (1.0, 1.0)
            or layer.position != (0.0, 0.0)
            or layer.rotation != 0.0
        ):
            lines.extend(
                [
                    f"transform_{index} = tree.nodes.new('CompositorNodeTransform')",
                    f"transform_{index}.location = (400, {y_offset})",
                    f"transform_{index}.inputs['X'].default_value = {layer.position[0]}",
                    f"transform_{index}.inputs['Y'].default_value = {layer.position[1]}",
                    f"transform_{index}.inputs['Angle'].default_value = {layer.rotation}",
                    f"transform_{index}.inputs['Scale'].default_value = {layer.scale[0]}",
                ]
            )

        # Add alpha over node for blending
        if index > 0:
            lines.extend(
                [
                    f"alpha_over_{index} = tree.nodes.new('CompositorNodeAlphaOver')",
                    f"alpha_over_{index}.location = (600, {y_offset})",
                    f"alpha_over_{index}.inputs['Fac'].default_value = {layer.opacity}",
                ]
            )

        lines.append("")
        return lines

    def _generate_checkpoint_script(self, job: RenderJob) -> List[str]:
        """Generate checkpointed rendering script."""
        return [
            "# Checkpointed rendering function",
            "def render_with_checkpoints():",
            "    import json",
            "    import os",
            f"    checkpoint_file = '{job.output_path}_checkpoint.json'",
            f"    ",
            "    # Load checkpoint if exists",
            "    start_frame = bpy.context.scene.frame_start",
            "    if os.path.exists(checkpoint_file):",
            "        try:",
            "            with open(checkpoint_file, 'r') as f:",
            "                checkpoint = json.load(f)",
            "            start_frame = checkpoint.get('last_frame', start_frame) + 1",
            "            print(f'Resuming from frame {start_frame}')",
            "        except:",
            "            print('Failed to load checkpoint, starting from beginning')",
            "    ",
            "    # Render frames with checkpointing",
            "    for frame in range(start_frame, bpy.context.scene.frame_end + 1):",
            "        try:",
            "            bpy.context.scene.frame_set(frame)",
            "            ",
            "            # Set output filename with frame number",
            f"            output_file = '{job.output_path}_' + str(frame).zfill(4)",
            "            bpy.context.scene.render.filepath = output_file",
            "            ",
            "            # Render single frame",
            "            bpy.ops.render.render(write_still=True)",
            "            ",
            "            print(f'Rendered frame {frame}')",
            "            ",
            "            # Save checkpoint every N frames",
            f"            if frame % {job.config.checkpoint_interval} == 0:",
            "                checkpoint_data = {",
            "                    'last_frame': frame,",
            "                    'timestamp': str(bpy.context.scene.frame_current),",
            "                    'total_frames': bpy.context.scene.frame_end",
            "                }",
            "                with open(checkpoint_file, 'w') as f:",
            "                    json.dump(checkpoint_data, f)",
            "                print(f'Checkpoint saved at frame {frame}')",
            "            ",
            "        except Exception as e:",
            "            print(f'Error rendering frame {frame}: {e}')",
            "            # Save error checkpoint",
            "            error_checkpoint = {",
            "                'last_frame': frame - 1,",
            "                'error_frame': frame,",
            "                'error': str(e),",
            "                'timestamp': str(bpy.context.scene.frame_current)",
            "            }",
            "            with open(checkpoint_file, 'w') as f:",
            "                json.dump(error_checkpoint, f)",
            "            break",
            "    ",
            "    # Clean up checkpoint file on successful completion",
            "    if frame == bpy.context.scene.frame_end:",
            "        try:",
            "            os.remove(checkpoint_file)",
            "            print('Rendering completed successfully')",
            "        except:",
            "            pass",
            "",
            "# Execute checkpointed rendering",
            "render_with_checkpoints()",
        ]


class BlenderCompositor:
    """Main class for Blender compositing operations."""

    def __init__(self, blender_executable: Optional[str] = None):
        self.blender_executable = blender_executable or self._find_blender()
        self.logger = get_logger(self.__class__.__name__)
        self.script_generator = BlenderScriptGenerator()

        # Job tracking
        self.active_jobs: Dict[str, RenderJob] = {}
        self.job_queue = queue.Queue()
        self.executor = ThreadPoolExecutor(max_workers=2)

        # Setup temp directory
        self.temp_dir = Path(tempfile.gettempdir()) / "blender_compositor"
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        # Validate Blender installation
        if not self._validate_blender():
            self.logger.warning("Blender not found or invalid installation")

    def _find_blender(self) -> str:
        """Find Blender executable."""
        possible_paths = [
            "/Applications/Blender.app/Contents/MacOS/Blender",  # macOS
            "/usr/bin/blender",  # Linux
            "/usr/local/bin/blender",  # Linux
            "C:\\Program Files\\Blender Foundation\\Blender\\blender.exe",  # Windows
            "blender",  # In PATH
        ]

        for path in possible_paths:
            if shutil.which(path) or Path(path).exists():
                return path

        return "blender"  # Fallback

    def _validate_blender(self) -> bool:
        """Validate Blender installation."""
        try:
            result = subprocess.run(
                [self.blender_executable, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0 and "Blender" in result.stdout:
                self.logger.info(f"Blender found: {result.stdout.split()[1]}")
                return True
            else:
                self.logger.error(f"Blender validation failed: {result.stderr}")
                return False

        except Exception as e:
            self.logger.error(f"Blender validation error: {e}")
            return False

    def create_composite_job(
        self,
        layers: List[CompositeLayer],
        output_path: str,
        job_id: Optional[str] = None,
        config: Optional[RenderConfig] = None,
        mode: CompositeMode = CompositeMode.FULL_COMPOSITE,
    ) -> RenderJob:
        """Create a new composite job."""
        if job_id is None:
            job_id = f"composite_{int(time.time())}_{len(self.active_jobs)}"

        # Validate layer sources
        for layer in layers:
            if not Path(layer.source_path).exists():
                raise FileNotFoundError(f"Layer source not found: {layer.source_path}")

        # Create output directory
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Generate project file path
        project_file = str(self.temp_dir / f"{job_id}.blend")

        job = RenderJob(
            job_id=job_id,
            project_file=project_file,
            output_path=output_path,
            layers=layers,
            config=config or RenderConfig(),
            mode=mode,
            metadata={
                "created_at": datetime.now().isoformat(),
                "layer_count": len(layers),
                "estimated_frames": (
                    config.frame_end - config.frame_start + 1 if config else 250
                ),
            },
        )

        self.active_jobs[job_id] = job
        self.logger.info(f"Composite job created: {job_id}")

        return job

    def process_job(self, job_id: str) -> bool:
        """Process a composite job."""
        if job_id not in self.active_jobs:
            raise ValueError(f"Job not found: {job_id}")

        job = self.active_jobs[job_id]
        job.status = "processing"
        job.start_time = datetime.now()
        job.progress = 0.0

        self.logger.info(f"Processing composite job: {job_id}")

        try:
            # Generate Blender script
            script_content = self.script_generator.generate_composite_script(job)
            script_path = self.temp_dir / f"{job_id}_script.py"

            with open(script_path, "w") as f:
                f.write(script_content)

            job.progress = 10.0

            # Execute Blender with script
            success = self._execute_blender_script(job, str(script_path))

            if success:
                job.status = "completed"
                job.progress = 100.0
                job.end_time = datetime.now()

                # Collect rendered frames
                job.rendered_frames = self._collect_rendered_frames(job)

                self.logger.info(f"Composite job completed: {job_id}")
                return True
            else:
                job.status = "failed"
                job.error_message = "Blender execution failed"
                job.end_time = datetime.now()

                self.logger.error(f"Composite job failed: {job_id}")
                return False

        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            job.end_time = datetime.now()

            self.logger.error(f"Composite job error: {job_id} - {e}")
            return False

    def _execute_blender_script(self, job: RenderJob, script_path: str) -> bool:
        """Execute Blender with the generated script."""
        try:
            cmd = [
                self.blender_executable,
                "--background",  # Run in background
                "--factory-startup",  # Start with factory settings
                "--python",
                script_path,
            ]

            # Add memory limit if specified
            if job.config.max_memory_gb > 0:
                cmd.extend(
                    ["--", "--memory", str(int(job.config.max_memory_gb * 1024))]
                )

            self.logger.info(f"Executing Blender: {' '.join(cmd)}")

            # Start process with progress monitoring
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(self.temp_dir),
            )

            # Monitor progress
            self._monitor_render_progress(job, process)

            # Wait for completion
            stdout, stderr = process.communicate()

            if process.returncode == 0:
                self.logger.info("Blender execution completed successfully")
                return True
            else:
                self.logger.error(f"Blender execution failed: {stderr}")
                job.error_message = stderr
                return False

        except Exception as e:
            self.logger.error(f"Error executing Blender: {e}")
            job.error_message = str(e)
            return False

    def _monitor_render_progress(
        self, job: RenderJob, process: subprocess.Popen
    ) -> None:
        """Monitor render progress and update job status."""

        def monitor():
            total_frames = job.config.frame_end - job.config.frame_start + 1

            while process.poll() is None:
                try:
                    # Check for checkpoint file
                    checkpoint_file = f"{job.output_path}_checkpoint.json"
                    if Path(checkpoint_file).exists():
                        with open(checkpoint_file, "r") as f:
                            checkpoint = json.load(f)

                        current_frame = checkpoint.get(
                            "last_frame", job.config.frame_start
                        )
                        job.current_frame = current_frame
                        job.progress = min(90.0, (current_frame / total_frames) * 90.0)

                    time.sleep(2)  # Check every 2 seconds

                except Exception as e:
                    self.logger.debug(f"Progress monitoring error: {e}")

        # Start monitoring in separate thread
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()

    def _collect_rendered_frames(self, job: RenderJob) -> List[int]:
        """Collect list of successfully rendered frames."""
        rendered_frames = []
        output_dir = Path(job.output_path).parent
        base_name = Path(job.output_path).stem

        for frame in range(job.config.frame_start, job.config.frame_end + 1):
            frame_file = (
                output_dir
                / f"{base_name}_{frame:04d}.{job.config.output_format.lower()}"
            )
            if frame_file.exists():
                rendered_frames.append(frame)

        return rendered_frames

    def resume_job(self, job_id: str) -> bool:
        """Resume a failed or paused job from checkpoint."""
        if job_id not in self.active_jobs:
            raise ValueError(f"Job not found: {job_id}")

        job = self.active_jobs[job_id]

        if job.status not in ["failed", "paused"]:
            self.logger.warning(
                f"Job {job_id} is not in a resumable state: {job.status}"
            )
            return False

        self.logger.info(f"Resuming job: {job_id}")
        return self.process_job(job_id)

    def pause_job(self, job_id: str) -> bool:
        """Pause a running job."""
        if job_id not in self.active_jobs:
            return False

        job = self.active_jobs[job_id]
        if job.status == "processing":
            job.status = "paused"
            self.logger.info(f"Job paused: {job_id}")
            return True

        return False

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a job."""
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
            job.status = "cancelled"
            job.end_time = datetime.now()
            self.logger.info(f"Job cancelled: {job_id}")
            return True
        return False

    def get_job_status(self, job_id: str) -> Optional[RenderJob]:
        """Get status of a composite job."""
        return self.active_jobs.get(job_id)

    def cleanup_temp_files(self, job_id: Optional[str] = None) -> None:
        """Clean up temporary files."""
        try:
            if job_id:
                # Clean up specific job files
                patterns = [f"{job_id}*"]
                for pattern in patterns:
                    for file_path in self.temp_dir.glob(pattern):
                        file_path.unlink(missing_ok=True)
            else:
                # Clean up all temp files
                shutil.rmtree(self.temp_dir)
                self.temp_dir.mkdir(parents=True, exist_ok=True)

            self.logger.info(f"Temporary files cleaned up: {job_id or 'all'}")
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")

    def create_avatar_composite(
        self,
        avatar_video: str,
        background_image: str,
        output_path: str,
        effects: Optional[List[str]] = None,
    ) -> str:
        """Convenience method to create avatar composite."""
        layers = [
            CompositeLayer(
                name="background",
                type="image",
                source_path=background_image,
                blend_mode="ALPHA_OVER",
                opacity=1.0,
            ),
            CompositeLayer(
                name="avatar",
                type="video",
                source_path=avatar_video,
                blend_mode="ALPHA_OVER",
                opacity=1.0,
            ),
        ]

        # Add effect layers if specified
        if effects:
            for i, effect in enumerate(effects):
                if Path(effect).exists():
                    layers.append(
                        CompositeLayer(
                            name=f"effect_{i}",
                            type=(
                                "image"
                                if effect.lower().endswith((".png", ".jpg", ".jpeg"))
                                else "video"
                            ),
                            source_path=effect,
                            blend_mode="SCREEN",
                            opacity=0.5,
                        )
                    )

        config = RenderConfig(
            engine=RenderEngine.EEVEE,
            quality=RenderQuality.PRODUCTION,
            resolution_x=1920,
            resolution_y=1080,
            fps=24,
        )

        job = self.create_composite_job(
            layers=layers,
            output_path=output_path,
            config=config,
            mode=CompositeMode.AVATAR_BACKGROUND,
        )

        if self.process_job(job.job_id):
            return job.job_id
        else:
            raise RuntimeError(
                f"Failed to create avatar composite: {job.error_message}"
            )


# Example usage and testing
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Create BlenderCompositor instance
    compositor = BlenderCompositor()

    # Example usage
    try:
        # Create avatar composite
        job_id = compositor.create_avatar_composite(
            avatar_video="./assets/avatar_animation.mp4",
            background_image="./assets/office_background.jpg",
            output_path="./output/final_composite",
            effects=["./assets/particle_effect.mp4"],
        )

        print(f"Avatar composite job created: {job_id}")

        # Monitor job progress
        while True:
            job = compositor.get_job_status(job_id)
            if job:
                print(f"Progress: {job.progress:.1f}% - Frame: {job.current_frame}")

                if job.status in ["completed", "failed", "cancelled"]:
                    break

            time.sleep(5)

        if job.status == "completed":
            print(f"Composite completed: {len(job.rendered_frames)} frames rendered")
        else:
            print(f"Composite failed: {job.error_message}")

        # Cleanup
        compositor.cleanup_temp_files(job_id)

    except Exception as e:
        print(f"Error: {e}")
