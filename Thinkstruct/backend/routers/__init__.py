"""
Routers Package

This package contains all FastAPI routers for the patent search API.
Each router handles a specific search scenario or functionality.

Routers:
- invalidity_router: Find prior art to invalidate patents (POST /api/search/invalidity)
- infringement_router: Monitor for patent infringement (POST /api/search/infringement)
- patentability_router: Assess invention patentability (POST /api/search/patentability)
- patent_id_router: Search by patent document number (POST /api/search/by-patent-id)
- stats_router: System statistics and health check (GET /api/stats, GET /api/health)

Usage in main.py:
    from .routers import invalidity_router, infringement_router, ...
    app.include_router(invalidity_router)
"""

from .invalidity import router as invalidity_router
from .infringement import router as infringement_router
from .patentability import router as patentability_router
from .patent_id import router as patent_id_router
from .stats import router as stats_router

__all__ = [
    'invalidity_router',
    'infringement_router',
    'patentability_router',
    'patent_id_router',
    'stats_router'
]
