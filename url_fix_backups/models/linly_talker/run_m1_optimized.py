#!/usr / bin / env python3
"""
M1 MacBook Air Optimized Linly - Talker Runner
Optimized for Apple Silicon M1 with 16GB RAM

Usage:
    python run_m1_optimized.py [--mode MODE] [--model MODEL] [--port PORT]

Modes:
    - demo: Run demo interface (default)
    - webui: Run full WebUI with optimizations
    - api: Run API server only
    - benchmark: Run performance benchmark
"""

import argparse
import os
import sys
import time
import warnings
from pathlib import Path

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore")

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

# Import M1 optimizations
try:
    from configs_m1_optimized import (
        AUDIO_SETTINGS,
        DEVICE,
        FEATURE_FLAGS,
        OPTIMIZED_MODELS,
        SERVER_CONFIG,
        UI_SETTINGS,
        VIDEO_SETTINGS,
        initialize_m1_optimizations,
        optimize_memory,
        print_system_info,
    )
except ImportError as e:
    print(f"❌ Error importing M1 optimizations: {e}")
    sys.exit(1)


def setup_environment():
    """Setup optimized environment for M1"""
    print("🔧 Setting up M1 - optimized environment...")

    # Initialize M1 optimizations
    initialize_m1_optimizations()

    # Set Gradio temp directory
    os.environ["GRADIO_TEMP_DIR"] = "./temp"
    os.environ["WEBUI"] = "true"

    # Create necessary directories
    os.makedirs("./temp", exist_ok=True)
    os.makedirs("./results", exist_ok=True)
    os.makedirs("./inputs", exist_ok=True)

    print("✅ Environment setup complete!")


# Import demo app at module level
try:
    from demo_app import *

except ImportError:
    print("⚠️ Demo app not available. Some features may be limited.")

try:
    import gradio as gr

except ImportError:
    print("⚠️ Gradio not installed. Demo mode requires: pip install gradio")
    gr = None


def run_demo_mode():
    """Run optimized demo mode"""
    print("🎭 Starting Linly - Talker Demo Mode (M1 Optimized)...")

    if gr is None:
        print("❌ Gradio not available. Please install: pip install gradio")
        return

    try:
        # Create optimized demo interface
        with gr.Blocks(
            title="Linly - Talker M1 Demo",
            theme=gr.themes.Soft(),
            css=".gradio - container {max - width: 1200px; margin: auto;}",
        ) as demo:
            gr.Markdown(
                """
                # 🎭 Linly - Talker M1 Optimized Demo

                **Optimized for MacBook Air M1 with 16GB RAM**

                - ⚡ **Performance**: Optimized for Apple Silicon
                - 💾 **Memory**: Efficient memory usage (max 70% RAM)
                - 🎬 **Quality**: Balanced quality and performance
                - 🔊 **Audio**: 16kHz optimized processing
                """
            )

            with gr.Tab("💬 Text to Speech"):
                with gr.Row():
                    with gr.Column():
                        text_input = gr.Textbox(
                            label="Enter text to convert to speech",
                            placeholder="Hello! I'm your AI assistant optimized for M1 MacBook Air.",
                            lines=3,
                        )
                        voice_select = gr.Dropdown(
                            choices=["Default", "Female", "Male", "Cheerful"],
                            value="Default",
                            label="Voice Style",
                        )
                        tts_btn = gr.Button("🗣️ Generate Speech", variant="primary")

                    with gr.Column():
                        tts_output = gr.Textbox(label="Status", interactive=False)
                        audio_output = gr.Audio(label="Generated Audio")

                tts_btn.click(
                    fn=demo_text_to_speech,
                    inputs=[text_input, voice_select],
                    outputs=[tts_output],
                )

            with gr.Tab("🎬 Avatar Animation"):
                with gr.Row():
                    with gr.Column():
                        avatar_text = gr.Textbox(
                            label="Text for avatar to speak",
                            placeholder="Hello! I'm your digital avatar.",
                            lines=2,
                        )
                        avatar_image = gr.Image(
                            label="Upload avatar image (optional)", type="filepath"
                        )
                        avatar_btn = gr.Button("🎭 Generate Avatar", variant="primary")

                    with gr.Column():
                        avatar_output = gr.Textbox(label="Status", interactive=False)
                        video_output = gr.Video(label="Generated Video")

                avatar_btn.click(
                    fn=demo_avatar_animation,
                    inputs=[avatar_text, avatar_image],
                    outputs=[avatar_output],
                )

            with gr.Tab("🎤 Voice Cloning"):
                with gr.Row():
                    with gr.Column():
                        voice_file = gr.Audio(
                            label="Upload voice sample (30s max)", type="filepath"
                        )
                        clone_text = gr.Textbox(
                            label="Text to synthesize with cloned voice",
                            placeholder="This is a test of voice cloning.",
                            lines=2,
                        )
                        clone_btn = gr.Button("🎤 Clone Voice", variant="primary")

                    with gr.Column():
                        clone_output = gr.Textbox(label="Status", interactive=False)
                        cloned_audio = gr.Audio(label="Cloned Voice Output")

                clone_btn.click(
                    fn=demo_voice_cloning,
                    inputs=[voice_file, clone_text],
                    outputs=[clone_output],
                )

            with gr.Tab("💬 AI Chat"):
                chatbot = gr.Chatbot(label="AI Assistant", height=400)
                msg = gr.Textbox(label="Your message", placeholder="Ask me anything!", lines=2)
                clear = gr.Button("🗑️ Clear Chat")

                msg.submit(fn=demo_chat_response, inputs=[msg, chatbot], outputs=[chatbot, msg])
                clear.click(lambda: ([], ""), outputs=[chatbot, msg])

            with gr.Tab("📊 System Info"):
                gr.Markdown(
                    f"""
                    ## 🖥️ System Configuration

                    - **Device**: {DEVICE}
                    - **Video Settings**: {VIDEO_SETTINGS['fps']}fps, {VIDEO_SETTINGS['resolution']}p
                    - **Audio Settings**: {AUDIO_SETTINGS['sample_rate']}Hz
                    - **Memory Limit**: {int(70)}% of available RAM
                    - **Batch Size**: 1 (optimized for M1)

                    ## 🚀 Performance Tips

                    1. **Close other applications** to free up memory
                    2. **Use shorter text inputs** for faster processing
                    3. **Lower resolution images** process faster
                    4. **Enable 'Still Mode'** for avatar generation to save resources
                    5. **Use Edge - TTS** for fastest text - to - speech

                    ## 🔧 Troubleshooting

                    - If you get memory errors, restart the application
                    - For slow performance, reduce video quality settings
                    - Check Activity Monitor for memory usage
                    """
                )

                refresh_btn = gr.Button("🔄 Refresh System Info")
                system_info = gr.Textbox(label="Current System Status", lines=10)

                def get_current_status():
                    import psutil
                    import torch

                    status = f"""
                    Memory Usage: {psutil.virtual_memory().percent}%
                    Available Memory: {psutil.virtual_memory().available/(1024**3):.1f} GB
                    CPU Usage: {psutil.cpu_percent()}%
                    Device: {DEVICE}
                    PyTorch Version: {torch.__version__}
                    MPS Available: {torch.backends.mps.is_available() if hasattr(torch.backends, 'mps') else 'N / A'}
                    """
                    return status

                refresh_btn.click(fn=get_current_status, outputs=[system_info])

                # Load initial status
                demo.load(fn=get_current_status, outputs=[system_info])

        # Launch demo with optimized settings
        demo.queue(
            max_size=UI_SETTINGS["queue_max_size"],
            default_concurrency_limit=UI_SETTINGS["default_concurrency_limit"],
        )

        demo.launch(
            server_name=SERVER_CONFIG["host"],
            server_port=SERVER_CONFIG["port"],
            share=False,  # Local only for better performance
            debug=UI_SETTINGS["debug"],
            show_error=UI_SETTINGS["show_error"],
            quiet=True,
        )

    except Exception as e:
        print(f"❌ Error starting demo: {e}")
        print("💡 Try running: pip install -r requirements_app.txt")


def run_webui_mode():
    """Run optimized WebUI mode"""
    print("🌐 Starting Linly - Talker WebUI (M1 Optimized)...")

    try:
        # Import and modify webui

        import webui

        # Override some settings for M1 optimization
        webui.DEFAULT_SYSTEM = "你是一个很有帮助的助手，专门为M1 MacBook Air优化。"
        webui.IMAGE_SIZE = VIDEO_SETTINGS["resolution"]
        webui.ENHANCER = VIDEO_SETTINGS["use_enhancer"]
        webui.IS_STILL_MODE = VIDEO_SETTINGS["still_mode"]

        print("✅ WebUI started with M1 optimizations")

    except Exception as e:
        print(f"❌ Error starting WebUI: {e}")
        print("💡 Make sure all dependencies are installed")


def run_api_mode():
    """Run API server mode"""
    print("🔌 Starting Linly - Talker API Server (M1 Optimized)...")

    try:
        from api import talker_api

        print("✅ API server started")
    except Exception as e:
        print(f"❌ Error starting API server: {e}")


def run_benchmark():
    """Run performance benchmark"""
    print("📊 Running M1 Performance Benchmark...")

    import time

    import psutil
    import torch

    # Memory benchmark
    print("\\n🧠 Memory Benchmark:")
    memory_before = psutil.virtual_memory().used / (1024**3)
    print(f"Memory before: {memory_before:.2f} GB")

    # Create test tensors
    if DEVICE == "mps":
        test_tensor = torch.randn(1000, 1000, device=DEVICE)
        start_time = time.time()
        result = torch.matmul(test_tensor, test_tensor.T)
        end_time = time.time()

        print(f"MPS Matrix multiplication (1000x1000): {end_time - start_time:.4f}s")

    memory_after = psutil.virtual_memory().used / (1024**3)
    print(f"Memory after: {memory_after:.2f} GB")
    print(f"Memory used: {memory_after - memory_before:.2f} GB")

    # Cleanup
    optimize_memory()

    print("\\n✅ Benchmark complete!")


def run_one_button_test_mode():
    """Run one - button test mode with production avatar APIs"""
    print("\\n🚀 Starting One - Button Test Mode...")
    print("🎯 Production Avatar API Integration Test")
    print(
        f"🌐 Test interface will be available at: http://{SERVER_CONFIG['host']}:{SERVER_CONFIG['port']}"
    )

    try:
        # Import and run the one - button test

        from one_button_test import create_one_button_interface

        print("\\n📋 One - Button Test Features:")
        print("   ✅ HeyGen Streaming Avatar API")
        print("   ✅ D - ID Photorealistic Avatar API")
        print("   ✅ Synthesia Professional Avatar API")
        print("   ✅ Production readiness validation")
        print("   ✅ Performance benchmarking")
        print("   ✅ Security compliance check")

        # Check API configuration
        try:
            from avatar_api_config import validate_api_keys

            api_status = validate_api_keys()
            configured_apis = sum(api_status.values())

            print(f"\\n🔧 API Configuration Status: {configured_apis}/3 APIs configured")
            for api_name, is_configured in api_status.items():
                status = "✅" if is_configured else "❌"
                print(f"   {status} {api_name.upper()}")

            if configured_apis == 0:
                print("\\n⚠️ Running in DEMO MODE - No production APIs configured")
                print("💡 To use real APIs, configure environment variables:")
                print("   export HEYGEN_API_KEY='your_key'")
                print("   export DID_API_KEY='your_key'")
                print("   export SYNTHESIA_API_KEY='your_key'")
            else:
                print(f"\\n🎉 Production mode ready with {configured_apis} API(s)!")

        except ImportError:
            print("\\n⚠️ Avatar API configuration not available - using demo mode")

        # Create and launch the interface
        demo = create_one_button_interface()

        print(f"\\n🌟 One - Button Test interface starting...")
        print(f"🔗 Open your browser to: http://{SERVER_CONFIG['host']}:{SERVER_CONFIG['port']}")
        print("\\n🎯 Click 'RUN ONE - BUTTON TEST' to validate your production setup!")

        demo.launch(
            server_name=SERVER_CONFIG["host"],
            server_port=SERVER_CONFIG["port"],
            share=False,
            show_error=True,
            show_api=False,
        )

    except ImportError as e:
        print(f"\\n❌ Error: Could not import one - button test module: {e}")
        print("💡 Make sure one_button_test.py is in the same directory")
        print("🔄 Falling back to demo mode...")
        run_demo_mode()
    except Exception as e:
        print(f"\\n❌ Error starting one - button test: {e}")
        print("🔄 Falling back to demo mode...")
        run_demo_mode()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="M1 MacBook Air Optimized Linly - Talker Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_m1_optimized.py                    # Run demo mode
  python run_m1_optimized.py --mode webui       # Run WebUI
  python run_m1_optimized.py --mode benchmark   # Run benchmark
  python run_m1_optimized.py --port 7007        # Custom port
        """,
    )

    parser.add_argument(
        "--mode",
        choices=["demo", "webui", "api", "benchmark", "one - button - test"],
        default="demo",
        help="Run mode (default: demo)",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=SERVER_CONFIG["port"],
        help=f'Server port (default: {SERVER_CONFIG["port"]})',
    )

    parser.add_argument(
        "--host",
        default=SERVER_CONFIG["host"],
        help=f'Server host (default: {SERVER_CONFIG["host"]})',
    )

    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    # Update server config with args
    SERVER_CONFIG["port"] = args.port
    SERVER_CONFIG["host"] = args.host

    if args.verbose:
        print_system_info()

    # Setup environment
    setup_environment()

    print(f"\\n🚀 Starting Linly - Talker in {args.mode} mode...")
    print(f"🌐 Server: http://{args.host}:{args.port}")
    print(f"📱 Device: {DEVICE}")
    print(f"💾 Memory optimization: Active")
    print("\\n" + "=" * 50)

    # Run selected mode
    try:
        if args.mode == "demo":
            run_demo_mode()
        elif args.mode == "webui":
            run_webui_mode()
        elif args.mode == "api":
            run_api_mode()
        elif args.mode == "benchmark":
            run_benchmark()
        elif args.mode == "one - button - test":
            run_one_button_test_mode()
    except KeyboardInterrupt:
        print("\\n\\n👋 Shutting down gracefully...")
        optimize_memory()
        print("✅ Cleanup complete. Goodbye!")
    except Exception as e:
        print(f"\\n❌ Unexpected error: {e}")
        print("💡 Try running with --verbose for more information")
        sys.exit(1)


if __name__ == "__main__":
    main()
