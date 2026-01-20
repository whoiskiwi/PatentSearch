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
