"""Database connections — SQLite locally, Postgres (Neon) in production.

The whole app talks to the database through five functions in this module, so
the SQLite/Postgres dialect gap is closed here rather than at 145 call sites.
Set DATABASE_URL to a postgresql:// string to switch backends; leave it unset
and the app uses the local SQLite file exactly as before.

What the adapter has to reconcile:
  * placeholders      SQLite `?`            -> Postgres `%s`
  * literal percent   SQLite `%`            -> Postgres `%%`
  * now               datetime('now')       -> NOW()
  * today             date('now')           -> CURRENT_DATE
  * upsert-ish        INSERT OR IGNORE      -> ON CONFLICT DO NOTHING
  * locking           BEGIN IMMEDIATE       -> BEGIN
  * pragmas           PRAGMA x = y          -> ignored (Postgres has no equivalent
                                               and always enforces foreign keys)
  * identity          INTEGER PRIMARY KEY AUTOINCREMENT -> BIGSERIAL PRIMARY KEY
  * booleans          Python True/False     -> 1/0, because the columns are INTEGER
  * decimals          Postgres AVG() returns Decimal -> float, matching SQLite

The last two are the silent killers: they do not raise, they just produce wrong
types that break arithmetic or JSON serialisation further up the stack.
"""

from __future__ import annotations

import re
import sqlite3
from contextlib import contextmanager
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterator, Sequence

from app.config.settings import get_settings

# --------------------------------------------------------------------------
# Backend detection
# --------------------------------------------------------------------------


def database_url() -> str | None:
    """A postgresql:// URL means Postgres; anything else (or unset) means SQLite."""
    url = get_settings().database_url
    if not url:
        return None
    url = url.strip()
    if url.startswith(("postgresql://", "postgres://")):
        # Neon hands out postgres:// in some consoles; psycopg wants postgresql://
        return url.replace("postgres://", "postgresql://", 1)
    return None


def is_postgres() -> bool:
    return database_url() is not None


# --------------------------------------------------------------------------
# SQL translation
# --------------------------------------------------------------------------

_PRAGMA_RE = re.compile(r"^\s*PRAGMA\b[^;]*;?\s*$", re.IGNORECASE)
# The timestamp columns are declared TEXT and the app compares them as strings,
# so Postgres must emit the exact format SQLite's datetime('now') produces
# ('YYYY-MM-DD HH:MM:SS', UTC, no timezone suffix, no microseconds). Casting
# NOW() to text instead would yield '2026-09-30 08:10:20.776+00' and every
# string comparison against those columns would silently misbehave.
_PG_TIMESTAMP = "to_char(NOW() AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS')"
_PG_DATE = "to_char(NOW() AT TIME ZONE 'UTC', 'YYYY-MM-DD')"
_DATETIME_NOW_RE = re.compile(r"datetime\(\s*'now'\s*\)", re.IGNORECASE)
_DATE_NOW_RE = re.compile(r"\bdate\(\s*'now'\s*\)", re.IGNORECASE)
_INSERT_OR_IGNORE_RE = re.compile(r"\bINSERT\s+OR\s+IGNORE\s+INTO\b", re.IGNORECASE)
_AUTOINCREMENT_RE = re.compile(
    r"\bINTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT\b", re.IGNORECASE
)
_SQLITE_MASTER_RE = re.compile(
    r"SELECT\s+name\s+FROM\s+sqlite_master\s+WHERE\s+type='table'\s+AND\s+name=(\?)",
    re.IGNORECASE,
)


def translate(sql: str, *, ddl: bool = False) -> str:
    """Rewrite a SQLite statement into its Postgres equivalent."""
    stripped = sql.strip()

    if _PRAGMA_RE.match(stripped):
        return ""  # no-op; the caller skips empty statements

    if _SQLITE_MASTER_RE.search(stripped):
        # migrate.py asks "does this table exist?" — answer it from the catalog.
        return (
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_name = %s"
        )

    out = stripped
    out = _DATETIME_NOW_RE.sub(_PG_TIMESTAMP, out)
    out = _DATE_NOW_RE.sub(_PG_DATE, out)

    if out.upper().startswith("BEGIN IMMEDIATE"):
        out = "BEGIN"

    # Trailing semicolons are fine for a single statement, but psycopg rejects
    # them when parameters are bound.
    if out.endswith(";") and "%s" not in out and "?" not in out:
        out = out[:-1]

    # Escape literal % BEFORE introducing %s, otherwise LIKE '%x%' becomes a
    # malformed placeholder.
    out = out.replace("%", "%%")
    out = out.replace("?", "%s")
    # The escape above also hit any %s we just created; undo that doubling.
    out = out.replace("%%s", "%s")

    if ddl:
        out = _AUTOINCREMENT_RE.sub("BIGSERIAL PRIMARY KEY", out)
        # Postgres rejects a parenthesised expression in DEFAULT for a TEXT column.
        out = re.sub(r"DEFAULT\s*\(\s*(to_char\([^)]*\)[^)]*\))\s*\)", r"DEFAULT \1", out)

    if _INSERT_OR_IGNORE_RE.search(out):
        out = _INSERT_OR_IGNORE_RE.sub("INSERT INTO", out)
        if "ON CONFLICT" not in out.upper():
            out = out.rstrip().rstrip(";") + " ON CONFLICT DO NOTHING"

    return out


def adapt_params(params: Sequence[Any]) -> tuple[Any, ...]:
    """Normalise bound values for Postgres.

    Booleans become 1/0 because every flag column is declared INTEGER, matching
    the SQLite schema. Postgres would otherwise reject a bool against INTEGER.
    """
    out = []
    for value in params:
        if isinstance(value, bool):
            out.append(1 if value else 0)
        elif isinstance(value, Path):
            out.append(str(value))
        else:
            out.append(value)
    return tuple(out)


# --------------------------------------------------------------------------
# Row object: supports both row["column"] and row[0]
# --------------------------------------------------------------------------


class Row:
    """Dict-and-index accessible row, mirroring sqlite3.Row's behaviour."""

    __slots__ = ("_values", "_index")

    def __init__(self, values: Sequence[Any], names: Sequence[str]):
        self._values = [float(v) if isinstance(v, Decimal) else v for v in values]
        self._index = {name: i for i, name in enumerate(names)}

    def __getitem__(self, key: Any) -> Any:
        if isinstance(key, int):
            return self._values[key]
        return self._values[self._index[key]]

    def get(self, key: str, default: Any = None) -> Any:
        i = self._index.get(key)
        return default if i is None else self._values[i]

    def keys(self) -> list[str]:
        return list(self._index)

    def __contains__(self, key: str) -> bool:
        return key in self._index

    def __iter__(self) -> Iterator[Any]:
        return iter(self._values)

    def __len__(self) -> int:
        return len(self._values)

    def __repr__(self) -> str:
        return f"Row({dict(zip(self._index, self._values))!r})"


# --------------------------------------------------------------------------
# Postgres connection wrapper
# --------------------------------------------------------------------------


class PgCursor:
    """Minimal cursor facade so `conn.execute(...).fetchone()` keeps working.

    This must stay a drop-in for sqlite3.Cursor, because the same call sites run
    against both backends. A missing dunder therefore fails only in production:
    sqlite3.Cursor is iterable, so `for row in conn.execute(...)` works locally
    and raises TypeError on Postgres, at startup, where it takes the whole app
    down. That is exactly what happened with __iter__.
    """

    def __init__(self, cursor: Any):
        self._cursor = cursor

    def __iter__(self) -> Iterator[Row]:
        """Yield rows like sqlite3.Cursor does.

        psycopg cursors are not iterable in the way this codebase assumes, so
        the conversion to Row happens here instead of at every call site.
        """
        if self._cursor.description is None:
            return
        names = [d.name for d in self._cursor.description]
        for raw in self._cursor:
            yield Row(raw, names)

    def __next__(self) -> Row:
        raw = self._cursor.__next__()
        return Row(raw, [d.name for d in self._cursor.description])

    @property
    def rowcount(self) -> int:
        return self._cursor.rowcount

    @property
    def description(self) -> Any:
        return self._cursor.description

    @property
    def lastrowid(self) -> int | None:
        # Postgres has no lastrowid; callers needing an id use RETURNING.
        return None

    def fetchone(self) -> Row | None:
        raw = self._cursor.fetchone()
        if raw is None:
            return None
        return Row(raw, [d.name for d in self._cursor.description])

    def fetchall(self) -> list[Row]:
        if self._cursor.description is None:
            return []
        names = [d.name for d in self._cursor.description]
        return [Row(raw, names) for raw in self._cursor.fetchall()]

    def close(self) -> None:
        self._cursor.close()


class PgConnection:
    """Exposes the slice of sqlite3.Connection this app actually uses."""

    def __init__(self, conn: Any):
        self._conn = conn
        # Autocommit off: the app opens explicit transactions where it needs
        # them and commits elsewhere, mirroring the SQLite isolation_level=None
        # behaviour closely enough for a single-writer workload.
        self._conn.autocommit = True

    def execute(self, sql: str, params: Sequence[Any] = ()) -> PgCursor:
        statement = translate(sql)
        if not statement:
            return _NullCursor()
        cursor = self._conn.cursor()
        cursor.execute(statement, adapt_params(params))
        return PgCursor(cursor)

    def executemany(self, sql: str, seq_params: Sequence[Sequence[Any]]) -> PgCursor:
        """Run one statement against many parameter sets.

        Delegates to psycopg's own executemany rather than looping in Python.
        That matters more than it looks: psycopg3 pipelines the whole batch into
        a single network conversation, so N rows cost roughly one round trip
        instead of N. Against a remote database at ~180 ms of latency, seeding
        the question bank is the difference between minutes and hours.
        """
        rows = [adapt_params(p) for p in seq_params]
        cursor = self._conn.cursor()
        if rows:
            cursor.executemany(translate(sql), rows)
        return PgCursor(cursor)

    def executescript(self, script: str) -> None:
        for statement in split_statements(script):
            translated = translate(statement, ddl=True)
            if translated:
                self._conn.execute(translated)

    def commit(self) -> None:
        # Autocommit mode: nothing to flush, but keep the call valid.
        pass

    def rollback(self) -> None:
        pass

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "PgConnection":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()


class _NullCursor:
    """Returned for statements translated away to nothing (e.g. PRAGMA)."""

    rowcount = 0
    description = None
    lastrowid = None

    def fetchone(self) -> None:
        return None

    def fetchall(self) -> list[Any]:
        return []

    def close(self) -> None:
        pass


def split_statements(script: str) -> list[str]:
    """Split a DDL script into statements.

    Tracks single-quoted strings AND `--` line comments while scanning, because
    a semicolon inside either must not terminate a statement. Splitting on `;`
    first and stripping comments afterwards breaks badly: a comment containing
    a semicolon gets cut mid-line, the leading `--` lands on the previous
    fragment, and the tail is then executed as SQL.
    """
    statements: list[str] = []
    current: list[str] = []
    in_string = False
    in_comment = False
    i = 0
    n = len(script)
    while i < n:
        ch = script[i]
        nxt = script[i + 1] if i + 1 < n else ""

        if in_comment:
            if ch == "\n":
                in_comment = False
                current.append(ch)
            i += 1
            continue

        if in_string:
            current.append(ch)
            if ch == "'" and nxt == "'":   # escaped quote inside a literal
                current.append(nxt)
                i += 2
                continue
            if ch == "'":
                in_string = False
            i += 1
            continue

        if ch == "-" and nxt == "-":
            in_comment = True
            i += 2
            continue
        if ch == "'":
            in_string = True
            current.append(ch)
            i += 1
            continue
        if ch == ";":
            statement = "".join(current).strip()
            if statement:
                statements.append(statement)
            current = []
            i += 1
            continue

        current.append(ch)
        i += 1

    tail = "".join(current).strip()
    if tail:
        statements.append(tail)
    return statements


# --------------------------------------------------------------------------
# SQLite (unchanged behaviour)
# --------------------------------------------------------------------------


def _configure(conn: sqlite3.Connection) -> sqlite3.Connection:
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.execute("PRAGMA temp_store = MEMORY")
    conn.execute("PRAGMA cache_size = -8000")  # ~8 MB page cache
    return conn


def _connect_sqlite(db_path: Path | None) -> sqlite3.Connection:
    path = db_path or get_settings().db_path
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
    return _configure(conn)


def _connect_postgres(url: str) -> PgConnection:
    import psycopg  # imported lazily so SQLite-only installs need no driver

    conn = psycopg.connect(url, connect_timeout=15)
    return PgConnection(conn)


def connect(db_path: Path | None = None) -> Any:
    """Return a connection to whichever backend DATABASE_URL selects."""
    url = database_url()
    if url:
        return _connect_postgres(url)
    return _connect_sqlite(db_path)


@contextmanager
def transaction(conn: Any) -> Iterator[Any]:
    """Single-writer transaction. Session submit uses exactly one of these."""
    if isinstance(conn, PgConnection):
        # psycopg needs a real transaction block; BEGIN IMMEDIATE is SQLite-only.
        conn._conn.autocommit = False
        try:
            yield conn
        except Exception:
            conn._conn.rollback()
            raise
        else:
            conn._conn.commit()
        finally:
            conn._conn.autocommit = True
        return

    conn.execute("BEGIN IMMEDIATE")
    try:
        yield conn
    except Exception:
        conn.execute("ROLLBACK")
        raise
    else:
        conn.execute("COMMIT")


def query_all(conn: Any, sql: str, params: tuple = ()) -> list[Any]:
    return conn.execute(sql, params).fetchall()


def query_one(conn: Any, sql: str, params: tuple = ()) -> Any:
    return conn.execute(sql, params).fetchone()


def execute(conn: Any, sql: str, params: tuple = ()) -> Any:
    return conn.execute(sql, params)
