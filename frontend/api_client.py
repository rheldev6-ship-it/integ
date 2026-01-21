"""
HTTP client for communicating with the Integ backend API.
Handles OAuth2, authentication, and API requests.
"""
import httpx
import os
from typing import Optional, Dict, Any


class IntegAPIClient:
    """Main API client for backend communication."""
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize API client.
        
        Args:
            base_url: Backend URL (default from .env BACKEND_URL)
        """
        self.base_url = base_url or os.getenv("BACKEND_URL", "http://localhost:8000")
        self.client = httpx.AsyncClient(base_url=self.base_url)
        self.access_token: Optional[str] = None
    
    async def health_check(self) -> Dict[str, Any]:
        """Check backend health."""
        response = await self.client.get("/health")
        return response.json()
    
    # TODO: Add OAuth2, games, users endpoints
    # - steam_login()
    # - gog_login()
    # - get_steam_library()
    # - get_gog_library()
    # - download_game()
    # - launch_game()
