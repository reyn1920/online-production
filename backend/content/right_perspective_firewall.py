#!/usr/bin/env python3
"""
Right Perspective Content Firewall

Implements strict content separation rules to ensure "The Right Perspective" channel
operates in complete isolation from all other channels, preventing:
- Cross-promotion
- Content repurposing 
- Asset sharing
- Data leakage
"""

import sqlite3
import json
import logging
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum

try:
    from .universal_channel_protocol import get_protocol, ChannelType, ContentFirewallLevel
except ImportError:
    # Fallback for development
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from universal_channel_protocol import get_protocol, ChannelType, ContentFirewallLevel

class FirewallViolationType(Enum):
    CROSS_PROMOTION = "cross_promotion"
    CONTENT_REPURPOSING = "content_repurposing"
    ASSET_SHARING = "asset_sharing"
    DATA_LEAKAGE = "data_leakage"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    PERSONA_CONTAMINATION = "persona_contamination"
    KNOWLEDGE_BASE_MIXING = "knowledge_base_mixing"

class FirewallAction(Enum):
    BLOCK = "block"
    WARN = "warn"
    LOG = "log"
    QUARANTINE = "quarantine"

@dataclass
class FirewallRule:
    """Represents a firewall rule"""
    rule_id: str
    rule_name: str
    violation_type: FirewallViolationType
    source_channel: str
    target_channel: str
    action: FirewallAction
    severity: str
    description: str
    is_active: bool
    created_at: datetime

@dataclass
class FirewallViolation:
    """Represents a firewall violation incident"""
    violation_id: str
    rule_id: str
    violation_type: FirewallViolationType
    source_channel: str
    target_channel: str
    content_id: str
    violation_details: Dict[str, Any]
    action_taken: FirewallAction
    severity: str
    detected_at: datetime
    resolved_at: Optional[datetime]

class RightPerspectiveFirewall:
    """
    Enforces strict content separation for The Right Perspective channel
    """
    
    # The protected channel ID - this should never change
    RIGHT_PERSPECTIVE_CHANNEL_ID = "right_perspective"
    
    def __init__(self, db_path: str = "data/right_perspective.db", protocol=None):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.protocol = protocol  # Accept protocol as parameter to avoid circular dependency
        self._initialize_firewall_tables()
        self._setup_default_rules()
        
        # Cache for performance
        self._rule_cache = {}
        self._violation_cache = []
        
        self.logger.info("Right Perspective Firewall initialized with maximum security")
    
    def set_protocol(self, protocol):
        """Set the protocol instance after initialization to avoid circular dependency"""
        self.protocol = protocol
    
    def _initialize_firewall_tables(self):
        """Initialize firewall database tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Firewall rules table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS firewall_rules (
                    rule_id TEXT PRIMARY KEY,
                    rule_name TEXT NOT NULL,
                    violation_type TEXT NOT NULL,
                    source_channel TEXT NOT NULL,
                    target_channel TEXT NOT NULL,
                    action TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    description TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Firewall violations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS firewall_violations (
                    violation_id TEXT PRIMARY KEY,
                    rule_id TEXT NOT NULL,
                    violation_type TEXT NOT NULL,
                    source_channel TEXT NOT NULL,
                    target_channel TEXT NOT NULL,
                    content_id TEXT,
                    violation_details TEXT,
                    action_taken TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TIMESTAMP,
                    resolution_notes TEXT,
                    FOREIGN KEY (rule_id) REFERENCES firewall_rules (rule_id)
                )
            """)
            
            # Content quarantine table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS content_quarantine (
                    quarantine_id TEXT PRIMARY KEY,
                    content_id TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    source_channel TEXT NOT NULL,
                    target_channel TEXT NOT NULL,
                    content_hash TEXT,
                    quarantine_reason TEXT,
                    quarantined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    released_at TIMESTAMP,
                    status TEXT DEFAULT 'quarantined'
                )
            """)
            
            # Asset tracking table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS asset_tracking (
                    asset_id TEXT PRIMARY KEY,
                    asset_type TEXT NOT NULL,
                    asset_path TEXT,
                    asset_hash TEXT,
                    owner_channel TEXT NOT NULL,
                    access_permissions TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_accessed TIMESTAMP,
                    access_count INTEGER DEFAULT 0
                )
            """)
            
            # Cross-reference monitoring
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cross_reference_monitor (
                    reference_id TEXT PRIMARY KEY,
                    source_content_id TEXT NOT NULL,
                    target_content_id TEXT,
                    reference_type TEXT NOT NULL,
                    source_channel TEXT NOT NULL,
                    target_channel TEXT,
                    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_violation BOOLEAN DEFAULT 0,
                    action_taken TEXT
                )
            """)
            
            conn.commit()
    
    def _setup_default_rules(self):
        """Setup default firewall rules for Right Perspective protection"""
        default_rules = [
            {
                "rule_name": "Block All Cross-Promotion to Right Perspective",
                "violation_type": FirewallViolationType.CROSS_PROMOTION,
                "source_channel": "*",  # Any channel
                "target_channel": self.RIGHT_PERSPECTIVE_CHANNEL_ID,
                "action": FirewallAction.BLOCK,
                "severity": "CRITICAL",
                "description": "Prevents any channel from creating content that mentions or links to Right Perspective"
            },
            {
                "rule_name": "Block All Cross-Promotion from Right Perspective",
                "violation_type": FirewallViolationType.CROSS_PROMOTION,
                "source_channel": self.RIGHT_PERSPECTIVE_CHANNEL_ID,
                "target_channel": "*",  # Any channel
                "action": FirewallAction.BLOCK,
                "severity": "CRITICAL",
                "description": "Prevents Right Perspective from promoting other channels (maintains one-way rule)"
            },
            {
                "rule_name": "Block Content Repurposing from Right Perspective",
                "violation_type": FirewallViolationType.CONTENT_REPURPOSING,
                "source_channel": self.RIGHT_PERSPECTIVE_CHANNEL_ID,
                "target_channel": "*",
                "action": FirewallAction.BLOCK,
                "severity": "CRITICAL",
                "description": "Prevents repurposing of Right Perspective content for other channels"
            },
            {
                "rule_name": "Block Asset Sharing from Right Perspective",
                "violation_type": FirewallViolationType.ASSET_SHARING,
                "source_channel": self.RIGHT_PERSPECTIVE_CHANNEL_ID,
                "target_channel": "*",
                "action": FirewallAction.BLOCK,
                "severity": "CRITICAL",
                "description": "Prevents sharing of Right Perspective scripts, audio, or video assets"
            },
            {
                "rule_name": "Block Knowledge Base Mixing",
                "violation_type": FirewallViolationType.KNOWLEDGE_BASE_MIXING,
                "source_channel": self.RIGHT_PERSPECTIVE_CHANNEL_ID,
                "target_channel": "*",
                "action": FirewallAction.BLOCK,
                "severity": "HIGH",
                "description": "Prevents Right Perspective knowledge base data from being used by other channels"
            },
            {
                "rule_name": "Block Persona Contamination",
                "violation_type": FirewallViolationType.PERSONA_CONTAMINATION,
                "source_channel": self.RIGHT_PERSPECTIVE_CHANNEL_ID,
                "target_channel": "*",
                "action": FirewallAction.BLOCK,
                "severity": "HIGH",
                "description": "Prevents Right Perspective persona characteristics from influencing other channels"
            }
        ]
        
        for rule_data in default_rules:
            self._create_firewall_rule(**rule_data)
    
    def _create_firewall_rule(self, rule_name: str, violation_type: FirewallViolationType,
                            source_channel: str, target_channel: str, action: FirewallAction,
                            severity: str, description: str) -> str:
        """Create a new firewall rule"""
        rule_id = f"rule_{hashlib.md5(f'{rule_name}_{source_channel}_{target_channel}'.encode()).hexdigest()[:8]}"
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO firewall_rules
                (rule_id, rule_name, violation_type, source_channel, target_channel, 
                 action, severity, description, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
            """, (
                rule_id, rule_name, violation_type.value, source_channel, target_channel,
                action.value, severity, description, 
                datetime.now().isoformat(), datetime.now().isoformat()
            ))
            
            conn.commit()
        
        # Update cache
        self._rule_cache[rule_id] = {
            'rule_name': rule_name,
            'violation_type': violation_type,
            'source_channel': source_channel,
            'target_channel': target_channel,
            'action': action,
            'severity': severity,
            'description': description
        }
        
        return rule_id
    
    def check_cross_promotion_violation(self, source_channel: str, content: str, 
                                      target_channels: List[str] = None) -> Tuple[bool, List[str]]:
        """Check if content violates cross-promotion rules"""
        violations = []
        
        # Check if Right Perspective is mentioned in content from other channels
        if (source_channel != self.RIGHT_PERSPECTIVE_CHANNEL_ID and 
            self._contains_right_perspective_reference(content)):
            violations.append(f"Content from {source_channel} contains reference to Right Perspective")
        
        # Check if Right Perspective is trying to promote other channels
        if source_channel == self.RIGHT_PERSPECTIVE_CHANNEL_ID:
            other_channel_refs = self._extract_channel_references(content)
            if other_channel_refs:
                violations.append(f"Right Perspective content contains references to other channels: {other_channel_refs}")
        
        # Check target channels if specified
        if target_channels:
            for target in target_channels:
                if (source_channel != self.RIGHT_PERSPECTIVE_CHANNEL_ID and 
                    target == self.RIGHT_PERSPECTIVE_CHANNEL_ID):
                    violations.append(f"Attempted cross-promotion from {source_channel} to Right Perspective")
        
        return len(violations) > 0, violations
    
    def check_content_repurposing_violation(self, source_channel: str, content_id: str, 
                                          target_channel: str, content_hash: str = None) -> Tuple[bool, str]:
        """Check if content repurposing violates firewall rules"""
        # Block any repurposing from Right Perspective
        if source_channel == self.RIGHT_PERSPECTIVE_CHANNEL_ID:
            return True, f"Content repurposing from Right Perspective to {target_channel} is strictly prohibited"
        
        # Block any repurposing to Right Perspective
        if target_channel == self.RIGHT_PERSPECTIVE_CHANNEL_ID:
            return True, f"Content repurposing from {source_channel} to Right Perspective is strictly prohibited"
        
        # Check for content hash matches if provided
        if content_hash and source_channel == self.RIGHT_PERSPECTIVE_CHANNEL_ID:
            if self._is_right_perspective_content(content_hash):
                return True, "Attempted repurposing of Right Perspective content detected via content hash"
        
        return False, ""
    
    def check_asset_sharing_violation(self, asset_path: str, source_channel: str, 
                                    target_channel: str, asset_type: str) -> Tuple[bool, str]:
        """Check if asset sharing violates firewall rules"""
        # Block any asset sharing from Right Perspective
        if source_channel == self.RIGHT_PERSPECTIVE_CHANNEL_ID:
            return True, f"Asset sharing from Right Perspective ({asset_type}: {asset_path}) is strictly prohibited"
        
        # Block any asset sharing to Right Perspective
        if target_channel == self.RIGHT_PERSPECTIVE_CHANNEL_ID:
            return True, f"Asset sharing to Right Perspective from {source_channel} is strictly prohibited"
        
        # Check if asset belongs to Right Perspective
        if self._is_right_perspective_asset(asset_path):
            return True, f"Attempted sharing of Right Perspective asset ({asset_path}) detected"
        
        return False, ""
    
    def check_knowledge_base_access(self, requesting_channel: str, knowledge_source: str, 
                                  data_type: str) -> Tuple[bool, str]:
        """Check if knowledge base access violates firewall rules"""
        # Block access to Right Perspective knowledge base
        if (requesting_channel != self.RIGHT_PERSPECTIVE_CHANNEL_ID and 
            self._is_right_perspective_knowledge(knowledge_source)):
            return True, f"Access to Right Perspective knowledge base denied for {requesting_channel}"
        
        # Block Right Perspective from accessing other knowledge bases (maintain isolation)
        if (requesting_channel == self.RIGHT_PERSPECTIVE_CHANNEL_ID and 
            not self._is_right_perspective_knowledge(knowledge_source)):
            return True, f"Right Perspective access to external knowledge base ({knowledge_source}) blocked to maintain isolation"
        
        return False, ""
    
    def check_persona_contamination(self, source_channel: str, target_channel: str, 
                                  persona_elements: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Check if persona elements violate isolation rules"""
        violations = []
        
        # Block Right Perspective persona from influencing others
        if source_channel == self.RIGHT_PERSPECTIVE_CHANNEL_ID:
            violations.append(f"Right Perspective persona elements cannot be used by {target_channel}")
        
        # Block other personas from influencing Right Perspective
        if target_channel == self.RIGHT_PERSPECTIVE_CHANNEL_ID:
            violations.append(f"External persona elements from {source_channel} cannot influence Right Perspective")
        
        # Check for specific Right Perspective characteristics
        rp_characteristics = self._get_right_perspective_characteristics()
        for element_key, element_value in persona_elements.items():
            if self._contains_rp_characteristics(element_value, rp_characteristics):
                violations.append(f"Persona element '{element_key}' contains Right Perspective characteristics")
        
        return len(violations) > 0, violations
    
    def log_violation(self, violation_type: FirewallViolationType, source_channel: str, 
                     target_channel: str, content_id: str = None, 
                     violation_details: Dict[str, Any] = None) -> str:
        """Log a firewall violation"""
        violation_id = f"violation_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5(f'{source_channel}_{target_channel}'.encode()).hexdigest()[:8]}"
        
        # Find matching rule
        rule_id = self._find_matching_rule(violation_type, source_channel, target_channel)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO firewall_violations
                (violation_id, rule_id, violation_type, source_channel, target_channel, 
                 content_id, violation_details, action_taken, severity, detected_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                violation_id, rule_id, violation_type.value, source_channel, target_channel,
                content_id, json.dumps(violation_details or {}), 
                FirewallAction.BLOCK.value, "CRITICAL", datetime.now().isoformat()
            ))
            
            conn.commit()
        
        # Log to system logger
        self.logger.critical(
            f"FIREWALL VIOLATION: {violation_type.value} - {source_channel} -> {target_channel} "
            f"(Content: {content_id}, Violation ID: {violation_id})"
        )
        
        return violation_id
    
    def quarantine_content(self, content_id: str, content_type: str, source_channel: str, 
                          target_channel: str, reason: str) -> str:
        """Quarantine content that violates firewall rules"""
        quarantine_id = f"quarantine_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5(content_id.encode()).hexdigest()[:8]}"
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO content_quarantine
                (quarantine_id, content_id, content_type, source_channel, target_channel, 
                 quarantine_reason, quarantined_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'quarantined')
            """, (
                quarantine_id, content_id, content_type, source_channel, target_channel,
                reason, datetime.now().isoformat()
            ))
            
            conn.commit()
        
        self.logger.warning(f"Content quarantined: {content_id} (Reason: {reason})")
        return quarantine_id
    
    def track_asset(self, asset_path: str, asset_type: str, owner_channel: str, 
                   asset_hash: str = None) -> str:
        """Track asset ownership for firewall enforcement"""
        asset_id = f"asset_{hashlib.md5(f'{asset_path}_{owner_channel}'.encode()).hexdigest()[:12]}"
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO asset_tracking
                (asset_id, asset_type, asset_path, asset_hash, owner_channel, 
                 access_permissions, created_at, access_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0)
            """, (
                asset_id, asset_type, asset_path, asset_hash, owner_channel,
                json.dumps({"owner_only": True}), datetime.now().isoformat()
            ))
            
            conn.commit()
        
        return asset_id
    
    def validate_content_creation(self, channel_id: str, content_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate content creation against firewall rules"""
        violations = []
        
        # Check cross-promotion
        content_text = str(content_data.get('script', '')) + str(content_data.get('title', '')) + str(content_data.get('description', ''))
        is_violation, cross_promo_violations = self.check_cross_promotion_violation(channel_id, content_text)
        if is_violation:
            violations.extend(cross_promo_violations)
        
        # Check asset usage
        assets = content_data.get('assets', [])
        for asset in assets:
            asset_path = asset.get('path', '')
            asset_type = asset.get('type', '')
            is_violation, violation_msg = self.check_asset_sharing_violation(
                asset_path, asset.get('source_channel', channel_id), channel_id, asset_type
            )
            if is_violation:
                violations.append(violation_msg)
        
        # Check knowledge base usage
        knowledge_sources = content_data.get('knowledge_sources', [])
        for source in knowledge_sources:
            is_violation, violation_msg = self.check_knowledge_base_access(
                channel_id, source.get('source_id', ''), source.get('data_type', '')
            )
            if is_violation:
                violations.append(violation_msg)
        
        return len(violations) == 0, violations
    
    def _contains_right_perspective_reference(self, content: str) -> bool:
        """Check if content contains references to Right Perspective"""
        rp_keywords = [
            "right perspective", "rightperspective", "the right perspective",
            "right-perspective", "right_perspective", "@rightperspective"
        ]
        
        content_lower = content.lower()
        return any(keyword in content_lower for keyword in rp_keywords)
    
    def _extract_channel_references(self, content: str) -> List[str]:
        """Extract references to other channels from content"""
        # This would be enhanced with actual channel name detection
        # For now, look for common patterns
        import re
        
        patterns = [
            r'@(\w+)',  # @mentions
            r'channel[:\s]+(\w+)',  # "channel: name" or "channel name"
            r'subscribe to (\w+)',  # "subscribe to channel"
            r'check out (\w+)'  # "check out channel"
        ]
        
        references = []
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            references.extend(matches)
        
        return list(set(references))  # Remove duplicates
    
    def _is_right_perspective_content(self, content_hash: str) -> bool:
        """Check if content hash belongs to Right Perspective"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM asset_tracking 
                WHERE asset_hash = ? AND owner_channel = ?
            """, (content_hash, self.RIGHT_PERSPECTIVE_CHANNEL_ID))
            
            return cursor.fetchone()[0] > 0
    
    def _is_right_perspective_asset(self, asset_path: str) -> bool:
        """Check if asset belongs to Right Perspective"""
        # Check database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM asset_tracking 
                WHERE asset_path = ? AND owner_channel = ?
            """, (asset_path, self.RIGHT_PERSPECTIVE_CHANNEL_ID))
            
            if cursor.fetchone()[0] > 0:
                return True
        
        # Check path patterns
        rp_path_patterns = [
            '/right_perspective/',
            '/rightperspective/',
            'right-perspective',
            'right_perspective'
        ]
        
        return any(pattern in asset_path.lower() for pattern in rp_path_patterns)
    
    def _is_right_perspective_knowledge(self, knowledge_source: str) -> bool:
        """Check if knowledge source belongs to Right Perspective"""
        rp_knowledge_patterns = [
            f'{self.RIGHT_PERSPECTIVE_CHANNEL_ID}_',
            'right_perspective_',
            'rightperspective_'
        ]
        
        return any(pattern in knowledge_source.lower() for pattern in rp_knowledge_patterns)
    
    def _get_right_perspective_characteristics(self) -> List[str]:
        """Get Right Perspective persona characteristics to prevent contamination"""
        # This would be loaded from the persona system
        return [
            "conservative", "traditional", "right-wing", "patriotic",
            "constitutional", "liberty", "freedom", "american values"
        ]
    
    def _contains_rp_characteristics(self, text: str, characteristics: List[str]) -> bool:
        """Check if text contains Right Perspective characteristics"""
        text_lower = str(text).lower()
        return any(char.lower() in text_lower for char in characteristics)
    
    def _find_matching_rule(self, violation_type: FirewallViolationType, 
                          source_channel: str, target_channel: str) -> str:
        """Find matching firewall rule for violation"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Try exact match first
            cursor.execute("""
                SELECT rule_id FROM firewall_rules 
                WHERE violation_type = ? AND source_channel = ? AND target_channel = ? AND is_active = 1
            """, (violation_type.value, source_channel, target_channel))
            
            result = cursor.fetchone()
            if result:
                return result[0]
            
            # Try wildcard matches
            cursor.execute("""
                SELECT rule_id FROM firewall_rules 
                WHERE violation_type = ? AND (source_channel = '*' OR target_channel = '*') AND is_active = 1
                ORDER BY (CASE WHEN source_channel = ? THEN 1 ELSE 0 END) + 
                         (CASE WHEN target_channel = ? THEN 1 ELSE 0 END) DESC
                LIMIT 1
            """, (violation_type.value, source_channel, target_channel))
            
            result = cursor.fetchone()
            return result[0] if result else "default_rule"
    
    def get_firewall_status(self) -> Dict[str, Any]:
        """Get comprehensive firewall status"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Active rules count
            cursor.execute("SELECT COUNT(*) FROM firewall_rules WHERE is_active = 1")
            active_rules = cursor.fetchone()[0]
            
            # Violations in last 24 hours
            cursor.execute("""
                SELECT COUNT(*) FROM firewall_violations 
                WHERE detected_at > datetime('now', '-1 day')
            """)
            recent_violations = cursor.fetchone()[0]
            
            # Quarantined content
            cursor.execute("SELECT COUNT(*) FROM content_quarantine WHERE status = 'quarantined'")
            quarantined_content = cursor.fetchone()[0]
            
            # Right Perspective protection status
            cursor.execute("""
                SELECT COUNT(*) FROM firewall_rules 
                WHERE (source_channel = ? OR target_channel = ?) AND is_active = 1
            """, (self.RIGHT_PERSPECTIVE_CHANNEL_ID, self.RIGHT_PERSPECTIVE_CHANNEL_ID))
            rp_protection_rules = cursor.fetchone()[0]
            
            return {
                "firewall_active": True,
                "active_rules": active_rules,
                "recent_violations": recent_violations,
                "quarantined_content": quarantined_content,
                "right_perspective_protection": {
                    "active_rules": rp_protection_rules,
                    "isolation_level": "MAXIMUM",
                    "last_violation_check": datetime.now().isoformat()
                },
                "security_level": "CRITICAL",
                "last_updated": datetime.now().isoformat()
            }
    
    def get_violation_report(self, days: int = 7) -> Dict[str, Any]:
        """Get violation report for specified period"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM firewall_violations 
                WHERE detected_at > datetime('now', '-{} days')
                ORDER BY detected_at DESC
            """.format(days))
            
            violations = [dict(row) for row in cursor.fetchall()]
            
            # Aggregate statistics
            violation_types = {}
            channel_violations = {}
            
            for violation in violations:
                vtype = violation['violation_type']
                violation_types[vtype] = violation_types.get(vtype, 0) + 1
                
                source = violation['source_channel']
                channel_violations[source] = channel_violations.get(source, 0) + 1
            
            return {
                "period_days": days,
                "total_violations": len(violations),
                "violations_by_type": violation_types,
                "violations_by_channel": channel_violations,
                "recent_violations": violations[:10],  # Last 10
                "right_perspective_incidents": [
                    v for v in violations 
                    if v['source_channel'] == self.RIGHT_PERSPECTIVE_CHANNEL_ID or 
                       v['target_channel'] == self.RIGHT_PERSPECTIVE_CHANNEL_ID
                ]
            }

# Global firewall instance
firewall = RightPerspectiveFirewall()

def get_firewall() -> RightPerspectiveFirewall:
    """Get the global Right Perspective Firewall instance"""
    return firewall

def validate_content_against_firewall(channel_id: str, content_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Convenience function to validate content against firewall"""
    return firewall.validate_content_creation(channel_id, content_data)

def check_cross_promotion(source_channel: str, content: str) -> Tuple[bool, List[str]]:
    """Convenience function to check cross-promotion violations"""
    return firewall.check_cross_promotion_violation(source_channel, content)

def log_firewall_violation(violation_type: str, source_channel: str, target_channel: str, 
                         content_id: str = None, details: Dict[str, Any] = None) -> str:
    """Convenience function to log firewall violations"""
    vtype = FirewallViolationType(violation_type)
    return firewall.log_violation(vtype, source_channel, target_channel, content_id, details)