"""Health / readiness — used by the frontend to show offline state.

Also the fastest way to confirm what a deploy actually connected to, which is
why it reports the live backend rather than the configured SQLite path.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from fastapi import APIRouter

from app.api.deps import Conn
from app.config.settings import get_settings
from app.db.connection import is_postgres, query_all, query_one

router = APIRouter(tags=["health"])


def _describe_database(settings: Any) -> dict[str, Any]:
    """Identify the backend in use WITHOUT echoing the connection string.

    A Postgres URL embeds the password, and this endpoint is public and
    unauthenticated, so reporting settings.database_url would publish it. The
    host is included because "which region am I actually talking to?" is the
    question this endpoint gets asked during a deploy.
    """
    if not is_postgres():
        return {"backend": "sqlite", "location": str(settings.db_path)}

    parsed = urlparse(settings.database_url or "")
    return {
        "backend": "postgresql",
        "host": parsed.hostname or "unknown",
        "database": (parsed.path or "/").lstrip("/") or "unknown",
        "ssl": "require" if "sslmode=require" in (settings.database_url or "") else "not-required",
    }


@router.get("/health")
def health(conn: Conn) -> dict[str, Any]:
    settings = get_settings()
    row = query_one(conn, "SELECT COUNT(*) AS n FROM questions WHERE status='approved'")
    profiles = query_one(conn, "SELECT COUNT(*) AS n FROM profiles")
    users = query_one(conn, "SELECT COUNT(*) AS n FROM users")

    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
        "version": settings.client_version,
        "database": _describe_database(settings),
        "questions": int(row["n"]) if row else 0,
        "profiles": int(profiles["n"]) if profiles else 0,
        "accounts": int(users["n"]) if users else 0,
        "offline_capable": True,
    }


def _content_summary(conn: Any) -> dict[str, Any]:
    """How much approved content this server actually holds.

    The sign-in screen says what the app offers, and a number written into the
    frontend goes stale the first time content is added - it would quietly
    understate the bank, or worse overstate it. Counting here keeps the claim
    true on every deploy without anyone remembering to edit a string.
    """
    rows = query_all(
        conn,
        """SELECT s.id AS subject_id, s.name AS subject_name, COUNT(q.id) AS n
             FROM subjects s
             JOIN branches b ON b.subject_id = s.id
             JOIN chapters c ON c.branch_id = b.id
             LEFT JOIN questions q ON q.chapter_id = c.id AND q.status = 'approved'
            WHERE s.is_active = 1
            GROUP BY s.id, s.name, s.display_order
            ORDER BY s.display_order""",
    )
    per_subject = [{"subject_id": r["subject_id"], "name": r["subject_name"], "questions": int(r["n"])} for r in rows]
    return {"questions": sum(item["questions"] for item in per_subject), "subjects": per_subject}


@router.get("/config")
def public_config(conn: Conn) -> dict[str, Any]:
    """Non-secret settings the UI needs in order to render the right controls.

    Nothing here is a secret: it describes which optional features this server
    has turned on, so the interface can hide a control that would only fail
    when clicked. Credentials themselves never appear.
    """
    settings = get_settings()
    return {
        "app_name": settings.app_name,
        "google_sign_in": bool(settings.google_client_id and settings.google_client_secret),
        "allow_local_profiles": settings.allow_local_profiles,
        "max_local_profiles": settings.max_local_profiles,
        "content": _content_summary(conn),
    }
