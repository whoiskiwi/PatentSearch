"""History router for search history management."""

from fastapi import APIRouter, Depends, HTTPException, Query

from ..auth.database import db
from ..auth.models import (
    User,
    SearchHistoryCreate,
    SearchHistoryResponse,
    SearchHistoryListResponse,
    MessageResponse,
)
from ..auth.dependencies import get_current_user

router = APIRouter(prefix="/api/history", tags=["history"])


@router.post("", response_model=SearchHistoryResponse)
async def save_search_history(
    data: SearchHistoryCreate,
    user: User = Depends(get_current_user),
):
    """Save a search to history."""
    # Validate scenario
    valid_scenarios = ["invalidity", "infringement", "patentability"]
    if data.scenario not in valid_scenarios:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid scenario. Must be one of: {', '.join(valid_scenarios)}",
        )

    history_id = await db.save_search_history(
        user_id=user.id,
        scenario=data.scenario,
        query_data=data.query_data,
        results_data=data.results_data,
        result_count=data.result_count,
        search_time_ms=data.search_time_ms,
    )

    entry = await db.get_history_entry(history_id, user.id)
    if not entry:
        raise HTTPException(status_code=500, detail="Failed to save history")

    return SearchHistoryResponse(
        id=entry["id"],
        scenario=entry["scenario"],
        query_data=entry["query_data"],
        results_data=entry.get("results_data"),
        result_count=entry["result_count"],
        search_time_ms=entry["search_time_ms"],
        created_at=entry["created_at"],
    )


@router.get("", response_model=SearchHistoryListResponse)
async def get_search_history(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
):
    """Get user's search history."""
    entries = await db.get_search_history(
        user_id=user.id,
        limit=limit,
        offset=offset,
    )

    items = [
        SearchHistoryResponse(
            id=entry["id"],
            scenario=entry["scenario"],
            query_data=entry["query_data"],
            results_data=entry.get("results_data"),
            result_count=entry["result_count"],
            search_time_ms=entry["search_time_ms"],
            created_at=entry["created_at"],
        )
        for entry in entries
    ]

    return SearchHistoryListResponse(items=items, total=len(items))


@router.get("/{history_id}", response_model=SearchHistoryResponse)
async def get_history_entry(
    history_id: int,
    user: User = Depends(get_current_user),
):
    """Get a specific history entry."""
    entry = await db.get_history_entry(history_id, user.id)
    if not entry:
        raise HTTPException(status_code=404, detail="History entry not found")

    return SearchHistoryResponse(
        id=entry["id"],
        scenario=entry["scenario"],
        query_data=entry["query_data"],
        results_data=entry.get("results_data"),
        result_count=entry["result_count"],
        search_time_ms=entry["search_time_ms"],
        created_at=entry["created_at"],
    )


@router.delete("/{history_id}", response_model=MessageResponse)
async def delete_history_entry(
    history_id: int,
    user: User = Depends(get_current_user),
):
    """Delete a specific history entry."""
    deleted = await db.delete_history_entry(history_id, user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="History entry not found")

    return MessageResponse(message="History entry deleted")


@router.delete("", response_model=MessageResponse)
async def clear_all_history(user: User = Depends(get_current_user)):
    """Clear all search history for the current user."""
    count = await db.clear_user_history(user.id)
    return MessageResponse(message=f"Cleared {count} history entries")
