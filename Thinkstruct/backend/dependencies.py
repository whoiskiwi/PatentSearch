"""
FastAPI Dependencies
"""

from pathlib import Path
from typing import Optional

from .services import PatentSearchEngine, get_latest_data_file

# Global search engine instance
_engine: Optional[PatentSearchEngine] = None


def get_engine() -> PatentSearchEngine:
    """Get search engine instance (lazy loading)"""
    global _engine
    if _engine is None:
        data_dir = Path(__file__).parent.parent / "data" / "cleaned_output"
        data_file = get_latest_data_file(data_dir)
        _engine = PatentSearchEngine(data_file)
    return _engine
