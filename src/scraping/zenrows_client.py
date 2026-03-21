"""ZenRows API client for web scraping operations"""

import requests
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta


logger = logging.getLogger(__name__)


@dataclass
class RateLimitStatus:
    """Rate limit status information"""
    requests_made: int
    requests_remaining: Optional[int]
    reset_time: Optional[datetime]
    is_limited: bool


@dataclass
class ZenRowsResponse:
    """Response from ZenRows API"""
    status_code: int
    content: str
    headers: Dict[str, str]
    success: bool
    error_message: Optional[str] = None


class ZenRowsClient:
    """Client for interacting with ZenRows API"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.zenrows.com/v1/",
                 timeout: int = 30, retry_attempts: int = 3):
        """
        Initialize ZenRows client
        
        Args:
            api_key: ZenRows API key for authentication
            base_url: Base URL for ZenRows API
            timeout: Request timeout in seconds
            retry_attempts: Number of retry attempts for failed requests
        """
        if not api_key:
            raise ValueError("API key is required for ZenRowsClient")
        
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        
        # Rate limiting tracking
        self._requests_made = 0
        self._last_request_time: Optional[datetime] = None
        self._rate_limit_reset: Optional[datetime] = None
        
        logger.info(f"ZenRowsClient initialized with base_url={base_url}, timeout={timeout}s")
    
    def fetch(self, url: str, params: Optional[Dict[str, Any]] = None) -> ZenRowsResponse:
        """
        Fetch content from a URL using ZenRows API
        
        Args:
            url: Target URL to scrape
            params: Optional additional parameters for the request
            
        Returns:
            ZenRowsResponse with status, content, and metadata
        """
        if not url:
            logger.error("Empty URL provided to fetch method")
            return ZenRowsResponse(
                status_code=400,
                content="",
                headers={},
                success=False,
                error_message="URL cannot be empty"
            )
        
        # Build request parameters
        request_params = {
            "url": url,
            "apikey": self.api_key,
            "js_render": "true",
            "premium_proxy": "true",
            "proxy_country": "us"
        }
        
        # Merge with additional params if provided
        if params:
            request_params.update(params)
        
        # Attempt request with retries
        last_error = None
        for attempt in range(self.retry_attempts):
            try:
                logger.debug(f"Fetching URL: {url} (attempt {attempt + 1}/{self.retry_attempts})")
                
                response = requests.get(
                    self.base_url,
                    params=request_params,
                    timeout=self.timeout
                )
                
                # Track request for rate limiting
                self._requests_made += 1
                self._last_request_time = datetime.now()
                
                # Check for rate limiting
                if response.status_code == 429:
                    logger.warning(f"Rate limit hit for URL: {url}")
                    retry_after = response.headers.get('Retry-After')
                    if retry_after:
                        self._rate_limit_reset = datetime.now() + timedelta(seconds=int(retry_after))
                    
                    return ZenRowsResponse(
                        status_code=429,
                        content="",
                        headers=dict(response.headers),
                        success=False,
                        error_message="Rate limit exceeded"
                    )
                
                # Check for authentication errors
                if response.status_code in [401, 403]:
                    logger.error(f"Authentication error (status {response.status_code}) for URL: {url}")
                    return ZenRowsResponse(
                        status_code=response.status_code,
                        content="",
                        headers=dict(response.headers),
                        success=False,
                        error_message="Authentication failed"
                    )
                
                # Check for server errors (5xx) - retry these
                if 500 <= response.status_code < 600:
                    logger.warning(f"Server error {response.status_code} for URL: {url}, attempt {attempt + 1}")
                    last_error = f"Server error: {response.status_code}"
                    continue
                
                # Success case
                if response.status_code == 200:
                    logger.info(f"Successfully fetched URL: {url}")
                    return ZenRowsResponse(
                        status_code=200,
                        content=response.text,
                        headers=dict(response.headers),
                        success=True
                    )
                
                # Other HTTP errors
                logger.warning(f"HTTP error {response.status_code} for URL: {url}")
                return ZenRowsResponse(
                    status_code=response.status_code,
                    content="",
                    headers=dict(response.headers),
                    success=False,
                    error_message=f"HTTP error: {response.status_code}"
                )
                
            except requests.Timeout:
                logger.warning(f"Timeout fetching URL: {url}, attempt {attempt + 1}")
                last_error = "Request timeout"
                continue
                
            except requests.RequestException as e:
                logger.warning(f"Network error fetching URL: {url}, attempt {attempt + 1}: {str(e)}")
                last_error = f"Network error: {str(e)}"
                continue
        
        # All retries exhausted
        logger.error(f"Failed to fetch URL after {self.retry_attempts} attempts: {url}")
        return ZenRowsResponse(
            status_code=0,
            content="",
            headers={},
            success=False,
            error_message=last_error or "Unknown error"
        )
    
    def is_available(self) -> bool:
        """
        Check if ZenRows API service is available
        
        Returns:
            True if service is available, False otherwise
        """
        try:
            # Make a simple test request to check service availability
            test_url = "https://httpbin.org/status/200"
            response = requests.get(
                self.base_url,
                params={
                    "url": test_url,
                    "apikey": self.api_key
                },
                timeout=10
            )
            
            # Service is available if we get any response (even rate limit or auth error)
            # Only network/connection errors indicate unavailability
            is_available = response.status_code != 0
            
            if is_available:
                logger.info("ZenRows API service is available")
            else:
                logger.warning("ZenRows API service is unavailable")
            
            return is_available
            
        except requests.RequestException as e:
            logger.error(f"ZenRows API service check failed: {str(e)}")
            return False
    
    def get_rate_limit_status(self) -> RateLimitStatus:
        """
        Get current rate limit status
        
        Returns:
            RateLimitStatus with current rate limiting information
        """
        is_limited = False
        requests_remaining = None
        
        # Check if we're currently rate limited
        if self._rate_limit_reset:
            if datetime.now() < self._rate_limit_reset:
                is_limited = True
            else:
                # Reset time has passed, clear the limit
                self._rate_limit_reset = None
        
        logger.debug(f"Rate limit status: {self._requests_made} requests made, limited={is_limited}")
        
        return RateLimitStatus(
            requests_made=self._requests_made,
            requests_remaining=requests_remaining,
            reset_time=self._rate_limit_reset,
            is_limited=is_limited
        )
