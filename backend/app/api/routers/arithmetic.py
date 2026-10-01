"""Live arithmetic trainer endpoints.

These do not touch the seeded question bank. Questions are generated per
request from the chosen level and operations, then re-graded server-side so
the score cannot be inflated by editing the client.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from app.api.deps import ProfileId, get_progress_service
from app.services.arithmetic import (
    LEVELS,
    LEVEL_OPS,
    OPERATIONS,
    ArithmeticError,
    generate,
    grade,
)
from app.services.progress_service import ProgressService

router = APIRouter(prefix="/quiz/arithmetic", tags=["arithmetic"])


class GenerateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    level: str = Field(default="medium", description="easy | medium | hard")
    operations: list[str] = Field(
        default_factory=lambda: ["add", "subtract", "multiply", "divide"],
        max_length=len(OPERATIONS),
    )
    count: int = Field(default=12, ge=1, le=60)
    seed: int | None = Field(default=None, ge=0, le=2**31 - 1)


class ArithmeticAttempt(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_id: str
    selected_key: str | None = None
    response_ms: int = Field(default=0, ge=0, le=600_000)


class SubmitRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    level: str = Field(default="medium")
    operations: list[str] = Field(default_factory=lambda: ["add", "subtract", "multiply", "divide"])
    seed: int | None = Field(default=None, ge=0, le=2**31 - 1)
    attempts: list[ArithmeticAttempt] = Field(default_factory=list, max_length=60)


@router.get("/options")
def options() -> dict[str, Any]:
    """What the level picker can offer. Keeps the UI from hardcoding levels."""
    return {
        "levels": [
            {"id": level, "name": level.capitalize(), "operations": list(LEVEL_OPS[level])}
            for level in LEVELS
        ],
        "operations": [
            {"id": "add", "name": "Addition", "symbol": "+"},
            {"id": "subtract", "name": "Subtraction", "symbol": "−"},
            {"id": "multiply", "name": "Multiplication", "symbol": "×"},
            {"id": "divide", "name": "Division", "symbol": "÷"},
            {"id": "square", "name": "Squares", "symbol": "n²"},
            {"id": "percent", "name": "Percentages", "symbol": "%"},
        ],
    }


@router.post("/generate")
def generate_questions(payload: GenerateRequest, profile_id: ProfileId) -> dict[str, Any]:
    try:
        result = generate(
            level=payload.level,
            operations=tuple(payload.operations),
            count=payload.count,
            seed=payload.seed,
        )
    except ArithmeticError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    # The client echoes level/operations/seed back on submit so the server can
    # rebuild the identical paper and grade it without storing anything.
    result["replay"] = {
        "level": payload.level,
        "operations": payload.operations,
        "seed": payload.seed,
        "count": payload.count,
    }
    return result


@router.post("/submit")
def submit(
    payload: SubmitRequest,
    profile_id: ProfileId,
    progress: Annotated[ProgressService, Depends(get_progress_service)],
) -> dict[str, Any]:
    # Rebuild the same questions from the seed, then grade from scratch.
    try:
        paper = generate(
            level=payload.level,
            operations=tuple(payload.operations),
            count=max(len(payload.attempts), 1),
            seed=payload.seed,
        )
    except ArithmeticError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    summary = grade(paper["questions"], [a.model_dump() for a in payload.attempts])
    awarded = progress.award_xp(profile_id, summary["xp"], reason="arithmetic_trainer")
    summary["profile"] = awarded
    summary["level"] = paper["level"]
    return {"summary": summary}
