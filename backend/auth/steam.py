"""
Steam OAuth2 provider implementation.

Handles Steam OpenID login and token exchange.
"""
import os
import httpx
from typing import Optional, Tuple
import xml.etree.ElementTree as ET
import re
from urllib.parse import urlencode, parse_qs, urlparse

STEAM_OPENID_URL = "https://steamcommunity.com/openid/login"
STEAM_API_KEY = os.getenv("STEAM_API_KEY")
STEAM_API_URL = "https://api.steampowered.com"
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


class SteamProvider:
    """Steam OpenID provider for authentication."""
    
    @staticmethod
    def get_login_url() -> str:
        """
        Get Steam OpenID login URL.
        
        Returns:
            Steam login URL for redirect
        """
        params = {
            "openid.ns": "http://specs.openid.net/auth/2.0",
            "openid.mode": "checkid_setup",
            "openid.return_to": f"{BACKEND_URL}/auth/steam/callback",
            "openid.realm": BACKEND_URL,
            "openid.identity": "http://specs.openid.net/auth/2.0/identifier_select",
            "openid.claimed_id": "http://specs.openid.net/auth/2.0/identifier_select",
        }
        return f"{STEAM_OPENID_URL}?{urlencode(params)}"
    
    @staticmethod
    async def verify_callback(query_params: dict) -> Optional[str]:
        """
        Verify Steam OpenID callback and extract Steam ID.
        
        Args:
            query_params: Query parameters from Steam callback
        
        Returns:
            Steam ID if valid, None if invalid
        """
        # Prepare verification request
        verification_params = {
            "openid.ns": "http://specs.openid.net/auth/2.0",
            "openid.mode": "check_auth",
        }
        
        # Add all parameters from callback
        for key, value in query_params.items():
            if key.startswith("openid."):
                verification_params[key] = value
        
        # Verify with Steam
        async with httpx.AsyncClient() as client:
            response = await client.post(
                STEAM_OPENID_URL,
                data=verification_params,
                timeout=10
            )
        
        if response.status_code != 200 or "is_valid:true" not in response.text:
            return None
        
        # Extract Steam ID from claimed_id
        claimed_id = query_params.get("openid.claimed_id", "")
        match = re.search(r"steamid/(\d+)$", claimed_id)
        
        if match:
            return match.group(1)
        
        return None
    
    @staticmethod
    async def get_user_info(steam_id: str) -> Optional[dict]:
        """
        Get user profile information from Steam API.
        
        Args:
            steam_id: Steam ID (e.g., "76561198123456789")
        
        Returns:
            User info dict or None if error
        """
        if not STEAM_API_KEY:
            return None
        
        params = {
            "key": STEAM_API_KEY,
            "steamids": steam_id,
            "include_applist": 1,
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{STEAM_API_URL}/ISteamUser/GetPlayerSummaries/v2",
                params=params,
                timeout=10
            )
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        players = data.get("response", {}).get("players", [])
        
        if not players:
            return None
        
        player = players[0]
        return {
            "steam_id": steam_id,
            "username": player.get("personaname"),
            "avatar_url": player.get("avatarfull"),
        }
