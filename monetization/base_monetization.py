"""Base classes for monetization platform integrations."""

import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

class MonetizationError(Exception):
    """Base exception for monetization platform errors."""
    pass

class ProductCreationError(MonetizationError):
    """Exception raised when product creation fails."""
    pass

class RateLimitError(MonetizationError):
    """Exception raised when rate limit is exceeded."""
    pass

@dataclass
class Product:
    """Represents a digital product across platforms."""
    title: str
    description: str
    price: float
    currency: str = "USD"
    category: Optional[str] = None
    tags: List[str] = None
    digital_files: List[str] = None
    preview_images: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.digital_files is None:
            self.digital_files = []
        if self.preview_images is None:
            self.preview_images = []
        if self.metadata is None:
            self.metadata = {}

@dataclass
class ProductResponse:
    """Response from product creation/update operations."""
    success: bool
    product_id: Optional[str] = None
    product_url: Optional[str] = None
    error_message: Optional[str] = None
    platform_data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.platform_data is None:
            self.platform_data = {}

class BaseMonetizationAPI(ABC):
    """Base class for all monetization platform APIs."""
    
    def __init__(self, api_key: str, base_url: str, rate_limit: int = 60):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.rate_limit = rate_limit
        self.last_request_time = 0
        self.request_count = 0
        self.session = self._create_session()
        
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry strategy."""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _enforce_rate_limit(self):
        """Enforce rate limiting between API calls."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < (60 / self.rate_limit):
            sleep_time = (60 / self.rate_limit) - time_since_last_request
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
        self.request_count += 1
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> requests.Response:
        """Make an authenticated API request with rate limiting."""
        self._enforce_rate_limit()
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Add authentication headers
        request_headers = self._get_auth_headers()
        if headers:
            request_headers.update(headers)
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=request_headers,
                timeout=30
            )
            
            if response.status_code == 429:
                raise RateLimitError("Rate limit exceeded")
            
            response.raise_for_status()
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise MonetizationError(f"API request failed: {e}")
    
    @abstractmethod
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests."""
        pass
    
    @abstractmethod
    def create_product(self, product: Product) -> ProductResponse:
        """Create a new product on the platform."""
        pass
    
    @abstractmethod
    def update_product(self, product_id: str, product: Product) -> ProductResponse:
        """Update an existing product on the platform."""
        pass
    
    @abstractmethod
    def delete_product(self, product_id: str) -> bool:
        """Delete a product from the platform."""
        pass
    
    @abstractmethod
    def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get product details from the platform."""
        pass
    
    @abstractmethod
    def list_products(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """List products from the platform."""
        pass
    
    @abstractmethod
    def get_sales_data(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get sales analytics for the specified date range."""
        pass
    
    def health_check(self) -> bool:
        """Check if the API is accessible and credentials are valid."""
        try:
            # Most platforms have a simple endpoint to check API status
            response = self._make_request('GET', '/health')
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Health check failed for {self.__class__.__name__}: {e}")
            return False
    
    def get_platform_name(self) -> str:
        """Get the name of the monetization platform."""
        return self.__class__.__name__.replace('API', '')
    
    def get_request_stats(self) -> Dict[str, Any]:
        """Get API request statistics."""
        return {
            'total_requests': self.request_count,
            'rate_limit': self.rate_limit,
            'last_request_time': self.last_request_time,
            'platform': self.get_platform_name()
        }