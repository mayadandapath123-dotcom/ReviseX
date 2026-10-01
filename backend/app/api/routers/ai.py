"""AI endpoints — all optional, all degrading to the local provider."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException

from app.ai.service import AIService
from app.api.deps import Conn, ProfileId, get_ai_service
from app.api.schemas.requests import GenerateRequest

router = APIRouter(prefix="/ai", tags=["ai"])

AI = Annotated[AIService, Depends(get_ai_service)]


@router.get("/status")
def status(ai: AI) -> dict[str, Any]:
    """The UI shows 'AI unavailable — core revision still works.' when this is false."""
    return ai.status()


@router.post("/generate")
def generate(payload: GenerateRequest, ai: AI) -> dict[str, Any]:
    result = ai.generate(
        chapter_id=payload.chapter_id,
        topic_id=payload.topic_id,
        count=payload.count,
        difficulty=payload.difficulty,
        extra_instructions=payload.extra_instructions,
    )
    if result.get("errors"):
        raise HTTPException(status_code=422, detail=result["errors"])
    return result


@router.get("/review-queue")
def review_queue(ai: AI) -> dict[str, Any]:
    return {"items": ai.review_queue()}


@router.get("/hints/{question_id}")
def hints(question_id: str, ai: AI) -> dict[str, Any]:
    return {"hints": ai.hints(question_id)}


@router.get("/explain/{question_id}")
def explain(question_id: str, ai: AI) -> dict[str, Any]:
    return ai.explain(question_id)


@router.get("/insights")
def insights(ai: AI, profile_id: ProfileId) -> dict[str, Any]:
    return ai.insights(profile_id)
