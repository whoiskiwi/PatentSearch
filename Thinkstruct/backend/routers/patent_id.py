"""
Patent ID Search Router

This router handles the patent ID search API endpoint.
Patent ID search finds patents similar to a given patent by its document number.
The system looks up the source patent and finds semantically similar patents.

Use case: Find related patents when you already know a relevant patent number.

Endpoint: POST /api/search/by-patent-id
"""

import time
from fastapi import APIRouter, HTTPException, Depends

from ..models import (
    PatentIdSearchRequest,
    PatentIdSearchResponse,
    PatentIdResultItem,
    SourcePatentInfo
)
from ..dependencies import get_engine

# Create router with prefix and tags for OpenAPI documentation
router = APIRouter(prefix="/api/search", tags=["search"])


@router.post("/by-patent-id", response_model=PatentIdSearchResponse)
async def patent_id_search(request: PatentIdSearchRequest, engine=Depends(get_engine)):
    """
    Patent ID search - Find similar patents using a patent number as input.

    This endpoint:
    1. Looks up the source patent by document number
    2. Uses the source patent's claims as the search query
    3. Finds semantically similar patents in the database
    4. Excludes the source patent from results

    This is useful when you want to find related patents based on
    an existing patent you've already identified.

    Args:
        request: PatentIdSearchRequest containing:
            - doc_number: Patent document number (e.g., "US20240217263A1")
            - classification: Optional IPC/CPC code prefix filter
            - top_k: Maximum results to return

    Returns:
        PatentIdSearchResponse containing:
            - success: Whether search succeeded (False if patent not found)
            - source_patent: Information about the query patent
            - total: Number of results
            - results: List of similar patents
            - search_time_ms: Search execution time

    Raises:
        HTTPException 500: If search fails
    """
    try:
        # Record start time for performance measurement
        start_time = time.perf_counter()

        # Execute the search using the engine
        # Returns tuple: (source_patent_dict, list_of_results)
        source_patent, results = engine.search_by_patent_id(
            doc_number=request.doc_number,
            classification=request.classification,
            top_k=request.top_k
        )

        # Handle case when patent is not found in database
        if source_patent is None:
            return PatentIdSearchResponse(
                success=False,
                source_patent=None,
                total=0,
                results=[],
                search_time_ms=round((time.perf_counter() - start_time) * 1000, 2)
            )

        # Build source patent info for the response
        source_info = SourcePatentInfo(
            doc_number=source_patent["doc_number"],
            title=source_patent["title"],
            abstract=source_patent["abstract"],
            classification=source_patent["classification"],
            publication_date=source_patent["publication_date"],
            claims=source_patent.get("claims", [])[:10]  # Limit to 10 claims
        )

        # Convert engine results to Pydantic response models
        result_items = [
            PatentIdResultItem(
                doc_number=r.doc_number,
                title=r.title,
                abstract=r.abstract,
                classification=r.classification,
                publication_date=r.publication_date,
                similarity_score=r.similarity_score,
                matched_claims=r.matched_claims,
                all_claims=r.all_claims,
                detailed_description=r.detailed_description
            )
            for r in results
        ]

        # Calculate search time in milliseconds
        search_time_ms = (time.perf_counter() - start_time) * 1000

        return PatentIdSearchResponse(
            success=True,
            source_patent=source_info,
            total=len(result_items),
            results=result_items,
            search_time_ms=round(search_time_ms, 2)
        )

    except Exception as e:
        # Return 500 error with exception message
        raise HTTPException(status_code=500, detail=str(e))
