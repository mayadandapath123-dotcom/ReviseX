"""Mistake book endpoints."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from app.api.deps import ProfileId, get_progress_service
from app.services.progress_service import ProgressService

router = APIRouter(prefix="/mistakes", tags=["mistakes"])

Progress = Annotated[ProgressService, Depends(get_progress_service)]


@router.get("")
def list_mistakes(
    progress: Progress,
    profile_id: ProfileId,
    branch: str | None = None,
    chapter: str | None = None,
    resolved: bool | None = Query(default=False),
    limit: int = Query(default=100, ge=1, le=500),
) -> dict[str, Any]:
    return {
        "mistakes": progress.mistake_list(profile_id, branch=branch, chapter=chapter, resolved=resolved, limit=limit),
        "stats": progress.mistake_stats(profile_id),
    }


@router.get("/stats")
def mistake_stats(progress: Progress, profile_id: ProfileId) -> dict[str, Any]:
    return progress.mistake_stats(profile_id)
