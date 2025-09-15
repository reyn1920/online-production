#!/usr/bin/env python3
"""
Web-Based Code Analysis Automation

This script automates code analysis using web-based platforms and tools,
integrating with services like SonarCloud, CodeClimate, and other online analyzers.
"""

import asyncio
import json
import logging
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from urllib.parse import urljoin, urlparse

import requests
from integrations.puppeteer_service import PuppeteerService
from integrations.mcp_client import MCPClient


@dataclass
class AnalysisResult:
    """Represents the result of a code analysis."""
    platform: str
    project_key: str
    status: str  # 'passed', 'failed', 'error'
    quality_gate: Optional[str] = None
    issues_count: int = 0
    coverage: Optional[float] = None
    duplications: Optional[float] = None
    maintainability_rating: Optional[str] = None
    reliability_rating: Optional[str] = None
    security_rating: Optional[str] = None
    technical_debt: Optional[str] = None
    report_url: Optional[str] = None
    execution_time: float = 0.0
    error_message: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None


@dataclass
class WebAnalyzerConfig:
    """Configuration for web-based code analysis."""
    # SonarCloud configuration
    sonar_token: Optional[str] = None
    sonar_organization: Optional[str] = None
    sonar_project_key: Optional[str] = None
    
    # CodeClimate configuration
    codeclimate_token: Optional[str] = None
    codeclimate_repo_id: Optional[str] = None
    
    # GitHub configuration
    github_token: Optional[str] = None
    github_repository: Optional[str] = None
    
    # General settings
    timeout: int = 300
    screenshot_dir: str = "analysis_screenshots"
    report_dir: str = "analysis_reports"
    
    def __post_init__(self):
        # Create directories
        Path(self.screenshot_dir).mkdir(parents=True, exist_ok=True)
        Path(self.report_dir).mkdir(parents=True, exist_ok=True)


class WebCodeAnalyzer:
    """Automated web-based code analysis orchestrator."""

    def __init__(self, config: WebAnalyzerConfig, puppeteer_service: Optional[PuppeteerService] = None):
        self.config = config
        self.puppeteer_service = puppeteer_service or PuppeteerService()
        self.logger = self._setup_logging()
        self.analysis_results: List[AnalysisResult] = []

    def _setup_logging(self) -> logging.Logger:
        """Set up logging configuration."""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger

    async def analyze_with_sonarcloud(self) -> AnalysisResult:
        """Analyze code using SonarCloud web interface."""
        start_time = time.time()
        
        try:
            if not self.config.sonar_token or not self.config.sonar_project_key:
                return AnalysisResult(
                platform="SonarCloud",
                project_key=self.config.sonar_project_key or "unknown",
                status="error",
                execution_time=time.time() - start_time,
                error_message="SonarCloud token or project key not configured"
            )
            
            # First, try API approach
            api_result = await self._sonarcloud_api_analysis()
            if api_result.status != "error":
                return api_result
            
            # Fallback to web scraping if API fails
            return await self._sonarcloud_web_analysis()
            
        except Exception as e:
            self.logger.error(f"SonarCloud analysis error: {e}")
            project_key = self.config.sonar_project_key or "unknown"
            return AnalysisResult(
                platform="SonarCloud",
                project_key=project_key,
                status="error",
                execution_time=time.time() - start_time,
                error_message=str(e)
            )

    async def _sonarcloud_api_analysis(self) -> AnalysisResult:
        """Analyze using SonarCloud API."""
        start_time = time.time()
        
        try:
            headers = {
                'Authorization': f'Bearer {self.config.sonar_token}',
                'Content-Type': 'application/json'
            }
            
            base_url = "https://sonarcloud.io/api"
            project_key = self.config.sonar_project_key or "unknown"
            
            # Get project status
            status_url = f"{base_url}/qualitygates/project_status"
            status_params = {'projectKey': project_key}
            
            status_response = requests.get(status_url, headers=headers, params=status_params)
            status_response.raise_for_status()
            status_data = status_response.json()
            
            # Get project measures
            measures_url = f"{base_url}/measures/component"
            measures_params = {
                'component': project_key,
                'metricKeys': 'bugs,vulnerabilities,code_smells,coverage,duplicated_lines_density,sqale_rating,reliability_rating,security_rating,sqale_index'
            }
            
            measures_response = requests.get(measures_url, headers=headers, params=measures_params)
            measures_response.raise_for_status()
            measures_data = measures_response.json()
            
            # Parse results
            quality_gate = status_data.get('projectStatus', {}).get('status', 'UNKNOWN')
            measures = {m['metric']: m.get('value') for m in measures_data.get('component', {}).get('measures', [])}
            
            # Count total issues
            issues_count = (
                int(measures.get('bugs', 0)) +
                int(measures.get('vulnerabilities', 0)) +
                int(measures.get('code_smells', 0))
            )
            
            return AnalysisResult(
                platform="SonarCloud",
                project_key=project_key,
                status="passed" if quality_gate == "OK" else "failed",
                quality_gate=quality_gate,
                issues_count=issues_count,
                coverage=float(measures.get('coverage', 0)) if measures.get('coverage') else None,
                duplications=float(measures.get('duplicated_lines_density', 0)) if measures.get('duplicated_lines_density') else None,
                maintainability_rating=measures.get('sqale_rating'),
                reliability_rating=measures.get('reliability_rating'),
                security_rating=measures.get('security_rating'),
                technical_debt=measures.get('sqale_index'),
                report_url=f"https://sonarcloud.io/dashboard?id={project_key}",
                execution_time=time.time() - start_time,
                raw_data={'status': status_data, 'measures': measures_data}
            )
            
        except Exception as e:
            self.logger.warning(f"SonarCloud API analysis failed: {e}")
            project_key = self.config.sonar_project_key or "unknown"
            return AnalysisResult(
                platform="SonarCloud",
                project_key=project_key,
                status="error",
                execution_time=time.time() - start_time,
                error_message=f"API analysis failed: {str(e)}"
            )

    async def _sonarcloud_web_analysis(self) -> AnalysisResult:
        """Analyze using SonarCloud web interface via Puppeteer."""
        start_time = time.time()
        
        try:
            if not hasattr(self.puppeteer_service, 'mcp_client') or not getattr(self.puppeteer_service, 'mcp_client', None):
                return AnalysisResult(
                    platform="SonarCloud",
                    project_key=self.config.sonar_project_key or "unknown",
                    status="error",
                    execution_time=time.time() - start_time,
                    error_message="Puppeteer service not available"
                )
            
            project_url = f"https://sonarcloud.io/dashboard?id={self.config.sonar_project_key}"
            
            # Navigate to SonarCloud project
            if hasattr(self.puppeteer_service, 'navigate_to_url'):
                navigate_method = getattr(self.puppeteer_service, 'navigate_to_url', None)
                if navigate_method:
                    await navigate_method(project_url)
            
            # Wait for page to load
            await asyncio.sleep(5)
            
            # Take screenshot
            screenshot_name = f"sonarcloud_{self.config.sonar_project_key}.png"
            if hasattr(self.puppeteer_service, 'take_screenshot'):
                screenshot_method = getattr(self.puppeteer_service, 'take_screenshot', None)
                if screenshot_method:
                    await screenshot_method(screenshot_name)
            
            # Extract quality gate status
            quality_gate_script = """
            const qualityGateElement = document.querySelector('[data-test="overview__quality-gate-status"]') ||
                                    document.querySelector('.quality-gate-status') ||
                                    document.querySelector('[class*="quality-gate"]');
            
            if (qualityGateElement) {
                return qualityGateElement.textContent.trim();
            }
            
            // Fallback: look for passed/failed indicators
            const passedElement = document.querySelector('[class*="passed"], [class*="success"]');
            const failedElement = document.querySelector('[class*="failed"], [class*="error"]');
            
            if (passedElement) return 'PASSED';
            if (failedElement) return 'FAILED';
            
            return 'UNKNOWN';
            """
            
            quality_gate = None
            if hasattr(self.puppeteer_service, 'evaluate_javascript'):
                evaluate_method = getattr(self.puppeteer_service, 'evaluate_javascript', None)
                if evaluate_method:
                    quality_gate = await evaluate_method(quality_gate_script)
            
            # Extract metrics
            metrics_script = """
            const metrics = {};
            
            // Look for coverage
            const coverageElement = document.querySelector('[data-test="measures-coverage"]') ||
                                  document.querySelector('[class*="coverage"]');
            if (coverageElement) {
                const coverageText = coverageElement.textContent.match(/([0-9.]+)%/);
                if (coverageText) metrics.coverage = parseFloat(coverageText[1]);
            }
            
            // Look for issues count
            const issuesElements = document.querySelectorAll('[data-test*="issues"], [class*="issues"]');
            let totalIssues = 0;
            issuesElements.forEach(el => {
                const issueText = el.textContent.match(/([0-9]+)/);
                if (issueText) totalIssues += parseInt(issueText[1]);
            });
            metrics.issues = totalIssues;
            
            // Look for duplications
            const duplicationsElement = document.querySelector('[data-test="measures-duplications"]') ||
                                      document.querySelector('[class*="duplication"]');
            if (duplicationsElement) {
                const dupText = duplicationsElement.textContent.match(/([0-9.]+)%/);
                if (dupText) metrics.duplications = parseFloat(dupText[1]);
            }
            
            return metrics;
            """
            
            metrics = None
            if hasattr(self.puppeteer_service, 'evaluate_javascript'):
                evaluate_method = getattr(self.puppeteer_service, 'evaluate_javascript', None)
                if evaluate_method:
                    metrics = await evaluate_method(metrics_script)
            
            # Determine status
            status = "passed" if quality_gate and "PASS" in quality_gate.upper() else "failed"
            
            return AnalysisResult(
                platform="SonarCloud",
                project_key=self.config.sonar_project_key or "unknown",
                status=status,
                quality_gate=quality_gate,
                issues_count=metrics.get('issues', 0) if metrics else 0,
                coverage=metrics.get('coverage') if metrics else None,
                duplications=metrics.get('duplications') if metrics else None,
                report_url=project_url,
                execution_time=time.time() - start_time,
                raw_data={'quality_gate': quality_gate, 'metrics': metrics}
            )
            
        except Exception as e:
            self.logger.error(f"SonarCloud web analysis error: {e}")
            return AnalysisResult(
                platform="SonarCloud",
                project_key=self.config.sonar_project_key or "unknown",
                status="error",
                execution_time=time.time() - start_time,
                error_message=str(e)
            )

    async def analyze_with_codeclimate(self) -> AnalysisResult:
        """Analyze code using CodeClimate."""
        start_time = time.time()
        
        try:
            if not self.config.codeclimate_token or not self.config.codeclimate_repo_id:
                return AnalysisResult(
                platform="CodeClimate",
                project_key=self.config.codeclimate_repo_id or "unknown",
                status="error",
                execution_time=time.time() - start_time,
                error_message="CodeClimate token or repo ID not configured"
            )
            
            # Try API first
            api_result = await self._codeclimate_api_analysis()
            if api_result.status != "error":
                return api_result
            
            # Fallback to web scraping
            return await self._codeclimate_web_analysis()
            
        except Exception as e:
            self.logger.error(f"CodeClimate analysis error: {e}")
            project_key = self.config.codeclimate_repo_id or "unknown"
            return AnalysisResult(
                platform="CodeClimate",
                project_key=project_key,
                status="error",
                execution_time=time.time() - start_time,
                error_message=str(e)
            )

    async def _codeclimate_api_analysis(self) -> AnalysisResult:
        """Analyze using CodeClimate API."""
        start_time = time.time()
        
        try:
            headers = {
                'Authorization': f'Token token={self.config.codeclimate_token}',
                'Content-Type': 'application/vnd.api+json'
            }
            
            base_url = "https://codeclimate.com/api/v1"
            repo_id = self.config.codeclimate_repo_id or "unknown"
            
            # Get repository information
            repo_url = f"{base_url}/repos/{repo_id}"
            repo_response = requests.get(repo_url, headers=headers)
            repo_response.raise_for_status()
            repo_data = repo_response.json()
            
            # Get test coverage
            coverage_url = f"{base_url}/repos/{repo_id}/test_reports"
            coverage_response = requests.get(coverage_url, headers=headers)
            coverage_data = coverage_response.json() if coverage_response.status_code == 200 else {}
            
            # Get issues
            issues_url = f"{base_url}/repos/{repo_id}/issues"
            issues_response = requests.get(issues_url, headers=headers)
            issues_data = issues_response.json() if issues_response.status_code == 200 else {}
            
            # Parse results
            attributes = repo_data.get('data', {}).get('attributes', {})
            maintainability_rating = attributes.get('ratings', {}).get('maintainability', {}).get('letter')
            technical_debt = attributes.get('ratings', {}).get('maintainability', {}).get('measure', {}).get('value')
            
            # Count issues
            issues_count = len(issues_data.get('data', []))
            
            # Get coverage
            coverage = None
            if coverage_data.get('data'):
                latest_coverage = coverage_data['data'][0] if coverage_data['data'] else {}
                coverage_attrs = latest_coverage.get('attributes', {})
                coverage = coverage_attrs.get('covered_percent')
            
            # Determine status based on maintainability rating
            status = "passed" if maintainability_rating in ['A', 'B'] else "failed"
            
            return AnalysisResult(
                platform="CodeClimate",
                project_key=repo_id,
                status=status,
                issues_count=issues_count,
                coverage=coverage,
                maintainability_rating=maintainability_rating,
                technical_debt=str(technical_debt) if technical_debt else None,
                report_url=f"https://codeclimate.com/github/{repo_id}",
                execution_time=time.time() - start_time,
                raw_data={'repo': repo_data, 'coverage': coverage_data, 'issues': issues_data}
            )
            
        except Exception as e:
            self.logger.warning(f"CodeClimate API analysis failed: {e}")
            project_key = self.config.codeclimate_repo_id or "unknown"
            return AnalysisResult(
                platform="CodeClimate",
                project_key=project_key,
                status="error",
                execution_time=time.time() - start_time,
                error_message=f"API analysis failed: {str(e)}"
            )

    async def _codeclimate_web_analysis(self) -> AnalysisResult:
        """Analyze using CodeClimate web interface via Puppeteer."""
        start_time = time.time()
        
        try:
            if not hasattr(self.puppeteer_service, 'mcp_client') or not getattr(self.puppeteer_service, 'mcp_client', None):
                return AnalysisResult(
                    platform="CodeClimate",
                    project_key=self.config.codeclimate_repo_id or "unknown",
                    status="error",
                    execution_time=time.time() - start_time,
                    error_message="Puppeteer service not available"
                )
            
            project_url = f"https://codeclimate.com/github/{self.config.codeclimate_repo_id}"
            
            # Navigate to CodeClimate project
            if hasattr(self.puppeteer_service, 'navigate_to_url'):
                navigate_method = getattr(self.puppeteer_service, 'navigate_to_url', None)
                if navigate_method:
                    await navigate_method(project_url)
            
            # Wait for page to load
            await asyncio.sleep(5)
            
            # Take screenshot
            repo_id_safe = self.config.codeclimate_repo_id.replace('/', '_') if self.config.codeclimate_repo_id else 'unknown'
            screenshot_name = f"codeclimate_{repo_id_safe}.png"
            if hasattr(self.puppeteer_service, 'take_screenshot'):
                screenshot_method = getattr(self.puppeteer_service, 'take_screenshot', None)
                if screenshot_method:
                    await screenshot_method(screenshot_name)
            
            # Extract metrics
            metrics_script = """
            const metrics = {};
            
            // Look for maintainability rating
            const maintainabilityElement = document.querySelector('[data-test="maintainability-rating"]') ||
                                         document.querySelector('.maintainability-rating') ||
                                         document.querySelector('[class*="rating"]');
            if (maintainabilityElement) {
                metrics.maintainability = maintainabilityElement.textContent.trim();
            }
            
            // Look for coverage
            const coverageElement = document.querySelector('[data-test="test-coverage"]') ||
                                  document.querySelector('.test-coverage') ||
                                  document.querySelector('[class*="coverage"]');
            if (coverageElement) {
                const coverageText = coverageElement.textContent.match(/([0-9.]+)%/);
                if (coverageText) metrics.coverage = parseFloat(coverageText[1]);
            }
            
            // Look for issues count
            const issuesElement = document.querySelector('[data-test="issues-count"]') ||
                                document.querySelector('.issues-count') ||
                                document.querySelector('[class*="issues"]');
            if (issuesElement) {
                const issuesText = issuesElement.textContent.match(/([0-9]+)/);
                if (issuesText) metrics.issues = parseInt(issuesText[1]);
            }
            
            // Look for technical debt
            const debtElement = document.querySelector('[data-test="technical-debt"]') ||
                              document.querySelector('.technical-debt') ||
                              document.querySelector('[class*="debt"]');
            if (debtElement) {
                metrics.technicalDebt = debtElement.textContent.trim();
            }
            
            return metrics;
            """
            
            metrics = None
            if hasattr(self.puppeteer_service, 'evaluate_javascript'):
                evaluate_method = getattr(self.puppeteer_service, 'evaluate_javascript', None)
                if evaluate_method:
                    metrics = await evaluate_method(metrics_script)
            
            # Determine status based on maintainability rating
            maintainability = metrics.get('maintainability', '') if metrics else ''
            status = "passed" if any(grade in maintainability.upper() for grade in ['A', 'B']) else "failed"
            
            return AnalysisResult(
                platform="CodeClimate",
                project_key=self.config.codeclimate_repo_id or "unknown",
                status=status,
                issues_count=metrics.get('issues', 0) if metrics else 0,
                coverage=metrics.get('coverage') if metrics else None,
                maintainability_rating=maintainability,
                technical_debt=metrics.get('technicalDebt') if metrics else None,
                report_url=project_url,
                execution_time=time.time() - start_time,
                raw_data={'metrics': metrics}
            )
            
        except Exception as e:
            self.logger.error(f"CodeClimate web analysis error: {e}")
            return AnalysisResult(
                platform="CodeClimate",
                project_key=self.config.codeclimate_repo_id or "unknown",
                status="error",
                execution_time=time.time() - start_time,
                error_message=str(e)
            )

    async def analyze_github_security(self) -> AnalysisResult:
        """Analyze GitHub security alerts and code scanning results."""
        start_time = time.time()
        
        try:
            if not self.config.github_token or not self.config.github_repository:
                return AnalysisResult(
                platform="GitHub Security",
                project_key=self.config.github_repository or "unknown",
                status="error",
                execution_time=time.time() - start_time,
                error_message="GitHub token or repository not configured"
            )
            
            headers = {
                'Authorization': f'token {self.config.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            base_url = "https://api.github.com"
            repo = self.config.github_repository
            
            # Get security alerts
            alerts_url = f"{base_url}/repos/{repo}/security-advisories"
            alerts_response = requests.get(alerts_url, headers=headers)
            alerts_data = alerts_response.json() if alerts_response.status_code == 200 else []
            
            # Get code scanning alerts
            scanning_url = f"{base_url}/repos/{repo}/code-scanning/alerts"
            scanning_response = requests.get(scanning_url, headers=headers)
            scanning_data = scanning_response.json() if scanning_response.status_code == 200 else []
            
            # Get dependency alerts (Dependabot)
            dependabot_url = f"{base_url}/repos/{repo}/dependabot/alerts"
            dependabot_response = requests.get(dependabot_url, headers=headers)
            dependabot_data = dependabot_response.json() if dependabot_response.status_code == 200 else []
            
            # Count issues
            security_alerts = len(alerts_data) if isinstance(alerts_data, list) else 0
            code_scanning_alerts = len(scanning_data) if isinstance(scanning_data, list) else 0
            dependabot_alerts = len(dependabot_data) if isinstance(dependabot_data, list) else 0
            
            total_issues = security_alerts + code_scanning_alerts + dependabot_alerts
            
            # Determine status
            status = "passed" if total_issues == 0 else "failed"
            
            return AnalysisResult(
                platform="GitHub Security",
                project_key=repo,
                status=status,
                issues_count=total_issues,
                report_url=f"https://github.com/{repo}/security",
                execution_time=time.time() - start_time,
                raw_data={
                    'security_alerts': alerts_data,
                    'code_scanning': scanning_data,
                    'dependabot': dependabot_data
                }
            )
            
        except Exception as e:
            self.logger.error(f"GitHub security analysis error: {e}")
            return AnalysisResult(
                platform="GitHub Security",
                project_key=self.config.github_repository or "unknown",
                status="error",
                execution_time=time.time() - start_time,
                error_message=str(e)
            )

    async def run_all_analyses(self) -> Dict[str, Any]:
        """Run all configured analyses and return comprehensive results."""
        self.logger.info("Starting web-based code analysis...")
        
        # Run SonarCloud analysis if configured
        if self.config.sonar_token and self.config.sonar_project_key:
            self.logger.info("Running SonarCloud analysis...")
            sonar_result = await self.analyze_with_sonarcloud()
            self.analysis_results.append(sonar_result)
        
        # Run CodeClimate analysis if configured
        if self.config.codeclimate_token and self.config.codeclimate_repo_id:
            self.logger.info("Running CodeClimate analysis...")
            codeclimate_result = await self.analyze_with_codeclimate()
            self.analysis_results.append(codeclimate_result)
        
        # Run GitHub security analysis if configured
        if self.config.github_token and self.config.github_repository:
            self.logger.info("Running GitHub security analysis...")
            github_result = await self.analyze_github_security()
            self.analysis_results.append(github_result)
        
        # Calculate summary
        total_analyses = len(self.analysis_results)
        passed_analyses = sum(1 for result in self.analysis_results if result.status == "passed")
        failed_analyses = sum(1 for result in self.analysis_results if result.status == "failed")
        error_analyses = sum(1 for result in self.analysis_results if result.status == "error")
        
        overall_success = failed_analyses == 0 and error_analyses == 0
        total_issues = sum(result.issues_count for result in self.analysis_results)
        
        summary = {
            'success': overall_success,
            'total_analyses': total_analyses,
            'passed_analyses': passed_analyses,
            'failed_analyses': failed_analyses,
            'error_analyses': error_analyses,
            'total_issues': total_issues,
            'execution_time': sum(result.execution_time for result in self.analysis_results),
            'results': [
                {
                    'platform': result.platform,
                    'project_key': result.project_key,
                    'status': result.status,
                    'quality_gate': result.quality_gate,
                    'issues_count': result.issues_count,
                    'coverage': result.coverage,
                    'duplications': result.duplications,
                    'maintainability_rating': result.maintainability_rating,
                    'reliability_rating': result.reliability_rating,
                    'security_rating': result.security_rating,
                    'technical_debt': result.technical_debt,
                    'report_url': result.report_url,
                    'execution_time': result.execution_time,
                    'error_message': result.error_message
                }
                for result in self.analysis_results
            ]
        }
        
        self.logger.info(f"Analysis completed: {passed_analyses}/{total_analyses} analyses passed")
        return summary

    def generate_report(self, results: Dict[str, Any], output_path: Optional[str] = None) -> str:
        """Generate a detailed analysis report."""
        if output_path is None:
            output_path = os.path.join(self.config.report_dir, "web_analysis_report.json")
        
        try:
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            self.logger.info(f"Analysis report generated: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error generating report: {e}")
            return ""


async def main():
    """Main function for running web-based code analysis."""
    # Load configuration from environment variables
    config = WebAnalyzerConfig(
        sonar_token=os.getenv('SONAR_TOKEN'),
        sonar_organization=os.getenv('SONAR_ORGANIZATION'),
        sonar_project_key=os.getenv('SONAR_PROJECT_KEY'),
        codeclimate_token=os.getenv('CODECLIMATE_TOKEN'),
        codeclimate_repo_id=os.getenv('CODECLIMATE_REPO_ID'),
        github_token=os.getenv('GITHUB_TOKEN'),
        github_repository=os.getenv('GITHUB_REPOSITORY'),
        timeout=int(os.getenv('ANALYSIS_TIMEOUT', '300')),
        screenshot_dir=os.getenv('SCREENSHOT_DIR', 'analysis_screenshots'),
        report_dir=os.getenv('REPORT_DIR', 'analysis_reports')
    )
    
    # Initialize Puppeteer service
    mcp_client = MCPClient()
    puppeteer_service = PuppeteerService()
    
    # Run analyses
    analyzer = WebCodeAnalyzer(config, puppeteer_service)
    results = await analyzer.run_all_analyses()
    
    # Generate report
    report_path = analyzer.generate_report(results)
    
    # Print summary
    print(f"\n=== Web-Based Code Analysis Results ===")
    print(f"Total Analyses: {results['total_analyses']}")
    print(f"Passed: {results['passed_analyses']}")
    print(f"Failed: {results['failed_analyses']}")
    print(f"Errors: {results['error_analyses']}")
    print(f"Total Issues: {results['total_issues']}")
    print(f"Overall Success: {results['success']}")
    print(f"Report: {report_path}")
    
    # Print individual results
    for result in results['results']:
        print(f"\n{result['platform']}: {result['status'].upper()}")
        if result['issues_count'] > 0:
            print(f"  Issues: {result['issues_count']}")
        if result['coverage'] is not None:
            print(f"  Coverage: {result['coverage']}%")
        if result['report_url']:
            print(f"  Report: {result['report_url']}")
    
    # Exit with appropriate code
    sys.exit(0 if results['success'] else 1)


if __name__ == "__main__":
    asyncio.run(main())