#!/usr/bin/env python3
"""
Test script for video creation workflow
"""

import asyncio
import os
import pytest
from backend.agents.specialized_agents import ContentAgent

@pytest.mark.asyncio
async def test_video_creation():
    """Test the complete video creation workflow"""
    print("Starting video creation workflow test...")
    
    # Initialize ContentAgent
    agent = ContentAgent()
    print(f"ContentAgent initialized - Tools available: {agent.tools_available}")
    
    # Test basic video script creation
    print("\n=== Testing Video Script Creation ===")
    script_task = {
        'task_type': 'create_content',
        'content_type': 'video_script',
        'topic': 'AI Technology Revolution',
        'duration': 120,
        'target_audience': 'tech enthusiasts'
    }
    
    try:
        script_result = await agent.process_task(script_task)
        print("Video script creation successful:")
        print(f"Title: {script_result.get('title', 'N/A')}")
        print(f"Content length: {len(str(script_result.get('content', '')))} characters")
        print(f"Status: {script_result.get('status', 'unknown')}")
    except Exception as e:
        print(f"Video script creation failed: {e}")
        return False
    
    # Test advanced video script with VidScriptPro (if available)
    if agent.tools_available:
        print("\n=== Testing VidScriptPro Advanced Script ===")
        advanced_script_task = {
            'task_type': 'create_content',
            'content_type': 'video_script_pro',
            'topic': 'Future of AI in Creative Industries',
            'genre': 'EDUCATIONAL',
            'duration': 300,
            'target_audience': 'creative professionals',
            'tone': 'professional'
        }
        
        try:
            advanced_result = await agent.process_task(advanced_script_task)
            print("Advanced video script creation successful:")
            print(f"Title: {advanced_result.get('title', 'N/A')}")
            print(f"Genre: {advanced_result.get('genre', 'N/A')}")
            print(f"Estimated duration: {advanced_result.get('estimated_duration', 'N/A')} seconds")
            print(f"Word count: {advanced_result.get('word_count', 'N/A')}")
        except Exception as e:
            print(f"Advanced video script creation failed: {e}")
    
    # Test content creation capabilities
    print("\n=== Testing Content Creation Capabilities ===")
    print(f"Supported content types: {list(agent.supported_types.keys())}")
    print(f"Active jobs: {len(agent.get_active_jobs())}")
    
    print("\n=== Video Creation Workflow Test Complete ===")
    return True

if __name__ == "__main__":
    # Set environment variable if not already set
    if not os.getenv('TRAE_MASTER_KEY'):
        os.environ['TRAE_MASTER_KEY'] = 'TRAE_AI_MASTER_2024'
    
    # Run the test
    success = asyncio.run(test_video_creation())
    
    if success:
        print("\n✅ Video creation workflow test completed successfully!")
    else:
        print("\n❌ Video creation workflow test failed!")
        exit(1)