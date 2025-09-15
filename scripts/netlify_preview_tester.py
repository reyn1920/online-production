#!/usr/bin/env python3
"""
Netlify Preview Testing Automation

This script automates the testing of Netlify deployment previews using Puppeteer
to ensure quality and functionality before production deployment.
"""

import asyncio
import json
import logging
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import requests
from integrations.puppeteer_service import PuppeteerService
from integrations.mcp_client import MCPClient


@dataclass
class TestResult:
    """Represents the result of a single test."""
    test_name: str
    passed: bool
    message: str
    screenshot_path: Optional[str] = None
    execution_time: float = 0.0
    error_details: Optional[str] = None


@dataclass
class PreviewTestConfig:
    """Configuration for preview testing."""
    netlify_site_id: str
    netlify_token: str
    github_token: str
    repository: str
    pr_number: Optional[int] = None
    branch_name: Optional[str] = None
    test_timeout: int = 300  # 5 minutes
    screenshot_dir: str = "screenshots"
    test_patterns: List[str] = None

    def __post_init__(self):
        if self.test_patterns is None:
            self.test_patterns = [
                "/",  # Home page
                "/about",  # About page
                "/contact",  # Contact page
                "/api/health"  # Health check endpoint
            ]


class NetlifyPreviewTester:
    """Automated testing for Netlify deployment previews."""

    def __init__(self, config: PreviewTestConfig, puppeteer_service: Optional[PuppeteerService] = None):
        self.config = config
        self.puppeteer_service = puppeteer_service or PuppeteerService()
        self.logger = self._setup_logging()
        self.test_results: List[TestResult] = []
        self.preview_url: Optional[str] = None
        
        # Ensure screenshot directory exists
        Path(self.config.screenshot_dir).mkdir(parents=True, exist_ok=True)

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

    async def get_preview_url(self) -> Optional[str]:
        """Get the Netlify preview URL for the deployment."""
        try:
            headers = {
                'Authorization': f'Bearer {self.config.netlify_token}',
                'Content-Type': 'application/json'
            }
            
            # Get site deployments
            url = f'https://api.netlify.com/api/v1/sites/{self.config.netlify_site_id}/deploys'
            params = {'per_page': 50}
            
            if self.config.pr_number:
                # Filter by PR number in commit message or branch
                params['branch'] = f'pull/{self.config.pr_number}/head'
            elif self.config.branch_name:
                params['branch'] = self.config.branch_name
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            deployments = response.json()
            
            # Find the most recent deployment that's ready
            for deployment in deployments:
                if deployment.get('state') == 'ready' and deployment.get('deploy_ssl_url'):
                    self.preview_url = deployment['deploy_ssl_url']
                    self.logger.info(f"Found preview URL: {self.preview_url}")
                    return self.preview_url
            
            self.logger.warning("No ready deployment found")
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting preview URL: {e}")
            return None

    async def wait_for_deployment(self, max_wait_time: int = 600) -> bool:
        """Wait for deployment to be ready."""
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            url = await self.get_preview_url()
            if url:
                return True
            
            self.logger.info("Waiting for deployment to be ready...")
            await asyncio.sleep(30)  # Wait 30 seconds before checking again
        
        self.logger.error(f"Deployment not ready after {max_wait_time} seconds")
        return False

    async def test_page_load(self, path: str) -> TestResult:
        """Test if a page loads successfully."""
        test_name = f"Page Load: {path}"
        start_time = time.time()
        
        try:
            if not self.preview_url:
                return TestResult(
                    test_name=test_name,
                    passed=False,
                    message="No preview URL available",
                    execution_time=time.time() - start_time
                )
            
            full_url = urljoin(self.preview_url, path)
            
            # Navigate to the page using Puppeteer
            if self.puppeteer_service and hasattr(self.puppeteer_service, 'mcp_client') and getattr(self.puppeteer_service, 'mcp_client', None):
                if hasattr(self.puppeteer_service, 'navigate_to_url'):
                    await getattr(self.puppeteer_service, 'navigate_to_url')(full_url)
                
                # Take a screenshot
                screenshot_name = f"page_load_{path.replace('/', '_').replace('?', '_')}.png"
                screenshot_path = os.path.join(self.config.screenshot_dir, screenshot_name)
                
                if hasattr(self.puppeteer_service, 'take_screenshot'):
                    await getattr(self.puppeteer_service, 'take_screenshot')(
                        screenshot_name,
                        width=1920,
                        height=1080
                    )
                
                # Check for JavaScript errors
                js_errors = []
                if hasattr(self.puppeteer_service, 'get_console_errors'):
                    js_errors = await getattr(self.puppeteer_service, 'get_console_errors')()
                
                if js_errors:
                    return TestResult(
                        test_name=test_name,
                        passed=False,
                        message=f"JavaScript errors found: {len(js_errors)} errors",
                        screenshot_path=screenshot_path,
                        execution_time=time.time() - start_time,
                        error_details=str(js_errors)
                    )
                
                return TestResult(
                    test_name=test_name,
                    passed=True,
                    message="Page loaded successfully",
                    screenshot_path=screenshot_path,
                    execution_time=time.time() - start_time
                )
            else:
                # Fallback to simple HTTP request
                response = requests.get(full_url, timeout=30)
                
                if response.status_code == 200:
                    return TestResult(
                        test_name=test_name,
                        passed=True,
                        message=f"HTTP {response.status_code} - Page accessible",
                        execution_time=time.time() - start_time
                    )
                else:
                    return TestResult(
                        test_name=test_name,
                        passed=False,
                        message=f"HTTP {response.status_code} - Page not accessible",
                        execution_time=time.time() - start_time
                    )
                    
        except Exception as e:
            return TestResult(
                test_name=test_name,
                passed=False,
                message=f"Error testing page: {str(e)}",
                execution_time=time.time() - start_time,
                error_details=str(e)
            )

    async def test_responsive_design(self, path: str = "/") -> TestResult:
        """Test responsive design at different viewport sizes."""
        test_name = f"Responsive Design: {path}"
        start_time = time.time()
        
        try:
            if not self.preview_url or not self.puppeteer_service or not hasattr(self.puppeteer_service, 'mcp_client') or not getattr(self.puppeteer_service, 'mcp_client', None):
                return TestResult(
                    test_name=test_name,
                    passed=False,
                    message="Puppeteer service not available",
                    execution_time=time.time() - start_time
                )
            
            full_url = urljoin(self.preview_url, path)
            if hasattr(self.puppeteer_service, 'navigate_to_url'):
                await getattr(self.puppeteer_service, 'navigate_to_url')(full_url)
            
            # Test different viewport sizes
            viewports = [
                (375, 667, "mobile"),    # iPhone SE
                (768, 1024, "tablet"),   # iPad
                (1920, 1080, "desktop") # Desktop
            ]
            
            screenshots = []
            
            for width, height, device_type in viewports:
                # Set viewport size
                if hasattr(self.puppeteer_service, 'set_viewport'):
                    await getattr(self.puppeteer_service, 'set_viewport')(width, height)
                
                # Take screenshot
                screenshot_name = f"responsive_{device_type}_{path.replace('/', '_')}.png"
                screenshot_path = os.path.join(self.config.screenshot_dir, screenshot_name)
                
                if hasattr(self.puppeteer_service, 'take_screenshot'):
                    await getattr(self.puppeteer_service, 'take_screenshot')(
                        screenshot_name,
                        width=width,
                        height=height
                    )
                
                screenshots.append(screenshot_path)
            
            return TestResult(
                test_name=test_name,
                passed=True,
                message=f"Responsive design tested across {len(viewports)} viewports",
                screenshot_path=", ".join(screenshots),
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return TestResult(
                test_name=test_name,
                passed=False,
                message=f"Error testing responsive design: {str(e)}",
                execution_time=time.time() - start_time,
                error_details=str(e)
            )

    async def test_performance_metrics(self, path: str = "/") -> TestResult:
        """Test performance metrics of the page."""
        test_name = f"Performance Metrics: {path}"
        start_time = time.time()
        
        try:
            if not self.preview_url or not self.puppeteer_service or not hasattr(self.puppeteer_service, 'mcp_client') or not getattr(self.puppeteer_service, 'mcp_client', None):
                return TestResult(
                    test_name=test_name,
                    passed=False,
                    message="Puppeteer service not available",
                    execution_time=time.time() - start_time
                )
            
            full_url = urljoin(self.preview_url, path)
            
            # Measure page load time
            load_start = time.time()
            if hasattr(self.puppeteer_service, 'navigate_to_url'):
                await getattr(self.puppeteer_service, 'navigate_to_url')(full_url)
            load_time = time.time() - load_start
            
            # Get performance metrics using JavaScript
            performance_script = """
            return {
                loadTime: performance.timing.loadEventEnd - performance.timing.navigationStart,
                domContentLoaded: performance.timing.domContentLoadedEventEnd - performance.timing.navigationStart,
                firstPaint: performance.getEntriesByType('paint').find(entry => entry.name === 'first-paint')?.startTime || 0,
                firstContentfulPaint: performance.getEntriesByType('paint').find(entry => entry.name === 'first-contentful-paint')?.startTime || 0
            };
            """
            
            metrics = None
            if hasattr(self.puppeteer_service, 'evaluate_javascript'):
                metrics = await getattr(self.puppeteer_service, 'evaluate_javascript')(performance_script)
            
            # Performance thresholds (in milliseconds)
            thresholds = {
                'load_time': 3000,  # 3 seconds
                'dom_content_loaded': 2000,  # 2 seconds
                'first_contentful_paint': 1500  # 1.5 seconds
            }
            
            issues = []
            if load_time * 1000 > thresholds['load_time']:
                issues.append(f"Load time ({load_time:.2f}s) exceeds threshold ({thresholds['load_time']/1000}s)")
            
            if metrics and isinstance(metrics, dict):
                if metrics.get('domContentLoaded', 0) > thresholds['dom_content_loaded']:
                    issues.append(f"DOM Content Loaded ({metrics['domContentLoaded']}ms) exceeds threshold ({thresholds['dom_content_loaded']}ms)")
                
                if metrics.get('firstContentfulPaint', 0) > thresholds['first_contentful_paint']:
                    issues.append(f"First Contentful Paint ({metrics['firstContentfulPaint']}ms) exceeds threshold ({thresholds['first_contentful_paint']}ms)")
            
            passed = len(issues) == 0
            message = "Performance metrics within acceptable ranges" if passed else f"Performance issues: {'; '.join(issues)}"
            
            return TestResult(
                test_name=test_name,
                passed=passed,
                message=message,
                execution_time=time.time() - start_time,
                error_details=json.dumps(metrics) if metrics else None
            )
            
        except Exception as e:
            return TestResult(
                test_name=test_name,
                passed=False,
                message=f"Error testing performance: {str(e)}",
                execution_time=time.time() - start_time,
                error_details=str(e)
            )

    async def test_accessibility(self, path: str = "/") -> TestResult:
        """Test basic accessibility features."""
        test_name = f"Accessibility: {path}"
        start_time = time.time()
        
        try:
            if not self.preview_url or not self.puppeteer_service or not hasattr(self.puppeteer_service, 'mcp_client') or not getattr(self.puppeteer_service, 'mcp_client', None):
                return TestResult(
                    test_name=test_name,
                    passed=False,
                    message="Puppeteer service not available",
                    execution_time=time.time() - start_time
                )
            
            full_url = urljoin(self.preview_url, path)
            if hasattr(self.puppeteer_service, 'navigate_to_url'):
                await getattr(self.puppeteer_service, 'navigate_to_url')(full_url)
            
            # Basic accessibility checks using JavaScript
            accessibility_script = """
            const issues = [];
            
            // Check for missing alt attributes on images
            const images = document.querySelectorAll('img');
            let missingAlt = 0;
            images.forEach(img => {
                if (!img.alt && !img.getAttribute('aria-label')) {
                    missingAlt++;
                }
            });
            if (missingAlt > 0) {
                issues.push(`${missingAlt} images missing alt text`);
            }
            
            // Check for heading structure
            const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
            if (headings.length === 0) {
                issues.push('No heading elements found');
            }
            
            // Check for form labels
            const inputs = document.querySelectorAll('input[type="text"], input[type="email"], input[type="password"], textarea');
            let unlabeledInputs = 0;
            inputs.forEach(input => {
                const hasLabel = input.labels && input.labels.length > 0;
                const hasAriaLabel = input.getAttribute('aria-label');
                const hasAriaLabelledBy = input.getAttribute('aria-labelledby');
                
                if (!hasLabel && !hasAriaLabel && !hasAriaLabelledBy) {
                    unlabeledInputs++;
                }
            });
            if (unlabeledInputs > 0) {
                issues.push(`${unlabeledInputs} form inputs missing labels`);
            }
            
            // Check for color contrast (basic check)
            const body = document.body;
            const computedStyle = window.getComputedStyle(body);
            const bgColor = computedStyle.backgroundColor;
            const textColor = computedStyle.color;
            
            return {
                issues: issues,
                totalImages: images.length,
                totalHeadings: headings.length,
                totalInputs: inputs.length,
                backgroundColor: bgColor,
                textColor: textColor
            };
            """
            
            accessibility_data = None
            if hasattr(self.puppeteer_service, 'evaluate_javascript'):
                accessibility_data = await getattr(self.puppeteer_service, 'evaluate_javascript')(accessibility_script)
            
            if accessibility_data and isinstance(accessibility_data, dict):
                issues = accessibility_data.get('issues', [])
                passed = len(issues) == 0
                
                if passed:
                    message = "Basic accessibility checks passed"
                else:
                    message = f"Accessibility issues found: {'; '.join(issues)}"
                
                return TestResult(
                    test_name=test_name,
                    passed=passed,
                    message=message,
                    execution_time=time.time() - start_time,
                    error_details=json.dumps(accessibility_data)
                )
            else:
                return TestResult(
                    test_name=test_name,
                    passed=False,
                    message="Could not evaluate accessibility",
                    execution_time=time.time() - start_time
                )
                
        except Exception as e:
            return TestResult(
                test_name=test_name,
                passed=False,
                message=f"Error testing accessibility: {str(e)}",
                execution_time=time.time() - start_time,
                error_details=str(e)
            )

    async def run_all_tests(self) -> Dict[str, any]:
        """Run all tests and return comprehensive results."""
        self.logger.info("Starting Netlify preview testing...")
        
        # Wait for deployment to be ready
        if not await self.wait_for_deployment():
            return {
                'success': False,
                'message': 'Deployment not ready for testing',
                'results': []
            }
        
        # Run tests for each configured path
        for path in self.config.test_patterns:
            self.logger.info(f"Testing path: {path}")
            
            # Page load test
            result = await self.test_page_load(path)
            self.test_results.append(result)
            
            # Only run additional tests if page loads successfully
            if result.passed:
                # Performance test
                perf_result = await self.test_performance_metrics(path)
                self.test_results.append(perf_result)
                
                # Accessibility test
                a11y_result = await self.test_accessibility(path)
                self.test_results.append(a11y_result)
        
        # Run responsive design test on home page
        responsive_result = await self.test_responsive_design("/")
        self.test_results.append(responsive_result)
        
        # Calculate summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result.passed)
        failed_tests = total_tests - passed_tests
        
        success = failed_tests == 0
        
        summary = {
            'success': success,
            'preview_url': self.preview_url,
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'execution_time': sum(result.execution_time for result in self.test_results),
            'results': [
                {
                    'test_name': result.test_name,
                    'passed': result.passed,
                    'message': result.message,
                    'screenshot_path': result.screenshot_path,
                    'execution_time': result.execution_time,
                    'error_details': result.error_details
                }
                for result in self.test_results
            ]
        }
        
        self.logger.info(f"Testing completed: {passed_tests}/{total_tests} tests passed")
        return summary

    def generate_report(self, results: Dict[str, any], output_path: str = "test_report.json") -> str:
        """Generate a detailed test report."""
        try:
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            self.logger.info(f"Test report generated: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error generating report: {e}")
            return ""


async def main():
    """Main function for running Netlify preview tests."""
    # Load configuration from environment variables
    config = PreviewTestConfig(
        netlify_site_id=os.getenv('NETLIFY_SITE_ID', ''),
        netlify_token=os.getenv('NETLIFY_TOKEN', ''),
        github_token=os.getenv('GITHUB_TOKEN', ''),
        repository=os.getenv('GITHUB_REPOSITORY', ''),
        pr_number=int(os.getenv('GITHUB_PR_NUMBER', '0')) or None,
        branch_name=os.getenv('GITHUB_HEAD_REF') or os.getenv('GITHUB_REF_NAME'),
        test_timeout=int(os.getenv('TEST_TIMEOUT', '300')),
        screenshot_dir=os.getenv('SCREENSHOT_DIR', 'screenshots')
    )
    
    if not config.netlify_site_id or not config.netlify_token:
        print("Error: NETLIFY_SITE_ID and NETLIFY_TOKEN environment variables are required")
        sys.exit(1)
    
    # Initialize Puppeteer service
    try:
        mcp_client = MCPClient()
        puppeteer_service = PuppeteerService()
    except Exception as e:
        print(f"Warning: Could not initialize Puppeteer service: {e}")
        puppeteer_service = None
    
    # Run tests
    tester = NetlifyPreviewTester(config, puppeteer_service)
    results = await tester.run_all_tests()
    
    # Generate report
    report_path = tester.generate_report(results)
    
    # Print summary
    print(f"\n=== Netlify Preview Test Results ===")
    print(f"Preview URL: {results.get('preview_url', 'N/A')}")
    print(f"Total Tests: {results['total_tests']}")
    print(f"Passed: {results['passed_tests']}")
    print(f"Failed: {results['failed_tests']}")
    print(f"Success: {results['success']}")
    print(f"Report: {report_path}")
    
    # Exit with appropriate code
    sys.exit(0 if results['success'] else 1)


if __name__ == "__main__":
    asyncio.run(main())