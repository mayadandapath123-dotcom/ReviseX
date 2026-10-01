"""Quiz endpoints — start a test (one bulk fetch) and submit it (one batched write)."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import ProfileId, get_quiz_engine
from app.api.schemas.requests import StartTestRequest, SubmitSessionRequest
from app.services.quiz_engine import EmptyQuestionBank, QuizEngine, SessionNotFound, TestRequest

router = APIRouter(prefix="/quiz", tags=["quiz"])

Engine = Annotated[QuizEngine, Depends(get_quiz_engine)]


@router.post("/sessions")
def start_test(payload: StartTestRequest, engine: Engine, profile_id: ProfileId) -> dict[str, Any]:
    request = TestRequest(
        profile_id=profile_id,
        mode_key=payload.mode_key,
        subject=payload.subject,
        branch=payload.branch,
        chapter=payload.chapter,
        topic=payload.topic,
        question_types=payload.question_types,
        difficulties=payload.difficulties,
        tags=payload.tags,
        question_count=payload.question_count,
        duration_limit_ms=payload.duration_limit_ms,
        include_off_syllabus=payload.include_off_syllabus,
        prioritise_weak=payload.prioritise_weak,
        shuffle_options=payload.shuffle_options,
        seed=payload.seed,
    )
    try:
        return engine.build_test(request)
    except EmptyQuestionBank as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/sessions/{session_id}/submit")
def submit_session(session_id: str, payload: SubmitSessionRequest, engine: Engine, profile_id: ProfileId) -> dict[str, Any]:
    try:
        return engine.submit(profile_id, session_id, payload.model_dump())
    except SessionNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/sessions/{session_id}")
def get_session_result(session_id: str, engine: Engine, profile_id: ProfileId) -> dict[str, Any]:
    result = engine.progress.session_summary(profile_id, session_id)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")
    return result
