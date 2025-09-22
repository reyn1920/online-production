"""
Automated Compliance Checking System
Monitors all actions in real-time against stated promises and commitments.
"""

import asyncio
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import json

from .memory_store import memory_store
from .behavioral_contract import behavioral_contract, ContractViolation

class ComplianceLevel(Enum):
    """Levels of compliance checking"""
    STRICT = "strict"
    MODERATE = "moderate"
    ADVISORY = "advisory"
    DISABLED = "disabled"

@dataclass
class ComplianceEvent:
    """Represents a compliance checking event"""
    event_id: str
    event_type: str
    description: str
    timestamp: str
    compliance_status: str
    violations: List[ContractViolation]
    action_taken: str
    metadata: Dict[str, Any] = None

class AutomatedComplianceChecker:
    """
    Real-time compliance monitoring system that automatically checks
    all actions against commitments and behavioral contracts.
    """
    
    def __init__(self, compliance_level: ComplianceLevel = ComplianceLevel.STRICT):
        self.compliance_level = compliance_level
        self.is_monitoring = False
        self.monitoring_thread = None
        self.event_queue = []
        self.violation_callbacks: List[Callable] = []
        self.compliance_history: List[ComplianceEvent] = []
        
        # Statistics tracking
        self.stats = {
            "total_checks": 0,
            "violations_detected": 0,
            "actions_blocked": 0,
            "last_check": None,
            "uptime_start": datetime.now().isoformat()
        }
        
        # Initialize monitoring
        self.setup_monitoring()
    
    def setup_monitoring(self):
        """Setup the monitoring system"""
        if self.compliance_level != ComplianceLevel.DISABLED:
            self.start_monitoring()
    
    def start_monitoring(self):
        """Start the compliance monitoring system"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitoring_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True
            )
            self.monitoring_thread.start()
            
            # Log monitoring start
            memory_store.log_action(
                action_type="monitoring_started",
                action_content="Automated compliance monitoring started",
                compliance_status="system_active",
                details={"compliance_level": self.compliance_level.value}
            )
    
    def stop_monitoring(self):
        """Stop the compliance monitoring system"""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=1.0)
        
        # Log monitoring stop
        memory_store.log_action(
            action_type="monitoring_stopped",
            action_content="Automated compliance monitoring stopped",
            compliance_status="system_inactive",
            details={"uptime": self._calculate_uptime()}
        )
    
    def _monitoring_loop(self):
        """Main monitoring loop that runs in a separate thread"""
        while self.is_monitoring:
            try:
                # Process any queued events
                self._process_event_queue()
                
                # Perform periodic compliance checks
                self._periodic_compliance_check()
                
                # Update statistics
                self.stats["last_check"] = datetime.now().isoformat()
                
                # Sleep for a short interval
                time.sleep(0.1)  # Check every 100ms
                
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                # Log the error but continue monitoring
                memory_store.log_action(
                    action_type="monitoring_error",
                    action_content=f"Monitoring error: {str(e)}",
                    compliance_status="error",
                    details={"error_type": type(e).__name__}
                )
    
    def check_action_compliance(self, action_description: str, 
                              action_type: str = "general",
                              metadata: Dict[str, Any] = None) -> bool:
        """
        Check if an action complies with all commitments and rules.
        Returns True if action is compliant, False if it should be blocked.
        """
        if self.compliance_level == ComplianceLevel.DISABLED:
            return True
        
        # Increment check counter
        self.stats["total_checks"] += 1
        
        # Check compliance using behavioral contract
        violations = behavioral_contract.check_action_compliance(
            action_description, action_type
        )
        
        # Create compliance event
        event = ComplianceEvent(
            event_id=f"check_{int(time.time() * 1000)}",
            event_type="action_compliance_check",
            description=action_description,
            timestamp=datetime.now().isoformat(),
            compliance_status="compliant" if not violations else "violation",
            violations=violations,
            action_taken="none",
            metadata=metadata or {}
        )
        
        # Process violations based on compliance level
        action_allowed = self._process_violations(violations, event)
        
        # Store compliance event
        self.compliance_history.append(event)
        
        # Keep only recent history (last 1000 events)
        if len(self.compliance_history) > 1000:
            self.compliance_history = self.compliance_history[-1000:]
        
        # Log the compliance check
        memory_store.log_action(
            action_type="compliance_check",
            action_content=action_description,
            compliance_status=event.compliance_status,
            details={
                "violations_count": len(violations),
                "action_allowed": action_allowed,
                "compliance_level": self.compliance_level.value,
                "metadata": metadata or {}
            }
        )
        
        return action_allowed
    
    def _process_violations(self, violations: List[ContractViolation], 
                          event: ComplianceEvent) -> bool:
        """
        Process detected violations based on compliance level.
        Returns True if action should be allowed, False if blocked.
        """
        if not violations:
            return True
        
        # Update statistics
        self.stats["violations_detected"] += len(violations)
        
        # Determine action based on compliance level
        if self.compliance_level == ComplianceLevel.STRICT:
            # Block any action with violations
            blocking_violations = [v for v in violations if v.action_blocked]
            if blocking_violations:
                self.stats["actions_blocked"] += 1
                event.action_taken = "blocked"
                
                # Notify violation callbacks
                for callback in self.violation_callbacks:
                    try:
                        callback(violations, "blocked")
                    except Exception as e:
                        print(f"Error in violation callback: {e}")
                
                return False
        
        elif self.compliance_level == ComplianceLevel.MODERATE:
            # Block only high-severity violations
            high_severity_violations = [
                v for v in violations 
                if v.severity == "high" and v.action_blocked
            ]
            if high_severity_violations:
                self.stats["actions_blocked"] += 1
                event.action_taken = "blocked"
                return False
            else:
                event.action_taken = "warned"
        
        elif self.compliance_level == ComplianceLevel.ADVISORY:
            # Log violations but don't block actions
            event.action_taken = "logged"
        
        # Notify violation callbacks for non-blocking violations
        for callback in self.violation_callbacks:
            try:
                callback(violations, event.action_taken)
            except Exception as e:
                print(f"Error in violation callback: {e}")
        
        return True
    
    def add_violation_callback(self, callback: Callable):
        """Add a callback function to be called when violations are detected"""
        self.violation_callbacks.append(callback)
    
    def remove_violation_callback(self, callback: Callable):
        """Remove a violation callback"""
        if callback in self.violation_callbacks:
            self.violation_callbacks.remove(callback)
    
    def _process_event_queue(self):
        """Process any queued compliance events"""
        while self.event_queue:
            try:
                event = self.event_queue.pop(0)
                # Process the event (placeholder for future functionality)
                pass
            except IndexError:
                break
            except Exception as e:
                print(f"Error processing event: {e}")
    
    def _periodic_compliance_check(self):
        """Perform periodic compliance checks on system state"""
        # Check if there are any expired commitments
        active_commitments = memory_store.get_active_commitments()
        current_time = datetime.now()
        
        for commitment in active_commitments:
            commitment_time = datetime.fromisoformat(commitment.timestamp)
            age = current_time - commitment_time
            
            # Check for commitments that might need review (older than 1 hour)
            if age > timedelta(hours=1):
                memory_store.log_action(
                    action_type="commitment_review",
                    action_content=f"Long-standing commitment: {commitment.content}",
                    commitment_id=commitment.id,
                    compliance_status="review_needed",
                    details={"age_hours": age.total_seconds() / 3600}
                )
    
    def get_compliance_report(self) -> Dict[str, Any]:
        """Generate a comprehensive compliance report"""
        recent_violations = [
            event for event in self.compliance_history[-100:]
            if event.violations
        ]
        
        violation_types = {}
        for event in recent_violations:
            for violation in event.violations:
                violation_type = violation.violation_type.value
                violation_types[violation_type] = violation_types.get(violation_type, 0) + 1
        
        return {
            "system_status": {
                "monitoring_active": self.is_monitoring,
                "compliance_level": self.compliance_level.value,
                "uptime": self._calculate_uptime()
            },
            "statistics": self.stats.copy(),
            "recent_violations": {
                "total": len(recent_violations),
                "by_type": violation_types
            },
            "active_commitments": len(memory_store.get_active_commitments()),
            "report_generated": datetime.now().isoformat()
        }
    
    def _calculate_uptime(self) -> str:
        """Calculate system uptime"""
        start_time = datetime.fromisoformat(self.stats["uptime_start"])
        uptime = datetime.now() - start_time
        return str(uptime)
    
    def reset_statistics(self):
        """Reset compliance statistics"""
        self.stats = {
            "total_checks": 0,
            "violations_detected": 0,
            "actions_blocked": 0,
            "last_check": None,
            "uptime_start": datetime.now().isoformat()
        }
        
        memory_store.log_action(
            action_type="stats_reset",
            action_content="Compliance statistics reset",
            compliance_status="system_maintenance"
        )
    
    def set_compliance_level(self, level: ComplianceLevel):
        """Change the compliance level"""
        old_level = self.compliance_level
        self.compliance_level = level
        
        memory_store.log_action(
            action_type="compliance_level_changed",
            action_content=f"Compliance level changed from {old_level.value} to {level.value}",
            compliance_status="system_configuration",
            details={"old_level": old_level.value, "new_level": level.value}
        )

# Global instance for easy access
compliance_checker = AutomatedComplianceChecker()