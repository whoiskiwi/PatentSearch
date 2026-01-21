"""
Stats & Health Check Router

This router handles system statistics and health check endpoints.

Endpoints:
- GET /api/health - Health check for load balancers/monitoring
- GET /api/stats - Patent database statistics
- GET /api/patent/{doc_number} - Get single patent by ID
"""

from collections import Counter
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from ..models import StatsResponse
from ..dependencies import get_engine

# Create router with prefix and tags
router = APIRouter(prefix="/api", tags=["stats"])


# ============================================================================
# Response Models
# ============================================================================

class PatentInfoResponse(BaseModel):
    """
    Response model for single patent lookup.

    Contains basic patent information and claims.
    """
    doc_number: str       # Patent document number
    title: str            # Patent title
    abstract: str         # Patent abstract
    classification: str   # IPC/CPC classification code
    publication_date: str # Publication date
    claims: list[str]     # Patent claims (up to 10)


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/health")
async def health_check():
    """
    Health check endpoint.

    Used by load balancers, monitoring systems, and deployment tools
    to verify the API is running and responsive.

    Returns:
        dict: {"status": "healthy"} if API is running
    """
    return {"status": "healthy"}


@router.get("/stats", response_model=StatsResponse)
async def get_stats(engine=Depends(get_engine)):
    """
    Get patent database statistics.

    Returns aggregate statistics about the patent data loaded in the system.

    Args:
        engine: PatentSearchEngine instance (injected)

    Returns:
        StatsResponse containing:
            - total_patents: Total number of patents
            - date_range: Min/max publication dates
            - classification_distribution: Top 10 classifications by count

    Raises:
        HTTPException 500: If statistics calculation fails
    """
    try:
        patents = engine.patents

        # Calculate date range from all patents
        dates = [p["publication_date"] for p in patents if p.get("publication_date")]
        date_range = {
            "min": min(dates) if dates else None,
            "max": max(dates) if dates else None
        }

        # Calculate classification distribution (top 10)
        # Use first 4 characters of classification code for grouping
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
    """
    Get a single patent by document number.

    Looks up a patent using its document number and returns its details.
    Supports flexible matching (with or without "US" prefix).

    Args:
        doc_number: Patent document number (e.g., "US20240217263A1")
        engine: PatentSearchEngine instance (injected)

    Returns:
        PatentInfoResponse with patent details

    Raises:
        HTTPException 404: If patent not found
        HTTPException 500: If lookup fails
    """
    try:
        patent = engine.get_patent_by_id(doc_number)

        if patent is None:
            raise HTTPException(
                status_code=404,
                detail=f"Patent '{doc_number}' not found"
            )

        return PatentInfoResponse(
            doc_number=patent["doc_number"],
            title=patent["title"],
            abstract=patent["abstract"],
            classification=patent["classification"],
            publication_date=patent["publication_date"],
            claims=patent.get("claims", [])[:10]  # Limit to 10 claims
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
