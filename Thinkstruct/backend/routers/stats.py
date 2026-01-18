"""
Stats & Health Check Router
"""

from collections import Counter
from fastapi import APIRouter, HTTPException, Depends

from ..models import StatsResponse
from ..dependencies import get_engine

router = APIRouter(prefix="/api", tags=["stats"])


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@router.get("/stats", response_model=StatsResponse)
async def get_stats(engine=Depends(get_engine)):
    """Get patent statistics"""
    try:
        patents = engine.patents

        dates = [p["publication_date"] for p in patents if p.get("publication_date")]
        date_range = {
            "min": min(dates) if dates else None,
            "max": max(dates) if dates else None
        }

        classifications = [
            p["classification"][:4] if p.get("classification") else "OTHER"
            for p in patents
        ]
        classification_distribution = dict(Counter(classifications).most_common(10))

        return StatsResponse(
            total_patents=len(patents),
            date_range=date_range,
            classification_distribution=classification_distribution
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
