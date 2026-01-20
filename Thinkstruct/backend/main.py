#!/usr/bin/env python3
"""
Thinkstruct Patent Search System - Backend API
FastAPI Backend Service - Port 5000
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import (
    invalidity_router,
    infringement_router,
    patentability_router,
    patent_id_router,
    stats_router
)
from .routers.auth import router as auth_router
from .routers.history import router as history_router
from .auth.database import db
from .auth.cache import cache
from .auth.config import settings

# Logging configuration
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
    """Application lifespan: startup and shutdown."""
    # Startup
    logger.info(f"Starting Thinkstruct API...")
    logger.info(f"Database type: {settings.database_type}")

    # Initialize database
    logger.info("Initializing database...")
    await db.init_db()
    logger.info("Database initialized successfully")

    # Initialize Redis cache
    if settings.redis_enabled:
        logger.info("Connecting to Redis cache...")
        await cache.connect()
    else:
        logger.info("Redis cache is disabled")

    yield

    # Shutdown
    logger.info("Shutting down...")
    await db.close()
    await cache.close()
    logger.info("Cleanup completed")


# ============================================================================
# FastAPI Application Configuration
# ============================================================================

app = FastAPI(
    title="Thinkstruct Patent Search API",
    description="Patent Intelligent Search System API",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Register Routers
# ============================================================================

# Search routers
app.include_router(invalidity_router)
app.include_router(infringement_router)
app.include_router(patentability_router)
app.include_router(patent_id_router)
app.include_router(stats_router)

# Auth and history routers
app.include_router(auth_router)
app.include_router(history_router)


# ============================================================================
# Root Route
# ============================================================================

@app.get("/")
async def root():
    """API root endpoint"""
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
# Startup Entry
# ============================================================================

def start():
    """Start the server"""
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=5000, reload=True)


if __name__ == "__main__":
    start()
