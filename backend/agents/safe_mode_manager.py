#!/usr/bin/env python3
"""
Safe Mode Manager - Environment Snapshot and Rollback System

This module implements a safe mode system that creates snapshots of the Python
virtual environment and Git commits before applying any automated repairs.
It provides automatic rollback capabilities if repairs fail.

Author: TRAE.AI System
Version: 1.0.0
"""

import os
import sys
import json
import shutil
import subprocess
import tempfile
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import sqlite3
import tarfile
import hashlib


@dataclass
class EnvironmentSnapshot:
    """Represents a snapshot of the system environment."""
    snapshot_id: str
    timestamp: datetime
    git_commit_hash: str
    venv_backup_path: str
    requirements_hash: str
    system_state: Dict[str, Any]
    description: str
    is_valid: bool = True


@dataclass
class RollbackResult:
    """Result of a rollback operation."""
    success: bool
    snapshot_id: str
    restored_commit: str
    restored_venv: bool
    error_message: Optional[str] = None
    duration: Optional[float] = None


class SafeModeManager:
    """Manages environment snapshots and rollback operations."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.db_path = config.get('db_path', 'right_perspective.db')
        self.snapshots_dir = Path(config.get('snapshots_dir', './snapshots'))
        self.venv_path = Path(config.get('venv_path', './venv'))
        self.project_root = Path(config.get('project_root', '.'))
        self.max_snapshots = config.get('max_snapshots', 10)
        
        self.logger = logging.getLogger(__name__)
        self._init_safe_mode()
    
    def _init_safe_mode(self):
        """Initialize safe mode directories and database tables."""
        try:
            # Create snapshots directory
            self.snapshots_dir.mkdir(exist_ok=True)
            
            # Initialize database table for snapshots
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS environment_snapshots (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        snapshot_id TEXT NOT NULL UNIQUE,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        git_commit_hash TEXT NOT NULL,
                        venv_backup_path TEXT NOT NULL,
                        requirements_hash TEXT NOT NULL,
                        system_state TEXT NOT NULL,
                        description TEXT NOT NULL,
                        is_valid BOOLEAN DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS rollback_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        snapshot_id TEXT NOT NULL,
                        rollback_reason TEXT NOT NULL,
                        success BOOLEAN NOT NULL,
                        restored_commit TEXT,
                        restored_venv BOOLEAN DEFAULT 0,
                        error_message TEXT,
                        duration_seconds REAL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.commit()
                
            self.logger.info("Safe Mode Manager initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Safe Mode Manager: {e}")
            raise
    
    def create_snapshot(self, description: str = "Pre-repair snapshot") -> Optional[EnvironmentSnapshot]:
        """Create a complete environment snapshot before repairs."""
        try:
            snapshot_id = self._generate_snapshot_id()
            timestamp = datetime.now()
            
            self.logger.info(f"Creating environment snapshot: {snapshot_id}")
            
            # 1. Create Git commit for current state
            git_commit = self._create_git_snapshot(snapshot_id, description)
            if not git_commit:
                self.logger.error("Failed to create Git snapshot")
                return None
            
            # 2. Backup virtual environment
            venv_backup_path = self._backup_virtual_environment(snapshot_id)
            if not venv_backup_path:
                self.logger.error("Failed to backup virtual environment")
                return None
            
            # 3. Calculate requirements hash
            requirements_hash = self._calculate_requirements_hash()
            
            # 4. Capture system state
            system_state = self._capture_system_state()
            
            # 5. Create snapshot object
            snapshot = EnvironmentSnapshot(
                snapshot_id=snapshot_id,
                timestamp=timestamp,
                git_commit_hash=git_commit,
                venv_backup_path=venv_backup_path,
                requirements_hash=requirements_hash,
                system_state=system_state,
                description=description
            )
            
            # 6. Store snapshot in database
            self._store_snapshot(snapshot)
            
            # 7. Cleanup old snapshots
            self._cleanup_old_snapshots()
            
            self.logger.info(f"Environment snapshot created successfully: {snapshot_id}")
            return snapshot
            
        except Exception as e:
            self.logger.error(f"Failed to create environment snapshot: {e}")
            return None
    
    def rollback_to_snapshot(self, snapshot_id: str, reason: str = "Automated rollback") -> RollbackResult:
        """Rollback system to a previous snapshot."""
        start_time = datetime.now()
        
        try:
            self.logger.info(f"Starting rollback to snapshot: {snapshot_id}")
            
            # 1. Retrieve snapshot from database
            snapshot = self._get_snapshot(snapshot_id)
            if not snapshot:
                return RollbackResult(
                    success=False,
                    snapshot_id=snapshot_id,
                    restored_commit="",
                    restored_venv=False,
                    error_message="Snapshot not found"
                )
            
            # 2. Rollback Git to snapshot commit
            git_success = self._rollback_git(snapshot.git_commit_hash)
            
            # 3. Restore virtual environment
            venv_success = self._restore_virtual_environment(snapshot.venv_backup_path)
            
            # 4. Verify system integrity
            integrity_check = self._verify_system_integrity(snapshot)
            
            success = git_success and venv_success and integrity_check
            duration = (datetime.now() - start_time).total_seconds()
            
            result = RollbackResult(
                success=success,
                snapshot_id=snapshot_id,
                restored_commit=snapshot.git_commit_hash if git_success else "",
                restored_venv=venv_success,
                duration=duration
            )
            
            if not success:
                result.error_message = "Rollback partially failed - manual intervention required"
            
            # 5. Log rollback attempt
            self._log_rollback_attempt(result, reason)
            
            if success:
                self.logger.info(f"Rollback completed successfully: {snapshot_id}")
            else:
                self.logger.error(f"Rollback failed: {result.error_message}")
            
            return result
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            result = RollbackResult(
                success=False,
                snapshot_id=snapshot_id,
                restored_commit="",
                restored_venv=False,
                error_message=str(e),
                duration=duration
            )
            
            self._log_rollback_attempt(result, reason)
            self.logger.error(f"Rollback exception: {e}")
            return result
    
    def _generate_snapshot_id(self) -> str:
        """Generate unique snapshot ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        hash_suffix = hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:8]
        return f"snapshot_{timestamp}_{hash_suffix}"
    
    def _create_git_snapshot(self, snapshot_id: str, description: str) -> Optional[str]:
        """Create Git commit for current state."""
        try:
            # Add all changes to staging
            subprocess.run(['git', 'add', '.'], cwd=self.project_root, check=True)
            
            # Create commit
            commit_message = f"Safe Mode Snapshot: {snapshot_id} - {description}"
            result = subprocess.run(
                ['git', 'commit', '-m', commit_message],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            # Get current commit hash
            hash_result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            
            return hash_result.stdout.strip()
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Git snapshot failed: {e}")
            return None
    
    def _backup_virtual_environment(self, snapshot_id: str) -> Optional[str]:
        """Create backup of virtual environment."""
        try:
            backup_path = self.snapshots_dir / f"{snapshot_id}_venv.tar.gz"
            
            with tarfile.open(backup_path, 'w:gz') as tar:
                tar.add(self.venv_path, arcname='venv')
            
            return str(backup_path)
            
        except Exception as e:
            self.logger.error(f"Virtual environment backup failed: {e}")
            return None
    
    def _calculate_requirements_hash(self) -> str:
        """Calculate hash of current requirements."""
        try:
            requirements_files = ['requirements.txt', 'requirements_creative.txt']
            combined_content = ""
            
            for req_file in requirements_files:
                req_path = self.project_root / req_file
                if req_path.exists():
                    with open(req_path, 'r') as f:
                        combined_content += f.read()
            
            return hashlib.sha256(combined_content.encode()).hexdigest()
            
        except Exception as e:
            self.logger.error(f"Requirements hash calculation failed: {e}")
            return "unknown"
    
    def _capture_system_state(self) -> Dict[str, Any]:
        """Capture current system state."""
        try:
            return {
                'python_version': sys.version,
                'python_executable': sys.executable,
                'working_directory': os.getcwd(),
                'environment_variables': dict(os.environ),
                'installed_packages': self._get_installed_packages(),
                'system_info': {
                    'platform': sys.platform,
                    'architecture': sys.maxsize > 2**32 and '64bit' or '32bit'
                }
            }
        except Exception as e:
            self.logger.error(f"System state capture failed: {e}")
            return {}
    
    def _get_installed_packages(self) -> List[str]:
        """Get list of installed Python packages."""
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'freeze'],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip().split('\n')
        except Exception:
            return []
    
    def _store_snapshot(self, snapshot: EnvironmentSnapshot):
        """Store snapshot metadata in database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO environment_snapshots 
                (snapshot_id, git_commit_hash, venv_backup_path, requirements_hash, 
                 system_state, description, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                snapshot.snapshot_id,
                snapshot.git_commit_hash,
                snapshot.venv_backup_path,
                snapshot.requirements_hash,
                json.dumps(snapshot.system_state),
                snapshot.description,
                snapshot.timestamp
            ))
            conn.commit()
    
    def _get_snapshot(self, snapshot_id: str) -> Optional[EnvironmentSnapshot]:
        """Retrieve snapshot from database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM environment_snapshots WHERE snapshot_id = ?",
                    (snapshot_id,)
                )
                row = cursor.fetchone()
                
                if row:
                    return EnvironmentSnapshot(
                        snapshot_id=row['snapshot_id'],
                        timestamp=datetime.fromisoformat(row['timestamp']),
                        git_commit_hash=row['git_commit_hash'],
                        venv_backup_path=row['venv_backup_path'],
                        requirements_hash=row['requirements_hash'],
                        system_state=json.loads(row['system_state']),
                        description=row['description'],
                        is_valid=bool(row['is_valid'])
                    )
                return None
        except Exception as e:
            self.logger.error(f"Failed to retrieve snapshot: {e}")
            return None
    
    def _rollback_git(self, commit_hash: str) -> bool:
        """Rollback Git to specific commit."""
        try:
            subprocess.run(
                ['git', 'reset', '--hard', commit_hash],
                cwd=self.project_root,
                check=True
            )
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Git rollback failed: {e}")
            return False
    
    def _restore_virtual_environment(self, backup_path: str) -> bool:
        """Restore virtual environment from backup."""
        try:
            # Remove current venv
            if self.venv_path.exists():
                shutil.rmtree(self.venv_path)
            
            # Extract backup
            with tarfile.open(backup_path, 'r:gz') as tar:
                tar.extractall(self.project_root)
            
            return True
        except Exception as e:
            self.logger.error(f"Virtual environment restore failed: {e}")
            return False
    
    def _verify_system_integrity(self, snapshot: EnvironmentSnapshot) -> bool:
        """Verify system integrity after rollback."""
        try:
            # Check if Git commit matches
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            
            current_commit = result.stdout.strip()
            if current_commit != snapshot.git_commit_hash:
                self.logger.error("Git commit mismatch after rollback")
                return False
            
            # Check if virtual environment exists
            if not self.venv_path.exists():
                self.logger.error("Virtual environment missing after rollback")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"System integrity check failed: {e}")
            return False
    
    def _log_rollback_attempt(self, result: RollbackResult, reason: str):
        """Log rollback attempt to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO rollback_history 
                    (snapshot_id, rollback_reason, success, restored_commit, 
                     restored_venv, error_message, duration_seconds)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    result.snapshot_id,
                    reason,
                    result.success,
                    result.restored_commit,
                    result.restored_venv,
                    result.error_message,
                    result.duration
                ))
                conn.commit()
        except Exception as e:
            self.logger.error(f"Failed to log rollback attempt: {e}")
    
    def _cleanup_old_snapshots(self):
        """Remove old snapshots to maintain storage limits."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get snapshots ordered by creation date
                cursor.execute("""
                    SELECT snapshot_id, venv_backup_path FROM environment_snapshots 
                    ORDER BY created_at DESC
                """)
                snapshots = cursor.fetchall()
                
                # Remove excess snapshots
                if len(snapshots) > self.max_snapshots:
                    for snapshot_id, venv_backup_path in snapshots[self.max_snapshots:]:
                        # Remove backup file
                        backup_path = Path(venv_backup_path)
                        if backup_path.exists():
                            backup_path.unlink()
                        
                        # Remove from database
                        cursor.execute(
                            "DELETE FROM environment_snapshots WHERE snapshot_id = ?",
                            (snapshot_id,)
                        )
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Snapshot cleanup failed: {e}")
    
    def get_available_snapshots(self) -> List[EnvironmentSnapshot]:
        """Get list of available snapshots."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM environment_snapshots 
                    WHERE is_valid = 1 
                    ORDER BY created_at DESC
                """)
                
                snapshots = []
                for row in cursor.fetchall():
                    snapshots.append(EnvironmentSnapshot(
                        snapshot_id=row['snapshot_id'],
                        timestamp=datetime.fromisoformat(row['timestamp']),
                        git_commit_hash=row['git_commit_hash'],
                        venv_backup_path=row['venv_backup_path'],
                        requirements_hash=row['requirements_hash'],
                        system_state=json.loads(row['system_state']),
                        description=row['description'],
                        is_valid=bool(row['is_valid'])
                    ))
                
                return snapshots
                
        except Exception as e:
            self.logger.error(f"Failed to get available snapshots: {e}")
            return []


if __name__ == "__main__":
    # Test the Safe Mode Manager
    logging.basicConfig(level=logging.INFO)
    
    config = {
        'db_path': 'right_perspective.db',
        'snapshots_dir': './snapshots',
        'venv_path': './venv',
        'project_root': '.',
        'max_snapshots': 5
    }
    
    manager = SafeModeManager(config)
    
    # Create a test snapshot
    snapshot = manager.create_snapshot("Test snapshot")
    if snapshot:
        print(f"Created snapshot: {snapshot.snapshot_id}")
        
        # List available snapshots
        snapshots = manager.get_available_snapshots()
        print(f"Available snapshots: {len(snapshots)}")
    else:
        print("Failed to create snapshot")