"""
Configuration and database setup for the Integ backend.

Uses SQLAlchemy with SQLite for development, PostgreSQL for production.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool
import os

# Database URL from environment (.env) or default to SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./integ.db")

# SQLAlchemy engine configuration
if DATABASE_URL.startswith("sqlite"):
    # SQLite for development - use StaticPool for in-memory usage
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
        poolclass=StaticPool if "sqlite" in DATABASE_URL else None,
    )
else:
    # PostgreSQL for production
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=20,
        max_overflow=10,
    )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ORM models
Base = declarative_base()


def get_db():
    """Dependency for FastAPI to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Create all tables on startup (development only)
def init_db():
    """Initialize database tables. Call on app startup."""
    Base.metadata.create_all(bind=engine)
