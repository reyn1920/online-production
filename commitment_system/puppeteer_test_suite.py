"""
Puppeteer Test Suite for Commitment System
Tests and verifies the commitment system works in real browser environments.
"""

import json
import asyncio
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import subprocess
import threading
import queue
import tempfile
import os

from .memory_store import memory_store
from .behavioral_contract import behavioral_contract
from .compliance_checker import compliance_checker
from .audit_trail import audit_trail, AuditEventType, ComplianceStatus
from .enforcement_engine import enforcement_engine
from .real_time_validator import real_time_validator, ValidationMode, ActionCategory

@dataclass
class PuppeteerTestCase:
    """Test case for Puppeteer validation"""
    test_id: str
    name: str
    description: str
    url: str
    actions: List[Dict[str, Any]]
    expected_commitments: List[str]
    expected_violations: List[str]
    timeout_seconds: int = 30
    priority: int = 5

@dataclass
class PuppeteerTestResult:
    """Result of a Puppeteer test"""
    test_id: str
    success: bool
    execution_time_ms: float
    screenshots_taken: List[str]
    commitments_verified: List[str]
    violations_detected: List[str]
    error_message: Optional[str] = None
    browser_logs: List[str] = None
    
    def __post_init__(self):
        if self.browser_logs is None:
            self.browser_logs = []

class PuppeteerCommitmentTester:
    """
    Comprehensive Puppeteer testing system for commitment validation.
    Tests the commitment system in real browser environments.
    """
    
    def __init__(self, test_server_url: str = "http://localhost:3000"):
        self.test_server_url = test_server_url
        self.test_results: List[PuppeteerTestResult] = []
        self.screenshots_dir = Path(__file__).parent / "test_screenshots"
        self.screenshots_dir.mkdir(exist_ok=True)
        
        # Test configuration
        self.browser_options = {
            "headless": False,  # Show browser for debugging
            "args": [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-web-security",
                "--allow-running-insecure-content"
            ]
        }
        
        # Initialize test cases
        self.test_cases = self._create_test_cases()
        
        # Statistics
        self.total_tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.total_execution_time = 0.0
    
    def _create_test_cases(self) -> List[PuppeteerTestCase]:
        """Create comprehensive test cases for commitment validation"""
        return [
            PuppeteerTestCase(
                test_id="commitment_display_test",
                name="Commitment Display Verification",
                description="Verify that commitments are properly displayed in the UI",
                url=f"{self.test_server_url}/commitments",
                actions=[
                    {"type": "navigate", "url": f"{self.test_server_url}/commitments"},
                    {"type": "wait", "selector": ".commitment-list", "timeout": 5000},
                    {"type": "screenshot", "name": "commitments_page"},
                    {"type": "evaluate", "script": "return document.querySelectorAll('.commitment-item').length"}
                ],
                expected_commitments=["Always use Puppeteer for web testing"],
                expected_violations=[]
            ),
            
            PuppeteerTestCase(
                test_id="real_time_validation_test",
                name="Real-time Validation Test",
                description="Test real-time validation of user actions",
                url=f"{self.test_server_url}/test-validation",
                actions=[
                    {"type": "navigate", "url": f"{self.test_server_url}/test-validation"},
                    {"type": "fill", "selector": "#action-input", "value": "delete all files"},
                    {"type": "click", "selector": "#validate-button"},
                    {"type": "wait", "selector": ".validation-result", "timeout": 3000},
                    {"type": "screenshot", "name": "validation_result"},
                    {"type": "evaluate", "script": "return document.querySelector('.validation-result').textContent"}
                ],
                expected_commitments=[],
                expected_violations=["Action violates safety commitment"]
            ),
            
            PuppeteerTestCase(
                test_id="behavioral_contract_test",
                name="Behavioral Contract Enforcement",
                description="Test behavioral contract enforcement in browser",
                url=f"{self.test_server_url}/behavioral-test",
                actions=[
                    {"type": "navigate", "url": f"{self.test_server_url}/behavioral-test"},
                    {"type": "click", "selector": "#trigger-violation"},
                    {"type": "wait", "selector": ".enforcement-message", "timeout": 3000},
                    {"type": "screenshot", "name": "enforcement_message"},
                    {"type": "evaluate", "script": "return document.querySelector('.enforcement-message').classList.contains('blocked')"}
                ],
                expected_commitments=[],
                expected_violations=["Behavioral contract violation detected"]
            ),
            
            PuppeteerTestCase(
                test_id="audit_trail_test",
                name="Audit Trail Verification",
                description="Verify audit trail is properly recorded",
                url=f"{self.test_server_url}/audit",
                actions=[
                    {"type": "navigate", "url": f"{self.test_server_url}/audit"},
                    {"type": "wait", "selector": ".audit-log", "timeout": 5000},
                    {"type": "screenshot", "name": "audit_trail"},
                    {"type": "evaluate", "script": "return document.querySelectorAll('.audit-entry').length"},
                    {"type": "click", "selector": ".refresh-audit"},
                    {"type": "wait", "timeout": 1000},
                    {"type": "screenshot", "name": "audit_trail_refreshed"}
                ],
                expected_commitments=[],
                expected_violations=[]
            ),
            
            PuppeteerTestCase(
                test_id="memory_persistence_test",
                name="Memory Persistence Test",
                description="Test that commitments persist across page reloads",
                url=f"{self.test_server_url}/memory-test",
                actions=[
                    {"type": "navigate", "url": f"{self.test_server_url}/memory-test"},
                    {"type": "fill", "selector": "#commitment-input", "value": "Test commitment for persistence"},
                    {"type": "click", "selector": "#save-commitment"},
                    {"type": "wait", "selector": ".success-message", "timeout": 3000},
                    {"type": "screenshot", "name": "commitment_saved"},
                    {"type": "reload"},
                    {"type": "wait", "selector": ".commitment-list", "timeout": 5000},
                    {"type": "screenshot", "name": "after_reload"},
                    {"type": "evaluate", "script": "return document.querySelector('.commitment-list').textContent.includes('Test commitment for persistence')"}
                ],
                expected_commitments=["Test commitment for persistence"],
                expected_violations=[]
            ),
            
            PuppeteerTestCase(
                test_id="compliance_dashboard_test",
                name="Compliance Dashboard Test",
                description="Test the compliance monitoring dashboard",
                url=f"{self.test_server_url}/compliance",
                actions=[
                    {"type": "navigate", "url": f"{self.test_server_url}/compliance"},
                    {"type": "wait", "selector": ".compliance-dashboard", "timeout": 5000},
                    {"type": "screenshot", "name": "compliance_dashboard"},
                    {"type": "click", "selector": ".compliance-metric"},
                    {"type": "wait", "selector": ".metric-details", "timeout": 3000},
                    {"type": "screenshot", "name": "compliance_details"},
                    {"type": "evaluate", "script": "return document.querySelector('.compliance-score').textContent"}
                ],
                expected_commitments=[],
                expected_violations=[]
            ),
            
            PuppeteerTestCase(
                test_id="enforcement_blocking_test",
                name="Enforcement Blocking Test",
                description="Test that enforcement engine properly blocks violations",
                url=f"{self.test_server_url}/enforcement-test",
                actions=[
                    {"type": "navigate", "url": f"{self.test_server_url}/enforcement-test"},
                    {"type": "click", "selector": "#dangerous-action"},
                    {"type": "wait", "timeout": 2000},
                    {"type": "screenshot", "name": "blocked_action"},
                    {"type": "evaluate", "script": "return document.querySelector('.block-message') !== null"},
                    {"type": "click", "selector": "#safe-action"},
                    {"type": "wait", "timeout": 2000},
                    {"type": "screenshot", "name": "allowed_action"}
                ],
                expected_commitments=[],
                expected_violations=["Dangerous action blocked by enforcement engine"]
            )
        ]
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all Puppeteer tests and return comprehensive results"""
        print("🚀 Starting Puppeteer Commitment System Tests...")
        
        start_time = time.time()
        results = []
        
        # Set validator to learning mode for testing
        original_mode = real_time_validator.validation_mode
        real_time_validator.set_validation_mode(ValidationMode.LEARNING)
        
        try:
            for test_case in self.test_cases:
                print(f"🧪 Running test: {test_case.name}")
                result = await self._run_single_test(test_case)
                results.append(result)
                
                if result.success:
                    self.tests_passed += 1
                    print(f"✅ {test_case.name} - PASSED")
                else:
                    self.tests_failed += 1
                    print(f"❌ {test_case.name} - FAILED: {result.error_message}")
                
                self.total_tests_run += 1
                
                # Brief pause between tests
                await asyncio.sleep(1)
            
            self.total_execution_time = time.time() - start_time
            
            # Generate comprehensive report
            report = self._generate_test_report(results)
            
            # Log to audit trail
            audit_trail.log_action(
                f"Puppeteer test suite completed: {self.tests_passed}/{self.total_tests_run} passed",
                action_type="puppeteer_testing",
                compliance_status=ComplianceStatus.COMPLIANT if self.tests_failed == 0 else ComplianceStatus.WARNING,
                context={"test_results": report}
            )
            
            return report
            
        finally:
            # Restore original validation mode
            real_time_validator.set_validation_mode(original_mode)
    
    async def _run_single_test(self, test_case: PuppeteerTestCase) -> PuppeteerTestResult:
        """Run a single Puppeteer test case"""
        start_time = time.time()
        screenshots_taken = []
        browser_logs = []
        commitments_verified = []
        violations_detected = []
        error_message = None
        
        try:
            # Create test script for Puppeteer
            test_script = self._generate_puppeteer_script(test_case)
            
            # Write script to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(test_script)
                script_path = f.name
            
            try:
                # Run Puppeteer script
                result = subprocess.run([
                    'node', script_path
                ], capture_output=True, text=True, timeout=test_case.timeout_seconds)
                
                if result.returncode == 0:
                    # Parse results from stdout
                    output = json.loads(result.stdout)
                    screenshots_taken = output.get('screenshots', [])
                    browser_logs = output.get('logs', [])
                    
                    # Verify commitments and violations
                    commitments_verified = self._verify_commitments(test_case, output)
                    violations_detected = self._detect_violations(test_case, output)
                    
                    success = True
                else:
                    error_message = result.stderr
                    success = False
                    
            finally:
                # Clean up temporary script
                os.unlink(script_path)
            
        except Exception as e:
            error_message = str(e)
            success = False
        
        execution_time = (time.time() - start_time) * 1000
        
        return PuppeteerTestResult(
            test_id=test_case.test_id,
            success=success,
            execution_time_ms=execution_time,
            screenshots_taken=screenshots_taken,
            commitments_verified=commitments_verified,
            violations_detected=violations_detected,
            error_message=error_message,
            browser_logs=browser_logs
        )
    
    def _generate_puppeteer_script(self, test_case: PuppeteerTestCase) -> str:
        """Generate a Puppeteer script for the test case"""
        script = f"""
const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

(async () => {{
    const browser = await puppeteer.launch({json.dumps(self.browser_options)});
    const page = await browser.newPage();
    
    const results = {{
        screenshots: [],
        logs: [],
        evaluations: [],
        errors: []
    }};
    
    // Capture console logs
    page.on('console', msg => {{
        results.logs.push({{
            type: msg.type(),
            text: msg.text(),
            timestamp: new Date().toISOString()
        }});
    }});
    
    // Capture errors
    page.on('error', err => {{
        results.errors.push({{
            message: err.message,
            stack: err.stack,
            timestamp: new Date().toISOString()
        }});
    }});
    
    try {{
"""
        
        # Add actions
        for i, action in enumerate(test_case.actions):
            if action['type'] == 'navigate':
                script += f"""
        await page.goto('{action['url']}', {{ waitUntil: 'networkidle2' }});
"""
            elif action['type'] == 'wait':
                if 'selector' in action:
                    timeout = action.get('timeout', 5000)
                    script += f"""
        await page.waitForSelector('{action['selector']}', {{ timeout: {timeout} }});
"""
                else:
                    timeout = action.get('timeout', 1000)
                    script += f"""
        await page.waitForTimeout({timeout});
"""
            elif action['type'] == 'click':
                script += f"""
        await page.click('{action['selector']}');
"""
            elif action['type'] == 'fill':
                script += f"""
        await page.type('{action['selector']}', '{action['value']}');
"""
            elif action['type'] == 'screenshot':
                screenshot_path = str(self.screenshots_dir / f"{test_case.test_id}_{action['name']}.png")
                script += f"""
        await page.screenshot({{ path: '{screenshot_path}', fullPage: true }});
        results.screenshots.push('{screenshot_path}');
"""
            elif action['type'] == 'evaluate':
                script += f"""
        const evaluation_{i} = await page.evaluate(() => {{
            {action['script']}
        }});
        results.evaluations.push({{
            script: `{action['script']}`,
            result: evaluation_{i}
        }});
"""
            elif action['type'] == 'reload':
                script += f"""
        await page.reload({{ waitUntil: 'networkidle2' }});
"""
        
        script += f"""
    }} catch (error) {{
        results.errors.push({{
            message: error.message,
            stack: error.stack,
            timestamp: new Date().toISOString()
        }});
    }} finally {{
        await browser.close();
        console.log(JSON.stringify(results));
    }}
}})();
"""
        
        return script
    
    def _verify_commitments(self, test_case: PuppeteerTestCase, output: Dict[str, Any]) -> List[str]:
        """Verify that expected commitments were found"""
        verified = []
        
        # Check evaluations and logs for commitment-related content
        for evaluation in output.get('evaluations', []):
            result = evaluation.get('result', '')
            for expected_commitment in test_case.expected_commitments:
                if expected_commitment.lower() in str(result).lower():
                    verified.append(expected_commitment)
        
        for log in output.get('logs', []):
            text = log.get('text', '')
            for expected_commitment in test_case.expected_commitments:
                if expected_commitment.lower() in text.lower():
                    verified.append(expected_commitment)
        
        return list(set(verified))  # Remove duplicates
    
    def _detect_violations(self, test_case: PuppeteerTestCase, output: Dict[str, Any]) -> List[str]:
        """Detect violations in the test output"""
        detected = []
        
        # Check for expected violations
        for evaluation in output.get('evaluations', []):
            result = evaluation.get('result', '')
            for expected_violation in test_case.expected_violations:
                if expected_violation.lower() in str(result).lower():
                    detected.append(expected_violation)
        
        for log in output.get('logs', []):
            text = log.get('text', '')
            for expected_violation in test_case.expected_violations:
                if expected_violation.lower() in text.lower():
                    detected.append(expected_violation)
        
        # Check for error patterns that indicate violations
        for error in output.get('errors', []):
            message = error.get('message', '')
            if 'violation' in message.lower() or 'blocked' in message.lower():
                detected.append(f"Error-based violation: {message}")
        
        return list(set(detected))  # Remove duplicates
    
    def _generate_test_report(self, results: List[PuppeteerTestResult]) -> Dict[str, Any]:
        """Generate a comprehensive test report"""
        return {
            "summary": {
                "total_tests": self.total_tests_run,
                "passed": self.tests_passed,
                "failed": self.tests_failed,
                "success_rate": (self.tests_passed / max(1, self.total_tests_run)) * 100,
                "total_execution_time_ms": self.total_execution_time * 1000
            },
            "test_results": [asdict(result) for result in results],
            "screenshots_directory": str(self.screenshots_dir),
            "timestamp": datetime.now().isoformat(),
            "browser_options": self.browser_options,
            "recommendations": self._generate_recommendations(results)
        }
    
    def _generate_recommendations(self, results: List[PuppeteerTestResult]) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        failed_tests = [r for r in results if not r.success]
        if failed_tests:
            recommendations.append(f"Review {len(failed_tests)} failed tests and fix underlying issues")
        
        slow_tests = [r for r in results if r.execution_time_ms > 10000]  # > 10 seconds
        if slow_tests:
            recommendations.append(f"Optimize {len(slow_tests)} slow-running tests for better performance")
        
        if all(r.success for r in results):
            recommendations.append("All tests passed! Commitment system is working correctly in browser environments")
        
        # Check for commitment verification
        commitment_tests = [r for r in results if r.commitments_verified]
        if commitment_tests:
            recommendations.append("Commitment verification is working properly")
        
        # Check for violation detection
        violation_tests = [r for r in results if r.violations_detected]
        if violation_tests:
            recommendations.append("Violation detection is functioning correctly")
        
        return recommendations
    
    def run_specific_test(self, test_id: str) -> Optional[PuppeteerTestResult]:
        """Run a specific test by ID"""
        test_case = next((tc for tc in self.test_cases if tc.test_id == test_id), None)
        if not test_case:
            return None
        
        return asyncio.run(self._run_single_test(test_case))
    
    def get_test_statistics(self) -> Dict[str, Any]:
        """Get comprehensive test statistics"""
        return {
            "total_tests_available": len(self.test_cases),
            "total_tests_run": self.total_tests_run,
            "tests_passed": self.tests_passed,
            "tests_failed": self.tests_failed,
            "success_rate": (self.tests_passed / max(1, self.total_tests_run)) * 100,
            "average_execution_time_ms": (self.total_execution_time * 1000) / max(1, self.total_tests_run),
            "screenshots_directory": str(self.screenshots_dir),
            "test_server_url": self.test_server_url
        }

# Integration with the commitment system
class CommitmentSystemPuppeteerIntegration:
    """
    Integration layer between the commitment system and Puppeteer testing.
    Provides real-time validation of browser-based actions.
    """
    
    def __init__(self):
        self.tester = PuppeteerCommitmentTester()
        self.active_tests = {}
        self.test_queue = queue.Queue()
    
    def validate_browser_action(self, action_type: str, action_details: Dict[str, Any]) -> bool:
        """Validate a browser action against commitments"""
        # Use real-time validator to check the action
        response = real_time_validator.validate_action_sync(
            action_category=ActionCategory.SYSTEM_ACTION,
            action_name=f"browser_{action_type}",
            action_parameters=action_details,
            context={"source": "puppeteer_integration"}
        )
        
        # Log the validation
        audit_trail.log_action(
            f"Browser action validated: {action_type}",
            action_type="browser_validation",
            compliance_status=ComplianceStatus.COMPLIANT if response.allowed else ComplianceStatus.VIOLATION,
            context={
                "action_details": action_details,
                "validation_response": asdict(response)
            }
        )
        
        return response.allowed
    
    def run_commitment_verification_tests(self) -> Dict[str, Any]:
        """Run tests specifically for commitment verification"""
        commitment_tests = [
            tc for tc in self.tester.test_cases 
            if 'commitment' in tc.name.lower() or tc.expected_commitments
        ]
        
        results = []
        for test_case in commitment_tests:
            result = asyncio.run(self.tester._run_single_test(test_case))
            results.append(result)
        
        return {
            "commitment_verification_results": [asdict(r) for r in results],
            "total_commitment_tests": len(commitment_tests),
            "passed_commitment_tests": sum(1 for r in results if r.success)
        }

# Global instances
puppeteer_tester = PuppeteerCommitmentTester()
puppeteer_integration = CommitmentSystemPuppeteerIntegration()