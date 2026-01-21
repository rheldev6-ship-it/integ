"""
Authentication API endpoints - OAuth2 callbacks and login.
"""
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional

from ..config import get_db
from ..models.user import User
from ..auth.steam import SteamProvider
from ..auth.jwt import create_access_token
from pydantic import BaseModel

router = APIRouter(tags=["authentication"])


class LoginResponse(BaseModel):
    """Response after successful login."""
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str


@router.get("/auth/steam/login")
async def steam_login():
    """
    Redirect user to Steam OpenID login.
    
    Returns:
        Redirect to Steam login URL
    """
    login_url = SteamProvider.get_login_url()
    return RedirectResponse(url=login_url)


@router.get("/auth/steam/callback")
async def steam_callback(
    request: Request,
    db: Session = Depends(get_db)
) -> LoginResponse:
    """
    Handle Steam OpenID callback.
    
    Verifies Steam ID, creates/updates user in database, and returns JWT token.
    
    Args:
        request: FastAPI request object (contains query params)
        db: Database session
    
    Returns:
        LoginResponse with access token
    
    Raises:
        HTTPException: If verification fails
    """
    # Convert query params to dict
    query_params = dict(request.query_params)
    
    # Verify callback with Steam
    steam_id = await SteamProvider.verify_callback(query_params)
    
    if not steam_id:
        raise HTTPException(status_code=401, detail="Steam verification failed")
    
    # Get user info from Steam API
    user_info = await SteamProvider.get_user_info(steam_id)
    
    if not user_info:
        raise HTTPException(status_code=500, detail="Failed to fetch Steam user info")
    
    # Check if user exists, create if not
    user = db.query(User).filter(User.steam_id == steam_id).first()
    
    if not user:
        user = User(
            steam_id=steam_id,
            username=user_info["username"],
            avatar_url=user_info["avatar_url"],
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Update user info
        user.username = user_info["username"]
        user.avatar_url = user_info["avatar_url"]
        db.commit()
    
    # Create JWT token
    access_token = create_access_token(user.id, "steam")
    
    return LoginResponse(
        access_token=access_token,
        user_id=user.id,
        username=user.username,
    )


@router.get("/auth/health")
async def auth_health():
    """Health check for auth service."""
    return {
        "status": "healthy",
        "service": "auth",
        "providers": ["steam", "gog (coming soon)"]
    }
