#!/usr/bin/env python3
"""
RouteLL Integration Setup Script
Initializes and tests the complete RouteLL integration
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def print_banner():
    """Print setup banner"""
    print("\n" + "=" * 60)
    print("🚀 RouteLL API Integration Setup")
    print("   Intelligent LLM Routing with Credit Optimization")
    print("=" * 60)


def check_dependencies():
    """Check if required dependencies are available"""
    print("\n📦 Checking dependencies...")

    required_modules = ["requests", "aiohttp", "flask", "sqlite3"]

    missing_modules = []

    for module in required_modules:
        try:
            __import__(module)
            print(f"   ✅ {module}")
        except ImportError:
            print(f"   ❌ {module} (missing)")
            missing_modules.append(module)

    if missing_modules:
        print(f"\n⚠️ Missing dependencies: {', '.join(missing_modules)}")
        print("Install with: pip install " + " ".join(missing_modules))
        return False

    print("   ✅ All dependencies available")
    return True


def setup_environment():
    """Setup environment variables"""
    print("\n🔧 Setting up environment...")

    api_key = "s2_f0b00d6897a0431f8367a7fc859b697a"

    # Set environment variable for current session
    os.environ["ROUTELLM_API_KEY"] = api_key
    print(f"   ✅ ROUTELLM_API_KEY set for current session")

    # Check if .env file exists and update it
    env_file = Path(".env")
    env_content = ""

    if env_file.exists():
        with open(env_file, "r") as f:
            env_content = f.read()

    if "ROUTELLM_API_KEY" not in env_content:
        with open(env_file, "a") as f:
            f.write(f"\n# RouteLL API Configuration\n")
            f.write(f"ROUTELLM_API_KEY={api_key}\n")
        print(f"   ✅ Added ROUTELLM_API_KEY to .env file")
    else:
        print(f"   ✅ ROUTELLM_API_KEY already in .env file")

    return True


def verify_file_structure():
    """Verify all integration files are in place"""
    print("\n📁 Verifying file structure...")

    required_files = [
        "config/routellm_config.json",
        "integrations/routellm_client.py",
        "utils/rate_limiter.py",
        "routing/model_router.py",
        "monitoring/routellm_monitor.py",
        "dashboard/routellm_dashboard.py",
        "examples/routellm_integration_example.py",
        "docs/RouteLL_Integration_Guide.md",
    ]

    missing_files = []

    for file_path in required_files:
        if Path(file_path).exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} (missing)")
            missing_files.append(file_path)

    if missing_files:
        print(f"\n⚠️ Missing files: {len(missing_files)}")
        return False

    print("   ✅ All integration files present")
    return True


def create_directories():
    """Create necessary directories"""
    print("\n📂 Creating directories...")

    directories = ["logs", "data", "backups"]

    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"   ✅ Created {directory}/")
        else:
            print(f"   ✅ {directory}/ already exists")

    return True


def test_integration():
    """Test the RouteLL integration"""
    print("\n🧪 Testing RouteLL integration...")

    try:
        # Import and test basic client
        from integrations.routellm_client import RouteLL_Client

        client = RouteLL_Client()
        print("   ✅ RouteLL client imported successfully")

        # Test API connectivity
        print("   🔍 Testing API connectivity...")
        try:
            status = client.get_status()
            api_health = status.get("api_health", {})

            if api_health.get("status") == "healthy":
                print(f"   ✅ API connection successful")
            else:
                print(
                    f"   ⚠️ API connection issue: {api_health.get('reason', 'unknown')}"
                )
        except Exception as e:
            print(f"   ⚠️ API connection failed: {e}")

        # Test credit status
        print("   💳 Checking credit status...")
        try:
            credit_status = client.check_credits()
            print(f"   ✅ Credits remaining: {credit_status.remaining_credits}")
            print(f"   📊 Daily usage: {credit_status.daily_usage}")
        except Exception as e:
            print(f"   ⚠️ Credit check failed: {e}")

        # Test model router
        print("   🎯 Testing model router...")
        from routing.model_router import ModelRouter

        router = ModelRouter()
        print(f"   ✅ Model router initialized with {len(router.models)} models")

        # Test routing decision
        messages = [{"role": "user", "content": "What is machine learning?"}]
        routing_result = router.route_request(messages)

        selected_model = routing_result["routing_decision"]["selected_model"]
        task_type = routing_result["routing_decision"]["task_type"]
        print(f"   ✅ Routing test: {selected_model} for {task_type}")

        # Test rate limiter
        print("   ⚡ Testing rate limiter...")
        from utils.rate_limiter import RateLimiter

        rate_limiter = RateLimiter()
        can_request = rate_limiter.can_make_request()
        print(f"   ✅ Rate limiter: {'Ready' if can_request else 'Limited'}")

        # Test integrated client
        print("   🔗 Testing integrated client...")
        from examples.routellm_integration_example import RouteLL_IntegratedClient

        integrated_client = RouteLL_IntegratedClient()
        print("   ✅ Integrated client initialized successfully")

        # Make a test request
        print("   📤 Making test request...")
        test_messages = [{"role": "user", "content": "Hello! This is a test message."}]

        response = client.chat_completion(test_messages)

        if response.success:
            print(f"   ✅ Test request successful")
            if response.data:
                data_str = str(response.data)[:100]
                print(f"   📝 Response preview: {data_str}...")
            print(f"   🎯 Model used: {response.model_used}")
            print(f"   ⏱️ Response time: {response.response_time_ms}ms")

            if hasattr(response, "routing_info"):
                print(f"   🧠 Task classified as: {response.routing_info['task_type']}")
        else:
            print(f"   ❌ Test request failed: {response.error}")
            return False

        # Get session analytics
        analytics = integrated_client.get_session_analytics()
        print(
            f"   📊 Session stats: {analytics['total_requests']} requests, {analytics['success_rate']:.1f}% success rate"
        )

        return True

    except Exception as e:
        print(f"   ❌ Integration test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def print_next_steps():
    """Print next steps for the user"""
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next Steps:")
    print("\n1. 📖 Read the documentation:")
    print("   open docs/RouteLL_Integration_Guide.md")

    print("\n2. 🧪 Run the example:")
    print("   python examples/routellm_integration_example.py")

    print("\n3. 📊 Start the dashboard:")
    print("   python dashboard/routellm_dashboard.py")
    print("   Then open: http://localhost:5000")

    print("\n4. 🔗 Integrate into your code:")
    print(
        "   from examples.routellm_integration_example import RouteLL_IntegratedClient"
    )
    print("   client = RouteLL_IntegratedClient()")
    print("   response = await client.chat_completion(messages)")

    print("\n5. 📈 Monitor usage:")
    print("   - Check dashboard for real-time metrics")
    print("   - Review logs/ directory for detailed logs")
    print("   - Use analytics methods for programmatic monitoring")

    print("\n💡 Key Features Available:")
    print("   ✅ Intelligent model routing based on task type")
    print("   ✅ Automatic cost optimization")
    print("   ✅ Real-time credit monitoring")
    print("   ✅ Rate limiting and usage analytics")
    print("   ✅ Web dashboard for monitoring")
    print("   ✅ Comprehensive error handling")

    print("\n🔑 Your API Key: s2_f0b00d6897a0431f8367a7fc859b697a")
    print("   (Already configured in environment)")

    print("\n📚 Resources:")
    print("   - Integration Guide: docs/RouteLL_Integration_Guide.md")
    print("   - RouteLL API Docs: https://routellm.abacus.ai/docs")
    print("   - Example Code: examples/routellm_integration_example.py")


def main():
    """Main setup function"""
    print_banner()

    # Step 1: Check dependencies
    if not check_dependencies():
        print("\n❌ Setup failed: Missing dependencies")
        return False

    # Step 2: Setup environment
    if not setup_environment():
        print("\n❌ Setup failed: Environment setup failed")
        return False

    # Step 3: Verify file structure
    if not verify_file_structure():
        print("\n❌ Setup failed: Missing integration files")
        return False

    # Step 4: Create directories
    if not create_directories():
        print("\n❌ Setup failed: Directory creation failed")
        return False

    # Step 5: Test integration
    if not test_integration():
        print("\n❌ Setup failed: Integration test failed")
        return False

    # Step 6: Print next steps
    print_next_steps()

    return True


if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n✅ RouteLL integration setup completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Setup failed. Please check the errors above.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error during setup: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
