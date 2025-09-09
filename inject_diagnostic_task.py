#!/usr/bin/env python3
"""
Diagnostic Task Injection Script for TRAE.AI System

This script injects a diagnostic task into the TaskQueueManager to command
the ProgressiveSelfRepairAgent to generate a comprehensive diagnostic report.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.task_queue_manager import TaskQueueManager, TaskPriority
import json

def inject_diagnostic_task():
    """
    Inject the diagnostic task into the TRAE.AI task queue system.
    """
    
    # Initialize TaskQueueManager
    tqm = TaskQueueManager()
    
    # Define the diagnostic task as specified by the user
    diagnostic_task = {
        "task_id": "diagnostic_report_001",
        "target_agent": "ProgressiveSelfRepairAgent",
        "task_type": "GENERATE_DIAGNOSTIC_REPORT",
        "priority": "HIGHEST",
        "payload": {
            "description": "The current self-repair and deployment cycle has failed. Analyze the entire process you have undertaken so far. Generate a comprehensive diagnostic report detailing your analysis, the point of failure, and your current hypothesis. The output of this task should be a structured report.",
            "report_format": {
                "sections": [
                    {
                        "section_name": "Initial Goal",
                        "description": "Summarize the primary objective you were trying to achieve (e.g., 'Fix all startup errors and prepare for live deployment')."
                    },
                    {
                        "section_name": "Analysis Log",
                        "description": "Provide a step-by-step log of the actions you took. Example: 1. Parsed error logs. 2. Identified Abstract Class error in orchestrator. 3. Loaded 'trae_ai/agent/content_agent.py' for analysis. 4. Attempted to generate a concrete class implementation..."
                    },
                    {
                        "section_name": "Point of Failure",
                        "description": "Describe the EXACT operation that failed and the error it produced. Be specific. Example: 'Failed during step 4. The code generation model produced a class with a syntax error, causing the validation check to fail.'"
                    },
                    {
                        "section_name": "Current Hypothesis",
                        "description": "Based on the failure, what do you believe is the root cause? Example: 'The abstract methods in the base agents lack sufficient context or docstrings for the AI to generate a meaningful and syntactically correct implementation.'"
                    },
                    {
                        "section_name": "Relevant Code Snippets",
                        "description": "Provide the specific function, class, or code block where the failure occurred. Include the code you were analyzing and any code you attempted to generate."
                    }
                ]
            }
        },
        "status": "pending"
    }
    
    try:
        # Inject the task using TaskQueueManager.add_task method
        task_id = tqm.add_task(
            task_type="GENERATE_DIAGNOSTIC_REPORT",
            payload=diagnostic_task["payload"],
            priority=TaskPriority.URGENT,  # HIGHEST priority maps to URGENT
            assigned_agent="ProgressiveSelfRepairAgent",
            metadata={
                "original_task_id": diagnostic_task["task_id"],
                "target_agent": diagnostic_task["target_agent"],
                "task_type_override": diagnostic_task["task_type"]
            }
        )
        
        print(f"✅ Diagnostic task successfully injected into TaskQueueManager")
        print(f"📋 Task ID: {task_id}")
        print(f"🎯 Target Agent: {diagnostic_task['target_agent']}")
        print(f"⚡ Priority: {diagnostic_task['priority']}")
        print(f"📝 Task Type: {diagnostic_task['task_type']}")
        
        # Print the task details in JSON format for verification
        print("\n📊 Complete Task Details:")
        print(json.dumps(diagnostic_task, indent=2))
        
        return task_id
        
    except Exception as e:
        print(f"❌ Failed to inject diagnostic task: {e}")
        return None

def main():
    """
    Main execution function.
    """
    print("🚀 TRAE.AI Diagnostic Task Injection")
    print("=" * 50)
    print("Injecting diagnostic task to command ProgressiveSelfRepairAgent...")
    print()
    
    task_id = inject_diagnostic_task()
    
    if task_id:
        print("\n✅ Task injection completed successfully!")
        print("\n📋 Next Steps:")
        print("1. The ProgressiveSelfRepairAgent should now execute the GENERATE_DIAGNOSTIC_REPORT task")
        print("2. Monitor the task queue for completion")
        print("3. Retrieve the diagnostic report from the task results")
        print("4. Analyze the report to identify the root cause of failures")
    else:
        print("\n❌ Task injection failed. Please check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()