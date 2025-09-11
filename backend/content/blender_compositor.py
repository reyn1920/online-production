#!/usr / bin / env python3
"""
Blender Compositor - Avatar Video Compositing with Checkpointed Rendering

This module implements Blender integration for compositing avatar videos,
backgrounds, and VFX with crash recovery through checkpointed rendering.
It supports batch processing, automated scene setup, and render optimization.

Author: TRAE.AI System
Version: 1.0.0
"""

import contextlib
import hashlib
import json
import logging
import multiprocessing
import os
import pickle
import platform
import queue
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import uuid
import weakref
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import psutil

# Import TRAE.AI utilities
try:
    from utils.logger import get_logger
except ImportError:


    def get_logger(name):
        return logging.getLogger(name)


class ResourceMonitor:
    """Monitor system resources during rendering."""


    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.monitoring = False
        self.stats = {
            "cpu_percent": [],
                "memory_percent": [],
                "disk_usage": [],
                "network_io": [],
                }


    def start_monitoring(self):
        """Start resource monitoring."""
        self.monitoring = True
        self.logger.info("Resource monitoring started")


    def stop_monitoring(self):
        """Stop resource monitoring."""
        self.monitoring = False
        self.logger.info("Resource monitoring stopped")


    def get_current_stats(self) -> Dict[str, float]:
        """Get current system resource statistics."""
        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval = 1),
                    "memory_percent": psutil.virtual_memory().percent,
                    "disk_usage": psutil.disk_usage("/").percent,
                    "available_memory_gb": psutil.virtual_memory().available / (1024**3),
                    }
        except Exception as e:
            self.logger.error(f"Error getting system stats: {e}")
            return {}


    def check_resource_limits(
        self, memory_limit_gb: float = 8.0, cpu_limit: float = 90.0
    ) -> bool:
        """Check if system resources are within limits."""
        stats = self.get_current_stats()
        if not stats:
            return True  # Assume OK if we can't get stats

        memory_ok = stats.get("available_memory_gb", 0) > memory_limit_gb
        cpu_ok = stats.get("cpu_percent", 0) < cpu_limit

        return memory_ok and cpu_ok


class CacheManager:
    """Manage rendering cache and temporary files."""


    def __init__(self, cache_dir: Path):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents = True, exist_ok = True)
        self.logger = get_logger(self.__class__.__name__)
        self.cache_index = {}


    def get_cache_key(self, job: "RenderJob") -> str:
        """Generate cache key for a render job."""
        job_data = f"{job.job_id}_{job.config.frame_start}_{job.config.frame_end}"
        return hashlib.md5(job_data.encode()).hexdigest()


    def is_cached(self, cache_key: str) -> bool:
        """Check if result is cached."""
        cache_file = self.cache_dir / f"{cache_key}.cache"
        return cache_file.exists()


    def get_cached_result(self, cache_key: str) -> Optional[Dict]:
        """Get cached result."""
        cache_file = self.cache_dir / f"{cache_key}.cache"
        if cache_file.exists():
            try:
                with open(cache_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Error reading cache: {e}")
        return None


    def cache_result(self, cache_key: str, result: Dict):
        """Cache render result."""
        cache_file = self.cache_dir / f"{cache_key}.cache"
        try:
            with open(cache_file, "w") as f:
                json.dump(result, f)
            self.cache_index[cache_key] = {
                "timestamp": time.time(),
                    "file": str(cache_file),
                    }
        except Exception as e:
            self.logger.error(f"Error caching result: {e}")


    def cleanup_old_cache(self, max_age_hours: int = 24):
        """Clean up old cache files."""
        cutoff_time = time.time() - (max_age_hours * 3600)
        cleaned = 0

        for cache_file in self.cache_dir.glob("*.cache"):
            try:
                if cache_file.stat().st_mtime < cutoff_time:
                    cache_file.unlink()
                    cleaned += 1
            except Exception as e:
                self.logger.error(f"Error cleaning cache file {cache_file}: {e}")

        self.logger.info(f"Cleaned {cleaned} old cache files")


    def get_cache_size(self) -> Dict[str, float]:
        """Get cache directory size statistics."""
        total_size = 0
        file_count = 0

        for cache_file in self.cache_dir.rglob("*"):
            if cache_file.is_file():
                total_size += cache_file.stat().st_size
                file_count += 1

        return {
            "total_size_mb": total_size / (1024 * 1024),
                "file_count": file_count,
                "directory": str(self.cache_dir),
                }


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


class RenderPriority(Enum):
    """Render job priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class DistributedMode(Enum):
    """Distributed rendering modes."""

    SINGLE_MACHINE = "single_machine"
    NETWORK_RENDER = "network_render"
    CLOUD_RENDER = "cloud_render"


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

    # Enhanced checkpoint and recovery settings
    checkpoint_interval: int = 10  # Frames between checkpoints
    auto_recovery: bool = True
    recovery_attempts: int = 3
    frame_timeout: int = 300  # Seconds per frame timeout

    # Memory and performance settings
    max_memory_gb: float = 8.0
    memory_limit_per_frame: float = 2.0
    thread_count: Optional[int] = None
    tile_size: int = 256
    use_persistent_data: bool = True

    # Output settings
    output_format: str = "PNG"  # PNG, JPEG, EXR, etc.
    color_depth: str = "8"  # 8, 16, 32
    compression: int = 15  # 0 - 100 for JPEG, 0 - 100 for PNG

    # Distributed rendering
    distributed_mode: DistributedMode = DistributedMode.SINGLE_MACHINE
    render_nodes: List[str] = field(default_factory = list)
    chunk_size: int = 5  # Frames per chunk for distributed rendering

    # Quality and optimization
    adaptive_sampling: bool = True
    light_threshold: float = 0.01
    use_optix: bool = True  # For RTX cards
    use_opencl: bool = False

    # Advanced features
    enable_cryptomatte: bool = False
    enable_motion_vectors: bool = False
    enable_z_pass: bool = False
    custom_passes: List[str] = field(default_factory = list)

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
    """Generates Blender Python scripts for compositing operations with advanced features."""


    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.script_templates = {
            "basic_composite": self._get_basic_composite_template(),
                "advanced_composite": self._get_advanced_composite_template(),
                "checkpoint_render": self._get_checkpoint_template(),
                "distributed_render": self._get_distributed_template(),
                "memory_optimized": self._get_memory_optimized_template(),
                }
        self.node_cache = {}
        self.performance_metrics = {
            "render_times": [],
                "memory_usage": [],
                "error_count": 0,
                }


    def generate_composite_script(self, job: RenderJob) -> str:
        """Generate a complete Blender Python script for compositing with advanced features."""
        config = job.config
        layers = job.layers

        # Choose template based on complexity and configuration
        template_key = self._select_optimal_template(config, layers)

        script_lines = [
            "import bpy",
                "import bmesh",
                "import os",
                "import sys",
                "import psutil",
                "import gc",
                "from mathutils import Vector",
                "",
                "# Clear existing mesh objects",
                "bpy.ops.object.select_all(action='SELECT')",
                "bpy.ops.object.delete(use_global = False)",
                "",
                "# Set render settings with error handling",
                "try:",
                f"    bpy.context.scene.render.engine = '{job.config.engine.value}'",
                f"    bpy.context.scene.render.resolution_x = {job.config.resolution_x}",
                f"    bpy.context.scene.render.resolution_y = {job.config.resolution_y}",
                f"    bpy.context.scene.frame_start = {job.config.frame_start}",
                f"    bpy.context.scene.frame_end = {job.config.frame_end}",
                f"    bpy.context.scene.render.fps = {job.config.fps}",
                f"    bpy.context.scene.render.filepath = '{job.output_path}'",
                f"    bpy.context.scene.render.image_settings.file_format = '{job.config.output_format}'",
                f"    bpy.context.scene.render.image_settings.color_depth = '{job.config.color_depth}'",
                "except Exception as e:",
                "    print(f'Error setting render settings: {e}')",
                "    raise",
                "",
                ]

        # Add engine - specific settings
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

        # Add memory management and performance optimizations
        script_lines.extend(self._get_memory_settings(config))
        script_lines.extend(self._get_performance_settings(config))

        # Add distributed rendering settings if enabled
        if config.distributed_mode != DistributedMode.SINGLE_MACHINE:
            script_lines.extend(self._get_distributed_settings(config))

        # Add error handling and cleanup code
        script_lines.extend(self._get_error_handling_code())
        script_lines.extend(self._get_cleanup_code())

        # Add helper methods for advanced features
        script_lines.extend(
            [
                "",
                    "# Helper methods for advanced features",
                    self._get_basic_composite_template(),
                    self._get_advanced_composite_template(),
                    self._get_checkpoint_template(),
                    self._get_distributed_template(),
                    self._get_memory_optimized_template(),
                    ]
        )

        return "\n".join(script_lines)


    def _select_optimal_template(
        self, config: RenderConfig, layers: List[CompositeLayer]
    ) -> str:
        """Select the optimal template based on configuration and complexity."""
        if config.distributed_mode != DistributedMode.SINGLE_MACHINE:
            return "distributed_render"
        elif config.max_memory_gb < 4.0 or len(layers) > 10:
            return "memory_optimized"
        elif len(layers) > 5 or config.quality == RenderQuality.FINAL:
            return "advanced_composite"
        else:
            return "basic_composite"


    def _generate_node_cache_key(
        self, layers: List[CompositeLayer], mode: CompositeMode
    ) -> str:
        """Generate cache key for node configuration."""
        layer_hash = hashlib.md5(
            str([(l.name, l.type, l.blend_mode) for l in layers]).encode()
        ).hexdigest()
        return f"{mode.value}_{layer_hash}_{len(layers)}"


    def _generate_layer_cache_key(self, layer: CompositeLayer, index: int) -> str:
        """Generate cache key for layer configuration."""
        layer_data = (
            f"{layer.name}_{layer.type}_{layer.blend_mode}_{layer.opacity}_{index}"
        )
        return hashlib.md5(layer_data.encode()).hexdigest()


    def _get_memory_settings(self, config: RenderConfig) -> List[str]:
        """Generate memory optimization settings."""
        return [
            "",
                "# Memory optimization settings",
                f"bpy.context.preferences.system.memory_cache_limit = {int(config.max_memory_gb * 1024)}",
                "bpy.context.preferences.system.use_gpu_subdivision = True",
                "# Force garbage collection",
                "import gc",
                "gc.collect()",
                ]


    def _get_performance_settings(self, config: RenderConfig) -> List[str]:
        """Generate performance optimization settings."""
        return [
            "",
                "# Performance optimization settings",
                f"bpy.context.scene.render.threads_mode = 'AUTO'",
                f"bpy.context.scene.render.threads = {config.thread_count or multiprocessing.cpu_count()}",
                f"bpy.context.scene.render.tile_x = {config.tile_size}",
                f"bpy.context.scene.render.tile_y = {config.tile_size}",
                f"bpy.context.scene.render.use_persistent_data = {config.use_persistent_data}",
                ]


    def _get_distributed_settings(self, config: RenderConfig) -> List[str]:
        """Generate distributed rendering settings."""
        return [
            "",
                "# Distributed rendering settings",
                "# TODO: Implement network rendering configuration",
                f"# Render nodes: {config.render_nodes}",
                f"# Chunk size: {config.chunk_size}",
                ]


    def _get_error_handling_code(self) -> List[str]:
        """Generate error handling code."""
        return [
            "",
                "# Error handling and recovery",
                "def handle_render_error(frame, error):",
                "    print(f'Render error at frame {frame}: {error}')",
                "    # Log error for analysis",
                "    with open('render_errors.log', 'a') as f:",
                "        f.write(f'{frame}: {error}\\n')",
                ]


    def _get_cleanup_code(self) -> List[str]:
        """Generate cleanup code."""
        return [
            "",
                "# Cleanup and memory management",
                "def cleanup_resources():",
                "    # Clear unused data blocks",
                "    bpy.ops.outliner.orphans_purge()",
                "    # Force garbage collection",
                "    import gc",
                "    gc.collect()",
                ]


    def _get_basic_composite_template(self) -> str:
        """Get basic composite template."""
        return "# Basic composite template placeholder"


    def _get_advanced_composite_template(self) -> str:
        """Get advanced composite template."""
        return "# Advanced composite template placeholder"


    def _get_checkpoint_template(self) -> str:
        """Get checkpoint template."""
        return "# Checkpoint template placeholder"


    def _get_distributed_template(self) -> str:
        """Get distributed rendering template."""
        return "# Distributed rendering template placeholder"


    def _get_memory_optimized_template(self) -> str:
        """Get memory optimized template."""
        return "# Memory optimized template placeholder"


    def _generate_layer_nodes(
        self, layer: CompositeLayer, index: int, y_offset: int
    ) -> List[str]:
        """Generate optimized compositor nodes for a layer with caching."""
        # Check cache for similar layer configurations
        cache_key = self._generate_layer_cache_key(layer, index)
        if cache_key in self.node_cache:
            return self.node_cache[cache_key]

        lines = [
            f"# Layer {index}: {layer.name} with advanced settings",
                ]

        if layer.type == "video":
            lines.extend(
                [
                    f"try:",
                        f"    movie_clip_{index} = tree.nodes.new('CompositorNodeMovieClip')",
                        f"    movie_clip_{index}.location = (200, {y_offset})",
                        f"    # Load movie clip with memory optimization",
                        f"    clip = bpy.data.movieclips.load('{layer.source_path}')",
                        f"    movie_clip_{index}.clip = clip",
                        f"    # Configure video settings",
                        f"    if hasattr(movie_clip_{index}, 'frame_duration'):",
                        f"        movie_clip_{index}.frame_duration = {layer.end_frame - layer.start_frame if layer.end_frame else 250}",
                        f"    if hasattr(movie_clip_{index}, 'frame_offset'):",
                        f"        movie_clip_{index}.frame_offset = {layer.start_frame}",
                        f"except Exception as e:",
                        f"    print(f'Failed to load video {layer.source_path}: {{e}}')",
                        f"    raise",
                        ]
            )
        elif layer.type == "image":
            lines.extend(
                [
                    f"try:",
                        f"    image_{index} = tree.nodes.new('CompositorNodeImage')",
                        f"    image_{index}.location = (200, {y_offset})",
                        f"    # Load image with memory optimization",
                        f"    img = bpy.data.images.load('{layer.source_path}')",
                        f"    image_{index}.image = img",
                        f"    # Configure image settings",
                        f"    if hasattr(img, 'colorspace_settings'):",
                        f"        img.colorspace_settings.name = 'sRGB'",
                        f"except Exception as e:",
                        f"    print(f'Failed to load image {layer.source_path}: {{e}}')",
                        f"    raise",
                        ]
            )

        # Add transform nodes with enhanced features
        if (
            layer.scale != (1.0, 1.0)
            or layer.position != (0.0, 0.0)
            or layer.rotation != 0.0
        ):
            lines.extend(
                [
                    f"try:",
                        f"    transform_{index} = tree.nodes.new('CompositorNodeTransform')",
                        f"    transform_{index}.location = (400, {y_offset})",
                        f"    transform_{index}.inputs['X'].default_value = {layer.position[0]}",
                        f"    transform_{index}.inputs['Y'].default_value = {layer.position[1]}",
                        f"    transform_{index}.inputs['Angle'].default_value = {layer.rotation}",
                        f"    transform_{index}.inputs['Scale'].default_value = {layer.scale[0]}",
                        f"    # Add interpolation settings",
                        f"    if hasattr(transform_{index}, 'filter_type'):",
                        f"        transform_{index}.filter_type = 'BICUBIC'",
                        f"except Exception as e:",
                        f"    print(f'Error creating transform node for layer {index}: {{e}}')",
                        f"    raise",
                        ]
            )

        # Add alpha over node for blending with advanced blend modes
        if index > 0:
            lines.extend(
                [
                    f"try:",
                        f"    alpha_over_{index} = tree.nodes.new('CompositorNodeAlphaOver')",
                        f"    alpha_over_{index}.location = (600, {y_offset})",
                        f"    alpha_over_{index}.inputs['Fac'].default_value = {layer.opacity}",
                        f"    # Configure blend mode",
                        f"    if hasattr(alpha_over_{index}, 'blend_type'):",
                        f"        alpha_over_{index}.blend_type = '{layer.blend_mode}'",
                        f"except Exception as e:",
                        f"    print(f'Error creating alpha over node for layer {index}: {{e}}')",
                        f"    raise",
                        ]
            )

        lines.append("")
        self.node_cache[cache_key] = lines
        return lines


    def _generate_alpha_over_nodes(self, layer_count: int) -> str:
        """Generate alpha over compositing nodes."""
        nodes = []
        for i in range(1, layer_count):
            nodes.append(
                f"""
# Alpha over blend for layer {i}
try:
    alpha_over_{i} = tree.nodes.new('CompositorNodeAlphaOver')
    alpha_over_{i}.location = ({600 + i * 200}, 0)
    alpha_over_{i}.inputs['Fac'].default_value = 1.0
    # Connect previous layer
    if {i} == 1:
        tree.links.new(render_layer_0.outputs[0], alpha_over_{i}.inputs[1])
        tree.links.new(render_layer_{i}.outputs[0], alpha_over_{i}.inputs[2])
    else:
        tree.links.new(alpha_over_{i - 1}.outputs[0], alpha_over_{i}.inputs[1])
        tree.links.new(render_layer_{i}.outputs[0], alpha_over_{i}.inputs[2])
except Exception as e:
    print(f'Error creating alpha over node {i}: {{e}}')
    raise
"""
            )
        return "\n".join(nodes)


    def _generate_multiply_nodes(self, layer_count: int) -> str:
        """Generate multiply compositing nodes."""
        nodes = []
        for i in range(1, layer_count):
            nodes.append(
                f"""
# Multiply blend for layer {i}
try:
    multiply_{i} = tree.nodes.new('CompositorNodeMixRGB')
    multiply_{i}.location = ({600 + i * 200}, 0)
    multiply_{i}.blend_type = 'MULTIPLY'
    multiply_{i}.inputs['Fac'].default_value = 1.0
    # Connect previous layer
    if {i} == 1:
        tree.links.new(render_layer_0.outputs[0], multiply_{i}.inputs[1])
        tree.links.new(render_layer_{i}.outputs[0], multiply_{i}.inputs[2])
    else:
        tree.links.new(multiply_{i - 1}.outputs[0], multiply_{i}.inputs[1])
        tree.links.new(render_layer_{i}.outputs[0], multiply_{i}.inputs[2])
except Exception as e:
    print(f'Error creating multiply node {i}: {{e}}')
    raise
"""
            )
        return "\n".join(nodes)


    def _generate_screen_nodes(self, layer_count: int) -> str:
        """Generate screen compositing nodes."""
        nodes = []
        for i in range(1, layer_count):
            nodes.append(
                f"""
# Screen blend for layer {i}
try:
    screen_{i} = tree.nodes.new('CompositorNodeMixRGB')
    screen_{i}.location = ({600 + i * 200}, 0)
    screen_{i}.blend_type = 'SCREEN'
    screen_{i}.inputs['Fac'].default_value = 1.0
    # Connect previous layer
    if {i} == 1:
        tree.links.new(render_layer_0.outputs[0], screen_{i}.inputs[1])
        tree.links.new(render_layer_{i}.outputs[0], screen_{i}.inputs[2])
    else:
        tree.links.new(screen_{i - 1}.outputs[0], screen_{i}.inputs[1])
        tree.links.new(render_layer_{i}.outputs[0], screen_{i}.inputs[2])
except Exception as e:
    print(f'Error creating screen node {i}: {{e}}')
    raise
"""
            )
        return "\n".join(nodes)


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
                "        except Exception:",
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
                "            bpy.ops.render.render(write_still = True)",
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
                "        except Exception:",
                "            pass",
                "",
                "# Execute checkpointed rendering",
                "render_with_checkpoints()",
                ]


class BlenderCompositor:
    """Advanced Blender compositing manager with production - ready features."""


    def __init__(self, blender_executable: Optional[str] = None, max_workers: int = 2):
        self.blender_executable = blender_executable or self._find_blender()
        self.logger = get_logger(self.__class__.__name__)
        self.script_generator = BlenderScriptGenerator()

        # Advanced job management
        self.active_jobs: Dict[str, RenderJob] = {}
        self.completed_jobs: Dict[str, RenderJob] = {}
        self.failed_jobs: Dict[str, RenderJob] = {}
        self.job_queue = queue.PriorityQueue()  # Priority - based queue
        self.job_history: List[RenderJob] = []  # Complete job history
        self.job_lock = threading.RLock()  # Reentrant lock for thread safety

        # Performance monitoring
        self.performance_monitor = {
            "total_render_time": 0.0,
                "average_frame_time": 0.0,
                "memory_peak": 0.0,
                "jobs_completed": 0,
                "jobs_failed": 0,
                "system_resources": {},
                }

        # Thread pool with enhanced configuration
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(
            max_workers = max_workers, thread_name_prefix="BlenderCompositor"
        )

        # Network and distributed rendering
        self.render_nodes: List[str] = []
        self.network_manager = None

        # Setup temp directory
        self.temp_dir = Path(tempfile.gettempdir()) / "blender_compositor"
        self.temp_dir.mkdir(parents = True, exist_ok = True)

        # Cache management
        self.cache_dir = self.temp_dir / "cache"
        self.cache_dir.mkdir(exist_ok = True)

        # Validate Blender installation
        if not self._validate_blender():
            self.logger.warning("Blender not found or invalid installation")

        # Initialize monitoring
        self._start_system_monitoring()


    def _find_blender(self) -> str:
        """Find Blender executable."""
        possible_paths = [
            "/Applications / Blender.app / Contents / MacOS / Blender",  # macOS
            "/usr / bin / blender",  # Linux
            "/usr / local / bin / blender",  # Linux
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
                    capture_output = True,
                    text = True,
                    timeout = 10,
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
        Path(output_path).parent.mkdir(parents = True, exist_ok = True)

        # Generate project file path
        project_file = str(self.temp_dir / f"{job_id}.blend")

        job = RenderJob(
            job_id = job_id,
                project_file = project_file,
                output_path = output_path,
                layers = layers,
                config = config or RenderConfig(),
                mode = mode,
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
                "--factory - startup",  # Start with factory settings
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
                    stdout = subprocess.PIPE,
                    stderr = subprocess.PIPE,
                    text = True,
                    cwd = str(self.temp_dir),
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
        monitor_thread = threading.Thread(target = monitor, daemon = True)
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
                        file_path.unlink(missing_ok = True)
            else:
                # Clean up all temp files
                shutil.rmtree(self.temp_dir)
                self.temp_dir.mkdir(parents = True, exist_ok = True)

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
                    source_path = background_image,
                    blend_mode="ALPHA_OVER",
                    opacity = 1.0,
                    ),
                CompositeLayer(
                name="avatar",
                    type="video",
                    source_path = avatar_video,
                    blend_mode="ALPHA_OVER",
                    opacity = 1.0,
                    ),
                ]

        # Add effect layers if specified
        if effects:
            for i, effect in enumerate(effects):
                if Path(effect).exists():
                    layers.append(
                        CompositeLayer(
                            name = f"effect_{i}",
                                type=(
                                "image"
                                if effect.lower().endswith((".png", ".jpg", ".jpeg"))
                                else "video"
                            ),
                                source_path = effect,
                                blend_mode="SCREEN",
                                opacity = 0.5,
                                )
                    )

        config = RenderConfig(
            engine = RenderEngine.EEVEE,
                quality = RenderQuality.PRODUCTION,
                resolution_x = 1920,
                resolution_y = 1080,
                fps = 24,
                )

        job = self.create_composite_job(
            layers = layers,
                output_path = output_path,
                config = config,
                mode = CompositeMode.AVATAR_BACKGROUND,
                )

        if self.process_job(job.job_id):
            return job.job_id
        else:
            raise RuntimeError(
                f"Failed to create avatar composite: {job.error_message}"
            )


    def _start_system_monitoring(self):
        """Start system resource monitoring."""


        def monitor_resources():
            while True:
                try:
                    stats = {
                        "cpu_percent": psutil.cpu_percent(interval = 1),
                            "memory_percent": psutil.virtual_memory().percent,
                            "disk_usage": psutil.disk_usage("/").percent,
                            "timestamp": time.time(),
                            }
                    self.performance_monitor["system_resources"] = stats

                    # Log warnings for high resource usage
                    if stats["memory_percent"] > 90:
                        self.logger.warning(
                            f"High memory usage: {stats['memory_percent']:.1f}%"
                        )
                    if stats["cpu_percent"] > 95:
                        self.logger.warning(
                            f"High CPU usage: {stats['cpu_percent']:.1f}%"
                        )

                    time.sleep(30)  # Monitor every 30 seconds
                except Exception as e:
                    self.logger.error(f"Resource monitoring error: {e}")
                    time.sleep(60)  # Wait longer on error

        monitor_thread = threading.Thread(target = monitor_resources, daemon = True)
        monitor_thread.start()


    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        with self.job_lock:
            active_jobs = len(self.active_jobs)
            completed_jobs = len(self.completed_jobs)
            failed_jobs = len(self.failed_jobs)

        return {
            "blender_executable": self.blender_executable,
                "temp_directory": str(self.temp_dir),
                "cache_directory": str(self.cache_dir),
                "max_workers": self.max_workers,
                "jobs": {
                "active": active_jobs,
                    "completed": completed_jobs,
                    "failed": failed_jobs,
                    "total_processed": self.performance_monitor["jobs_completed"]
                + self.performance_monitor["jobs_failed"],
                    },
                "performance": self.performance_monitor,
                "system_resources": self.performance_monitor.get("system_resources", {}),
                "distributed_nodes": len(self.render_nodes),
                }


    def optimize_performance(self) -> Dict[str, Any]:
        """Optimize system performance based on current conditions."""
        optimizations = []
        system_stats = self.performance_monitor.get("system_resources", {})

        # Memory optimization
        if system_stats.get("memory_percent", 0) > 80:
            # Clean up old cache files
            cache_cleaned = 0
            for cache_file in self.cache_dir.glob("*.cache"):
                try:
                    if time.time() - cache_file.stat().st_mtime > 3600:  # 1 hour old
                        cache_file.unlink()
                        cache_cleaned += 1
                except Exception:
                    pass

            if cache_cleaned > 0:
                optimizations.append(f"Cleaned {cache_cleaned} old cache files")

        # CPU optimization
        if system_stats.get("cpu_percent", 0) > 90:
            # Reduce worker threads temporarily
            if self.max_workers > 1:
                self.max_workers = max(1, self.max_workers - 1)
                optimizations.append(f"Reduced worker threads to {self.max_workers}")

        # Disk space optimization
        if system_stats.get("disk_usage", 0) > 90:
            self.cleanup_temp_files()
            optimizations.append("Cleaned temporary files")

        return {
            "optimizations_applied": optimizations,
                "system_stats": system_stats,
                "timestamp": datetime.now().isoformat(),
                }


    def setup_distributed_rendering(self, nodes: List[str]) -> bool:
        """Setup distributed rendering nodes.

        Args:
            nodes: List of node addresses (e.g., ['192.168.1.100:8080', 'node2.local:8080'])
        """
        self.render_nodes = nodes
        available_nodes = 0

        for node in nodes:
            try:
                # Simple connectivity test (ping - like)
                host, port = node.split(":") if ":" in node else (node, "22")
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((host, int(port)))
                sock.close()

                if result == 0:
                    available_nodes += 1
                    self.logger.info(f"Render node available: {node}")
                else:
                    self.logger.warning(f"Render node unavailable: {node}")

            except Exception as e:
                self.logger.error(f"Error testing node {node}: {e}")

        self.logger.info(
            f"Distributed rendering: {available_nodes}/{len(nodes)} nodes available"
        )
        return available_nodes > 0


    def shutdown(self):
        """Shutdown the compositor and clean up resources."""
        self.logger.info("Shutting down Blender compositor...")

        # Cancel all active jobs
        with self.job_lock:
            for job_id in list(self.active_jobs.keys()):
                self.cancel_job(job_id)

        # Shutdown thread pool
        self.executor.shutdown(wait = True)

        # Clean up temporary files
        try:
            shutil.rmtree(self.temp_dir, ignore_errors = True)
        except Exception as e:
            self.logger.error(f"Error cleaning temp directory: {e}")

        self.logger.info("Blender compositor shutdown complete")

# Example usage and testing
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level = logging.INFO)

    # Create BlenderCompositor instance
    compositor = BlenderCompositor()

    # Example usage
    try:
        # Create avatar composite
        job_id = compositor.create_avatar_composite(
            avatar_video="./assets / avatar_animation.mp4",
                background_image="./assets / office_background.jpg",
                output_path="./output / final_composite",
                effects=["./assets / particle_effect.mp4"],
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
