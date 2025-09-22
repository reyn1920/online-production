"""
Session Persistence System for Commitment Tracking
Ensures all commitments and behavioral rules persist across sessions and conversations
"""

import json
import os
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

from memory_store import MemoryStore
from behavioral_contract import BehavioralContract
from compliance_checker import ComplianceChecker
from audit_trail import AuditTrail
from enforcement_engine import EnforcementEngine


@dataclass
class SessionState:
    """Represents the state of a session"""
    session_id: str
    start_time: datetime
    last_activity: datetime
    commitments: List[Dict[str, Any]]
    behavioral_rules: List[Dict[str, Any]]
    compliance_level: float
    total_actions: int
    violations: int
    is_active: bool


class SessionPersistence:
    """
    Manages persistence of commitments and behavioral rules across sessions
    """
    
    def __init__(self, persistence_dir: str = "commitment_data"):
        self.persistence_dir = Path(persistence_dir)
        self.persistence_dir.mkdir(exist_ok=True)
        
        # Database for session persistence
        self.db_path = self.persistence_dir / "sessions.db"
        self.lock = threading.Lock()
        
        # Initialize components
        self.memory_store = MemoryStore()
        self.behavioral_contract = BehavioralContract()
        self.compliance_checker = ComplianceChecker()
        self.audit_trail = AuditTrail()
        self.enforcement_engine = EnforcementEngine()
        
        # Session management
        self.current_session_id = None
        self.session_timeout = timedelta(hours=24)  # Sessions expire after 24 hours
        
        self._init_database()
        self._load_persistent_state()
        
    def _init_database(self):
        """Initialize the session persistence database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    start_time TEXT NOT NULL,
                    last_activity TEXT NOT NULL,
                    commitments TEXT NOT NULL,
                    behavioral_rules TEXT NOT NULL,
                    compliance_level REAL NOT NULL,
                    total_actions INTEGER NOT NULL,
                    violations INTEGER NOT NULL,
                    is_active BOOLEAN NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS persistent_commitments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    commitment_text TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    is_permanent BOOLEAN NOT NULL,
                    metadata TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS persistent_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_name TEXT NOT NULL,
                    rule_description TEXT NOT NULL,
                    rule_pattern TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    is_active BOOLEAN NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS system_state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
    
    def start_session(self, session_id: Optional[str] = None) -> str:
        """
        Start a new session or resume an existing one
        
        Args:
            session_id: Optional session ID to resume
            
        Returns:
            The session ID
        """
        with self.lock:
            if session_id and self._session_exists(session_id):
                # Resume existing session
                self.current_session_id = session_id
                self._update_session_activity(session_id)
                self.audit_trail.log_event("session_resumed", {"session_id": session_id})
            else:
                # Create new session
                self.current_session_id = self._generate_session_id()
                self._create_new_session(self.current_session_id)
                self.audit_trail.log_event("session_started", {"session_id": self.current_session_id})
            
            # Load session state
            self._load_session_state(self.current_session_id)
            
            return self.current_session_id
    
    def end_session(self, session_id: Optional[str] = None):
        """
        End the current session and save state
        
        Args:
            session_id: Optional session ID to end (defaults to current)
        """
        with self.lock:
            target_session = session_id or self.current_session_id
            if target_session:
                self._save_session_state(target_session)
                self._deactivate_session(target_session)
                self.audit_trail.log_event("session_ended", {"session_id": target_session})
                
                if target_session == self.current_session_id:
                    self.current_session_id = None
    
    def save_permanent_commitment(self, commitment_text: str, priority: int = 1, metadata: Optional[Dict] = None):
        """
        Save a commitment that persists across all sessions
        
        Args:
            commitment_text: The commitment text
            priority: Priority level (1-10, higher is more important)
            metadata: Optional metadata dictionary
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO persistent_commitments 
                (commitment_text, created_at, priority, is_permanent, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (
                commitment_text,
                datetime.now().isoformat(),
                priority,
                True,
                json.dumps(metadata or {})
            ))
        
        # Add to current session
        self.memory_store.store_commitment(commitment_text, metadata or {})
        self.audit_trail.log_event("permanent_commitment_saved", {
            "commitment": commitment_text,
            "priority": priority
        })
    
    def save_permanent_rule(self, rule_name: str, rule_description: str, 
                           rule_pattern: str, action_type: str):
        """
        Save a behavioral rule that persists across all sessions
        
        Args:
            rule_name: Name of the rule
            rule_description: Description of what the rule does
            rule_pattern: Pattern to match against actions
            action_type: Type of action (block, warn, allow)
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO persistent_rules 
                (rule_name, rule_description, rule_pattern, action_type, created_at, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                rule_name,
                rule_description,
                rule_pattern,
                action_type,
                datetime.now().isoformat(),
                True
            ))
        
        # Add to current behavioral contract
        self.behavioral_contract.add_rule(rule_name, rule_pattern, action_type)
        self.audit_trail.log_event("permanent_rule_saved", {
            "rule_name": rule_name,
            "action_type": action_type
        })
    
    def get_persistent_commitments(self) -> List[Dict[str, Any]]:
        """Get all persistent commitments"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT commitment_text, created_at, priority, metadata
                FROM persistent_commitments
                WHERE is_permanent = 1
                ORDER BY priority DESC, created_at ASC
            """)
            
            commitments = []
            for row in cursor.fetchall():
                commitments.append({
                    "text": row[0],
                    "created_at": row[1],
                    "priority": row[2],
                    "metadata": json.loads(row[3])
                })
            
            return commitments
    
    def get_persistent_rules(self) -> List[Dict[str, Any]]:
        """Get all persistent behavioral rules"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT rule_name, rule_description, rule_pattern, action_type, created_at
                FROM persistent_rules
                WHERE is_active = 1
                ORDER BY created_at ASC
            """)
            
            rules = []
            for row in cursor.fetchall():
                rules.append({
                    "name": row[0],
                    "description": row[1],
                    "pattern": row[2],
                    "action_type": row[3],
                    "created_at": row[4]
                })
            
            return rules
    
    def get_session_history(self, limit: int = 10) -> List[SessionState]:
        """
        Get recent session history
        
        Args:
            limit: Maximum number of sessions to return
            
        Returns:
            List of session states
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT session_id, start_time, last_activity, commitments, 
                       behavioral_rules, compliance_level, total_actions, 
                       violations, is_active
                FROM sessions
                ORDER BY last_activity DESC
                LIMIT ?
            """, (limit,))
            
            sessions = []
            for row in cursor.fetchall():
                sessions.append(SessionState(
                    session_id=row[0],
                    start_time=datetime.fromisoformat(row[1]),
                    last_activity=datetime.fromisoformat(row[2]),
                    commitments=json.loads(row[3]),
                    behavioral_rules=json.loads(row[4]),
                    compliance_level=row[5],
                    total_actions=row[6],
                    violations=row[7],
                    is_active=bool(row[8])
                ))
            
            return sessions
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions from the database"""
        cutoff_time = datetime.now() - self.session_timeout
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT session_id FROM sessions 
                WHERE last_activity < ? AND is_active = 1
            """, (cutoff_time.isoformat(),))
            
            expired_sessions = [row[0] for row in cursor.fetchall()]
            
            for session_id in expired_sessions:
                self._deactivate_session(session_id)
                self.audit_trail.log_event("session_expired", {"session_id": session_id})
    
    def export_session_data(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Export session data for backup or transfer
        
        Args:
            session_id: Session to export (defaults to current)
            
        Returns:
            Dictionary containing all session data
        """
        target_session = session_id or self.current_session_id
        if not target_session:
            raise ValueError("No session specified and no current session")
        
        with sqlite3.connect(self.db_path) as conn:
            # Get session data
            cursor = conn.execute("""
                SELECT * FROM sessions WHERE session_id = ?
            """, (target_session,))
            session_row = cursor.fetchone()
            
            if not session_row:
                raise ValueError(f"Session {target_session} not found")
            
            # Get persistent data
            persistent_commitments = self.get_persistent_commitments()
            persistent_rules = self.get_persistent_rules()
            
            return {
                "session_id": target_session,
                "session_data": {
                    "start_time": session_row[1],
                    "last_activity": session_row[2],
                    "commitments": json.loads(session_row[3]),
                    "behavioral_rules": json.loads(session_row[4]),
                    "compliance_level": session_row[5],
                    "total_actions": session_row[6],
                    "violations": session_row[7],
                    "is_active": bool(session_row[8])
                },
                "persistent_commitments": persistent_commitments,
                "persistent_rules": persistent_rules,
                "export_timestamp": datetime.now().isoformat()
            }
    
    def import_session_data(self, data: Dict[str, Any]) -> str:
        """
        Import session data from backup
        
        Args:
            data: Session data dictionary from export
            
        Returns:
            New session ID
        """
        new_session_id = self._generate_session_id()
        
        # Import persistent commitments
        for commitment in data.get("persistent_commitments", []):
            self.save_permanent_commitment(
                commitment["text"],
                commitment["priority"],
                commitment["metadata"]
            )
        
        # Import persistent rules
        for rule in data.get("persistent_rules", []):
            self.save_permanent_rule(
                rule["name"],
                rule["description"],
                rule["pattern"],
                rule["action_type"]
            )
        
        # Create session with imported data
        session_data = data["session_data"]
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO sessions 
                (session_id, start_time, last_activity, commitments, 
                 behavioral_rules, compliance_level, total_actions, 
                 violations, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                new_session_id,
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                session_data["commitments"],
                session_data["behavioral_rules"],
                session_data["compliance_level"],
                session_data["total_actions"],
                session_data["violations"],
                True
            ))
        
        self.audit_trail.log_event("session_imported", {
            "new_session_id": new_session_id,
            "original_session": data.get("session_id")
        })
        
        return new_session_id
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID"""
        timestamp = int(time.time() * 1000)
        return f"session_{timestamp}"
    
    def _session_exists(self, session_id: str) -> bool:
        """Check if a session exists and is active"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 1 FROM sessions 
                WHERE session_id = ? AND is_active = 1
            """, (session_id,))
            return cursor.fetchone() is not None
    
    def _create_new_session(self, session_id: str):
        """Create a new session in the database"""
        now = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO sessions 
                (session_id, start_time, last_activity, commitments, 
                 behavioral_rules, compliance_level, total_actions, 
                 violations, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                now,
                now,
                json.dumps([]),
                json.dumps([]),
                1.0,
                0,
                0,
                True
            ))
    
    def _update_session_activity(self, session_id: str):
        """Update the last activity time for a session"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE sessions 
                SET last_activity = ?
                WHERE session_id = ?
            """, (datetime.now().isoformat(), session_id))
    
    def _deactivate_session(self, session_id: str):
        """Mark a session as inactive"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE sessions 
                SET is_active = 0
                WHERE session_id = ?
            """, (session_id,))
    
    def _load_session_state(self, session_id: str):
        """Load state for a specific session"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT commitments, behavioral_rules, compliance_level
                FROM sessions WHERE session_id = ?
            """, (session_id,))
            
            row = cursor.fetchone()
            if row:
                # Load session-specific commitments
                commitments = json.loads(row[0])
                for commitment in commitments:
                    self.memory_store.store_commitment(
                        commitment["text"], 
                        commitment.get("metadata", {})
                    )
                
                # Load session-specific rules
                rules = json.loads(row[1])
                for rule in rules:
                    self.behavioral_contract.add_rule(
                        rule["name"],
                        rule["pattern"],
                        rule["action_type"]
                    )
        
        # Always load persistent commitments and rules
        self._load_persistent_state()
    
    def _load_persistent_state(self):
        """Load persistent commitments and rules"""
        # Load persistent commitments
        for commitment in self.get_persistent_commitments():
            self.memory_store.store_commitment(
                commitment["text"],
                commitment["metadata"]
            )
        
        # Load persistent rules
        for rule in self.get_persistent_rules():
            self.behavioral_contract.add_rule(
                rule["name"],
                rule["pattern"],
                rule["action_type"]
            )
    
    def _save_session_state(self, session_id: str):
        """Save current state to session"""
        # Get current commitments and rules
        commitments = self.memory_store.get_all_commitments()
        rules = self.behavioral_contract.get_all_rules()
        compliance_level = self.compliance_checker.get_compliance_level()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE sessions 
                SET commitments = ?, behavioral_rules = ?, 
                    compliance_level = ?, last_activity = ?
                WHERE session_id = ?
            """, (
                json.dumps(commitments),
                json.dumps(rules),
                compliance_level,
                datetime.now().isoformat(),
                session_id
            ))


# Global session persistence instance
_session_persistence = None

def get_session_persistence() -> SessionPersistence:
    """Get the global session persistence instance"""
    global _session_persistence
    if _session_persistence is None:
        _session_persistence = SessionPersistence()
    return _session_persistence


def ensure_persistence():
    """
    Decorator to ensure session persistence is active
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            persistence = get_session_persistence()
            if not persistence.current_session_id:
                persistence.start_session()
            return func(*args, **kwargs)
        return wrapper
    return decorator


if __name__ == "__main__":
    # Test the session persistence system
    persistence = SessionPersistence()
    
    # Start a session
    session_id = persistence.start_session()
    print(f"Started session: {session_id}")
    
    # Add some persistent commitments
    persistence.save_permanent_commitment(
        "Always use Puppeteer for web testing and automation",
        priority=10
    )
    
    persistence.save_permanent_commitment(
        "Never delete files without explicit user permission",
        priority=9
    )
    
    # Add some persistent rules
    persistence.save_permanent_rule(
        "no_file_deletion",
        "Prevent unauthorized file deletion",
        r"delete|remove|rm\s+",
        "block"
    )
    
    # Test export/import
    exported_data = persistence.export_session_data()
    print(f"Exported session data: {len(exported_data)} keys")
    
    # End session
    persistence.end_session()
    print("Session ended and state saved")
    
    # Test session resume
    new_session = persistence.start_session(session_id)
    print(f"Resumed session: {new_session}")
    
    # Verify persistent data loaded
    commitments = persistence.get_persistent_commitments()
    rules = persistence.get_persistent_rules()
    
    print(f"Loaded {len(commitments)} persistent commitments")
    print(f"Loaded {len(rules)} persistent rules")
    
    print("✅ Session persistence system test completed successfully")