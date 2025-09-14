# M1 MacBook Air Optimization Configuration for Linly - Talker
# Optimized for Apple Silicon M1 with 16GB RAM
# Based on research and best practices for M1 performance

import os
import platform

import torch

# ============================================================================
# DEVICE AND MEMORY OPTIMIZATION FOR M1 MACBOOK AIR
# ============================================================================

# Force MPS (Metal Performance Shaders) usage on M1 Macs
if platform.system() == "Darwin" and torch.backends.mps.is_available():
    DEVICE = "mps"
    print("✅ Using MPS (Metal Performance Shaders) for M1 optimization")
else:
    DEVICE = "cpu"
    print("⚠️ MPS not available, falling back to CPU")

# Memory optimization settings for 16GB RAM
MEMORY_OPTIMIZATION = {
    "max_memory_fraction": 0.7,  # Use max 70% of available memory
    "enable_memory_efficient_attention": True,
    "gradient_checkpointing": True,
    "mixed_precision": True,
    "cpu_offload": True,  # Offload unused models to CPU
}

# ============================================================================
# MODEL OPTIMIZATION SETTINGS
# ============================================================================

# Optimized model selections for M1 performance
OPTIMIZED_MODELS = {
    # Use lighter ASR model for better performance
    "asr_model": "whisper - base",  # Instead of large models
    # Use efficient TTS
    "tts_model": "edge - tts",  # Lightweight and fast
    # Optimized avatar generation
    "avatar_model": "wav2lip",  # More M1 - friendly than SadTalker
    # Lightweight LLM options
    "llm_model": "qwen - 1.8b",  # Smaller model for better performance
}

# ============================================================================
# PERFORMANCE OPTIMIZATION PARAMETERS
# ============================================================================

# Batch processing optimization
BATCH_SETTINGS = {
    "batch_size": 1,  # Single batch for memory efficiency
    "max_concurrent_requests": 1,  # Prevent memory overflow
    "queue_size": 2,  # Small queue to prevent memory buildup
}

# Video generation optimization
VIDEO_SETTINGS = {
    "fps": 20,  # Reduced from 25 for better performance
    "resolution": 256,  # Optimized resolution for M1
    "quality": "medium",  # Balance between quality and performance
    "use_enhancer": False,  # Disable enhancer to save memory
    "still_mode": True,  # Enable for less computation
}

# Audio processing optimization
AUDIO_SETTINGS = {
    "sample_rate": 16000,  # Standard rate, good balance
    "chunk_length": 30,  # Process in smaller chunks
    "enable_vad": True,  # Voice activity detection to save processing
}

# ============================================================================
# M1 - SPECIFIC PYTORCH OPTIMIZATIONS
# ============================================================================

# PyTorch optimizations for M1
PYTORCH_OPTIMIZATIONS = {
    "torch.backends.mps.enabled": True,
    "torch.backends.mps.allow_fallback": True,  # Allow CPU fallback if needed
    "torch.set_num_threads": 4,  # Optimize for M1's 4 performance cores
    "torch.set_num_interop_threads": 2,
}

# Apply PyTorch optimizations


def apply_pytorch_optimizations():
    """Apply M1 - specific PyTorch optimizations"""
    print("🔧 Applying PyTorch optimizations for M1...")

    if DEVICE == "mps":
        # Enable MPS optimizations
        os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
        os.environ["PYTORCH_MPS_HIGH_WATERMARK_RATIO"] = "0.0"

        # Set thread counts for M1's architecture
        try:
            torch.set_num_threads(4)  # M1 has 4 performance cores
            print("✅ Set PyTorch threads to 4")
        except RuntimeError as e:
            print(f"⚠️ PyTorch threads already configured: {e}")

        try:
            torch.set_num_interop_threads(2)
            print("✅ Set PyTorch interop threads to 2")
        except RuntimeError as e:
            print(f"⚠️ PyTorch interop threads already configured: {e}")

        print("✅ Applied M1 - specific PyTorch optimizations")


# ============================================================================
# MEMORY MANAGEMENT
# ============================================================================


def optimize_memory():
    """Optimize memory usage for M1 MacBook Air"""

    import gc

    # Clear Python garbage collection
    gc.collect()

    # Clear MPS cache if available
    if DEVICE == "mps" and hasattr(torch.mps, "empty_cache"):
        torch.mps.empty_cache()
        print("✅ Cleared MPS memory cache")

    # Set memory growth for better management
    if DEVICE == "mps":
        # Prevent memory fragmentation
        os.environ["PYTORCH_MPS_PREFER_METAL"] = "1"


# ============================================================================
# MODEL LOADING OPTIMIZATION
# ============================================================================

MODEL_LOADING = {
    "lazy_loading": True,  # Load models only when needed
    "model_cache_size": 2,  # Keep max 2 models in memory
    "auto_unload": True,  # Automatically unload unused models
    "preload_essential": ["tts", "asr"],  # Only preload essential models
}

# ============================================================================
# GRADIO UI OPTIMIZATION
# ============================================================================

UI_SETTINGS = {
    "queue_max_size": 2,  # Small queue for memory efficiency
    "default_concurrency_limit": 1,  # Single concurrent user
    "enable_queue": True,
    "show_error": True,
    "debug": False,  # Disable debug for better performance
}

# ============================================================================
# NETWORK AND API SETTINGS
# ============================================================================

# Server configuration optimized for local M1 usage
SERVER_CONFIG = {
    "host": "127.0.0.1",  # Local only for better performance
    "port": 6006,
    "workers": 1,  # Single worker to prevent memory issues
    "timeout": 300,  # 5 minute timeout
    "max_request_size": 50 * 1024 * 1024,  # 50MB max request
}

# ============================================================================
# FEATURE FLAGS FOR M1 OPTIMIZATION
# ============================================================================

FEATURE_FLAGS = {
    "enable_musetalk": False,  # Disable heavy features
    "enable_voice_cloning": False,  # Disable if not needed
    "enable_real_time": False,  # Disable real - time features
    "enable_batch_processing": False,  # Disable batch processing
    "enable_gpu_acceleration": True,  # Use MPS acceleration
    "enable_memory_monitoring": True,  # Monitor memory usage
}

# ============================================================================
# INITIALIZATION FUNCTION
# ============================================================================


def initialize_m1_optimizations():
    """Initialize all M1 - specific optimizations"""
    print("🚀 Initializing M1 MacBook Air optimizations...")

    # Apply PyTorch optimizations first (before any PyTorch operations)
    try:
        apply_pytorch_optimizations()
    except Exception as e:
        print(f"⚠️ PyTorch optimization warning: {e}")

    # Optimize memory
    optimize_memory()

    # Set environment variables
    os.environ["OMP_NUM_THREADS"] = "4"
    os.environ["MKL_NUM_THREADS"] = "4"
    os.environ["NUMEXPR_NUM_THREADS"] = "4"

    # Disable some features that may cause issues on M1
    os.environ["TOKENIZERS_PARALLELISM"] = "false"

    print("✅ M1 optimizations applied successfully!")
    print(f"📱 Device: {DEVICE}")
    print(f"💾 Memory optimization: {MEMORY_OPTIMIZATION['max_memory_fraction']*100}% max usage")
    print(f"🎬 Video settings: {VIDEO_SETTINGS['fps']}fps, {VIDEO_SETTINGS['resolution']}p")
    print(f"🔊 Audio settings: {AUDIO_SETTINGS['sample_rate']}Hz sample rate")


# ============================================================================
# MONITORING AND DIAGNOSTICS
# ============================================================================


def get_system_info():
    """Get system information for diagnostics"""

    import psutil

    info = {
        "platform": platform.system(),
        "machine": platform.machine(),
        "python_version": platform.python_version(),
        "pytorch_version": torch.__version__,
        "mps_available": (
            torch.backends.mps.is_available() if hasattr(torch.backends, "mps") else False
        ),
        "total_memory_gb": round(psutil.virtual_memory().total / (1024**3), 2),
        "available_memory_gb": round(psutil.virtual_memory().available / (1024**3), 2),
        "cpu_count": psutil.cpu_count(),
    }

    return info


def print_system_info():
    """Print system information"""
    info = get_system_info()
    print("\\n" + "=" * 50)
    print("SYSTEM INFORMATION")
    print("=" * 50)
    for key, value in info.items():
        print(f"{key}: {value}")
    print("=" * 50 + "\\n")


# Auto - initialize when imported
if __name__ == "__main__" or os.getenv("AUTO_INIT_M1", "true").lower() == "true":
    initialize_m1_optimizations()
    print_system_info()
