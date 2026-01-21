"""
Infringement Monitoring Router

This router handles the infringement monitoring API endpoint.
Infringement search finds patents that may infringe on your patent rights
by detecting similar claims published after your patent date.

Use case: Monitor competitors for potential patent infringement.

Endpoint: POST /api/search/infringement
"""

import time
from fastapi import APIRouter, HTTPException, Depends

from ..models import (
    InfringementSearchRequest,
    InfringementSearchResponse,
    InfringementResultItem
)
from ..dependencies import get_engine

# Create router with prefix and tags for OpenAPI documentation
router = APIRouter(prefix="/api/search", tags=["search"])


@router.post("/infringement", response_model=InfringementSearchResponse)
async def infringement_search(request: InfringementSearchRequest, engine=Depends(get_engine)):
    """
    Infringement monitoring - Find patents that may infringe your rights.

    This endpoint searches for patents that:
    1. Are semantically similar to your patent claims
    2. Were published within the specified date range
    3. Meet the minimum similarity threshold
    4. Match any specified filters (classification, keywords, title)

    The results include risk level assessment based on similarity scores:
    - Very High (>= 0.8): Strong potential infringement
    - High (>= 0.65): Significant overlap
    - Medium (>= 0.5): Moderate similarity
    - Low (< 0.5): Minor overlap

    Args:
        request: InfringementSearchRequest containing:
            - my_claims: Your patent claims to monitor
            - my_doc_number: Your patent number (excluded from results)
            - classification: IPC/CPC code prefix filter
            - keywords: Required keywords filter
            - title_search: Title substring filter
            - date_from: Only return patents after this date
            - date_to: Only return patents before this date
            - min_similarity: Minimum similarity threshold (default 0.5)
            - top_k: Maximum results to return

    Returns:
        InfringementSearchResponse containing:
            - success: Whether search succeeded
            - total: Number of results
            - results: List of potentially infringing patents with risk levels
            - search_time_ms: Search execution time

    Raises:
        HTTPException 500: If search fails
    """
    try:
        # Record start time for performance measurement
        start_time = time.perf_counter()

        # Execute the search using the engine
        results = engine.infringement_search(
            my_claims=request.my_claims,
            my_doc_number=request.my_doc_number,
            classification=request.classification,
            keywords=request.keywords,
            title_search=request.title_search,
            date_from=request.date_from,
            date_to=request.date_to,
            min_similarity=request.min_similarity,
            top_k=request.top_k
        )

        # Convert engine results to Pydantic response models
        result_items = [
            InfringementResultItem(
                doc_number=r.doc_number,
                title=r.title,
                abstract=r.abstract,
                classification=r.classification,
                publication_date=r.publication_date,
                similarity_score=r.similarity_score,
                risk_level=r.risk_level,
                matched_claims=r.matched_claims,
                overlapping_features=r.overlapping_features,
                all_claims=r.all_claims,
                detailed_description=r.detailed_description
            )
            for r in results
        ]

        # Calculate search time in milliseconds
        search_time_ms = (time.perf_counter() - start_time) * 1000

        return InfringementSearchResponse(
            success=True,
            total=len(result_items),
            results=result_items,
            search_time_ms=round(search_time_ms, 2)
        )

    except Exception as e:
        # Return 500 error with exception message
        raise HTTPException(status_code=500, detail=str(e))
