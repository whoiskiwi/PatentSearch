#!/usr/bin/env python3
"""
Thinkstruct Patent Search System - Backend API
FastAPI Backend Service - Port 5000
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import (
    invalidity_router,
    infringement_router,
    patentability_router,
    stats_router
)

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ============================================================================
# FastAPI Application Configuration
# ============================================================================

app = FastAPI(
    title="Thinkstruct Patent Search API",
    description="Patent Intelligent Search System API",
    version="2.0.0"
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

app.include_router(invalidity_router)
app.include_router(infringement_router)
app.include_router(patentability_router)
app.include_router(stats_router)


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
            "stats": "GET /api/stats",
            "health": "GET /api/health"
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
