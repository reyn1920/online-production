#!/usr/bin/env python3
"""
Enhanced Web Scraping Tools Module

Implements comprehensive web scraping capabilities with:
- Advanced error handling and retry mechanisms
- Proxy rotation and anti-detection measures
- Rate limiting and respectful scraping
- Multiple parsing strategies (BeautifulSoup, Selenium, requests-html)
- Data extraction pipelines with validation
- Caching and performance optimization
"""

import asyncio
import hashlib
import json
import logging
import os
import pickle
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from urllib.parse import quote, urljoin, urlparse

try:
    import lxml
    import requests
    from bs4 import BeautifulSoup
    from requests.adapters import HTTPAdapter
    from requests.packages.urllib3.util.retry import Retry
except ImportError as e:
    logging.warning(
        f"Required dependency missing: {e}. Basic scraping features will be limited."
    )
    requests = None
    BeautifulSoup = None
    lxml = None

try:
    from selenium import webdriver
    from selenium.common.exceptions import NoSuchElementException, TimeoutException
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait
except ImportError as e:
    logging.warning(
        f"Selenium not available: {e}. Advanced browser automation will be limited."
    )
    webdriver = None
    By = None
    Keys = None
    ActionChains = None
    WebDriverWait = None
    EC = None
    ChromeOptions = None
    FirefoxOptions = None
    TimeoutException = None
    NoSuchElementException = None

try:
    import requests_html
except ImportError:
    logging.warning(
        "requests-html not available. JavaScript rendering will be limited."
    )
    requests_html = None


class ScrapingMethod(Enum):
    """Available scraping methods"""

    REQUESTS = "requests"
    SELENIUM = "selenium"
    REQUESTS_HTML = "requests_html"
    HYBRID = "hybrid"


class ProxyType(Enum):
    """Proxy types for rotation"""

    HTTP = "http"
    HTTPS = "https"
    SOCKS4 = "socks4"
    SOCKS5 = "socks5"


class DataFormat(Enum):
    """Output data formats"""

    JSON = "json"
    CSV = "csv"
    XML = "xml"
    HTML = "html"
    TEXT = "text"


@dataclass
class ProxyConfig:
    """Proxy configuration"""

    host: str
    port: int
    proxy_type: ProxyType = ProxyType.HTTP
    username: Optional[str] = None
    password: Optional[str] = None
    is_active: bool = True
    success_rate: float = 1.0
    last_used: Optional[datetime] = None


@dataclass
class ScrapingConfig:
    """Configuration for scraping operations"""

    method: ScrapingMethod = ScrapingMethod.REQUESTS
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout: float = 30.0
    rate_limit: float = 1.0  # Seconds between requests
    use_proxies: bool = False
    rotate_user_agents: bool = True
    respect_robots_txt: bool = True
    cache_responses: bool = True
    cache_duration: int = 3600  # Seconds
    javascript_enabled: bool = False
    headless: bool = True
    custom_headers: Dict[str, str] = field(default_factory=dict)
    cookies: Dict[str, str] = field(default_factory=dict)


@dataclass
class ExtractionRule:
    """Rule for extracting data from HTML"""

    name: str
    selector: str  # CSS selector or XPath
    attribute: Optional[str] = None  # Extract attribute value instead of text
    regex_pattern: Optional[str] = None  # Apply regex to extracted text
    is_list: bool = False  # Extract multiple elements
    required: bool = True  # Fail if not found
    default_value: Any = None
    post_process: Optional[Callable] = None  # Function to process extracted data


@dataclass
class ScrapingResult:
    """Result of a scraping operation"""

    url: str
    status_code: int
    success: bool
    data: Dict[str, Any]
    raw_html: Optional[str] = None
    error_message: Optional[str] = None
    response_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    method_used: Optional[ScrapingMethod] = None
    proxy_used: Optional[str] = None


class EnhancedWebScraper:
    """Enhanced web scraper with advanced features"""

    def __init__(self, config: Optional[ScrapingConfig] = None):
        self.config = config or ScrapingConfig()
        self.logger = logging.getLogger(__name__)
        self.session = None
        self.driver = None
        self.proxies: List[ProxyConfig] = []
        self.user_agents = self._load_user_agents()
        self.cache_dir = Path("scraping_cache")
        self.cache_dir.mkdir(exist_ok=True)
        self.last_request_time = 0.0

        # Initialize session with retry strategy
        self._init_session()

        # Load proxies if configured
        if self.config.use_proxies:
            self._load_proxies()

    def _init_session(self) -> None:
        """Initialize requests session with retry strategy"""
        if not requests:
            return

        self.session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=self.config.retry_delay,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "OPTIONS"],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set default headers
        self.session.headers.update(
            {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
        )

        # Add custom headers
        if self.config.custom_headers:
            self.session.headers.update(self.config.custom_headers)

        # Add cookies
        if self.config.cookies:
            self.session.cookies.update(self.config.cookies)

    def _load_user_agents(self) -> List[str]:
        """Load realistic user agents"""
        return [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (X11; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
        ]

    def _load_proxies(self) -> None:
        """Load proxy configurations from file or environment"""
        # Try to load from environment variable
        proxy_list = os.getenv("SCRAPING_PROXIES")
        if proxy_list:
            try:
                proxy_data = json.loads(proxy_list)
                for proxy in proxy_data:
                    self.proxies.append(ProxyConfig(**proxy))
            except json.JSONDecodeError:
                self.logger.warning("Invalid proxy configuration in environment")

        # Try to load from file
        proxy_file = Path("proxies.json")
        if proxy_file.exists():
            try:
                with open(proxy_file, "r") as f:
                    proxy_data = json.load(f)
                    for proxy in proxy_data:
                        self.proxies.append(ProxyConfig(**proxy))
            except (json.JSONDecodeError, FileNotFoundError):
                self.logger.warning("Could not load proxy configuration file")

    def _get_cache_key(self, url: str, method: ScrapingMethod) -> str:
        """Generate cache key for URL and method"""
        key_data = f"{url}_{method.value}_{self.config.javascript_enabled}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _get_cached_response(self, cache_key: str) -> Optional[Dict]:
        """Get cached response if available and not expired"""
        if not self.config.cache_responses:
            return None

        cache_file = self.cache_dir / f"{cache_key}.pkl"
        if not cache_file.exists():
            return None

        try:
            with open(cache_file, "rb") as f:
                cached_data = pickle.load(f)

            # Check if cache is expired
            if datetime.now() - cached_data["timestamp"] > timedelta(
                seconds=self.config.cache_duration
            ):
                cache_file.unlink()  # Remove expired cache
                return None

            return cached_data
        except (pickle.PickleError, KeyError, FileNotFoundError):
            return None

    def _cache_response(self, cache_key: str, data: Dict) -> None:
        """Cache response data"""
        if not self.config.cache_responses:
            return

        cache_file = self.cache_dir / f"{cache_key}.pkl"
        try:
            with open(cache_file, "wb") as f:
                pickle.dump(data, f)
        except pickle.PickleError:
            self.logger.warning(f"Failed to cache response for key: {cache_key}")

    def _get_random_proxy(self) -> Optional[Dict[str, str]]:
        """Get a random active proxy"""
        if not self.proxies:
            return None

        active_proxies = [p for p in self.proxies if p.is_active]
        if not active_proxies:
            return None

        # Select proxy based on success rate (weighted random)
        weights = [p.success_rate for p in active_proxies]
        proxy = random.choices(active_proxies, weights=weights)[0]

        proxy_url = f"{proxy.proxy_type.value}://"
        if proxy.username and proxy.password:
            proxy_url += f"{proxy.username}:{proxy.password}@"
        proxy_url += f"{proxy.host}:{proxy.port}"

        return {"http": proxy_url, "https": proxy_url}

    def _get_random_user_agent(self) -> str:
        """Get a random user agent"""
        return random.choice(self.user_agents)

    async def _respect_rate_limit(self) -> None:
        """Ensure rate limiting is respected"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.config.rate_limit:
            sleep_time = self.config.rate_limit - time_since_last
            await asyncio.sleep(sleep_time)

        self.last_request_time = time.time()

    async def _scrape_with_requests(self, url: str) -> ScrapingResult:
        """Scrape using requests library"""
        if not requests:
            return ScrapingResult(
                url=url,
                status_code=0,
                success=False,
                data={},
                error_message="requests library not available",
            )

        start_time = time.time()
        proxy_used = None

        try:
            # Set up request parameters
            kwargs = {"timeout": self.config.timeout, "allow_redirects": True}

            # Add proxy if configured
            if self.config.use_proxies:
                proxy = self._get_random_proxy()
                if proxy:
                    kwargs["proxies"] = proxy
                    proxy_used = list(proxy.values())[0]

            # Rotate user agent
            if self.config.rotate_user_agents:
                self.session.headers["User-Agent"] = self._get_random_user_agent()

            # Make request
            response = self.session.get(url, **kwargs)
            response.raise_for_status()

            response_time = time.time() - start_time

            return ScrapingResult(
                url=url,
                status_code=response.status_code,
                success=True,
                data={"html": response.text},
                raw_html=response.text,
                response_time=response_time,
                method_used=ScrapingMethod.REQUESTS,
                proxy_used=proxy_used,
            )

        except requests.RequestException as e:
            response_time = time.time() - start_time
            return ScrapingResult(
                url=url,
                status_code=(
                    getattr(e.response, "status_code", 0)
                    if hasattr(e, "response")
                    else 0
                ),
                success=False,
                data={},
                error_message=str(e),
                response_time=response_time,
                method_used=ScrapingMethod.REQUESTS,
                proxy_used=proxy_used,
            )

    async def _scrape_with_selenium(self, url: str) -> ScrapingResult:
        """Scrape using Selenium WebDriver"""
        if not webdriver:
            return ScrapingResult(
                url=url,
                status_code=0,
                success=False,
                data={},
                error_message="Selenium not available",
            )

        start_time = time.time()
        driver = None

        try:
            # Set up Chrome options
            options = ChromeOptions()
            if self.config.headless:
                options.add_argument("--headless")

            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")

            # Add user agent
            if self.config.rotate_user_agents:
                user_agent = self._get_random_user_agent()
                options.add_argument(f"--user-agent={user_agent}")

            # Add proxy if configured
            proxy_used = None
            if self.config.use_proxies:
                proxy = self._get_random_proxy()
                if proxy:
                    proxy_url = list(proxy.values())[0]
                    options.add_argument(f"--proxy-server={proxy_url}")
                    proxy_used = proxy_url

            # Initialize driver
            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(self.config.timeout)

            # Navigate to URL
            driver.get(url)

            # Wait for page to load if JavaScript is enabled
            if self.config.javascript_enabled:
                WebDriverWait(driver, 10).until(
                    lambda d: d.execute_script("return document.readyState")
                    == "complete"
                )

            html = driver.page_source
            response_time = time.time() - start_time

            return ScrapingResult(
                url=url,
                status_code=200,  # Selenium doesn't provide status codes
                success=True,
                data={"html": html},
                raw_html=html,
                response_time=response_time,
                method_used=ScrapingMethod.SELENIUM,
                proxy_used=proxy_used,
            )

        except Exception as e:
            response_time = time.time() - start_time
            return ScrapingResult(
                url=url,
                status_code=0,
                success=False,
                data={},
                error_message=str(e),
                response_time=response_time,
                method_used=ScrapingMethod.SELENIUM,
            )
        finally:
            if driver:
                driver.quit()

    async def _scrape_with_requests_html(self, url: str) -> ScrapingResult:
        """Scrape using requests-html library"""
        if not requests_html:
            return ScrapingResult(
                url=url,
                status_code=0,
                success=False,
                data={},
                error_message="requests-html not available",
            )

        start_time = time.time()

        try:
            session = requests_html.HTMLSession()

            # Set user agent
            if self.config.rotate_user_agents:
                session.headers["User-Agent"] = self._get_random_user_agent()

            # Make request
            response = session.get(url, timeout=self.config.timeout)
            response.raise_for_status()

            # Render JavaScript if enabled
            if self.config.javascript_enabled:
                response.html.render(timeout=20)

            html = response.html.html
            response_time = time.time() - start_time

            return ScrapingResult(
                url=url,
                status_code=response.status_code,
                success=True,
                data={"html": html},
                raw_html=html,
                response_time=response_time,
                method_used=ScrapingMethod.REQUESTS_HTML,
            )

        except Exception as e:
            response_time = time.time() - start_time
            return ScrapingResult(
                url=url,
                status_code=0,
                success=False,
                data={},
                error_message=str(e),
                response_time=response_time,
                method_used=ScrapingMethod.REQUESTS_HTML,
            )

    async def scrape_url(
        self, url: str, extraction_rules: Optional[List[ExtractionRule]] = None
    ) -> ScrapingResult:
        """Scrape a single URL with the configured method"""
        # Check cache first
        cache_key = self._get_cache_key(url, self.config.method)
        cached_result = self._get_cached_response(cache_key)
        if cached_result:
            self.logger.info(f"Using cached result for {url}")
            return ScrapingResult(**cached_result)

        # Respect rate limiting
        await self._respect_rate_limit()

        # Choose scraping method
        if self.config.method == ScrapingMethod.REQUESTS:
            result = await self._scrape_with_requests(url)
        elif self.config.method == ScrapingMethod.SELENIUM:
            result = await self._scrape_with_selenium(url)
        elif self.config.method == ScrapingMethod.REQUESTS_HTML:
            result = await self._scrape_with_requests_html(url)
        elif self.config.method == ScrapingMethod.HYBRID:
            # Try requests first, fallback to Selenium if needed
            result = await self._scrape_with_requests(url)
            if not result.success and self.config.javascript_enabled:
                result = await self._scrape_with_selenium(url)
        else:
            result = await self._scrape_with_requests(url)

        # Extract data if rules provided and scraping was successful
        if result.success and extraction_rules and result.raw_html:
            extracted_data = self._extract_data(result.raw_html, extraction_rules)
            result.data.update(extracted_data)

        # Cache the result
        if result.success:
            cache_data = {
                "url": result.url,
                "status_code": result.status_code,
                "success": result.success,
                "data": result.data,
                "raw_html": result.raw_html,
                "response_time": result.response_time,
                "timestamp": result.timestamp,
                "method_used": result.method_used,
                "proxy_used": result.proxy_used,
            }
            self._cache_response(cache_key, cache_data)

        return result

    def _extract_data(
        self, html: str, extraction_rules: List[ExtractionRule]
    ) -> Dict[str, Any]:
        """Extract data from HTML using extraction rules"""
        if not BeautifulSoup:
            return {"error": "BeautifulSoup not available for data extraction"}

        soup = BeautifulSoup(html, "lxml" if lxml else "html.parser")
        extracted_data = {}

        for rule in extraction_rules:
            try:
                if rule.is_list:
                    elements = soup.select(rule.selector)
                    values = []
                    for element in elements:
                        value = self._extract_element_value(element, rule)
                        if value is not None:
                            values.append(value)
                    extracted_data[rule.name] = values
                else:
                    element = soup.select_one(rule.selector)
                    if element:
                        value = self._extract_element_value(element, rule)
                        extracted_data[rule.name] = value
                    elif rule.required:
                        extracted_data[rule.name] = rule.default_value
                        self.logger.warning(f"Required field '{rule.name}' not found")
                    else:
                        extracted_data[rule.name] = rule.default_value

            except Exception as e:
                self.logger.error(f"Error extracting data for rule '{rule.name}': {e}")
                extracted_data[rule.name] = rule.default_value

        return extracted_data

    def _extract_element_value(self, element, rule: ExtractionRule) -> Any:
        """Extract value from a single element"""
        if rule.attribute:
            value = element.get(rule.attribute)
        else:
            value = element.get_text(strip=True)

        if value and rule.regex_pattern:
            import re

            match = re.search(rule.regex_pattern, value)
            value = match.group(1) if match and match.groups() else value

        if value and rule.post_process:
            try:
                value = rule.post_process(value)
            except Exception as e:
                self.logger.warning(
                    f"Post-processing failed for rule '{rule.name}': {e}"
                )

        return value

    async def scrape_multiple_urls(
        self,
        urls: List[str],
        extraction_rules: Optional[List[ExtractionRule]] = None,
        max_concurrent: int = 5,
    ) -> List[ScrapingResult]:
        """Scrape multiple URLs concurrently"""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def scrape_with_semaphore(url: str) -> ScrapingResult:
            async with semaphore:
                return await self.scrape_url(url, extraction_rules)

        tasks = [scrape_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(
                    ScrapingResult(
                        url=urls[i],
                        status_code=0,
                        success=False,
                        data={},
                        error_message=str(result),
                    )
                )
            else:
                final_results.append(result)

        return final_results

    def export_results(
        self, results: List[ScrapingResult], format_type: DataFormat, output_file: str
    ) -> bool:
        """Export scraping results to file"""
        try:
            if format_type == DataFormat.JSON:
                data = [
                    {
                        "url": r.url,
                        "status_code": r.status_code,
                        "success": r.success,
                        "data": r.data,
                        "error_message": r.error_message,
                        "response_time": r.response_time,
                        "timestamp": r.timestamp.isoformat(),
                        "method_used": r.method_used.value if r.method_used else None,
                        "proxy_used": r.proxy_used,
                    }
                    for r in results
                ]

                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

            elif format_type == DataFormat.CSV:
                import csv

                with open(output_file, "w", newline="", encoding="utf-8") as f:
                    if results:
                        # Get all unique keys from data
                        all_keys = set()
                        for result in results:
                            all_keys.update(result.data.keys())

                        fieldnames = [
                            "url",
                            "status_code",
                            "success",
                            "error_message",
                            "response_time",
                            "timestamp",
                            "method_used",
                            "proxy_used",
                        ] + list(all_keys)

                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()

                        for result in results:
                            row = {
                                "url": result.url,
                                "status_code": result.status_code,
                                "success": result.success,
                                "error_message": result.error_message,
                                "response_time": result.response_time,
                                "timestamp": result.timestamp.isoformat(),
                                "method_used": (
                                    result.method_used.value
                                    if result.method_used
                                    else None
                                ),
                                "proxy_used": result.proxy_used,
                            }
                            row.update(result.data)
                            writer.writerow(row)

            return True

        except Exception as e:
            self.logger.error(f"Failed to export results: {e}")
            return False

    def get_statistics(self, results: List[ScrapingResult]) -> Dict[str, Any]:
        """Get statistics from scraping results"""
        if not results:
            return {}

        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        stats = {
            "total_requests": len(results),
            "successful_requests": len(successful),
            "failed_requests": len(failed),
            "success_rate": len(successful) / len(results) * 100,
            "average_response_time": sum(r.response_time for r in results)
            / len(results),
            "total_response_time": sum(r.response_time for r in results),
            "methods_used": {},
            "status_codes": {},
            "error_types": {},
        }

        # Method statistics
        for result in results:
            if result.method_used:
                method = result.method_used.value
                stats["methods_used"][method] = stats["methods_used"].get(method, 0) + 1

        # Status code statistics
        for result in results:
            code = result.status_code
            stats["status_codes"][code] = stats["status_codes"].get(code, 0) + 1

        # Error type statistics
        for result in failed:
            if result.error_message:
                error_type = type(result.error_message).__name__
                stats["error_types"][error_type] = (
                    stats["error_types"].get(error_type, 0) + 1
                )

        return stats

    def cleanup(self) -> None:
        """Clean up resources"""
        if self.session:
            self.session.close()

        if self.driver:
            self.driver.quit()

        self.logger.info("Enhanced Web Scraper cleanup completed")


# Example usage and testing
if __name__ == "__main__":

    async def test_enhanced_scraper():
        """Test the enhanced web scraper"""
        # Configure scraper
        config = ScrapingConfig(
            method=ScrapingMethod.REQUESTS,
            max_retries=3,
            rate_limit=1.0,
            cache_responses=True,
            rotate_user_agents=True,
        )

        scraper = EnhancedWebScraper(config)

        # Define extraction rules
        extraction_rules = [
            ExtractionRule(name="title", selector="title", required=True),
            ExtractionRule(
                name="meta_description",
                selector="meta[name='description']",
                attribute="content",
                required=False,
                default_value="No description",
            ),
            ExtractionRule(
                name="headings", selector="h1, h2, h3", is_list=True, required=False
            ),
        ]

        # Test URLs
        test_urls = [
            "https://httpbin.org/html",
            "https://httpbin.org/json",
            "https://example.com",
        ]

        try:
            # Scrape multiple URLs
            results = await scraper.scrape_multiple_urls(test_urls, extraction_rules)

            # Print results
            for result in results:
                print(f"\nURL: {result.url}")
                print(f"Success: {result.success}")
                print(f"Status Code: {result.status_code}")
                print(f"Response Time: {result.response_time:.2f}s")
                if result.success:
                    print(f"Data: {result.data}")
                else:
                    print(f"Error: {result.error_message}")

            # Export results
            scraper.export_results(results, DataFormat.JSON, "scraping_results.json")

            # Get statistics
            stats = scraper.get_statistics(results)
            print(f"\nStatistics: {json.dumps(stats, indent=2)}")

        finally:
            scraper.cleanup()

    # Run the test
    asyncio.run(test_enhanced_scraper())
