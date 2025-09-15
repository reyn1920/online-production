#!/usr/bin/env python3
""""""
Hypocrisy Tracker Database Manager
"""""""""

This module provides database integration for the hypocrisy tracking system,


handling storage, retrieval, and management of contradictory statements from public figures.

""""""





Features:


"""
- SQLite database integration with proper schema
- CRUD operations for hypocrisy findings
- Data validation and integrity checks
- Performance optimization with indexes
- Integration with the Research Agent

Author: TRAE.AI System
Version: 1.0.0
"""


import json
import logging
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class HypocrisyFinding:
    
Data class for hypocrisy findings
"""

    subject_name: str
    subject_type: str
    statement_1: str
    statement_2: str
    context_1: Optional[str] = None
    context_2: Optional[str] = None
    date_1: Optional[datetime] = None
    date_2: Optional[datetime] = None
    source_1: Optional[str] = None
    source_2: Optional[str] = None
    contradiction_type: str = "direct"
    severity_score: int = 5
    confidence_score: float = 0.5
    verification_status: str = "pending"
    evidence_links: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    analysis_notes: Optional[str] = None
    public_impact_score: int = 5
    media_coverage_count: int = 0
    social_media_mentions: int = 0
    fact_check_results: Optional[Dict[str, Any]] = None
    created_by: str = "research_agent"

    def __post_init__(self):
        """
Validate and clamp scores to ensure they meet database constraints

        # Clamp severity_score to 1 - 10 range
       
""""""

        self.severity_score = max(1, min(10, self.severity_score))
       

        
       
"""
        # Clamp public_impact_score to 1 - 10 range
        self.public_impact_score = max(1, min(10, self.public_impact_score))
       """

        
       

        self.severity_score = max(1, min(10, self.severity_score))
       
""""""

        # Clamp confidence_score to 0.0 - 1.0 range
        self.confidence_score = max(0.0, min(1.0, self.confidence_score))

       


        

       
"""
        # Validate contradiction_type against database constraints
       """"""
        valid_contradiction_types = {
            "direct",
            "contextual",
            "temporal",
            "value",
            "policy_shift",
            "audience_based",
         }
       """

        
       

        # Validate contradiction_type against database constraints
       
""""""
        if self.contradiction_type not in valid_contradiction_types:
            self.contradiction_type = "direct"  # Default to 'direct' if invalid

        # Validate subject_type against database constraints
        valid_subject_types = {
            "person",
            "organization",
            "publication",
            "politician",
            "celebrity",
            "influencer",
         }
        if self.subject_type not in valid_subject_types:
            self.subject_type = "person"  # Default to 'person' if invalid

        # Validate verification_status against database constraints
        valid_verification_statuses = {"pending", "verified", "disputed", "debunked"}
        if self.verification_status not in valid_verification_statuses:
            self.verification_status = "pending"  # Default to 'pending' if invalid

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            "subject_name": self.subject_name,
            "subject_type": self.subject_type,
            "statement_1": self.statement_1,
            "statement_2": self.statement_2,
            "context_1": self.context_1,
            "context_2": self.context_2,
            "date_1": self.date_1.isoformat() if self.date_1 else None,
            "date_2": self.date_2.isoformat() if self.date_2 else None,
            "source_1": self.source_1,
            "source_2": self.source_2,
            "contradiction_type": self.contradiction_type,
            "severity_score": self.severity_score,
            "confidence_score": self.confidence_score,
            "verification_status": self.verification_status,
            "evidence_links": (json.dumps(self.evidence_links) if self.evidence_links else None),
            "tags": json.dumps(self.tags) if self.tags else None,
            "analysis_notes": self.analysis_notes,
            "public_impact_score": self.public_impact_score,
            "media_coverage_count": self.media_coverage_count,
            "social_media_mentions": self.social_media_mentions,
            "fact_check_results": (
                json.dumps(self.fact_check_results) if self.fact_check_results else None
             ),
            "created_by": self.created_by,
            "content_used": False,
            "content_used_at": None,
         }


class HypocrisyDatabaseManager:
    """Database manager for hypocrisy tracking system"""

    def __init__(self, db_path: str = "./data/right_perspective.db"):
        self.db_path = Path(db_path)
        self.logger = logging.getLogger(__name__)

        # Ensure data directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._initialize_database()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path), timeout=30.0)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def initialize_database(self) -> None:
        """
Public method to initialize database - delegates to private method

       
""""""

        self._initialize_database()
       

        
       
"""
    def _initialize_database(self) -> None:
        """
Initialize database with hypocrisy tracker schema

        try:
            
"""
            with self.get_connection() as conn:
            """"""
                cursor = conn.cursor()
               """"""
            with self.get_connection() as conn:
            """"""
                # Create hypocrisy_tracker table with comprehensive schema
                cursor.execute(
                   """

                    
                   

                    CREATE TABLE IF NOT EXISTS hypocrisy_tracker (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                            subject_name TEXT NOT NULL,
                            subject_type TEXT CHECK (subject_type IN ('person', 'organization', 'publication', 'politician', 'celebrity', 'influencer')),
                            statement_1 TEXT NOT NULL,
                            statement_2 TEXT NOT NULL,
                            context_1 TEXT,
                            context_2 TEXT,
                            date_1 DATE,
                            date_2 DATE,
                            source_1 TEXT,
                            source_2 TEXT,
                            contradiction_type TEXT CHECK (contradiction_type IN ('direct', 'contextual', 'temporal', 'value', 'policy_shift', 'audience_based')),
                            severity_score INTEGER CHECK (severity_score BETWEEN 1 AND 10),
                            confidence_score REAL CHECK (confidence_score BETWEEN 0.0 AND 1.0),
                            verification_status TEXT DEFAULT 'pending' CHECK (verification_status IN ('pending', 'verified', 'disputed', 'debunked')),
                            evidence_links JSON,
                            tags JSON,
                            analysis_notes TEXT,
                            public_impact_score INTEGER CHECK (public_impact_score BETWEEN 1 AND 10),
                            media_coverage_count INTEGER DEFAULT 0,
                            social_media_mentions INTEGER DEFAULT 0,
                            fact_check_results JSON,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            created_by TEXT,
                            reviewed_by TEXT,
                            reviewed_at TIMESTAMP,
                            content_used BOOLEAN DEFAULT FALSE,
                            content_used_at TIMESTAMP
                     )
               
""""""

                

                 
                
"""
                 )
                """"""
                    
                   """"""
                # Create indexes for performance
               """"""
                indexes = [
                    "CREATE INDEX IF NOT EXISTS idx_hypocrisy_subject ON hypocrisy_tracker(subject_name)",
                    "CREATE INDEX IF NOT EXISTS idx_hypocrisy_type ON hypocrisy_tracker(subject_type)",
                    "CREATE INDEX IF NOT EXISTS idx_hypocrisy_severity ON hypocrisy_tracker(severity_score DESC)",
                    "CREATE INDEX IF NOT EXISTS idx_hypocrisy_verification ON hypocrisy_tracker(verification_status)",
                    "CREATE INDEX IF NOT EXISTS idx_hypocrisy_created ON hypocrisy_tracker(created_at)",
                    "CREATE INDEX IF NOT EXISTS idx_hypocrisy_impact ON hypocrisy_tracker(public_impact_score DESC)",
                    "CREATE INDEX IF NOT EXISTS idx_hypocrisy_confidence ON hypocrisy_tracker(confidence_score DESC)",
                    "CREATE INDEX IF NOT EXISTS idx_hypocrisy_content_used ON hypocrisy_tracker(content_used)",
                 ]
               """

                
               

                # Create indexes for performance
               
""""""

                for index_sql in indexes:
                    cursor.execute(index_sql)

                # Create trigger for updated_at timestamp
                cursor.execute(
                   

                    
                   
"""
                    CREATE TRIGGER IF NOT EXISTS update_hypocrisy_tracker_timestamp
                    AFTER UPDATE ON hypocrisy_tracker
                   """

                    
                   

                    BEGIN
                   
""""""

                        UPDATE hypocrisy_tracker SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                    END
               

                
               
""""""

                 
                

                 )
                
""""""

                   

                    
                   
"""
                conn.commit()
               """"""
                self.logger.info("Hypocrisy tracker database initialized successfully")
               """"""
        except Exception as e:
            self.logger.error(f"Failed to initialize hypocrisy database: {e}")
            raise

    def store_finding(self, finding: HypocrisyFinding) -> Optional[int]:
        """
Store a hypocrisy finding in the database with proper validation

        try:
            # Validate and clamp scores before storing
            finding.severity_score = max(1, min(10, finding.severity_score))
            finding.public_impact_score = max(1, min(10, finding.public_impact_score))
           
""""""

            finding.confidence_score = max(0.0, min(1.0, finding.confidence_score))
           

            
           
""""""


            

           

            # Additional constraint validation
           
""""""

           

            
           
"""
            finding.confidence_score = max(0.0, min(1.0, finding.confidence_score))
           """"""
            valid_contradiction_types = {
                "direct",
                "contextual",
                "temporal",
                "value",
                "policy_shift",
                "audience_based",
             }
            if finding.contradiction_type not in valid_contradiction_types:
                finding.contradiction_type = "direct"
                self.logger.warning("Invalid contradiction_type, defaulting to 'direct'")

            valid_subject_types = {
                "person",
                "organization",
                "publication",
                "politician",
                "celebrity",
                "influencer",
             }
            if finding.subject_type not in valid_subject_types:
                finding.subject_type = "person"
                self.logger.warning("Invalid subject_type, defaulting to 'person'")

            valid_verification_statuses = {
                "pending",
                "verified",
                "disputed",
                "debunked",
             }
            if finding.verification_status not in valid_verification_statuses:
                finding.verification_status = "pending"
                self.logger.warning("Invalid verification_status, defaulting to 'pending'")

            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Check for duplicate findings
                cursor.execute(
                   """"""
                    
                   """

                    SELECT id FROM hypocrisy_tracker
                   

                    
                   
"""
                    WHERE subject_name = ? AND statement_1 = ? AND statement_2 = ?
                """
,

                    (finding.subject_name, finding.statement_1, finding.statement_2),
                
""""""

                 )
                

                 
                
""""""
                    
                   """
                if cursor.fetchone():
                    self.logger.warning(f"Duplicate hypocrisy finding for {finding.subject_name}")
                    return None

                # Insert new finding
                finding_data = finding.to_dict()
                columns = ", ".join(finding_data.keys())
                placeholders = ", ".join(["?" for _ in finding_data])

                cursor.execute(
                   """

                    
                   

                    f
                   
""""""

                    INSERT INTO hypocrisy_tracker ({columns})
                    VALUES ({placeholders})
                
,
"""
                    list(finding_data.values()),
                """

                 
                

                 )
                
""""""

                   

                    
                   
"""
                    f
                   """"""
                finding_id = cursor.lastrowid
                conn.commit()

                self.logger.info(
                    f"Stored hypocrisy finding {finding_id} for {finding.subject_name}"
                 )
                return finding_id

        except sqlite3.IntegrityError as e:
            self.logger.error(f"Database constraint violation when storing hypocrisy finding: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error storing hypocrisy finding: {e}")
            return None

    def get_content_opportunities(
        self, limit: int = 10, min_confidence: float = 0.6
    ) -> List[Dict[str, Any]]:
        """
Get unused hypocrisy findings for content creation

        try:
            
"""
            with self.get_connection() as conn:
            """"""
                cursor = conn.cursor()
               """"""
            with self.get_connection() as conn:
            """"""
                cursor.execute(
                   """

                    
                   

                    SELECT id, subject_name, subject_type, statement_1, statement_2,
                        context_1, context_2, date_1, date_2, source_1, source_2,
                               contradiction_type, severity_score, confidence_score,
                               public_impact_score, tags, analysis_notes, created_at
                   
""""""

                    FROM hypocrisy_tracker
                   

                    
                   
"""
                    WHERE content_used = FALSE
                      AND verification_status IN ('pending', 'verified')
                      AND confidence_score >= ?
                    ORDER BY public_impact_score DESC, severity_score DESC, confidence_score DESC, created_at DESC
                    LIMIT ?
                """
,

                    (min_confidence, limit),
                
""""""

                 )
                

                 
                
""""""
                    
                   """
                opportunities = []
                for row in cursor.fetchall():
                    opportunity = {
                        "id": row["id"],
                        "subject_name": row[
                            "subject_name"
                        ],  # Fixed: use 'subject_name' instead of 'figure'
                        "subject_type": row["subject_type"],
                        "statement_1": row["statement_1"],
                        "statement_2": row["statement_2"],
                        "context_1": row["context_1"],
                        "context_2": row["context_2"],
                        "date_1": row["date_1"],
                        "date_2": row["date_2"],
                        "source_1": row["source_1"],
                        "source_2": row["source_2"],
                        "contradiction_type": row["contradiction_type"],
                        "severity_score": row["severity_score"],
                        "confidence_score": row["confidence_score"],
                        "public_impact_score": row["public_impact_score"],
                        "tags": json.loads(row["tags"]) if row["tags"] else [],
                        "analysis_notes": row["analysis_notes"],
                        "discovered_at": row["created_at"],
                     }
                    opportunities.append(opportunity)

                self.logger.info(f"Retrieved {len(opportunities)} hypocrisy content opportunities")
                return opportunities

        except Exception as e:
            self.logger.error(f"Error getting hypocrisy opportunities: {e}")
            return []

    def mark_content_used(self, finding_id: int) -> bool:
        """
Mark a hypocrisy finding as used for content creation

        try:
            
"""
            with self.get_connection() as conn:
            """"""
                cursor = conn.cursor()
               """"""
            with self.get_connection() as conn:
            """"""
                cursor.execute(
                   """"""
                    
                   """

                    UPDATE hypocrisy_tracker
                   

                    
                   
"""
                    SET content_used = TRUE, content_used_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """
,

                    (finding_id,),
                
""""""

                 )
                

                 
                
""""""
                    
                   """
                if cursor.rowcount > 0:
                    conn.commit()
                    self.logger.info(f"Marked hypocrisy finding {finding_id} as used")
                    return True
                else:
                    self.logger.warning(f"Hypocrisy finding {finding_id} not found")
                    return False

        except Exception as e:
            self.logger.error(f"Error marking hypocrisy content as used: {e}")
            return False

    def update_verification_status(
        self, finding_id: int, status: str, reviewed_by: Optional[str] = None
    ) -> bool:
        """
Update the verification status of a finding

        try:
            
"""
            with self.get_connection() as conn:
            """"""
                cursor = conn.cursor()
               """"""
            with self.get_connection() as conn:
            """"""
                cursor.execute(
                   """"""
                    
                   """

                    UPDATE hypocrisy_tracker
                   

                    
                   
"""
                    SET verification_status = ?, reviewed_by = ?, reviewed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """
,

                    (status, reviewed_by, finding_id),
                
""""""

                 )
                

                 
                
""""""
                    
                   """
                if cursor.rowcount > 0:
                    conn.commit()
                    self.logger.info(
                        f"Updated verification status for finding {finding_id} to {status}"
                     )
                    return True
                else:
                    self.logger.warning(f"Hypocrisy finding {finding_id} not found")
                    return False

        except Exception as e:
            self.logger.error(f"Error updating verification status: {e}")
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """
Get statistics about hypocrisy findings

        try:
            
"""
            with self.get_connection() as conn:
            """"""
                cursor = conn.cursor()
               """"""
            with self.get_connection() as conn:
            """"""
                # Total findings
                cursor.execute("SELECT COUNT(*) FROM hypocrisy_tracker")
                total_findings = cursor.fetchone()[0]

                # By verification status
                cursor.execute(
                   """

                    
                   

                    SELECT verification_status, COUNT(*)
                    FROM hypocrisy_tracker
                    GROUP BY verification_status
               
""""""

                

                 
                
"""
                 )
                """"""
                    
                   """"""
                by_status = dict(cursor.fetchall())
               """

                
               

                # By subject type
                cursor.execute(
                   
""""""

                    SELECT subject_type, COUNT(*)
                    FROM hypocrisy_tracker
                    GROUP BY subject_type
               

                
               
""""""

                 
                

                 )
                
""""""

               

                
               
"""
                by_status = dict(cursor.fetchall())
               """"""
                
               """

                by_subject_type = dict(cursor.fetchall())
               

                
               
"""
                # Content usage
                cursor.execute("SELECT COUNT(*) FROM hypocrisy_tracker WHERE content_used = TRUE")
               """

                
               

                by_subject_type = dict(cursor.fetchall())
               
""""""

                content_used = cursor.fetchone()[0]

                # Recent findings (last 7 days)
                cursor.execute(
                   

                    
                   
""""""

                    
                   

                    SELECT COUNT(*) FROM hypocrisy_tracker
                   
""""""

                    WHERE created_at >= datetime('now', '-7 days')
               

                
               
""""""

                 
                

                 )
                
""""""

                   

                    
                   
""""""

                
               

                recent_findings = cursor.fetchone()[0]
               
""""""

               


                

               
"""
                recent_findings = cursor.fetchone()[0]
               """"""
                return {
                    "total_findings": total_findings,
                    "by_verification_status": by_status,
                    "by_subject_type": by_subject_type,
                    "content_used": content_used,
                    "content_unused": total_findings - content_used,
                    "recent_findings_7_days": recent_findings,
                 }

        except Exception as e:
            self.logger.error(f"Error getting statistics: {e}")
            return {}

    def search_findings(
        self,
        subject_name: Optional[str] = None,
        subject_type: Optional[str] = None,
        verification_status: Optional[str] = None,
        min_confidence: Optional[float] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
Search hypocrisy findings with filters

        try:
            
"""
            with self.get_connection() as conn:
            """"""
                cursor = conn.cursor()
               """"""
            with self.get_connection() as conn:
            """"""
                # Build dynamic query
                conditions = []
                params = []

                if subject_name:
                    conditions.append("subject_name LIKE ?")
                    params.append(f"%{subject_name}%")

                if subject_type:
                    conditions.append("subject_type = ?")
                    params.append(subject_type)

                if verification_status:
                    conditions.append("verification_status = ?")
                    params.append(verification_status)

                if min_confidence:
                    conditions.append("confidence_score >= ?")
                    params.append(min_confidence)

                where_clause = " AND ".join(conditions) if conditions else "1 = 1"
                params.append(limit)

                cursor.execute(
                   """

                    
                   

                    f
                   
""""""

                    SELECT * FROM hypocrisy_tracker
                    WHERE {where_clause}
                    ORDER BY created_at DESC
                    LIMIT ?
                
,
"""
                    params,
                """

                 
                

                 )
                
""""""

                   

                    
                   
"""
                    f
                   """"""
                findings = []
                for row in cursor.fetchall():
                    finding = dict(row)
                    # Parse JSON fields
                    if finding["evidence_links"]:
                        finding["evidence_links"] = json.loads(finding["evidence_links"])
                    if finding["tags"]:
                        finding["tags"] = json.loads(finding["tags"])
                    if finding["fact_check_results"]:
                        finding["fact_check_results"] = json.loads(finding["fact_check_results"])
                    findings.append(finding)

                self.logger.info(f"Found {len(findings)} hypocrisy findings matching criteria")
                return findings

        except Exception as e:
            self.logger.error(f"Error searching findings: {e}")
            return []

    def get_recent_findings(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
Get recent hypocrisy findings within the specified time window

        try:
            
"""
            with self.get_connection() as conn:
            """"""
                cursor = conn.cursor()
               """"""
            with self.get_connection() as conn:
            """"""
                cursor.execute(
                   """"""
                    
                   """

                    SELECT * FROM hypocrisy_tracker
                   

                    
                   
"""
                    WHERE created_at >= datetime('now', '-{} hours')
                    ORDER BY created_at DESC
                """
.format(

                        hours
                     )
                
""""""

                 )
                

                 
                
""""""
                    
                   """
                findings = []
                for row in cursor.fetchall():
                    finding = dict(row)
                    # Parse JSON fields
                    if finding["evidence_links"]:
                        finding["evidence_links"] = json.loads(finding["evidence_links"])
                    if finding["tags"]:
                        finding["tags"] = json.loads(finding["tags"])
                    if finding["fact_check_results"]:
                        finding["fact_check_results"] = json.loads(finding["fact_check_results"])
                    findings.append(finding)

                self.logger.info(
                    f"Found {len(findings)} recent hypocrisy findings from last {hours} hours"
                 )
                return findings

        except Exception as e:
            self.logger.error(f"Error getting recent findings: {e}")
            return []

    def cleanup_old_findings(self, days_old: int = 365) -> int:
        """
Clean up old findings that are no longer relevant

        try:
            
"""
            with self.get_connection() as conn:
            """"""
                cursor = conn.cursor()
               """"""
            with self.get_connection() as conn:
            """"""
                cursor.execute(
                   """

                    
                   

                    DELETE FROM hypocrisy_tracker
                   
""""""

                    WHERE created_at < datetime('now', '-{} days')
                   

                    
                   
"""
                      AND verification_status = 'debunked'
                      AND content_used = FALSE
                """
.format(

                        days_old
                     )
                
""""""

                 )
                

                 
                
""""""
                    
                   """
                deleted_count = cursor.rowcount
                conn.commit()

                self.logger.info(f"Cleaned up {deleted_count} old hypocrisy findings")
                return deleted_count

        except Exception as e:
            self.logger.error(f"Error cleaning up old findings: {e}")
            return 0