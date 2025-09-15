#!/usr/bin/env python3
"""
Enhanced Puppeteer Service for Web AI Integration and Code Quality Automation
Handles browser automation for interacting with web AI platforms and code analysis tools
"""

import asyncio
import json
import logging
import time
import subprocess
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING
from pathlib import Path

if TYPE_CHECKING:
    from integrations.mcp_client import MCPClient

@dataclass
class BrowserSession:
    """Browser session information"""
    session_id: str
    platform: str
    url: str
    created_at: datetime
    last_used: datetime
    is_active: bool = True

@dataclass
class CodeQualityResult:
    """Code quality analysis result"""
    tool: str
    status: str
    issues: List[Dict[str, Any]]
    score: Optional[float] = None
    report_url: Optional[str] = None

class EnhancedPuppeteerService:
    """Enhanced service for managing Puppeteer browser automation with code quality features"""

    def __init__(self, config: Optional[Dict[str, Any]] = None, mcp_client: Optional['MCPClient'] = None):
        """Initialize Enhanced Puppeteer service"""
        self.config = config or self._get_default_config()
        self.logger = self._setup_logging()
        self.sessions = {}
        self.mcp_available = True
        self.mcp_client: Optional['MCPClient'] = mcp_client
        self.code_quality_tools = {
            'flake8': self._run_flake8,
            'pylint': self._run_pylint,
            'bandit': self._run_bandit,
            'sonarqube': self._automate_sonarqube
        }

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration with macOS compatibility fixes"""
        return {
            "browser": {
                "headless": False,
                "width": 1280,
                "height": 720,
                "timeout": 30000,
                "args": [
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-accelerated-2d-canvas",
                    "--no-first-run",
                    "--no-zygote",
                    "--disable-gpu",
                    "--disable-blink-features=AutomationControlled",
                    "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                ],
                "ignoreDefaultArgs": ["--disable-extensions"],
                "slowMo": 100
            },
            "retry": {"max_attempts": 3, "delay": 2},
            "selectors": {
                "chatgpt": {
                    "input": 'textarea[data-id="root"]',
                    "send_button": 'button[data-testid="send-button"]',
                    "response": '[data-message-author-role="assistant"] .markdown',
                    "loading": ".result-streaming"
                },
                "gemini": {
                    "input": '.ql-editor[contenteditable="true"]',
                    "send_button": 'button[aria-label="Send message"]',
                    "response": "[data-response-index] .markdown",
                    "loading": ".loading-indicator"
                },
                "claude": {
                    "input": 'div[contenteditable="true"][data-testid="chat-input"]',
                    "send_button": 'button[aria-label="Send Message"]',
                    "response": '[data-testid="conversation"] .font-claude-message',
                    "loading": ".thinking-indicator"
                },
                "sonarqube": {
                    "login_button": 'button[data-testid="login"]',
                    "project_search": 'input[placeholder="Search projects"]',
                    "quality_gate": '.quality-gate-status',
                    "issues_tab": 'a[href*="issues"]',
                    "security_tab": 'a[href*="security_hotspots"]'
                }
            },
            "code_quality": {
                "flake8_config": ".flake8",
                "pylint_config": ".pylintrc",
                "bandit_config": ".bandit",
                "sonarqube_url": os.getenv('SONARQUBE_URL', 'https://sonarcloud.io')
            }
        }

    def _setup_logging(self) -> logging.Logger:
        """Setup logging"""
        logger = logging.getLogger("EnhancedPuppeteerService")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger

    async def navigate_to_platform(self, platform: str, url: str) -> str:
        """Navigate to AI platform and return session ID"""
        session_id = f"{platform}_{int(time.time())}"

        try:
            self.logger.info(f"Navigating to {platform} at {url}")

            # Use MCP Puppeteer to navigate
            from integrations.mcp_client import MCPClient
            mcp = MCPClient()

            # Navigate to the platform with full launch options
            nav_result = await mcp.call_tool(
                "puppeteer_navigate",
                {
                    "url": url,
                    "launchOptions": {
                        "headless": self.config["browser"]["headless"],
                        "args": self.config["browser"]["args"],
                        "ignoreDefaultArgs": self.config["browser"]["ignoreDefaultArgs"],
                        "slowMo": self.config["browser"]["slowMo"],
                        "timeout": self.config["browser"]["timeout"]
                    },
                    "allowDangerous": True
                }
            )

            if nav_result.get("success"):
                # Store session info
                self.sessions[session_id] = BrowserSession(
                    session_id=session_id,
                    platform=platform,
                    url=url,
                    created_at=datetime.now(),
                    last_used=datetime.now()
                )

                self.logger.info(f"Successfully navigated to {platform}")
                return session_id
            else:
                raise Exception(f"Navigation failed: {nav_result.get('error')}")

        except Exception as e:
            self.logger.error(f"Navigation to {platform} failed: {e}")
            raise

    async def run_code_quality_analysis(self, project_path: str, tools: Optional[List[str]] = None) -> Dict[str, CodeQualityResult]:
        """Run comprehensive code quality analysis using multiple tools"""
        if tools is None:
            tools = ['flake8', 'pylint', 'bandit']
        
        results = {}
        
        for tool in tools:
            if tool in self.code_quality_tools:
                self.logger.info(f"Running {tool} analysis...")
                try:
                    result = await self.code_quality_tools[tool](project_path)
                    results[tool] = result
                except Exception as e:
                    self.logger.error(f"Error running {tool}: {e}")
                    results[tool] = CodeQualityResult(
                        tool=tool,
                        status="error",
                        issues=[{"error": str(e)}]
                    )
        
        return results

    async def _run_flake8(self, project_path: str) -> CodeQualityResult:
        """Run Flake8 static analysis"""
        try:
            cmd = ['flake8', project_path, '--format=json']
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_path)
            
            issues = []
            if result.stdout:
                try:
                    issues = json.loads(result.stdout)
                except json.JSONDecodeError:
                    # Fallback to parsing text output
                    issues = self._parse_flake8_output(result.stdout)
            
            return CodeQualityResult(
                tool="flake8",
                status="completed" if result.returncode == 0 else "issues_found",
                issues=issues
            )
        except Exception as e:
            raise Exception(f"Flake8 analysis failed: {e}")

    async def _run_pylint(self, project_path: str) -> CodeQualityResult:
        """Run Pylint static analysis"""
        try:
            cmd = ['pylint', project_path, '--output-format=json']
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_path)
            
            issues = []
            if result.stdout:
                try:
                    issues = json.loads(result.stdout)
                except json.JSONDecodeError:
                    issues = []
            
            return CodeQualityResult(
                tool="pylint",
                status="completed" if result.returncode == 0 else "issues_found",
                issues=issues
            )
        except Exception as e:
            raise Exception(f"Pylint analysis failed: {e}")

    async def _run_bandit(self, project_path: str) -> CodeQualityResult:
        """Run Bandit security analysis"""
        try:
            cmd = ['bandit', '-r', project_path, '-f', 'json']
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_path)
            
            issues = []
            if result.stdout:
                try:
                    data = json.loads(result.stdout)
                    issues = data.get('results', [])
                except json.JSONDecodeError:
                    issues = []
            
            return CodeQualityResult(
                tool="bandit",
                status="completed" if result.returncode == 0 else "issues_found",
                issues=issues
            )
        except Exception as e:
            raise Exception(f"Bandit analysis failed: {e}")

    async def _automate_sonarqube(self, project_path: str) -> CodeQualityResult:
        """Automate SonarQube web interface interaction"""
        try:
            from integrations.mcp_client import MCPClient
            mcp = MCPClient()
            
            sonarqube_url = self.config["code_quality"]["sonarqube_url"]
            
            # Navigate to SonarQube
            await mcp.call_tool("puppeteer_navigate", {"url": sonarqube_url})
            
            # Wait for page to load
            await asyncio.sleep(3)
            
            # Search for project
            project_name = Path(project_path).name
            selectors = self.config["selectors"]["sonarqube"]
            
            await mcp.call_tool(
                "puppeteer_fill",
                {
                    "selector": selectors["project_search"],
                    "value": project_name
                }
            )
            
            # Wait for search results
            await asyncio.sleep(2)
            
            # Get quality gate status
            quality_gate_result = await mcp.call_tool(
                "puppeteer_evaluate",
                {
                    "script": f'''
                    const qualityGate = document.querySelector("{selectors['quality_gate']}");
                    qualityGate ? qualityGate.textContent : "Not found";
                    '''
                }
            )
            
            # Get issues count
            issues_result = await mcp.call_tool(
                "puppeteer_evaluate",
                {
                    "script": '''
                    const issuesElements = document.querySelectorAll(".issue-item");
                    Array.from(issuesElements).map(el => ({
                        type: el.querySelector(".issue-type")?.textContent || "unknown",
                        severity: el.querySelector(".issue-severity")?.textContent || "unknown",
                        message: el.querySelector(".issue-message")?.textContent || "unknown"
                    }));
                    '''
                }
            )
            
            return CodeQualityResult(
                tool="sonarqube",
                status="completed",
                issues=issues_result if isinstance(issues_result, list) else [],
                report_url=f"{sonarqube_url}/dashboard?id={project_name}"
            )
            
        except Exception as e:
            raise Exception(f"SonarQube automation failed: {e}")

    async def test_netlify_deployment(self, preview_url: str) -> Dict[str, Any]:
        """Test Netlify deployment preview using browser automation"""
        try:
            from integrations.mcp_client import MCPClient
            mcp = MCPClient()
            
            self.logger.info(f"Testing Netlify deployment at {preview_url}")
            
            # Navigate to preview URL
            await mcp.call_tool("puppeteer_navigate", {"url": preview_url})
            
            # Wait for page to load
            await asyncio.sleep(5)
            
            # Take screenshot
            screenshot_result = await mcp.call_tool(
                "puppeteer_screenshot",
                {
                    "name": f"netlify_preview_{int(time.time())}",
                    "width": 1280,
                    "height": 720
                }
            )
            
            # Check for common issues
            page_check_result = await mcp.call_tool(
                "puppeteer_evaluate",
                {
                    "script": '''
                    (function() {
                        const checks = {
                            hasTitle: !!document.title,
                            hasContent: document.body.children.length > 0,
                            hasErrors: !!document.querySelector(".error, .exception, [class*='error']"),
                            loadTime: performance.timing.loadEventEnd - performance.timing.navigationStart,
                            consoleErrors: window.console._errors || []
                        };
                        return checks;
                    })();
                    '''
                }
            )
            
            return {
                "status": "success",
                "url": preview_url,
                "screenshot": screenshot_result,
                "checks": page_check_result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Netlify deployment test failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "url": preview_url,
                "timestamp": datetime.now().isoformat()
            }

    def _parse_flake8_output(self, output: str) -> List[Dict[str, Any]]:
        """Parse Flake8 text output into structured format"""
        issues = []
        for line in output.strip().split('\n'):
            if ':' in line:
                parts = line.split(':')
                if len(parts) >= 4:
                    issues.append({
                        "filename": parts[0],
                        "line": int(parts[1]) if parts[1].isdigit() else 0,
                        "column": int(parts[2]) if parts[2].isdigit() else 0,
                        "code": parts[3].strip().split()[0] if parts[3].strip() else "",
                        "message": ' '.join(parts[3].strip().split()[1:]) if parts[3].strip() else ""
                    })
        return issues

    async def generate_quality_report(self, results: Dict[str, CodeQualityResult]) -> str:
        """Generate a comprehensive quality report"""
        report = ["# Code Quality Analysis Report\n"]
        report.append(f"Generated at: {datetime.now().isoformat()}\n\n")
        
        for tool, result in results.items():
            report.append(f"## {tool.upper()} Analysis\n")
            report.append(f"Status: {result.status}\n")
            report.append(f"Issues found: {len(result.issues)}\n")
            
            if result.score:
                report.append(f"Score: {result.score}\n")
            
            if result.report_url:
                report.append(f"Report URL: {result.report_url}\n")
            
            if result.issues:
                report.append("\n### Issues:\n")
                for i, issue in enumerate(result.issues[:10]):  # Limit to first 10 issues
                    report.append(f"{i+1}. {issue}\n")
                
                if len(result.issues) > 10:
                    report.append(f"... and {len(result.issues) - 10} more issues\n")
            
            report.append("\n")
        
        return ''.join(report)

# Backward compatibility
PuppeteerService = EnhancedPuppeteerService