"""
Enforcement Engine - Prevents actions that violate stated commitments
Real-time blocking and intervention system for commitment violations.
"""

import json
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass
from enum import Enum
import sqlite3
from pathlib import Path

from .memory_store import memory_store
from .behavioral_contract import behavioral_contract
from .compliance_checker import compliance_checker
from .audit_trail import audit_trail, AuditEventType, ComplianceStatus

class EnforcementAction(Enum):
    """Types of enforcement actions"""
    BLOCK = "block"
    WARN = "warn"
    LOG_ONLY = "log_only"
    REDIRECT = "redirect"
    REQUIRE_CONFIRMATION = "require_confirmation"

class ViolationSeverity(Enum):
    """Severity levels for violations"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class EnforcementRule:
    """Defines an enforcement rule"""
    rule_id: str
    name: str
    description: str
    pattern: str  # Pattern to match against actions
    action: EnforcementAction
    severity: ViolationSeverity
    commitment_ids: List[str]  # Related commitments
    active: bool = True
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

@dataclass
class EnforcementResult:
    """Result of an enforcement check"""
    allowed: bool
    action_taken: EnforcementAction
    violation_detected: bool
    violated_rules: List[EnforcementRule]
    message: str
    requires_user_confirmation: bool = False
    alternative_actions: List[str] = None
    
    def __post_init__(self):
        if self.alternative_actions is None:
            self.alternative_actions = []

class ActionInterceptor:
    """Intercepts and validates actions before execution"""
    
    def __init__(self):
        self.intercepted_functions: Dict[str, Callable] = {}
        self.bypass_tokens: Set[str] = set()
        self.active = True
    
    def register_function(self, function_name: str, original_function: Callable):
        """Register a function to be intercepted"""
        self.intercepted_functions[function_name] = original_function
    
    def intercept_call(self, function_name: str, *args, **kwargs):
        """Intercept and validate a function call"""
        if not self.active:
            return self.intercepted_functions[function_name](*args, **kwargs)
        
        # Check if this call should be allowed
        enforcement_result = enforcement_engine.check_action(
            action_type="function_call",
            action_details={
                "function_name": function_name,
                "args": str(args)[:200],  # Truncate for storage
                "kwargs": str(kwargs)[:200]
            }
        )
        
        if not enforcement_result.allowed:
            raise PermissionError(f"Action blocked by enforcement engine: {enforcement_result.message}")
        
        # Execute the original function
        return self.intercepted_functions[function_name](*args, **kwargs)
    
    def create_bypass_token(self, duration_minutes: int = 5) -> str:
        """Create a temporary bypass token"""
        import uuid
        token = str(uuid.uuid4())
        self.bypass_tokens.add(token)
        
        # Remove token after duration
        def remove_token():
            time.sleep(duration_minutes * 60)
            self.bypass_tokens.discard(token)
        
        threading.Thread(target=remove_token, daemon=True).start()
        return token

class EnforcementEngine:
    """
    Main enforcement engine that prevents actions violating commitments.
    Provides real-time blocking and intervention capabilities.
    """
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            project_root = Path(__file__).parent.parent
            enforcement_dir = project_root / "commitment_system" / "data"
            enforcement_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(enforcement_dir / "enforcement.db")
        
        self.db_path = db_path
        self.init_enforcement_database()
        
        # Core components
        self.action_interceptor = ActionInterceptor()
        self.enforcement_rules: List[EnforcementRule] = []
        self.active = True
        
        # Performance optimization
        self.rule_cache: Dict[str, List[EnforcementRule]] = {}
        self.cache_expiry = datetime.now()
        self.cache_duration = timedelta(minutes=5)
        
        # Statistics
        self.blocked_actions_count = 0
        self.warnings_issued_count = 0
        self.total_checks_count = 0
        
        # Load default rules
        self._load_default_rules()
        self._load_rules_from_database()
    
    def init_enforcement_database(self):
        """Initialize the enforcement database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS enforcement_rules (
                    rule_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    pattern TEXT NOT NULL,
                    action TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    commitment_ids TEXT DEFAULT '[]',
                    active INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS enforcement_events (
                    event_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    action_details TEXT DEFAULT '{}',
                    enforcement_result TEXT NOT NULL,
                    violated_rules TEXT DEFAULT '[]',
                    user_override INTEGER DEFAULT 0
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS enforcement_statistics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL,
                    metric_value INTEGER NOT NULL,
                    timestamp TEXT NOT NULL
                )
            """)
            
            conn.commit()
    
    def add_rule(self, rule: EnforcementRule) -> bool:
        """Add a new enforcement rule"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO enforcement_rules 
                    (rule_id, name, description, pattern, action, severity, 
                     commitment_ids, active, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    rule.rule_id,
                    rule.name,
                    rule.description,
                    rule.pattern,
                    rule.action.value,
                    rule.severity.value,
                    json.dumps(rule.commitment_ids),
                    1 if rule.active else 0,
                    rule.created_at
                ))
                conn.commit()
            
            # Update in-memory rules
            self.enforcement_rules.append(rule)
            self._invalidate_cache()
            
            # Log the rule addition
            audit_trail.log_event({
                "event_type": AuditEventType.SYSTEM_EVENT,
                "description": f"Enforcement rule added: {rule.name}",
                "compliance_status": ComplianceStatus.COMPLIANT,
                "context": {"rule_id": rule.rule_id}
            })
            
            return True
            
        except Exception as e:
            print(f"Error adding enforcement rule: {e}")
            return False
    
    def check_action(self, action_type: str, action_details: Dict[str, Any],
                    context: Dict[str, Any] = None) -> EnforcementResult:
        """
        Check if an action is allowed based on enforcement rules.
        This is the main entry point for enforcement checks.
        """
        self.total_checks_count += 1
        
        if not self.active:
            return EnforcementResult(
                allowed=True,
                action_taken=EnforcementAction.LOG_ONLY,
                violation_detected=False,
                violated_rules=[],
                message="Enforcement engine is disabled"
            )
        
        try:
            # Get applicable rules
            applicable_rules = self._get_applicable_rules(action_type, action_details)
            
            if not applicable_rules:
                return EnforcementResult(
                    allowed=True,
                    action_taken=EnforcementAction.LOG_ONLY,
                    violation_detected=False,
                    violated_rules=[],
                    message="No applicable enforcement rules"
                )
            
            # Check each rule
            violated_rules = []
            highest_severity = ViolationSeverity.LOW
            most_restrictive_action = EnforcementAction.LOG_ONLY
            
            for rule in applicable_rules:
                if self._rule_matches_action(rule, action_type, action_details):
                    violated_rules.append(rule)
                    
                    # Track highest severity and most restrictive action
                    if self._severity_level(rule.severity) > self._severity_level(highest_severity):
                        highest_severity = rule.severity
                    
                    if self._action_restrictiveness(rule.action) > self._action_restrictiveness(most_restrictive_action):
                        most_restrictive_action = rule.action
            
            # Determine final enforcement result
            if violated_rules:
                result = self._create_enforcement_result(
                    violated_rules, highest_severity, most_restrictive_action, action_details
                )
                
                # Log the enforcement event
                self._log_enforcement_event(action_type, action_details, result)
                
                # Update statistics
                if result.action_taken == EnforcementAction.BLOCK:
                    self.blocked_actions_count += 1
                elif result.action_taken == EnforcementAction.WARN:
                    self.warnings_issued_count += 1
                
                return result
            
            else:
                return EnforcementResult(
                    allowed=True,
                    action_taken=EnforcementAction.LOG_ONLY,
                    violation_detected=False,
                    violated_rules=[],
                    message="Action allowed - no violations detected"
                )
                
        except Exception as e:
            # Fail-safe: log error but allow action
            audit_trail.log_action(
                f"Enforcement check error: {str(e)}",
                action_type="enforcement_error",
                compliance_status=ComplianceStatus.UNKNOWN,
                severity="high"
            )
            
            return EnforcementResult(
                allowed=True,
                action_taken=EnforcementAction.LOG_ONLY,
                violation_detected=False,
                violated_rules=[],
                message=f"Enforcement check failed: {str(e)}"
            )
    
    def _get_applicable_rules(self, action_type: str, action_details: Dict[str, Any]) -> List[EnforcementRule]:
        """Get rules that might apply to this action"""
        # Use cache if available and not expired
        cache_key = f"{action_type}_{hash(str(action_details))}"
        
        if (cache_key in self.rule_cache and 
            datetime.now() < self.cache_expiry):
            return self.rule_cache[cache_key]
        
        # Filter rules based on action type and active status
        applicable_rules = [
            rule for rule in self.enforcement_rules
            if rule.active and (
                action_type in rule.pattern or
                rule.pattern == "*" or
                any(keyword in str(action_details).lower() 
                    for keyword in rule.pattern.split(","))
            )
        ]
        
        # Cache the result
        self.rule_cache[cache_key] = applicable_rules
        
        return applicable_rules
    
    def _rule_matches_action(self, rule: EnforcementRule, action_type: str, 
                           action_details: Dict[str, Any]) -> bool:
        """Check if a specific rule matches the action"""
        try:
            # Simple pattern matching - can be enhanced with regex
            pattern_parts = rule.pattern.lower().split(",")
            action_string = f"{action_type} {str(action_details)}".lower()
            
            return any(part.strip() in action_string for part in pattern_parts)
            
        except Exception as e:
            print(f"Error matching rule {rule.rule_id}: {e}")
            return False
    
    def _create_enforcement_result(self, violated_rules: List[EnforcementRule],
                                 severity: ViolationSeverity, action: EnforcementAction,
                                 action_details: Dict[str, Any]) -> EnforcementResult:
        """Create an enforcement result based on violated rules"""
        
        # Determine if action should be allowed
        allowed = action not in [EnforcementAction.BLOCK]
        
        # Create appropriate message
        rule_names = [rule.name for rule in violated_rules]
        message = f"Violation detected in rules: {', '.join(rule_names)}"
        
        if action == EnforcementAction.BLOCK:
            message = f"Action BLOCKED: {message}"
        elif action == EnforcementAction.WARN:
            message = f"WARNING: {message}"
        elif action == EnforcementAction.REQUIRE_CONFIRMATION:
            message = f"User confirmation required: {message}"
        
        # Generate alternative actions if blocked
        alternative_actions = []
        if action == EnforcementAction.BLOCK:
            alternative_actions = self._generate_alternatives(action_details, violated_rules)
        
        return EnforcementResult(
            allowed=allowed,
            action_taken=action,
            violation_detected=True,
            violated_rules=violated_rules,
            message=message,
            requires_user_confirmation=(action == EnforcementAction.REQUIRE_CONFIRMATION),
            alternative_actions=alternative_actions
        )
    
    def _generate_alternatives(self, action_details: Dict[str, Any], 
                             violated_rules: List[EnforcementRule]) -> List[str]:
        """Generate alternative actions when an action is blocked"""
        alternatives = []
        
        # Generic alternatives
        alternatives.append("Request explicit user permission for this action")
        alternatives.append("Modify the action to comply with stated commitments")
        alternatives.append("Log the attempted action for later review")
        
        # Rule-specific alternatives
        for rule in violated_rules:
            if "autonomous" in rule.pattern.lower():
                alternatives.append("Wait for explicit user instruction before proceeding")
            if "commitment" in rule.pattern.lower():
                alternatives.append("Review and update relevant commitments first")
        
        return alternatives[:3]  # Limit to top 3 alternatives
    
    def _severity_level(self, severity: ViolationSeverity) -> int:
        """Convert severity to numeric level for comparison"""
        levels = {
            ViolationSeverity.LOW: 1,
            ViolationSeverity.MEDIUM: 2,
            ViolationSeverity.HIGH: 3,
            ViolationSeverity.CRITICAL: 4
        }
        return levels.get(severity, 1)
    
    def _action_restrictiveness(self, action: EnforcementAction) -> int:
        """Convert action to numeric restrictiveness level"""
        levels = {
            EnforcementAction.LOG_ONLY: 1,
            EnforcementAction.WARN: 2,
            EnforcementAction.REQUIRE_CONFIRMATION: 3,
            EnforcementAction.REDIRECT: 4,
            EnforcementAction.BLOCK: 5
        }
        return levels.get(action, 1)
    
    def _log_enforcement_event(self, action_type: str, action_details: Dict[str, Any],
                             result: EnforcementResult):
        """Log an enforcement event to the database and audit trail"""
        try:
            event_id = f"enf_{int(time.time() * 1000)}"
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO enforcement_events 
                    (event_id, timestamp, action_type, action_details, 
                     enforcement_result, violated_rules, user_override)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    event_id,
                    datetime.now().isoformat(),
                    action_type,
                    json.dumps(action_details),
                    json.dumps({
                        "allowed": result.allowed,
                        "action_taken": result.action_taken.value,
                        "message": result.message
                    }),
                    json.dumps([rule.rule_id for rule in result.violated_rules]),
                    0  # No user override by default
                ))
                conn.commit()
            
            # Also log to audit trail
            audit_trail.log_action(
                f"Enforcement check: {result.message}",
                action_type="enforcement_check",
                compliance_status=ComplianceStatus.VIOLATION if result.violation_detected else ComplianceStatus.COMPLIANT,
                context={
                    "original_action_type": action_type,
                    "enforcement_action": result.action_taken.value,
                    "violated_rules": len(result.violated_rules)
                },
                severity="high" if result.action_taken == EnforcementAction.BLOCK else "medium"
            )
            
        except Exception as e:
            print(f"Error logging enforcement event: {e}")
    
    def _load_default_rules(self):
        """Load default enforcement rules"""
        default_rules = [
            EnforcementRule(
                rule_id="no_autonomous_action",
                name="No Autonomous Actions",
                description="Prevent any autonomous actions without explicit user instruction",
                pattern="autonomous,automatic,proactive,initiative",
                action=EnforcementAction.BLOCK,
                severity=ViolationSeverity.HIGH,
                commitment_ids=["core_commitment_1"]
            ),
            EnforcementRule(
                rule_id="exact_instruction_only",
                name="Exact Instructions Only",
                description="Only execute exactly what user instructs",
                pattern="interpretation,assumption,inference,thinking_ahead",
                action=EnforcementAction.WARN,
                severity=ViolationSeverity.MEDIUM,
                commitment_ids=["core_commitment_2"]
            ),
            EnforcementRule(
                rule_id="no_promises",
                name="No Promise Making",
                description="Prevent making promises or commitments without user approval",
                pattern="promise,commit,guarantee,ensure,will_do",
                action=EnforcementAction.REQUIRE_CONFIRMATION,
                severity=ViolationSeverity.HIGH,
                commitment_ids=["core_commitment_3"]
            )
        ]
        
        for rule in default_rules:
            if not any(r.rule_id == rule.rule_id for r in self.enforcement_rules):
                self.enforcement_rules.append(rule)
    
    def _load_rules_from_database(self):
        """Load enforcement rules from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT rule_id, name, description, pattern, action, severity,
                           commitment_ids, active, created_at
                    FROM enforcement_rules
                    WHERE active = 1
                """)
                
                for row in cursor.fetchall():
                    rule = EnforcementRule(
                        rule_id=row[0],
                        name=row[1],
                        description=row[2],
                        pattern=row[3],
                        action=EnforcementAction(row[4]),
                        severity=ViolationSeverity(row[5]),
                        commitment_ids=json.loads(row[6]),
                        active=bool(row[7]),
                        created_at=row[8]
                    )
                    
                    # Only add if not already in memory
                    if not any(r.rule_id == rule.rule_id for r in self.enforcement_rules):
                        self.enforcement_rules.append(rule)
                        
        except Exception as e:
            print(f"Error loading rules from database: {e}")
    
    def _invalidate_cache(self):
        """Invalidate the rule cache"""
        self.rule_cache.clear()
        self.cache_expiry = datetime.now()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get enforcement engine statistics"""
        return {
            "total_checks": self.total_checks_count,
            "blocked_actions": self.blocked_actions_count,
            "warnings_issued": self.warnings_issued_count,
            "active_rules": len([r for r in self.enforcement_rules if r.active]),
            "enforcement_active": self.active,
            "block_rate": self.blocked_actions_count / max(1, self.total_checks_count)
        }
    
    def enable(self):
        """Enable the enforcement engine"""
        self.active = True
        audit_trail.log_action(
            "Enforcement engine enabled",
            action_type="system_control",
            compliance_status=ComplianceStatus.COMPLIANT
        )
    
    def disable(self):
        """Disable the enforcement engine"""
        self.active = False
        audit_trail.log_action(
            "Enforcement engine disabled",
            action_type="system_control",
            compliance_status=ComplianceStatus.COMPLIANT
        )

# Global instance for easy access
enforcement_engine = EnforcementEngine()