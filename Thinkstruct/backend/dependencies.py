"""
FastAPI Dependencies

This module provides dependency injection for the FastAPI application.
Dependencies are functions that provide shared resources to route handlers.

Main dependency:
- get_engine(): Returns the singleton PatentSearchEngine instance

Usage in routes:
    @router.post("/search")
    async def search(engine: PatentSearchEngine = Depends(get_engine)):
        return engine.search(...)
"""

from pathlib import Path
from typing import Optional

from .services import PatentSearchEngine, get_latest_data_file

# Global search engine instance (singleton pattern)
# Initialized lazily on first request to avoid startup delay
_engine: Optional[PatentSearchEngine] = None


def get_engine() -> PatentSearchEngine:
    """
    Get the PatentSearchEngine singleton instance.

    Uses lazy loading - the engine is only created on first call.
    This avoids loading the model during application startup.

    The engine loads:
    - Patent data from the latest cleaned JSON file
    - Pre-computed embeddings from .npy file (or computes them)
    - PatentSBERTa model (on first search)

    Returns:
        PatentSearchEngine: The shared search engine instance

    Raises:
        FileNotFoundError: If no patent data file is found
    """
    global _engine

    if _engine is None:
        # Find the data directory relative to this file
        # Path: backend/dependencies.py -> backend -> Thinkstruct -> data/cleaned_output
        data_dir = Path(__file__).parent.parent / "data" / "cleaned_output"

        # Get the latest cleaned patent data file
        data_file = get_latest_data_file(data_dir)

        # Create the search engine (loads data and embeddings)
        _engine = PatentSearchEngine(data_file)

    return _engine
