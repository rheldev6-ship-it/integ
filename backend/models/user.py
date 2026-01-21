"""
Database models for Integ backend.

User, Game, Library, ProtonVersion models using SQLAlchemy ORM.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

from .config import Base


class User(Base):
    """User model - Steam/GOG profiles."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    steam_id = Column(String(50), unique=True, nullable=True, index=True)
    gog_id = Column(String(50), unique=True, nullable=True, index=True)
    
    # User info from Steam/GOG
    username = Column(String(255))
    avatar_url = Column(String(500), nullable=True)
    
    # Auth tokens
    steam_access_token = Column(String(500), nullable=True)
    gog_access_token = Column(String(500), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    games = relationship("Game", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, steam_id={self.steam_id})>"


class Game(Base):
    """Game model - Available games from Steam/GOG."""
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    
    # Game info
    provider = Column(String(20))  # "steam" or "gog"
    provider_game_id = Column(String(50), index=True)  # Steam AppID or GOG ID
    title = Column(String(255), index=True)
    description = Column(Text, nullable=True)
    icon_url = Column(String(500), nullable=True)
    
    # Game status
    is_installed = Column(Boolean, default=False)
    install_path = Column(String(500), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="games")
    
    def __repr__(self):
        return f"<Game(id={self.id}, title={self.title}, provider={self.provider})>"


class ProtonVersion(Base):
    """ProtonVersion model - Cached Proton releases."""
    __tablename__ = "proton_versions"

    id = Column(Integer, primary_key=True, index=True)
    
    # Version info
    version = Column(String(50), unique=True, index=True)  # e.g., "ge-8.26"
    download_url = Column(String(500))
    
    # Cache status
    is_cached = Column(Boolean, default=False)
    cached_path = Column(String(500), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<ProtonVersion(version={self.version}, cached={self.is_cached})>"
