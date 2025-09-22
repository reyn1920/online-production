"""
Behavioral Contract Framework for AI Commitment Enforcement
Automatically tracks and enforces all stated commitments and behavioral rules.
"""

import re
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum

from .memory_store import memory_store, Commitment

class ContractViolationType(Enum):
    """Types of contract violations"""
    DIRECT_VIOLATION = "direct_violation"
    IMPLICIT_VIOLATION = "implicit_violation"
    PATTERN_VIOLATION = "pattern_violation"
    COMMITMENT_BREACH = "commitment_breach"

@dataclass
class BehavioralRule:
    """Represents a behavioral rule or constraint"""
    id: str
    rule_type: str
    pattern: str
    description: str
    enforcement_level: str = "strict"  # strict, moderate, advisory
    is_active: bool = True
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

@dataclass
class ContractViolation:
    """Represents a detected contract violation"""
    violation_type: ContractViolationType
    rule_id: str
    commitment_id: Optional[str]
    description: str
    severity: str
    timestamp: str
    action_blocked: bool = False

class BehavioralContractFramework:
    """
    Framework for creating, managing, and enforcing behavioral contracts.
    Automatically parses commitments and creates enforceable rules.
    """
    
    def __init__(self):
        self.rules: Dict[str, BehavioralRule] = {}
        self.violation_handlers: Dict[str, Callable] = {}
        self.load_existing_rules()
        self.setup_default_rules()
    
    def setup_default_rules(self):
        """Setup default behavioral rules based on common AI commitments"""
        default_rules = [
            BehavioralRule(
                id="no_autonomous_action",
                rule_type="prohibition",
                pattern=r"(I will|I'll)\s+(wait|stop|not\s+act|be\s+idle|do\s+nothing)",
                description="Prohibits autonomous actions when commitment to wait/stop is made",
                enforcement_level="strict"
            ),
            BehavioralRule(
                id="follow_exact_instructions",
                rule_type="requirement",
                pattern=r"(I will|I'll)\s+(follow|do)\s+(exactly|only|precisely)",
                description="Requires following exact instructions when committed",
                enforcement_level="strict"
            ),
            BehavioralRule(
                id="no_interpretation",
                rule_type="prohibition",
                pattern=r"(I will|I'll)\s+(not\s+interpret|avoid\s+thinking|stop\s+analyzing)",
                description="Prohibits interpretation when commitment to literal following is made",
                enforcement_level="strict"
            ),
            BehavioralRule(
                id="ask_before_acting",
                rule_type="requirement",
                pattern=r"(I will|I'll)\s+(ask|request|wait\s+for)\s+(permission|approval|instructions)",
                description="Requires asking permission before acting when committed",
                enforcement_level="strict"
            ),
            BehavioralRule(
                id="no_promises_without_action",
                rule_type="requirement",
                pattern=r"(I will|I'll|I\s+promise|I\s+commit)",
                description="Requires following through on all promises and commitments",
                enforcement_level="strict"
            )
        ]
        
        for rule in default_rules:
            self.add_rule(rule)
    
    def add_rule(self, rule: BehavioralRule) -> bool:
        """Add a new behavioral rule to the framework"""
        try:
            self.rules[rule.id] = rule
            # Store in persistent memory
            memory_store.log_action(
                action_type="rule_added",
                action_content=f"Added rule: {rule.description}",
                compliance_status="compliant",
                details={"rule_id": rule.id, "rule_type": rule.rule_type}
            )
            return True
        except Exception as e:
            print(f"Error adding rule: {e}")
            return False
    
    def parse_commitments_from_text(self, text: str, context: str = "") -> List[Commitment]:
        """
        Parse commitments from text using natural language processing.
        Identifies promises, commitments, and behavioral statements.
        """
        commitments = []
        
        # Patterns for identifying commitments
        commitment_patterns = [
            r"I will (not )?([^.!?]+)",
            r"I'll (not )?([^.!?]+)",
            r"I promise to (not )?([^.!?]+)",
            r"I commit to (not )?([^.!?]+)",
            r"I won't ([^.!?]+)",
            r"I will never ([^.!?]+)",
            r"I am going to (not )?([^.!?]+)",
            r"I'm going to (not )?([^.!?]+)",
            r"I will stop ([^.!?]+)",
            r"I will avoid ([^.!?]+)",
            r"I will only ([^.!?]+)",
            r"I will wait ([^.!?]+)",
            r"I will be ([^.!?]+)"
        ]
        
        for pattern in commitment_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                full_match = match.group(0)
                commitment_id = hashlib.md5(
                    (full_match + context + str(datetime.now())).encode()
                ).hexdigest()[:12]
                
                commitment = Commitment(
                    id=commitment_id,
                    content=full_match.strip(),
                    timestamp=datetime.now().isoformat(),
                    context=context,
                    status="active",
                    enforcement_level="strict"
                )
                
                commitments.append(commitment)
                # Store in persistent memory
                memory_store.store_commitment(commitment)
        
        return commitments
    
    def check_action_compliance(self, action_description: str, 
                              action_type: str = "general") -> List[ContractViolation]:
        """
        Check if a proposed action complies with all active commitments and rules.
        Returns list of violations if any are found.
        """
        violations = []
        active_commitments = memory_store.get_active_commitments()
        
        # Check against active commitments
        for commitment in active_commitments:
            violation = self._check_commitment_compliance(
                action_description, commitment, action_type
            )
            if violation:
                violations.append(violation)
        
        # Check against behavioral rules
        for rule in self.rules.values():
            if rule.is_active:
                violation = self._check_rule_compliance(
                    action_description, rule, action_type
                )
                if violation:
                    violations.append(violation)
        
        # Log the compliance check
        compliance_status = "violation" if violations else "compliant"
        memory_store.log_action(
            action_type="compliance_check",
            action_content=action_description,
            compliance_status=compliance_status,
            details={
                "violations_count": len(violations),
                "action_type": action_type,
                "violations": [v.description for v in violations]
            }
        )
        
        return violations
    
    def _check_commitment_compliance(self, action: str, commitment: Commitment, 
                                   action_type: str) -> Optional[ContractViolation]:
        """Check if an action violates a specific commitment"""
        commitment_text = commitment.content.lower()
        action_text = action.lower()
        
        # Check for direct violations of "I will not" commitments
        if "will not" in commitment_text or "won't" in commitment_text:
            prohibited_action = re.search(r"will not (.+)|won't (.+)", commitment_text)
            if prohibited_action:
                prohibited = prohibited_action.group(1) or prohibited_action.group(2)
                if prohibited.strip() in action_text:
                    return ContractViolation(
                        violation_type=ContractViolationType.DIRECT_VIOLATION,
                        rule_id="commitment_violation",
                        commitment_id=commitment.id,
                        description=f"Action '{action}' violates commitment: {commitment.content}",
                        severity="high",
                        timestamp=datetime.now().isoformat(),
                        action_blocked=True
                    )
        
        # Check for violations of "I will only" commitments
        if "will only" in commitment_text:
            allowed_action = re.search(r"will only (.+)", commitment_text)
            if allowed_action:
                allowed = allowed_action.group(1).strip()
                if allowed not in action_text and action_type != "compliance_check":
                    return ContractViolation(
                        violation_type=ContractViolationType.COMMITMENT_BREACH,
                        rule_id="only_commitment_violation",
                        commitment_id=commitment.id,
                        description=f"Action '{action}' violates 'only' commitment: {commitment.content}",
                        severity="high",
                        timestamp=datetime.now().isoformat(),
                        action_blocked=True
                    )
        
        # Check for violations of "I will wait" commitments
        if "will wait" in commitment_text or "will be idle" in commitment_text:
            if action_type not in ["compliance_check", "waiting", "idle"]:
                return ContractViolation(
                    violation_type=ContractViolationType.COMMITMENT_BREACH,
                    rule_id="wait_commitment_violation",
                    commitment_id=commitment.id,
                    description=f"Action '{action}' violates waiting commitment: {commitment.content}",
                    severity="high",
                    timestamp=datetime.now().isoformat(),
                    action_blocked=True
                )
        
        return None
    
    def _check_rule_compliance(self, action: str, rule: BehavioralRule, 
                             action_type: str) -> Optional[ContractViolation]:
        """Check if an action violates a specific behavioral rule"""
        # This is a simplified rule checking - in practice, this would be more sophisticated
        if rule.rule_type == "prohibition":
            if re.search(rule.pattern, action, re.IGNORECASE):
                return ContractViolation(
                    violation_type=ContractViolationType.PATTERN_VIOLATION,
                    rule_id=rule.id,
                    commitment_id=None,
                    description=f"Action '{action}' violates rule: {rule.description}",
                    severity="medium",
                    timestamp=datetime.now().isoformat(),
                    action_blocked=rule.enforcement_level == "strict"
                )
        
        return None
    
    def enforce_compliance(self, violations: List[ContractViolation]) -> bool:
        """
        Enforce compliance by blocking actions that violate commitments.
        Returns True if action should be blocked, False if it can proceed.
        """
        blocking_violations = [v for v in violations if v.action_blocked]
        
        if blocking_violations:
            # Log enforcement action
            memory_store.log_action(
                action_type="enforcement_action",
                action_content="Action blocked due to contract violations",
                compliance_status="blocked",
                details={
                    "violations": [v.description for v in blocking_violations],
                    "violation_count": len(blocking_violations)
                }
            )
            return True
        
        return False
    
    def get_active_commitments_summary(self) -> Dict[str, Any]:
        """Get a summary of all active commitments and their status"""
        active_commitments = memory_store.get_active_commitments()
        
        return {
            "total_commitments": len(active_commitments),
            "commitments": [
                {
                    "id": c.id,
                    "content": c.content,
                    "timestamp": c.timestamp,
                    "enforcement_level": c.enforcement_level
                }
                for c in active_commitments
            ],
            "active_rules": len([r for r in self.rules.values() if r.is_active]),
            "last_updated": datetime.now().isoformat()
        }
    
    def load_existing_rules(self):
        """Load existing rules from persistent storage"""
        # This would load rules from the database in a real implementation
        pass

# Global instance for easy access
behavioral_contract = BehavioralContractFramework()