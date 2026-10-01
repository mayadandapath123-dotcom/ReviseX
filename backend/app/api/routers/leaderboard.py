"""Leaderboard endpoints.

LOCAL ONLY in the MVP: profiles on the same installation, nicknames only.
The online board will live behind a separate service and will reuse these shapes
so the client does not need to change.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Query

from app.api.deps import OptionalProfileId, get_leaderboard_service
from app.services.leaderboard_service import LeaderboardService

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])

Board = Annotated[LeaderboardService, Depends(get_leaderboard_service)]
Scope = Literal["today", "week", "all"]


@router.get("/local")
def local_board(
    board: Board,
    profile_id: OptionalProfileId,
    scope: Scope = Query(default="today"),
    mode_key: str | None = None,
    limit: int = Query(default=10, ge=1, le=50),
) -> dict[str, Any]:
    entries = board.local(scope, mode_key=mode_key, limit=limit)
    return {
        "scope": scope,
        "mode_key": mode_key,
        "entries": entries,
        "you": board.personal_rank(profile_id, scope, mode_key) if profile_id else None,
        "online": False,
        "note": "Local leaderboard: compares profiles on this installation only.",
    }


@router.get("/recent")
def recent(board: Board, limit: int = Query(default=15, ge=1, le=50)) -> dict[str, Any]:
    return {"entries": board.recent_entries(limit)}
