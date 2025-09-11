#!/usr/bin/env python3
"""
TRAE AI Error Tracking and Alerting System
Monitors application logs, tracks errors, and sends alerts for critical issues.
"""

import json
import logging
import os
import re
import smtplib
import sqlite3
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger("trae_ai.error_tracker")


@dataclass
class ErrorEvent:
    """Error event data structure."""

    timestamp: str
    level: str
    logger_name: str
    message: str
    module: str
    function: str
    line_number: int
    exception_type: Optional[str] = None
    stack_trace: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


@dataclass
class AlertRule:
    """Alert rule configuration."""

    name: str
    pattern: str
    threshold: int
    time_window_minutes: int
    severity: str
    enabled: bool = True
    description: str = ""


class ErrorTracker:
    """Main error tracking and alerting class."""

    def __init__(self, db_path: str = "monitoring/error_tracking.db"):
        self.db_path = db_path
        self.log_files = [
            "logs/trae-ai.log",
            "logs/trae-ai-errors.log",
            "logs/trae-ai-security.log",
        ]
        self.error_buffer = deque(maxlen=1000)  # Keep last 1000 errors in memory
        self.alert_rules = self._load_default_alert_rules()
        self.last_positions = {}  # Track file positions for log tailing

        self._ensure_db_directory()
        self._init_database()
        self._init_log_positions()

    def _ensure_db_directory(self):
        """Ensure the monitoring directory exists."""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

        # Ensure logs directory exists
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)

    def _init_database(self):
        """Initialize the error tracking database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Error events table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS error_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        level TEXT NOT NULL,
                        logger_name TEXT,
                        message TEXT NOT NULL,
                        module TEXT,
                        function TEXT,
                        line_number INTEGER,
                        exception_type TEXT,
                        stack_trace TEXT,
                        context TEXT,
                        fingerprint TEXT,
                        count INTEGER DEFAULT 1,
                        first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                        last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                        resolved BOOLEAN DEFAULT FALSE
                    )
                """
                )

                # Alert history table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS alert_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        rule_name TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        message TEXT NOT NULL,
                        error_count INTEGER,
                        time_window_minutes INTEGER,
                        triggered_by TEXT,
                        acknowledged BOOLEAN DEFAULT FALSE,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Error patterns table for ML-based detection
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS error_patterns (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        pattern_hash TEXT UNIQUE,
                        pattern_description TEXT,
                        occurrence_count INTEGER DEFAULT 1,
                        severity_score REAL DEFAULT 0.0,
                        first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                        last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                        auto_resolved BOOLEAN DEFAULT FALSE
                    )
                """
                )

                conn.commit()
                logger.info("Error tracking database initialized")

        except Exception as e:
            logger.error(f"Failed to initialize error tracking database: {e}")
            raise

    def _init_log_positions(self):
        """Initialize log file positions for tailing."""
        for log_file in self.log_files:
            if os.path.exists(log_file):
                # Start from end of file for existing logs
                with open(log_file, "r") as f:
                    f.seek(0, 2)  # Seek to end
                    self.last_positions[log_file] = f.tell()
            else:
                self.last_positions[log_file] = 0

    def _load_default_alert_rules(self) -> List[AlertRule]:
        """Load default alert rules."""
        return [
            AlertRule(
                name="critical_errors",
                pattern=r"CRITICAL|FATAL",
                threshold=1,
                time_window_minutes=5,
                severity="critical",
                description="Any critical or fatal error",
            ),
            AlertRule(
                name="high_error_rate",
                pattern=r"ERROR",
                threshold=10,
                time_window_minutes=10,
                severity="warning",
                description="High error rate detected",
            ),
            AlertRule(
                name="security_alerts",
                pattern=r"security|authentication|authorization|breach|attack",
                threshold=1,
                time_window_minutes=1,
                severity="critical",
                description="Security-related incidents",
            ),
            AlertRule(
                name="database_errors",
                pattern=r"database|sqlite|connection.*failed|query.*error",
                threshold=5,
                time_window_minutes=15,
                severity="warning",
                description="Database connectivity or query issues",
            ),
            AlertRule(
                name="agent_failures",
                pattern=r"agent.*failed|agent.*error|task.*failed",
                threshold=3,
                time_window_minutes=10,
                severity="warning",
                description="Agent execution failures",
            ),
            AlertRule(
                name="memory_issues",
                pattern=r"memory|out of memory|oom|malloc",
                threshold=1,
                time_window_minutes=5,
                severity="critical",
                description="Memory-related issues",
            ),
        ]

    def parse_log_line(self, line: str, source_file: str) -> Optional[ErrorEvent]:
        """Parse a log line and extract error information."""
        try:
            # Standard log format: timestamp | level | logger | message
            # Example: 2025-01-09 10:30:05 | ERROR | trae_ai.agent | Task failed

            # Try JSON format first
            if line.strip().startswith("{"):
                try:
                    log_data = json.loads(line.strip())
                    return ErrorEvent(
                        timestamp=log_data.get("timestamp", ""),
                        level=log_data.get("level", "UNKNOWN"),
                        logger_name=log_data.get("logger", ""),
                        message=log_data.get("message", ""),
                        module=log_data.get("module", ""),
                        function=log_data.get("function", ""),
                        line_number=log_data.get("line", 0),
                    )
                except json.JSONDecodeError:
                    pass

            # Try standard format
            pattern = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s*\|\s*(\w+)\s*\|\s*([^|]+)\s*\|\s*(.+)"
            match = re.match(pattern, line.strip())

            if match:
                timestamp_str, level, logger_name, message = match.groups()

                # Only track ERROR, CRITICAL, FATAL, and WARNING levels
                if level.upper() in ["ERROR", "CRITICAL", "FATAL", "WARNING"]:
                    return ErrorEvent(
                        timestamp=timestamp_str,
                        level=level.upper(),
                        logger_name=logger_name.strip(),
                        message=message.strip(),
                        module=source_file,
                        function="",
                        line_number=0,
                    )

            return None

        except Exception as e:
            logger.debug(f"Failed to parse log line: {e}")
            return None

    def generate_error_fingerprint(self, error: ErrorEvent) -> str:
        """Generate a unique fingerprint for error deduplication."""
        # Create fingerprint based on logger, level, and normalized message
        normalized_message = re.sub(r"\d+", "N", error.message)  # Replace numbers
        normalized_message = re.sub(
            r"[a-f0-9]{8,}", "HASH", normalized_message
        )  # Replace hashes

        fingerprint_data = (
            f"{error.logger_name}:{error.level}:{normalized_message[:100]}"
        )
        return str(hash(fingerprint_data))

    def store_error(self, error: ErrorEvent):
        """Store error in database with deduplication."""
        try:
            fingerprint = self.generate_error_fingerprint(error)

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Check if error already exists
                cursor.execute(
                    "SELECT id, count FROM error_events WHERE fingerprint = ?",
                    (fingerprint,),
                )
                existing = cursor.fetchone()

                if existing:
                    # Update existing error
                    cursor.execute(
                        """
                        UPDATE error_events 
                        SET count = count + 1, last_seen = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """,
                        (existing[0],),
                    )
                else:
                    # Insert new error
                    cursor.execute(
                        """
                        INSERT INTO error_events (
                            timestamp, level, logger_name, message, module,
                            function, line_number, exception_type, stack_trace,
                            context, fingerprint
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            error.timestamp,
                            error.level,
                            error.logger_name,
                            error.message,
                            error.module,
                            error.function,
                            error.line_number,
                            error.exception_type,
                            error.stack_trace,
                            json.dumps(error.context) if error.context else None,
                            fingerprint,
                        ),
                    )

                conn.commit()

        except Exception as e:
            logger.error(f"Failed to store error: {e}")

    def check_alert_rules(self, error: ErrorEvent) -> List[Dict[str, Any]]:
        """Check if error triggers any alert rules."""
        triggered_alerts = []

        for rule in self.alert_rules:
            if not rule.enabled:
                continue

            # Check if error matches pattern
            if re.search(rule.pattern, error.message, re.IGNORECASE):
                # Count matching errors in time window
                cutoff_time = datetime.now(timezone.utc) - timedelta(
                    minutes=rule.time_window_minutes
                )

                try:
                    with sqlite3.connect(self.db_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            """
                            SELECT COUNT(*) FROM error_events 
                            WHERE timestamp >= ? AND message REGEXP ?
                        """,
                            (cutoff_time.isoformat(), rule.pattern),
                        )

                        count = cursor.fetchone()[0]

                        if count >= rule.threshold:
                            alert = {
                                "rule_name": rule.name,
                                "severity": rule.severity,
                                "message": f"{rule.description}: {count} occurrences in {rule.time_window_minutes} minutes",
                                "error_count": count,
                                "time_window_minutes": rule.time_window_minutes,
                                "triggered_by": error.message[:200],
                                "threshold": rule.threshold,
                            }
                            triggered_alerts.append(alert)

                except Exception as e:
                    logger.error(f"Failed to check alert rule {rule.name}: {e}")

        return triggered_alerts

    def send_alert(self, alert: Dict[str, Any]):
        """Send alert notification."""
        try:
            # Store alert in database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO alert_history (
                        timestamp, rule_name, severity, message, error_count,
                        time_window_minutes, triggered_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        datetime.now(timezone.utc).isoformat(),
                        alert["rule_name"],
                        alert["severity"],
                        alert["message"],
                        alert["error_count"],
                        alert["time_window_minutes"],
                        alert["triggered_by"],
                    ),
                )
                conn.commit()

            # Log alert (in production, this could send emails, Slack messages, etc.)
            severity_emoji = {"critical": "🚨", "warning": "⚠️", "info": "ℹ️"}

            emoji = severity_emoji.get(alert["severity"], "📢")
            logger.warning(
                f"{emoji} ALERT [{alert['severity'].upper()}] {alert['rule_name']}: {alert['message']}"
            )

            # In production, implement actual notification mechanisms:
            # - Email notifications
            # - Slack/Discord webhooks
            # - PagerDuty integration
            # - SMS alerts for critical issues

        except Exception as e:
            logger.error(f"Failed to send alert: {e}")

    def tail_log_files(self) -> List[ErrorEvent]:
        """Tail log files for new entries."""
        new_errors = []

        for log_file in self.log_files:
            if not os.path.exists(log_file):
                continue

            try:
                with open(log_file, "r") as f:
                    # Seek to last known position
                    f.seek(self.last_positions.get(log_file, 0))

                    # Read new lines
                    new_lines = f.readlines()

                    # Update position
                    self.last_positions[log_file] = f.tell()

                    # Parse new lines
                    for line in new_lines:
                        error = self.parse_log_line(line, log_file)
                        if error:
                            new_errors.append(error)

            except Exception as e:
                logger.error(f"Failed to tail log file {log_file}: {e}")

        return new_errors

    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get error summary for the specified time period."""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Total error count
                cursor.execute(
                    "SELECT COUNT(*) FROM error_events WHERE timestamp >= ?",
                    (cutoff_time.isoformat(),),
                )
                total_errors = cursor.fetchone()[0]

                # Errors by level
                cursor.execute(
                    """
                    SELECT level, COUNT(*) FROM error_events 
                    WHERE timestamp >= ? GROUP BY level
                """,
                    (cutoff_time.isoformat(),),
                )
                errors_by_level = dict(cursor.fetchall())

                # Top error messages
                cursor.execute(
                    """
                    SELECT message, COUNT(*) as count FROM error_events 
                    WHERE timestamp >= ? GROUP BY fingerprint 
                    ORDER BY count DESC LIMIT 10
                """,
                    (cutoff_time.isoformat(),),
                )
                top_errors = cursor.fetchall()

                # Recent alerts
                cursor.execute(
                    """
                    SELECT rule_name, severity, message, timestamp FROM alert_history 
                    WHERE timestamp >= ? ORDER BY timestamp DESC LIMIT 10
                """,
                    (cutoff_time.isoformat(),),
                )
                recent_alerts = cursor.fetchall()

                return {
                    "period_hours": hours,
                    "total_errors": total_errors,
                    "errors_by_level": errors_by_level,
                    "top_errors": [
                        {"message": msg, "count": count} for msg, count in top_errors
                    ],
                    "recent_alerts": [
                        {
                            "rule_name": rule,
                            "severity": severity,
                            "message": message,
                            "timestamp": timestamp,
                        }
                        for rule, severity, message, timestamp in recent_alerts
                    ],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

        except Exception as e:
            logger.error(f"Failed to get error summary: {e}")
            return {"error": str(e)}

    def run_monitoring_cycle(self):
        """Run a single error monitoring cycle."""
        try:
            # Tail log files for new errors
            new_errors = self.tail_log_files()

            for error in new_errors:
                # Store error
                self.store_error(error)

                # Add to buffer
                self.error_buffer.append(error)

                # Check alert rules
                alerts = self.check_alert_rules(error)

                # Send alerts
                for alert in alerts:
                    self.send_alert(alert)

            if new_errors:
                logger.info(f"Processed {len(new_errors)} new error events")

            return len(new_errors)

        except Exception as e:
            logger.error(f"Error monitoring cycle failed: {e}")
            return 0


def main():
    """Main error tracking function."""
    import sys

    tracker = ErrorTracker()

    if len(sys.argv) > 1:
        if sys.argv[1] == "--summary":
            hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
            summary = tracker.get_error_summary(hours)
            print(json.dumps(summary, indent=2))
            return
        elif sys.argv[1] == "--test":
            # Test alert by creating a fake error
            test_error = ErrorEvent(
                timestamp=datetime.now(timezone.utc).isoformat(),
                level="CRITICAL",
                logger_name="trae_ai.test",
                message="Test critical error for alert system",
                module="error_tracker.py",
                function="main",
                line_number=0,
            )
            tracker.store_error(test_error)
            alerts = tracker.check_alert_rules(test_error)
            for alert in alerts:
                tracker.send_alert(alert)
            print(f"Generated test error and {len(alerts)} alerts")
            return

    # Run continuous monitoring
    logger.info("Starting TRAE AI Error Tracker")

    try:
        while True:
            tracker.run_monitoring_cycle()
            time.sleep(10)  # Check every 10 seconds

    except KeyboardInterrupt:
        logger.info("Error tracking stopped by user")
    except Exception as e:
        logger.error(f"Error tracking failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
