"""ProgressService — XP, levels, mastery, mistakes, personal bests, badges.

One transaction per submitted session (driven by QuizEngine.submit) keeps all
rollups consistent: either everything lands or nothing does.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Sequence

from app.db.connection import query_all, query_one
from app.services import spaced_repetition_service as srs
from app.services.scoring_engine import SessionSummary, confidence, mastery_update

LEVEL_NAMES = [
    "Beginner",
    "Learner",
    "Quick Recall",
    "Fast Recall",
    "Chapter Master",
    "Speed Reader",
    "Revision Pro",
    "Concept Crusher",
    "Syllabus Slayer",
    "Exam Ready",
    "Top Scorer",
    "Grandmaster",
]

MISTAKES_RESOLVE_THRESHOLD = 2  # correct answers after the last mistake


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


# ───────────────────────── levels ─────────────────────────


def xp_for_level(level: int) -> int:
    """Cumulative XP required to reach `level`. Level 1 starts at 0."""
    if level <= 1:
        return 0
    return int(round(300 * ((level - 1) ** 1.6) / 10.0) * 10)


def level_for_xp(xp: int) -> int:
    level = 1
    while xp >= xp_for_level(level + 1):
        level += 1
    return level


def level_info(xp: int) -> dict[str, Any]:
    level = level_for_xp(xp)
    current = xp_for_level(level)
    next_threshold = xp_for_level(level + 1)
    span = max(1, next_threshold - current)
    return {
        "level": level,
        "name": LEVEL_NAMES[min(level - 1, len(LEVEL_NAMES) - 1)],
        "xp": xp,
        "xp_into_level": xp - current,
        "xp_for_next_level": next_threshold,
        "level_progress": round(min(1.0, (xp - current) / span), 4),
    }


class ProgressService:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    # ───────────────────────── session application ─────────────────────────

    def apply_session(
        self,
        *,
        profile_id: str,
        session_id: str,
        attempts: Sequence[dict[str, Any]],
        summary: SessionSummary,
        elapsed_ms: int,
        topic_names: dict[str, str],
        config: dict[str, Any],
    ) -> dict[str, Any]:
        events: list[dict[str, Any]] = []

        self._update_mastery(profile_id, attempts)
        self._update_mistakes(profile_id, attempts)
        srs.update_from_attempts(self.conn, profile_id, attempts)

        pb_results = self._update_personal_bests(profile_id, session_id, summary, config)
        events.extend(pb_results["events"])

        badge_results = self._award_badges(profile_id, session_id, summary, attempts)
        events.extend(badge_results)

        level_before = self._profile_level(profile_id)
        xp_awarded = summary.xp
        self._add_xp(profile_id, xp_awarded, "session", session_id)
        level_after = self._profile_level(profile_id)

        if level_after > level_before:
            self.conn.execute(
                "INSERT INTO session_events (session_id, profile_id, kind, payload_json) VALUES (?, ?, 'level_up', ?)",
                (session_id, profile_id, json.dumps({"from": level_before, "to": level_after})),
            )
            events.append({"kind": "level_up", "from": level_before, "to": level_after, "name": level_info(self._profile_xp(profile_id))["name"]})

        self._update_day_streak(profile_id)
        self._record_leaderboard(profile_id, session_id, summary, config)

        weak_strong = self._weak_and_strong(summary, topic_names)

        for event in events:
            self.conn.execute(
                "INSERT INTO session_events (session_id, profile_id, kind, payload_json) VALUES (?, ?, ?, ?)",
                (session_id, profile_id, event.get("kind", "event"), json.dumps(event, ensure_ascii=False)),
            )

        return {
            "xp_awarded": xp_awarded,
            "level": level_after,
            "level_info": level_info(self._profile_xp(profile_id)),
            "events": events,
            "personal_bests": pb_results["records"],
            "weak_areas": weak_strong["weak"],
            "strong_areas": weak_strong["strong"],
        }

    def session_summary(self, profile_id: str, session_id: str) -> dict[str, Any]:
        """Idempotent read of an already-finished session (used on duplicate submit)."""
        row = query_one(
            self.conn,
            "SELECT * FROM sessions WHERE id = ? AND profile_id = ?",
            (session_id, profile_id),
        )
        if row is None:
            return {}
        return {
            "session_id": row["id"],
            "summary": {
                "score": row["score"],
                "xp": row["xp_awarded"],
                "correct": row["correct_count"],
                "answered": row["questions_answered"],
                "accuracy": row["accuracy"] or 0.0,
                "avg_response_ms": row["avg_response_ms"] or 0.0,
                "fastest_response_ms": row["fastest_response_ms"],
                "best_streak": row["best_streak"],
            },
            "analysis": json.loads(row["summary_json"] or "{}"),
        }

    # ───────────────────────── mastery ─────────────────────────

    def _update_mastery(self, profile_id: str, attempts: Sequence[dict[str, Any]]) -> None:
        by_topic: dict[str, list[dict[str, Any]]] = {}
        for attempt in attempts:
            topic_id = attempt.get("topic_id")
            if topic_id:
                by_topic.setdefault(topic_id, []).append(attempt)

        for topic_id, group in by_topic.items():
            existing = query_one(
                self.conn,
                "SELECT mastery, attempts, correct FROM topic_mastery WHERE profile_id = ? AND topic_id = ?",
                (profile_id, topic_id),
            )
            mastery = float(existing["mastery"]) if existing else 0.5
            total = int(existing["attempts"]) if existing else 0
            correct = int(existing["correct"]) if existing else 0

            for attempt in group:
                mastery = mastery_update(mastery, bool(attempt["is_correct"]), attempt["difficulty"])
                total += 1
                correct += 1 if attempt["is_correct"] else 0

            self.conn.execute(
                """INSERT INTO topic_mastery (profile_id, topic_id, chapter_id, attempts, correct, mastery, last_result, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(profile_id, topic_id) DO UPDATE SET
                     attempts=excluded.attempts, correct=excluded.correct, mastery=excluded.mastery,
                     last_result=excluded.last_result, updated_at=excluded.updated_at""",
                (
                    profile_id,
                    topic_id,
                    group[0].get("chapter_id"),
                    total,
                    correct,
                    mastery,
                    1.0 if group[-1]["is_correct"] else 0.0,
                    _now_iso(),
                ),
            )

    def mastery_overview(self, profile_id: str, *, branch: str | None = None, chapter: str | None = None) -> list[dict[str, Any]]:
        sql = """
            SELECT tm.topic_id, t.name AS topic_name, c.id AS chapter_id, c.name AS chapter_name,
                   b.id AS branch_id, b.name AS branch_name,
                   tm.attempts, tm.correct, tm.mastery, tm.updated_at
            FROM topic_mastery tm
            JOIN topics t ON t.id = tm.topic_id
            JOIN chapters c ON c.id = t.chapter_id
            JOIN branches b ON b.id = c.branch_id
            WHERE tm.profile_id = ?
        """
        params: list[Any] = [profile_id]
        if branch:
            sql += " AND b.id = ?"
            params.append(branch)
        if chapter:
            sql += " AND c.id = ?"
            params.append(chapter)
        sql += " ORDER BY tm.mastery ASC, tm.attempts DESC"

        rows = query_all(self.conn, sql, tuple(params))
        return [
            {
                "topic_id": r["topic_id"],
                "topic_name": r["topic_name"],
                "chapter_id": r["chapter_id"],
                "chapter_name": r["chapter_name"],
                "branch_id": r["branch_id"],
                "branch_name": r["branch_name"],
                "attempts": r["attempts"],
                "correct": r["correct"],
                "accuracy": (r["correct"] / r["attempts"]) if r["attempts"] else 0.0,
                "mastery": r["mastery"],
                "confidence": confidence(r["attempts"]),
                "updated_at": r["updated_at"],
            }
            for r in rows
        ]

    def _weak_and_strong(self, summary: SessionSummary, topic_names: dict[str, str]) -> dict[str, list[dict[str, Any]]]:
        scored = [
            {
                "topic_id": topic_id,
                "name": topic_names.get(topic_id, topic_id),
                "attempts": int(values["attempts"]),
                "correct": int(values["correct"]),
                "accuracy": values.get("accuracy", 0.0),
            }
            for topic_id, values in summary.by_topic.items()
            if values["attempts"] >= 2
        ]
        scored.sort(key=lambda item: (item["accuracy"], -item["attempts"]))
        return {
            "weak": [item for item in scored if item["accuracy"] < 0.7][:4],
            "strong": [item for item in scored if item["accuracy"] >= 0.85][-4:],
        }

    # ───────────────────────── mistakes ─────────────────────────

    def _update_mistakes(self, profile_id: str, attempts: Sequence[dict[str, Any]]) -> None:
        now = _now_iso()
        for attempt in attempts:
            existing = query_one(
                self.conn,
                "SELECT id, wrong_count, correct_since_count, resolved FROM mistakes WHERE profile_id = ? AND question_id = ?",
                (profile_id, attempt["question_id"]),
            )

            if attempt["is_correct"]:
                if existing is None:
                    continue
                resolved = int(existing["resolved"])
                streak_correct = int(existing["correct_since_count"]) + 1
                if streak_correct >= MISTAKES_RESOLVE_THRESHOLD:
                    resolved = 1
                self.conn.execute(
                    "UPDATE mistakes SET correct_since_count = ?, resolved = ? WHERE id = ?",
                    (streak_correct, resolved, existing["id"]),
                )
            else:
                if existing is None:
                    self.conn.execute(
                        """INSERT INTO mistakes (profile_id, question_id, chapter_id, topic_id, question_type,
                                                 wrong_count, correct_since_count, last_wrong_at, resolved)
                             VALUES (?, ?, ?, ?, ?, 1, 0, ?, 0)""",
                        (profile_id, attempt["question_id"], attempt.get("chapter_id"), attempt.get("topic_id"),
                         attempt.get("question_type"), now),
                    )
                else:
                    self.conn.execute(
                        "UPDATE mistakes SET wrong_count = wrong_count + 1, correct_since_count = 0, resolved = 0, last_wrong_at = ? WHERE id = ?",
                        (now, existing["id"]),
                    )

    def unresolved_mistake_ids(self, profile_id: str, *, limit: int = 200) -> list[str]:
        rows = query_all(
            self.conn,
            """SELECT question_id FROM mistakes
               WHERE profile_id = ? AND resolved = 0
               ORDER BY wrong_count DESC, last_wrong_at DESC LIMIT ?""",
            (profile_id, limit),
        )
        return [r["question_id"] for r in rows]

    def mistake_list(self, profile_id: str, *, branch: str | None = None, chapter: str | None = None,
                     resolved: bool | None = False, limit: int = 100) -> list[dict[str, Any]]:
        sql = """
            SELECT m.question_id, m.wrong_count, m.correct_since_count, m.last_wrong_at, m.resolved,
                   q.prompt, q.question_type, q.difficulty, q.answer_key, q.explanation, q.stimulus_json,
                   t.name AS topic_name, c.name AS chapter_name, b.name AS branch_name, b.id AS branch_id,
                   c.id AS chapter_id, m.topic_id
            FROM mistakes m
            JOIN questions q ON q.id = m.question_id
            JOIN chapters c ON c.id = q.chapter_id
            JOIN branches b ON b.id = c.branch_id
            LEFT JOIN topics t ON t.id = q.topic_id
            WHERE m.profile_id = ?
        """
        params: list[Any] = [profile_id]
        if branch:
            sql += " AND b.id = ?"
            params.append(branch)
        if chapter:
            sql += " AND c.id = ?"
            params.append(chapter)
        if resolved is not None:
            sql += " AND m.resolved = ?"
            params.append(int(resolved))
        sql += " ORDER BY m.wrong_count DESC, m.last_wrong_at DESC LIMIT ?"
        params.append(limit)

        rows = query_all(self.conn, sql, tuple(params))
        out = []
        for r in rows:
            out.append(
                {
                    "question_id": r["question_id"],
                    "prompt": r["prompt"],
                    "question_type": r["question_type"],
                    "difficulty": r["difficulty"],
                    "answer_key": r["answer_key"],
                    "explanation": r["explanation"],
                    "stimulus": json.loads(r["stimulus_json"] or "{}"),
                    "topic_id": r["topic_id"],
                    "topic_name": r["topic_name"],
                    "chapter_id": r["chapter_id"],
                    "chapter_name": r["chapter_name"],
                    "branch": r["branch_id"],
                    "branch_name": r["branch_name"],
                    "wrong_count": r["wrong_count"],
                    "correct_since_count": r["correct_since_count"],
                    "last_wrong_at": r["last_wrong_at"],
                    "resolved": bool(r["resolved"]),
                }
            )
        return out

    def mistake_stats(self, profile_id: str) -> dict[str, Any]:
        row = query_one(
            self.conn,
            """SELECT COUNT(*) AS total,
                      SUM(CASE WHEN resolved = 0 THEN 1 ELSE 0 END) AS open_count
               FROM mistakes WHERE profile_id = ?""",
            (profile_id,),
        )
        by_branch = query_all(
            self.conn,
            """SELECT b.id AS branch_id, b.name AS branch_name, COUNT(*) AS n
               FROM mistakes m
               JOIN questions q ON q.id = m.question_id
               JOIN chapters c ON c.id = q.chapter_id
               JOIN branches b ON b.id = c.branch_id
               WHERE m.profile_id = ? AND m.resolved = 0
               GROUP BY b.id""",
            (profile_id,),
        )
        return {
            "total": int(row["total"] or 0) if row else 0,
            "open": int(row["open_count"] or 0) if row else 0,
            "by_branch": [{"branch": r["branch_id"], "name": r["branch_name"], "count": r["n"]} for r in by_branch],
        }

    # ───────────────────────── personal bests ─────────────────────────

    def _update_personal_bests(self, profile_id: str, session_id: str, summary: SessionSummary, config: dict[str, Any]) -> dict[str, Any]:
        scopes: list[tuple[str, str]] = []
        mode_key = config.get("mode_key") or "custom"
        scopes.append(("mode", mode_key))
        if config.get("chapter"):
            scopes.append(("chapter", config["chapter"]))
        if config.get("branch"):
            scopes.append(("branch", config["branch"]))
        scopes.append(("day", _today()))

        metrics: list[tuple[str, float, str]] = [
            ("score", float(summary.score), "higher"),
            ("accuracy", float(summary.accuracy), "higher"),
            ("longest_streak", float(summary.best_streak), "higher"),
            ("most_questions", float(summary.answered), "higher"),
        ]
        if summary.avg_response_ms > 0 and summary.answered >= 5:
            metrics.append(("fastest_avg", float(summary.avg_response_ms), "lower"))

        records: list[dict[str, Any]] = []
        events: list[dict[str, Any]] = []

        for scope, scope_key in scopes:
            for metric, value, direction in metrics:
                if value <= 0:
                    continue
                existing = query_one(
                    self.conn,
                    "SELECT value FROM personal_bests WHERE profile_id=? AND scope=? AND scope_key=? AND metric=?",
                    (profile_id, scope, scope_key, metric),
                )
                is_record = existing is None or (
                    (direction == "higher" and value > existing["value"])
                    or (direction == "lower" and value < existing["value"])
                )
                if not is_record:
                    continue

                previous = existing["value"] if existing else None
                self.conn.execute(
                    """INSERT INTO personal_bests (profile_id, scope, scope_key, metric, value, session_id, achieved_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)
                       ON CONFLICT(profile_id, scope, scope_key, metric) DO UPDATE SET
                         value=excluded.value, session_id=excluded.session_id, achieved_at=excluded.achieved_at""",
                    (profile_id, scope, scope_key, metric, value, session_id, _now_iso()),
                )
                record = {"scope": scope, "scope_key": scope_key, "metric": metric, "value": value, "previous": previous}
                records.append(record)
                if scope == "mode":
                    events.append({"kind": "personal_best", **record})
                if metric == "score":
                    self._add_xp(profile_id, 25, "personal_best", session_id)

        return {"records": records, "events": events}

    def personal_bests(self, profile_id: str) -> list[dict[str, Any]]:
        rows = query_all(
            self.conn,
            """SELECT pb.scope, pb.scope_key, pb.metric, pb.value, pb.achieved_at,
                      COALESCE(tm.name, c.name, b.name, pb.scope_key) AS label
               FROM personal_bests pb
               LEFT JOIN test_modes tm ON pb.scope='mode' AND tm.key = pb.scope_key
               LEFT JOIN chapters c ON pb.scope='chapter' AND c.id = pb.scope_key
               LEFT JOIN branches b ON pb.scope='branch' AND b.id = pb.scope_key
               WHERE pb.profile_id = ?
               ORDER BY pb.scope, pb.metric, pb.value DESC""",
            (profile_id,),
        )
        return [
            {
                "scope": r["scope"],
                "scope_key": r["scope_key"],
                "label": r["label"],
                "metric": r["metric"],
                "value": r["value"],
                "achieved_at": r["achieved_at"],
            }
            for r in rows
        ]

    # ───────────────────────── XP, levels, badges, streaks ─────────────────────────

    def _profile_xp(self, profile_id: str) -> int:
        row = query_one(self.conn, "SELECT xp_total FROM profiles WHERE id = ?", (profile_id,))
        return int(row["xp_total"]) if row else 0

    def _profile_level(self, profile_id: str) -> int:
        row = query_one(self.conn, "SELECT level FROM profiles WHERE id = ?", (profile_id,))
        return int(row["level"]) if row else 1

    def _add_xp(self, profile_id: str, amount: int, reason: str, session_id: str | None) -> None:
        if amount <= 0:
            return
        self.conn.execute(
            "INSERT INTO xp_events (profile_id, amount, reason, session_id, created_at) VALUES (?, ?, ?, ?, ?)",
            (profile_id, amount, reason, session_id, _now_iso()),
        )
        self.conn.execute(
            "UPDATE profiles SET xp_total = xp_total + ?, updated_at = datetime('now') WHERE id = ?",
            (amount, profile_id),
        )
        new_level = level_for_xp(self._profile_xp(profile_id))
        self.conn.execute("UPDATE profiles SET level = ? WHERE id = ?", (new_level, profile_id))

    def award_xp(self, profile_id: str, amount: int, *, reason: str) -> dict[str, Any]:
        """Public XP award for activity outside a seeded-bank session.

        The arithmetic trainer generates questions live, so it never creates a
        row in `sessions`; it still needs to move XP, level and the day streak.
        """
        self._add_xp(profile_id, amount, reason, None)
        self._update_day_streak(profile_id)
        self.conn.commit()
        total = self._profile_xp(profile_id)
        level = level_for_xp(total)
        floor = xp_for_level(level)
        ceil = xp_for_level(level + 1)
        return {
            "xp_total": total,
            "xp_awarded": amount,
            "level": level,
            "xp_into_level": total - floor,
            "xp_for_next_level": max(ceil - floor, 1),
            "level_progress": round((total - floor) / max(ceil - floor, 1), 4),
            "streak_day_count": self._day_streak(profile_id),
        }

    def _update_day_streak(self, profile_id: str) -> None:
        row = query_one(self.conn, "SELECT last_active_day, streak_day_count FROM profiles WHERE id = ?", (profile_id,))
        if row is None:
            return

        today = _today()
        last = row["last_active_day"]
        current = int(row["streak_day_count"] or 0)

        if last == today:
            return

        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
        new_count = current + 1 if last == yesterday else 1

        self.conn.execute(
            "UPDATE profiles SET last_active_day = ?, streak_day_count = ?, updated_at = datetime('now') WHERE id = ?",
            (today, new_count, profile_id),
        )

    def _award_badges(self, profile_id: str, session_id: str, summary: SessionSummary, attempts: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
        rows = query_all(self.conn, "SELECT * FROM badges")
        owned = {r["badge_id"] for r in query_all(self.conn, "SELECT badge_id FROM badge_awards WHERE profile_id = ?", (profile_id,))}
        awarded: list[dict[str, Any]] = []

        stats = self._badge_stats(profile_id, summary, attempts)

        for row in rows:
            badge_id = row["id"]
            if badge_id in owned:
                continue
            criterion = json.loads(row["criterion_json"] or "{}")
            if not self._criterion_met(criterion, stats):
                continue
            self.conn.execute(
                "INSERT OR IGNORE INTO badge_awards (profile_id, badge_id, awarded_at) VALUES (?, ?, ?)",
                (profile_id, badge_id, _now_iso()),
            )
            self._add_xp(profile_id, 50, "badge", session_id)
            awarded.append({"kind": "badge", "badge_id": badge_id, "name": row["name"], "icon": row["icon"], "description": row["description"]})

        return awarded

    def _badge_stats(self, profile_id: str, summary: SessionSummary, attempts: Sequence[dict[str, Any]]) -> dict[str, float]:
        totals = query_one(
            self.conn,
            """SELECT COUNT(*) AS answered, SUM(is_correct) AS correct FROM attempts WHERE profile_id = ?""",
            (profile_id,),
        )
        sessions_row = query_one(
            self.conn,
            "SELECT COUNT(*) AS n FROM sessions WHERE profile_id = ? AND finished_at IS NOT NULL",
            (profile_id,),
        )
        resolved = query_one(
            self.conn,
            "SELECT COUNT(*) AS n FROM mistakes WHERE profile_id = ? AND resolved = 1",
            (profile_id,),
        )
        balancing = query_one(
            self.conn,
            "SELECT COUNT(*) AS n FROM attempts WHERE profile_id = ? AND question_type='balancing' AND is_correct=1",
            (profile_id,),
        )
        best_streak_row = query_one(
            self.conn,
            "SELECT MAX(streak_at_answer) AS best FROM attempts WHERE profile_id = ?",
            (profile_id,),
        )

        return {
            "questions_answered": float((totals["answered"] or 0) if totals else 0),
            "sessions_completed": float((sessions_row["n"] or 0) if sessions_row else 0),
            "mistakes_resolved": float((resolved["n"] or 0) if resolved else 0),
            "balancing_correct": float((balancing["n"] or 0) if balancing else 0),
            "answer_streak": float(max(summary.best_streak, (best_streak_row["best"] or 0) if best_streak_row else 0)),
            "session_accuracy": float(summary.accuracy * 100),
            "session_avg_response_ms": float(summary.avg_response_ms),
            "session_questions": float(summary.answered),
            "level": float(level_for_xp(self._profile_xp(profile_id))),
            "day_streak": float(self._day_streak(profile_id)),
        }

    def _day_streak(self, profile_id: str) -> int:
        row = query_one(self.conn, "SELECT streak_day_count FROM profiles WHERE id = ?", (profile_id,))
        return int(row["streak_day_count"] or 0) if row else 0

    def _criterion_met(self, criterion: dict[str, Any], stats: dict[str, float]) -> bool:
        kind = criterion.get("type")
        target = float(criterion.get("value", 0))
        minimum_questions = float(criterion.get("min_questions", 0))

        if kind == "sessions_completed":
            return stats["sessions_completed"] >= target
        if kind == "questions_answered":
            return stats["questions_answered"] >= target
        if kind == "answer_streak":
            return stats["answer_streak"] >= target
        if kind == "mistakes_resolved":
            return stats["mistakes_resolved"] >= target
        if kind == "question_type_correct":
            return stats["balancing_correct"] >= target
        if kind == "level":
            return stats["level"] >= target
        if kind == "day_streak":
            return stats["day_streak"] >= target
        if kind == "session_accuracy":
            return stats["session_questions"] >= minimum_questions and stats["session_accuracy"] >= target
        if kind == "session_avg_response_ms":
            return stats["session_questions"] >= minimum_questions and 0 < stats["session_avg_response_ms"] <= target
        return False

    def badge_status(self, profile_id: str) -> list[dict[str, Any]]:
        rows = query_all(self.conn, "SELECT * FROM badges")
        owned = {
            r["badge_id"]: r["awarded_at"]
            for r in query_all(self.conn, "SELECT badge_id, awarded_at FROM badge_awards WHERE profile_id = ?", (profile_id,))
        }
        return [
            {
                "id": r["id"],
                "name": r["name"],
                "description": r["description"],
                "icon": r["icon"],
                "earned": r["id"] in owned,
                "awarded_at": owned.get(r["id"]),
            }
            for r in rows
        ]

    def _record_leaderboard(self, profile_id: str, session_id: str, summary: SessionSummary, config: dict[str, Any]) -> None:
        profile = query_one(self.conn, "SELECT display_name FROM profiles WHERE id = ?", (profile_id,))
        if profile is None or summary.score <= 0:
            return
        day = _today()
        self.conn.execute(
            """INSERT INTO leaderboard_entries (scope, day, profile_id, display_name, mode_key, score, accuracy, xp_delta, created_at)
               VALUES ('local_today', ?, ?, ?, ?, ?, ?, ?, ?)""",
            (day, profile_id, profile["display_name"], config.get("mode_key"), summary.score, summary.accuracy, summary.xp, _now_iso()),
        )

    # ───────────────────────── dashboard ─────────────────────────

    def lifetime_stats(self, profile_id: str) -> dict[str, Any]:
        row = query_one(
            self.conn,
            """SELECT COUNT(*) AS answered, COALESCE(SUM(is_correct),0) AS correct,
                      COALESCE(AVG(response_ms),0) AS avg_ms, MIN(CASE WHEN response_ms>0 THEN response_ms END) AS fastest
               FROM attempts WHERE profile_id = ?""",
            (profile_id,),
        )
        sessions_row = query_one(
            self.conn,
            "SELECT COUNT(*) AS n, COALESCE(SUM(score),0) AS score FROM sessions WHERE profile_id = ? AND finished_at IS NOT NULL",
            (profile_id,),
        )
        profile = query_one(self.conn, "SELECT xp_total, level, streak_day_count, last_active_day FROM profiles WHERE id = ?", (profile_id,))

        answered = int(row["answered"] or 0) if row else 0
        correct = int(row["correct"] or 0) if row else 0

        return {
            "questions_answered": answered,
            "correct_answers": correct,
            "accuracy": (correct / answered) if answered else 0.0,
            "avg_response_ms": float(row["avg_ms"] or 0) if row else 0.0,
            "fastest_response_ms": int(row["fastest"]) if row and row["fastest"] else None,
            "sessions_completed": int(sessions_row["n"] or 0) if sessions_row else 0,
            "total_score": int(sessions_row["score"] or 0) if sessions_row else 0,
            "xp_total": int(profile["xp_total"]) if profile else 0,
            "level": int(profile["level"]) if profile else 1,
            "day_streak": int(profile["streak_day_count"] or 0) if profile else 0,
            "last_active_day": profile["last_active_day"] if profile else None,
        }

    def today_stats(self, profile_id: str) -> dict[str, Any]:
        day = _today()
        row = query_one(
            self.conn,
            """SELECT COUNT(*) AS answered, COALESCE(SUM(is_correct),0) AS correct, COALESCE(AVG(response_ms),0) AS avg_ms
               FROM attempts WHERE profile_id = ? AND substr(created_at,1,10) = ?""",
            (profile_id, day),
        )
        xp_row = query_one(
            self.conn,
            "SELECT COALESCE(SUM(amount),0) AS xp FROM xp_events WHERE profile_id = ? AND substr(created_at,1,10) = ?",
            (profile_id, day),
        )
        sessions_row = query_one(
            self.conn,
            "SELECT COUNT(*) AS n FROM sessions WHERE profile_id = ? AND substr(started_at,1,10) = ? AND finished_at IS NOT NULL",
            (profile_id, day),
        )
        answered = int(row["answered"] or 0) if row else 0
        correct = int(row["correct"] or 0) if row else 0

        return {
            "day": day,
            "questions": answered,
            "accuracy": (correct / answered) if answered else 0.0,
            "avg_response_ms": float(row["avg_ms"] or 0) if row else 0.0,
            "xp_today": int(xp_row["xp"] or 0) if xp_row else 0,
            "sessions_today": int(sessions_row["n"] or 0) if sessions_row else 0,
        }

    def recent_sessions(self, profile_id: str, limit: int = 10) -> list[dict[str, Any]]:
        rows = query_all(
            self.conn,
            """SELECT s.id, s.mode_key, s.started_at, s.finished_at, s.score, s.accuracy, s.best_streak,
                      s.questions_answered, s.correct_count, s.avg_response_ms, s.xp_awarded,
                      tm.name AS mode_name
               FROM sessions s LEFT JOIN test_modes tm ON tm.key = s.mode_key
               WHERE s.profile_id = ? AND s.finished_at IS NOT NULL
               ORDER BY s.started_at DESC LIMIT ?""",
            (profile_id, limit),
        )
        return [
            {
                "session_id": r["id"],
                "mode_key": r["mode_key"],
                "mode_name": r["mode_name"] or r["mode_key"],
                "started_at": r["started_at"],
                "score": r["score"],
                "accuracy": r["accuracy"],
                "best_streak": r["best_streak"],
                "questions": r["questions_answered"],
                "correct": r["correct_count"],
                "avg_response_ms": r["avg_response_ms"],
                "xp": r["xp_awarded"],
            }
            for r in rows
        ]

    def chapter_progress(self, profile_id: str, branch_id: str | None = None) -> list[dict[str, Any]]:
        sql = """
            SELECT c.id AS chapter_id, c.name AS chapter_name, c.code, c.display_order, c.syllabus_status,
                   b.id AS branch_id, b.name AS branch_name,
                   COUNT(DISTINCT q.id) AS bank_size,
                   COALESCE(MAX(p.attempts), 0) AS attempts,
                   COALESCE(MAX(p.correct), 0) AS correct,
                   COALESCE(MAX(p.mastery), 0) AS mastery,
                   COALESCE(MAX(p.best_score), 0) AS best_score
            FROM chapters c
            JOIN branches b ON b.id = c.branch_id
            LEFT JOIN questions q ON q.chapter_id = c.id AND q.status = 'approved'
            LEFT JOIN (
                SELECT a.chapter_id,
                       COUNT(*) AS attempts,
                       SUM(a.is_correct) AS correct,
                       AVG(a.is_correct) AS mastery,
                       MAX(s.score) AS best_score
                FROM attempts a JOIN sessions s ON s.id = a.session_id
                WHERE a.profile_id = ?
                GROUP BY a.chapter_id
            ) p ON p.chapter_id = c.id
            WHERE c.syllabus_status IN ('core','foundation','optional')
        """
        params: list[Any] = [profile_id]
        if branch_id:
            sql += " AND b.id = ?"
            params.append(branch_id)
        # b.id joined in so Postgres accepts b.name / b.display_order; c.id alone
        # only covers columns of `chapters`.
        sql += " GROUP BY c.id, b.id ORDER BY b.display_order, c.display_order"

        rows = query_all(self.conn, sql, tuple(params))
        return [
            {
                "chapter_id": r["chapter_id"],
                "name": r["chapter_name"],
                "code": r["code"],
                "branch": r["branch_id"],
                "branch_name": r["branch_name"],
                "syllabus_status": r["syllabus_status"],
                "bank_size": r["bank_size"],
                "attempts": r["attempts"],
                "correct": r["correct"],
                "accuracy": (r["correct"] / r["attempts"]) if r["attempts"] else 0.0,
                "mastery": r["mastery"],
                "best_score": r["best_score"],
            }
            for r in rows
        ]

    def xp_history(self, profile_id: str, days: int = 14) -> list[dict[str, Any]]:
        rows = query_all(
            self.conn,
            """SELECT substr(created_at,1,10) AS day, SUM(amount) AS xp, COUNT(*) AS events
               FROM xp_events WHERE profile_id = ?
               GROUP BY day ORDER BY day DESC LIMIT ?""",
            (profile_id, days),
        )
        return [{"day": r["day"], "xp": int(r["xp"] or 0)} for r in reversed(rows)]
