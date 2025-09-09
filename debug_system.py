#!/usr/bin/env python3
"""
System Debug Script for TRAE.AI

This script performs comprehensive system health checks and debugging.
"""

import sys
import os
from pathlib import Path

def main():
    print("=== TRAE.AI System Debug Report ===")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    
    # Test core imports
    print("\n=== Testing Core Imports ===")
    try:
        from backend.secret_store import SecretStore
        print("✓ SecretStore import successful")
    except Exception as e:
        print(f"✗ SecretStore import failed: {e}")
    
    try:
        from backend.task_queue_manager import TaskQueueManager
        print("✓ TaskQueueManager import successful")
    except Exception as e:
        print(f"✗ TaskQueueManager import failed: {e}")
    
    # Test database connectivity
    print("\n=== Testing Database Connectivity ===")
    try:
        tqm = TaskQueueManager()
        tasks = tqm.get_tasks(limit=5)
        print(f"✓ Database connection successful - Found {len(tasks)} tasks")
        
        # Show recent tasks
        if tasks:
            print("\nRecent tasks:")
            for i, task in enumerate(tasks[:3], 1):
                task_id = task.get('id', 'unknown')[:8]
                status = task.get('status', 'unknown')
                task_type = task.get('task_type', 'unknown')
                print(f"  {i}. {task_id}... - {status} - {task_type}")
        
        # Get queue stats
        try:
            stats = tqm.get_queue_stats()
            print(f"\nQueue statistics: {stats}")
        except Exception as e:
            print(f"Queue stats unavailable: {e}")
            
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
    
    # Test file system
    print("\n=== Testing File System ===")
    critical_files = [
        'schema.sql',
        'launch_live.py',
        'app/dashboard.py',
        'backend/secret_store.py',
        'backend/task_queue_manager.py'
    ]
    
    for file_path in critical_files:
        if Path(file_path).exists():
            print(f"✓ {file_path} exists")
        else:
            print(f"✗ {file_path} missing")
    
    # Test data directory
    data_dir = Path('data')
    if data_dir.exists():
        print(f"✓ Data directory exists")
        db_files = list(data_dir.glob('*.db'))
        print(f"  Database files: {[f.name for f in db_files]}")
    else:
        print(f"✗ Data directory missing")
    
    print("\n=== Debug Report Complete ===")

if __name__ == '__main__':
    main()