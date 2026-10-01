"""Parity between the SQLite and Postgres backends.

This file exists because of a production outage. `for row in conn.execute(...)`
worked in every local test, because sqlite3.Cursor is iterable, and raised
`TypeError: 'PgCursor' object is not iterable` on Postgres during startup, which
took the whole app down. The Postgres facade was missing `__iter__`.

The lesson is not "fix that one line", it is that the two backends must stay
swappable, and that a gap between them is invisible until it reaches production.
So the first test below is deliberately written against the *interface*: it does
not need a database at all, it fails the moment the facades drift apart.

Run:  cd backend && python -m pytest -q
      TEST_POSTGRES_URL=postgresql://user@host/db python -m pytest -q
"""

from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.connection import PgConnection, PgCursor, Row, is_postgres  # noqa: E402


# ─────────────────── psycopg-shaped stub (no server needed) ───────────────────


class _StubDescription:
    def __init__(self, name: str):
        self.name = name


class _StubPgCursor:
    """Mimics psycopg's Cursor for the attributes PgCursor actually touches.

    Deliberately yields plain tuples and is itself the iterator, exactly as
    psycopg behaves — that shape is what PgCursor has to adapt.
    """

    def __init__(self, rows, names):
        self._rows = [tuple(r) for r in rows]
        self._names = list(names)
        self._pos = 0
        self.rowcount = len(self._rows)
        self.closed = False
        self.description = (
            [_StubDescription(n) for n in self._names] if self._names else None
        )

    def execute(self, sql, params=()):
        """psycopg cursors are executable; PgConnection calls this on them."""
        self._pos = 0
        return self

    def __iter__(self):
        return self

    def __next__(self):
        if self._pos >= len(self._rows):
            raise StopIteration
        row = self._rows[self._pos]
        self._pos += 1
        return row

    def fetchone(self):
        if self._pos >= len(self._rows):
            return None
        row = self._rows[self._pos]
        self._pos += 1
        return row

    def fetchall(self):
        rest = self._rows[self._pos:]
        self._pos = len(self._rows)
        return rest

    def close(self):
        self.closed = True


def _stub(rows=((1, "alpha"), (2, "beta")), names=("id", "name")):
    return PgCursor(_StubPgCursor(rows, names))


# ─────────────────────────── the outage regression ───────────────────────────


def test_pg_cursor_is_iterable():
    """The exact failure: iterating a PgCursor must work, as it does on SQLite."""
    rows = list(_stub())
    assert [r["id"] for r in rows] == [1, 2]
    assert [r["name"] for r in rows] == ["alpha", "beta"]


def test_sqlite_cursor_is_iterable_too():
    """Both backends agree. This is why the bug could not show up locally."""
    conn = sqlite3.connect(":memory:", isolation_level=None)
    conn.execute("CREATE TABLE t (id INTEGER, name TEXT)")
    conn.executemany("INSERT INTO t VALUES (?, ?)", [(1, "alpha"), (2, "beta")])
    assert [r[0] for r in conn.execute("SELECT id FROM t ORDER BY id")] == [1, 2]
    conn.close()


def test_iterating_a_pg_cursor_yields_row_objects():
    """Rows, not tuples: call sites use row['column'] and row[0] interchangeably."""
    row = next(iter(_stub()))
    assert isinstance(row, Row)
    assert row["id"] == 1
    assert row[0] == 1
    assert row["name"] == "alpha"
    assert row[1] == "alpha"


def test_a_statement_without_results_is_safely_empty():
    """An UPDATE has description=None; iterating it must not raise."""
    assert list(_stub(rows=[], names=[])) == []
    assert _stub(rows=[], names=[]).fetchall() == []


def test_iteration_is_consumable_only_once():
    """Matches a real cursor: it is a stream, not a list."""
    cursor = _stub()
    assert len(list(cursor)) == 2
    assert list(cursor) == []


def test_pg_cursor_offers_every_method_the_app_calls():
    """Guard against the next missing method, not just this one.

    Each entry is something the app actually does through conn.execute(...).
    If a call site starts using a new one, it belongs here.
    """
    cursor = _stub()
    for method in ("fetchone", "fetchall", "close"):
        assert callable(getattr(cursor, method)), f"PgCursor.{method} missing"

    # Iteration protocol, which is what broke.
    assert hasattr(PgCursor, "__iter__"), "PgCursor must be iterable"
    assert hasattr(PgCursor, "__next__"), "PgCursor must support next()"

    # Properties the app reads off a cursor.
    assert cursor.rowcount == 2
    assert cursor.description is not None
    assert cursor.lastrowid is None  # Postgres has no lastrowid; callers use RETURNING


def test_pg_connection_executes_and_delegates():
    """PgConnection.execute must hand back a wrapped PgCursor, not a raw one."""

    class _StubPgConn:
        """psycopg shape: .cursor() hands back a cursor you then execute on."""

        def __init__(self):
            self.autocommit = False
            self.committed = 0
            self.rolled_back = 0
            self.closed = False

        def cursor(self):
            return _StubPgCursor([(7,)], ["n"])

        def commit(self):
            self.committed += 1

        def rollback(self):
            self.rolled_back += 1

        def close(self):
            self.closed = True

    inner = _StubPgConn()
    conn = PgConnection(inner)

    assert conn.execute("SELECT 1").fetchone()["n"] == 7
    assert [r[0] for r in conn.execute("SELECT 1")] == [7]

    # The connection runs in autocommit, so commit/rollback are deliberate
    # no-ops kept only so that call sites shared with SQLite stay valid.
    assert inner.autocommit is True, "PgConnection must enable autocommit"
    conn.commit()
    conn.rollback()
    assert inner.committed == 0 and inner.rolled_back == 0

    # close() is real and delegates.
    conn.close()
    assert inner.closed is True


# ──────────────── opt-in: the real thing, when one is reachable ────────────────


TEST_POSTGRES_URL = os.environ.get("TEST_POSTGRES_URL")

postgres_only = pytest.mark.skipif(
    not TEST_POSTGRES_URL,
    reason="set TEST_POSTGRES_URL to run the Postgres integration checks",
)


@postgres_only
def test_real_postgres_cursor_iterates(tmp_path):
    """Same assertions as the stub, against a live server."""
    import psycopg

    conn = PgConnection(psycopg.connect(TEST_POSTGRES_URL, autocommit=False))
    conn.executescript("DROP TABLE IF EXISTS parity_check")
    conn.executescript("CREATE TABLE parity_check (id INTEGER, name TEXT)")
    conn.executemany(
        "INSERT INTO parity_check (id, name) VALUES (?, ?)", [(1, "alpha"), (2, "beta")]
    )
    conn.commit()

    assert [r["id"] for r in conn.execute("SELECT id, name FROM parity_check ORDER BY id")] == [1, 2]
    assert conn.execute("SELECT COUNT(*) AS n FROM parity_check").fetchone()["n"] == 2
    assert len(conn.execute("SELECT id FROM parity_check").fetchall()) == 2

    conn.executescript("DROP TABLE parity_check")
    conn.commit()
    conn.close()


@postgres_only
def test_real_postgres_seed_completes(tmp_path):
    """The end-to-end version: a full seed must run on Postgres without raising.

    This is the check that would have caught the outage before it shipped.
    """
    import psycopg

    from app.db.migrate import migrate
    from app.db.seed import seed_all

    conn = PgConnection(psycopg.connect(TEST_POSTGRES_URL, autocommit=False))
    # Migrate first. Without this the test only passes against a database that
    # some earlier command happened to leave in a migrated state, which makes it
    # fail on a fresh scratch database — exactly the case it exists to cover.
    migrate(conn)
    report = seed_all(conn, reset_content=True)

    assert report.errors == [], report.errors[:5]
    assert report.warnings == [], report.warnings[:5]

    bank = (
        report.questions_inserted
        + report.questions_updated
        + report.questions_unchanged
    )
    # The full bank, not a sample: the crash happened at the very end of the
    # seed, so a test that only checked the first rows would have missed it.
    assert bank >= 12000, f"expected the full bank, seeded {bank}"
    assert report.question_ids, "the run must report the ids it produced"

    # And it must be re-runnable: a second pass changes nothing.
    second = seed_all(conn, reset_content=True)
    assert second.errors == [], second.errors[:5]
    assert second.questions_inserted == bank
    conn.close()


def test_backend_detection_still_works(monkeypatch):
    """is_postgres() must key off the URL scheme, since it picks the facade.

    get_settings() is lru_cached, so the cache has to be dropped after each
    setenv or every assertion below reads the first value it ever saw. That
    caching is fine in production, where the environment never changes under a
    running process, and only bites in tests.
    """
    from app.config.settings import get_settings

    def reread():
        get_settings.cache_clear()

    try:
        reread()
        monkeypatch.setenv("DATABASE_URL", "postgresql://user@host/db")
        reread()
        assert is_postgres() is True

        # Neon's console sometimes hands out the postgres:// spelling.
        monkeypatch.setenv("DATABASE_URL", "postgres://user@host/db")
        reread()
        assert is_postgres() is True

        monkeypatch.setenv("DATABASE_URL", "sqlite:///tmp/x.sqlite3")
        reread()
        assert is_postgres() is False

        monkeypatch.delenv("DATABASE_URL", raising=False)
        reread()
        assert is_postgres() is False
    finally:
        reread()


# ──────────────── admin promotion must not depend on the seed ────────────────


def test_admins_are_promoted_when_content_is_unchanged(tmp_path, monkeypatch):
    """A second real bug: configuring an admin did nothing on a healthy boot.

    The admin bootstrap used to sit inside the reseed branch, which a healthy
    site skips because its content fingerprint matches. So ADMIN_USERNAMES was
    only honoured on a boot that also reseeded, and otherwise failed silently —
    every admin endpoint answered 403 with no log line, no error, and nothing to
    search for.

    This boots the app twice against SQLite: the first boot seeds, the second
    takes the content-unchanged path and must still promote.
    """
    import asyncio
    import sqlite3

    from app.config.settings import get_settings
    from app.db.connection import connect
    from app.main import create_app, lifespan

    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("DB_FILENAME", "admin_check.sqlite3")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("ADMIN_USERNAMES", raising=False)
    get_settings.cache_clear()

    def boot():
        """Run app startup to completion and hand back the app object."""

        async def go():
            app = create_app()
            cm = lifespan(app)
            await cm.__aenter__()
            await cm.__aexit__(None, None, None)
            return app

        return asyncio.run(go())

    first = boot()
    assert not first.state.seed_report.get("skipped"), "the first boot must seed"

    # A regular account, created the way the app would create one.
    conn = connect()
    conn.execute(
        """INSERT INTO users (id, username, password_hash, created_at, last_login_at, is_active, is_admin)
           VALUES (?, ?, ?, datetime('now'), NULL, 1, 0)""",
        ("u_admintest", "future_admin", "x"),
    )
    conn.commit()
    assert conn.execute(
        "SELECT is_admin FROM users WHERE username = 'future_admin'"
    ).fetchone()[0] == 0
    conn.close()

    # Now configure them as an admin and boot again. Content has not changed,
    # so this is the path that used to skip the promotion entirely.
    monkeypatch.setenv("ADMIN_USERNAMES", "future_admin")
    get_settings.cache_clear()

    second = boot()
    assert second.state.seed_report.get("skipped"), (
        "this test is only meaningful when the second boot skips the reseed"
    )

    conn = connect()
    is_admin = conn.execute(
        "SELECT is_admin FROM users WHERE username = 'future_admin'"
    ).fetchone()[0]
    conn.close()
    assert is_admin == 1, "ADMIN_USERNAMES must be honoured even when content is unchanged"

    get_settings.cache_clear()
