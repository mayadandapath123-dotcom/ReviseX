"""QuestionService — the only module that reads the question bank.

All selection happens here so test generation, mistake practice and weak-topic
revision share one implementation and one set of indexes.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from typing import Any, Iterable, Sequence

from app.db.connection import query_all, query_one


@dataclass(frozen=True)
class QuestionFilter:
    subject: str | None = None
    branch: str | None = None
    chapter: str | None = None
    chapters: Sequence[str] | None = None
    topic: str | None = None
    topics: Sequence[str] | None = None
    question_types: Sequence[str] | None = None
    difficulties: Sequence[str] | None = None
    tags: Sequence[str] | None = None
    syllabus_status: Sequence[str] = ("core", "foundation")
    statuses: Sequence[str] = ("approved",)
    question_ids: Sequence[str] | None = None
    exclude_ids: Sequence[str] | None = None
    limit: int | None = None


def _select_columns() -> str:
    return """
        q.id, q.chapter_id, q.topic_id, q.question_type, q.prompt, q.stimulus_json,
        q.answer_key, q.explanation, q.hint, q.difficulty, q.time_budget_ms,
        q.source_ref, q.origin, q.status, q.meta_json,
        c.name AS chapter_name, c.syllabus_status AS syllabus_status,
        b.id AS branch_id, b.name AS branch_name, s.id AS subject_id, s.name AS subject_name,
        t.name AS topic_name
    """


def _base_from() -> str:
    return """
        FROM questions q
        JOIN chapters c ON c.id = q.chapter_id
        JOIN branches b ON b.id = c.branch_id
        JOIN subjects s ON s.id = b.subject_id
        LEFT JOIN topics t ON t.id = q.topic_id
    """


def _build_where(f: QuestionFilter) -> tuple[list[str], list[Any]]:
    clauses: list[str] = []
    params: list[Any] = []

    if f.statuses:
        clauses.append(f"q.status IN ({_placeholders(len(f.statuses))})")
        params.extend(f.statuses)
    if f.subject:
        clauses.append("s.id = ?")
        params.append(f.subject)
    if f.branch:
        clauses.append("b.id = ?")
        params.append(f.branch)
    if f.chapter:
        clauses.append("q.chapter_id = ?")
        params.append(f.chapter)
    if f.chapters:
        clauses.append(f"q.chapter_id IN ({_placeholders(len(f.chapters))})")
        params.extend(f.chapters)
    if f.topic:
        clauses.append("q.topic_id = ?")
        params.append(f.topic)
    if f.topics:
        clauses.append(f"q.topic_id IN ({_placeholders(len(f.topics))})")
        params.extend(f.topics)
    if f.question_types:
        clauses.append(f"q.question_type IN ({_placeholders(len(f.question_types))})")
        params.extend(f.question_types)
    if f.difficulties:
        clauses.append(f"q.difficulty IN ({_placeholders(len(f.difficulties))})")
        params.extend(f.difficulties)
    if f.syllabus_status:
        clauses.append(f"c.syllabus_status IN ({_placeholders(len(f.syllabus_status))})")
        params.extend(f.syllabus_status)
    if f.question_ids:
        clauses.append(f"q.id IN ({_placeholders(len(f.question_ids))})")
        params.extend(f.question_ids)
    if f.exclude_ids:
        clauses.append(f"q.id NOT IN ({_placeholders(len(f.exclude_ids))})")
        params.extend(f.exclude_ids)
    if f.tags:
        # meta_json stores {"tags": [...]}; a LIKE probe per tag keeps this index-free
        # but cheap at MVP scale. Replaced by a tags table if the bank grows past 10^5.
        tag_clauses = []
        for tag in f.tags:
            tag_clauses.append("q.meta_json LIKE ?")
            params.append(f'%"{tag}"%')
        clauses.append("(" + " OR ".join(tag_clauses) + ")")

    return clauses, params


def _placeholders(count: int) -> str:
    return ", ".join("?" * count)


def row_to_question(row: sqlite3.Row, *, include_answers: bool = True) -> dict[str, Any]:
    question: dict[str, Any] = {
        "id": row["id"],
        "subject": row["subject_id"],
        "subject_name": row["subject_name"],
        "branch": row["branch_id"],
        "branch_name": row["branch_name"],
        "chapter": row["chapter_id"],
        "chapter_name": row["chapter_name"],
        "topic": row["topic_id"],
        "topic_name": row["topic_name"],
        "question_type": row["question_type"],
        "prompt": row["prompt"],
        "stimulus": json.loads(row["stimulus_json"] or "{}"),
        "difficulty": row["difficulty"],
        "time_budget_ms": row["time_budget_ms"],
        "syllabus_status": row["syllabus_status"],
        "tags": json.loads(row["meta_json"] or "{}").get("tags", []),
        "source_ref": row["source_ref"],
        "origin": row["origin"],
        "status": row["status"],
    }

    if include_answers:
        question["answer_key"] = row["answer_key"]
        question["explanation"] = row["explanation"]
        question["hint"] = row["hint"]

    return question


def attach_options(conn: sqlite3.Connection, questions: Sequence[dict[str, Any]], *, include_correct_flag: bool = True) -> None:
    """Bulk-load options for a set of questions in one query (no N+1)."""
    if not questions:
        return

    ids = [q["id"] for q in questions]
    rows = query_all(
        conn,
        f"""SELECT question_id, opt_key, text, render_json, is_correct, display_order
            FROM question_options
            WHERE question_id IN ({_placeholders(len(ids))})
            ORDER BY question_id, display_order""",
        tuple(ids),
    )

    grouped: dict[str, list[dict[str, Any]]] = {qid: [] for qid in ids}
    for row in rows:
        option: dict[str, Any] = {
            "key": row["opt_key"],
            "text": row["text"],
            "render": json.loads(row["render_json"] or "{}"),
        }
        if include_correct_flag:
            option["is_correct"] = bool(row["is_correct"])
        grouped.setdefault(row["question_id"], []).append(option)

    for question in questions:
        question["options"] = grouped.get(question["id"], [])


def find_questions(conn: sqlite3.Connection, f: QuestionFilter, *, include_answers: bool = True) -> list[dict[str, Any]]:
    clauses, params = _build_where(f)
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    limit = f"LIMIT {int(f.limit)}" if f.limit else ""

    sql = f"SELECT {_select_columns()} {_base_from()} {where} {limit}"
    rows = query_all(conn, sql, tuple(params))
    questions = [row_to_question(row, include_answers=include_answers) for row in rows]
    attach_options(conn, questions, include_correct_flag=include_answers)
    return questions


def count_questions(conn: sqlite3.Connection, f: QuestionFilter) -> int:
    clauses, params = _build_where(f)
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    row = query_one(conn, f"SELECT COUNT(*) AS n {_base_from()} {where}", tuple(params))
    return int(row["n"]) if row else 0


def get_question(conn: sqlite3.Connection, question_id: str) -> dict[str, Any] | None:
    row = query_one(conn, f"SELECT {_select_columns()} {_base_from()} WHERE q.id = ?", (question_id,))
    if row is None:
        return None
    question = row_to_question(row)
    attach_options(conn, [question])
    return question


def recently_seen_ids(conn: sqlite3.Connection, profile_id: str, limit: int = 40) -> list[str]:
    """Used to avoid immediate repetition across consecutive tests."""
    rows = query_all(
        conn,
        # GROUP BY rather than DISTINCT: Postgres forbids ORDER BY on a column
        # that is not in the select list of a SELECT DISTINCT. This form is
        # valid on both backends and keeps the "most recently seen first" intent.
        """SELECT a.question_id
           FROM attempts a
           JOIN sessions s ON s.id = a.session_id
           WHERE s.profile_id = ?
           GROUP BY a.question_id
           ORDER BY MAX(a.created_at) DESC
           LIMIT ?""",
        (profile_id, limit),
    )
    return [r["question_id"] for r in rows]


def bank_stats(conn: sqlite3.Connection) -> dict[str, Any]:
    by_branch = query_all(
        conn,
        """SELECT b.id AS branch_id, b.name AS branch_name, COUNT(q.id) AS n
           FROM branches b
           LEFT JOIN chapters c ON c.branch_id = b.id
           LEFT JOIN questions q ON q.chapter_id = c.id AND q.status = 'approved'
           GROUP BY b.id
           ORDER BY b.display_order""",
    )
    by_type = query_all(
        conn,
        "SELECT question_type, COUNT(*) AS n FROM questions WHERE status='approved' GROUP BY question_type",
    )
    by_difficulty = query_all(
        conn,
        "SELECT difficulty, COUNT(*) AS n FROM questions WHERE status='approved' GROUP BY difficulty",
    )
    total = query_one(conn, "SELECT COUNT(*) AS n FROM questions WHERE status='approved'")

    return {
        "total": int(total["n"]) if total else 0,
        "by_branch": [{"branch": r["branch_id"], "name": r["branch_name"], "count": r["n"]} for r in by_branch],
        "by_type": {r["question_type"]: r["n"] for r in by_type},
        "by_difficulty": {r["difficulty"]: r["n"] for r in by_difficulty},
    }


def question_types_available(conn: sqlite3.Connection, chapter_id: str | None = None) -> list[dict[str, Any]]:
    if chapter_id:
        rows = query_all(
            conn,
            "SELECT question_type, COUNT(*) AS n FROM questions WHERE status='approved' AND chapter_id=? GROUP BY question_type",
            (chapter_id,),
        )
    else:
        rows = query_all(
            conn,
            "SELECT question_type, COUNT(*) AS n FROM questions WHERE status='approved' GROUP BY question_type",
        )
    return [{"question_type": r["question_type"], "count": r["n"]} for r in rows]


def ids_for_filter(conn: sqlite3.Connection, f: QuestionFilter) -> list[str]:
    clauses, params = _build_where(f)
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    rows = query_all(conn, f"SELECT q.id {_base_from()} {where}", tuple(params))
    return [r["id"] for r in rows]


def topic_names(conn: sqlite3.Connection, topic_ids: Iterable[str]) -> dict[str, str]:
    ids = [t for t in topic_ids if t]
    if not ids:
        return {}
    rows = query_all(conn, f"SELECT id, name FROM topics WHERE id IN ({_placeholders(len(ids))})", tuple(ids))
    return {r["id"]: r["name"] for r in rows}
