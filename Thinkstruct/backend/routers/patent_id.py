"""
Patent ID Search Router
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

router = APIRouter(prefix="/api/search", tags=["search"])


@router.post("/by-patent-id", response_model=PatentIdSearchResponse)
async def patent_id_search(request: PatentIdSearchRequest, engine=Depends(get_engine)):
    """Search similar patents using a patent ID as input"""
    try:
        start_time = time.perf_counter()

        source_patent, results = engine.search_by_patent_id(
            doc_number=request.doc_number,
            classification=request.classification,
            top_k=request.top_k
        )

        # Handle case when patent is not found
        if source_patent is None:
            return PatentIdSearchResponse(
                success=False,
                source_patent=None,
                total=0,
                results=[],
                search_time_ms=round((time.perf_counter() - start_time) * 1000, 2)
            )

        # Build source patent info
        source_info = SourcePatentInfo(
            doc_number=source_patent["doc_number"],
            title=source_patent["title"],
            abstract=source_patent["abstract"],
            classification=source_patent["classification"],
            publication_date=source_patent["publication_date"],
            claims=source_patent.get("claims", [])[:10]
        )

        # Build result items
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

        search_time_ms = (time.perf_counter() - start_time) * 1000

        return PatentIdSearchResponse(
            success=True,
            source_patent=source_info,
            total=len(result_items),
            results=result_items,
            search_time_ms=round(search_time_ms, 2)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
