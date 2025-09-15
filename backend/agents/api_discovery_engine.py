#!/usr/bin/env python3
"""
API Discovery Engine

Automated API discovery and integration system that:
- Discovers APIs from multiple sources (PublicAPIs.org, RapidAPI, GitHub, etc.)
- Validates API endpoints and documentation
- Generates integration code automatically
- Manages API credentials and rate limits
- Provides unified interface for discovered APIs
"""

import asyncio
import json
import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

try:
    import requests
    from requests.auth import HTTPBasicAuth, HTTPDigestAuth
except ImportError:
    requests = None
    HTTPBasicAuth = None
    HTTPDigestAuth = None

try:
    from .enhanced_web_scraping_tools import (
        DataFormat,
        EnhancedWebScraper,
        ExtractionRule,
        ScrapingConfig,
        ScrapingMethod,
        ScrapingResult,
    )
except ImportError:
    logging.warning("Enhanced web scraping tools not available")
    EnhancedWebScraper = None
    DataFormat = None
    ExtractionRule = None
    ScrapingConfig = None
    ScrapingMethod = None
    ScrapingResult = None


class APICategory(Enum):
    """API categories for classification"""
    WEATHER = "weather"
    NEWS = "news"
    FINANCE = "finance"
    SOCIAL_MEDIA = "social_media"
    ENTERTAINMENT = "entertainment"
    PRODUCTIVITY = "productivity"
    DEVELOPER_TOOLS = "developer_tools"
    DATA_SCIENCE = "data_science"
    MACHINE_LEARNING = "machine_learning"
    BLOCKCHAIN = "blockchain"
    IOT = "iot"
    HEALTH = "health"
    EDUCATION = "education"
    TRAVEL = "travel"
    FOOD = "food"
    SPORTS = "sports"
    GAMING = "gaming"
    BUSINESS = "business"
    GOVERNMENT = "government"
    UTILITIES = "utilities"
    OTHER = "other"


class AuthType(Enum):
    """API authentication types"""
    NONE = "none"
    API_KEY = "api_key"
    BEARER_TOKEN = "bearer_token"
    BASIC_AUTH = "basic_auth"
    OAUTH2 = "oauth2"
    CUSTOM_HEADER = "custom_header"
    QUERY_PARAM = "query_param"


@dataclass
class APIInfo:
    """Information about a discovered API"""
    name: str
    description: str
    base_url: str
    category: APICategory
    auth_type: AuthType
    endpoints: List[Dict[str, Any]] = field(default_factory=list)
    documentation_url: Optional[str] = None
    pricing: Optional[str] = None
    rate_limits: Optional[Dict[str, Any]] = None
    headers: Dict[str, str] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)
    response_format: str = "json"
    status: str = "active"
    last_updated: datetime = field(default_factory=datetime.now)
    quality_score: float = 0.0
    popularity_score: float = 0.0


@dataclass
class APIDiscoveryConfig:
    """Configuration for API discovery"""
    max_apis_per_source: int = 100
    timeout: int = 30
    retry_attempts: int = 3
    rate_limit_delay: float = 1.0
    quality_threshold: float = 0.5
    cache_duration: int = 3600
    enable_validation: bool = True
    enable_code_generation: bool = True
    output_directory: Path = field(default_factory=lambda: Path("discovered_apis"))


class APIDiscoveryEngine:
    """Main API discovery engine"""
    
    def __init__(self, config: Optional[APIDiscoveryConfig] = None):
        self.config = config or APIDiscoveryConfig()
        self.logger = logging.getLogger(__name__)
        self.discovered_apis: Dict[str, List[APIInfo]] = {}
        self.api_cache: Dict[str, Any] = {}
        
        # Configure API sources
        self.api_sources = {
            "publicapis": {
                "method": "api_endpoint",
                "url": "https://api.publicapis.org/entries",
                "enabled": True
            },
            "rapidapi": {
                "method": "web_scraping",
                "url": "https://rapidapi.com/collection/list-of-free-apis",
                "enabled": False  # Requires API key
            },
            "github_awesome_apis": {
                "method": "markdown_parsing",
                "url": "https://raw.githubusercontent.com/public-apis/public-apis/master/README.md",
                "enabled": True
            }
        }
        
        # Initialize web scraper if available
        self.web_scraper = None
        if EnhancedWebScraper:
            try:
                self.web_scraper = EnhancedWebScraper()
            except Exception as e:
                self.logger.warning(f"Failed to initialize web scraper: {e}")
    
    async def discover_apis(self) -> Dict[str, List[APIInfo]]:
        """Discover APIs from all configured sources"""
        results = {}
        
        for source_name, source_config in self.api_sources.items():
            if not source_config.get("enabled", True):
                continue
                
            try:
                self.logger.info(f"Discovering APIs from {source_name}")
                apis = await self._discover_from_source(source_name, source_config)
                results[source_name] = apis
                self.logger.info(f"Discovered {len(apis)} APIs from {source_name}")
            except Exception as e:
                self.logger.error(f"Failed to discover APIs from {source_name}: {e}")
                results[source_name] = []
        
        self.discovered_apis = results
        return results
    
    async def _discover_from_source(self, source_name: str, source_config: Dict[str, Any]) -> List[APIInfo]:
        """Discover APIs from a specific source"""
        method = source_config["method"]
        
        if method == "api_endpoint":
            return await self._discover_from_api_endpoint(source_config["url"])
        elif method == "web_scraping":
            return await self._discover_from_web_scraping(source_name, source_config["url"])
        elif method == "markdown_parsing":
            return await self._discover_from_markdown(source_config["url"])
        else:
            self.logger.warning(f"Unknown discovery method: {method}")
            return []
    
    async def _discover_from_api_endpoint(self, url: str) -> List[APIInfo]:
        """Discover APIs from PublicAPIs.org API endpoint"""
        if not requests:
            self.logger.warning("requests library not available")
            return []
        
        try:
            response = requests.get(url, timeout=self.config.timeout)
            response.raise_for_status()
            data = response.json()
            
            apis = []
            entries = data.get("entries", [])
            
            for entry in entries[:self.config.max_apis_per_source]:
                try:
                    api_info = self._parse_publicapi_entry(entry)
                    if api_info:
                        apis.append(api_info)
                except Exception as e:
                    self.logger.warning(f"Failed to parse API entry: {e}")
                    continue
            
            return apis
            
        except Exception as e:
            self.logger.error(f"Failed to fetch APIs from {url}: {e}")
            return []
    
    async def _discover_from_web_scraping(self, source_name: str, url: str) -> List[APIInfo]:
        """Discover APIs using web scraping"""
        if not self.web_scraper:
            self.logger.warning("Web scraper not available")
            return []
        
        try:
            self.logger.info(f"Scraping APIs from {source_name}: {url}")
            # Implementation would depend on specific scraping logic
            return []
        except Exception as e:
            self.logger.error(f"Failed to scrape APIs from {source_name}: {e}")
            return []
    
    async def _discover_from_markdown(self, url: str) -> List[APIInfo]:
        """Discover APIs from markdown documentation"""
        if not requests:
            self.logger.warning("requests library not available")
            return []
        
        try:
            response = requests.get(url, timeout=self.config.timeout)
            response.raise_for_status()
            content = response.text
            
            # Parse markdown content for API information
            apis = self._parse_markdown_apis(content)
            return apis[:self.config.max_apis_per_source]
            
        except Exception as e:
            self.logger.error(f"Failed to fetch markdown from {url}: {e}")
            return []
    
    def _parse_publicapi_entry(self, entry: Dict[str, Any]) -> Optional[APIInfo]:
        """Parse a PublicAPI entry into APIInfo"""
        try:
            # Map category
            category_str = entry.get("Category", "other").lower().replace(" ", "_")
            category = APICategory.OTHER
            for cat in APICategory:
                if cat.value == category_str:
                    category = cat
                    break
            
            # Determine auth type
            auth = entry.get("Auth", "").lower()
            auth_type = AuthType.NONE
            if "api" in auth and "key" in auth:
                auth_type = AuthType.API_KEY
            elif "oauth" in auth:
                auth_type = AuthType.OAUTH2
            elif auth and auth != "no":
                auth_type = AuthType.API_KEY
            
            api_info = APIInfo(
                name=entry.get("API", "Unknown"),
                description=entry.get("Description", ""),
                base_url=entry.get("Link", ""),
                category=category,
                auth_type=auth_type,
                documentation_url=entry.get("Link", ""),
                response_format="json"
            )
            
            return api_info
            
        except Exception as e:
            self.logger.warning(f"Failed to parse PublicAPI entry: {e}")
            return None
    
    def _parse_markdown_apis(self, content: str) -> List[APIInfo]:
        """Parse APIs from markdown content"""
        apis = []
        
        # Simple regex patterns to extract API information
        # This is a basic implementation - could be enhanced
        lines = content.split('\n')
        current_category = APICategory.OTHER
        
        for line in lines:
            # Check for category headers
            if line.startswith('##') and not line.startswith('###'):
                category_name = line.replace('#', '').strip().lower().replace(' ', '_')
                for cat in APICategory:
                    if cat.value in category_name or category_name in cat.value:
                        current_category = cat
                        break
            
            # Look for API entries (basic pattern)
            if '|' in line and 'http' in line.lower():
                parts = [part.strip() for part in line.split('|')]
                if len(parts) >= 4:
                    try:
                        name = parts[1] if len(parts) > 1 else "Unknown"
                        description = parts[2] if len(parts) > 2 else ""
                        auth_info = parts[3] if len(parts) > 3 else ""
                        link = parts[4] if len(parts) > 4 else ""
                        
                        # Extract URL from markdown link format
                        url_match = re.search(r'\[.*?\]\((.*?)\)', link)
                        if url_match:
                            base_url = url_match.group(1)
                        else:
                            base_url = link
                        
                        if base_url and base_url.startswith('http'):
                            auth_type = AuthType.NONE
                            if 'api' in auth_info.lower() and 'key' in auth_info.lower():
                                auth_type = AuthType.API_KEY
                            elif 'oauth' in auth_info.lower():
                                auth_type = AuthType.OAUTH2
                            
                            api_info = APIInfo(
                                name=name,
                                description=description,
                                base_url=base_url,
                                category=current_category,
                                auth_type=auth_type,
                                documentation_url=base_url
                            )
                            apis.append(api_info)
                    except Exception as e:
                        continue
        
        return apis
    
    async def validate_api(self, api_info: APIInfo) -> bool:
        """Validate an API endpoint"""
        if not self.config.enable_validation or not requests:
            return True
        
        try:
            response = requests.head(
                api_info.base_url,
                timeout=self.config.timeout,
                allow_redirects=True
            )
            return response.status_code < 400
        except Exception:
            return False
    
    def generate_integration_code(self, api_info: APIInfo, language: str = "python") -> str:
        """Generate integration code for an API"""
        if not self.config.enable_code_generation:
            return ""
        
        if language.lower() == "python":
            return self._generate_python_code(api_info)
        else:
            return f"# Code generation for {language} not implemented yet"
    
    def _generate_python_code(self, api_info: APIInfo) -> str:
        """Generate Python integration code"""
        code_template = f'''
# Generated integration code for {api_info.name}
import requests
from typing import Dict, Any, Optional

class {api_info.name.replace(" ", "")}API:
    """Integration class for {api_info.name}"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.base_url = "{api_info.base_url}"
        self.api_key = api_key
        self.session = requests.Session()
        
        # Set up authentication
        if self.api_key and "{api_info.auth_type.value}" == "api_key":
            self.session.headers.update({{"Authorization": f"Bearer {{self.api_key}}"}}) 
    
    def make_request(self, endpoint: str, method: str = "GET", **kwargs) -> Dict[str, Any]:
        """Make a request to the API"""
        url = f"{{self.base_url}}/{{endpoint.lstrip('/')}}"
        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()
'''
        return code_template
    
    def save_discovered_apis(self, filename: Optional[str] = None) -> Path:
        """Save discovered APIs to a JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"discovered_apis_{timestamp}.json"
        
        output_path = self.config.output_directory / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert APIInfo objects to dictionaries for JSON serialization
        serializable_data = {}
        for source, apis in self.discovered_apis.items():
            serializable_data[source] = [
                {
                    "name": api.name,
                    "description": api.description,
                    "base_url": api.base_url,
                    "category": api.category.value,
                    "auth_type": api.auth_type.value,
                    "documentation_url": api.documentation_url,
                    "endpoints": api.endpoints,
                    "pricing": api.pricing,
                    "rate_limits": api.rate_limits,
                    "response_format": api.response_format,
                    "status": api.status,
                    "last_updated": api.last_updated.isoformat(),
                    "quality_score": api.quality_score,
                    "popularity_score": api.popularity_score
                }
                for api in apis
            ]
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Saved discovered APIs to {output_path}")
        return output_path
    
    async def run_discovery(self) -> Dict[str, List[APIInfo]]:
        """Run the complete API discovery process"""
        self.logger.info("Starting API discovery process")
        
        # Discover APIs
        results = await self.discover_apis()
        
        # Validate APIs if enabled
        if self.config.enable_validation:
            for source, apis in results.items():
                validated_apis = []
                for api in apis:
                    if await self.validate_api(api):
                        validated_apis.append(api)
                    else:
                        self.logger.warning(f"API validation failed: {api.name}")
                results[source] = validated_apis
        
        # Save results
        self.save_discovered_apis()
        
        total_apis = sum(len(apis) for apis in results.values())
        self.logger.info(f"Discovery complete. Found {total_apis} APIs across {len(results)} sources")
        
        return results


# Example usage
if __name__ == "__main__":
    async def main():
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Create discovery engine
        config = APIDiscoveryConfig(
            max_apis_per_source=50,
            enable_validation=True,
            enable_code_generation=True
        )
        
        engine = APIDiscoveryEngine(config)
        
        # Run discovery
        results = await engine.run_discovery()
        
        # Print summary
        for source, apis in results.items():
            print(f"\n{source}: {len(apis)} APIs")
            for api in apis[:3]:  # Show first 3 APIs
                print(f"  - {api.name}: {api.description[:100]}...")
    
    # Run the async main function
    asyncio.run(main())