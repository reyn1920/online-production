#!/usr / bin / env python3
"""
Find the specific strategic project task by ID.
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.task_queue_manager import TaskQueueManager


def main():
    print("🔍 Looking for strategic project task...")

    # The task ID from when we submitted it
    strategic_task_id = "93f9a950 - 9cc7 - 4ee7 - 86af - 4fe91cc12be0"

    try:
        # Initialize task queue manager
        task_manager = TaskQueueManager()

        # Try to get the specific task
        print(f"\n🎯 Searching for task ID: {strategic_task_id}")
        task = task_manager.get_task(strategic_task_id)

        if task:
            print(f"  ✅ Found the strategic project task!")
            print(f"     Task ID: {task.get('id')}")
            print(f"     Status: {task.get('status')}")
            print(f"     Task Type: {task.get('task_type')}")
            print(f"     Priority: {task.get('priority')}")
            print(f"     Target Agent: {task.get('target_agent')}")
            print(f"     Created: {task.get('created_at')}")
            if task.get("started_at"):
                print(f"     Started: {task.get('started_at')}")
            if task.get("completed_at"):
                print(f"     Completed: {task.get('completed_at')}")
            if task.get("assigned_agent"):
                print(f"     Assigned Agent: {task.get('assigned_agent')}")
            if task.get("error_message"):
                print(f"     Error: {task.get('error_message')}")

            # Show the payload
            if "payload" in task and task["payload"]:
                print(f"\n📋 Task Payload:")
                payload = task["payload"]
                if "goal" in payload:
                    print(f"     Goal: {payload['goal']}")
                if "instructions" in payload:
                    print(f"     Instructions:")
                    for i, instruction in enumerate(payload["instructions"], 1):
                        print(f"       {i}. {instruction}")

            # Show result if completed
            if task.get("result"):
                print(f"\n📊 Task Result:")
                print(f"     {task['result']}")

        else:
            print(f"  ❌ Task {strategic_task_id} not found in database.")

            # Let's also search for any tasks with 'Right Perspective' in the payload
            print(f"\n🔍 Searching for tasks containing 'Right Perspective'...")
            all_tasks = task_manager.get_tasks(limit = 200)  # Get more tasks
            found_tasks = []

            for t in all_tasks:
                if t.get("payload") and isinstance(t["payload"], dict):
                    goal = t["payload"].get("goal", "")
                    if "Right Perspective" in goal or "Q4 2025" in goal:
                        found_tasks.append(t)
                elif t.get("task_type") == "STRATEGIC_PROJECT_EXECUTION":
                    found_tasks.append(t)

            if found_tasks:
                print(f"  ✅ Found {len(found_tasks)} related tasks:")
                for t in found_tasks:
                    print(
                        f"     • {t.get('id')} - {t.get('status')} - {t.get('task_type')}"
                    )
            else:
                print(f"  ❌ No related tasks found.")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
