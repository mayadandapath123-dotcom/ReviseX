"""LeaderboardService — local today/week/all boards.

The online board is a future, opt-in addition. This module is deliberately the
only place that shapes leaderboard payloads, so the online path can reuse the
same privacy rules: nicknames only, no email, no per-question data, opt-in flag.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any

from app.db.connection import query_all


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _week_start() -> str:
    now = datetime.now(timezone.utc)
    return (now - timedelta(days=now.weekday())).strftime("%Y-%m-%d")


class LeaderboardService:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def local(self, scope: str = "today", *, mode_key: str | None = None, limit: int = 10) -> list[dict[str, Any]]:
        """Best score per profile for the requested window."""
        if scope == "week":
            since = _week_start()
        elif scope == "all":
            since = "0000-00-00"
        else:
            since = _today()

        sql = """
            SELECT s.profile_id, p.display_name, p.level,
                   MAX(s.score) AS best_score,
                   AVG(s.accuracy) AS avg_accuracy,
                   COUNT(*) AS tests,
                   SUM(s.xp_awarded) AS xp
            FROM sessions s
            JOIN profiles p ON p.id = s.profile_id
            WHERE s.finished_at IS NOT NULL AND substr(s.started_at,1,10) >= ?
        """
        params: list[Any] = [since]
        if mode_key:
            sql += " AND s.mode_key = ?"
            params.append(mode_key)
        # p.id must be grouped too: Postgres rejects selecting p.display_name
        # under GROUP BY s.profile_id alone, because s.profile_id is not the
        # primary key of `profiles` so no functional dependency is inferred.
        # Grouping on a PK lets the rest of that table's columns through.
        sql += " GROUP BY s.profile_id, p.id ORDER BY best_score DESC LIMIT ?"
        params.append(limit)

        rows = query_all(self.conn, sql, tuple(params))
        return [
            {
                "rank": index + 1,
                "profile_id": r["profile_id"],
                "display_name": r["display_name"],
                "level": r["level"],
                "score": int(r["best_score"] or 0),
                "accuracy": float(r["avg_accuracy"] or 0.0),
                "tests": int(r["tests"] or 0),
                "xp": int(r["xp"] or 0),
            }
            for index, r in enumerate(rows)
        ]

    def personal_rank(self, profile_id: str, scope: str = "today", mode_key: str | None = None) -> dict[str, Any] | None:
        board = self.local(scope, mode_key=mode_key, limit=500)
        for entry in board:
            if entry["profile_id"] == profile_id:
                return {"rank": entry["rank"], **entry}
        return None

    def recent_entries(self, limit: int = 15) -> list[dict[str, Any]]:
        rows = query_all(
            self.conn,
            """SELECT e.display_name, e.mode_key, e.score, e.accuracy, e.xp_delta, e.created_at,
                      tm.name AS mode_name
               FROM leaderboard_entries e LEFT JOIN test_modes tm ON tm.key = e.mode_key
               WHERE e.scope = 'local_today'
               ORDER BY e.created_at DESC LIMIT ?""",
            (limit,),
        )
        return [
            {
                "display_name": r["display_name"],
                "mode_key": r["mode_key"],
                "mode_name": r["mode_name"] or r["mode_key"],
                "score": r["score"],
                "accuracy": r["accuracy"],
                "xp": r["xp_delta"],
                "created_at": r["created_at"],
            }
            for r in rows
        ]
