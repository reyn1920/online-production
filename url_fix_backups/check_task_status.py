#!/usr / bin / env python3
""""""
Check the status of the strategic project task in the task queue.
""""""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.agents.base_agents import AgentStatus
from backend.task_queue_manager import TaskQueueManager


def main():
    print("🔍 Checking task queue status...")

    try:
        # Initialize task queue manager
        task_manager = TaskQueueManager()

        # Get all pending tasks
        print("\\n📋 Pending Tasks:")
        pending_tasks = task_manager.get_tasks(status="pending", limit=10)
        if pending_tasks:
            for task in pending_tasks:
                print(f"  • Task ID: {task.get('id', 'N / A')}")
                print(f"    Type: {task.get('task_type', 'N / A')}")
                print(f"    Priority: {task.get('priority', 'N / A')}")
                print(f"    Target Agent: {task.get('target_agent', 'N / A')}")
                print(f"    Created: {task.get('created_at', 'N / A')}")
                if "payload" in task and "goal" in task["payload"]:
                    print(f"    Goal: {task['payload']['goal']}")
                print()
        else:
            print("  No pending tasks found.")

        # Get in - progress tasks
        print("\\n⚡ In - Progress Tasks:")
        in_progress_tasks = task_manager.get_tasks(status="in_progress", limit=10)
        if in_progress_tasks:
            for task in in_progress_tasks:
                print(f"  • Task ID: {task.get('id', 'N / A')}")
                print(f"    Type: {task.get('task_type', 'N / A')}")
                print(f"    Target Agent: {task.get('target_agent', 'N / A')}")
                print(f"    Started: {task.get('started_at', 'N / A')}")
                print()
        else:
            print("  No in - progress tasks found.")

        # Get completed tasks (last 5)
        print("\\n✅ Recent Completed Tasks:")
        completed_tasks = task_manager.get_tasks(status="completed", limit=5)
        if completed_tasks:
            for task in completed_tasks:
                print(f"  • Task ID: {task.get('id', 'N / A')}")
                print(f"    Type: {task.get('task_type', 'N / A')}")
                print(f"    Completed: {task.get('completed_at', 'N / A')}")
                print()
        else:
            print("  No completed tasks found.")

        # Check for our specific strategic project task
        print("\\n🎯 Looking for Strategic Project Task:")
        all_tasks = task_manager.get_tasks(limit=50)
        strategic_task = None
        for task in all_tasks:
            if task.get("task_type") == "STRATEGIC_PROJECT_EXECUTION" or (
                task.get("payload", {}).get("goal", "").find("Right Perspective Q4 2025") != -1
# BRACKET_SURGEON: disabled
#             ):
                strategic_task = task
                break

        if strategic_task:
            print(f"  ✅ Found strategic project task!")
            print(f"     Task ID: {strategic_task.get('id')}")
            print(f"     Status: {strategic_task.get('status')}")
            print(f"     Target Agent: {strategic_task.get('target_agent')}")
            print(f"     Created: {strategic_task.get('created_at')}")
            if strategic_task.get("started_at"):
                print(f"     Started: {strategic_task.get('started_at')}")
            if strategic_task.get("completed_at"):
                print(f"     Completed: {strategic_task.get('completed_at')}")
        else:
            print("  ❌ Strategic project task not found in recent tasks.")

        print("\\n📊 Task Queue Summary:")
        total_tasks = len(all_tasks)
        pending_count = len([t for t in all_tasks if t.get("status") == "pending"])
        in_progress_count = len([t for t in all_tasks if t.get("status") == "in_progress"])
        completed_count = len([t for t in all_tasks if t.get("status") == "completed"])

        print(f"  Total Tasks: {total_tasks}")
        print(f"  Pending: {pending_count}")
        print(f"  In Progress: {in_progress_count}")
        print(f"  Completed: {completed_count}")

    except Exception as e:
        print(f"❌ Error checking task status: {e}")

        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())