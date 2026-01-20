"""
Infringement Monitoring Router
"""

import time
from fastapi import APIRouter, HTTPException, Depends

from ..models import (
    InfringementSearchRequest,
    InfringementSearchResponse,
    InfringementResultItem
)
from ..dependencies import get_engine

router = APIRouter(prefix="/api/search", tags=["search"])


@router.post("/infringement", response_model=InfringementSearchResponse)
async def infringement_search(request: InfringementSearchRequest, engine=Depends(get_engine)):
    """Infringement monitoring - Monitor new patents for potential infringement"""
    try:
        start_time = time.perf_counter()

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

        search_time_ms = (time.perf_counter() - start_time) * 1000

        return InfringementSearchResponse(
            success=True,
            total=len(result_items),
            results=result_items,
            search_time_ms=round(search_time_ms, 2)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
