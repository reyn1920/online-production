"""
External Memory System for AI Commitment Tracking
Provides persistent storage for all commitments and promises made by the AI system.
"""

import json
import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class Commitment:
    """Represents a single commitment or promise made by the AI"""
    id: str
    content: str
    timestamp: str
    context: str
    status: str = "active"  # active, fulfilled, violated, cancelled
    enforcement_level: str = "strict"  # strict, moderate, advisory
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class ExternalMemoryStore:
    """
    Persistent storage system for AI commitments and behavioral contracts.
    Uses SQLite for reliability and JSON for complex data structures.
    """
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Create memory store in project directory
            project_root = Path(__file__).parent.parent
            memory_dir = project_root / "commitment_system" / "data"
            memory_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(memory_dir / "commitments.db")
        
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the SQLite database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS commitments (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    context TEXT NOT NULL,
                    status TEXT DEFAULT 'active',
                    enforcement_level TEXT DEFAULT 'strict',
                    metadata TEXT DEFAULT '{}'
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS behavioral_rules (
                    id TEXT PRIMARY KEY,
                    rule_type TEXT NOT NULL,
                    rule_content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    metadata TEXT DEFAULT '{}'
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action_type TEXT NOT NULL,
                    action_content TEXT NOT NULL,
                    commitment_id TEXT,
                    compliance_status TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    details TEXT DEFAULT '{}'
                )
            """)
            
            conn.commit()
    
    def store_commitment(self, commitment: Commitment) -> bool:
        """Store a new commitment in the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO commitments 
                    (id, content, timestamp, context, status, enforcement_level, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    commitment.id,
                    commitment.content,
                    commitment.timestamp,
                    commitment.context,
                    commitment.status,
                    commitment.enforcement_level,
                    json.dumps(commitment.metadata)
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error storing commitment: {e}")
            return False
    
    def get_commitment(self, commitment_id: str) -> Optional[Commitment]:
        """Retrieve a specific commitment by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT id, content, timestamp, context, status, enforcement_level, metadata
                    FROM commitments WHERE id = ?
                """, (commitment_id,))
                
                row = cursor.fetchone()
                if row:
                    return Commitment(
                        id=row[0],
                        content=row[1],
                        timestamp=row[2],
                        context=row[3],
                        status=row[4],
                        enforcement_level=row[5],
                        metadata=json.loads(row[6])
                    )
                return None
        except Exception as e:
            print(f"Error retrieving commitment: {e}")
            return None
    
    def get_active_commitments(self) -> List[Commitment]:
        """Retrieve all active commitments"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT id, content, timestamp, context, status, enforcement_level, metadata
                    FROM commitments WHERE status = 'active'
                    ORDER BY timestamp DESC
                """)
                
                commitments = []
                for row in cursor.fetchall():
                    commitments.append(Commitment(
                        id=row[0],
                        content=row[1],
                        timestamp=row[2],
                        context=row[3],
                        status=row[4],
                        enforcement_level=row[5],
                        metadata=json.loads(row[6])
                    ))
                return commitments
        except Exception as e:
            print(f"Error retrieving active commitments: {e}")
            return []
    
    def update_commitment_status(self, commitment_id: str, new_status: str) -> bool:
        """Update the status of a commitment"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE commitments SET status = ? WHERE id = ?
                """, (new_status, commitment_id))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error updating commitment status: {e}")
            return False
    
    def log_action(self, action_type: str, action_content: str, 
                   commitment_id: str = None, compliance_status: str = "unknown",
                   details: Dict[str, Any] = None) -> bool:
        """Log an action for audit trail purposes"""
        try:
            if details is None:
                details = {}
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO audit_log 
                    (action_type, action_content, commitment_id, compliance_status, timestamp, details)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    action_type,
                    action_content,
                    commitment_id,
                    compliance_status,
                    datetime.now().isoformat(),
                    json.dumps(details)
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error logging action: {e}")
            return False
    
    def get_audit_trail(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve recent audit trail entries"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT action_type, action_content, commitment_id, compliance_status, timestamp, details
                    FROM audit_log ORDER BY timestamp DESC LIMIT ?
                """, (limit,))
                
                entries = []
                for row in cursor.fetchall():
                    entries.append({
                        'action_type': row[0],
                        'action_content': row[1],
                        'commitment_id': row[2],
                        'compliance_status': row[3],
                        'timestamp': row[4],
                        'details': json.loads(row[5])
                    })
                return entries
        except Exception as e:
            print(f"Error retrieving audit trail: {e}")
            return []
    
    def clear_all_data(self) -> bool:
        """Clear all stored data (use with extreme caution)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM commitments")
                conn.execute("DELETE FROM behavioral_rules")
                conn.execute("DELETE FROM audit_log")
                conn.commit()
                return True
        except Exception as e:
            print(f"Error clearing data: {e}")
            return False

# Global instance for easy access
memory_store = ExternalMemoryStore()