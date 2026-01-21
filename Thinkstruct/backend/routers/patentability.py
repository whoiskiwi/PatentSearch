"""
Patentability Review Router

This router handles the patentability review API endpoint.
Patentability search finds prior art patents that are similar to your
new invention, helping assess whether it can be patented.

Use case: Evaluate if a new invention is novel enough to patent.

Endpoint: POST /api/search/patentability
"""

import time
from fastapi import APIRouter, HTTPException, Depends

from ..models import (
    PatentabilitySearchRequest,
    PatentabilitySearchResponse,
    PatentabilityResultItem
)
from ..dependencies import get_engine

# Create router with prefix and tags for OpenAPI documentation
router = APIRouter(prefix="/api/search", tags=["search"])


@router.post("/patentability", response_model=PatentabilitySearchResponse)
async def patentability_search(request: PatentabilitySearchRequest, engine=Depends(get_engine)):
    """
    Patentability review - Assess if a new invention can be patented.

    This endpoint searches for prior art patents that:
    1. Are semantically similar to your invention description
    2. Match any specified classification, keywords, or title filters

    Results include novelty assessment based on similarity scores:
    - Novel (< 0.6): Likely patentable, low similarity to prior art
    - Similar (0.6 - 0.75): Moderate similarity, needs differentiation
    - Identical (>= 0.75): High similarity, patentability concerns

    Lower similarity scores indicate better patentability prospects.

    Args:
        request: PatentabilitySearchRequest containing:
            - invention_description: Description of your new invention
            - draft_claims: Optional draft patent claims
            - classification: Estimated IPC/CPC code filter
            - keywords: Core technical terms filter
            - title_search: Title substring filter
            - top_k: Maximum results to return

    Returns:
        PatentabilitySearchResponse containing:
            - success: Whether search succeeded
            - total: Number of results
            - results: List of prior art patents with novelty assessments
            - search_time_ms: Search execution time

    Raises:
        HTTPException 500: If search fails
    """
    try:
        # Record start time for performance measurement
        start_time = time.perf_counter()

        # Execute the search using the engine
        results = engine.patentability_search(
            invention_description=request.invention_description,
            draft_claims=request.draft_claims,
            classification=request.classification,
            keywords=request.keywords,
            title_search=request.title_search,
            top_k=request.top_k
        )

        # Convert engine results to Pydantic response models
        result_items = [
            PatentabilityResultItem(
                doc_number=r.doc_number,
                title=r.title,
                abstract=r.abstract,
                classification=r.classification,
                publication_date=r.publication_date,
                similarity_score=r.similarity_score,
                novelty_assessment=r.novelty_assessment,
                closest_prior_art=r.closest_prior_art,
                key_differences=r.key_differences,
                matched_claims=r.matched_claims,
                technical_field=r.technical_field,
                all_claims=r.all_claims,
                detailed_description=r.detailed_description
            )
            for r in results
        ]

        # Calculate search time in milliseconds
        search_time_ms = (time.perf_counter() - start_time) * 1000

        return PatentabilitySearchResponse(
            success=True,
            total=len(result_items),
            results=result_items,
            search_time_ms=round(search_time_ms, 2)
        )

    except Exception as e:
        # Return 500 error with exception message
        raise HTTPException(status_code=500, detail=str(e))
