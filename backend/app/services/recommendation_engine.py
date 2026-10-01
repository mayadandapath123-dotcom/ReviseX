"""RecommendationEngine — what to revise next, and in what order.

Weighting (kept intentionally simple and explainable):
    weakness = 0.7 * (1 - mastery) + 0.2 * recency_penalty + 0.1 * error_rate

`recency_penalty` is 1.0 for a topic untouched in the last 7 days, decaying to 0.0
for one practised today. This stops the same weak topic from dominating forever
while still surfacing neglected material.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any, Sequence

from app.db.connection import query_all, query_one
from app.services.scoring_engine import confidence

WEAK_MASTERY_THRESHOLD = 0.70
STRONG_MASTERY_THRESHOLD = 0.85
MIN_ATTEMPTS_FOR_CONFIDENCE = 3
RECENCY_WINDOW_DAYS = 7


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


class RecommendationEngine:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def topic_scores(self, profile_id: str) -> list[dict[str, Any]]:
        rows = query_all(
            self.conn,
            """SELECT tm.topic_id, tm.mastery, tm.attempts, tm.correct, tm.updated_at,
                      t.name AS topic_name, c.id AS chapter_id, c.name AS chapter_name,
                      b.id AS branch_id, b.name AS branch_name
               FROM topic_mastery tm
               JOIN topics t ON t.id = tm.topic_id
               JOIN chapters c ON c.id = t.chapter_id
               JOIN branches b ON b.id = c.branch_id
               WHERE tm.profile_id = ?""",
            (profile_id,),
        )

        now = datetime.now(timezone.utc)
        scored: list[dict[str, Any]] = []

        for row in rows:
            attempts = int(row["attempts"])
            correct = int(row["correct"])
            mastery = float(row["mastery"])
            conf = confidence(attempts)

            updated = _parse_iso(row["updated_at"])
            days_since = (now - updated).days if updated else RECENCY_WINDOW_DAYS
            recency_penalty = min(1.0, max(0.0, days_since / RECENCY_WINDOW_DAYS))
            error_rate = 1.0 - (correct / attempts) if attempts else 0.0

            weakness = 0.7 * (1.0 - mastery) + 0.2 * recency_penalty + 0.1 * error_rate

            scored.append(
                {
                    "topic_id": row["topic_id"],
                    "topic_name": row["topic_name"],
                    "chapter_id": row["chapter_id"],
                    "chapter_name": row["chapter_name"],
                    "branch_id": row["branch_id"],
                    "branch_name": row["branch_name"],
                    "mastery": mastery,
                    "confidence": conf,
                    "attempts": attempts,
                    "accuracy": (correct / attempts) if attempts else 0.0,
                    "recency_penalty": round(recency_penalty, 4),
                    "weakness": round(weakness, 4),
                    "status": "unseen" if attempts == 0 else ("weak" if mastery < WEAK_MASTERY_THRESHOLD and conf >= 0.3 else "strong" if mastery >= STRONG_MASTERY_THRESHOLD else "learning"),
                }
            )

        scored.sort(key=lambda item: item["weakness"], reverse=True)
        return scored

    def reorder_by_weakness(self, profile_id: str, questions: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
        """Put weak-topic questions earlier in the set without discarding the rest."""
        scores = {item["topic_id"]: item["weakness"] for item in self.topic_scores(profile_id)}
        if not scores:
            return list(questions)

        decorated = [(scores.get(q.get("topic") or "", 0.5), index, q) for index, q in enumerate(questions)]
        decorated.sort(key=lambda entry: (-entry[0], entry[1]))
        return [q for _, _, q in decorated]

    def weak_topics(self, profile_id: str, limit: int = 6) -> list[dict[str, Any]]:
        return [
            item
            for item in self.topic_scores(profile_id)
            if item["status"] == "weak" or (item["status"] == "unseen" and item["attempts"] == 0)
        ][:limit]

    def unpractised_topics(self, profile_id: str, limit: int = 6) -> list[dict[str, Any]]:
        """Topics that exist in the bank but the student has never attempted."""
        rows = query_all(
            self.conn,
            """SELECT t.id AS topic_id, t.name AS topic_name, c.id AS chapter_id, c.name AS chapter_name,
                      b.id AS branch_id, b.name AS branch_name, COUNT(q.id) AS bank_size
               FROM topics t
               JOIN chapters c ON c.id = t.chapter_id
               JOIN branches b ON b.id = c.branch_id
               JOIN questions q ON q.topic_id = t.id AND q.status = 'approved'
               WHERE c.syllabus_status IN ('core','foundation')
                 AND t.id NOT IN (SELECT topic_id FROM topic_mastery WHERE profile_id = ?)
               -- c.id and b.id joined in: Postgres needs every non-aggregated
               -- column covered, and grouping on a table's PK covers that table.
               GROUP BY t.id, c.id, b.id
               ORDER BY b.display_order, c.display_order, t.display_order
               LIMIT ?""",
            (profile_id, limit),
        )
        return [
            {
                "topic_id": r["topic_id"],
                "topic_name": r["topic_name"],
                "chapter_id": r["chapter_id"],
                "chapter_name": r["chapter_name"],
                "branch_id": r["branch_id"],
                "branch_name": r["branch_name"],
                "bank_size": r["bank_size"],
                "status": "unseen",
            }
            for r in rows
        ]

    def continue_recommendation(self, profile_id: str) -> dict[str, Any] | None:
        """The single 'Continue' card on the dashboard: highest-value next action."""
        from app.services import spaced_repetition_service as srs_service

        due = srs_service.due_count(self.conn, profile_id)
        weak = self.weak_topics(profile_id, limit=3)
        unseen = self.unpractised_topics(profile_id, limit=3)

        if weak:
            target = weak[0]
            return {
                "kind": "weak_topic",
                "reason": f"Lowest mastery: {target['topic_name']} at {round(target['mastery'] * 100)}%",
                "label": target["topic_name"],
                "chapter_id": target["chapter_id"],
                "chapter_name": target["chapter_name"],
                "branch": target["branch_id"],
                "topic_id": target["topic_id"],
                "mastery": target["mastery"],
                "suggested_mode": "topic_test",
            }

        if unseen:
            target = unseen[0]
            return {
                "kind": "new_topic",
                "reason": f"Not practised yet: {target['topic_name']}",
                "label": target["topic_name"],
                "chapter_id": target["chapter_id"],
                "chapter_name": target["chapter_name"],
                "branch": target["branch_id"],
                "topic_id": target["topic_id"],
                "mastery": 0.0,
                "suggested_mode": "topic_test",
            }

        if due:
            return {
                "kind": "review_due",
                "reason": f"{due} item(s) due for spaced review",
                "label": "Spaced revision",
                "suggested_mode": "revision_mix",
                "mastery": None,
            }

        return None

    def suggestions(self, profile_id: str) -> dict[str, Any]:
        return {
            "continue": self.continue_recommendation(profile_id),
            "weak_topics": self.weak_topics(profile_id, limit=5),
            "unpractised": self.unpractised_topics(profile_id, limit=5),
        }
