"""
Patentability Review Router
"""

from fastapi import APIRouter, HTTPException, Depends

from ..models import (
    PatentabilitySearchRequest,
    PatentabilitySearchResponse,
    PatentabilityResultItem
)
from ..dependencies import get_engine

router = APIRouter(prefix="/api/search", tags=["search"])


@router.post("/patentability", response_model=PatentabilitySearchResponse)
async def patentability_search(request: PatentabilitySearchRequest, engine=Depends(get_engine)):
    """Patentability review - Evaluate patentability of new invention"""
    try:
        results = engine.patentability_search(
            invention_description=request.invention_description,
            draft_claims=request.draft_claims,
            classification=request.classification,
            keywords=request.keywords,
            top_k=request.top_k
        )

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

        return PatentabilitySearchResponse(
            success=True,
            total=len(result_items),
            results=result_items
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
