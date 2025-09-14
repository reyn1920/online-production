#!/usr / bin / env python3
"""
Progressive Self - Repair System Agent

Implements intelligent, tiered escalation for component failures:
- Tier 1: Simple restart attempts
- Tier 2: Dependency verification
- Tier 3: AI - powered research and novel solution generation

Author: TRAE.AI System
Version: 1.0.0
"""

import json
import logging
import os
import sqlite3
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import psutil
import requests

from backend.integrations.ollama_integration import OllamaClient

from .base_agents import BaseAgent
from .safe_mode_manager import EnvironmentSnapshot, SafeModeManager


class RepairTier(Enum):
    RESTART = 1
    DEPENDENCY_CHECK = 2
    AI_RESEARCH = 3


class ComponentStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILING = "failing"
    CRITICAL = "critical"


class RepairOutcome(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"

@dataclass


class RepairAttempt:
    component_name: str
    error_message: str
    error_type: str
    repair_tier: RepairTier
    repair_action: str
    outcome: Optional[RepairOutcome] = None
    execution_details: Optional[str] = None
    error_context: Optional[Dict] = None
    duration: Optional[float] = None


class ProgressiveSelfRepairAgent(BaseAgent):
    """Autonomous system repair agent with progressive escalation."""


    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        self.config = config
        self.db_path = config.get("db_path", "right_perspective.db")
        self.ollama_client = OllamaClient(
            config.get("ollama_endpoint", "http://localhost:11434")
        )
        self.max_tier1_attempts = config.get("max_tier1_attempts", 3)
        self.max_tier2_attempts = config.get("max_tier2_attempts", 2)
        self.failure_threshold = config.get("failure_threshold", 5)
        self.escalation_cooldown = config.get("escalation_cooldown", 300)  # 5 minutes

        self.logger = logging.getLogger(__name__)

        # Initialize Safe Mode Manager
        self.safe_mode = SafeModeManager(
            {
                "db_path": self.db_path,
                    "snapshots_dir": config.get("snapshots_dir", "./snapshots"),
                    "venv_path": config.get("venv_path", "./venv"),
                    "project_root": config.get("project_root", "."),
                    "max_snapshots": config.get("max_snapshots", 10),
                    }
        )

        self._init_database()


    def _init_database(self):
        """Initialize the repair log database using the master schema."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # The repair_log table is already defined in right_perspective_schema.sql
                # Just ensure it exists with the correct structure
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS repair_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                            component_name TEXT NOT NULL,
                            error_message TEXT NOT NULL,
                            repair_action TEXT NOT NULL,
                            repair_tier INTEGER NOT NULL,
                            outcome TEXT NOT NULL,
                            execution_details TEXT,
                            attempt_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            resolution_time_seconds INTEGER
                    )
                """
                )

                # Create component_health table for tracking component status
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS component_health (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                            component_name TEXT NOT NULL UNIQUE,
                            status TEXT NOT NULL DEFAULT 'healthy',
                            consecutive_failures INTEGER DEFAULT 0,
                            total_failures INTEGER DEFAULT 0,
                            last_check TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            last_failure_at TIMESTAMP,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                conn.commit()
                self.logger.info(
                    "Progressive Self - Repair database initialized successfully"
                )
        except Exception as e:
            self.logger.error(f"Failed to initialize repair database: {e}")
            raise


    def handle_component_failure(
        self,
            component_name: str,
            error_message: str,
            error_context: Optional[Dict] = None,
            ) -> bool:
        """Main entry point for handling component failures with enhanced pre - repair validation \
    and Safe Mode protection."""
        snapshot = None
        try:
            self.logger.info(f"Handling failure for component: {component_name}")

            # Enhanced pre - repair validation
            validation_result = self._perform_pre_repair_validation(
                component_name, error_message
            )
            if not validation_result["can_proceed"]:
                self.logger.error(
                    f"Pre - repair validation failed: {validation_result['reason']}"
                )
                self._update_component_health(component_name, ComponentStatus.CRITICAL)
                return False

            # Create environment snapshot before attempting repair
            snapshot = self.safe_mode.create_snapshot(
                f"Pre - repair snapshot for {component_name} failure"
            )

            if not snapshot:
                self.logger.warning(
                    "Failed to create pre - repair snapshot - proceeding without Safe Mode"
                )
            else:
                self.logger.info(f"Created pre - repair snapshot: {snapshot.snapshot_id}")

            # Update component health status
            self._update_component_health(component_name, ComponentStatus.FAILING)

            # Get repair history for this component
            repair_history = self._get_repair_history(component_name)

            # Determine appropriate repair tier
            repair_tier = self._determine_repair_tier(component_name, repair_history)

            # Execute repair based on tier with enhanced monitoring
            success = False
            repair_start_time = time.time()

            if repair_tier == RepairTier.RESTART:
                success = self._execute_tier1_repair(
                    component_name, error_message, error_context
                )
            elif repair_tier == RepairTier.DEPENDENCY_CHECK:
                success = self._execute_tier2_repair(
                    component_name, error_message, error_context
                )
            elif repair_tier == RepairTier.AI_RESEARCH:
                success = self._execute_tier3_repair(
                    component_name, error_message, error_context, repair_history
                )

            repair_duration = time.time() - repair_start_time

            # Enhanced post - repair validation and stability verification
            if success:
                post_repair_validation = self._perform_post_repair_validation(
                    component_name, repair_duration
                )

                if not post_repair_validation["stable"]:
                    self.logger.warning(
                        f"Post - repair validation failed: {post_repair_validation['issues']}"
                    )

                    if snapshot:
                        self.logger.info(
                            "Initiating automatic rollback due to validation failure"
                        )
                        rollback_result = self.safe_mode.rollback_to_snapshot(
                            snapshot.snapshot_id,
                                f"Post - repair validation failed for {component_name}: {post_repair_validation['issues']}",
                                )

                        if rollback_result.success:
                            success = False
                            self.logger.info(
                                "Automatic rollback completed successfully"
                            )
                            self._log_rollback_event(
                                component_name,
                                    snapshot.snapshot_id,
                                    "validation_failure",
                                    )
                        else:
                            self.logger.error(
                                f"Automatic rollback failed: {rollback_result.error_message}"
                            )
                            self._log_rollback_event(
                                component_name, snapshot.snapshot_id, "rollback_failed"
                            )

            # Update component health based on final outcome
            if success:
                self._update_component_health(component_name, ComponentStatus.HEALTHY)
                self.logger.info(
                    f"Component {component_name} successfully repaired and validated"
                )
            else:
                self._update_component_health(component_name, ComponentStatus.CRITICAL)
                self.logger.error(
                    f"Component {component_name} repair failed or was rolled back"
                )

            return success

        except Exception as e:
            self.logger.error(f"Exception in handle_component_failure: {e}")

            # Enhanced exception handling with automatic rollback
            if snapshot:
                try:
                    self.logger.info("Initiating emergency rollback due to exception")
                    rollback_result = self.safe_mode.rollback_to_snapshot(
                        snapshot.snapshot_id,
                            f"Emergency rollback - Exception during {component_name} repair: {str(e)}",
                            )
                    if rollback_result.success:
                        self.logger.info("Emergency rollback completed successfully")
                        self._log_rollback_event(
                            component_name, snapshot.snapshot_id, "exception_recovery"
                        )
                    else:
                        self.logger.error(
                            f"Emergency rollback failed: {rollback_result.error_message}"
                        )
                except Exception as rollback_error:
                    self.logger.error(
                        f"Emergency rollback failed with exception: {rollback_error}"
                    )

            self._update_component_health(component_name, ComponentStatus.CRITICAL)
            return False


    def _determine_repair_tier(
        self, component_name: str, repair_history: List[Dict]
    ) -> RepairTier:
        """Determine which repair tier to use based on history."""
        if not repair_history:
            return RepairTier.RESTART

        # Count recent attempts by tier
        recent_cutoff = datetime.now() - timedelta(hours = 1)
        recent_attempts = [
            attempt
            for attempt in repair_history
            if datetime.fromisoformat(attempt["created_at"]) > recent_cutoff
        ]

        tier1_attempts = len([a for a in recent_attempts if a["repair_tier"] == 1])
        tier2_attempts = len([a for a in recent_attempts if a["repair_tier"] == 2])

        if tier1_attempts < self.max_tier1_attempts:
            return RepairTier.RESTART
        elif tier2_attempts < self.max_tier2_attempts:
            return RepairTier.DEPENDENCY_CHECK
        else:
            return RepairTier.AI_RESEARCH


    def _execute_tier1_repair(
        self, component_name: str, error_message: str, error_context: Optional[Dict]
    ) -> bool:
        """Tier 1: Simple component restart."""
        start_time = time.time()
        repair_action = f"Restarting component: {component_name}"

        try:
            # Attempt to restart the component
            success = self._restart_component(component_name)

            outcome = RepairOutcome.SUCCESS if success else RepairOutcome.FAILURE
            execution_details = f"Restart {'successful' if success else 'failed'}"

        except Exception as e:
            success = False
            outcome = RepairOutcome.FAILURE
            execution_details = f"Restart exception: {str(e)}"

        # Log the repair attempt
        self._log_repair_attempt(
            RepairAttempt(
                component_name = component_name,
                    error_message = error_message,
                    error_type="component_failure",
                    repair_tier = RepairTier.RESTART,
                    repair_action = repair_action,
                    outcome = outcome,
                    execution_details = execution_details,
                    error_context = error_context,
                    duration = time.time() - start_time,
                    )
        )

        return success


    def _execute_tier2_repair(
        self, component_name: str, error_message: str, error_context: Optional[Dict]
    ) -> bool:
        """Tier 2: Dependency verification and repair."""
        start_time = time.time()
        repair_action = f"Checking dependencies for: {component_name}"

        try:
            # Check component dependencies
            dependency_issues = self._check_dependencies(component_name)

            if dependency_issues:
                # Attempt to fix dependency issues
                fix_success = self._fix_dependencies(component_name, dependency_issues)
                if fix_success:
                    # Try restarting after fixing dependencies
                    success = self._restart_component(component_name)
                    execution_details = f"Fixed dependencies: {dependency_issues}, restart {'successful' if success else 'failed'}"
                else:
                    success = False
                    execution_details = (
                        f"Failed to fix dependencies: {dependency_issues}"
                    )
            else:
                # No dependency issues found, try restart anyway
                success = self._restart_component(component_name)
                execution_details = f"No dependency issues found, restart {'successful' if success else 'failed'}"

            outcome = RepairOutcome.SUCCESS if success else RepairOutcome.FAILURE

        except Exception as e:
            success = False
            outcome = RepairOutcome.FAILURE
            execution_details = f"Dependency check exception: {str(e)}"

        # Log the repair attempt
        self._log_repair_attempt(
            RepairAttempt(
                component_name = component_name,
                    error_message = error_message,
                    error_type="dependency_failure",
                    repair_tier = RepairTier.DEPENDENCY_CHECK,
                    repair_action = repair_action,
                    outcome = outcome,
                    execution_details = execution_details,
                    error_context = error_context,
                    duration = time.time() - start_time,
                    )
        )

        return success


    def _execute_tier3_repair(
        self,
            component_name: str,
            error_message: str,
            error_context: Optional[Dict],
            repair_history: List[Dict],
            ) -> bool:
        """Tier 3: AI - powered research and novel solution generation."""
        start_time = time.time()
        repair_action = f"AI - powered repair research for: {component_name}"

        try:
            # Generate AI prompt using the repair history directly
            prompt = self._generate_ai_repair_prompt(
                component_name, error_message, repair_history
            )

            # Get AI - generated solution
            ai_response = self.ollama_client.generate_completion(prompt)

            if ai_response and ai_response.get("response"):
                solution = ai_response["response"]

                # Extract executable code from AI response
                executable_code = self._extract_executable_code(solution)

                if executable_code:
                    # Execute the AI - generated solution
                    success = self._execute_ai_solution(component_name, executable_code)
                    execution_details = (
                        f"AI solution executed: {executable_code[:200]}..."
                    )
                else:
                    success = False
                    execution_details = (
                        f"No executable code found in AI response: {solution[:200]}..."
                    )
            else:
                success = False
                execution_details = "Failed to get AI response"

            outcome = RepairOutcome.SUCCESS if success else RepairOutcome.FAILURE

        except Exception as e:
            success = False
            outcome = RepairOutcome.FAILURE
            execution_details = f"AI repair exception: {str(e)}"

        # Log the repair attempt
        self._log_repair_attempt(
            RepairAttempt(
                component_name = component_name,
                    error_message = error_message,
                    error_type="ai_research",
                    repair_tier = RepairTier.AI_RESEARCH,
                    repair_action = repair_action,
                    outcome = outcome,
                    execution_details = execution_details,
                    error_context = error_context,
                    duration = time.time() - start_time,
                    )
        )

        return success


    def _generate_ai_repair_prompt(
        self, component_name: str, error_message: str, repair_history: List[Dict]
    ) -> str:
        """Generate prompt for AI - powered repair research using the exact format specified in the Progressive Self - Repair Protocol."""
        # Format repair history as specified in the protocol
        if repair_history:
            failed_repairs = [
                f"Tier {r['repair_tier']}: {r['repair_action']} - {r['outcome']}"
                for r in repair_history[-10:]
            ]  # Last 10 attempts
            history_summary = ", ".join(failed_repairs)
        else:
            history_summary = "None"

        # Check if this is a creative component
        is_creative = component_name in [
            "linly_talker",
                "blender_compositor",
                "creative_pipeline",
                ]

        creative_context = ""
        if is_creative:
            creative_context = " Note: This component uses an isolated Python virtual environment (venv_creative) with creative dependencies (torch,
    opencv - python,
    librosa,
    etc.). Use 'source activate_creative.sh' before executing Python commands."

        # Use the exact prompt format from the Progressive Self - Repair Protocol specification
        return f"""
I am an autonomous system. The component '[{component_name}]' is failing with the error: '[{error_message}]'. I have already tried the following repairs: [{history_summary}].{creative_context} Based on this error, research \
    and suggest a new, different command - line or Python - based repair strategy. Formulate the solution as executable code.

Provide your response in this format:
```python
# Your repair solution here
```

OR

```bash
# Your shell commands here
```
"""


    def _extract_executable_code(self, ai_response: str) -> Optional[str]:
        """Extract executable code from AI response."""

        import re

        # Look for code blocks
        python_match = re.search(r"```python\\s*\\n(.*?)\\n```", ai_response, re.DOTALL)
        bash_match = re.search(r"```bash\\s*\\n(.*?)\\n```", ai_response, re.DOTALL)

        if python_match:
            return python_match.group(1).strip()
        elif bash_match:
            return bash_match.group(1).strip()

        return None


    def _execute_ai_solution(self, component_name: str, code: str) -> bool:
        """Execute AI - generated repair solution."""

        import tempfile

        try:
            # Check if this is a creative component
            is_creative = component_name in [
                "linly_talker",
                    "blender_compositor",
                    "creative_pipeline",
                    ]

            # Determine if it's Python or shell code
            if any(
                keyword in code for keyword in ["import ", "def ", "class ", "print("]
            ):
                # Execute as Python with proper environment
                if is_creative:
                    # Create a temporary file for the solution
                    with tempfile.NamedTemporaryFile(
                        mode="w", suffix=".py", delete = False
                    ) as f:
                        f.write(code)
                        temp_file = f.name

                    try:
                        # Execute within creative environment
                        cmd = [
                            "bash",
                                "-c",
                                f"source activate_creative.sh && python {temp_file}",
                                ]
                        result = subprocess.run(
                            cmd,
                                capture_output = True,
                                text = True,
                                timeout = 300,
                                cwd = os.getcwd(),
                                )
                        os.unlink(temp_file)
                        return result.returncode == 0
                    except Exception:
                        if os.path.exists(temp_file):
                            os.unlink(temp_file)
                        raise
                else:
                    # Execute in main environment
                    exec(code)
                    return True
            else:
                # Execute as shell command
                    if is_creative and "python" in code:
                    # Wrap shell command with creative environment activation
                    code = f"source activate_creative.sh && {code}"
                result = subprocess.run(
                    code, shell = True, capture_output = True, text = True, timeout = 60
                )
                return result.returncode == 0
        except Exception as e:
            self.logger.error(f"Failed to execute AI solution: {e}")
            return False


    def _restart_component(self, component_name: str) -> bool:
        """Restart a system component."""
        # Component - specific restart logic
        restart_commands = {
            "youtube_automation": "pkill -f youtube_automation && python -m backend.agents.youtube_automation &",
                "content_generator": "pkill -f content_generator && python -m backend.content.automated_author &",
                "ollama_service": "systemctl restart ollama || brew services restart ollama",
                "database": 'sqlite3 right_perspective.db "PRAGMA integrity_check;"',
                "linly_talker": "source activate_creative.sh && python -c \\"from backend.content.animate_avatar import LinlyTalkerEngine; engine = LinlyTalkerEngine(); print('Linly - Talker restarted')\\"",
                "blender_compositor": "source activate_creative.sh && python -c \\"from backend.content.blender_compositor import BlenderCompositor; compositor = BlenderCompositor(); print('Blender compositor restarted')\\"",
                "creative_pipeline": "source activate_creative.sh && python -c \\"import torch,
    cv2,
    librosa; print('Creative pipeline dependencies verified')\\"",
                }

        command = restart_commands.get(component_name)
        if not command:
            self.logger.warning(
                f"No restart command defined for component: {component_name}"
            )
            return False

        try:
            result = subprocess.run(
                command, shell = True, capture_output = True, text = True, timeout = 30
            )
            return result.returncode == 0
        except Exception as e:
            self.logger.error(f"Failed to restart {component_name}: {e}")
            return False


    def _check_dependencies(self, component_name: str) -> List[str]:
        """Check component dependencies and return list of issues."""
        issues = []

        # Component - specific dependency checks
        if component_name == "youtube_automation":
            # Check internet connectivity
            try:
                requests.get("https://www.youtube.com", timeout = 5)
            except Exception:
                issues.append("internet_connectivity")

            # Check YouTube API key
            if not os.getenv("YOUTUBE_API_KEY"):
                issues.append("missing_youtube_api_key")

        elif component_name == "ollama_service":
            # Check if Ollama is running
            try:
                requests.get("http://localhost:11434 / api / tags", timeout = 5)
            except Exception:
                issues.append("ollama_not_running")

        elif component_name == "database":
            # Check database file exists and is accessible
            if not os.path.exists(self.db_path):
                issues.append("database_file_missing")
            else:
                try:
                    with sqlite3.connect(self.db_path) as conn:
                        conn.execute("SELECT 1")
                except Exception:
                    issues.append("database_corrupted")

        elif component_name in [
            "linly_talker",
                "blender_compositor",
                "creative_pipeline",
                ]:
            # Check creative environment
            creative_env_path = "venv_creative"
            if not os.path.exists(creative_env_path):
                issues.append("creative_environment_missing")
            else:
                # Check if essential creative packages are installed
                try:
                    result = subprocess.run(
                        [
                            f"{creative_env_path}/bin / python",
                                "-c",
                                'import torch,
    cv2,
    librosa; print("Creative dependencies OK")',
                                ],
                            capture_output = True,
                            text = True,
                            timeout = 30,
                            )
                    if result.returncode != 0:
                        issues.append("creative_dependencies_missing")
                except Exception:
                    issues.append("creative_environment_corrupted")

        return issues


    def _fix_dependencies(self, component_name: str, issues: List[str]) -> bool:
        """Attempt to fix dependency issues."""
        success = True

        for issue in issues:
            try:
                if issue == "ollama_not_running":
                    subprocess.run("brew services start ollama",
    shell = True,
    timeout = 30)
                elif issue == "database_file_missing":
                    # Recreate database from schema
                    with open("schema.sql", "r") as f:
                        schema = f.read()
                    with sqlite3.connect(self.db_path) as conn:
                        conn.executescript(schema)
                elif issue == "missing_youtube_api_key":
                    self.logger.error(
                        "YouTube API key missing - manual intervention required"
                    )
                    success = False
                elif issue == "creative_environment_missing":
                    # Recreate creative environment
                    result = subprocess.run(
                        ["python", "scripts / setup_creative_environment.py"],
                            check = True,
                            timeout = 300,
                            )
                elif issue == "creative_dependencies_missing":
                    # Reinstall creative dependencies
                    result = subprocess.run(
                        ["python", "scripts / setup_creative_environment.py", "--update"],
                            check = True,
                            timeout = 300,
                            )
                elif issue == "creative_environment_corrupted":
                    # Remove and recreate creative environment
                    subprocess.run(["rm", "-rf", "venv_creative"], check = True)
                    result = subprocess.run(
                        ["python", "scripts / setup_creative_environment.py"],
                            check = True,
                            timeout = 300,
                            )
                # Add more dependency fixes as needed
            except Exception as e:
                self.logger.error(f"Failed to fix dependency {issue}: {e}")
                success = False

        return success


    def _get_repair_history(self, component_name: str, limit: int = 50) -> List[Dict]:
        """Get repair history for a component from the master schema."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT * FROM repair_log
                    WHERE component_name = ?
                    ORDER BY attempt_timestamp DESC
                    LIMIT ?
                """,
                    (component_name, limit),
                        )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Failed to get repair history: {e}")
            return []


    def _log_repair_attempt(
        self, attempt: RepairAttempt, snapshot_id: Optional[str] = None
    ):
        """Log a repair attempt to the database using the master schema structure with snapshot information."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Check if snapshot_id column exists, add if not
                cursor.execute("PRAGMA table_info(repair_log)")
                columns = [column[1] for column in cursor.fetchall()]

                if "snapshot_id" not in columns:
                    cursor.execute("ALTER TABLE repair_log ADD COLUMN snapshot_id TEXT")

                cursor.execute(
                    """
                    INSERT INTO repair_log (
                        component_name, error_message, repair_action, repair_tier,
                            outcome, execution_details, resolution_time_seconds, snapshot_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        attempt.component_name,
                            attempt.error_message,
                            attempt.repair_action,
                            attempt.repair_tier.value,
                            attempt.outcome.value if attempt.outcome else "pending",
                            (
                            json.dumps(
                                {
                                    "error_type": attempt.error_type,
                                        "error_context": attempt.error_context,
                                        "execution_details": attempt.execution_details,
                                        }
                            )
                            if attempt.execution_details or attempt.error_context
                            else None
                        ),
                            int(attempt.duration) if attempt.duration else None,
                            snapshot_id,
                            ),
                        )
                conn.commit()
                self.logger.info(
                    f"Logged repair attempt for {attempt.component_name}: {attempt.repair_action}"
                )
        except Exception as e:
            self.logger.error(f"Failed to log repair attempt: {e}")


    def _update_component_health(self, component_name: str, status: ComponentStatus):
        """Update component health status."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Check if component exists
                cursor.execute(
                    "SELECT id, consecutive_failures, total_failures FROM component_health WHERE component_name = ?",
                        (component_name,),
                        )
                existing = cursor.fetchone()

                if existing:
                    # Update existing record
                    component_id, consecutive_failures, total_failures = existing

                    if status == ComponentStatus.HEALTHY:
                        consecutive_failures = 0
                    else:
                        consecutive_failures += 1
                        total_failures += 1

                    cursor.execute(
                        """
                        UPDATE component_health
                        SET status = ?, last_check = CURRENT_TIMESTAMP,
                            consecutive_failures = ?, total_failures = ?,
                                last_failure_at = CASE WHEN ? != 'healthy' THEN CURRENT_TIMESTAMP ELSE last_failure_at END,
                                updated_at = CURRENT_TIMESTAMP
                        WHERE component_name = ?
                    """,
                        (
                            status.value,
                                consecutive_failures,
                                total_failures,
                                status.value,
                                component_name,
                                ),
                            )
                else:
                    # Insert new record
                    cursor.execute(
                        """
                        INSERT INTO component_health (
                            component_name, status, consecutive_failures, total_failures,
                                last_failure_at
                        ) VALUES (?, ?, ?, ?, ?)
                    """,
                        (
                            component_name,
                                status.value,
                                0 if status == ComponentStatus.HEALTHY else 1,
                                0 if status == ComponentStatus.HEALTHY else 1,
                                (
                                datetime.now().isoformat()
                                if status != ComponentStatus.HEALTHY
                                else None
                            ),
                                ),
                            )

                conn.commit()
        except Exception as e:
            self.logger.error(f"Failed to update component health: {e}")


    def get_system_health_report(self) -> Dict[str, Any]:
        """Generate comprehensive system health report."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Get component health summary
                cursor.execute(
                    """
                    SELECT status, COUNT(*) as count
                    FROM component_health
                    GROUP BY status
                """
                )
                health_summary = {
                    row["status"]: row["count"] for row in cursor.fetchall()
                }

                # Get recent repair activity
                cursor.execute(
                    """
                    SELECT repair_tier, repair_outcome, COUNT(*) as count
                    FROM repair_log
                    WHERE created_at > datetime('now', '-24 hours')
                    GROUP BY repair_tier, repair_outcome
                """
                )
                repair_activity = [dict(row) for row in cursor.fetchall()]

                # Get most problematic components
                cursor.execute(
                    """
                    SELECT component_name, consecutive_failures, total_failures, status
                    FROM component_health
                    WHERE status != 'healthy'
                    ORDER BY consecutive_failures DESC, total_failures DESC
                    LIMIT 10
                """
                )
                problematic_components = [dict(row) for row in cursor.fetchall()]

                return {
                    "timestamp": datetime.now().isoformat(),
                        "health_summary": health_summary,
                        "repair_activity_24h": repair_activity,
                        "problematic_components": problematic_components,
                        "system_status": (
                        "healthy"
                        if health_summary.get("critical", 0) == 0
                        else "degraded"
                    ),
                        }
        except Exception as e:
            self.logger.error(f"Failed to generate health report: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}


    def _perform_pre_repair_validation(
        self, component_name: str, error_message: str
    ) -> Dict[str, Any]:
        """Enhanced pre - repair validation to ensure repair safety."""
        validation_result = {
            "can_proceed": True,
                "reason": None,
                "risk_level": "low",
                "recommendations": [],
                }

        try:
            # Check system resources
            memory_usage = psutil.virtual_memory().percent
            disk_usage = psutil.disk_usage("/").percent
            cpu_usage = psutil.cpu_percent(interval = 1)

            if memory_usage > 90:
                validation_result["can_proceed"] = False
                validation_result["reason"] = f"Critical memory usage: {memory_usage}%"
                validation_result["risk_level"] = "critical"
                return validation_result

            if disk_usage > 95:
                validation_result["can_proceed"] = False
                validation_result["reason"] = f"Critical disk usage: {disk_usage}%"
                validation_result["risk_level"] = "critical"
                return validation_result

            # Check for concurrent repair operations
            recent_repairs = self._get_recent_repair_attempts(minutes = 5)
            if len(recent_repairs) > 3:
                validation_result["can_proceed"] = False
                validation_result["reason"] = "Too many concurrent repair attempts"
                validation_result["risk_level"] = "high"
                return validation_result

            # Component - specific pre - repair checks
            if component_name in ["database", "ollama_service"]:
                # Critical components require extra validation
                if self._is_component_in_use(component_name):
                    validation_result["risk_level"] = "high"
                    validation_result["recommendations"].append(
                        "Consider scheduling repair during low usage"
                    )

            # Check error pattern for known dangerous scenarios
            dangerous_patterns = ["corruption", "segfault", "memory leak", "deadlock"]
            if any(pattern in error_message.lower() for pattern in dangerous_patterns):
                validation_result["risk_level"] = "high"
                validation_result["recommendations"].append(
                    "High - risk error detected - proceed with caution"
                )

            self.logger.info(
                f"Pre - repair validation for {component_name}: {validation_result['risk_level']} risk"
            )
            return validation_result

        except Exception as e:
            self.logger.error(f"Pre - repair validation failed: {e}")
            validation_result["can_proceed"] = False
            validation_result["reason"] = f"Validation error: {str(e)}"
            return validation_result


    def _perform_post_repair_validation(
        self, component_name: str, repair_duration: float
    ) -> Dict[str, Any]:
        """Enhanced post - repair validation to ensure system stability."""
        validation_result = {
            "stable": True,
                "issues": [],
                "performance_impact": "none",
                "recommendations": [],
                }

        try:
            # Basic system stability checks
            if not os.path.exists(self.db_path):
                validation_result["stable"] = False
                validation_result["issues"].append("Database file missing after repair")
                return validation_result

            # Test database connectivity and integrity
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("PRAGMA integrity_check")
                    conn.execute("SELECT COUNT(*) FROM repair_log")
            except Exception as db_error:
                validation_result["stable"] = False
                validation_result["issues"].append(
                    f"Database integrity compromised: {str(db_error)}"
                )

            # Component - specific post - repair validation
            if component_name == "ollama_service":
                try:
                    response = requests.get(
                        "http://localhost:11434 / api / tags", timeout = 10
                    )
                    if response.status_code != 200:
                        validation_result["stable"] = False
                        validation_result["issues"].append(
                            "Ollama service not responding correctly"
                        )
                except Exception as ollama_error:
                    validation_result["stable"] = False
                    validation_result["issues"].append(
                        f"Ollama connectivity failed: {str(ollama_error)}"
                    )

            elif component_name in [
                "linly_talker",
                    "blender_compositor",
                    "creative_pipeline",
                    ]:
                # Validate creative environment
                try:
                    result = subprocess.run(
                        [
                            "venv_creative / bin / python",
                                "-c",
                                'import torch,
    cv2,
    librosa; print("Creative environment OK")',
                                ],
                            capture_output = True,
                            text = True,
                            timeout = 30,
                            )
                    if result.returncode != 0:
                        validation_result["stable"] = False
                        validation_result["issues"].append(
                            "Creative environment validation failed"
                        )
                except Exception as creative_error:
                    validation_result["stable"] = False
                    validation_result["issues"].append(
                        f"Creative environment error: {str(creative_error)}"
                    )

            # Performance impact assessment
            if repair_duration > 60:
                validation_result["performance_impact"] = "high"
                validation_result["recommendations"].append(
                    "Long repair duration may indicate underlying issues"
                )
            elif repair_duration > 30:
                validation_result["performance_impact"] = "moderate"

            # System resource check after repair
            memory_usage = psutil.virtual_memory().percent
            if memory_usage > 85:
                validation_result["issues"].append(
                    f"High memory usage after repair: {memory_usage}%"
                )
                validation_result["recommendations"].append(
                    "Monitor memory usage closely"
                )

            # Check for new error patterns
            time.sleep(2)  # Allow time for any immediate post - repair issues
            recent_errors = self._check_for_immediate_errors(component_name)
            if recent_errors:
                validation_result["stable"] = False
                validation_result["issues"].extend(recent_errors)

            self.logger.info(
                f"Post - repair validation for {component_name}: {'STABLE' if validation_result['stable'] else 'UNSTABLE'}"
            )
            return validation_result

        except Exception as e:
            self.logger.error(f"Post - repair validation failed: {e}")
            validation_result["stable"] = False
            validation_result["issues"].append(f"Validation error: {str(e)}")
            return validation_result


    def _get_recent_repair_attempts(self, minutes: int = 5) -> List[Dict]:
        """Get repair attempts from the last N minutes."""
        try:
            cutoff_time = datetime.now() - timedelta(minutes = minutes)
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT * FROM repair_log
                    WHERE attempt_timestamp > ?
                    ORDER BY attempt_timestamp DESC
                """,
                    (cutoff_time.isoformat(),),
                        )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Failed to get recent repair attempts: {e}")
            return []


    def _is_component_in_use(self, component_name: str) -> bool:
        """Check if a component is currently in active use."""
        try:
            if component_name == "database":
                # Check for active database connections
                result = subprocess.run(
                    ["lsof", self.db_path], capture_output = True, text = True
                )
                return len(result.stdout.strip()) > 0
            elif component_name == "ollama_service":
                # Check for active Ollama processes
                for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                    if "ollama" in proc.info["name"].lower():
                        return True
            return False
        except Exception:
            return False


    def _check_for_immediate_errors(self, component_name: str) -> List[str]:
        """Check for immediate errors after repair."""
        errors = []
        try:
            # Component - specific error checking
            if component_name == "ollama_service":
                try:
                    response = requests.get(
                        "http://localhost:11434 / api / tags", timeout = 5
                    )
                    if response.status_code >= 400:
                        errors.append(f"Ollama HTTP error: {response.status_code}")
                except requests.exceptions.RequestException as e:
                    errors.append(f"Ollama connection error: {str(e)}")

            # Check system logs for recent errors (if available)
            # This is a simplified check - in production, you might want to check actual system logs

        except Exception as e:
            errors.append(f"Error checking failed: {str(e)}")

        return errors


    def _log_rollback_event(
        self, component_name: str, snapshot_id: str, rollback_reason: str
    ):
        """Log rollback events for audit and analysis."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Create rollback_log table if it doesn't exist
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS rollback_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                            component_name TEXT NOT NULL,
                            snapshot_id TEXT NOT NULL,
                            rollback_reason TEXT NOT NULL,
                            rollback_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                cursor.execute(
                    """
                    INSERT INTO rollback_log (component_name,
    snapshot_id,
    rollback_reason)
                    VALUES (?, ?, ?)
                """,
                    (component_name, snapshot_id, rollback_reason),
                        )

                conn.commit()
                self.logger.info(
                    f"Logged rollback event for {component_name}: {rollback_reason}"
                )
        except Exception as e:
            self.logger.error(f"Failed to log rollback event: {e}")


    def _verify_system_stability(self, component_name: str) -> bool:
        """Legacy method - now redirects to enhanced post - repair validation."""
        validation_result = self._perform_post_repair_validation(component_name, 0)
        return validation_result["stable"]