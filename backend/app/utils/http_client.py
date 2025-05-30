import asyncio
import logging
from typing import Dict, Any, Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.exceptions import (
    TomTomAPIException, 
    TomTomRateLimitException,
    TomTomServiceUnavailableException
)

logger = logging.getLogger(__name__)

class HTTPClient:
    def __init__(self, base_url: str, api_key: str, timeout: int = 30):
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
        )
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((TomTomServiceUnavailableException, httpx.TimeoutException))
    )
    async def get(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make GET request with retry logic"""
        url = f"{self.base_url}{endpoint}"
        
        # Add API key to params
        if params is None:
            params = {}
        params['key'] = self.api_key
        
        try:
            logger.info(f"Making request to: {url} with params: {params}")
            response = await self.client.get(url, params=params)
            
            # Handle different HTTP status codes
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                raise TomTomAuthenticationException(
                    "Invalid API key or authentication failed",
                    status_code=response.status_code
                )
            elif response.status_code == 429:
                raise TomTomRateLimitException(
                    "Rate limit exceeded",
                    status_code=response.status_code
                )
            elif response.status_code >= 500:
                raise TomTomServiceUnavailableException(
                    f"TomTom service unavailable: {response.status_code}",
                    status_code=response.status_code
                )
            else:
                raise TomTomAPIException(
                    f"API request failed: {response.status_code} - {response.text}",
                    status_code=response.status_code,
                    response_data=response.json() if response.content else None
                )
                
        except httpx.TimeoutException:
            logger.error(f"Timeout occurred for request to {url}")
            raise TomTomServiceUnavailableException("Request timeout")
        except httpx.RequestError as e:
            logger.error(f"Request error: {e}")
            raise TomTomAPIException(f"Request failed: {str(e)}") 