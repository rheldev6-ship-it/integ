"""
FastAPI application entry point for the Integ backend.

Initialize the application with CORS middleware, lifespan events,
and route registration.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from contextlib import asynccontextmanager

# Import database initialization
from .config import init_db
from .api import auth

# Lifespan context for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle app startup and shutdown."""
    # Startup
    print("🚀 Integ Backend starting...")
    init_db()  # Create tables if they don't exist
    print("✅ Database initialized")
    yield
    # Shutdown
    print("⛔ Integ Backend shutting down...")


# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Integ API",
    description="Unified GOG & Steam game integration platform for Linux",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware for frontend communication
allowed_origins = [
    "http://localhost:5000",
    "http://localhost:3000",
    "http://127.0.0.1:5000",
    "http://127.0.0.1:3000",
]

# Add production origins from environment if available
production_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
if production_origins and production_origins[0]:
    allowed_origins.extend(production_origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router)


@app.get("/")
async def root():
    """Root endpoint - API information."""
    return {
        "message": "Integ Backend API",
        "version": "0.1.0",
        "docs": "/docs",
        "status": "ready"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "service": "integ-backend",
        "version": "0.1.0"
    }


# TODO: Import and include routers
# from .api import auth, games, users, proton
# app.include_router(auth.router, prefix="/auth", tags=["authentication"])
# app.include_router(games.router, prefix="/games", tags=["games"])
# app.include_router(users.router, prefix="/users", tags=["users"])
# app.include_router(proton.router, prefix="/proton", tags=["proton"])


@app.exception_handler(404)
async def not_found_exception_handler(request, exc):
    """Custom 404 handler."""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "path": str(request.url.path),
            "message": "Check /docs for available endpoints"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
