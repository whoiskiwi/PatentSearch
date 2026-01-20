"""
Stats & Health Check Router
"""

from collections import Counter
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from ..models import StatsResponse
from ..dependencies import get_engine

router = APIRouter(prefix="/api", tags=["stats"])


class PatentInfoResponse(BaseModel):
    """Single patent info response"""
    doc_number: str
    title: str
    abstract: str
    classification: str
    publication_date: str
    claims: list[str]


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


@router.get("/patent/{doc_number}", response_model=PatentInfoResponse)
async def get_patent_by_id(doc_number: str, engine=Depends(get_engine)):
    """Get a single patent by document number"""
    try:
        patent = engine.get_patent_by_id(doc_number)
        if patent is None:
            raise HTTPException(status_code=404, detail=f"Patent '{doc_number}' not found")

        return PatentInfoResponse(
            doc_number=patent["doc_number"],
            title=patent["title"],
            abstract=patent["abstract"],
            classification=patent["classification"],
            publication_date=patent["publication_date"],
            claims=patent.get("claims", [])[:10]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
