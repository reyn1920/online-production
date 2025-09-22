"""
Comprehensive Audit Trail System
Logs all actions and compares them to commitments for complete accountability.
"""

import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
from pathlib import Path

from .memory_store import memory_store

class AuditEventType(Enum):
    """Types of audit events"""
    COMMITMENT_MADE = "commitment_made"
    COMMITMENT_FULFILLED = "commitment_fulfilled"
    COMMITMENT_VIOLATED = "commitment_violated"
    ACTION_TAKEN = "action_taken"
    ACTION_BLOCKED = "action_blocked"
    COMPLIANCE_CHECK = "compliance_check"
    SYSTEM_EVENT = "system_event"
    USER_INTERACTION = "user_interaction"

class ComplianceStatus(Enum):
    """Compliance status for audit events"""
    COMPLIANT = "compliant"
    VIOLATION = "violation"
    PARTIAL_COMPLIANCE = "partial_compliance"
    UNDER_REVIEW = "under_review"
    UNKNOWN = "unknown"

@dataclass
class AuditEvent:
    """Represents a single audit trail event"""
    event_id: str
    event_type: AuditEventType
    timestamp: str
    description: str
    compliance_status: ComplianceStatus
    commitment_id: Optional[str] = None
    action_details: Dict[str, Any] = None
    context: Dict[str, Any] = None
    severity: str = "medium"  # low, medium, high, critical
    
    def __post_init__(self):
        if self.action_details is None:
            self.action_details = {}
        if self.context is None:
            self.context = {}

@dataclass
class ComplianceAnalysis:
    """Analysis of compliance patterns and trends"""
    total_events: int
    compliance_rate: float
    violation_count: int
    most_common_violations: List[Tuple[str, int]]
    commitment_fulfillment_rate: float
    trend_analysis: Dict[str, Any]
    recommendations: List[str]

class AuditTrailSystem:
    """
    Comprehensive audit trail system that tracks all actions,
    commitments, and compliance events with detailed analysis.
    """
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            project_root = Path(__file__).parent.parent
            audit_dir = project_root / "commitment_system" / "data"
            audit_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(audit_dir / "audit_trail.db")
        
        self.db_path = db_path
        self.init_audit_database()
        
        # Cache for recent events
        self.recent_events_cache: List[AuditEvent] = []
        self.cache_size = 100
        
        # Analysis cache
        self.last_analysis: Optional[ComplianceAnalysis] = None
        self.analysis_cache_time: Optional[datetime] = None
        self.analysis_cache_duration = timedelta(minutes=5)
    
    def init_audit_database(self):
        """Initialize the audit trail database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    description TEXT NOT NULL,
                    compliance_status TEXT NOT NULL,
                    commitment_id TEXT,
                    action_details TEXT DEFAULT '{}',
                    context TEXT DEFAULT '{}',
                    severity TEXT DEFAULT 'medium'
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS compliance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata TEXT DEFAULT '{}'
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS commitment_tracking (
                    commitment_id TEXT PRIMARY KEY,
                    commitment_content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    status TEXT DEFAULT 'active',
                    fulfillment_events TEXT DEFAULT '[]',
                    violation_events TEXT DEFAULT '[]',
                    last_updated TEXT NOT NULL
                )
            """)
            
            # Create indexes for better performance
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_timestamp 
                ON audit_events(timestamp)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_compliance 
                ON audit_events(compliance_status)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_commitment 
                ON audit_events(commitment_id)
            """)
            
            conn.commit()
    
    def log_event(self, event: AuditEvent) -> bool:
        """Log an audit event to the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO audit_events 
                    (event_id, event_type, timestamp, description, compliance_status,
                     commitment_id, action_details, context, severity)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.event_id,
                    event.event_type.value,
                    event.timestamp,
                    event.description,
                    event.compliance_status.value,
                    event.commitment_id,
                    json.dumps(event.action_details),
                    json.dumps(event.context),
                    event.severity
                ))
                conn.commit()
            
            # Update cache
            self.recent_events_cache.append(event)
            if len(self.recent_events_cache) > self.cache_size:
                self.recent_events_cache = self.recent_events_cache[-self.cache_size:]
            
            # Update commitment tracking if applicable
            if event.commitment_id:
                self._update_commitment_tracking(event)
            
            return True
            
        except Exception as e:
            print(f"Error logging audit event: {e}")
            return False
    
    def log_action(self, action_description: str, action_type: str = "general",
                   compliance_status: ComplianceStatus = ComplianceStatus.UNKNOWN,
                   commitment_id: str = None, context: Dict[str, Any] = None,
                   severity: str = "medium") -> str:
        """
        Convenience method to log an action with automatic event ID generation.
        Returns the generated event ID.
        """
        event_id = self._generate_event_id(action_description)
        
        event = AuditEvent(
            event_id=event_id,
            event_type=AuditEventType.ACTION_TAKEN,
            timestamp=datetime.now().isoformat(),
            description=action_description,
            compliance_status=compliance_status,
            commitment_id=commitment_id,
            action_details={"action_type": action_type},
            context=context or {},
            severity=severity
        )
        
        self.log_event(event)
        return event_id
    
    def log_commitment_event(self, commitment_id: str, event_type: AuditEventType,
                           description: str, compliance_status: ComplianceStatus,
                           context: Dict[str, Any] = None) -> str:
        """Log a commitment-related event"""
        event_id = self._generate_event_id(f"{event_type.value}_{commitment_id}")
        
        event = AuditEvent(
            event_id=event_id,
            event_type=event_type,
            timestamp=datetime.now().isoformat(),
            description=description,
            compliance_status=compliance_status,
            commitment_id=commitment_id,
            context=context or {}
        )
        
        self.log_event(event)
        return event_id
    
    def get_events(self, limit: int = 100, event_type: AuditEventType = None,
                   commitment_id: str = None, 
                   start_time: datetime = None, end_time: datetime = None) -> List[AuditEvent]:
        """Retrieve audit events with optional filtering"""
        try:
            query = """
                SELECT event_id, event_type, timestamp, description, compliance_status,
                       commitment_id, action_details, context, severity
                FROM audit_events
                WHERE 1=1
            """
            params = []
            
            if event_type:
                query += " AND event_type = ?"
                params.append(event_type.value)
            
            if commitment_id:
                query += " AND commitment_id = ?"
                params.append(commitment_id)
            
            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time.isoformat())
            
            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time.isoformat())
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(query, params)
                events = []
                
                for row in cursor.fetchall():
                    events.append(AuditEvent(
                        event_id=row[0],
                        event_type=AuditEventType(row[1]),
                        timestamp=row[2],
                        description=row[3],
                        compliance_status=ComplianceStatus(row[4]),
                        commitment_id=row[5],
                        action_details=json.loads(row[6]),
                        context=json.loads(row[7]),
                        severity=row[8]
                    ))
                
                return events
                
        except Exception as e:
            print(f"Error retrieving events: {e}")
            return []
    
    def analyze_compliance(self, days: int = 7) -> ComplianceAnalysis:
        """
        Perform comprehensive compliance analysis over the specified period.
        Uses caching to avoid expensive recalculations.
        """
        # Check if we have a recent analysis in cache
        if (self.last_analysis and self.analysis_cache_time and 
            datetime.now() - self.analysis_cache_time < self.analysis_cache_duration):
            return self.last_analysis
        
        try:
            start_time = datetime.now() - timedelta(days=days)
            events = self.get_events(limit=10000, start_time=start_time)
            
            if not events:
                return ComplianceAnalysis(
                    total_events=0,
                    compliance_rate=0.0,
                    violation_count=0,
                    most_common_violations=[],
                    commitment_fulfillment_rate=0.0,
                    trend_analysis={},
                    recommendations=["No events to analyze"]
                )
            
            # Basic statistics
            total_events = len(events)
            compliant_events = len([e for e in events if e.compliance_status == ComplianceStatus.COMPLIANT])
            violation_events = [e for e in events if e.compliance_status == ComplianceStatus.VIOLATION]
            violation_count = len(violation_events)
            
            compliance_rate = compliant_events / total_events if total_events > 0 else 0.0
            
            # Analyze violation patterns
            violation_patterns = {}
            for event in violation_events:
                pattern = event.description[:50]  # First 50 chars as pattern
                violation_patterns[pattern] = violation_patterns.get(pattern, 0) + 1
            
            most_common_violations = sorted(
                violation_patterns.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5]
            
            # Commitment fulfillment analysis
            commitment_events = [e for e in events if e.commitment_id]
            commitment_ids = set(e.commitment_id for e in commitment_events)
            
            fulfilled_commitments = 0
            for commitment_id in commitment_ids:
                commitment_events_filtered = [e for e in commitment_events if e.commitment_id == commitment_id]
                fulfillment_events = [e for e in commitment_events_filtered 
                                    if e.event_type == AuditEventType.COMMITMENT_FULFILLED]
                if fulfillment_events:
                    fulfilled_commitments += 1
            
            commitment_fulfillment_rate = (
                fulfilled_commitments / len(commitment_ids) 
                if commitment_ids else 0.0
            )
            
            # Trend analysis
            trend_analysis = self._analyze_trends(events, days)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                compliance_rate, violation_count, most_common_violations
            )
            
            analysis = ComplianceAnalysis(
                total_events=total_events,
                compliance_rate=compliance_rate,
                violation_count=violation_count,
                most_common_violations=most_common_violations,
                commitment_fulfillment_rate=commitment_fulfillment_rate,
                trend_analysis=trend_analysis,
                recommendations=recommendations
            )
            
            # Cache the analysis
            self.last_analysis = analysis
            self.analysis_cache_time = datetime.now()
            
            return analysis
            
        except Exception as e:
            print(f"Error analyzing compliance: {e}")
            return ComplianceAnalysis(
                total_events=0,
                compliance_rate=0.0,
                violation_count=0,
                most_common_violations=[],
                commitment_fulfillment_rate=0.0,
                trend_analysis={},
                recommendations=[f"Analysis error: {str(e)}"]
            )
    
    def _analyze_trends(self, events: List[AuditEvent], days: int) -> Dict[str, Any]:
        """Analyze trends in compliance over time"""
        try:
            # Group events by day
            daily_stats = {}
            for event in events:
                event_date = datetime.fromisoformat(event.timestamp).date()
                date_str = event_date.isoformat()
                
                if date_str not in daily_stats:
                    daily_stats[date_str] = {
                        'total': 0,
                        'compliant': 0,
                        'violations': 0
                    }
                
                daily_stats[date_str]['total'] += 1
                if event.compliance_status == ComplianceStatus.COMPLIANT:
                    daily_stats[date_str]['compliant'] += 1
                elif event.compliance_status == ComplianceStatus.VIOLATION:
                    daily_stats[date_str]['violations'] += 1
            
            # Calculate daily compliance rates
            daily_rates = {}
            for date, stats in daily_stats.items():
                daily_rates[date] = stats['compliant'] / stats['total'] if stats['total'] > 0 else 0.0
            
            # Calculate trend direction
            rates = list(daily_rates.values())
            if len(rates) >= 2:
                recent_avg = sum(rates[-3:]) / min(3, len(rates))
                older_avg = sum(rates[:-3]) / max(1, len(rates) - 3) if len(rates) > 3 else rates[0]
                trend_direction = "improving" if recent_avg > older_avg else "declining"
            else:
                trend_direction = "insufficient_data"
            
            return {
                'daily_compliance_rates': daily_rates,
                'trend_direction': trend_direction,
                'average_daily_events': sum(stats['total'] for stats in daily_stats.values()) / len(daily_stats) if daily_stats else 0,
                'peak_violation_day': max(daily_stats.items(), key=lambda x: x[1]['violations'])[0] if daily_stats else None
            }
            
        except Exception as e:
            print(f"Error analyzing trends: {e}")
            return {"error": str(e)}
    
    def _generate_recommendations(self, compliance_rate: float, violation_count: int,
                                most_common_violations: List[Tuple[str, int]]) -> List[str]:
        """Generate actionable recommendations based on compliance analysis"""
        recommendations = []
        
        if compliance_rate < 0.8:
            recommendations.append("Compliance rate is below 80%. Consider reviewing and strengthening commitment enforcement.")
        
        if violation_count > 10:
            recommendations.append("High number of violations detected. Implement stricter compliance checking.")
        
        if most_common_violations:
            top_violation = most_common_violations[0]
            recommendations.append(f"Most common violation pattern: '{top_violation[0]}' ({top_violation[1]} occurrences). Focus on addressing this specific issue.")
        
        if compliance_rate > 0.95:
            recommendations.append("Excellent compliance rate! Current system is working well.")
        
        if not recommendations:
            recommendations.append("System appears to be functioning normally. Continue monitoring.")
        
        return recommendations
    
    def _update_commitment_tracking(self, event: AuditEvent):
        """Update commitment tracking based on audit events"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get existing tracking record
                cursor = conn.execute("""
                    SELECT fulfillment_events, violation_events 
                    FROM commitment_tracking 
                    WHERE commitment_id = ?
                """, (event.commitment_id,))
                
                row = cursor.fetchone()
                if row:
                    fulfillment_events = json.loads(row[0])
                    violation_events = json.loads(row[1])
                else:
                    fulfillment_events = []
                    violation_events = []
                
                # Update appropriate list
                if event.event_type == AuditEventType.COMMITMENT_FULFILLED:
                    fulfillment_events.append(event.event_id)
                elif event.compliance_status == ComplianceStatus.VIOLATION:
                    violation_events.append(event.event_id)
                
                # Update or insert tracking record
                conn.execute("""
                    INSERT OR REPLACE INTO commitment_tracking 
                    (commitment_id, commitment_content, created_at, status, 
                     fulfillment_events, violation_events, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.commitment_id,
                    event.description,  # This might need to be fetched from commitments table
                    event.timestamp,
                    "active",
                    json.dumps(fulfillment_events),
                    json.dumps(violation_events),
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                
        except Exception as e:
            print(f"Error updating commitment tracking: {e}")
    
    def _generate_event_id(self, content: str) -> str:
        """Generate a unique event ID based on content and timestamp"""
        timestamp = datetime.now().isoformat()
        content_hash = hashlib.md5((content + timestamp).encode()).hexdigest()
        return f"audit_{content_hash[:12]}"
    
    def export_audit_report(self, format: str = "json", days: int = 30) -> str:
        """Export comprehensive audit report in specified format"""
        try:
            start_time = datetime.now() - timedelta(days=days)
            events = self.get_events(limit=10000, start_time=start_time)
            analysis = self.analyze_compliance(days)
            
            report_data = {
                "report_metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "period_days": days,
                    "total_events": len(events)
                },
                "compliance_analysis": asdict(analysis),
                "recent_events": [asdict(event) for event in events[:50]],
                "summary": {
                    "compliance_rate": analysis.compliance_rate,
                    "total_violations": analysis.violation_count,
                    "commitment_fulfillment_rate": analysis.commitment_fulfillment_rate
                }
            }
            
            if format.lower() == "json":
                return json.dumps(report_data, indent=2)
            else:
                return str(report_data)  # Fallback to string representation
                
        except Exception as e:
            return f"Error generating report: {str(e)}"

# Global instance for easy access
audit_trail = AuditTrailSystem()