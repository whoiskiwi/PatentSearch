#!/usr/bin/env python3
"""
Thinkstruct Patent Search System - Backend API

This is the main entry point for the FastAPI backend service.
It configures the application, registers routers, and handles startup/shutdown.

Server runs on port 5000 by default.

Features:
- Patent semantic search (invalidity, infringement, patentability)
- Google OAuth authentication
- Search history management
- PostgreSQL/SQLite database support
- Optional Redis caching
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routers for different API endpoints
from .routers import (
    invalidity_router,
    infringement_router,
    patentability_router,
    patent_id_router,
    stats_router
)
from .routers.auth import router as auth_router
from .routers.history import router as history_router

# Import database and cache modules
from .auth.database import db
from .auth.cache import cache
from .auth.config import settings

# ============================================================================
# Logging Configuration
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Lifespan Context Manager
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.

    Startup:
        - Initialize database connection (PostgreSQL or SQLite)
        - Connect to Redis cache if enabled

    Shutdown:
        - Close database connections
        - Close Redis connection

    Args:
        app: FastAPI application instance

    Yields:
        Control to the application during its lifetime
    """
    # ==================== Startup ====================
    logger.info(f"Starting Thinkstruct API...")
    logger.info(f"Database type: {settings.database_type}")

    # Initialize database connection
    logger.info("Initializing database...")
    await db.init_db()
    logger.info("Database initialized successfully")

    # Initialize Redis cache if enabled
    if settings.redis_enabled:
        logger.info("Connecting to Redis cache...")
        await cache.connect()
    else:
        logger.info("Redis cache is disabled")

    yield  # Application runs here

    # ==================== Shutdown ====================
    logger.info("Shutting down...")
    await db.close()
    await cache.close()
    logger.info("Cleanup completed")


# ============================================================================
# FastAPI Application Configuration
# ============================================================================

app = FastAPI(
    title="Thinkstruct Patent Search API",
    description="Patent Intelligent Search System API - Semantic search for US patents",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS (Cross-Origin Resource Sharing) configuration
# Allows frontend (localhost:3000) to make requests to backend (localhost:5000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Frontend URLs
    allow_credentials=True,  # Allow cookies for authentication
    allow_methods=["*"],     # Allow all HTTP methods
    allow_headers=["*"],     # Allow all headers
)


# ============================================================================
# Register Routers
# ============================================================================

# Search API routers - each handles a specific search scenario
app.include_router(invalidity_router)      # POST /api/search/invalidity
app.include_router(infringement_router)    # POST /api/search/infringement
app.include_router(patentability_router)   # POST /api/search/patentability
app.include_router(patent_id_router)       # POST /api/search/by-patent-id
app.include_router(stats_router)           # GET /api/stats, GET /api/health

# Authentication and history routers
app.include_router(auth_router)            # /api/auth/* endpoints
app.include_router(history_router)         # /api/history/* endpoints


# ============================================================================
# Root Route
# ============================================================================

@app.get("/")
async def root():
    """
    API root endpoint.

    Returns API information and available endpoints for documentation.

    Returns:
        dict: API name, version, and endpoint listing
    """
    return {
        "name": "Thinkstruct Patent Search API",
        "version": "2.0.0",
        "endpoints": {
            "invalidity_search": "POST /api/search/invalidity",
            "infringement_search": "POST /api/search/infringement",
            "patentability_search": "POST /api/search/patentability",
            "patent_id_search": "POST /api/search/by-patent-id",
            "stats": "GET /api/stats",
            "health": "GET /api/health",
            "auth": {
                "login": "GET /api/auth/login/google",
                "callback": "GET /api/auth/callback/google",
                "me": "GET /api/auth/me",
                "logout": "POST /api/auth/logout",
                "status": "GET /api/auth/status"
            },
            "history": {
                "save": "POST /api/history",
                "list": "GET /api/history",
                "get": "GET /api/history/{id}",
                "delete": "DELETE /api/history/{id}",
                "clear": "DELETE /api/history"
            }
        }
    }


# ============================================================================
# Startup Entry Point
# ============================================================================

def start():
    """
    Start the server using uvicorn.

    This function is called when running the module directly.
    Uses hot-reload for development convenience.
    """
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=5000, reload=True)


if __name__ == "__main__":
    start()
