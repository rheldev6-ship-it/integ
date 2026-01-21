"""
JWT token generation and validation for authentication.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
import os
from jose import JWTError, jwt
from pydantic import BaseModel

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))


class TokenData(BaseModel):
    """JWT token payload."""
    user_id: int
    provider: str  # "steam" or "gog"
    exp: datetime


def create_access_token(user_id: int, provider: str, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token.
    
    Args:
        user_id: User database ID
        provider: OAuth provider ("steam" or "gog")
        expires_delta: Token expiration time (default: ACCESS_TOKEN_EXPIRE_MINUTES)
    
    Returns:
        JWT token string
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {
        "user_id": user_id,
        "provider": provider,
        "exp": expire,
    }
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_access_token(token: str) -> Optional[TokenData]:
    """
    Verify JWT token.
    
    Args:
        token: JWT token string
    
    Returns:
        TokenData if valid, None if invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        provider = payload.get("provider")
        
        if user_id is None or provider is None:
            return None
        
        return TokenData(
            user_id=user_id,
            provider=provider,
            exp=datetime.fromtimestamp(payload.get("exp"))
        )
    except JWTError:
        return None
