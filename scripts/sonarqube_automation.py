#!/usr/bin/env python3
"""
SonarQube Web Interface Automation

This script automates SonarQube web interface interactions for quality gate validation,
project analysis, and report generation using Puppeteer integration.

Features:
- Automated login and authentication
- Project analysis triggering
- Quality gate status monitoring
- Metrics extraction and reporting
- Screenshot capture for documentation
- Integration with CI/CD pipelines
"""

import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urljoin, urlparse

import requests
from integrations.puppeteer_service import PuppeteerService
from integrations.mcp_client import MCPClient


@dataclass
class SonarQubeMetrics:
    """SonarQube project metrics."""
    project_key: str
    quality_gate_status: str
    coverage: Optional[float] = None
    duplicated_lines_density: Optional[float] = None
    maintainability_rating: Optional[str] = None
    reliability_rating: Optional[str] = None
    security_rating: Optional[str] = None
    technical_debt: Optional[str] = None
    bugs: int = 0
    vulnerabilities: int = 0
    code_smells: int = 0
    lines_of_code: int = 0
    complexity: Optional[int] = None
    last_analysis_date: Optional[str] = None
    report_url: Optional[str] = None
    execution_time: float = 0.0
    raw_data: Optional[Dict[str, Any]] = None


@dataclass
class SonarQubeConfig:
    """Configuration for SonarQube automation."""
    # SonarQube server configuration
    server_url: str = "http://localhost:9000"
    username: Optional[str] = None
    password: Optional[str] = None
    token: Optional[str] = None
    
    # Project configuration
    project_key: Optional[str] = None
    organization: Optional[str] = None
    
    # Automation settings
    timeout: int = 300
    screenshot_dir: str = "sonarqube_screenshots"
    report_dir: str = "sonarqube_reports"
    headless: bool = True
    
    def __post_init__(self):
        """Validate configuration."""
        if not self.token and not (self.username and self.password):
            raise ValueError("Either token or username/password must be provided")


class SonarQubeAutomation:
    """Automates SonarQube web interface interactions."""
    
    def __init__(self, config: SonarQubeConfig, puppeteer_service: Optional[PuppeteerService] = None):
        self.config = config
        self.logger = self._setup_logging()
        self.puppeteer_service = puppeteer_service or PuppeteerService()
        self.mcp_client = MCPClient() if hasattr(MCPClient, '__init__') else None
        
        # Ensure directories exist
        Path(self.config.screenshot_dir).mkdir(parents=True, exist_ok=True)
        Path(self.config.report_dir).mkdir(parents=True, exist_ok=True)
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    async def authenticate(self) -> bool:
        """Authenticate with SonarQube."""
        try:
            login_url = urljoin(self.config.server_url, "/sessions/new")
            
            if hasattr(self.puppeteer_service, 'navigate_to_url'):
                await getattr(self.puppeteer_service, 'navigate_to_url')(login_url)
            elif self.mcp_client and hasattr(self.mcp_client, 'call_tool'):
                await getattr(self.mcp_client, 'call_tool')(
                    "mcp.config.usrlocalmcp.Puppeteer",
                    "puppeteer_navigate",
                    {"url": login_url}
                )
            
            # Wait for page to load
            await asyncio.sleep(2)
            
            if self.config.token:
                # Use token-based authentication via API
                return await self._authenticate_with_token()
            else:
                # Use form-based authentication
                return await self._authenticate_with_form()
                
        except Exception as e:
            self.logger.error(f"Authentication failed: {e}")
            return False
    
    async def _authenticate_with_token(self) -> bool:
        """Authenticate using API token."""
        try:
            # Test token validity
            headers = {'Authorization': f'Bearer {self.config.token}'}
            response = requests.get(
                urljoin(self.config.server_url, "/api/authentication/validate"),
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                self.logger.info("Token authentication successful")
                return True
            else:
                self.logger.error(f"Token authentication failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Token authentication error: {e}")
            return False
    
    async def _authenticate_with_form(self) -> bool:
        """Authenticate using login form."""
        try:
            # Fill login form
            if hasattr(self.puppeteer_service, 'fill_form_field'):
                fill_method = getattr(self.puppeteer_service, 'fill_form_field')
                click_method = getattr(self.puppeteer_service, 'click_element')
                await fill_method('#login', self.config.username or "")
                await fill_method('#password', self.config.password or "")
                await click_method('input[type="submit"]')
            elif self.mcp_client and hasattr(self.mcp_client, 'call_tool'):
                call_tool = getattr(self.mcp_client, 'call_tool')
                await call_tool(
                    "mcp.config.usrlocalmcp.Puppeteer",
                    "puppeteer_fill",
                    {"selector": "#login", "value": self.config.username or ""}
                )
                await call_tool(
                    "mcp.config.usrlocalmcp.Puppeteer",
                    "puppeteer_fill",
                    {"selector": "#password", "value": self.config.password or ""}
                )
                await call_tool(
                    "mcp.config.usrlocalmcp.Puppeteer",
                    "puppeteer_click",
                    {"selector": 'input[type="submit"]'}
                )
            
            # Wait for redirect
            await asyncio.sleep(3)
            
            # Check if login was successful
            current_url = await self._get_current_url()
            if "/sessions/new" not in current_url:
                self.logger.info("Form authentication successful")
                return True
            else:
                self.logger.error("Form authentication failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Form authentication error: {e}")
            return False
    
    async def _get_current_url(self) -> str:
        """Get current page URL."""
        try:
            if hasattr(self.puppeteer_service, 'get_current_url'):
                return await getattr(self.puppeteer_service, 'get_current_url')()
            elif self.mcp_client and hasattr(self.mcp_client, 'call_tool'):
                result = await getattr(self.mcp_client, 'call_tool')(
                    "mcp.config.usrlocalmcp.Puppeteer",
                    "puppeteer_evaluate",
                    {"script": "window.location.href"}
                )
                return result.get('result', '') if isinstance(result, dict) else ''
            return ""
        except Exception:
            return ""
    
    async def analyze_project(self, project_key: Optional[str] = None) -> SonarQubeMetrics:
        """Analyze a project and extract metrics."""
        start_time = time.time()
        project_key = project_key or self.config.project_key or "unknown"
        
        try:
            # Navigate to project dashboard
            project_url = urljoin(
                self.config.server_url,
                f"/dashboard?id={project_key}"
            )
            
            if hasattr(self.puppeteer_service, 'navigate_to_url'):
                await getattr(self.puppeteer_service, 'navigate_to_url')(project_url)
            elif self.mcp_client and hasattr(self.mcp_client, 'call_tool'):
                await getattr(self.mcp_client, 'call_tool')(
                    "mcp.config.usrlocalmcp.Puppeteer",
                    "puppeteer_navigate",
                    {"url": project_url}
                )
            
            # Wait for page to load
            await asyncio.sleep(3)
            
            # Take screenshot
            screenshot_path = os.path.join(
                self.config.screenshot_dir,
                f"sonarqube_project_{project_key}_{int(time.time())}.png"
            )
            await self._take_screenshot(screenshot_path)
            
            # Extract metrics from the page
            metrics = await self._extract_project_metrics(project_key)
            metrics.execution_time = time.time() - start_time
            metrics.report_url = project_url
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Project analysis failed: {e}")
            return SonarQubeMetrics(
                project_key=project_key,
                quality_gate_status="ERROR",
                execution_time=time.time() - start_time,
                raw_data={"error": str(e)}
            )
    
    async def _extract_project_metrics(self, project_key: str) -> SonarQubeMetrics:
        """Extract metrics from SonarQube project page."""
        try:
            # Use API if token is available
            if self.config.token:
                return await self._extract_metrics_via_api(project_key)
            else:
                return await self._extract_metrics_via_web(project_key)
                
        except Exception as e:
            self.logger.error(f"Metrics extraction failed: {e}")
            return SonarQubeMetrics(
                project_key=project_key,
                quality_gate_status="UNKNOWN",
                raw_data={"error": str(e)}
            )
    
    async def _extract_metrics_via_api(self, project_key: str) -> SonarQubeMetrics:
        """Extract metrics using SonarQube API."""
        headers = {'Authorization': f'Bearer {self.config.token}'}
        base_url = urljoin(self.config.server_url, "/api")
        
        # Get quality gate status
        qg_response = requests.get(
            f"{base_url}/qualitygates/project_status",
            params={'projectKey': project_key},
            headers=headers,
            timeout=30
        )
        
        quality_gate_status = "UNKNOWN"
        qg_data = {}
        if qg_response.status_code == 200:
            qg_data = qg_response.json()
            quality_gate_status = qg_data.get('projectStatus', {}).get('status', 'UNKNOWN')
        
        # Get project measures
        measures_response = requests.get(
            f"{base_url}/measures/component",
            params={
                'component': project_key,
                'metricKeys': 'coverage,duplicated_lines_density,maintainability_rating,reliability_rating,security_rating,sqale_index,bugs,vulnerabilities,code_smells,ncloc,complexity'
            },
            headers=headers,
            timeout=30
        )
        
        metrics_data = {}
        if measures_response.status_code == 200:
            measures_data = measures_response.json()
            measures = {m['metric']: m.get('value') for m in measures_data.get('component', {}).get('measures', [])}
            
            return SonarQubeMetrics(
                project_key=project_key,
                quality_gate_status=quality_gate_status,
                coverage=float(measures.get('coverage', 0)) if measures.get('coverage') else None,
                duplicated_lines_density=float(measures.get('duplicated_lines_density', 0)) if measures.get('duplicated_lines_density') else None,
                maintainability_rating=measures.get('maintainability_rating'),
                reliability_rating=measures.get('reliability_rating'),
                security_rating=measures.get('security_rating'),
                technical_debt=measures.get('sqale_index'),
                bugs=int(measures.get('bugs', 0)),
                vulnerabilities=int(measures.get('vulnerabilities', 0)),
                code_smells=int(measures.get('code_smells', 0)),
                lines_of_code=int(measures.get('ncloc', 0)),
                complexity=int(measures.get('complexity', 0)) if measures.get('complexity') else None,
                raw_data={'quality_gate': qg_data, 'measures': measures_data}
            )
        
        return SonarQubeMetrics(
            project_key=project_key,
            quality_gate_status=quality_gate_status
        )
    
    async def _extract_metrics_via_web(self, project_key: str) -> SonarQubeMetrics:
        """Extract metrics by scraping the web interface."""
        try:
            # Extract quality gate status
            quality_gate_status = await self._extract_text_content('.overview-quality-gate-status')
            
            # Extract coverage
            coverage_text = await self._extract_text_content('[data-test="overview__coverage"]')
            coverage = None
            if coverage_text and '%' in coverage_text:
                try:
                    coverage = float(coverage_text.replace('%', '').strip())
                except ValueError:
                    pass
            
            # Extract other metrics
            bugs = await self._extract_numeric_content('[data-test="overview__bugs"]')
            vulnerabilities = await self._extract_numeric_content('[data-test="overview__vulnerabilities"]')
            code_smells = await self._extract_numeric_content('[data-test="overview__code_smells"]')
            
            return SonarQubeMetrics(
                project_key=project_key,
                quality_gate_status=quality_gate_status or "UNKNOWN",
                coverage=coverage,
                bugs=bugs,
                vulnerabilities=vulnerabilities,
                code_smells=code_smells
            )
            
        except Exception as e:
            self.logger.error(f"Web scraping failed: {e}")
            return SonarQubeMetrics(
                project_key=project_key,
                quality_gate_status="UNKNOWN"
            )
    
    async def _extract_text_content(self, selector: str) -> Optional[str]:
        """Extract text content from a CSS selector."""
        try:
            if hasattr(self.puppeteer_service, 'get_element_text'):
                return await getattr(self.puppeteer_service, 'get_element_text')(selector)
            elif self.mcp_client and hasattr(self.mcp_client, 'call_tool'):
                result = await getattr(self.mcp_client, 'call_tool')(
                    "mcp.config.usrlocalmcp.Puppeteer",
                    "puppeteer_evaluate",
                    {"script": f"document.querySelector('{selector}')?.textContent?.trim()"}
                )
                return result.get('result') if isinstance(result, dict) else None
            return None
        except Exception:
            return None
    
    async def _extract_numeric_content(self, selector: str) -> int:
        """Extract numeric content from a CSS selector."""
        try:
            text = await self._extract_text_content(selector)
            if text:
                # Extract numbers from text
                import re
                numbers = re.findall(r'\d+', text.replace(',', ''))
                if numbers:
                    return int(numbers[0])
            return 0
        except Exception:
            return 0
    
    async def _take_screenshot(self, filename: str) -> bool:
        """Take a screenshot of the current page."""
        try:
            if hasattr(self.puppeteer_service, 'take_screenshot'):
                await getattr(self.puppeteer_service, 'take_screenshot')(filename)
            elif self.mcp_client and hasattr(self.mcp_client, 'call_tool'):
                await getattr(self.mcp_client, 'call_tool')(
                    "mcp.config.usrlocalmcp.Puppeteer",
                    "puppeteer_screenshot",
                    {"name": filename}
                )
            return True
        except Exception as e:
            self.logger.error(f"Screenshot failed: {e}")
            return False
    
    async def wait_for_analysis_completion(self, project_key: Optional[str] = None, max_wait: int = 600) -> bool:
        """Wait for project analysis to complete."""
        project_key = project_key or self.config.project_key or "unknown"
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                if self.config.token:
                    # Check via API
                    headers = {'Authorization': f'Bearer {self.config.token}'}
                    response = requests.get(
                        urljoin(self.config.server_url, f"/api/ce/activity?component={project_key}"),
                        headers=headers,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        tasks = data.get('tasks', [])
                        if tasks:
                            latest_task = tasks[0]
                            status = latest_task.get('status')
                            if status in ['SUCCESS', 'FAILED', 'CANCELED']:
                                self.logger.info(f"Analysis completed with status: {status}")
                                return status == 'SUCCESS'
                
                self.logger.info(f"Waiting for analysis completion... ({int(time.time() - start_time)}s)")
                await asyncio.sleep(10)
                
            except Exception as e:
                self.logger.error(f"Error checking analysis status: {e}")
                await asyncio.sleep(10)
        
        self.logger.warning(f"Analysis wait timeout after {max_wait}s")
        return False
    
    def generate_report(self, metrics: SonarQubeMetrics, output_path: Optional[str] = None) -> str:
        """Generate a detailed metrics report."""
        if output_path is None:
            output_path = os.path.join(
                self.config.report_dir,
                f"sonarqube_report_{metrics.project_key}_{int(time.time())}.json"
            )
        
        try:
            report_data = asdict(metrics)
            with open(output_path, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            
            self.logger.info(f"SonarQube report generated: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error generating report: {e}")
            return ""
    
    async def run_full_analysis(self, project_key: Optional[str] = None) -> Dict[str, Any]:
        """Run complete SonarQube analysis workflow."""
        project_key = project_key or self.config.project_key or "unknown"
        
        workflow_results = {
            'project_key': project_key,
            'timestamp': time.time(),
            'authentication': False,
            'analysis_completion': False,
            'metrics': None,
            'report_path': None,
            'errors': []
        }
        
        try:
            # Step 1: Authenticate
            self.logger.info("Starting SonarQube authentication...")
            auth_success = await self.authenticate()
            workflow_results['authentication'] = auth_success
            
            if not auth_success:
                errors = workflow_results.get('errors', [])
                if not isinstance(errors, list):
                    errors = []
                errors.append("Authentication failed")
                workflow_results['errors'] = errors
                return workflow_results
            
            # Step 2: Wait for analysis completion (if needed)
            self.logger.info("Checking analysis completion...")
            analysis_complete = await self.wait_for_analysis_completion(project_key, max_wait=300)
            workflow_results['analysis_completion'] = analysis_complete
            
            # Step 3: Extract metrics
            self.logger.info("Extracting project metrics...")
            metrics = await self.analyze_project(project_key)
            workflow_results['metrics'] = asdict(metrics) if metrics else {}
            
            # Step 4: Generate report
            self.logger.info("Generating analysis report...")
            report_path = self.generate_report(metrics)
            workflow_results['report_path'] = report_path
            
            self.logger.info(f"SonarQube analysis completed for project: {project_key}")
            
        except Exception as e:
            error_msg = f"SonarQube analysis workflow failed: {e}"
            self.logger.error(error_msg)
            errors = workflow_results.get('errors', [])
            if not isinstance(errors, list):
                errors = []
            errors.append(error_msg)
            workflow_results['errors'] = errors
        
        return workflow_results


async def main():
    """Main function for testing SonarQube automation."""
    # Example configuration
    config = SonarQubeConfig(
        server_url=os.getenv('SONARQUBE_URL', 'http://localhost:9000'),
        token=os.getenv('SONARQUBE_TOKEN'),
        username=os.getenv('SONARQUBE_USERNAME'),
        password=os.getenv('SONARQUBE_PASSWORD'),
        project_key=os.getenv('SONARQUBE_PROJECT_KEY', 'my-project'),
        timeout=300
    )
    
    # Initialize automation
    automation = SonarQubeAutomation(config)
    
    # Run full analysis
    results = await automation.run_full_analysis()
    
    # Print results
    print("\n=== SonarQube Analysis Results ===")
    print(json.dumps(results, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())