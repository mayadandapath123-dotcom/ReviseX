#!/usr/bin/env python3
"""Wipe every learner record (profiles, sessions, scores) and keep content.

Use this to hand the app to someone fresh, or to start your own progress over.
Run:  python scripts/reset_progress.py
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

DB = Path(__file__).resolve().parent.parent / "backend" / "data" / "revise.sqlite3"

# Order matters only for readability; FKs are deferred by disabling them below.
LEARNER_TABLES = [
    "badge_awards", "leaderboard_entries", "personal_bests", "xp_events",
    "mistakes", "attempts", "session_events", "srs_cards", "topic_mastery",
    "sessions", "profiles",
]


def main() -> int:
    if not DB.exists():
        print(f"Database not found at {DB}", file=sys.stderr)
        return 1
    if "--yes" not in sys.argv:
        ans = input(f"This deletes all learner data in {DB.name}. Continue? [y/N] ")
        if ans.strip().lower() not in {"y", "yes"}:
            print("Cancelled.")
            return 0

    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys = OFF")
    before = conn.execute("SELECT COUNT(*) FROM profiles").fetchone()[0]
    with conn:
        for table in LEARNER_TABLES:
            try:
                n = conn.execute(f"DELETE FROM {table}").rowcount
                print(f"  {table:<20} removed {n}")
            except sqlite3.OperationalError:
                pass
        for seq in conn.execute(
            "SELECT name FROM sqlite_sequence WHERE name IN (%s)"
            % ",".join("?" * len(LEARNER_TABLES)), LEARNER_TABLES
        ).fetchall():
            conn.execute("DELETE FROM sqlite_sequence WHERE name = ?", (seq[0],))
    conn.execute("VACUUM")
    conn.close()
    print(f"\nDone. {before} profile(s) removed. Content (questions/chapters) untouched.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
