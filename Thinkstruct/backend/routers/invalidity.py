"""
Invalidity Search Router

This router handles the invalidity search API endpoint.
Invalidity search finds prior art patents that were published BEFORE
a target date and are semantically similar to the query claims.

Use case: Find prior art to invalidate an existing patent.

Endpoint: POST /api/search/invalidity
"""

import time
from fastapi import APIRouter, HTTPException, Depends

from ..models import (
    InvaliditySearchRequest,
    InvaliditySearchResponse,
    InvalidityResultItem
)
from ..dependencies import get_engine

# Create router with prefix and tags for OpenAPI documentation
router = APIRouter(prefix="/api/search", tags=["search"])


@router.post("/invalidity", response_model=InvaliditySearchResponse)
async def invalidity_search(request: InvaliditySearchRequest, engine=Depends(get_engine)):
    """
    Invalidity search - Find prior art earlier than target patent.

    This endpoint searches for patents that:
    1. Are semantically similar to the query claims
    2. Were published before the target date (if specified)
    3. Match any specified classification, keywords, or title filters

    Args:
        request: InvaliditySearchRequest containing:
            - query_claims: Claims text to search for
            - query_doc_number: Optional reference document number
            - classification: IPC/CPC code prefix filter
            - keywords: Required keywords filter
            - title_search: Title substring filter
            - target_date: Only return patents before this date
            - top_k: Maximum results to return

    Returns:
        InvaliditySearchResponse containing:
            - success: Whether search succeeded
            - total: Number of results
            - results: List of matching patents with similarity scores
            - search_time_ms: Search execution time

    Raises:
        HTTPException 500: If search fails
    """
    try:
        # Record start time for performance measurement
        start_time = time.perf_counter()

        # Execute the search using the engine
        results = engine.invalidity_search(
            query_claims=request.query_claims,
            query_doc_number=request.query_doc_number,
            classification=request.classification,
            keywords=request.keywords,
            title_search=request.title_search,
            target_date=request.target_date,
            top_k=request.top_k
        )

        # Convert engine results to Pydantic response models
        result_items = [
            InvalidityResultItem(
                doc_number=r.doc_number,
                title=r.title,
                abstract=r.abstract,
                classification=r.classification,
                publication_date=r.publication_date,
                similarity_score=r.similarity_score,
                matched_claims=r.matched_claims,
                independent_claims=r.independent_claims,
                claims_count=r.claims_count,
                all_claims=r.all_claims,
                detailed_description=r.detailed_description
            )
            for r in results
        ]

        # Calculate search time in milliseconds
        search_time_ms = (time.perf_counter() - start_time) * 1000

        return InvaliditySearchResponse(
            success=True,
            total=len(result_items),
            results=result_items,
            search_time_ms=round(search_time_ms, 2)
        )

    except Exception as e:
        # Return 500 error with exception message
        raise HTTPException(status_code=500, detail=str(e))
