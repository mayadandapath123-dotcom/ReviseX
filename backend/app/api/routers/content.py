"""Curriculum, chapter and test-mode endpoints."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import OptionalProfileId, get_content_service, get_quiz_engine
from app.services.content_service import ContentService
from app.services.quiz_engine import QuizEngine

router = APIRouter(prefix="/content", tags=["content"])

Content = Annotated[ContentService, Depends(get_content_service)]
Engine = Annotated[QuizEngine, Depends(get_quiz_engine)]


@router.get("/tree")
def curriculum_tree(
    content: Content,
    profile_id: OptionalProfileId,
    include_inactive: bool = Query(default=False),
    include_off_syllabus: bool = Query(default=False),
) -> dict[str, Any]:
    """Subject -> branch -> chapter -> topic, with bank size and per-profile mastery."""
    statuses = ("core", "foundation", "optional", "removed") if include_off_syllabus else ("core", "foundation", "optional")
    return {"subjects": content.tree(profile_id=profile_id, include_inactive=include_inactive, syllabus_status=statuses)}


@router.get("/chapters/{chapter_id}")
def chapter_detail(chapter_id: str, content: Content, profile_id: OptionalProfileId) -> dict[str, Any]:
    chapter = content.chapter(chapter_id, profile_id=profile_id)
    if chapter is None:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return {"chapter": chapter}


@router.get("/modes")
def list_modes(engine: Engine) -> dict[str, Any]:
    modes = engine.list_modes()
    return {
        "modes": modes,
        "groups": _group_modes(modes),
        "quick_start": [m for m in modes if m["quick_start"]],
    }


@router.get("/stats")
def bank_stats(content: Content) -> dict[str, Any]:
    return {"bank": content.bank_stats()}


def _group_modes(modes: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for mode in modes:
        grouped.setdefault(mode["group"], []).append(mode)
    return grouped
