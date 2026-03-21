"""Serper API client for Google Search and Google Scholar operations"""

import requests
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime


logger = logging.getLogger(__name__)


@dataclass
class SerperSearchResult:
    """Single search result from Serper API"""
    title: str
    link: str
    snippet: str
    date: Optional[str] = None
    position: Optional[int] = None


@dataclass
class SerperScholarResult:
    """Single scholar result from Serper API"""
    title: str
    link: str
    snippet: str
    publication: Optional[str] = None
    cited_by: Optional[int] = None
    year: Optional[str] = None
    position: Optional[int] = None


@dataclass
class SerperResponse:
    """Response from Serper API"""
    status_code: int
    results: List[Any]
    success: bool
    error_message: Optional[str] = None
    search_metadata: Optional[Dict[str, Any]] = None


class SerperClient:
    """Client for interacting with Serper.dev API"""
    
    def __init__(self, api_key: str, base_url: str = "https://google.serper.dev",
                 timeout: int = 30, retry_attempts: int = 3):
        """
        Initialize Serper client
        
        Args:
            api_key: Serper API key for authentication
            base_url: Base URL for Serper API
            timeout: Request timeout in seconds
            retry_attempts: Number of retry attempts for failed requests
        """
        if not api_key:
            raise ValueError("API key is required for SerperClient")
        
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        
        # Request tracking
        self._requests_made = 0
        self._last_request_time: Optional[datetime] = None
        
        logger.info(f"SerperClient initialized with base_url={base_url}, timeout={timeout}s")
    
    def search_google(self, query: str, num_results: int = 10) -> SerperResponse:
        """
        Search Google using Serper API
        
        Args:
            query: Search query string
            num_results: Number of results to return (default: 10)
            
        Returns:
            SerperResponse with search results
        """
        if not query:
            logger.error("Empty query provided to search_google")
            return SerperResponse(
                status_code=400,
                results=[],
                success=False,
                error_message="Query cannot be empty"
            )
        
        endpoint = f"{self.base_url}/search"
        payload = {
            "q": query,
            "num": num_results
        }
        
        return self._make_request(endpoint, payload, "google")
    
    def search_scholar(self, query: str, num_results: int = 10) -> SerperResponse:
        """
        Search Google Scholar using Serper API
        
        Args:
            query: Search query string
            num_results: Number of results to return (default: 10)
            
        Returns:
            SerperResponse with scholar results
        """
        if not query:
            logger.error("Empty query provided to search_scholar")
            return SerperResponse(
                status_code=400,
                results=[],
                success=False,
                error_message="Query cannot be empty"
            )
        
        endpoint = f"{self.base_url}/scholar"
        payload = {
            "q": query,
            "num": num_results
        }
        
        return self._make_request(endpoint, payload, "scholar")
    
    def _make_request(self, endpoint: str, payload: Dict[str, Any], search_type: str) -> SerperResponse:
        """
        Make HTTP request to Serper API with retry logic
        
        Args:
            endpoint: API endpoint URL
            payload: Request payload
            search_type: Type of search ("google" or "scholar")
            
        Returns:
            SerperResponse with results or error
        """
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        
        last_error = None
        
        for attempt in range(self.retry_attempts):
            try:
                logger.debug(f"Making {search_type} search request (attempt {attempt + 1}/{self.retry_attempts})")
                logger.debug(f"Query: {payload.get('q', '')}")
                
                response = requests.post(
                    endpoint,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout
                )
                
                # Track request
                self._requests_made += 1
                self._last_request_time = datetime.now()
                
                # Check for rate limiting
                if response.status_code == 429:
                    logger.warning(f"Rate limit hit for {search_type} search")
                    return SerperResponse(
                        status_code=429,
                        results=[],
                        success=False,
                        error_message="Rate limit exceeded"
                    )
                
                # Check for authentication errors
                if response.status_code in [401, 403]:
                    logger.error(f"Authentication error (status {response.status_code}) for {search_type} search")
                    return SerperResponse(
                        status_code=response.status_code,
                        results=[],
                        success=False,
                        error_message="Authentication failed"
                    )
                
                # Check for payment required (out of credits)
                if response.status_code == 402:
                    logger.error(f"Payment required (status 402) - API credits exhausted")
                    return SerperResponse(
                        status_code=402,
                        results=[],
                        success=False,
                        error_message="API credits exhausted"
                    )
                
                # Check for server errors (5xx) - retry these
                if 500 <= response.status_code < 600:
                    logger.warning(f"Server error {response.status_code} for {search_type} search, attempt {attempt + 1}")
                    last_error = f"Server error: {response.status_code}"
                    continue
                
                # Success case
                if response.status_code == 200:
                    try:
                        data = response.json()
                        results = self._parse_results(data, search_type)
                        
                        logger.info(f"Successfully completed {search_type} search: {len(results)} results")
                        
                        return SerperResponse(
                            status_code=200,
                            results=results,
                            success=True,
                            search_metadata=data.get('searchParameters')
                        )
                    except Exception as e:
                        logger.error(f"Error parsing {search_type} response: {str(e)}")
                        return SerperResponse(
                            status_code=200,
                            results=[],
                            success=False,
                            error_message=f"Failed to parse response: {str(e)}"
                        )
                
                # Other HTTP errors
                logger.warning(f"HTTP error {response.status_code} for {search_type} search")
                return SerperResponse(
                    status_code=response.status_code,
                    results=[],
                    success=False,
                    error_message=f"HTTP error: {response.status_code}"
                )
                
            except requests.Timeout:
                logger.warning(f"Timeout for {search_type} search, attempt {attempt + 1}")
                last_error = "Request timeout"
                continue
                
            except requests.RequestException as e:
                logger.warning(f"Network error for {search_type} search, attempt {attempt + 1}: {str(e)}")
                last_error = f"Network error: {str(e)}"
                continue
        
        # All retries exhausted
        logger.error(f"Failed {search_type} search after {self.retry_attempts} attempts")
        return SerperResponse(
            status_code=0,
            results=[],
            success=False,
            error_message=last_error or "Unknown error"
        )
    
    def _parse_results(self, data: Dict[str, Any], search_type: str) -> List[Any]:
        """
        Parse results from Serper API response
        
        Args:
            data: JSON response data
            search_type: Type of search ("google" or "scholar")
            
        Returns:
            List of parsed result objects
        """
        results = []
        organic_results = data.get('organic', [])
        
        if search_type == "google":
            for idx, item in enumerate(organic_results):
                try:
                    result = SerperSearchResult(
                        title=item.get('title', ''),
                        link=item.get('link', ''),
                        snippet=item.get('snippet', ''),
                        date=item.get('date'),
                        position=item.get('position', idx + 1)
                    )
                    results.append(result)
                except Exception as e:
                    logger.debug(f"Error parsing Google search result: {str(e)}")
                    continue
        
        elif search_type == "scholar":
            for idx, item in enumerate(organic_results):
                try:
                    # Extract citation count from citedBy field
                    cited_by = None
                    if 'citedBy' in item:
                        cited_by = item['citedBy']
                    
                    result = SerperScholarResult(
                        title=item.get('title', ''),
                        link=item.get('link', ''),
                        snippet=item.get('snippet', ''),
                        publication=item.get('publication'),
                        cited_by=cited_by,
                        year=item.get('year'),
                        position=item.get('position', idx + 1)
                    )
                    results.append(result)
                except Exception as e:
                    logger.debug(f"Error parsing Scholar result: {str(e)}")
                    continue
        
        return results
    
    def is_available(self) -> bool:
        """
        Check if Serper API service is available
        
        Returns:
            True if service is available, False otherwise
        """
        try:
            # Make a simple test request
            test_query = "test"
            endpoint = f"{self.base_url}/search"
            
            response = requests.post(
                endpoint,
                json={"q": test_query, "num": 1},
                headers={
                    "X-API-KEY": self.api_key,
                    "Content-Type": "application/json"
                },
                timeout=10
            )
            
            # Service is available if we get any valid response (even rate limit or auth error)
            # Only network/connection errors indicate unavailability
            is_available = response.status_code in [200, 401, 402, 403, 429]
            
            if is_available:
                logger.info("Serper API service is available")
            else:
                logger.warning("Serper API service is unavailable")
            
            return is_available
            
        except requests.RequestException as e:
            logger.error(f"Serper API service check failed: {str(e)}")
            return False
    
    def get_requests_made(self) -> int:
        """Get total number of requests made"""
        return self._requests_made
