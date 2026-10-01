"""SpacedRepetitionService — deliberately simple, per the brief.

Schedule:
    wrong              -> re-show after a few questions in the same session; due immediately next session
    1st correct        -> +1 day
    2nd correct        -> +3 days
    3rd correct        -> +7 days
    4th and beyond     -> interval x 2.5, capped at 30 days

A full SM-2/FSRS implementation can replace `next_interval` later; the table
schema already stores `ease` and `interval_days` so no migration is needed.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any, Sequence

from app.db.connection import query_all

BASE_INTERVALS = [1.0, 3.0, 7.0]
GROWTH_FACTOR = 2.5
MAX_INTERVAL_DAYS = 30.0
MASTERED_INTERVAL_DAYS = 21.0
IN_SESSION_GAP = 4  # re-show a wrong card after this many questions


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def next_interval(repetitions: int) -> float:
    """Interval in days after `repetitions` consecutive correct answers."""
    if repetitions <= 0:
        return 0.0
    if repetitions <= len(BASE_INTERVALS):
        return BASE_INTERVALS[repetitions - 1]
    interval = BASE_INTERVALS[-1]
    for _ in range(repetitions - len(BASE_INTERVALS)):
        interval *= GROWTH_FACTOR
    return min(interval, MAX_INTERVAL_DAYS)


def update_from_attempts(conn: sqlite3.Connection, profile_id: str, attempts: Sequence[dict[str, Any]]) -> None:
    """Apply one attempt at a time, in order, so repeated cards within a session behave."""
    now = _now()

    for attempt in attempts:
        question_id = attempt.get("question_id")
        if not question_id:
            continue

        row = conn.execute(
            "SELECT state, interval_days, ease, lapses, repetitions FROM srs_cards WHERE profile_id=? AND question_id=?",
            (profile_id, question_id),
        ).fetchone()

        state = row["state"] if row else "new"
        interval = float(row["interval_days"]) if row else 0.0
        ease = float(row["ease"]) if row else 2.5
        lapses = int(row["lapses"]) if row else 0
        repetitions = int(row["repetitions"]) if row else 0

        if attempt["is_correct"]:
            repetitions += 1
            interval = next_interval(repetitions)
            state = "mastered" if interval >= MASTERED_INTERVAL_DAYS else ("review" if repetitions >= 2 else "learning")
        else:
            repetitions = 0
            lapses += 1
            interval = 0.0
            state = "learning"
            ease = max(1.3, ease - 0.2)

        conn.execute(
            """INSERT INTO srs_cards (profile_id, question_id, state, interval_days, ease, lapses, repetitions, due_at, last_reviewed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(profile_id, question_id) DO UPDATE SET
                 state=excluded.state, interval_days=excluded.interval_days, ease=excluded.ease,
                 lapses=excluded.lapses, repetitions=excluded.repetitions,
                 due_at=excluded.due_at, last_reviewed_at=excluded.last_reviewed_at""",
            (profile_id, question_id, state, interval, ease, lapses, repetitions, _iso(now + timedelta(days=interval)), _iso(now)),
        )


def due_question_ids(conn: sqlite3.Connection, profile_id: str, *, limit: int = 20) -> list[str]:
    rows = query_all(
        conn,
        """SELECT question_id FROM srs_cards
           WHERE profile_id = ? AND due_at <= ? AND state != 'mastered'
           ORDER BY due_at ASC LIMIT ?""",
        (profile_id, _iso(_now()), limit),
    )
    return [r["question_id"] for r in rows]


def due_count(conn: sqlite3.Connection, profile_id: str) -> int:
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM srs_cards WHERE profile_id = ? AND due_at <= ?",
        (profile_id, _iso(_now())),
    ).fetchone()
    return int(row["n"]) if row else 0


def stats(conn: sqlite3.Connection, profile_id: str) -> dict[str, Any]:
    rows = query_all(
        conn,
        "SELECT state, COUNT(*) AS n FROM srs_cards WHERE profile_id = ? GROUP BY state",
        (profile_id,),
    )
    return {"due": due_count(conn, profile_id), "by_state": {r["state"]: r["n"] for r in rows}}


def in_session_requeue(question_id: str, seen_count: int) -> int:
    """Index at which a wrong card should re-appear within the running session."""
    return seen_count + IN_SESSION_GAP
