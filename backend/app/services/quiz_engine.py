"""QuizEngine — test generation and session submission.

Generation policy (see brief §40):
  1. resolve configuration (mode preset + overrides)
  2. retrieve eligible questions
  3. avoid immediate repetition
  4. optionally prioritise weak topics / due SRS cards
  5. shuffle questions and options
  6. persist the session shell, return the full set to the client

Submission is authoritative on the server: client-reported points are ignored and
recomputed by ScoringEngine, and balancing answers are re-verified by BalancingEngine.
"""

from __future__ import annotations

import dataclasses
import json
import random
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Sequence

from app.db.connection import query_all, query_one, transaction
from app.services import question_service as qs
from app.services import spaced_repetition_service as srs
from app.services.balancing_engine import Equation, FormulaError, verify
from app.services.progress_service import ProgressService
from app.services.recommendation_engine import RecommendationEngine
from app.services.scoring_engine import summarise

DEFAULT_SYLLABUS = ("core", "foundation")
MS_PER_QUESTION_FALLBACK = 7000
MAX_TIME_MODE_QUESTIONS = 80
MIN_TIME_MODE_QUESTIONS = 12


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


@dataclass
class TestRequest:
    profile_id: str
    mode_key: str | None = None
    subject: str | None = None
    branch: str | None = None
    chapter: str | None = None
    topic: str | None = None
    question_types: Sequence[str] | None = None
    difficulties: Sequence[str] | None = None
    tags: Sequence[str] | None = None
    question_count: int | None = None
    duration_limit_ms: int | None = None
    include_off_syllabus: bool = False
    prioritise_weak: bool | None = None
    shuffle_options: bool | None = None
    seed: int | None = None


class QuizEngine:
    def __init__(self, conn: sqlite3.Connection, progress: ProgressService, recommender: RecommendationEngine):
        self.conn = conn
        self.progress = progress
        self.recommender = recommender
        # Filter used by the most recent _select_pool call, so SRS injection can
        # re-apply exactly the same eligibility rules.
        self._last_filter: qs.QuestionFilter | None = None

    # ───────────────────────── generation ─────────────────────────

    def get_mode(self, mode_key: str) -> dict[str, Any] | None:
        row = query_one(self.conn, "SELECT * FROM test_modes WHERE key = ? AND is_active = 1", (mode_key,))
        if row is None:
            return None
        return {
            "key": row["key"],
            "name": row["name"],
            "description": row["description"],
            "icon": row["icon"],
            "group": row["group_name"],
            "featured": bool(row["is_featured"]),
            "quick_start": bool(row["is_quick_start"]),
            "duration_limit_ms": row["duration_limit_ms"],
            "question_count": row["question_count"],
            "filters": json.loads(row["filters_json"] or "{}"),
            "scoring": json.loads(row["scoring_json"] or "{}"),
        }

    def list_modes(self) -> list[dict[str, Any]]:
        rows = query_all(self.conn, "SELECT key FROM test_modes WHERE is_active = 1 ORDER BY display_order")
        return [mode for mode in (self.get_mode(r["key"]) for r in rows) if mode]

    def build_test(self, request: TestRequest) -> dict[str, Any]:
        mode = self.get_mode(request.mode_key) if request.mode_key else None
        filters = dict((mode or {}).get("filters", {}))
        scoring = dict((mode or {}).get("scoring", {}))

        subject = request.subject or filters.get("subject")
        branch = request.branch or filters.get("branch")
        chapter = request.chapter or filters.get("chapter")
        topic = request.topic or filters.get("topic")
        question_types = request.question_types or filters.get("question_types")
        difficulties = request.difficulties or filters.get("difficulties")
        tags = request.tags or filters.get("tags")

        syllabus = list(filters.get("syllabus_status") or DEFAULT_SYLLABUS)
        if request.include_off_syllabus:
            syllabus = list(dict.fromkeys([*syllabus, "optional", "removed"]))

        question_count = request.question_count or filters.get("question_count") or (mode or {}).get("question_count")
        duration_limit_ms = request.duration_limit_ms or (mode or {}).get("duration_limit_ms")
        prioritise_weak = request.prioritise_weak if request.prioritise_weak is not None else bool(scoring.get("prioritise_weak"))
        shuffle_options = request.shuffle_options if request.shuffle_options is not None else bool(scoring.get("shuffle_options", True))

        if question_count is None and duration_limit_ms:
            question_count = max(
                MIN_TIME_MODE_QUESTIONS,
                min(MAX_TIME_MODE_QUESTIONS, int(duration_limit_ms / MS_PER_QUESTION_FALLBACK)),
            )
        question_count = int(question_count or 20)
        # Over-fetch: time-based modes never run out, count-based modes can be trimmed.
        fetch_limit = question_count * 4 if not duration_limit_ms else question_count + 20

        rng = random.Random(request.seed if request.seed is not None else uuid.uuid4().int)

        pool = self._select_pool(
            request=request,
            subject=subject,
            branch=branch,
            chapter=chapter,
            topic=topic,
            question_types=question_types,
            difficulties=difficulties,
            tags=tags,
            syllabus=syllabus,
            source=str(filters.get("source", "bank")),
            limit=fetch_limit,
            rng=rng,
        )

        if prioritise_weak and pool:
            pool = self.recommender.reorder_by_weakness(request.profile_id, pool)

        pool = self._inject_due_cards(request.profile_id, pool, question_count, rng, self._last_filter)

        if duration_limit_ms:
            selected = pool[: max(question_count, MIN_TIME_MODE_QUESTIONS)]
        else:
            selected = pool[:question_count]

        if not selected:
            raise EmptyQuestionBank(
                "No questions match this configuration. Try a broader chapter or a different mode."
            )

        rng.shuffle(selected)
        if shuffle_options:
            for question in selected:
                options = list(question.get("options", []))
                rng.shuffle(options)
                question["options"] = options

        session_id = f"ses_{uuid.uuid4().hex[:16]}"
        config = {
            "mode_key": request.mode_key,
            "mode_name": (mode or {}).get("name"),
            "subject": subject,
            "branch": branch,
            "chapter": chapter,
            "topic": topic,
            "question_types": question_types,
            "difficulties": difficulties,
            "tags": tags,
            "syllabus_status": syllabus,
            "question_count": question_count,
            "prioritise_weak": prioritise_weak,
            "shuffle_options": shuffle_options,
        }

        with transaction(self.conn):
            self.conn.execute(
                """INSERT INTO sessions (id, profile_id, mode_key, subject_id, branch_id, chapter_id, topic_id,
                                         started_at, duration_limit_ms, questions_total, config_json, client_version)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    session_id,
                    request.profile_id,
                    request.mode_key or "custom",
                    subject,
                    branch,
                    chapter,
                    topic,
                    _now_iso(),
                    duration_limit_ms,
                    len(selected),
                    json.dumps(config, ensure_ascii=False),
                    None,
                ),
            )

        return {
            "session_id": session_id,
            "mode": mode,
            "config": config,
            "duration_limit_ms": duration_limit_ms,
            "per_question_time_ms": scoring.get("per_question_time_ms"),
            "max_attempts": scoring.get("max_attempts", 1),
            "show_explanation": scoring.get("show_explanation", "on_wrong"),
            "wrong_penalty": float(scoring.get("wrong_penalty", 0.0)),
            "stop_on_time": bool(scoring.get("stop_on_time", False)),
            "questions_total": len(selected),
            "questions": selected,
            "server_time": _now_iso(),
        }

    def _select_pool(
        self,
        *,
        request: TestRequest,
        subject: str | None,
        branch: str | None,
        chapter: str | None,
        topic: str | None,
        question_types: Sequence[str] | None,
        difficulties: Sequence[str] | None,
        tags: Sequence[str] | None,
        syllabus: Sequence[str],
        source: str,
        limit: int,
        rng: random.Random,
    ) -> list[dict[str, Any]]:
        allowed_ids: Sequence[str] | None = None
        if source == "mistakes":
            allowed_ids = self.progress.unresolved_mistake_ids(request.profile_id)
            if not allowed_ids:
                return []

        recent = set(qs.recently_seen_ids(self.conn, request.profile_id, limit=40))

        base_filter = qs.QuestionFilter(
            subject=subject,
            branch=branch,
            chapter=chapter,
            topic=topic,
            question_types=question_types,
            difficulties=difficulties,
            tags=tags,
            syllabus_status=tuple(syllabus),
            question_ids=allowed_ids,
            limit=None,
        )
        self._last_filter = base_filter
        pool = qs.find_questions(self.conn, base_filter)

        fresh = [q for q in pool if q["id"] not in recent]
        chosen = fresh if len(fresh) >= min(limit, 5) else pool
        rng.shuffle(chosen)
        return chosen[: max(limit, 1)]

    def _inject_due_cards(
        self,
        profile_id: str,
        pool: list[dict[str, Any]],
        target_count: int,
        rng: random.Random,
        base_filter: qs.QuestionFilter | None = None,
    ) -> list[dict[str, Any]]:
        """Front-load up to ~30% of the set with cards that are due for review.

        Due cards must still satisfy the mode's own filters (question type,
        chapter, syllabus status) — otherwise a due MCQ would leak into, say, a
        balancing-only drill. We re-apply `base_filter` scoped to the due ids.
        """
        due_ids = srs.due_question_ids(self.conn, profile_id, limit=max(4, target_count // 3))
        if not due_ids:
            return pool

        due_index = {q["id"]: q for q in pool}
        due_questions = [due_index[qid] for qid in due_ids if qid in due_index]

        missing_ids = [qid for qid in due_ids if qid not in due_index]
        if missing_ids and base_filter is not None:
            eligible = dataclasses.replace(base_filter, question_ids=missing_ids, limit=None)
            due_questions.extend(qs.find_questions(self.conn, eligible))

        if not due_questions:
            return pool

        rest = [q for q in pool if q["id"] not in {d["id"] for d in due_questions}]
        rng.shuffle(due_questions)
        return [*due_questions, *rest]

    # ───────────────────────── submission ─────────────────────────

    def submit(self, profile_id: str, session_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        session = query_one(self.conn, "SELECT * FROM sessions WHERE id = ? AND profile_id = ?", (session_id, profile_id))
        if session is None:
            raise SessionNotFound(session_id)
        if session["finished_at"]:
            return self.progress.session_summary(profile_id, session_id)

        attempts_in: list[dict[str, Any]] = list(payload.get("attempts", []))
        config = json.loads(session["config_json"] or "{}")
        scoring = (self.get_mode(session["mode_key"]) or {}).get("scoring", {})
        wrong_penalty_factor = float(payload.get("wrong_penalty", scoring.get("wrong_penalty", 0.0)))

        question_ids = [str(a.get("question_id")) for a in attempts_in]
        questions = {q["id"]: q for q in qs.find_questions(self.conn, qs.QuestionFilter(question_ids=question_ids))} if question_ids else {}

        graded: list[dict[str, Any]] = []
        streak = 0

        for index, raw in enumerate(attempts_in):
            question_id = str(raw.get("question_id"))
            question = questions.get(question_id)
            if question is None:
                continue  # unknown/removed question: skip rather than corrupt the session

            response_ms = max(0, int(raw.get("response_ms", 0)))
            difficulty = question["difficulty"]

            if question["question_type"] == "balancing":
                is_correct = self._grade_balancing(question, raw)
            else:
                selected = raw.get("selected_key")
                is_correct = selected is not None and str(selected) == str(question["answer_key"])

            # Server-side scoring is authoritative; client points are ignored.
            from app.services.scoring_engine import score_answer

            result = score_answer(
                difficulty=difficulty,
                response_ms=response_ms,
                time_budget_ms=int(question["time_budget_ms"]),
                streak_before=streak,
                is_correct=is_correct,
                wrong_penalty_factor=wrong_penalty_factor,
            )
            streak = streak + 1 if is_correct else 0

            graded.append(
                {
                    "seq": int(raw.get("seq", index + 1)),
                    "question_id": question_id,
                    "topic_id": question["topic"],
                    "chapter_id": question["chapter"],
                    "difficulty": difficulty,
                    "question_type": question["question_type"],
                    "response_ms": response_ms,
                    "shown_ms": max(0, int(raw.get("shown_ms", 0))),
                    "is_correct": is_correct,
                    "selected_key": raw.get("selected_key"),
                    "option_order": raw.get("option_order", []),
                    "coefficients": raw.get("coefficients"),
                    "points": result.points,
                    "streak": streak,
                    "created_at": _now_iso(),
                }
            )

        summary = summarise(
            [
                {
                    "difficulty": g["difficulty"],
                    "response_ms": g["response_ms"],
                    "time_budget_ms": questions[g["question_id"]]["time_budget_ms"],
                    "is_correct": g["is_correct"],
                    "topic_id": g["topic_id"],
                }
                for g in graded
            ],
            wrong_penalty_factor=wrong_penalty_factor,
            completion_ratio=(len(graded) / session["questions_total"]) if session["questions_total"] else 0.0,
        )

        elapsed_ms = int(payload.get("elapsed_ms") or (session["duration_limit_ms"] or 0))

        with transaction(self.conn):
            for item in graded:
                self.conn.execute(
                    """INSERT INTO attempts (session_id, question_id, profile_id, seq, selected_key,
                                             option_order_json, is_correct, response_ms, shown_ms,
                                             points_awarded, streak_at_answer, difficulty, question_type,
                                             chapter_id, topic_id, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        session_id,
                        item["question_id"],
                        profile_id,
                        item["seq"],
                        item["selected_key"],
                        json.dumps(item["option_order"], ensure_ascii=False),
                        int(item["is_correct"]),
                        item["response_ms"],
                        item["shown_ms"],
                        item["points"],
                        item["streak"],
                        item["difficulty"],
                        item["question_type"],
                        item["chapter_id"],
                        item["topic_id"],
                        item["created_at"],
                    ),
                )

            names = qs.topic_names(self.conn, summary.by_topic.keys())
            analysis = self.progress.apply_session(
                profile_id=profile_id,
                session_id=session_id,
                attempts=graded,
                summary=summary,
                elapsed_ms=elapsed_ms,
                topic_names=names,
                config=config,
            )

            self.conn.execute(
                """UPDATE sessions SET finished_at=?, elapsed_ms=?, questions_answered=?, correct_count=?,
                       score=?, xp_awarded=?, best_streak=?, accuracy=?, avg_response_ms=?, fastest_response_ms=?,
                       summary_json=?, sync_state='local'
                   WHERE id=?""",
                (
                    _now_iso(),
                    elapsed_ms,
                    summary.answered,
                    summary.correct,
                    summary.score,
                    summary.xp,
                    summary.best_streak,
                    summary.accuracy,
                    summary.avg_response_ms,
                    summary.fastest_response_ms,
                    json.dumps(analysis, ensure_ascii=False),
                    session_id,
                ),
            )

        return {
            "session_id": session_id,
            "summary": summary.as_dict(),
            "analysis": analysis,
            "attempts": [
                {
                    "question_id": g["question_id"],
                    "is_correct": g["is_correct"],
                    "points": g["points"],
                    "response_ms": g["response_ms"],
                    "correct_answer": questions[g["question_id"]]["answer_key"],
                    "explanation": questions[g["question_id"]]["explanation"],
                }
                for g in graded
            ],
        }

    def _grade_balancing(self, question: dict[str, Any], raw: dict[str, Any]) -> bool:
        stimulus = question.get("stimulus") or {}
        coefficients = raw.get("coefficients")
        if not coefficients:
            return False
        try:
            equation = Equation(
                reactants=tuple(stimulus.get("reactants", [])),
                products=tuple(stimulus.get("products", [])),
                coefficients=tuple(stimulus.get("solution", [])),
            )
            result = verify(equation, [int(c) for c in coefficients])
        except (FormulaError, ValueError, TypeError):
            return False
        # Only the simplest whole-number ratio counts as fully correct.
        return result.is_balanced and result.is_simplest


class SessionNotFound(Exception):
    def __init__(self, session_id: str):
        super().__init__(f"Session not found: {session_id}")
        self.session_id = session_id


class EmptyQuestionBank(Exception):
    pass
