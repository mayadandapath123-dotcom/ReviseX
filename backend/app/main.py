"""FastAPI application factory.

Startup performs: directory setup -> migrations -> idempotent content seed.
A fresh clone therefore needs no manual database step.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any
from pathlib import Path
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routers import arithmetic, admin, ai, auth, content, friends, health, leaderboard, mistakes, profiles, progress, quiz
from app.config.settings import PROJECT_ROOT, get_settings
from app.db.connection import connect, query_one
from app.db.migrate import migrate
from app.db.seed import ContentSeedError, seed_all

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(name)s: %(message)s")
logger = logging.getLogger("leap")


def content_fingerprint(settings: Any) -> str:
    """Hash everything that determines the generated question bank.

    Covers the content JSON *and* the Python that turns it into questions. The
    generators are not a pure copy - a bank of distractors or a param-set
    expansion lives in code, so hashing only the JSON would skip a reseed that
    genuinely changes output, and students would silently keep stale questions.
    """
    digest = hashlib.sha256()
    roots = [
        (settings.content_dir, "*.json"),
        (PROJECT_ROOT / "backend" / "app" / "content", "*.py"),
    ]
    for root, pattern in roots:
        root = Path(root)
        if not root.exists():
            continue
        for path in sorted(root.rglob(pattern)):
            if "__pycache__" in path.parts:
                continue
            digest.update(path.relative_to(root).as_posix().encode("utf-8"))
            digest.update(b"\0")
            digest.update(path.read_bytes())
            digest.update(b"\0")
    # The seed script itself defines how rows are written.
    for extra in ("app/db/seed.py",):
        path = PROJECT_ROOT / "backend" / extra
        if path.exists():
            digest.update(extra.encode("utf-8"))
            digest.update(path.read_bytes())
    return digest.hexdigest()


def _state_get(conn: Any, key: str) -> str | None:
    try:
        row = query_one(conn, "SELECT value FROM content_state WHERE key = ?", (key,))
    except Exception:
        return None
    return row["value"] if row else None


def _state_set(conn: Any, key: str, value: str) -> None:
    conn.execute(
        """INSERT INTO content_state (key, value, updated_at) VALUES (?, ?, datetime('now'))
           ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at""",
        (key, value),
    )
    conn.commit()


def _bootstrap_admins(conn: Any, settings: Any) -> None:
    """Promote the usernames listed in ADMIN_USERNAMES. Runs on every boot.

    Configuration-driven on purpose: the first admin cannot be promoted by an
    admin that does not exist yet.

    This must stay OUTSIDE the reseed branch. On a healthy site the content
    fingerprint matches, so that branch returns early — and while this lived
    inside it, adding a username to ADMIN_USERNAMES silently did nothing: no
    log line, no error, just a 403 from every admin endpoint on a fresh boot.
    """
    try:
        from app.services.admin_service import AdminService

        promoted = AdminService(conn).bootstrap_admins(settings.admin_username_set)
        if promoted:
            logger.info("Promoted admin account(s): %s", ", ".join(sorted(promoted)))
    except Exception:
        logger.exception("Admin bootstrap failed (continuing)")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    started = time.perf_counter()

    conn = connect()
    try:
        applied = migrate(conn)
        if applied:
            logger.info("Applied migrations: %s", ", ".join(applied))

        fingerprint = content_fingerprint(settings)
        already = query_one(conn, "SELECT COUNT(*) AS n FROM questions")
        have_questions = bool(already and int(already["n"]) > 0)

        # Skip the whole content pass when nothing that feeds it has changed.
        # The question-count guard matters: a fingerprint match on an empty
        # database (restored dump, fresh project) must still seed.
        if have_questions and _state_get(conn, "content_fingerprint") == fingerprint:
            app.state.seed_report = {"skipped": True, "reason": "content unchanged"}
            logger.info(
                "Content unchanged (fingerprint %s) - skipped reseed in %.0f ms",
                fingerprint[:12],
                (time.perf_counter() - started) * 1000,
            )
            _bootstrap_admins(conn, settings)
            yield
            return

        try:
            report = seed_all(conn)
        except ContentSeedError as exc:
            logger.error("Content seeding failed: %s", exc)
            for error in exc.report.errors[:10]:
                logger.error("  %s", error)
            raise
        except Exception:
            logger.exception("Content seeding raised an unexpected error")
            raise

        app.state.seed_report = report.as_dict()
        logger.info(
            "Content ready: %s questions (%s new, %s updated), %s facts, %s modes in %.0f ms",
            report.questions_inserted + report.questions_updated + report.questions_unchanged,
            report.questions_inserted,
            report.questions_updated,
            report.facts,
            report.modes,
            (time.perf_counter() - started) * 1000,
        )
        for warning in report.warnings[:10]:
            logger.warning("seed: %s", warning)

        # Recorded only after a successful seed, so a failed load retries next
        # boot instead of being marked done.
        _state_set(conn, "content_fingerprint", fingerprint)

        # Idempotent, and it runs on both startup paths.
        _bootstrap_admins(conn, settings)
    finally:
        conn.close()

    yield


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=f"{settings.app_name} API",
        version=settings.client_version,
        description="Class 10 rapid-revision platform. Local-first; AI optional.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "X-Profile-Id"],
    )

    @app.middleware("http")
    async def add_offline_header(request: Request, call_next):
        response = await call_next(request)
        # Hashed build assets are immutable; everything else (the quiz loop in
        # particular) must never be cached by a proxy.
        if request.url.path.startswith("/assets/"):
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        else:
            response.headers["Cache-Control"] = "no-store"
        return response

    prefix = settings.api_prefix
    app.include_router(health.router, prefix=prefix)
    app.include_router(profiles.router, prefix=prefix)
    app.include_router(content.router, prefix=prefix)
    app.include_router(quiz.router, prefix=prefix)
    app.include_router(progress.router, prefix=prefix)
    app.include_router(mistakes.router, prefix=prefix)
    app.include_router(leaderboard.router, prefix=prefix)
    app.include_router(admin.router, prefix=prefix)
    app.include_router(ai.router, prefix=prefix)
    app.include_router(arithmetic.router, prefix=prefix)
    app.include_router(auth.router, prefix=prefix)
    app.include_router(friends.router, prefix=prefix)

    # Single-origin production deploy: if the frontend has been built, serve it
    # from the API process so '/api' relative calls work with no CORS and no
    # separate static host. In dev (no dist/) the JSON root is served instead and
    # Vite handles the UI on :5173.
    dist = PROJECT_ROOT / "frontend" / "dist"
    index_html = dist / "index.html"

    if index_html.is_file():
        assets = dist / "assets"
        if assets.is_dir():
            app.mount("/assets", StaticFiles(directory=str(assets)), name="assets")

        @app.get("/{full_path:path}", include_in_schema=False)
        def spa(full_path: str):
            """Serve real files, else fall back to index.html for client routing."""
            if full_path:
                candidate = (dist / full_path).resolve()
                # Path-traversal guard: only serve files inside dist/.
                if candidate.is_file() and candidate.is_relative_to(dist.resolve()):
                    return FileResponse(candidate)
            return FileResponse(index_html)

        logger.info("Serving built frontend from %s", dist)
    else:

        @app.get("/", include_in_schema=False)
        def root() -> JSONResponse:
            return JSONResponse(
                {
                    "app": settings.app_name,
                    "status": "ok",
                    "docs": "/docs",
                    "health": f"{prefix}/health",
                    "offline_capable": True,
                    "note": "No frontend/dist build found; API only.",
                }
            )

    @app.exception_handler(Exception)
    async def unhandled(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    return app


app = create_app()
