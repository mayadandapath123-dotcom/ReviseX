"""Minimal, ordered SQL migrations.

Applied files are recorded in `schema_version`. Never edit an applied migration;
add a new NNNN_*.sql file instead.
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"
_NAME_RE = re.compile(r"^(\d{4})_(.+)\.sql$")


def _applied_versions(conn: sqlite3.Connection) -> set[int]:
    # Parameterised so the Postgres adapter can redirect this at the catalog;
    # sqlite_master does not exist there.
    exists = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        ("schema_version",),
    ).fetchone()
    if not exists:
        return set()
    return {int(row[0]) for row in conn.execute("SELECT version FROM schema_version").fetchall()}


def discover_migrations(directory: Path = MIGRATIONS_DIR) -> list[tuple[int, str, Path]]:
    found: list[tuple[int, str, Path]] = []
    for path in sorted(directory.glob("*.sql")):
        match = _NAME_RE.match(path.name)
        if not match:
            raise ValueError(f"Migration filename must look like 0001_name.sql: {path.name}")
        found.append((int(match.group(1)), match.group(2), path))
    versions = [v for v, _, _ in found]
    if len(set(versions)) != len(versions):
        raise ValueError("Duplicate migration version numbers detected")
    return found


def migrate(conn: sqlite3.Connection, directory: Path = MIGRATIONS_DIR) -> list[str]:
    """Apply pending migrations. Returns the names of migrations applied."""
    applied = _applied_versions(conn)
    newly_applied: list[str] = []

    for version, name, path in discover_migrations(directory):
        if version in applied:
            continue
        sql = path.read_text(encoding="utf-8")
        # NOTE: sqlite3.executescript() implicitly commits any open transaction, so
        # migrations cannot be wrapped in BEGIN/COMMIT here. Migrations are DDL-only
        # and additive, and the version row is written after a successful run, so a
        # failed migration is simply re-applied on the next start.
        conn.executescript(sql)
        conn.execute(
            "INSERT INTO schema_version (version, name) VALUES (?, ?)",
            (version, name),
        )
        newly_applied.append(f"{version:04d}_{name}")

    return newly_applied
