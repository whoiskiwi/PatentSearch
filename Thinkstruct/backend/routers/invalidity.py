"""
Invalidity Search Router
"""

import time
from fastapi import APIRouter, HTTPException, Depends

from ..models import (
    InvaliditySearchRequest,
    InvaliditySearchResponse,
    InvalidityResultItem
)
from ..dependencies import get_engine

router = APIRouter(prefix="/api/search", tags=["search"])


@router.post("/invalidity", response_model=InvaliditySearchResponse)
async def invalidity_search(request: InvaliditySearchRequest, engine=Depends(get_engine)):
    """Invalidity search - Find prior art earlier than target patent"""
    try:
        start_time = time.perf_counter()

        results = engine.invalidity_search(
            query_claims=request.query_claims,
            query_doc_number=request.query_doc_number,
            classification=request.classification,
            keywords=request.keywords,
            title_search=request.title_search,
            target_date=request.target_date,
            top_k=request.top_k
        )

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

        search_time_ms = (time.perf_counter() - start_time) * 1000

        return InvaliditySearchResponse(
            success=True,
            total=len(result_items),
            results=result_items,
            search_time_ms=round(search_time_ms, 2)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
