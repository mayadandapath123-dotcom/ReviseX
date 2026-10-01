"""FastAPI dependencies.

A SQLite connection is opened per request (cheap) so requests running on
different threads never share cursor state. Services are constructed per
request from that connection.
"""

from __future__ import annotations

import sqlite3
from typing import Annotated, Any, Iterator

from fastapi import Depends, Header, HTTPException

from app.db.connection import connect
from app.services.auth_service import AuthService
from app.services.content_service import ContentService
from app.services.admin_service import AdminService
from app.services.friend_service import FriendService
from app.services.google_auth_service import GoogleAuthService
from app.services.leaderboard_service import LeaderboardService
from app.services.profile_service import ProfileService
from app.services.progress_service import ProgressService
from app.services.quiz_engine import QuizEngine
from app.services.recommendation_engine import RecommendationEngine


def get_conn() -> Iterator[sqlite3.Connection]:
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()


Conn = Annotated[sqlite3.Connection, Depends(get_conn)]


def get_profile_service(conn: Conn) -> ProfileService:
    return ProfileService(conn)


def get_auth_service(conn: Conn) -> AuthService:
    return AuthService(conn)


def get_friend_service(conn: Conn) -> FriendService:
    return FriendService(conn)


def get_admin_service(conn: Conn) -> AdminService:
    return AdminService(conn)


def get_google_auth_service(
    conn: Conn, auth: Annotated[AuthService, Depends(get_auth_service)]
) -> GoogleAuthService:
    return GoogleAuthService(conn, auth)


def get_progress_service(conn: Conn) -> ProgressService:
    return ProgressService(conn)


def get_content_service(conn: Conn) -> ContentService:
    return ContentService(conn)


def get_leaderboard_service(conn: Conn) -> LeaderboardService:
    return LeaderboardService(conn)


def get_recommender(conn: Conn) -> RecommendationEngine:
    return RecommendationEngine(conn)


def get_quiz_engine(
    conn: Conn,
    progress: Annotated[ProgressService, Depends(get_progress_service)],
    recommender: Annotated[RecommendationEngine, Depends(get_recommender)],
) -> QuizEngine:
    return QuizEngine(conn, progress, recommender)


def get_ai_service(conn: Conn):
    from app.ai.service import AIService

    return AIService(conn)


def _bearer(authorization: str | None) -> str | None:
    if not authorization:
        return None
    token = authorization.removeprefix("Bearer ").strip()
    return token or None


def _resolve_profile(
    profiles: ProfileService,
    x_profile_id: str | None,
    auth: AuthService | None = None,
    authorization: str | None = None,
) -> str | None:
    """Work out whose data this request touches.

    A signed-in user always wins: their token maps to exactly one profile, so a
    caller cannot reach someone else's data by editing a header. That is the
    whole point of accounts. The X-Profile-Id path survives only for a local,
    account-free install where there is no token to present.
    """
    token = _bearer(authorization)
    if token:
        if auth is None:
            raise HTTPException(status_code=500, detail="Auth is not available on this route.")
        user = auth.user_from_token(token)
        if user is None:
            raise HTTPException(status_code=401, detail="Not signed in, or the session expired.")
        # Presence for the admin panel. Throttled inside to one write per user
        # per minute, so it does not add a round trip to every request.
        try:
            from app.services.admin_service import touch_presence

            touch_presence(auth.conn, user["id"])
        except Exception:
            # Presence is telemetry, never a reason to fail a student's request.
            pass

        profile = auth.profile_for_user(user["id"])
        if profile is None:
            raise HTTPException(status_code=409, detail="This account has no profile yet.")
        return profile["id"]

    if x_profile_id:
        if profiles.get(x_profile_id) is None:
            raise HTTPException(status_code=404, detail=f"Unknown profile: {x_profile_id}")
        return x_profile_id
    active = profiles.active()
    return active["id"] if active else None


def require_optional_profile(
    profiles: Annotated[ProfileService, Depends(get_profile_service)],
    auth: Annotated[AuthService, Depends(get_auth_service)],
    x_profile_id: Annotated[str | None, Header(alias="X-Profile-Id")] = None,
    authorization: Annotated[str | None, Header()] = None,
) -> str | None:
    """For read-only endpoints that show progress when a profile exists."""
    try:
        return _resolve_profile(profiles, x_profile_id, auth, authorization)
    except HTTPException as exc:
        # A read-only route degrades to "no progress" rather than failing hard
        # when the only problem is an expired token.
        return None if exc.status_code in (401, 404, 409) else None


def require_user(
    auth: Annotated[AuthService, Depends(get_auth_service)],
    authorization: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    """The signed-in user, or 401.

    Used by routes that are meaningless without an account - friends being the
    obvious one. There is no header fallback here on purpose: a local,
    account-free install has no users, so these routes should simply say so
    rather than silently acting as an anonymous profile.
    """
    user = auth.user_from_token(_bearer(authorization))
    if user is None:
        raise HTTPException(
            status_code=401, detail="Sign in to use this feature."
        )
    try:
        from app.services.admin_service import touch_presence

        touch_presence(auth.conn, user["id"])
    except Exception:
        pass
    return user


def require_profile(
    profiles: Annotated[ProfileService, Depends(get_profile_service)],
    auth: Annotated[AuthService, Depends(get_auth_service)],
    x_profile_id: Annotated[str | None, Header(alias="X-Profile-Id")] = None,
    authorization: Annotated[str | None, Header()] = None,
) -> str:
    """For endpoints that must write progress."""
    profile_id = _resolve_profile(profiles, x_profile_id, auth, authorization)
    if profile_id is None:
        raise HTTPException(status_code=409, detail="No profile selected. Create or activate one first.")
    return profile_id


ProfileId = Annotated[str, Depends(require_profile)]
OptionalProfileId = Annotated[str | None, Depends(require_optional_profile)]
