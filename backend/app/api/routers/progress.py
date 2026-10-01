"""Progress endpoints — dashboard, mastery, personal bests, badges, history."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from app.api.deps import (
    Conn,
    ProfileId,
    get_content_service,
    get_progress_service,
    get_recommender,
)
from app.services import spaced_repetition_service as srs
from app.services.content_service import ContentService
from app.services.progress_service import ProgressService, level_info
from app.services.recommendation_engine import RecommendationEngine

router = APIRouter(prefix="/progress", tags=["progress"])

Progress = Annotated[ProgressService, Depends(get_progress_service)]
Content = Annotated[ContentService, Depends(get_content_service)]
Recommender = Annotated[RecommendationEngine, Depends(get_recommender)]


@router.get("/dashboard")
def dashboard(
    conn: Conn,
    progress: Progress,
    recommender: Recommender,
    profile_id: ProfileId,
) -> dict[str, Any]:
    """One call for the whole dashboard: today, lifetime, level, continue, weak topics."""
    xp = progress.lifetime_stats(profile_id)
    return {
        "today": progress.today_stats(profile_id),
        "lifetime": xp,
        "level": level_info(xp["xp_total"]),
        "day_streak": xp["day_streak"],
        "srs": srs.stats(conn, profile_id),
        "suggestions": recommender.suggestions(profile_id),
        "recent_sessions": progress.recent_sessions(profile_id, limit=5),
        "mistakes": progress.mistake_stats(profile_id),
    }


@router.get("/mastery")
def mastery(progress: Progress, profile_id: ProfileId, branch: str | None = None, chapter: str | None = None) -> dict[str, Any]:
    return {"topics": progress.mastery_overview(profile_id, branch=branch, chapter=chapter)}


@router.get("/chapters")
def chapters(progress: Progress, profile_id: ProfileId, branch: str | None = None) -> dict[str, Any]:
    return {"chapters": progress.chapter_progress(profile_id, branch)}


@router.get("/bests")
def bests(progress: Progress, profile_id: ProfileId) -> dict[str, Any]:
    return {"personal_bests": progress.personal_bests(profile_id)}


@router.get("/badges")
def badges(progress: Progress, profile_id: ProfileId) -> dict[str, Any]:
    return {"badges": progress.badge_status(profile_id)}


@router.get("/sessions")
def sessions(progress: Progress, profile_id: ProfileId, limit: int = Query(default=20, ge=1, le=100)) -> dict[str, Any]:
    return {"sessions": progress.recent_sessions(profile_id, limit)}


@router.get("/xp")
def xp_history(progress: Progress, profile_id: ProfileId, days: int = Query(default=14, ge=1, le=90)) -> dict[str, Any]:
    return {"history": progress.xp_history(profile_id, days)}


@router.get("/suggestions")
def suggestions(recommender: Recommender, profile_id: ProfileId) -> dict[str, Any]:
    return recommender.suggestions(profile_id)
