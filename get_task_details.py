#!/usr/bin/env python3
"""
Get complete details of the strategic project task.
"""

import json
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.task_queue_manager import TaskQueueManager


def main():
    print("🔍 Getting strategic project task details...")

    strategic_task_id = "93f9a950-9cc7-4ee7-86af-4fe91cc12be0"

    try:
        task_manager = TaskQueueManager()
        task = task_manager.get_task(strategic_task_id)

        if task:
            print(f"\n✅ Task Found: {task.get('id')}")
            print(f"Status: {task.get('status')}")
            print(f"Task Type: {task.get('task_type')}")
            print(f"Priority: {task.get('priority')}")
            print(f"Assigned Agent: {task.get('assigned_agent')}")
            print(f"Created: {task.get('created_at')}")

            # Print payload in a readable format
            if "payload" in task and task["payload"]:
                print(f"\n📋 Task Payload:")
                payload = task["payload"]
                print(json.dumps(payload, indent=2))
            else:
                print(f"\n❌ No payload found")

        else:
            print(f"❌ Task not found")

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
