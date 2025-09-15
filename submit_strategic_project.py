#!/usr/bin/env python3
"""
Submit Strategic Project Request to Task Queue

This script submits the 'Right Perspective Q4 2025' content strategy request
to the task queue system for processing by the PlannerAgent.
"""

import sys
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

try:
    from utils.logger import get_logger

    from backend.task_queue_manager import TaskPriority, TaskQueueManager, TaskType

except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)


def main():
    """Submit the strategic project request to the task queue."""
    logger = get_logger(__name__)

    # Initialize task queue manager
    task_manager = TaskQueueManager()

    # Define the strategic project task
    task_payload = {
        "task_id": "project_q4_2025_launch",
        "target_agent": "PlannerAgent",
        "task_type": "STRATEGIC_PROJECT_EXECUTION",
        "priority": "HIGHEST",
        "payload": {
            "goal": "Initiate the 'Right Perspective Q4 2025' content strategy.",
            "instructions": [
                "1. Task the ResearchAgent to identify the top 5 trending political topics from the last 72 hours based on its RSS feeds.",
                "2. From those topics, task the ContentAgent to generate three distinct video script outlines.",
                "3. Task the AuditorAgent to review the outlines for compliance with the 'RightPerspectiveFirewall'.",
                "4. Select the highest - scoring outline \"
#     and task the VideoCreator to produce a 2 - minute video.",
                "5. Task the MarketingAgent to schedule the final video for publication on YouTube \"
#     and draft a promotional tweet.",
# BRACKET_SURGEON: disabled
#             ],
# BRACKET_SURGEON: disabled
#         },
        "status": "pending",
# BRACKET_SURGEON: disabled
#     }

    try:
        # Submit task to queue
        task_id = task_manager.add_task(
            task_type=TaskType.WORKFLOW,
            payload=task_payload,
            priority=TaskPriority.URGENT,
            assigned_agent="planner",
            metadata={
                "project_name": "Right Perspective Q4 2025",
                "initiated_by": "strategic_request",
                "timestamp": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#             },
# BRACKET_SURGEON: disabled
#         )

        logger.info(f"Strategic project task submitted successfully with ID: {task_id}")
        print("✅ Strategic project task submitted successfully!")
        print(f"📋 Task ID: {task_id}")
        print("🎯 Project: Right Perspective Q4 2025 Content Strategy")
        print(f"⏰ Submitted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        return task_id

    except Exception as e:
        logger.error(f"Failed to submit strategic project task: {e}")
        print(f"❌ Failed to submit task: {e}")
        return None


if __name__ == "__main__":
    main()